#!/bin/bash
# OMS Dispatcher — lock-aware claude --print invoker
# Usage: oms-dispatcher.sh <project-slug> <prompt>
# Called by discord-bot.py for every autonomous OMS step

set -eo pipefail

PROJECT_SLUG="${1:-}"
PROMPT="${2:-}"

if [ -z "$PROJECT_SLUG" ] || [ -z "$PROMPT" ]; then
  echo "[dispatcher] Usage: oms-dispatcher.sh <project-slug> <prompt>" >&2
  exit 1
fi

CONFIG="$HOME/.claude/oms-config.json"
if [ ! -f "$CONFIG" ]; then
  echo "[dispatcher] oms-config.json not found — run /init-oms first" >&2
  exit 1
fi

PROJECT_PATH=$(python3 -c "
import json, sys
with open('$CONFIG') as f:
    c = json.load(f)
p = c.get('projects', {}).get('$PROJECT_SLUG', {})
print(p.get('path', ''))
" 2>/dev/null)

if [ -z "$PROJECT_PATH" ] || [ ! -d "$PROJECT_PATH" ]; then
  echo "[dispatcher] Unknown project or path not found: $PROJECT_SLUG" >&2
  exit 1
fi

LOCK_DIR="$HOME/.claude/oms-locks"
LOCK_FILE="$LOCK_DIR/${PROJECT_SLUG}.lock"
MANUAL_LOCK="$PROJECT_PATH/.claude/manual.lock"
LOG_DIR="$HOME/.claude/logs"

mkdir -p "$LOCK_DIR" "$LOG_DIR"

if [ -f "$MANUAL_LOCK" ]; then
  echo "[dispatcher] Manual session active for $PROJECT_SLUG — skipping" >&2
  exit 0
fi

# Atomic lock acquisition using O_EXCL — prevents TOCTOU race between concurrent dispatchers
LOCK_ACQUIRED=0
if python3 -c "
import json, os, sys
try:
    fd = os.open('$LOCK_FILE', os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    json.dump({'pid': os.getpid(), 'project': '$PROJECT_SLUG',
               'started': '$(date -u +%Y-%m-%dT%H:%M:%SZ)', 'step': 'running'},
              os.fdopen(fd, 'w'))
    sys.exit(0)  # acquired
except FileExistsError:
    # Lock exists — check if PID is alive
    try:
        d = json.load(open('$LOCK_FILE'))
        pid = d.get('pid', '')
        if pid and os.kill(int(pid), 0) is None:
            sys.exit(1)  # alive — skip
    except (json.JSONDecodeError, ValueError, TypeError):
        pass  # corrupted lock — fall through to clear
    except (ProcessLookupError, PermissionError):
        pass  # stale lock — fall through to clear
    os.unlink('$LOCK_FILE')
    # Re-acquire atomically after clearing stale lock
    try:
        fd = os.open('$LOCK_FILE', os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        json.dump({'pid': os.getpid(), 'project': '$PROJECT_SLUG',
                   'started': '$(date -u +%Y-%m-%dT%H:%M:%SZ)', 'step': 'running'},
                  os.fdopen(fd, 'w'))
        sys.exit(0)  # acquired after clearing stale lock
    except FileExistsError:
        sys.exit(1)  # another process beat us to it — skip
" 2>/dev/null; then
  LOCK_ACQUIRED=1
else
  echo "[dispatcher] Step already running for $PROJECT_SLUG — skipping" >&2
  exit 0
fi
cleanup() { rm -f "$LOCK_FILE"; }
trap cleanup EXIT

if [ -f "$HOME/.config/github/token" ]; then
  export GH_TOKEN=$(cat "$HOME/.config/github/token")
fi

# Read checkpoint — all values in one Python call
NEXT=""
TASK_ID=""
PRIOR_SESSION=""
ROUNDS_REQUIRED="3"
if [ "$PROMPT" = "_auto" ]; then
  CHECKPOINT="$PROJECT_PATH/.claude/oms-checkpoint.json"
  if [ -f "$CHECKPOINT" ]; then
    _CP=$(python3 -c "
import json
try:
    d = json.load(open('$CHECKPOINT'))
    print(d.get('next',''))
    print(d.get('task_id',''))
    print(d.get('session_id',''))
    print(str(d.get('rounds_required', 3)))
except: print(''); print(''); print(''); print('3')
" 2>/dev/null || printf '\n\n\n3')
    NEXT=$(echo "$_CP" | sed -n '1p')
    TASK_ID=$(echo "$_CP" | sed -n '2p')
    PRIOR_SESSION=$(echo "$_CP" | sed -n '3p')
    ROUNDS_REQUIRED=$(echo "$_CP" | sed -n '4p')
    # Project-level default_rounds only applies when checkpoint doesn't specify
    if [ -z "$ROUNDS_REQUIRED" ]; then
      ROUNDS_REQUIRED=$(python3 -c "
import json
try:
    c = json.load(open('$CONFIG'))
    r = c.get('projects', {}).get('$PROJECT_SLUG', {}).get('default_rounds', '')
    print(str(r) if r else '')
except: print('')
" 2>/dev/null)
    fi
    ROUNDS_REQUIRED="${ROUNDS_REQUIRED:-3}"

    # Pre-flight idempotency: grep task log before invoking claude (zero token cost)
    LOG_FILE="$PROJECT_PATH/logs/tasks/$TASK_ID.md"
    if [ -n "$TASK_ID" ] && [ -f "$LOG_FILE" ]; then
      case "$NEXT" in
        round_*)
          ROUND="${NEXT#round_}"
          if grep -qE "^#{1,3} Round $ROUND" "$LOG_FILE" 2>/dev/null; then
            echo "[dispatcher] Pre-flight: Round $ROUND already in log — advancing" >&2
            NEXT_CP="round_$((ROUND+1))"
            [ "$ROUND" -ge "$ROUNDS_REQUIRED" ] && NEXT_CP="synthesis"
            python3 -c "
import json, os
cp = json.load(open('$CHECKPOINT'))
cp['next'] = '$NEXT_CP'
tmp = '$CHECKPOINT.tmp'; json.dump(cp, open(tmp,'w')); os.replace(tmp,'$CHECKPOINT')
"
            echo "## OMS Update"$'\n'"Round $ROUND already complete — advancing to $NEXT_CP"
            exit 0
          fi ;;
        synthesis)
          if grep -qE "^#{1,3} Synthesis" "$LOG_FILE" 2>/dev/null; then
            echo "[dispatcher] Pre-flight: Synthesis already in log — advancing" >&2
            python3 -c "
import json, os
cp = json.load(open('$CHECKPOINT'))
cp['next'] = 'implement'
tmp = '$CHECKPOINT.tmp'; json.dump(cp, open(tmp,'w')); os.replace(tmp,'$CHECKPOINT')
"
            echo "## OMS Update"$'\n'"Synthesis already complete — advancing to implement"
            exit 0
          fi ;;
        cpo_backlog)
          BACKLOG="$PROJECT_PATH/.claude/agents/backlog/priority-queue.md"
          if [ -f "$BACKLOG" ] && grep -qE "status:done|Status.*done" "$BACKLOG" 2>/dev/null; then
            # Already scored this session — but cpo_backlog may still need to run for new items
            # Only skip if steps_written includes cpo_backlog (checkpoint tracks this)
            if python3 -c "
import json, sys
cp = json.load(open('$CHECKPOINT'))
sys.exit(0 if 'cpo_backlog' in cp.get('steps_written', []) else 1)
" 2>/dev/null; then
              echo "[dispatcher] Pre-flight: cpo_backlog already run this task — advancing" >&2
              python3 -c "
import json, os
cp = json.load(open('$CHECKPOINT'))
cp['next'] = 'trainer'
tmp = '$CHECKPOINT.tmp'; json.dump(cp, open(tmp,'w')); os.replace(tmp,'$CHECKPOINT')
"
              echo "## OMS Update"$'\n'"CPO backlog already complete — advancing to trainer"
              exit 0
            fi
          fi ;;
        trainer)
          if python3 -c "
import json, sys
cp = json.load(open('$CHECKPOINT'))
sys.exit(0 if 'trainer' in cp.get('steps_written', []) else 1)
" 2>/dev/null; then
            echo "[dispatcher] Pre-flight: trainer already run this task — advancing" >&2
            python3 -c "
import json, os
cp = json.load(open('$CHECKPOINT'))
cp['next'] = 'compact_check'
tmp = '$CHECKPOINT.tmp'; json.dump(cp, open(tmp,'w')); os.replace(tmp,'$CHECKPOINT')
"
            echo "## OMS Update"$'\n'"Trainer already complete — advancing to compact_check"
            exit 0
          fi ;;
      esac
    fi

    # Session-aware: skip log reads when resuming (model has context in working memory)
    if [ -n "$PRIOR_SESSION" ]; then
      READ_LOG=""
      READ_LOG_ROUNDS=""
    else
      READ_LOG="Read logs/tasks/$TASK_ID.md for context. "
      READ_LOG_ROUNDS="Read logs/tasks/$TASK_ID.md for all rounds. "
    fi

    case "$NEXT" in
      router)
        PROMPT="OMS autonomous step: run Step 1 (Router) for task $TASK_ID. ${READ_LOG}Run Router only — write checkpoint next:round_1 and rounds_required:N (1=Tier0, 2=Tier1/2, 3=Tier3). Then output exactly: ## OMS Update\n[1-2 sentences: which agents are involved and the core question being tackled]" ;;
      round_*)
        ROUND="${NEXT#round_}"
        PROMPT="OMS autonomous step: run Round $ROUND discussion for task $TASK_ID (rounds_required: $ROUNDS_REQUIRED). ${READ_LOG}FIRST CHECK: if Round $ROUND is already written in the log, immediately write checkpoint next:round_$((ROUND+1)) or next:synthesis if $ROUND >= $ROUNDS_REQUIRED, then output ## OMS Update\n[1 sentence: round already complete, advancing] — do NOT re-run it. Otherwise run Round $ROUND now. After writing, if $ROUND >= $ROUNDS_REQUIRED write checkpoint next:synthesis, else next:round_$((ROUND+1)). Output ## OMS Update\n[1-2 sentences: key insight or decision from this round]" ;;
      ceo_gate)
        # Pre-flight: if .question file already exists, checkpoint wasn't updated last run — advance without re-asking
        QUESTION_FILE="$PROJECT_PATH/.claude/oms-pending/${PROJECT_SLUG}.question"
        if [ -f "$QUESTION_FILE" ]; then
          echo "[dispatcher] ceo_gate pre-flight: question file exists, checkpoint not updated — advancing to waiting_ceo" >&2
          python3 -c "
