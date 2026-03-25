#!/usr/bin/env python3
"""
oms-work — execute pre-cleared OMS tasks with worktree isolation.

Usage:
  oms-work.py <project-slug>              # run first ready task
  oms-work.py <project-slug> --all        # run all ready tasks (background mode)
  oms-work.py <project-slug> --dry-run    # show plan without executing
  oms-work.py <project-slug> TASK-NNN     # run specific task

Each task gets its own git worktree (branch: oms-work/task-nnn).
On done: commit + remove worktree. On cto-stop: leave worktree open for review.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

CONFIG        = Path.home() / '.claude' / 'oms-config.json'
CLAUDE        = Path.home() / '.local' / 'bin' / 'claude'
TEMPLATE      = Path.home() / '.claude' / 'agents' / 'oms-work' / 'cleared-queue-template.md'
ELAB_LESSONS  = Path.home() / '.claude' / 'agents' / 'task-elaboration' / 'lessons.md'

VALIDATOR_ROLE: dict[str, str] = {
    'dev':        'Review for correctness, completeness, and code quality against acceptance criteria.',
    'qa':         'Test each acceptance criterion. Identify any failing cases or edge cases.',
    'em':         'Final approval: spec met, all criteria passed, ready to merge.',
    'researcher': 'Evaluate methodology soundness and finding completeness.',
    'cro':        'Validate findings are rigorous, aligned with research question, and actionable.',
    'cpo':        'Confirm output creates clear product direction or actionable roadmap items.',
    'cto':        'Review for architectural soundness. Name any blocking technical risk.',
}


# ── Spec failure logging ──────────────────────────────────────────────────────

SPEC_FAILURE_SIGNALS = [
    'ambiguous', 'unclear', 'missing scenario', 'incomplete', 'not specified',
    'criteria', 'undefined', 'no test', 'edge case', 'not covered',
    'missing artifact', 'wrong file', 'wrong export', 'path not found',
]


def _is_spec_failure(reason: str) -> bool:
    low = reason.lower()
    return any(sig in low for sig in SPEC_FAILURE_SIGNALS)


def log_spec_failure(task: dict, validator: str, reason: str) -> None:
    """Append a spec lesson to task-elaboration/lessons.md when failure is spec-related."""
    if not _is_spec_failure(reason):
        return
    lesson = (f'- [{task["id"]}] {validator} FAIL — {reason[:200].strip()}'
              f' | Spec: "{task["spec"][:120]}"')
    try:
        with ELAB_LESSONS.open('a') as f:
            f.write(lesson + '\n')
    except OSError:
        pass  # non-fatal


# ── Queue parsing ─────────────────────────────────────────────────────────────

TASK_HEADER = re.compile(r'^## (TASK-\d+) — (.+)$', re.MULTILINE)
FIELD       = re.compile(r'^- \*\*([^:]+):\*\* (.+)$', re.MULTILINE)


def parse_queue(path: Path) -> list[dict]:
    if not path.exists():
        return []
    chunks = re.split(r'(?=^## TASK-)', path.read_text(), flags=re.MULTILINE)
    tasks = []
    for chunk in chunks:
        m = TASK_HEADER.match(chunk)
        if not m:
            continue
        f = dict(FIELD.findall(chunk))
        deps_raw = f.get('Depends', 'none').strip()
        # Scenarios: new field; fall back to Acceptance for backwards compat
        scenarios_raw = f.get('Scenarios', f.get('Acceptance', ''))
        tasks.append({
            'id':         m.group(1),
            'title':      m.group(2).strip(),
            'status':     f.get('Status', 'queued').strip().lower(),
            'type':       f.get('Type', 'impl').strip().lower(),
            'spec':       f.get('Spec', '').strip(),
            'scenarios':  [s.strip() for s in scenarios_raw.split('|') if s.strip()],
            'artifacts':  [a.strip() for a in f.get('Artifacts', '').split('|') if a.strip()],
            'produces':   f.get('Produces', 'none').strip(),
            'verify':     [v.strip() for v in f.get('Verify', '').split('|') if v.strip()],
            'context':    [c.strip() for c in f.get('Context', '').split(',')
                           if c.strip() and c.strip() != 'none'],
            'validation': [v.strip() for v in re.split(r'\s*→\s*', f.get('Validation', ''))
                           if v.strip()],
            'depends':    [] if deps_raw.lower() == 'none'
                          else [d.strip() for d in deps_raw.split(',') if d.strip()],
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


def find_all_ready(tasks: list[dict]) -> list[dict]:
    done = {t['id'] for t in tasks if t['status'] == 'done'}
    return [t for t in tasks
            if t['status'] == 'queued' and all(d in done for d in t['depends'])]


def update_status(path: Path, task_id: str, status: str, notes: str = '') -> None:
    def replacer(m: re.Match) -> str:
        block = m.group(0)
        block = re.sub(r'(- \*\*Status:\*\*) \S+', rf'\1 {status}', block)
        if notes:
            if '**Notes:**' in block:
                block = re.sub(r'(- \*\*Notes:\*\*) .+', rf'\1 {notes}', block)
            else:
                block = block.rstrip('\n') + f'\n- **Notes:** {notes}\n'
        return block
    pattern = rf'(## {re.escape(task_id)} — .+?)(?=\n## TASK-|\Z)'
    path.write_text(re.sub(pattern, replacer, path.read_text(), flags=re.DOTALL))


# ── Worktree management ───────────────────────────────────────────────────────

def _wt_path(project_path: Path, task_id: str) -> Path:
    return project_path / '.claude' / 'worktrees' / task_id


def create_worktree(project_path: Path, task_id: str) -> tuple[Path, str]:
    branch = f'oms-work/{task_id.lower()}'
    wt = _wt_path(project_path, task_id)
    wt.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(['git', 'worktree', 'add', str(wt), '-b', branch, 'HEAD'],
                       capture_output=True, text=True, cwd=project_path)
    if r.returncode != 0:
        # Branch exists from prior attempt — reuse
        subprocess.run(['git', 'worktree', 'add', str(wt), branch],
                       capture_output=True, cwd=project_path)
    return wt, branch


def commit_worktree(wt: Path, task_id: str, title: str) -> bool:
    subprocess.run(['git', 'add', '-A'], cwd=wt, capture_output=True)
    r = subprocess.run(['git', 'commit', '--allow-empty',
                        '-m', f'oms-work: {task_id} — {title}'],
                       capture_output=True, text=True, cwd=wt)
    return r.returncode == 0


def remove_worktree(project_path: Path, task_id: str) -> None:
    subprocess.run(['git', 'worktree', 'remove', '--force',
                    str(_wt_path(project_path, task_id))],
                   capture_output=True, cwd=project_path)


# ── Claude invocation ─────────────────────────────────────────────────────────

def run_claude(prompt: str, cwd: Path, model: str, allow_writes: bool = False) -> tuple[str, int]:
    args = [str(CLAUDE), '--print', '--output-format', 'json', '--model', model, '-p', prompt]
    if allow_writes:
        args.append('--dangerously-skip-permissions')
    r = subprocess.run(args, capture_output=True, text=True, cwd=cwd, timeout=600)
    if r.returncode != 0:
        print(f'[oms-work] claude exit {r.returncode}: {r.stderr[:200]}', file=sys.stderr)
        return '', r.returncode
    try:
        data = json.loads(r.stdout)
        return data.get('result') or data.get('content') or '', 0
    except Exception:
        return r.stdout.strip(), 0


# ── Execution + validation ────────────────────────────────────────────────────

def exec_prompt(task: dict, wt: Path) -> str:
    scenarios  = '\n'.join(f'- {s}' for s in task['scenarios'])
    artifacts  = '\n'.join(f'- {a}' for a in task['artifacts'])
    produces   = task['produces']

    # Pre-load context files — no cold reads during execution
    ctx_blocks: list[str] = []
    for rel in task['context']:
        full = wt / rel
        if full.exists():
            content = full.read_text(encoding='utf-8', errors='replace')[:3000]
            ctx_blocks.append(f'### {rel}\n```\n{content}\n```')
        else:
            ctx_blocks.append(f'### {rel}\n(not found — create it)')
    ctx_section = ('\n\n## Context Files\n\n' + '\n\n'.join(ctx_blocks)) if ctx_blocks else ''

    artifact_section = (f'\n\n## Required Artifacts\nYou MUST produce exactly these files:\n{artifacts}'
                        if artifacts else '')
    produces_section = (f'\n\n## Produces (downstream contract)\n{produces}'
                        if produces and produces.lower() != 'none' else '')

    if task['type'] == 'research':
        action = ('Write findings to logs/research/{id}.md. '
                  'Include ≥3 evidence-backed findings, each with a testable prediction.'
                  ).format(id=task['id'])
    else:
        action = 'Make all required file changes to satisfy every scenario.'

    return (f"OMS work task ({task['id']}): {task['spec']}\n\n"
            f"## Behavioral Scenarios\n{scenarios}"
            f"{artifact_section}{produces_section}{ctx_section}\n\n"
            f"{action}\n\n"
            "Output a 1–2 sentence summary when complete.")


def validate_step(validator: str, task: dict, summary: str, cwd: Path) -> tuple[bool, str]:
    role = VALIDATOR_ROLE.get(validator.lower(),
                               f'Validate as {validator}: confirm all scenarios are met.')
    scenarios = '\n'.join(f'- {s}' for s in task['scenarios'])
    artifacts = '\n'.join(f'- {a}' for a in task['artifacts'])
    artifact_section = f'\n\nRequired artifacts:\n{artifacts}' if artifacts else ''
    prompt = (f"Task ({task['id']}): {task['spec']}\n\nScenarios:\n{scenarios}{artifact_section}\n\n"
              f"Work summary: {summary}\n\nYour role: {role}\n\n"
              "Output EXACTLY: PASS — [reason]  OR  FAIL — [reason]. Nothing else.")
    out, _ = run_claude(prompt, cwd, model='claude-haiku-4-5-20251001')
    return out.strip().upper().startswith('PASS'), out.strip()


def execute_task(task: dict, project_path: Path, dry_run: bool) -> tuple[bool, str]:
    print(f'\n[oms-work] ▶ {task["id"]} — {task["title"]}', flush=True)
    if dry_run:
        print(f'[oms-work]   DRY RUN: {task["spec"]}')
        print(f'[oms-work]   Chain: {" → ".join(task["validation"])}')
        return True, 'dry-run'

    wt, branch = create_worktree(project_path, task['id'])
    try:
        work_out, code = run_claude(exec_prompt(task, wt), wt, 'claude-sonnet-4-6', allow_writes=True)
        if code != 0:
            remove_worktree(project_path, task['id'])
            return False, f'CTO-STOP: claude execution failed (exit {code})'

        summary = work_out[:300].replace('\n', ' ').strip()
        print(f'[oms-work]   exec: {summary[:120]}', flush=True)

        # Hallucination guard — impl tasks must produce file changes
        if task['type'] != 'research':
            gs = subprocess.run(['git', 'status', '--porcelain'],
                                capture_output=True, text=True, cwd=wt)
            if not gs.stdout.strip():
                remove_worktree(project_path, task['id'])
                return False, f'CTO-STOP: hallucination — no files changed in worktree'

        for validator in task['validation']:
            passed, reason = validate_step(validator, task, summary, wt)
            print(f'[oms-work]   {"✓" if passed else "✗"} {validator}: {reason[:100]}', flush=True)
            if not passed:
                log_spec_failure(task, validator, reason)
                stop_type = 'CTO-STOP' if validator == 'cto' else 'FAIL'
                return False, f'{stop_type} ({validator}): {reason[:200]} | branch: {branch}'

        # Shell verification — deterministic command-tier check
        for cmd in task['verify']:
            vr = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                cwd=wt, timeout=120)
            label = '✓' if vr.returncode == 0 else '✗'
            print(f'[oms-work]   {label} verify `{cmd[:60]}`', flush=True)
            if vr.returncode != 0:
                output = (vr.stdout + vr.stderr)[-300:].strip()
                return False, f'FAIL (verify `{cmd}`): {output} | branch: {branch}'

        commit_worktree(wt, task['id'], task['title'])
        remove_worktree(project_path, task['id'])
        return True, f'{summary[:180]} | branch: {branch} — merge when ready'

    except Exception as e:
        remove_worktree(project_path, task['id'])
        return False, f'CTO-STOP: exception — {e}'


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: oms-work.py <project-slug> [--all] [--dry-run] [TASK-NNN]', file=sys.stderr)
        sys.exit(1)

    slug      = sys.argv[1]
    run_all   = '--all' in sys.argv
    dry_run   = '--dry-run' in sys.argv
    target_id = next((a for a in sys.argv[2:] if a.startswith('TASK-')), None)

    cfg  = json.loads(CONFIG.read_text())
    proj = cfg.get('projects', {}).get(slug)
    if not proj:
        print(f'[oms-work] Unknown project: {slug}', file=sys.stderr)
        sys.exit(1)

    project_path = Path(proj['path'])
    queue_path   = project_path / '.claude' / 'cleared-queue.md'

    if not queue_path.exists() and TEMPLATE.exists():
        queue_path.write_text(TEMPLATE.read_text())
        print(f'[oms-work] Created queue at {queue_path}')

    results: list[tuple[str, str, bool]] = []  # (id, title, passed)

    while True:
        tasks    = parse_queue(queue_path)
        done_ids = {t['id'] for t in tasks if t['status'] == 'done'}
        ready    = find_all_ready(tasks)
        blocked  = [t for t in tasks if t['status'] == 'queued' and t not in ready]
        print(f'[oms-work] Queue: {len(ready)} ready, {len(blocked)} blocked, '
              f'{len(done_ids)} done', flush=True)

        task = find_ready(tasks, target_id) if target_id else (ready[0] if ready else None)
        if not task:
            break

        update_status(queue_path, task['id'], 'in-progress')
        passed, notes = execute_task(task, project_path, dry_run)
        final = 'done' if passed else 'cto-stop'
        update_status(queue_path, task['id'], final, notes)
        results.append((task['id'], task['title'], passed))

        if not run_all or not passed and 'CTO-STOP' in notes:
            break  # single-task mode, or CTO-stop: stop this chain

        if not run_all:
            break

    # Report
    done_r  = [(i, t) for i, t, p in results if p]
    stops   = [(i, t) for i, t, p in results if not p]
    lines   = ['## OMS Work']
    for i, t in done_r:
        lines.append(f'✓ {i} — {t}')
    for i, t in stops:
        lines.append(f'⚑ {i} — {t} [cto-stop]')
    if not results:
        lines.append('No tasks ran.')
    print('\n'.join(lines))
    sys.exit(0)


if __name__ == '__main__':
    main()
