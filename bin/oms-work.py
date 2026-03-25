#!/usr/bin/env python3
"""
oms-work — sequential MVP executor for pre-cleared OMS tasks.

Usage: oms-work.py <project-slug> [--dry-run] [--task TASK-NNN]

Reads [project]/.claude/cleared-queue.md, executes first ready task,
runs validation chain, updates queue status.

Exit 0 = task processed (done or cto-stop). Exit 1 = queue empty or fatal.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

CONFIG    = Path.home() / '.claude' / 'oms-config.json'
CLAUDE    = Path.home() / '.local' / 'bin' / 'claude'
TEMPLATE  = Path.home() / '.claude' / 'agents' / 'oms-work' / 'cleared-queue-template.md'

VALIDATOR_ROLE: dict[str, str] = {
    'dev':        'Review this implementation for correctness, completeness, and code quality.',
    'qa':         'Test against each acceptance criterion. Identify any failing cases.',
    'em':         'Final approval: confirm the spec is met and output is ready to merge.',
    'researcher': 'Evaluate research quality: methodology sound, findings complete and supported.',
    'cro':        'Validate findings are rigorous, aligned with the research question, and actionable.',
    'cpo':        'Confirm the output creates clear product direction or actionable roadmap items.',
    'cto':        'Review for architectural soundness. Name any technical risk that blocks merging.',
    'pm':         'Confirm requirements coverage: output matches spec and acceptance criteria fully.',
}


# ── Queue parsing ─────────────────────────────────────────────────────────────

TASK_HEADER = re.compile(r'^## (TASK-\d+) — (.+)$', re.MULTILINE)
FIELD       = re.compile(r'^- \*\*([^:]+):\*\* (.+)$', re.MULTILINE)


def parse_queue(path: Path) -> list[dict]:
    if not path.exists():
        return []
    text = path.read_text()
    # Split on task headers, keeping header as part of chunk
    chunks = re.split(r'(?=^## TASK-)', text, flags=re.MULTILINE)
    tasks = []
    for chunk in chunks:
        m = TASK_HEADER.match(chunk)
        if not m:
            continue
        fields = dict(FIELD.findall(chunk))
        deps_raw = fields.get('Depends', 'none').strip()
        tasks.append({
            'id':         m.group(1),
            'title':      m.group(2).strip(),
            'status':     fields.get('Status', 'queued').strip().lower(),
            'type':       fields.get('Type', 'impl').strip().lower(),
            'spec':       fields.get('Spec', '').strip(),
            'acceptance': [a.strip() for a in fields.get('Acceptance', '').split('|') if a.strip()],
            'context':    [c.strip() for c in fields.get('Context', '').split(',') if c.strip() and c.strip() != 'none'],
            'activated':  [a.strip() for a in fields.get('Activated', '').split(',') if a.strip()],
            'validation': [v.strip() for v in re.split(r'\s*→\s*', fields.get('Validation', '')) if v.strip()],
            'depends':    [] if deps_raw.lower() == 'none' else [d.strip() for d in deps_raw.split(',') if d.strip()],
        })
    return tasks


def find_ready(tasks: list[dict], target_id: str | None = None) -> dict | None:
    done = {t['id'] for t in tasks if t['status'] == 'done'}
    for t in tasks:
        if target_id and t['id'] != target_id:
            continue
        if t['status'] == 'queued' and all(d in done for d in t['depends']):
            return t
    return None


def update_status(path: Path, task_id: str, status: str, notes: str = '') -> None:
    text = path.read_text()

    def replacer(m: re.Match) -> str:
        block = m.group(0)
        block = re.sub(r'(- \*\*Status:\*\*) \S+', rf'\1 {status}', block)
        if notes:
            if '**Notes:**' in block:
                block = re.sub(r'(- \*\*Notes:\*\*) .+', rf'\1 {notes}', block)
            else:
                # insert before first blank line or end
                block = block.rstrip('\n') + f'\n- **Notes:** {notes}\n'
        return block

    pattern = rf'(## {re.escape(task_id)} — .+?)(?=\n## TASK-|\Z)'
    path.write_text(re.sub(pattern, replacer, text, flags=re.DOTALL))


# ── Claude invocation ─────────────────────────────────────────────────────────

def run_claude(prompt: str, cwd: Path, model: str, allow_writes: bool = False) -> tuple[str, int]:
    args = [str(CLAUDE), '--print', '--output-format', 'json', '--model', model, '-p', prompt]
    if allow_writes:
        args.append('--dangerously-skip-permissions')
    result = subprocess.run(args, capture_output=True, text=True, cwd=cwd, timeout=600)
    if result.returncode != 0:
        print(f'[oms-work] claude exit {result.returncode}: {result.stderr[:200]}', file=sys.stderr)
        return '', result.returncode
    try:
        data = json.loads(result.stdout)
        return data.get('result') or data.get('content') or '', 0
    except Exception:
        return result.stdout.strip(), 0


# ── Execution + validation ────────────────────────────────────────────────────

def exec_prompt(task: dict) -> str:
    criteria = '\n'.join(f'- {a}' for a in task['acceptance'])
    ctx = f"\nRead these files first: {', '.join(task['context'])}." if task['context'] else ''
    research_note = (
        'Write findings to logs/research/{id}.md. Minimum: 3 evidence-backed findings, '
        'each with a testable prediction.'
    ).format(id=task['id']) if task['type'] == 'research' else 'Make all required file changes.'
    return (
        f"OMS work task ({task['id']}): {task['spec']}\n\n"
        f"Acceptance criteria:\n{criteria}\n"
        f"{ctx}\n\n"
        f"{research_note}\n\n"
        "Output a 1–2 sentence summary of what you did when complete."
    )


def validate_step(validator: str, task: dict, work_summary: str, cwd: Path) -> tuple[bool, str]:
    role = VALIDATOR_ROLE.get(validator.lower(), f'Validate as {validator}: confirm acceptance criteria are met.')
    criteria = '\n'.join(f'- {a}' for a in task['acceptance'])
    prompt = (
        f"Task ({task['id']}): {task['spec']}\n\n"
        f"Acceptance criteria:\n{criteria}\n\n"
        f"Work summary: {work_summary}\n\n"
        f"Your role: {role}\n\n"
        "Output EXACTLY one of:\n"
        "  PASS — [one sentence reason]\n"
        "  FAIL — [one sentence reason]\n"
        "Nothing else."
    )
    out, _ = run_claude(prompt, cwd, model='claude-haiku-4-5-20251001')
    first_line = out.strip().split('\n')[0].upper()
    passed = first_line.startswith('PASS')
    return passed, out.strip()


def execute_task(task: dict, project_path: Path, dry_run: bool) -> tuple[bool, str]:
    print(f'\n[oms-work] ▶ {task["id"]} — {task["title"]}', flush=True)

    if dry_run:
        print(f'[oms-work]   DRY RUN: {task["spec"]}')
        chain_str = ' → '.join(task['validation'])
        print(f'[oms-work]   Validation chain: {chain_str}')
        return True, 'dry-run'

    # Step 1: implementation
    work_out, code = run_claude(
        exec_prompt(task), project_path,
        model='claude-sonnet-4-6', allow_writes=True,
    )
    if code != 0:
        return False, f'CTO-STOP: execution failed (claude exit {code})'

    summary = work_out[:300].replace('\n', ' ').strip()
    print(f'[oms-work]   exec: {summary[:120]}', flush=True)

    # Step 2: validation chain
    for validator in task['validation']:
        passed, reason = validate_step(validator, task, summary, project_path)
        marker = '✓' if passed else '✗'
        print(f'[oms-work]   {marker} {validator}: {reason[:100]}', flush=True)
        if not passed:
            stop = 'CTO-STOP' if validator == 'cto' else 'FAIL'
            return False, f'{stop} ({validator}): {reason[:200]}'

    return True, summary[:200]


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: oms-work.py <project-slug> [--dry-run] [--task TASK-NNN]', file=sys.stderr)
        sys.exit(1)

    slug      = sys.argv[1]
    dry_run   = '--dry-run' in sys.argv
    target_id = next((a for a in sys.argv[2:] if a.startswith('TASK-')), None)

    cfg = json.loads(CONFIG.read_text())
    proj = cfg.get('projects', {}).get(slug)
    if not proj:
        print(f'[oms-work] Unknown project: {slug}', file=sys.stderr)
        sys.exit(1)

    project_path = Path(proj['path'])
    queue_path   = project_path / '.claude' / 'cleared-queue.md'

    # Bootstrap empty queue from template if needed
    if not queue_path.exists() and TEMPLATE.exists():
        queue_path.write_text(TEMPLATE.read_text())
        print(f'[oms-work] Created cleared-queue.md from template at {queue_path}')

    tasks = parse_queue(queue_path)
    if not tasks:
        print('[oms-work] Queue empty or not found.')
        sys.exit(1)

    # Summary
    queued   = [t for t in tasks if t['status'] == 'queued']
    done_ids = {t['id'] for t in tasks if t['status'] == 'done'}
    ready    = [t for t in queued if all(d in done_ids for d in t['depends'])]
    blocked  = [t for t in queued if not all(d in done_ids for d in t['depends'])]
    print(f'[oms-work] Queue: {len(ready)} ready, {len(blocked)} blocked, {len(done_ids)} done')

    task = find_ready(tasks, target_id)
    if not task:
        msg = f'task {target_id} not ready' if target_id else 'no ready tasks'
        print(f'[oms-work] {msg}')
        sys.exit(1)

    update_status(queue_path, task['id'], 'in-progress')
    passed, notes = execute_task(task, project_path, dry_run)

    final_status = 'done' if passed else 'cto-stop'
    update_status(queue_path, task['id'], final_status, notes)

    if passed:
        print(f'\n## OMS Work\n✓ {task["id"]} — {task["title"]} complete.\n{notes}')
    else:
        print(f'\n## OMS Work\n⚑ {task["id"]} — {task["title"]} blocked.\n{notes}')

    sys.exit(0)


if __name__ == '__main__':
    main()
