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
from __future__ import annotations
import json
import os
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
            data = json.loads(metrics_file.read_text())
            rows = data if isinstance(data, list) else []
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
    args = [str(CLAUDE), '--print', '--bare', '--output-format', 'json', '--model', model]
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
LITELLM_PORT = 4000
LITELLM_URL = f'http://localhost:{LITELLM_PORT}'
LITELLM_KEY = 'sk-litellm-local-dev'

MODEL_MAP: dict[str | None, str] = {
    'haiku':  'claude-haiku-4-5-20251001',
    'sonnet': 'claude-sonnet-4-6',
    'opus':   'claude-opus-4-6',
}

# All models routable via LiteLLM proxy (free OpenRouter tier)
EXTERNAL_MODELS: set[str] = {
    'qwen', 'qwen36', 'qwen-coder',
    'llama', 'gpt-oss', 'nemotron', 'gemma', 'stepfun',
}

# Map short hint names to LiteLLM model IDs
LITELLM_MODEL_MAP: dict[str, str] = {
    'qwen':       'qwen-3.6-plus',
    'qwen36':     'qwen-3.6-plus',
    'qwen-coder': 'qwen-3-coder',
    'llama':      'llama-3.3-70b',
    'gpt-oss':    'gpt-oss-120b',
    'nemotron':   'nemotron-3-super',
    'gemma':      'gemma-3-27b',
    'stepfun':    'stepfun-3.5',
}

# Fallback chains when primary model is rate-limited or unavailable
LITELLM_FALLBACKS: dict[str, list[str]] = {
    'qwen-3.6-plus':   ['qwen-3-coder', 'gpt-oss-120b', 'stepfun-3.5'],
    'qwen-3-coder':    ['qwen-3.6-plus', 'llama-3.3-70b', 'stepfun-3.5'],
    'llama-3.3-70b':   ['gpt-oss-120b', 'nemotron-3-super', 'gemma-3-27b'],
    'gpt-oss-120b':    ['nemotron-3-super', 'llama-3.3-70b', 'qwen-3.6-plus'],
    'gemma-3-27b':     ['llama-3.3-70b', 'stepfun-3.5'],
    'nemotron-3-super': ['gpt-oss-120b', 'llama-3.3-70b'],
    'stepfun-3.5':     ['qwen-3.6-plus', 'llama-3.3-70b'],
}


LITELLM_CONFIG = Path.home() / '.claude' / 'config' / 'llm-router.yaml'
LITELLM_PID_FILE = Path('/tmp/litellm-proxy.pid')
LITELLM_LOG = Path('/tmp/litellm-proxy.log')
OPENROUTER_KEY_FILE = Path.home() / '.config' / 'openrouter' / 'key'


def _litellm_health() -> bool:
    """Quick health check — is LiteLLM responding?"""
    import urllib.request
    try:
        req = urllib.request.Request(f'{LITELLM_URL}/health',
                                     headers={'Authorization': f'Bearer {LITELLM_KEY}'})
        urllib.request.urlopen(req, timeout=3)
        return True
    except Exception:
        return False


def _ensure_litellm() -> bool:
    """Ensure LiteLLM proxy is running. Start it if not."""
    if _litellm_health():
        return True

    # Check if PID file exists and process is alive
    if LITELLM_PID_FILE.exists():
        try:
            pid = int(LITELLM_PID_FILE.read_text().strip())
            os.kill(pid, 0)  # check if alive
            # Process exists but not responding — give it a moment
            import time
            time.sleep(2)
            if _litellm_health():
                return True
        except (ValueError, ProcessLookupError, OSError):
            pass  # stale PID file

    # Start LiteLLM proxy
    if not LITELLM_CONFIG.exists():
        print('[oms-work] LiteLLM config not found — cannot start proxy', file=sys.stderr)
        return False

    env = dict(os.environ)
    if OPENROUTER_KEY_FILE.exists():
        env['OPENROUTER_API_KEY'] = OPENROUTER_KEY_FILE.read_text().strip()

    import shutil
    litellm_bin = shutil.which('litellm')
    if not litellm_bin:
        # Try common locations
        for candidate in [
            Path.home() / '.local/share/mise/installs/python/miniforge3-22.11.1-4/bin/litellm',
            Path.home() / '.local/bin/litellm',
            Path('/usr/local/bin/litellm'),
        ]:
            if candidate.exists():
                litellm_bin = str(candidate)
                break
    if not litellm_bin:
        print('[oms-work] litellm binary not found', file=sys.stderr)
        return False

    print(f'[oms-work] Starting LiteLLM proxy ({litellm_bin})...', flush=True)
    with open(LITELLM_LOG, 'w') as log_f:
        proc = subprocess.Popen(
            [litellm_bin, '--config', str(LITELLM_CONFIG), '--port', str(LITELLM_PORT)],
            stdout=log_f, stderr=log_f, env=env,
            start_new_session=True,  # detach from parent
        )
    LITELLM_PID_FILE.write_text(str(proc.pid))

    # Wait for proxy to be ready (max 15s)
    import time
    for _ in range(30):
        time.sleep(0.5)
        if _litellm_health():
            print('[oms-work] LiteLLM proxy ready', flush=True)
            return True

    print('[oms-work] LiteLLM failed to start after 15s', file=sys.stderr)
    return False


