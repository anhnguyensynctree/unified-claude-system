#!/usr/bin/env python3
"""
oms-work — execute pre-cleared OMS tasks with worktree isolation.

Usage:
  oms-work.py <project-slug>              # run first ready task
  oms-work.py <project-slug> --all        # run all ready tasks
  oms-work.py <project-slug> --dry-run    # show plan without executing
  oms-work.py <project-slug> TASK-NNN     # run specific task

Each task gets its own git worktree (branch: oms-work/task-nnn).
Pass → auto-merge to main + remove worktree.
Fail → leave worktree open for review + notify Discord.
Always posts final task status to Discord (CLI or Discord trigger).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / '.claude' / 'bin'))
import oms_discord as discord  # noqa: E402  # type: ignore[import]

CONFIG            = Path.home() / '.claude' / 'oms-config.json'
CLAUDE            = Path.home() / '.local' / 'bin' / 'claude'
TEMPLATE          = Path.home() / '.claude' / 'agents' / 'oms-work' / 'cleared-queue-template.md'
ELAB_LESSONS      = Path.home() / '.claude' / 'agents' / 'task-elaboration' / 'lessons.md'
BUDGET_FILE       = Path.home() / '.claude' / 'oms-budget.json'
PENDING_RESUMES   = Path.home() / '.claude' / 'oms-pending-resumes.json'

_RATE_LIMIT_PATTERNS = (
    'rate limit', 'rate_limit', 'usage limit', 'claude max',
    'overloaded', '429', '529', 'exceeded', 'quota',
)


def _is_rate_limited(text: str) -> bool:
    low = text.lower()
    return any(p in low for p in _RATE_LIMIT_PATTERNS)


def _rate_limit_reset_iso() -> str:
    import datetime as _dt
    try:
        if BUDGET_FILE.exists():
            b = json.loads(BUDGET_FILE.read_text())
            start_raw = b.get('current_session_start', '')
            window_h = b.get('session_window_hours', 5)
            if start_raw:
                ss = _dt.datetime.fromisoformat(start_raw)
                if ss.tzinfo is None:
                    ss = ss.replace(tzinfo=_dt.timezone.utc)
                reset = ss + _dt.timedelta(hours=window_h)
                now = _dt.datetime.now(_dt.timezone.utc)
                if reset <= now:
                    reset = now + _dt.timedelta(minutes=5)
                return reset.isoformat()
    except Exception:
        pass
    import datetime as _dt2
    return (_dt2.datetime.now(_dt2.timezone.utc) + _dt2.timedelta(hours=5)).isoformat()


def _update_budget(cost_usd: float) -> None:
    """Add task cost to current session + week spend in oms-budget.json."""
    import datetime as _dt
    if cost_usd <= 0:
        return
    try:
        data: dict = json.loads(BUDGET_FILE.read_text()) if BUDGET_FILE.exists() else {}
        now = _dt.datetime.now(_dt.timezone.utc)

        # Reset week if 7+ days elapsed
        week_start_raw = data.get('current_week_start', '')
        if week_start_raw:
            ws = _dt.datetime.fromisoformat(week_start_raw)
            if ws.tzinfo is None:
                ws = ws.replace(tzinfo=_dt.timezone.utc)
            if (now - ws).days >= 7:
                data['current_week_start'] = now.isoformat()
                data['current_week_spend_usd'] = 0.0
        else:
            data['current_week_start'] = now.isoformat()
            data['current_week_spend_usd'] = 0.0

        # Reset session if window expired
        session_start_raw = data.get('current_session_start', '')
        window_h = data.get('session_window_hours', 5)
        if session_start_raw:
            ss = _dt.datetime.fromisoformat(session_start_raw)
            if ss.tzinfo is None:
                ss = ss.replace(tzinfo=_dt.timezone.utc)
            if (now - ss) > _dt.timedelta(hours=window_h):
                data['current_session_start'] = now.isoformat()
                data['current_session_spend_usd'] = 0.0
        else:
            data['current_session_start'] = now.isoformat()
            data['current_session_spend_usd'] = 0.0

        data['current_week_spend_usd'] = round(data.get('current_week_spend_usd', 0) + cost_usd, 6)
        data['current_session_spend_usd'] = round(data.get('current_session_spend_usd', 0) + cost_usd, 6)
        data['last_updated'] = now.isoformat()

        tmp = str(BUDGET_FILE) + '.tmp'
        Path(tmp).write_text(json.dumps(data, indent=2))
        Path(tmp).replace(BUDGET_FILE)
    except Exception as exc:
        print(f'[oms-work] failed to update budget: {exc}', file=sys.stderr)


def write_task_metrics(
    queue_path: Path,
    project_path: Path,
    task_id: str,
    cost_usd: float,
    validator_log: list[tuple[str, bool, bool]],  # (name, first_pass, final_pass)
    passed: bool,
    *,
    slug: str = '',
    title: str = '',
    milestone: str = '',
    task_type: str = '',
    fail_at: str | None = None,
    notes: str = '',
    validator_details: dict[str, str] | None = None,  # name → full reason string
) -> None:
    """
    Write cost + quality metrics into:
      - cleared-queue.md (compact inline fields)
      - <project>/.claude/oms-costs.json (project array)
      - <project>/.claude/oms-metrics.json (same schema as SKILL path)
      - ~/.claude/oms-costs/SLUG-TASK-NNN.json (individual file, SKILL-compatible)
      - ~/.claude/oms-budget.json (session + week spend)

    validator_log entries: (validator_name, passed_first_attempt, passed_final)
    validator_details: full reason strings per validator (optional)
    """
    import datetime as _dt

    # Build compact validator summary: dev✓ qa↺✓ em✗
    parts = []
    first_pass_all = True
    for name, first_ok, final_ok in validator_log:
        if first_ok:
            parts.append(f'{name}✓')
        elif final_ok:
            parts.append(f'{name}↺✓')
            first_pass_all = False
        else:
            parts.append(f'{name}✗')
            first_pass_all = False
    validator_str = ' '.join(parts) if parts else 'none'
    first_pass_str = 'yes' if first_pass_all else 'no'

    # Build validator dict (full reasons) — matches SKILL path format
    vdict: dict[str, str] = {}
    if validator_details:
        vdict = validator_details
    else:
        for name, first_ok, final_ok in validator_log:
            vdict[name] = 'PASS' if final_ok else 'FAIL'

    now_iso = _dt.datetime.now(_dt.timezone.utc).isoformat() + 'Z'

    # 1. Update cleared-queue.md — compact inline fields
    def replacer(m: re.Match) -> str:
        block = m.group(0)
        for field, value in [
            ('Cost', f'${cost_usd:.4f}'),
            ('Validators', validator_str),
            ('First-pass', first_pass_str),
        ]:
            marker = f'**{field}:**'
            if marker in block:
                block = re.sub(rf'(- \*\*{field}:\*\*) .+', rf'\1 {value}', block)
            else:
                block = block.rstrip('\n') + f'\n- **{field}:** {value}\n'
        return block

    try:
        pattern = rf'(## {re.escape(task_id)} — .+?)(?=\n## TASK-|\Z)'
        queue_path.write_text(
            re.sub(pattern, replacer, queue_path.read_text(), flags=re.DOTALL)
        )
    except Exception as exc:
        print(f'[oms-work] failed to write metrics to queue: {exc}', file=sys.stderr)

    # 2. Append to per-project oms-costs.json (legacy array format)
    costs_file = project_path / '.claude' / 'oms-costs.json'
    try:
        records: list = []
        if costs_file.exists():
            records = json.loads(costs_file.read_text())
        records.append({
            'task_id': task_id,
            'cost_usd': round(cost_usd, 6),
            'passed': passed,
            'first_pass': first_pass_all,
            'validators': validator_str,
            'ts': now_iso,
        })
        costs_file.write_text(json.dumps(records, indent=2))
    except Exception as exc:
        print(f'[oms-work] failed to write oms-costs.json: {exc}', file=sys.stderr)

    # 3. Write individual file — SKILL-compatible schema
    if slug:
        ind_dir = Path.home() / '.claude' / 'oms-costs'
        ind_dir.mkdir(exist_ok=True)
        ind_file = ind_dir / f'{slug}-{task_id}.json'
        try:
            ind_file.write_text(json.dumps({
                'task_id': task_id,
                'slug': slug,
                'title': title,
                'type': task_type,
                'milestone': milestone,
                'date': now_iso,
                'passed': passed,
                'fail_at': fail_at,
                'validators': vdict,
                'cost_usd': round(cost_usd, 6),
                'total_usd': round(cost_usd, 6),
                'first_pass': first_pass_all,
                'notes': notes,
            }, indent=2))
        except Exception as exc:
            print(f'[oms-work] failed to write individual cost file: {exc}', file=sys.stderr)

    # 4. Append to oms-metrics.json — same schema as SKILL path
    metrics_file = project_path / '.claude' / 'oms-metrics.json'
    try:
        rows: list = []
        if metrics_file.exists():
            rows = json.loads(metrics_file.read_text())
        rows.append({
            'task_id': task_id,
            'slug': slug,
            'title': title,
            'date': now_iso,
            'passed': passed,
            'fail_at': fail_at,
            'cost_usd': round(cost_usd, 6),
            'validators': vdict,
            'milestone': milestone,
            'type': task_type,
            'first_pass': first_pass_all,
            'notes': notes,
        })
        metrics_file.write_text(json.dumps(rows, indent=2))
    except Exception as exc:
        print(f'[oms-work] failed to write oms-metrics.json: {exc}', file=sys.stderr)

    # 5. Update budget
    _update_budget(cost_usd)


def _write_pending_resume(slug: str, channel_id: str) -> None:
    reset_iso = _rate_limit_reset_iso()
    try:
        data: dict = {}
        if PENDING_RESUMES.exists():
            data = json.loads(PENDING_RESUMES.read_text())
        data[slug] = {'channel_id': channel_id, 'reset_at': reset_iso}
        PENDING_RESUMES.write_text(json.dumps(data))
        print(f'[oms-work] rate limited — scheduled resume at {reset_iso}', file=sys.stderr)
    except Exception as exc:
        print(f'[oms-work] failed to write pending resume: {exc}', file=sys.stderr)

VALIDATOR_ROLE: dict[str, str] = {
    'dev':        'Review for correctness, completeness, and code quality against acceptance criteria.',
    'qa':         'Test each acceptance criterion. Identify any failing cases or edge cases.',
    'em':         'Final approval: spec met, all criteria passed, ready to merge.',
    'researcher': 'Evaluate methodology soundness and finding completeness.',
    'cro':        'Validate findings are rigorous, aligned with research question, and actionable.',
    'cpo':        'Confirm output creates clear product direction or actionable roadmap items.',
    'cto':        'Review for architectural soundness. Name any blocking technical risk.',
}

SPEC_FAILURE_SIGNALS = [
    'ambiguous', 'unclear', 'missing scenario', 'incomplete', 'not specified',
    'criteria', 'undefined', 'no test', 'edge case', 'not covered',
    'missing artifact', 'wrong file', 'wrong export', 'path not found',
]


# ── Spec failure logging ──────────────────────────────────────────────────────

def log_spec_failure(task: dict, validator: str, reason: str) -> None:
    if not any(s in reason.lower() for s in SPEC_FAILURE_SIGNALS):
        return
    lesson = (f'- [{task["id"]}] {validator} FAIL — {reason[:200].strip()}'
              f' | Spec: "{task["spec"][:120]}"')
    try:
        with ELAB_LESSONS.open('a') as f:
            f.write(lesson + '\n')
    except OSError:
        pass


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
        scenarios_raw = f.get('Scenarios', f.get('Acceptance', ''))
        tasks.append({
            'id':         m.group(1),
            'title':      m.group(2).strip(),
            'status':     f.get('Status', 'queued').strip().lower(),
            'type':       f.get('Type', 'impl').strip().lower(),
            'milestone':  f.get('Milestone', 'none').strip(),
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
            'model_hint': f.get('Model-hint', '').strip().lower() or None,
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


# ── Cross-milestone dependency scan ───────────────────────────────────────────

def _produces_paths(produces: str) -> list[str]:
    """Extract file paths from a Produces field value."""
    paths = []
    for part in produces.split('|'):
        part = part.strip()
        path = part.split(' — ')[0].strip() if ' — ' in part else part
        if path and path.lower() != 'none':
            paths.append(path)
    return paths


def _contract_still_holds(project_path: Path, produces: str,
                           context_refs: list[str]) -> tuple[bool, str]:
    """Check that exports named in Produces still exist in the actual file.
    Only checks files referenced in context_refs.
    Returns (still_valid, detail)."""
    for part in produces.split('|'):
        part = part.strip()
        if ' — exports: ' not in part:
            continue
        file_str, exports_str = part.split(' — exports: ', 1)
        file_path = file_str.strip()
        if not any(file_path in ctx or ctx in file_path for ctx in context_refs):
            continue
        full = project_path / file_path
        if not full.exists():
            return False, f'{file_path} no longer exists'
        content = full.read_text(errors='replace')
        missing = [e.strip() for e in exports_str.split(',')
                   if e.strip() and e.strip() not in content]
        if missing:
            return False, f'{file_path} — missing exports: {", ".join(missing)}'
    return True, 'contract satisfied'


def flag_downstream_tasks(queue_path: Path, project_path: Path,
                          completed: dict, channel_id: str) -> None:
    """After an impl task completes, check queued tasks in OTHER milestones
    whose Context references this task's Produces.
    Auto-confirms if contract still holds — only flags when interface actually changed."""
    if completed['type'] == 'research':
        return
    produces = completed.get('produces', 'none')
    paths = _produces_paths(produces)
    if not paths:
        return

    tasks = parse_queue(queue_path)
    for task in tasks:
        if task['status'] != 'queued':
            continue
        if task['milestone'] == completed['milestone']:
            continue
        if not any(p in ctx or ctx in p
                   for p in paths for ctx in task['context']):
            continue
        # Contract check — no CEO input needed if exports still exist
        valid, detail = _contract_still_holds(project_path, produces, task['context'])
        if valid:
            print(f'[oms-work] ✓ {task["id"]} contract check passed '
                  f'({completed["id"]} Produces unchanged)', flush=True)
            continue  # task stays queued, no action needed
        # Interface actually changed — flag for CEO
        note = f'upstream {completed["id"]} interface changed: {detail}'
        update_status(queue_path, task['id'], 'needs-review', note)
        msg = (f'⚠ **{task["id"]}** — {task["title"]} `needs-review`\n'
               f'> {completed["id"]} ({completed["milestone"]}) changed its interface: {detail}\n'
               f'> Re-spec this task before running.')
        discord.post_message(channel_id, msg)
        print(f'[oms-work] ⚠ {task["id"]} → needs-review: {detail}', flush=True)


# ── Worktree + merge ──────────────────────────────────────────────────────────

def _wt_path(project_path: Path, task_id: str) -> Path:
    return project_path / '.claude' / 'worktrees' / task_id


def create_worktree(project_path: Path, task_id: str) -> tuple[Path, str]:
    branch = f'oms-work/{task_id.lower()}'
    wt = _wt_path(project_path, task_id)
    wt.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(['git', 'worktree', 'add', str(wt), '-b', branch, 'HEAD'],
                       capture_output=True, text=True, cwd=project_path)
    if r.returncode != 0:
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


def merge_to_main(project_path: Path, branch: str, task_id: str, title: str) -> tuple[bool, str]:
    """Merge task branch to main. Returns (merged, notes)."""
    # Only merge if working tree is clean
    gs = subprocess.run(['git', 'status', '--porcelain'],
                        capture_output=True, text=True, cwd=project_path)
    if gs.stdout.strip():
        return False, f'branch {branch} ready — merge manually (working tree not clean)'

    cur = subprocess.run(['git', 'branch', '--show-current'],
                         capture_output=True, text=True, cwd=project_path)
    if cur.stdout.strip() != 'main':
        subprocess.run(['git', 'checkout', 'main'], capture_output=True, cwd=project_path)

    r = subprocess.run(
        ['git', 'merge', '--no-ff', branch, '-m', f'oms-work: {task_id} — {title}'],
        capture_output=True, text=True, cwd=project_path,
    )
    if r.returncode != 0:
        subprocess.run(['git', 'merge', '--abort'], cwd=project_path, capture_output=True)
        return False, f'branch {branch} ready — merge conflict, merge manually'

    subprocess.run(['git', 'branch', '-d', branch], capture_output=True, cwd=project_path)
    return True, 'merged to main'


# ── Claude invocation ─────────────────────────────────────────────────────────

def run_claude(prompt: str, cwd: Path, model: str, allow_writes: bool = False) -> tuple[str, int, str, float]:
    """Returns (content, returncode, stderr, cost_usd). stderr non-empty only on failure."""
    args = [str(CLAUDE), '--print', '--output-format', 'json', '--model', model]
    if allow_writes:
        args.append('--dangerously-skip-permissions')
    # Unset CLAUDECODE + related vars — prevents subprocess claude blocking for interactive input
    # when oms-work.py is invoked from within a Claude Code session
    env = {k: v for k, v in __import__('os').environ.items()
           if k not in ('CLAUDECODE', 'CLAUDE_CODE', 'ANTHROPIC_CLAUDE_CODE')}
    # Prompt via stdin — avoids ARG_MAX limits and shell-escaping bugs in generated code
    r = subprocess.run(args, input=prompt, capture_output=True, text=True, cwd=cwd, timeout=600, env=env)
    if r.returncode != 0:
        print(f'[oms-work] claude exit {r.returncode}: {r.stderr[:200]}', file=sys.stderr)
        return '', r.returncode, r.stderr, 0.0
    try:
        data = json.loads(r.stdout)
        cost = float(data.get('total_cost_usd') or 0.0)
        return data.get('result') or data.get('content') or '', 0, '', cost
    except Exception:
        return r.stdout.strip(), 0, '', 0.0


LLM_ROUTE = Path.home() / '.claude' / 'bin' / 'llm-route.sh'

MODEL_MAP: dict[str | None, str] = {
    'haiku':  'claude-haiku-4-5-20251001',
    'sonnet': 'claude-sonnet-4-6',
    'opus':   'claude-opus-4-6',
}


def run_llm_route(model: str, prompt: str, cwd: Path) -> tuple[str, int]:
    """Route to any LLM via llm-route.sh. Prompt passed via stdin — no arg/escaping limits."""
    r = subprocess.run(
        [str(LLM_ROUTE), model],
        input=prompt,
        capture_output=True, text=True, cwd=cwd, timeout=600,
    )
    if r.returncode != 0:
        print(f'[oms-work] llm-route exit {r.returncode}: {r.stderr[:200]}', file=sys.stderr)
    return r.stdout.strip(), r.returncode


def resolve_model(task: dict) -> tuple[str, bool]:
    """Return (model_or_route, is_external) based on Model-hint field."""
    hint = task.get('model_hint')
    if hint in ('qwen', 'qwen36'):
        return hint, True
    if hint in MODEL_MAP:
        return MODEL_MAP[hint], False
    return MODEL_MAP['sonnet'], False


# ── Execution + validation ────────────────────────────────────────────────────

def exec_prompt(task: dict, wt: Path) -> str:
    scenarios = '\n'.join(f'- {s}' for s in task['scenarios'])
    artifacts = '\n'.join(f'- {a}' for a in task['artifacts'])
    produces  = task['produces']

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

    action = ('Write findings to logs/research/{id}.md. '
              'Include ≥3 evidence-backed findings, each with a testable prediction.'
              ).format(id=task['id']) if task['type'] == 'research' \
             else 'Make all required file changes to satisfy every scenario.'

    return (f"OMS work task ({task['id']}): {task['spec']}\n\n"
            f"## Behavioral Scenarios\n{scenarios}"
            f"{artifact_section}{produces_section}{ctx_section}\n\n"
            f"{action}\n\nOutput a 1–2 sentence summary when complete.")


def validate_step(validator: str, task: dict, summary: str, cwd: Path) -> tuple[bool, str, float]:
    """Returns (passed, reason, cost_usd)."""
    role = VALIDATOR_ROLE.get(validator.lower(),
                               f'Validate as {validator}: confirm all scenarios are met.')
    scenarios = '\n'.join(f'- {s}' for s in task['scenarios'])
    artifacts = '\n'.join(f'- {a}' for a in task['artifacts'])
    artifact_section = f'\n\nRequired artifacts:\n{artifacts}' if artifacts else ''
    prompt = (f"Task ({task['id']}): {task['spec']}\n\nScenarios:\n{scenarios}{artifact_section}\n\n"
              f"Work summary: {summary}\n\nYour role: {role}\n\n"
              "Output EXACTLY: PASS — [reason]  OR  FAIL — [reason]. Nothing else.")
    out, _, _err, cost = run_claude(prompt, cwd, model='claude-haiku-4-5-20251001')
    return out.strip().upper().startswith('PASS'), out.strip(), cost


def execute_task(task: dict, project_path: Path,
                 channel_id: str, threads_file: Path,
                 queue_path: Path, dry_run: bool, slug: str = '') -> tuple[bool, str]:
    print(f'\n[oms-work] ▶ {task["id"]} — {task["title"]}', flush=True)
    if dry_run:
        print(f'[oms-work]   DRY RUN: {task["spec"]}')
        return True, 'dry-run'

    if not task.get('model_hint'):
        notes = 'CTO-STOP: Model-hint missing — task was not properly elaborated. Re-run elaboration.'
        discord.notify_task(channel_id, threads_file, task['milestone'],
                            task['id'], task['title'], False, notes)
        return False, notes

    wt, branch = create_worktree(project_path, task['id'])
    task_cost = 0.0
    # validator_log: (name, passed_first_attempt, passed_final)
    validator_log: list[tuple[str, bool, bool]] = []
    validator_details: dict[str, str] = {}  # name → full reason string
    task_notes = ''
    task_fail_at: str | None = None
    try:
        model, is_external = resolve_model(task)
        print(f'[oms-work]   model: {model} ({"external" if is_external else "subscription"})', flush=True)
        if is_external:
            work_out, code = run_llm_route(model, exec_prompt(task, wt), wt)
            run_stderr = ''
        else:
            work_out, code, run_stderr, exec_cost = run_claude(exec_prompt(task, wt), wt, model, allow_writes=True)
            task_cost += exec_cost
        if code != 0:
            remove_worktree(project_path, task['id'])
            if slug and _is_rate_limited(run_stderr):
                _write_pending_resume(slug, channel_id)
                notes = f'RATE-LIMITED: auto-resume scheduled — {task["id"]} will retry when window resets'
            else:
                notes = f'CTO-STOP: claude execution failed (exit {code})'
            discord.notify_task(channel_id, threads_file, task['milestone'],
                                task['id'], task['title'], False, notes)
            return False, notes

        summary = work_out[:300].replace('\n', ' ').strip()
        task_notes = summary
        print(f'[oms-work]   exec: {summary[:120]}', flush=True)

        if task['type'] != 'research':
            gs = subprocess.run(['git', 'status', '--porcelain'],
                                capture_output=True, text=True, cwd=wt)
            if not gs.stdout.strip():
                remove_worktree(project_path, task['id'])
                task_notes = 'CTO-STOP: hallucination — no files changed in worktree'
                task_fail_at = 'hallucination'
                write_task_metrics(queue_path, project_path, task['id'], task_cost, validator_log,
                                   passed=False, slug=slug, title=task['title'],
                                   milestone=task['milestone'], task_type=task['type'],
                                   fail_at=task_fail_at, notes=task_notes,
                                   validator_details=validator_details)
                discord.notify_task(channel_id, threads_file, task['milestone'],
                                    task['id'], task['title'], False, task_notes)
                return False, task_notes

        research_retried = False
        for validator in task['validation']:
            passed, reason, val_cost = validate_step(validator, task, summary, wt)
            task_cost += val_cost
            first_pass = passed
            print(f'[oms-work]   {"✓" if passed else "✗"} {validator}: {reason[:100]}', flush=True)
            if not passed:
                if (validator == 'cro' and task['type'] == 'research'
                        and task.get('model_hint') == 'qwen36' and not research_retried):
                    print('[oms-work]   research quality insufficient — retrying with sonnet', flush=True)
                    research_retried = True
                    work_out, code, _, retry_cost = run_claude(
                        exec_prompt(task, wt), wt, 'claude-sonnet-4-6', allow_writes=True)
                    task_cost += retry_cost
                    if code == 0:
                        summary = work_out[:300].replace('\n', ' ').strip()
                        passed, reason, val_cost = validate_step(validator, task, summary, wt)
                        task_cost += val_cost
                        print(f'[oms-work]   {"✓" if passed else "✗"} {validator} (sonnet retry): {reason[:100]}', flush=True)
                if not passed:
                    validator_log.append((validator, False, False))
                    validator_details[validator] = reason
                    task_fail_at = validator
                    task_notes = f'FAIL ({validator}): {reason[:200]}'
                    log_spec_failure(task, validator, reason)
                    write_task_metrics(queue_path, project_path, task['id'], task_cost, validator_log,
                                       passed=False, slug=slug, title=task['title'],
                                       milestone=task['milestone'], task_type=task['type'],
                                       fail_at=task_fail_at, notes=task_notes,
                                       validator_details=validator_details)
                    stop_type = 'CTO-STOP' if validator == 'cto' else 'FAIL'
                    notes = f'{stop_type} ({validator}): {reason[:200]} | branch: {branch}'
                    discord.notify_task(channel_id, threads_file, task['milestone'],
                                        task['id'], task['title'], False, notes)
                    return False, notes
            validator_log.append((validator, first_pass, passed))
            validator_details[validator] = reason

        for cmd in task['verify']:
            vr = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                cwd=wt, timeout=120)
            print(f'[oms-work]   {"✓" if vr.returncode == 0 else "✗"} verify `{cmd[:60]}`', flush=True)
            if vr.returncode != 0:
                output = (vr.stdout + vr.stderr)[-300:].strip()
                task_fail_at = f'verify:{cmd[:60]}'
                task_notes = f'FAIL (verify `{cmd}`): {output}'
                write_task_metrics(queue_path, project_path, task['id'], task_cost, validator_log,
                                   passed=False, slug=slug, title=task['title'],
                                   milestone=task['milestone'], task_type=task['type'],
                                   fail_at=task_fail_at, notes=task_notes,
                                   validator_details=validator_details)
                notes = f'{task_notes} | branch: {branch}'
                discord.notify_task(channel_id, threads_file, task['milestone'],
                                    task['id'], task['title'], False, notes)
                return False, notes

        commit_worktree(wt, task['id'], task['title'])
        remove_worktree(project_path, task['id'])

        task_notes = summary
        write_task_metrics(queue_path, project_path, task['id'], task_cost, validator_log,
                           passed=True, slug=slug, title=task['title'],
                           milestone=task['milestone'], task_type=task['type'],
                           fail_at=None, notes=task_notes,
                           validator_details=validator_details)
        _, merge_notes = merge_to_main(project_path, branch, task['id'], task['title'])
        notes = f'{summary[:180]} | {merge_notes} | cost: ${task_cost:.4f}'
        print(f'[oms-work]   cost: ${task_cost:.4f}', flush=True)
        discord.notify_task(channel_id, threads_file, task['milestone'],
                            task['id'], task['title'], True, notes)
        flag_downstream_tasks(queue_path, project_path, task, channel_id)
        return True, notes

    except Exception as e:
        remove_worktree(project_path, task['id'])
        task_fail_at = 'exception'
        task_notes = f'CTO-STOP: exception — {e}'
        write_task_metrics(queue_path, project_path, task['id'], task_cost, validator_log,
                           passed=False, slug=slug, title=task['title'],
                           milestone=task['milestone'], task_type=task['type'],
                           fail_at=task_fail_at, notes=task_notes,
                           validator_details=validator_details)
        notes = task_notes
        discord.notify_task(channel_id, threads_file, task['milestone'],
                            task['id'], task['title'], False, notes)
        return False, notes


# ── Milestone gate ───────────────────────────────────────────────────────────

def detect_e2e_cmd(project_path: Path) -> str | None:
    """Return the E2E test command if playwright is configured in this project.
    Deprecated: use detect_e2e() which also returns the correct cwd."""
    cmd, _ = detect_e2e(project_path)
    return cmd


def detect_e2e(project_path: Path) -> tuple[str, Path] | tuple[None, None]:
    """Return (e2e_cmd, cwd) where cwd is the directory containing playwright.config.ts.
    Searches project root first, then common monorepo sub-packages (apps/*/,  packages/*/).
    Returns (None, None) if playwright is not configured anywhere."""
    candidates: list[Path] = [project_path]
    # Monorepo sub-packages — check apps/* and packages/*
    for subdir in ('apps', 'packages'):
        parent = project_path / subdir
        if parent.is_dir():
            candidates.extend(sorted(parent.iterdir()))

    for cwd in candidates:
        if not cwd.is_dir():
            continue
        if (cwd / 'playwright.config.ts').exists() or (cwd / 'playwright.config.js').exists():
            # Determine package manager from lock file (check cwd then root)
            if (cwd / 'pnpm-lock.yaml').exists() or (project_path / 'pnpm-lock.yaml').exists():
                return 'pnpm exec playwright test', cwd
            if (cwd / 'bun.lockb').exists() or (project_path / 'bun.lockb').exists():
                return 'bunx playwright test', cwd
            return 'npx playwright test', cwd
    return None, None




def _queue_e2e_setup_task(project_path: Path, milestone: str) -> None:
    """Append a playwright E2E setup task to cleared-queue.md if not already present."""
    queue_path = project_path / '.claude' / 'cleared-queue.md'
    if not queue_path.exists():
        return
    content = queue_path.read_text()
    if 'TASK-e2e-setup' in content or 'playwright' in content.lower():
        return  # already queued or configured
    task_block = (
        '\n## TASK-e2e-setup — Setup Playwright E2E testing\n'
        '- **Status:** queued\n'
        f'- **Milestone:** {milestone}\n'
        '- **Type:** impl\n'
        '- **Spec:** The project SHALL have a Playwright E2E suite with specs covering all '
        'user-facing flows, each with 5 test categories and page.screenshot() calls.\n'
        '- **Artifacts:** playwright.config.ts | e2e/\n'
        '- **Verify:** pnpm exec playwright test\n'
        '- **Validation:** dev → qa → em\n'
        '- **Model-hint:** sonnet\n'
        '- **Depends:** none\n'
    )
    queue_path.write_text(content + task_block)
    print('[oms-work] Added TASK-e2e-setup to queue', flush=True)


def run_milestone_gate(done_tasks: list[dict], project_path: Path,
                       channel_id: str, threads_file: Path) -> bool:
    """Run all Verify commands + full E2E suite on main. Called after --all completes."""
    verify_cmds: list[str] = []
    seen: set[str] = set()
    milestones: set[str] = set()
    for task in done_tasks:
        if task.get('milestone'):
            milestones.add(task['milestone'])
        for cmd in task.get('verify', []):
            if cmd not in seen:
                verify_cmds.append(cmd)
                seen.add(cmd)

    e2e_cmd, e2e_cwd = detect_e2e(project_path)
    # e2e_cwd is the directory containing playwright.config.ts (may be a sub-package like apps/web/)
    # Fall back to project_path if not detected (keeps verify_cmds running correctly)
    e2e_cwd = e2e_cwd or project_path

    # Hard-fail if E2E is not found for a project with UI artifacts.
    # Previously this silently queued a setup task and continued — that masked the M3 gate being
    # a no-op (detect_e2e_cmd only looked at repo root; playwright.config.ts was in apps/web/).
    if not e2e_cmd:
        ui_tasks = [t for t in done_tasks
                    if any(ext in ' '.join(t.get('artifacts', []))
                           for ext in ('.tsx', '.jsx', '.html', '.css', 'page.', 'route.'))]
        if ui_tasks:
            # HARD FAIL — milestone gate must not pass without E2E on a UI project
            msg = ('⛔ **Milestone gate BLOCKED** — playwright not found.\n'
                   'E2E is required for UI milestones. Check that `playwright.config.ts` exists '
                   'under the project root or a sub-package (apps/*, packages/*).\n'
                   'Fix: ensure playwright is installed and `detect_e2e()` can locate the config.')
            thread_id = discord.get_or_create_thread(channel_id, threads_file,
                                                     next(iter(milestones), 'current'))
            if thread_id:
                discord.post_to_thread(thread_id, msg)
            print('[oms-work] ⛔ BLOCKED — playwright not found; milestone gate cannot pass without E2E',
                  flush=True)
            return False  # gate fails — no milestone credit without E2E

    if not verify_cmds and not e2e_cmd:
        print('[oms-work] Milestone gate: no verify commands or E2E — skip (non-UI milestone)', flush=True)
        return True

    milestone = next(iter(milestones)) if len(milestones) == 1 else 'multi-milestone'
    total = len(verify_cmds) + (1 if e2e_cmd else 0)
    print(f'\n[oms-work] ── Milestone gate ({total} check(s) on main) ──', flush=True)
    if e2e_cmd:
        print(f'[oms-work]   E2E cwd: {e2e_cwd}', flush=True)

    failures: list[str] = []

    # 1. Per-task Verify commands (unit tests, lint, type checks)
    for cmd in verify_cmds:
        vr = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                            cwd=project_path, timeout=300)
        ok = vr.returncode == 0
        print(f'[oms-work]   {"✓" if ok else "✗"} verify: {cmd[:70]}', flush=True)
        if not ok:
            tail = (vr.stdout + vr.stderr)[-400:].strip()
            failures.append(f'`{cmd}`: {tail[:200]}')

    # 2. Full E2E suite (if playwright configured)
    e2e_ok = True
    if e2e_cmd:
        # Clear browse per-task screenshots before E2E runs — only Playwright output should remain
        # Use e2e_cwd so we clear the correct qa/screenshots/ (may be apps/web/qa/screenshots/)
        shots_dir = e2e_cwd / 'qa' / 'screenshots'
        if shots_dir.exists():
            for f in shots_dir.glob('*.png'):
                f.unlink(missing_ok=True)
            print(f'[oms-work]   cleared {shots_dir.relative_to(project_path)} (browse task screenshots)', flush=True)

        print(f'[oms-work]   running E2E suite: {e2e_cmd}', flush=True)
        er = subprocess.run(e2e_cmd, shell=True, capture_output=True, text=True,
                            cwd=e2e_cwd, timeout=600)
        e2e_ok = er.returncode == 0
        print(f'[oms-work]   {"✓" if e2e_ok else "✗"} E2E suite', flush=True)
        if not e2e_ok:
            tail = (er.stdout + er.stderr)[-600:].strip()
            failures.append(f'E2E (`{e2e_cmd}`): {tail[:300]}')

    passed = not failures
    icon = '✅' if passed else '⚠️'
    status = ('unit + E2E pass' if e2e_cmd else 'unit checks pass') if passed \
             else f'{len(failures)} check(s) failed on main'
    msg = f'{icon} **Milestone gate** `{milestone}` — {status}'
    if failures:
        msg += '\n' + '\n'.join(f'> {f[:150]}' for f in failures[:3])

    thread_id = discord.get_or_create_thread(channel_id, threads_file, milestone)
    if thread_id:
        discord.post_to_thread(thread_id, msg)
    else:
        discord.post_message(channel_id, msg)

    # Archive + post Playwright screenshots to milestone thread
    if thread_id and e2e_cmd:
        screenshots = _collect_media(e2e_cwd, passed)
        if screenshots:
            # Archive to qa/milestones/[milestone]/ under e2e_cwd (sub-package) as permanent record
            archive_dir = e2e_cwd / 'qa' / 'milestones' / milestone.replace(' ', '-').lower()
            archive_dir.mkdir(parents=True, exist_ok=True)
            for shot in screenshots:
                dest = archive_dir / shot.name
                dest.write_bytes(shot.read_bytes())
            rel = archive_dir.relative_to(project_path)
            print(f'[oms-work]   archived {len(screenshots)} screenshot(s) → {rel}', flush=True)

            # Post all to Discord (batched — no cap)
            label = '🖼 Visual QA' if passed else '⚠️ E2E failure screenshots'
            discord.post_media_batched(thread_id, f'{label} — `{milestone}`', screenshots)

    if not passed:
        print(f'[oms-work] ⚠ Milestone gate FAILED — fix before CEO brief', flush=True)
        for f in failures:
            print(f'[oms-work]   {f[:160]}', flush=True)

    return passed


def _collect_media(project_path: Path, passed: bool) -> list[Path]:
    """Collect Playwright page.screenshot() output from qa/screenshots/ only.
    Browse per-task screenshots are cleared before E2E runs — only Playwright output remains.
    Falls back to test-results/ on failure."""
    shots_dir = project_path / 'qa' / 'screenshots'
    if shots_dir.exists():
        screenshots = sorted(shots_dir.glob('*.png'), key=lambda p: p.stat().st_mtime)
        if screenshots:
            return screenshots
    # Fallback on failure: playwright test-results artifacts
    if not passed:
        results_dir = project_path / 'test-results'
        if results_dir.exists():
            return sorted(results_dir.glob('**/*.png'), key=lambda p: p.stat().st_mtime)
    return []


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
    channel_id   = proj.get('channel_id', '')
    threads_file = project_path / '.claude' / 'oms-work-threads.json'
    queue_path   = project_path / '.claude' / 'cleared-queue.md'

    if not queue_path.exists() and TEMPLATE.exists():
        queue_path.write_text(TEMPLATE.read_text())
        print(f'[oms-work] Created queue at {queue_path}')

    results: list[tuple[str, str, bool, dict]] = []

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
        passed, notes = execute_task(task, project_path, channel_id, threads_file, queue_path, dry_run, slug=slug)
        final = 'done' if passed else 'cto-stop'
        update_status(queue_path, task['id'], final, notes)
        results.append((task['id'], task['title'], passed, task))

        if not run_all or (not passed and ('CTO-STOP' in notes or 'RATE-LIMITED' in notes)):
            break

    done_r  = [(i, t) for i, t, p, _  in results if p]
    done_tk = [tk      for _, _, p, tk in results if p]
    stops   = [(i, t)  for i, t, p, _  in results if not p]

    # Milestone gate — run all Verify commands on main after --all completes
    gate_passed = True
    if run_all and done_tk:
        gate_passed = run_milestone_gate(done_tk, project_path, channel_id, threads_file)

    lines = ['## OMS Work']
    for i, t in done_r:
        lines.append(f'✓ {i} — {t}')
    for i, t in stops:
        lines.append(f'⚑ {i} — {t} [cto-stop]')
    if not results:
        lines.append('No tasks ran.')
    if run_all and done_tk:
        lines.append(f'\nMilestone gate: {"PASS" if gate_passed else "FAIL — fix before CEO brief"}')
    print('\n'.join(lines))
    sys.exit(0)


if __name__ == '__main__':
    main()
