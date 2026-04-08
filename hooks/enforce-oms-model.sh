#!/usr/bin/env bash
# PreToolUse hook: enforce model routing for OMS Agent calls.
# Reads tool_input from stdin, checks if an OMS agent role is being invoked,
# and blocks if the wrong model is specified.
#
# Only fires on Agent tool calls where the prompt contains OMS role markers.
# Non-OMS Agent calls pass through unchanged.
set -euo pipefail

INPUT=$(cat)

# Only process Agent tool calls
TOOL=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || true)
[ "$TOOL" = "Agent" ] || exit 0

# Extract model and prompt from tool_input
eval "$(echo "$INPUT" | python3 -c "
import json, sys, os
data = json.load(sys.stdin)
ti = data.get('tool_input', {})
model = ti.get('model', '')
prompt = ti.get('prompt', '')[:2000].lower()
print(f'MODEL={model!r}')
print(f'PROMPT_LOWER={prompt[:500]!r}')
" 2>/dev/null)" || exit 0

# Skip non-OMS agent calls — detect OMS by role markers in the prompt
IS_OMS=false
OMS_ROLE=""

# Router detection
if echo "$PROMPT_LOWER" | grep -qE '(router|persona\.md.*router|routing.*tier|cynefin|activated_agents)'; then
    IS_OMS=true
    OMS_ROLE="router"
fi

# Facilitator detection
if echo "$PROMPT_LOWER" | grep -qE '(facilitator|position_distribution|da_protocol|livelock|convergence.*check)'; then
    IS_OMS=true
    if echo "$PROMPT_LOWER" | grep -qE '(pre.facilitator|short_circuit|stage.gate.*2)'; then
        OMS_ROLE="facilitator_pre"
    else
        OMS_ROLE="facilitator_full"
    fi
fi

# Synthesizer detection
if echo "$PROMPT_LOWER" | grep -qE '(synthesizer|synthesis.*decision|rationale.*cite|dissent.*preserve|action_items)'; then
    IS_OMS=true
    OMS_ROLE="synthesizer"
fi

# CEO Gate detection
if echo "$PROMPT_LOWER" | grep -qE '(ceo.gate|ceo.*mandatory|business.*model.*change|market.*pivot|vision.*conflict)'; then
    IS_OMS=true
    OMS_ROLE="facilitator_pre"  # CEO Gate Phase 1 uses haiku
fi

# Path Diversity detection
if echo "$PROMPT_LOWER" | grep -qE '(path.diversity|key_assumption|structurally.*distinct.*path)'; then
    IS_OMS=true
    OMS_ROLE="path_diversity"
fi

# Trainer detection
if echo "$PROMPT_LOWER" | grep -qE '(trainer|coaching.*note|sbi.*situation|lesson_candidates|validation.criteria)'; then
    IS_OMS=true
    OMS_ROLE="facilitator_full"  # Trainer uses sonnet
fi

# Context Optimizer detection
if echo "$PROMPT_LOWER" | grep -qE '(context.optimizer|efficiency.*check|ctx.*md.*audit)'; then
    IS_OMS=true
    OMS_ROLE="validator"  # Context Optimizer uses haiku
fi

# Elaboration detection
if echo "$PROMPT_LOWER" | grep -qE '(task.elaboration|elaboration.*agent|openspec|spec.*exploration)'; then
    IS_OMS=true
    OMS_ROLE="elaboration"
fi

# OMS Exec C-suite detection — only fires when no specific infrastructure role matched.
# Infrastructure agents (router, facilitator, synthesizer, etc.) keep their own model even in exec.
# Only C-suite discussion agents (CPO, CTO, CRO, CLO, CFO) map to oms-exec → opus.
if [ -z "$OMS_ROLE" ]; then
    if echo "$PROMPT_LOWER" | grep -qE '(exec.*mode|task_mode.*exec|oms.exec|c.suite|cpo.*lead|cto.*exec|cro.*exec|clo.*exec|cfo.*exec|product-direction\.ctx|strategic.*milestone|feature.*draft|cleared-queue.*draft)'; then
        IS_OMS=true
        OMS_ROLE="oms-exec"
    fi
fi

# Not an OMS call — pass through
$IS_OMS || exit 0

# Load expected model from oms-config.json
CONFIG="$HOME/.claude/oms-config.json"
if [ ! -f "$CONFIG" ]; then
    echo "[oms-model] WARNING: oms-config.json not found — cannot enforce model routing" >&2
    exit 0
fi

EXPECTED=$(python3 -c "
import json
c = json.load(open('$CONFIG'))
overrides = c.get('model_overrides', {})
role = '$OMS_ROLE'
print(overrides.get(role, ''))
" 2>/dev/null || true)

[ -n "$EXPECTED" ] || exit 0

# Check if model matches
if [ -z "$MODEL" ]; then
    echo "[oms-model] ⛔ Agent call for OMS role '$OMS_ROLE' has NO model param — must be '$EXPECTED'" >&2
    echo "[oms-model] Add model: \"$EXPECTED\" to the Agent tool call" >&2
    exit 2
fi

if [ "$MODEL" != "$EXPECTED" ]; then
    # Allow opus when it's an escalation (synthesizer_escalation)
    if [ "$OMS_ROLE" = "synthesizer" ] && [ "$MODEL" = "opus" ]; then
        # Check if escalation config allows opus
        ESCALATION=$(python3 -c "
import json
c = json.load(open('$CONFIG'))
print(c.get('model_overrides', {}).get('synthesizer_escalation', 'opus'))
" 2>/dev/null || true)
        if [ "$MODEL" = "$ESCALATION" ]; then
            exit 0  # Opus escalation is allowed
        fi
    fi

    echo "[oms-model] ⛔ OMS role '$OMS_ROLE' requires model '$EXPECTED' but got '$MODEL'" >&2
    echo "[oms-model] Fix: change model: \"$MODEL\" to model: \"$EXPECTED\" in the Agent tool call" >&2
    exit 2
fi

exit 0