def _call_litellm(model_id: str, prompt: str, timeout_s: int = 360) -> tuple[str, int]:
    """Call LiteLLM proxy directly via HTTP. Returns (content, returncode)."""
    import urllib.request
    payload = json.dumps({
        'model': model_id,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 16000,
    }).encode()
    req = urllib.request.Request(
        f'{LITELLM_URL}/chat/completions',
        data=payload,
        headers={
            'Authorization': f'Bearer {LITELLM_KEY}',
            'Content-Type': 'application/json',
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout_s)
        data = json.loads(resp.read())
        content = (data.get('choices', [{}])[0].get('message', {}).get('content', '') or '').strip()
        if not content:
            return '', 1
        return content, 0
    except Exception as e:
        print(f'[oms-work] LiteLLM call failed ({model_id}): {e}', file=sys.stderr)
        return '', 1


def run_llm_route(model: str, prompt: str, cwd: Path) -> tuple[str, int]:
    """Route to free LLM via LiteLLM proxy (direct HTTP, no claude -p overhead).
    Falls back through chain if primary model fails."""
    model_id = LITELLM_MODEL_MAP.get(model, model)
    chain = [model_id] + LITELLM_FALLBACKS.get(model_id, [])

    if not _ensure_litellm():
        print('[oms-work] LiteLLM proxy not available — falling back to llm-route.sh', file=sys.stderr)
        r = subprocess.run(
            [str(LLM_ROUTE), model], input=prompt,
            capture_output=True, text=True, cwd=cwd, timeout=600,
        )
        return r.stdout.strip(), r.returncode

    for i, mid in enumerate(chain):
        print(f'[oms-work]   trying {mid} ({"primary" if i == 0 else "fallback " + str(i)})', flush=True)
        content, rc = _call_litellm(mid, prompt)
        if rc == 0 and content.strip():
            return content, 0
        print(f'[oms-work]   {mid} failed — {"trying next" if i < len(chain) - 1 else "all exhausted"}', flush=True)

    return '', 1


def resolve_model(task: dict) -> tuple[str, bool]:
    """Return (model_or_route, is_external) based on Model-hint field."""
    hint = task.get('model_hint')
    if hint in EXTERNAL_MODELS:
        return hint, True
    if hint in MODEL_MAP:
        return MODEL_MAP[hint], False
    # Defensive only — validation hook should catch missing hints before execution
    print(f'[oms-work]   WARN: missing Model-hint, defaulting to qwen (free)', flush=True)
    return 'qwen', True


# ── Execution + validation ────────────────────────────────────────────────────

TEST_PATTERNS = ('.test.', '.spec.', '__tests__/', 'test_', '/tests/')

QUALITY_RULES = (
    '\n\n## Code Quality Rules\n'
    '- Max 300 lines per file, max 50 lines per function\n'
    '- No console.log / print debugging in production code\n'
    '- No commented-out code blocks\n'
    '- camelCase for variables/functions, PascalCase for classes, UPPER_SNAKE for constants\n'
    '- Comments explain WHY not WHAT\n'
    '- Always handle errors — no silent swallowing\n'
    '- Prefer async/await over promise chains\n'
    '- Group imports: external → internal → relative\n'
    '- API responses: always { data, error, meta? } shape\n'
    '- TypeScript: define schemas in Zod first, derive types with z.infer<>\n'
    '- Python: define schemas in Pydantic first, use .model_validate() at boundaries\n'
    '- No hardcoded secrets, API keys, or passwords\n'
)

OUTPUT_FMT = (
    '\n\n## Output Format\n'
    'For each file, output:\n'
    '### path/to/file.ext\n'
    '```language\n'
    '<complete file content>\n'
    '```\n'
    'Output ALL files completely. No placeholders, no TODO, no truncation.\n'
)


def _split_artifacts(artifacts: list[str]) -> tuple[list[str], list[str]]:
    """Split artifacts into (test_files, impl_files) by path pattern."""
    tests = [a for a in artifacts if any(p in a for p in TEST_PATTERNS)]
    impl = [a for a in artifacts if a not in tests]
    return tests, impl


def _build_ctx_section(task: dict, wt: Path) -> str:
    ctx_blocks: list[str] = []
    for rel in task['context']:
        full = wt / rel
        if full.exists():
            content = full.read_text(encoding='utf-8', errors='replace')[:3000]
            ctx_blocks.append(f'### {rel}\n```\n{content}\n```')
        else:
            ctx_blocks.append(f'### {rel}\n(not found — create it)')
    return ('\n\n## Context Files\n\n' + '\n\n'.join(ctx_blocks)) if ctx_blocks else ''


def _build_base_prompt(task: dict, wt: Path) -> str:
    """Common prompt parts shared by test_prompt, impl_prompt, and research_prompt."""
    scenarios = '\n'.join(f'- {s}' for s in task['scenarios'])
    produces = task['produces']
    ctx_section = _build_ctx_section(task, wt)
    produces_section = (f'\n\n## Produces (downstream contract)\n{produces}'
                        if produces and produces.lower() != 'none' else '')
    return (f"OMS work task ({task['id']}): {task['spec']}\n\n"
            f"## Behavioral Scenarios\n{scenarios}"
            f"{produces_section}{ctx_section}")


def test_prompt(task: dict, wt: Path) -> str:
    """TDD Phase 1: Generate test files ONLY from spec + scenarios."""
    base = _build_base_prompt(task, wt)
    test_arts, _ = _split_artifacts(task['artifacts'])
    art_list = '\n'.join(f'- {a}' for a in test_arts)

    return (f"{base}\n\n"
            f"## Test Files to Write\n{art_list}\n"
            f"{QUALITY_RULES}{OUTPUT_FMT}\n\n"
            "Write ONLY the test files listed above. Do NOT write any implementation code.\n"
            "Tests must cover ALL behavioral scenarios from the spec.\n"
            "Each test should assert the expected behavior — tests WILL FAIL until implementation is written.\n"
            "This is TDD RED phase — tests define the contract.\n\n"
            "Output a 1-sentence summary of test coverage when complete.")


def impl_prompt(task: dict, wt: Path) -> str:
    """TDD Phase 2: Generate implementation that makes tests pass."""
    base = _build_base_prompt(task, wt)
    test_arts, impl_arts = _split_artifacts(task['artifacts'])
    impl_list = '\n'.join(f'- {a}' for a in impl_arts)

    # Include actual test file contents so model knows exactly what to satisfy
    test_blocks: list[str] = []
    for t in test_arts:
        f = wt / t
        if f.exists():
            content = f.read_text(encoding='utf-8', errors='replace')[:4000]
            test_blocks.append(f'### {t}\n```\n{content}\n```')
    test_section = '\n\n## Test Files (already written — make these PASS)\n\n' + '\n\n'.join(test_blocks) if test_blocks else ''

    return (f"{base}\n\n"
            f"## Implementation Files to Write\n{impl_list}\n"
            f"{test_section}"
            f"{QUALITY_RULES}{OUTPUT_FMT}\n\n"
            "Write ONLY the implementation files listed above. Do NOT modify the test files.\n"
            "Your code MUST make all existing tests pass.\n"
            "This is TDD GREEN phase — satisfy the test contract.\n\n"
            "Output a 1-sentence summary when complete.")


def exec_prompt(task: dict, wt: Path) -> str:
    """Fallback single-shot prompt for tasks without test files (scaffold, config, etc.)."""
    base = _build_base_prompt(task, wt)
    artifacts = '\n'.join(f'- {a}' for a in task['artifacts'])
    artifact_section = f'\n\n## Required Artifacts\nYou MUST produce exactly these files:\n{artifacts}' if artifacts else ''

    if task['type'] == 'research':
        action = ('Write findings to logs/research/{id}.md. '
                  'Include ≥3 evidence-backed findings under separate ## headings, '
                  'each with a testable prediction and at least one source/citation.'
                  ).format(id=task['id'])
        return f"{base}{artifact_section}{QUALITY_RULES}\n\n{action}\n\nOutput a 1-2 sentence summary when complete."

    return (f"{base}{artifact_section}"
            f"{QUALITY_RULES}{OUTPUT_FMT}\n\n"
            f"Make all required file changes to satisfy every scenario.\n\n"
            f"Output a 1-2 sentence summary when complete.")


def validate_step(validator: str, task: dict, summary: str, cwd: Path,
                   verify_result: str = '', quality_result: str = '') -> tuple[bool, str, float]:
    """Returns (passed, reason, cost_usd).
    Includes actual file contents so validator judges real code, not just summary.
    Tries free model (gemma — fastest) first; falls back to subscription haiku."""
    role = VALIDATOR_ROLE.get(validator.lower(),
                               f'Validate as {validator}: confirm all scenarios are met.')
    scenarios = '\n'.join(f'- {s}' for s in task['scenarios'])
    artifacts = '\n'.join(f'- {a}' for a in task['artifacts'])
    artifact_section = f'\n\nRequired artifacts:\n{artifacts}' if artifacts else ''

    # Include actual generated code (capped at 8K total to fit in context)
    code_sections: list[str] = []
    total_chars = 0
    for art in task.get('artifacts', []):
        f = cwd / art
        if f.exists() and total_chars < 8000:
            content = f.read_text(encoding='utf-8', errors='replace')
            cap = min(len(content), 8000 - total_chars)
            code_sections.append(f'### {art}\n```\n{content[:cap]}\n```')
            total_chars += cap
    code_block = '\n\n'.join(code_sections) if code_sections else '(no files found)'

    # Include deterministic check results
    checks = ''
    if verify_result:
        checks += f'\nVerify commands: {verify_result}'
    if quality_result:
        checks += f'\nQuality checks: {quality_result}'

    prompt = (f"Task ({task['id']}): {task['spec']}\n\nScenarios:\n{scenarios}{artifact_section}\n\n"
              f"## Generated Code\n{code_block}\n\n"
              f"Work summary: {summary}{checks}\n\n"
              f"Your role: {role}\n"
              "Review the ACTUAL CODE above against each scenario. Check for correctness, completeness, and quality.\n\n"
              "Output EXACTLY: PASS — [reason]  OR  FAIL — [reason]. Nothing else.")
    # Try free model first (gemma = fastest free, ~70s)
    out, rc = run_llm_route('gemma', prompt, cwd)
    if rc == 0 and out.strip():
        print(f'[oms-work]   validator {validator} via gemma (free)', flush=True)
        return out.strip().upper().startswith('PASS'), out.strip(), 0.0
    # Fallback to subscription haiku
    print(f'[oms-work]   validator {validator} gemma failed — falling back to haiku', flush=True)
    out, rc, _err, cost = run_claude(prompt, cwd, model='claude-haiku-4-5-20251001')
    return out.strip().upper().startswith('PASS'), out.strip(), cost


def _extract_and_write_files(output: str, wt: Path, artifacts: list[str]) -> int:
    """Parse code blocks from LLM output and write to worktree.
    Returns number of files written. Supports formats:
      ### path/to/file.py\n```lang\n...\n```
      **path/to/file.py**\n```lang\n...\n```
      ```lang path/to/file.py\n...\n```
    """
    written = 0
    remaining_arts = list(artifacts)

    # Split output into sections by heading or bold markers
    # Look for lines that contain a file path before a code block
    lines = output.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        path_str = ''

        # Pattern: ### path/to/file.ext or ## path/to/file.ext
        m = re.match(r'^#{1,4}\s+(.+?)$', line)
        if m:
            candidate = m.group(1).strip().strip('`').strip('*').strip()
            if '.' in candidate and '/' in candidate:
                path_str = candidate

        # Pattern: **path/to/file.ext**
        if not path_str:
            m = re.match(r'^\*\*(.+?)\*\*', line)
            if m:
                candidate = m.group(1).strip()
                if '.' in candidate and '/' in candidate:
                    path_str = candidate

        # Pattern: ```lang path/to/file.ext
        if not path_str:
            m = re.match(r'^```\w*\s+(.+?)$', line)
            if m:
                candidate = m.group(1).strip()
                if '.' in candidate:
                    path_str = candidate

        if path_str:
            # Find the next code fence
            j = i + 1
            while j < len(lines) and not lines[j].startswith('```'):
                j += 1
            if j < len(lines) and lines[j].startswith('```'):
                # Collect content until closing fence
                k = j + 1
                code_lines: list[str] = []
                while k < len(lines) and not lines[k].startswith('```'):
                    code_lines.append(lines[k])
                    k += 1
                content = '\n'.join(code_lines)

                # Clean path
                path_str = path_str.lstrip('/').lstrip('./')

                # Match to artifact
                matched = None
                for art in remaining_arts:
                    if path_str == art or Path(path_str).name == Path(art).name:
                        matched = art
                        break
                target = wt / (matched or path_str)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content.strip() + '\n')
                print(f'[oms-work]   wrote {matched or path_str} ({len(content)} chars)', flush=True)
                written += 1
                if matched:
                    remaining_arts.remove(matched)
                i = k + 1
                continue
        i += 1

    # Fallback: if no heading-based blocks found, try matching fenced blocks to artifacts by order
    if written == 0 and artifacts:
        blocks = re.findall(r'```\w*\n(.*?)```', output, re.DOTALL)
        for block, art in zip(blocks, artifacts):
            target = wt / art
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(block.strip() + '\n')
            print(f'[oms-work]   wrote {art} ({len(block)} chars, order-matched)', flush=True)
            written += 1

    return written


