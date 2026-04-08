#!/usr/bin/env bash
# PreToolUse hook: require explicit model on ALL Agent tool calls.
#
# Subagents inherit the parent's model by default. Since the user runs Opus
# interactively, unspecified agents would run on Opus (20x costlier than needed).
# This hook forces every Agent call to declare its model explicitly.
#
# OMS-specific routing is handled by enforce-oms-model.sh (runs first).
# This hook catches everything else.
set -euo pipefail

INPUT=$(cat)

# Only process Agent tool calls
TOOL=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || true)
[ "$TOOL" = "Agent" ] || exit 0

# Extract model and subagent_type
eval "$(echo "$INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
ti = data.get('tool_input', {})
model = ti.get('model', '')
subagent = ti.get('subagent_type', '')
prompt = ti.get('prompt', '')[:500].lower()
print(f'MODEL={model!r}')
print(f'SUBAGENT={subagent!r}')
print(f'PROMPT_LOWER={prompt!r}')
" 2>/dev/null)" || exit 0

# Skip if OMS hook already handles this (detect OMS markers)
if echo "$PROMPT_LOWER" | grep -qE '(router|facilitator|synthesizer|ceo.gate|path.diversity|trainer|context.optimizer|task.elaboration|oms.work)'; then
    exit 0
fi

# Hardcoded agents that don't need model override — they ignore it
case "$SUBAGENT" in
    Explore|claude-code-guide|statusline-setup)
        exit 0
        ;;
esac

# Require explicit model on all other Agent calls
if [ -z "$MODEL" ]; then
    echo "[agent-model] ⛔ Agent call without explicit model param." >&2
    echo "[agent-model] Add model: \"sonnet\" (default), \"haiku\" (judge/search), or \"opus\" (architect)" >&2
    echo "[agent-model] Optimal defaults:" >&2
    echo "  Plan agent         → model: \"sonnet\"" >&2
    echo "  Research agent     → model: \"sonnet\"" >&2
    echo "  Code writing agent → model: \"sonnet\"" >&2
    echo "  Validator/judge    → model: \"haiku\"" >&2
    echo "  Architecture (5+ files, high-stakes) → model: \"opus\"" >&2
    exit 2
fi

exit 0