import json, os
cp_path = '$PROJECT_PATH/.claude/oms-checkpoint.json'
cp = json.load(open(cp_path))
cp['next'] = 'waiting_ceo'
tmp = cp_path + '.tmp'; json.dump(cp, open(tmp,'w')); os.replace(tmp, cp_path)
" 2>/dev/null
          echo "## OMS Update"$'\n'"CEO Gate: question already posted — waiting for CEO"
          exit 0
        fi
        PROMPT="OMS autonomous step: run Step 3.5 CEO Gate for task $TASK_ID. ${READ_LOG_ROUNDS}If no CEO input needed, write checkpoint next:synthesis and output ## OMS Update\n[passed — proceeding to synthesis]. If CEO input IS needed, write a full decision brief to .claude/oms-pending/${PROJECT_SLUG}.question as JSON with field 'question' containing: (1) decision context and why it matters, (2) each option with bullet-point pros and cons, (3) agent recommendation with one-line reason. Write checkpoint next:waiting_ceo and output ## OMS Update\n[blocking — decision brief posted to CEO]" ;;
      synthesis)
        PROMPT="OMS autonomous step: run Step 4 Synthesizer for task $TASK_ID. ${READ_LOG_ROUNDS}FIRST CHECK: if Synthesis already written in log, write checkpoint next:implement and output ## OMS Update\n[synthesis already complete, advancing to implement]. Otherwise run Synthesizer — write full synthesis output to logs/tasks/$TASK_ID.md, write checkpoint next:implement, output ## OMS Update\n[1-2 sentences: core recommendation locked in synthesis]" ;;
      log)
        # Ghost step — synthesis already writes to the log. Just advance.
        echo "[dispatcher] log step is a ghost — force-advancing to cpo_backlog" >&2
        python3 -c "