# ── Browse daemon integration ────────────────────────────────────────────────

BROWSE_DIR = Path.home() / '.claude' / 'skills' / 'browse'
BROWSE_STATE = BROWSE_DIR / '.state.json'
BUN = Path.home() / '.bun' / 'bin' / 'bun'


def _ensure_browse() -> tuple[int | None, str | None]:
    """Ensure browse daemon is running. Returns (port, token) or (None, None)."""
    import urllib.request

    def _read_state() -> tuple[int | None, str | None]:
        if not BROWSE_STATE.exists():
            return None, None
        try:
            s = json.loads(BROWSE_STATE.read_text())
            return s.get('port'), s.get('token')
        except Exception:
            return None, None

    def _health(port: int) -> bool:
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=2)
            return True
        except Exception:
            return False

    port, token = _read_state()
    if port and token and _health(port):
        return port, token

    # Start daemon
    if not BUN.exists() or not (BROWSE_DIR / 'server.ts').exists():
        print('[oms-work] browse daemon not available (bun or server.ts missing)', file=sys.stderr)
        return None, None

    print('[oms-work] Starting browse daemon...', flush=True)
    log_f = open(BROWSE_DIR / '.daemon.log', 'w')
    subprocess.Popen(
        [str(BUN), 'run', str(BROWSE_DIR / 'server.ts')],
        stdout=log_f, stderr=log_f,
        start_new_session=True,
    )

    import time
    for _ in range(20):  # max 10s
        time.sleep(0.5)
        port, token = _read_state()
        if port and token and _health(port):
            print(f'[oms-work] Browse daemon ready on port {port}', flush=True)
            return port, token

    print('[oms-work] Browse daemon failed to start', file=sys.stderr)
    return None, None


