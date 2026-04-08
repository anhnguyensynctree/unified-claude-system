#!/usr/bin/env bash
# PostToolUse hook: TDD enforcement — BLOCK edits to implementation files without a test file
# 99% of implementation needs tests. Exceptions list covers the 1%.

HOOK_INPUT=$(cat)
FILE=$(echo "$HOOK_INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

[ -z "$FILE" ] && exit 0
[ -f "$FILE" ] || exit 0

# --- Exception: non-code files ---
echo "$FILE" | grep -qE '\.(ts|tsx|js|jsx|py)$' || exit 0

# --- Exception: this IS a test file ---
echo "$FILE" | grep -qE '\.(test|spec)\.(ts|tsx|js|jsx)$' && exit 0
echo "$FILE" | grep -qE '(test_|_test)\.' && exit 0
echo "$FILE" | grep -qE '(__tests__|e2e|tests)/' && exit 0

# --- Exception: config/type/index/barrel files ---
BASENAME=$(basename "$FILE")
echo "$BASENAME" | grep -qE '^(index|__init__|types|constants)\.' && exit 0
echo "$BASENAME" | grep -qE '\.config\.' && exit 0
echo "$BASENAME" | grep -qE '\.d\.ts$' && exit 0

# --- Exception: system/script directories ---
echo "$FILE" | grep -qE '(\.claude/|scripts/|bin/|hooks/|migrations/|seeds/|fixtures/|mocks/)' && exit 0

# --- Exception: project has no test infrastructure ---
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -n "$PROJECT_ROOT" ]; then
    # Check for any test files in the project
    HAS_TESTS=$(find "$PROJECT_ROOT" -maxdepth 4 \
        \( -name "*.test.*" -o -name "*.spec.*" -o -name "test_*" -o -name "*_test.*" \) \
        -not -path "*/node_modules/*" -not -path "*/.next/*" \
        2>/dev/null | head -1)
    if [ -z "$HAS_TESTS" ]; then
        # No test infrastructure — greenfield project, don't block
        exit 0
    fi
fi

# --- Check: does a test file exist for this module? ---
DIR=$(dirname "$FILE")
NAME=$(basename "$FILE" | sed 's/\.[^.]*$//')  # strip extension
EXT=$(basename "$FILE" | grep -oE '\.[^.]+$')   # get extension

# Search patterns for test file
FOUND=0
for test_pattern in \
    "$DIR/$NAME.test$EXT" \
    "$DIR/$NAME.spec$EXT" \
    "$DIR/__tests__/$NAME.test$EXT" \
    "$DIR/__tests__/$NAME$EXT" \
    "$DIR/test_$NAME.py" \
    "$DIR/../__tests__/$NAME.test$EXT" \
    "$DIR/../tests/test_$NAME.py" \
    ; do
    [ -f "$test_pattern" ] && FOUND=1 && break
done

# Also check for nearby test directories
if [ "$FOUND" -eq 0 ] && [ -n "$PROJECT_ROOT" ]; then
    # Broader search: any test file with this module name
    BROAD=$(find "$PROJECT_ROOT" -maxdepth 5 \
        \( -name "$NAME.test$EXT" -o -name "$NAME.spec$EXT" -o -name "test_$NAME.py" \) \
        -not -path "*/node_modules/*" \
        2>/dev/null | head -1)
    [ -n "$BROAD" ] && FOUND=1
fi

if [ "$FOUND" -eq 0 ]; then
    echo "[BLOCKED] TDD required: no test file found for $(basename "$FILE")" >&2
    echo "  Create the test file first, then edit the implementation." >&2
    echo "  Expected: $NAME.test$EXT or $NAME.spec$EXT" >&2
    exit 2
fi

exit 0
