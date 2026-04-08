#!/usr/bin/env bash
# PreToolUse hook: Smart Grep routing
# Default: BLOCK (use mgrep). Allow ONLY simple exact-match patterns.
# mgrep is the primary search tool. Grep is only for trivial literal lookups.

HOOK_INPUT=$(cat)
PATTERN=$(echo "$HOOK_INPUT" | jq -r '.tool_input.pattern // empty' 2>/dev/null)

# No pattern = block
if [ -z "$PATTERN" ]; then
    echo '[BLOCKED] No pattern — use mgrep skill for search. Invoke: Skill tool with skill="mgrep:mgrep"' >&2
    exit 2
fi

# Length check: patterns > 40 chars are likely semantic/complex
if [ "${#PATTERN}" -gt 40 ]; then
    echo "[BLOCKED] Pattern too long for exact match (${#PATTERN} chars). Use mgrep skill instead." >&2
    exit 2
fi

# Check if pattern contains ONLY exact-match characters:
# alphanumeric, dots, underscores, colons, hyphens, parens, slashes, brackets, at-signs, equals
# NO spaces, NO regex metacharacters (.*+?{}|^$)
if echo "$PATTERN" | grep -qE '^[a-zA-Z0-9._:@/=\(\)\[\]-]+$'; then
    # Simple exact match — allow Grep tool
    exit 0
fi

# Check for common regex metacharacters
if echo "$PATTERN" | grep -qE '[*+?{}|^$]|\\[sdwb]'; then
    echo "[BLOCKED] Regex pattern detected. Use mgrep skill for complex searches." >&2
    exit 2
fi

# Contains spaces = likely semantic/natural language
if echo "$PATTERN" | grep -q ' '; then
    echo "[BLOCKED] Multi-word pattern — use mgrep skill for semantic search." >&2
    exit 2
fi

# Default: block — mgrep is the primary tool
echo '[BLOCKED] Use mgrep skill for search. Grep only for simple exact identifiers. Invoke: Skill tool with skill="mgrep:mgrep"' >&2
exit 2