def _browse_command(port: int, token: str, commands: list[str]) -> dict:
    """Send batch commands to browse daemon. Returns response dict."""
    import urllib.request
    payload = json.dumps({'commands': commands}).encode()
    req = urllib.request.Request(
        f'http://127.0.0.1:{port}/command',
        data=payload,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        },
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read())
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def _is_ui_task(task: dict) -> bool:
    """Check if task involves UI that needs visual verification."""
    ui_exts = ('.tsx', '.jsx', '.html', '.css', '.vue', '.svelte')
    ui_patterns = ('page.', 'route.', 'layout.', 'component')
    arts = ' '.join(task.get('artifacts', []))
    return any(ext in arts for ext in ui_exts) or any(p in arts for p in ui_patterns)


def _derive_routes(artifacts: list[str]) -> list[str]:
    """Derive URL routes from artifact file paths.
    e.g. app/(app)/dashboard/page.tsx → /dashboard
         app/page.tsx → /
         app/privacy/page.tsx → /privacy
    """
    routes: list[str] = []
    for art in artifacts:
        if 'page.' not in art and 'route.' not in art:
            continue
        # Strip app/ prefix and file name
        parts = Path(art).parts
        # Remove 'app' prefix
        if parts and parts[0] == 'app':
            parts = parts[1:]
        # Remove route groups like (app)
        parts = [p for p in parts if not (p.startswith('(') and p.endswith(')'))]
        # Remove file name
        if parts:
            parts = parts[:-1]
        route = '/' + '/'.join(parts) if parts else '/'
        if route not in routes:
            routes.append(route)
    return routes or ['/']