import json, os
cp_path = '$PROJECT_PATH/.claude/oms-checkpoint.json'
cp = json.load(open(cp_path))
cp['next'] = 'cpo_backlog'
tmp = cp_path + '.tmp'; json.dump(cp, open(tmp,'w')); os.replace(tmp, cp_path)
" 2>/dev/null
        echo "## OMS Update"$'\n'"Synthesis already in log — advancing to CPO backlog"
        exit 0 ;;
      cpo_backlog)
        PROMPT="OMS autonomous step: run Step 5.5 CPO backlog pass for task $TASK_ID. Read .claude/agents/backlog/priority-queue.md. For each queued item missing a RICE score: estimate Reach, Impact (0.25/0.5/1/2/3), Confidence (50/80/100%), Effort (weeks), compute score=(R×I×C)/E, add inline. Re-sort by score descending. Apply Kano class (basic/performance/delighter) and Now/Next/Later slot to items missing them. Write the updated file. Write checkpoint next:trainer. Output exactly: ## OMS Update\n[1 sentence: top task and its RICE score]" ;;
      trainer)
        PROMPT="OMS autonomous step: run Step 6 Trainer evaluation for task $TASK_ID. ${READ_LOG}Run Trainer only — write checkpoint next:compact_check. For any lesson_candidate with channel:shared_lesson, also write to ~/.claude/agents/shared-lessons/[category].md. Output exactly: ## OMS Update\n[1-2 sentences: lesson quality and any shared patterns identified]" ;;
      compact_check)
        PROMPT="OMS autonomous step: run Step 7 Context Optimizer for task $TASK_ID. Load ~/.claude/agents/context-optimizer/persona.md and ~/.claude/agents/context-optimizer/metrics.md. Run Mode 1 post-task lightweight check against logs/tasks/$TASK_ID.md. Execute safe auto-fixes. Update metrics.md. Write checkpoint next:mark_done. Output exactly: ## OMS Update\n[1 sentence: efficiency status and any optimisations applied]" ;;
      implement)
        PROMPT="OMS autonomous step: run /oms-implement $TASK_ID — implement the completed synthesis. Write checkpoint next:cpo_backlog when complete. Output ## OMS Update\n[1 sentence: what was implemented]" ;;
      milestone_gate)
        PROMPT="OMS autonomous step: check milestone gate for task $TASK_ID. Write checkpoint next:waiting_ceo or next:mark_done. Output ## OMS Update\n[1 sentence: milestone status]" ;;
      waiting_ceo)
        echo "[dispatcher] Waiting for CEO input on $TASK_ID — skipping" >&2; exit 0 ;;
      pipeline_frozen)
        echo "[dispatcher] Pipeline frozen (stuck step) for $TASK_ID — skipping until CEO skip/reset" >&2; exit 0 ;;
      mark_done)
        echo "[dispatcher] mark_done: marking $TASK_ID as done in backlog" >&2
        PROMPT="OMS autonomous step (mark_done): Open .claude/agents/backlog/priority-queue.md and mark the entry for $TASK_ID as status:done — update both the table row (change 'queued' to 'done') and the **Status** field in its ## section. Do NOTHING else. Write checkpoint {\"task_id\":\"$TASK_ID\",\"next\":\"transition\"} and output exactly: ## OMS Update\n$TASK_ID marked done in backlog."
        PRIOR_SESSION=""
        ;;
      transition)
        echo "[dispatcher] transition: picking next task after $TASK_ID" >&2
        PROMPT="OMS autonomous step (transition): Read .claude/agents/backlog/priority-queue.md. Find the highest-priority task that is NOT $TASK_ID with status 'queued' or slot 'Next'. If none exists: write checkpoint {\"next\":\"complete\"} and output exactly: ## OMS Update\nBacklog empty — no next task. If a task exists: run Router silently for it, then write a FRESH checkpoint with ONLY these fields: task_id, next=round_1, rounds_required, tier, activated_agents. No other fields — do not copy completion_reported or any prior task fields. Output exactly: ## OMS Update\n[new task name + core question]."
        PRIOR_SESSION=""
        ;;
      done)
        # Legacy alias — force-advance to mark_done without a Claude call (zero cost)
        echo "[dispatcher] done: legacy step — advancing to mark_done (no Claude call)" >&2
        python3 -c "
