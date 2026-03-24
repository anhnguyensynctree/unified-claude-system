#!/usr/bin/env python3
"""
OMS Watcher — pipeline integrity agent.
Called by oms-dispatcher.sh when pipeline_frozen is written.

Reads bug-list.md, applies deterministic fixes, posts CEO notification.

Usage: oms-watcher.py <cp_path> <frozen_step> <task_id> [missing_field ...]

Exit codes:
  0 — fix applied; dispatcher prints notification and exits normally.
      Next heartbeat runs the corrected step.
  1 — no fix available or attempt limit reached; pipeline stays frozen.
"""
import json
import os
import re
import sys
from datetime import date

MAX_ATTEMPTS = 2

ALLOWLIST = re.compile(
    r'^(router|round_[1-9][0-9]?|ceo_gate|synthesis|implement|log|'
    r'cpo_backlog|trainer|compact_check|mark_done|transition|'
    r'waiting_ceo|pipeline_frozen|complete|done|)$'
)

ROUND_RE = re.compile(r'^round_[1-9][0-9]?$')


def load_cp(cp_path):
    try:
        return json.load(open(cp_path))
    except Exception:
        return None


def save_cp(cp_path, cp):
    tmp = cp_path + '.tmp'
    json.dump(cp, open(tmp, 'w'))
    os.replace(tmp, cp_path)


def write_lesson(agent, task_id, frozen_step, lesson_text):
    lessons_path = os.path.expanduser(f'~/.claude/agents/{agent}/lessons.md')
    today = date.today().isoformat()
    # 4-word fingerprint dedup check
    fingerprint = ' '.join(lesson_text.split()[:4]).lower()
    try:
        existing = open(lessons_path).read() if os.path.exists(lessons_path) else ''
        if fingerprint in existing.lower():
            return  # already present
        entry = (f'\n{today} | {task_id} | importance:critical | {lesson_text}\n'
                 f'Surfaces when: Watcher fired for {frozen_step} step\n')
        with open(lessons_path, 'a') as f:
            f.write(entry)
        print(f'[watcher] Wrote lesson to {agent}/lessons.md', file=sys.stderr)
    except Exception as e:
        print(f'[watcher] Could not write lesson to {agent}: {e}', file=sys.stderr)


def get_attempts(cp, fix_key):
    return cp.get('fix_attempts', {}).get(fix_key, 0)


def increment_attempts(cp, fix_key):
    attempts = cp.setdefault('fix_attempts', {})
    attempts[fix_key] = attempts.get(fix_key, 0) + 1
    return attempts[fix_key]


def match_bug(frozen_step, missing_fields):
    """Match failure signature to a bug entry. Returns bug dict or None."""
    has_rr  = any('rounds_required'  in m for m in missing_fields)
    has_aa  = any('activated_agents' in m for m in missing_fields)
    has_tid = any('task_id'          in m for m in missing_fields)
    is_round = ROUND_RE.match(frozen_step)

    # BUG-003: both missing (check before 001/002 — more specific)
    if is_round and has_rr and has_aa:
        return {
            'bug_id': 'BUG-003',
            'description': 'Router did not run — both rounds_required and activated_agents missing',
            'rerun_step': 'router',
            'next': 'router',
            'responsible_agent': 'router',
            'lesson': ('router', 'Router must complete fully and write all required fields before '
                       'pipeline advances — silent Router failure leaves checkpoint empty'),
        }

    # BUG-001: rounds_required missing
    if is_round and has_rr:
        return {
            'bug_id': 'BUG-001',
            'description': 'Router missing rounds_required',
            'rerun_step': 'router',
            'next': 'router',
            'responsible_agent': 'router',
            'lesson': ('router', 'rounds_required must be non-null before setting stage_gate: passed '
                       '— R8 blocking failure; derived from tier (Tier 0→1, Tier 1→2, Tier 2→2, Tier 3→3)'),
        }

    # BUG-002: activated_agents missing
    if is_round and has_aa:
        return {
            'bug_id': 'BUG-002',
            'description': 'Router missing activated_agents',
            'rerun_step': 'router',
            'next': 'router',
            'responsible_agent': 'router',
            'lesson': ('router', 'activated_agents must be written to checkpoint before advancing to '
                       'round_1 — Stage-Gate 1 must verify this field is non-null before passing'),
        }

    # BUG-005: task_id missing — no auto-fix, escalate
    if has_tid:
        return None  # forces escalation

    # BUG-004: invalid next value (frozen_step is the bad value itself)
    if frozen_step and not ALLOWLIST.match(frozen_step):
        return {
            'bug_id': 'BUG-004',
            'description': f'Invalid next value "{frozen_step}"',
            'rerun_step': 'router',
            'next': 'router',
            'responsible_agent': None,
            'lesson': None,
        }

    return None  # unknown bug — escalate


def main():
    if len(sys.argv) < 4:
        print('[watcher] Usage: oms-watcher.py <cp_path> <frozen_step> <task_id> [missing ...]',
              file=sys.stderr)
        sys.exit(1)

    cp_path    = sys.argv[1]
    frozen_step = sys.argv[2]
    task_id    = sys.argv[3]
    missing    = sys.argv[4:]

    cp = load_cp(cp_path)
    if cp is None:
        print('[watcher] Cannot read checkpoint — escalating', file=sys.stderr)
        print('## OMS Update\n🚨 Watcher: cannot read checkpoint — manual intervention needed')
        sys.exit(1)

    bug = match_bug(frozen_step, missing)

    if bug is None:
        details = ', '.join(missing) if missing else f'invalid step "{frozen_step}"'
        print(f'[watcher] No deterministic fix for frozen_step={frozen_step} missing=[{details}]',
              file=sys.stderr)
        print(f'## OMS Update\n🚨 Watcher escalation: no fix for {frozen_step} ({details}) '
              f'on {task_id} — manual intervention needed')
        sys.exit(1)

    fix_key  = f"{bug['bug_id']}:{frozen_step}:{task_id}"
    attempts = get_attempts(cp, fix_key)

    if attempts >= MAX_ATTEMPTS:
        print(f'[watcher] {fix_key} already attempted {attempts}x — escalating', file=sys.stderr)
        print(f'## OMS Update\n🚨 Watcher escalation: {bug["description"]} failed after '
              f'{attempts} attempts on {frozen_step} for {task_id}. Manual intervention needed.')
        sys.exit(1)

    # Apply fix
    cp['next'] = bug['next']
    cp.pop('frozen_step', None)
    new_attempts = increment_attempts(cp, fix_key)
    save_cp(cp_path, cp)

    # Write lesson if applicable (dedup check inside)
    if bug.get('lesson'):
        agent, lesson_text = bug['lesson']
        write_lesson(agent, task_id, frozen_step, lesson_text)

    warning = ' ⚠️ Last auto-attempt — will escalate if it fails again.' if new_attempts >= MAX_ATTEMPTS else ''
    print(f'## OMS Update\n🔧 Watcher: {bug["description"]} '
          f'(attempt {new_attempts}/{MAX_ATTEMPTS}).{warning} '
          f'Resetting to {bug["rerun_step"]} — rerunning next heartbeat.')
    sys.exit(0)


if __name__ == '__main__':
    main()