def _run_browse_check(task: dict, wt: Path, project_path: Path) -> tuple[bool, list[str]]:
    """Run visual verification via browse daemon. Returns (passed, issues)."""
    _port, _token = _ensure_browse()
    if not _port or not _token:
        return True, []  # skip if daemon unavailable — don't block task
    port: int = _port
    token: str = _token

    issues: list[str] = []
    routes = _derive_routes(task.get('artifacts', []))

    # Detect dev server port (check if something is running on 3000)
    import urllib.request
    dev_url = 'http://localhost:3000'
    dev_running = False
    try:
        urllib.request.urlopen(dev_url, timeout=2)
        dev_running = True
    except Exception:
        pass

    if not dev_running:
        # Try to start dev server
        pkg_json = project_path / 'package.json'
        if pkg_json.exists():
            print('[oms-work]   starting dev server for browse check...', flush=True)
            dev_proc = subprocess.Popen(
                ['pnpm', 'dev'], cwd=project_path,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            import time
            for _ in range(20):  # wait max 10s for dev server
                time.sleep(0.5)
                try:
                    urllib.request.urlopen(dev_url, timeout=1)
                    dev_running = True
                    break
                except Exception:
                    continue
            if not dev_running:
                dev_proc.terminate()
                return True, []  # skip if dev server won't start
        else:
            return True, []  # no package.json = not a web project

    # Save evidence dir
    evidence_dir = project_path / 'qa' / 'evidence' / task['id'].lower()
    evidence_dir.mkdir(parents=True, exist_ok=True)

    for route in routes:
        url = f'{dev_url}{route}'
        print(f'[oms-work]   browse: {url}', flush=True)

        # Desktop viewport
        resp = _browse_command(port, token, [
            f'go {url}',
            'screenshot',
            'console-errors',
            'network-errors',
        ])

        if not resp.get('ok'):
            issues.append(f'{route}: browse failed — {resp.get("error", "unknown")}')
            continue

        # Check console errors
        console_errs = resp.get('new_console_errors', [])
        real_errors = [e for e in console_errs if e.get('type') == 'error']
        if real_errors:
            issues.append(f'{route}: {len(real_errors)} console error(s): {real_errors[0].get("text", "")[:100]}')

        # Check network errors
        network_errs = resp.get('new_network_errors', [])
        if network_errs:
            issues.append(f'{route}: {len(network_errs)} network error(s): {network_errs[0].get("url", "")[:80]}')

        # Save screenshot
        shot_path = resp.get('screenshot')
        if shot_path and Path(shot_path).exists():
            dest = evidence_dir / f'{route.strip("/").replace("/", "-") or "root"}-desktop.png'
            dest.write_bytes(Path(shot_path).read_bytes())

        # Mobile viewport check
        resp_mobile = _browse_command(port, token, [
            'viewport 375 812',
            'screenshot',
        ])
        if resp_mobile.get('ok') and resp_mobile.get('screenshot'):
            shot_m = resp_mobile['screenshot']
            if Path(shot_m).exists():
                dest_m = evidence_dir / f'{route.strip("/").replace("/", "-") or "root"}-mobile.png'
                dest_m.write_bytes(Path(shot_m).read_bytes())

        # Reset viewport
        _browse_command(port, token, ['viewport 1440 900'])

    if issues:
        for issue in issues:
            print(f'[oms-work]   browse issue: {issue}', flush=True)

    return len(issues) == 0, issues


def _run_quality_checks(wt: Path, artifacts: list[str], is_test: bool = False) -> tuple[bool, list[str]]:
    """Run quality checks. Different rules for test vs impl files.
    Test files: relaxed (500 lines, allow console.log, skip secret check).
    Impl files: strict (300 lines, no console.log, no secrets)."""
    issues: list[str] = []
    max_lines = 500 if is_test else 300

    for art in artifacts:
        f = wt / art
        if not f.exists():
            continue
        content = f.read_text(encoding='utf-8', errors='replace')
        lines = content.splitlines()

        # Check: file size
        if len(lines) > max_lines:
            issues.append(f'{art}: {len(lines)} lines (max {max_lines})')

        # Check: console.log — skip for test files (test debugging is OK)
        if not is_test and f.suffix in ('.ts', '.tsx', '.js', '.jsx'):
            for i, line in enumerate(lines, 1):
                if 'console.log' in line and not line.strip().startswith('//'):
                    issues.append(f'{art}:{i}: console.log found')
                    break

        # Check: hardcoded secrets — skip for test files (fixtures may have fake keys)
        if not is_test:
            for i, line in enumerate(lines, 1):
                low = line.lower()
                if any(p in low for p in ('api_key =', 'secret =', 'password =', 'token =')) \
                        and not line.strip().startswith('#') and not line.strip().startswith('//') \
                        and 'env' not in low and 'os.get' not in low and 'process.env' not in low:
                    issues.append(f'{art}:{i}: possible hardcoded secret')
                    break

        # Prettier auto-fix (both test and impl)
        if f.suffix in ('.ts', '.tsx', '.js', '.jsx'):
            r = subprocess.run(
                ['npx', 'prettier', '--check', str(f)],
                capture_output=True, text=True, cwd=wt, timeout=15,
            )
            if r.returncode != 0:
                subprocess.run(
                    ['npx', 'prettier', '--write', str(f)],
                    capture_output=True, text=True, cwd=wt, timeout=15,
                )

        # Pyright — only if config exists
        if f.suffix == '.py' and (wt / 'pyrightconfig.json').exists():
            r = subprocess.run(
                ['pyright', str(f)],
                capture_output=True, text=True, cwd=wt, timeout=30,
            )
            errs = [l for l in r.stdout.splitlines() if 'error' in l.lower()]
            if errs:
                issues.append(f'{art}: {len(errs)} pyright errors')

    if issues:
        for issue in issues:
            print(f'[oms-work]   quality: {issue}', flush=True)

    return len(issues) == 0, issues


def _verify_research_output(wt: Path, task_id: str) -> tuple[bool, list[str]]:
    """Verify research task output meets minimum quality standards."""
    issues: list[str] = []
    research_file = wt / 'logs' / 'research' / f'{task_id}.md'
    if not research_file.exists():
        return False, [f'Research output not found: logs/research/{task_id}.md']

    content = research_file.read_text(encoding='utf-8', errors='replace')
    lines = [l for l in content.splitlines() if l.strip()]

    if len(lines) < 20:
        issues.append(f'Research output too short ({len(lines)} lines, minimum 20)')

    headings = [l for l in content.splitlines() if l.startswith('## ')]
    if len(headings) < 3:
        issues.append(f'Research output needs ≥3 findings (found {len(headings)} ## headings)')

    # Check for at least one URL/citation
    has_url = 'http' in content.lower() or 'doi' in content.lower()
    if not has_url:
        issues.append('Research output has no URLs or citations')

    return len(issues) == 0, issues


def _run_verify_commands(verify_cmds: list[str], cwd: Path) -> tuple[bool, str]:
    """Run Verify commands locally. Returns (all_passed, summary)."""
    if not verify_cmds:
        return True, 'no verify commands'
    results: list[str] = []
    all_ok = True
    for cmd in verify_cmds:
        print(f'[oms-work]   verify: {cmd}', flush=True)
        try:
            r = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, cwd=cwd, timeout=120,
            )
            if r.returncode == 0:
                results.append(f'PASS: {cmd}')
            else:
                all_ok = False
                err = (r.stderr or r.stdout)[:200].strip()
                results.append(f'FAIL: {cmd} — {err}')
                print(f'[oms-work]   verify FAIL: {cmd} (exit {r.returncode})', flush=True)
        except subprocess.TimeoutExpired:
            results.append(f'TIMEOUT: {cmd}')
            all_ok = False
        except Exception as e:
            results.append(f'ERROR: {cmd} — {e}')
            all_ok = False
    return all_ok, '; '.join(results)


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
    MAX_RETRIES = 2       # retry with same model
    MAX_ESCALATIONS = 1   # retry with stronger model
    try:
        model, is_external = resolve_model(task)
        print(f'[oms-work]   model: {model} ({"external" if is_external else "subscription"})', flush=True)

        # ── TDD Execution loop (RED → GREEN → verify → browse) ──
        error_feedback = ''
        work_out = ''
        exec_passed = False
        tdd_red_result = ''
        tdd_green_result = ''
        total_attempts = MAX_RETRIES + MAX_ESCALATIONS + 1
        test_arts, impl_arts = _split_artifacts(task['artifacts'])
        use_tdd = bool(test_arts) and task['type'] == 'impl'

        if use_tdd:
            print(f'[oms-work]   TDD mode: {len(test_arts)} test file(s), {len(impl_arts)} impl file(s)', flush=True)
        else:
            print(f'[oms-work]   single-shot mode ({"research" if task["type"] == "research" else "no test files"})', flush=True)

        for attempt in range(total_attempts):
            if attempt > 0:
                label = f'retry {attempt}' if attempt <= MAX_RETRIES else f'escalation {attempt - MAX_RETRIES}'
                print(f'[oms-work]   attempt {attempt + 1}/{total_attempts} ({label})', flush=True)
                subprocess.run(['git', 'checkout', '.'], cwd=wt, capture_output=True)
                subprocess.run(['git', 'clean', '-fd'], cwd=wt, capture_output=True)

            # Choose model (escalate on later attempts)
            current_model = model
            current_external = is_external
            if attempt > MAX_RETRIES and is_external:
                escalation_chain = ['qwen', 'gpt-oss', 'nemotron']
                for esc in escalation_chain:
                    if esc != model:
                        current_model = esc
                        break
                print(f'[oms-work]   escalated to {current_model}', flush=True)

            def _run_model(prompt: str) -> tuple[str, int]:
                nonlocal task_cost
                if current_external:
                    return run_llm_route(current_model, prompt, wt)
                out, code, stderr, cost = run_claude(prompt, wt, current_model, allow_writes=True)
                task_cost += cost
                if code != 0 and _is_rate_limited(stderr):
                    fb = 'qwen' if 'sonnet' in current_model else 'qwen-coder'
                    return run_llm_route(fb, prompt, wt)
                return out, code

            if use_tdd:
                # ── PHASE 1: RED — generate tests ──
                print(f'[oms-work]   RED: generating tests...', flush=True)
                t_prompt = test_prompt(task, wt)
                if error_feedback:
                    t_prompt += f'\n\n## Previous Attempt Failed\n{error_feedback}\n\nFix the test files.'
                test_out, code = _run_model(t_prompt)
                if code != 0:
                    error_feedback = f'Test generation failed (exit {code})'
                    continue

                if current_external and test_out.strip():
                    n = _extract_and_write_files(test_out, wt, test_arts)
                    print(f'[oms-work]   RED: extracted {n} test file(s)', flush=True)

                # Quality check on test files (relaxed rules)
                tq_ok, tq_issues = _run_quality_checks(wt, test_arts, is_test=True)
                if not tq_ok:
                    error_feedback = f'Test quality issues: {"; ".join(tq_issues)}'
                    continue

                # RED verification: tests SHOULD FAIL without implementation
                if task.get('verify'):
                    v_ok, v_summary = _run_verify_commands(task['verify'], wt)
                    if v_ok:
                        tdd_red_result = 'WARN: tests passed without implementation (may be tautological)'
                        print(f'[oms-work]   RED: {tdd_red_result}', flush=True)
                        # Not a hard fail — some tests (e.g. config existence) may legitimately pass
                    else:
                        tdd_red_result = f'RED OK: tests fail as expected ({v_summary[:80]})'
                        print(f'[oms-work]   RED: tests fail as expected ✓', flush=True)

                # ── PHASE 2: GREEN — generate implementation ──
                print(f'[oms-work]   GREEN: generating implementation...', flush=True)
                i_prompt = impl_prompt(task, wt)
                if error_feedback and 'test' not in error_feedback.lower():
                    i_prompt += f'\n\n## Previous Attempt Failed\n{error_feedback}\n\nFix the implementation.'
                work_out, code = _run_model(i_prompt)
                if code != 0:
                    error_feedback = f'Implementation generation failed (exit {code})'
                    continue

                if current_external and work_out.strip():
                    n = _extract_and_write_files(work_out, wt, impl_arts)
                    print(f'[oms-work]   GREEN: extracted {n} impl file(s)', flush=True)

            else:
                # ── Single-shot mode (research, scaffold, no-test tasks) ──
                prompt = exec_prompt(task, wt)
                if error_feedback:
                    prompt += f'\n\n## Previous Attempt Failed\n{error_feedback}\n\nFix ALL issues.'
                work_out, code = _run_model(prompt)
                if code != 0:
                    if _is_rate_limited('') and slug:
                        _write_pending_resume(slug, channel_id)
                        remove_worktree(project_path, task['id'])
                        return False, 'RATE-LIMITED: auto-resume scheduled'
                    error_feedback = f'LLM execution failed (exit {code})'
                    continue

                if current_external and task['type'] != 'research' and work_out.strip():
                    n = _extract_and_write_files(work_out, wt, list(task['artifacts']))
                    print(f'[oms-work]   extracted {n} files', flush=True)

            # ── Common checks (both TDD and single-shot) ──

            # Hallucination check (skip for research)
            if task['type'] != 'research':
                gs = subprocess.run(['git', 'status', '--porcelain'],
                                    capture_output=True, text=True, cwd=wt)
                if not gs.stdout.strip():
                    error_feedback = 'No files were written to disk. You MUST create all required artifacts.'
                    continue

            # Quality checks on impl files (strict rules)
            check_arts = impl_arts if use_tdd else task['artifacts']
            q_ok, q_issues = _run_quality_checks(wt, check_arts, is_test=False)
            if not q_ok:
                error_feedback = f'Quality issues: {"; ".join(q_issues)}'
                print(f'[oms-work]   quality: FAIL — {error_feedback[:120]}', flush=True)
                continue

            # Research output verification
            if task['type'] == 'research':
                r_ok, r_issues = _verify_research_output(wt, task['id'])
                if not r_ok:
                    error_feedback = f'Research quality: {"; ".join(r_issues)}'
                    print(f'[oms-work]   research quality: FAIL — {error_feedback[:120]}', flush=True)
                    continue

            # Stage files
            subprocess.run(['git', 'add', '-A'], cwd=wt, capture_output=True)

            # GREEN verification: tests MUST PASS with implementation
            if task.get('verify'):
                v_ok, v_summary = _run_verify_commands(task['verify'], wt)
                print(f'[oms-work]   {"GREEN" if use_tdd else "verify"}: {"PASS" if v_ok else "FAIL"}', flush=True)
                if not v_ok:
                    error_feedback = f'Test failures:\n{v_summary}'
                    tdd_green_result = f'GREEN FAIL: {v_summary[:100]}'
                    continue
                tdd_green_result = 'GREEN OK: all tests pass'

            # Browse check (UI tasks)
            if _is_ui_task(task):
                b_ok, b_issues = _run_browse_check(task, wt, project_path)
                if not b_ok:
                    error_feedback = f'Visual issues: {"; ".join(b_issues)}'
                    print(f'[oms-work]   browse: FAIL — {error_feedback[:120]}', flush=True)
                    continue

            exec_passed = True
            break

        if not exec_passed:
            remove_worktree(project_path, task['id'])
            notes = f'CTO-STOP: failed after {total_attempts} attempts — {error_feedback[:200]}'
            task_fail_at = 'execution'
            write_task_metrics(queue_path, project_path, task['id'], task_cost, [],
                               passed=False, slug=slug, title=task['title'],
                               milestone=task['milestone'], task_type=task['type'],
                               fail_at=task_fail_at, notes=notes, validator_details={})
            discord.notify_task(channel_id, threads_file, task['milestone'],
                                task['id'], task['title'], False, notes)
            return False, notes

        summary = work_out[:300].replace('\n', ' ').strip()
        task_notes = summary
        # Track results for validators
        tdd_info = ''
        if use_tdd:
            tdd_info = f'TDD: {tdd_red_result} | {tdd_green_result}'
        last_verify = tdd_green_result if use_tdd else 'PASS'
        last_quality = 'PASS (all checks passed)'
        print(f'[oms-work]   exec: {summary[:120]}', flush=True)
        if tdd_info:
            print(f'[oms-work]   {tdd_info}', flush=True)

        # ── Validation chain ──
        research_retried = False
        for validator in task['validation']:
            passed, reason, val_cost = validate_step(
                validator, task, summary, wt,
                verify_result=last_verify, quality_result=last_quality)
            task_cost += val_cost
            first_pass = passed
            print(f'[oms-work]   {"✓" if passed else "✗"} {validator}: {reason[:100]}', flush=True)
            if not passed:
                if (validator == 'cro' and task['type'] == 'research'
                        and not research_retried):
                    research_retried = True
                    # Try stronger free model (qwen — 1M ctx, deep reasoning) before sonnet
                    print('[oms-work]   research quality insufficient — retrying with qwen (free)', flush=True)
                    work_out, code = run_llm_route('qwen', exec_prompt(task, wt), wt)
                    retry_cost = 0.0
                    # If free model also fails, escalate to sonnet
                    if code != 0 or not work_out.strip():
                        print('[oms-work]   qwen retry failed — escalating to sonnet', flush=True)
                        work_out, code, _, retry_cost = run_claude(
                            exec_prompt(task, wt), wt, 'claude-sonnet-4-6', allow_writes=True)
                    task_cost += retry_cost
                    if code == 0:
                        summary = work_out[:300].replace('\n', ' ').strip()
                        passed, reason, val_cost = validate_step(
                            validator, task, summary, wt,
                            verify_result=last_verify, quality_result=last_quality)
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