import json, os
cp_path = '$PROJECT_PATH/.claude/oms-checkpoint.json'
try:
    cp = json.load(open(cp_path))
    if cp.get('next') == 'done':
        cp['next'] = 'mark_done'
        tmp = cp_path + '.tmp'; json.dump(cp, open(tmp,'w')); os.replace(tmp, cp_path)
except Exception:
    pass
" 2>/dev/null
        echo "## OMS Update"$'\n'"Legacy done step — advancing to mark_done"
        exit 0 ;;
      *)
        PROMPT="OMS autonomous step: read .claude/oms-checkpoint.json and run only the single next step indicated. Write updated checkpoint and output '## OMS Update' then exit." ;;
    esac
  else
    PROMPT="OMS autonomous step: start the next task. First check .claude/agents/backlog/priority-queue.md — if it exists and has a queued task, pick the highest-priority one. If no backlog or all tasks are done, read .claude/agents/product-direction.ctx.md and pick the first unstarted item from Current Priorities or Next Milestone. You MUST pick one task autonomously — never ask CEO. Run Router silently for it, write checkpoint {task_id, next:round_1, rounds_required} to .claude/oms-checkpoint.json. Output EXACTLY two lines: ## OMS Update\nTASK:[task_id] [core question being tackled]"
  fi
fi

# Budget gate — primary: 5h session window %; secondary: weekly (warning only)
BUDGET_FILE="$HOME/.claude/oms-budget.json"
BUDGET_STATUS="ok"
if [ -f "$BUDGET_FILE" ]; then
  BUDGET_STATUS=$(python3 -c "
import json, sys
from datetime import datetime, timedelta, timezone
with open('$BUDGET_FILE') as f:
    b = json.load(f)
now = datetime.now(timezone.utc)
thresholds = b.get('thresholds', {})
skip_pct = thresholds.get('session_skip_non_critical_pct', 75)
pause_pct = thresholds.get('session_pause_pct', 90)
weekly_warn_pct = thresholds.get('weekly_warning_pct', 80)

# --- Session window check (primary gate) ---
session_limit = b.get('session_limit_usd', 20)
session_spend = b.get('current_session_spend_usd', 0)
session_start_raw = b.get('current_session_start', '')
window_hours = b.get('session_window_hours', 5)
session_pct = 0
if session_start_raw and session_limit > 0:
    try:
        ss = datetime.fromisoformat(session_start_raw)
        if ss.tzinfo is None:
            ss = ss.replace(tzinfo=timezone.utc)
        if now - ss > timedelta(hours=window_hours):
            # Window expired — reset in next post-step, treat as fresh
            session_pct = 0
        else:
            session_pct = session_spend / session_limit * 100
    except Exception:
        session_pct = 0

# --- Weekly check (warning only — not a gate) ---
weekly_limit = b.get('weekly_limit_usd', 100)
weekly_spend = b.get('current_week_spend_usd', 0)
weekly_pct = (weekly_spend / weekly_limit * 100) if weekly_limit > 0 else 0
if weekly_pct >= weekly_warn_pct:
    print(f'[dispatcher] Weekly usage at {weekly_pct:.0f}% (\${weekly_spend:.2f}/\${weekly_limit:.0f})', file=sys.stderr)

if session_pct >= pause_pct: print('pause')
elif session_pct >= skip_pct: print('skip_non_critical')
else: print('ok')
" 2>/dev/null || echo "ok")

  case "$BUDGET_STATUS" in
    pause)
      echo "[dispatcher] Session gate: at/above 90% of 5h window — pausing OMS for $PROJECT_SLUG" >&2
      exit 0 ;;
    skip_non_critical)
      echo "[dispatcher] Session gate: at 75% of 5h window — non-critical steps may be skipped" >&2 ;;
  esac
fi

# Model selection — Haiku for mechanical/routing steps (20x cheaper, no reasoning required)
case "$NEXT" in
  log|cpo_backlog|trainer|compact_check|transition|mark_done|done) STEP_MODEL="claude-haiku-4-5-20251001" ;;
  *) STEP_MODEL="claude-sonnet-4-6" ;;
esac

# Pre-step input validation — check required checkpoint fields exist before invoking Claude
# Catches upstream stage failures before they cascade into downstream garbage output
if [ -n "$NEXT" ] && [ -f "$PROJECT_PATH/.claude/oms-checkpoint.json" ]; then
  python3 -c "
import json, os, sys, re
cp_path = '$PROJECT_PATH/.claude/oms-checkpoint.json'
try:
    cp = json.load(open(cp_path))
except Exception:
    sys.exit(0)

nxt = '$NEXT'
missing = []

# Fields required before round steps — Router must have written these
if re.fullmatch(r'round_[1-9][0-9]?', nxt):
    if not cp.get('activated_agents'):
        missing.append('activated_agents (Router must run first)')
    rr = cp.get('rounds_required')
    if not rr or str(rr).strip() in ('', 'None', 'null'):
        missing.append('rounds_required (Router output incomplete — R8)')

# task_id required for all content-producing steps
content_steps = {'round_1','round_2','round_3','round_4','synthesis','implement',
                 'cpo_backlog','trainer','compact_check','mark_done'}
if nxt in content_steps and not cp.get('task_id'):
    missing.append('task_id')

if not missing:
    sys.exit(0)

# Missing required inputs — freeze pipeline, then hand off to Watcher for auto-recovery
print('[dispatcher] Pre-step validation FAILED for step ' + nxt + ':', file=sys.stderr)
for m in missing:
    print('  missing: ' + m, file=sys.stderr)
cp['frozen_step'] = nxt
cp['next'] = 'pipeline_frozen'
tmp = cp_path + '.tmp'
json.dump(cp, open(tmp, 'w'))
os.replace(tmp, cp_path)
# Pass missing field names as args so Watcher can match the bug
print(' '.join(missing))  # captured by bash as MISSING_FIELDS
sys.exit(1)
" 2>/dev/null
PRESTEP_EXIT=$?
if [ $PRESTEP_EXIT -ne 0 ]; then
  MISSING_FIELDS=$(python3 -c "
import json, re
cp_path = '$PROJECT_PATH/.claude/oms-checkpoint.json'
try:
    cp = json.load(open(cp_path))
except: cp = {}
nxt = '$NEXT'
missing = []
if re.fullmatch(r'round_[1-9][0-9]?', nxt):
    if not cp.get('activated_agents'): missing.append('activated_agents')
    rr = cp.get('rounds_required')
    if not rr or str(rr).strip() in ('', 'None', 'null'): missing.append('rounds_required')
content_steps = {'round_1','round_2','round_3','round_4','synthesis','implement','cpo_backlog','trainer','compact_check','mark_done'}
if nxt in content_steps and not cp.get('task_id'): missing.append('task_id')
print(' '.join(missing))
" 2>/dev/null)
  WATCHER_OUT=$(python3 "$HOME/.claude/bin/oms-watcher.py" \
    "$PROJECT_PATH/.claude/oms-checkpoint.json" \
    "$NEXT" "$TASK_ID" $MISSING_FIELDS 2>>"${STEP_LOG:-/dev/stderr}")
  WATCHER_EXIT=$?
  if [ $WATCHER_EXIT -eq 0 ]; then
    echo "$WATCHER_OUT"
    exit 0  # Watcher fixed it — next heartbeat runs corrected step
  else
    echo "$WATCHER_OUT"
    exit 0  # Watcher escalated — pipeline stays frozen, CEO notified
  fi
fi
fi

echo "[dispatcher] Starting step for $PROJECT_SLUG (next: ${NEXT:-explicit}, model: $STEP_MODEL)" >&2

CLAUDE_BIN="${HOME}/.local/bin/claude"
mkdir -p "$HOME/.claude/oms-costs"

# Session chaining — resume prior session for persistent context
RESUME_ARGS=()
if [ -n "$PRIOR_SESSION" ]; then
  RESUME_ARGS=(--resume "$PRIOR_SESSION")
  echo "[dispatcher] Resuming session ${PRIOR_SESSION:0:16}... for $PROJECT_SLUG" >&2
fi

# Per-step log — named by step so history is preserved across the pipeline
# Retries append to the same step log (not overwrite) so all attempts are visible
STEP_LOG="$LOG_DIR/oms-${PROJECT_SLUG}-${NEXT:-step}.log"

TMPJSON=$(mktemp)
cd "$PROJECT_PATH" && OMS_BOT=1 "$CLAUDE_BIN" \
  --print \
  --dangerously-skip-permissions \
  --output-format json \
  --model "$STEP_MODEL" \
  "${RESUME_ARGS[@]}" \
  -p "$PROMPT" < /dev/null >"$TMPJSON" 2>"$STEP_LOG"
EXIT_CODE=$?

# Session resumption fallback — if --resume failed, retry as fresh session
if [ $EXIT_CODE -ne 0 ] && [ -n "$PRIOR_SESSION" ]; then
  echo "[dispatcher] Session resume failed for ${PRIOR_SESSION:0:16} — retrying fresh" >&2
  echo "--- RETRY (fresh session) $(date -u +%Y-%m-%dT%H:%M:%SZ) ---" >>"$STEP_LOG"
  # Clear stale session_id from checkpoint so it doesn't loop
  python3 -c "
import json, os
cp_path = '$PROJECT_PATH/.claude/oms-checkpoint.json'
try:
    cp = json.load(open(cp_path))
    cp.pop('session_id', None)
    tmp = cp_path + '.tmp'; json.dump(cp, open(tmp,'w')); os.replace(tmp, cp_path)
except Exception: pass
" 2>/dev/null
  cd "$PROJECT_PATH" && OMS_BOT=1 "$CLAUDE_BIN" \
    --print \
    --dangerously-skip-permissions \
    --output-format json \
    --model "$STEP_MODEL" \
    -p "$PROMPT" < /dev/null >"$TMPJSON" 2>>"$STEP_LOG"
  EXIT_CODE=$?
fi

OUTPUT=$(python3 "$HOME/.claude/bin/oms-post-step.py" \
  "$TMPJSON" "$PROJECT_PATH" "$TASK_ID" "${NEXT:-step}" "$PROJECT_SLUG" 2>/dev/null)
rm -f "$TMPJSON"

# Force-advance checkpoint for deterministic steps — fallback if Claude forgot to write it.
if [ -n "$TASK_ID" ] && [ -f "$PROJECT_PATH/.claude/oms-checkpoint.json" ]; then
  case "$NEXT" in
    round_*)
      ROUND="${NEXT#round_}"
      NEXT_ROUND=$((ROUND+1))
      if [ "$ROUND" -ge "$ROUNDS_REQUIRED" ]; then
        FORCE_NEXT="synthesis"
      else
        FORCE_NEXT="round_${NEXT_ROUND}"
      fi ;;
    synthesis)     FORCE_NEXT="implement" ;;
    implement)     FORCE_NEXT="cpo_backlog" ;;
    ceo_gate)      FORCE_NEXT="waiting_ceo" ;;
    cpo_backlog)   FORCE_NEXT="trainer" ;;
    trainer)       FORCE_NEXT="compact_check" ;;
    compact_check) FORCE_NEXT="mark_done" ;;
    mark_done)     FORCE_NEXT="transition" ;;
    done)          FORCE_NEXT="mark_done" ;;
    *)             FORCE_NEXT="" ;;
  esac
  if [ -n "$FORCE_NEXT" ]; then
    python3 -c "
import json, os
cp_path = '$PROJECT_PATH/.claude/oms-checkpoint.json'
try:
    cp = json.load(open(cp_path))
    if cp.get('next') == '$NEXT':  # Only advance if agent didn't already
        cp['next'] = '$FORCE_NEXT'
        if '$NEXT' == 'mark_done':
            # transition checkpoint must be fresh — strip stale carry-over fields
            cp.pop('completion_reported', None)
        tmp = cp_path + '.tmp'
        json.dump(cp, open(tmp, 'w'))
        os.replace(tmp, cp_path)
        import sys; print('[dispatcher] Force-advanced checkpoint: $NEXT -> $FORCE_NEXT', file=sys.stderr)
except Exception as e:
    import sys; print(f'[dispatcher] Checkpoint advance error: {e}', file=sys.stderr)
" 2>&1 >&2
  fi
fi

# _auto fallback: if Claude didn't write the checkpoint, extract task_id from output and write it
if [ -z "$TASK_ID" ] && [ ! -f "$PROJECT_PATH/.claude/oms-checkpoint.json" ]; then
  EXTRACTED_TASK=$(echo "$OUTPUT" | grep -oE 'TASK:[a-z0-9][a-z0-9-]+' | head -1 | sed 's/TASK://')
  if [ -n "$EXTRACTED_TASK" ]; then
    echo "[dispatcher] _auto fallback: writing checkpoint for $EXTRACTED_TASK" >&2
    python3 -c "
import json, os
cp = {'task_id': '$EXTRACTED_TASK', 'next': 'round_1', 'rounds_required': 3}
p = '$PROJECT_PATH/.claude/oms-checkpoint.json'
os.makedirs(os.path.dirname(p), exist_ok=True)
json.dump(cp, open(p + '.tmp', 'w'))
os.replace(p + '.tmp', p)
" 2>&1 >&2
  fi
fi

# Validate checkpoint next value against allowlist — catches bad writes before they corrupt the pipeline
if [ -f "$PROJECT_PATH/.claude/oms-checkpoint.json" ]; then
  python3 -c "
import json, os, sys, re
cp_path = '$PROJECT_PATH/.claude/oms-checkpoint.json'
try:
    cp = json.load(open(cp_path))
except Exception:
    sys.exit(0)  # unreadable checkpoint — dispatcher will catch on next cycle

nxt = cp.get('next', '')
valid = {
    'router', 'ceo_gate', 'synthesis', 'implement', 'log',
    'cpo_backlog', 'trainer', 'compact_check', 'mark_done',
    'transition', 'waiting_ceo', 'pipeline_frozen', 'complete',
    'done',  # legacy alias
    '',      # empty = not yet started
}
if nxt in valid or re.fullmatch(r'round_[1-9][0-9]?', nxt):
    sys.exit(0)  # valid

# Invalid next value — freeze then hand to Watcher
print(f'[dispatcher] INVALID next value \"{nxt}\" — freezing pipeline for $PROJECT_SLUG', file=sys.stderr)
cp['frozen_step'] = nxt
cp['next'] = 'pipeline_frozen'
tmp = cp_path + '.tmp'
json.dump(cp, open(tmp, 'w'))
os.replace(tmp, cp_path)
print('INVALID_NEXT')  # sentinel for bash
sys.exit(1)
" 2>/dev/null
  POSTWRITE_EXIT=$?
  if [ $POSTWRITE_EXIT -ne 0 ]; then
    WATCHER_OUT=$(python3 "$HOME/.claude/bin/oms-watcher.py" \
      "$PROJECT_PATH/.claude/oms-checkpoint.json" \
      "$NEXT" "$TASK_ID" 2>>"${STEP_LOG:-/dev/stderr}")
    # Append watcher notification to output regardless of exit code
    OUTPUT="$OUTPUT
$WATCHER_OUT"
  fi
fi

echo "$OUTPUT"
exit $EXIT_CODE
