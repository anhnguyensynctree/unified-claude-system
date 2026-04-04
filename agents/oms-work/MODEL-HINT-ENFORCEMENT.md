# Model-Hint Enforcement — Blocking Validation for All OMS Tasks

**Status:** ✅ Enforced as of 2026-04-04

All OMS queued tasks route through the LLM router. **Model-hint is mandatory and enforced.**

---

## Before vs. After

### Before (Advisory Mode)
```
Task queued with missing/wrong Model-hint
    ↓
[model-hint] SUGGESTIONS for cleared-queue.md:
  TASK-100: Missing Model-hint → suggest qwen-coder
    ↓
✓ Write succeeds (exit 0)
    ↓
Task queued without Model-hint
LLM router has no hint — MUST default to fallback (wastes resources)
```

**Problem:** Model-hint gaps could reach the executor, forcing fallback logic and suboptimal routing.

---

### After (Enforced Mode)
```
Task queued with missing/wrong Model-hint
    ↓
[model-hint] BLOCKED: Model-hint violations in cleared-queue.md:
  TASK-100: Missing Model-hint → suggest qwen-coder
[model-hint] Fix all suggestions above before queuing.
    ↓
✗ Write blocked (exit 2)
    ↓
Developer must fix Model-hint before save succeeds
    ↓
All tasks reach router with correct Model-hint
LLM router routes with right model on first try (optimal latency/cost)
```

**Benefit:** Zero Model-hint discrepancies. Every task has correct routing hint.

---

## What Gets Blocked

### 1. Missing Model-hint
```markdown
## TASK-100 — Example
- **Type:** impl
- **File-count:** 2
- **Verify:** npm test
- (no Model-hint field)
```

**Error:**
```
[model-hint] BLOCKED: Model-hint violations
  TASK-100: Missing Model-hint → suggest qwen-coder
```

**Fix:** Add `- **Model-hint:** qwen-coder`

---

### 2. Wrong Model-hint
```markdown
## TASK-100 — Example
- **Type:** impl
- **File-count:** 2
- **Verify:** npm test
- **Model-hint:** gemma  ← Wrong! Impl ≤3 files should be qwen-coder
```

**Error:**
```
[model-hint] BLOCKED: Model-hint violations
  TASK-100: Model-hint: gemma → should be qwen-coder
```

**Fix:** Change to `- **Model-hint:** qwen-coder`

---

### 3. Contradictory Flags
```markdown
## TASK-100 — Example
- **Type:** impl
- **Large-context:** true  ← ERROR! Impl tasks don't use this flag
```

**Error:**
```
[model-hint] BLOCKED: Model-hint violations
  TASK-100: ERROR: impl tasks cannot have large-context flag
```

**Fix:** Remove `large-context` flag (impl handles context natively)

---

## Validation Pipeline

### Three Layers of Blocking Validation

```
1. SCHEMA VALIDATION (validate-queue.sh)
   ↓ Checks: Required fields, format compliance, sizing rules
   ↓ Blocks: Missing/wrong field values
   ↓ Exit: 2 if violations
   
2. SCHEMA SYNC (schema-sync-hook.sh)
   ↓ Checks: REQUIRED_FIELDS match between script and task-schema.md
   ↓ Warns: File sync issues
   ↓ Exit: 0 (non-blocking, informational)
   
3. MODEL-HINT VALIDATION (validate-model-hint.sh)  ← NEW ENFORCEMENT
   ↓ Checks: All queued tasks have correct Model-hint
   ↓ Auto-derives: Based on Type + File-count + optional flags
   ↓ Detects: Contradictory flag combinations
   ↓ Blocks: Missing/wrong/contradictory hints
   ↓ Exit: 2 if violations
```

### Execution Order (PostToolUse Hook)
```
Edit/Write cleared-queue.md
    ↓
1. validate-queue.sh         → exit 0 or 2 (BLOCKING)
2. schema-sync-hook.sh       → exit 0 (WARNS ONLY)
3. validate-model-hint.sh    → exit 0 or 2 (BLOCKING)
    ↓
Write succeeds (all validations passed)
or
Write blocked (one or more validations failed)
```

---

## Model-Hint Auto-Derivation Rules

**Elaboration agents don't set Model-hint manually** — validation script auto-derives it.

### Implementation Tasks
```
Type: impl
File-count: 1–3 + Verify exists
    ↓
Default:           qwen-coder
With speed-critical: gemma
```

### Research Tasks
```
Type: research
File-count: 1–3
    ↓
Default:              qwen (best reasoning, 1M context)
With speed-critical:  gemma (70s, ⭐⭐⭐)
With large-context:   nemotron (262K context)
```

### Gate & Infra-Critical
```
Type: gate OR Infra-critical: true
    ↓
Always: sonnet (Anthropic subscription, ⭐⭐⭐⭐⭐ quality)
```

---

## Contradictory Flag Detection

### Error 1: impl + large-context
```python
if task_type == 'impl' and large_context:
    return ERROR: "impl tasks cannot have large-context flag"
```

**Why:** Code models (qwen-coder, gemma) handle large context natively. Flag is research-only.

**Fix:** Remove `large-context: true` from impl tasks.

---

### Error 2: speed-critical + large-context + ≥4 files
```python
if speed_critical and large_context and file_count >= 4:
    return ERROR: "contradictory (large context requires depth, speed requires heuristics)"
```

**Why:** 
- `large-context: true` = "I need to reason deeply over lots of information"
- `speed-critical: true` = "I need a fast answer, trade depth for speed"
- With 4+ files (large context), these are fundamentally opposed

**Fix:** Choose ONE:
- Remove `speed-critical` if you need depth
- Remove `large-context` if you need speed
- Split into two tasks if both matter

---

## Workflow Example

### Scenario: Add user authentication to app

**Elaboration agent writes draft:**
```markdown
## TASK-050 — Implement OAuth 2.0 authentication
- **Type:** impl
- **File-count:** 3
- **Verify:** npm test src/auth
- (no Model-hint — will be auto-derived)
```

**Editor saves → validation hook fires:**
```
1. Schema validation: ✓ All required fields present, format OK
2. Schema sync: ✓ REQUIRED_FIELDS match task-schema.md
3. Model-hint validation:
   Type: impl, File-count: 3, Verify: present
   → Auto-derive: qwen-coder (impl ≤3 files + verify)
   → Check: No contradictory flags
   → Result: ✓ Model-hint auto-derived
```

**Hook output:**
```
[model-hint] ✓ All Model-hints correct in cleared-queue.md
```

**Write succeeds.** Task in queue now has:
```markdown
- **Model-hint:** qwen-coder  ← Added by validation, not by hand
```

**LLM router receives:**
```
TASK-050: OAuth 2.0 auth
Model-hint: qwen-coder
Route: LiteLLM → qwen3-coder:free
Latency: ~100s
Cost: $0
```

---

## Testing Model-Hint Enforcement

### Test 1: Missing Model-hint (Blocked)
```bash
cat > /tmp/test.md << 'EOF'
## TASK-100
- **Type:** impl
- **File-count:** 1
- **Verify:** npm test
EOF

python3 ~/.claude/bin/validate-model-hint.py /tmp/test.md 2>&1
# Output: [model-hint] BLOCKED: ...Missing Model-hint
# Exit code: 1 (blocks write)
```

### Test 2: Wrong Model-hint (Blocked)
```bash
cat > /tmp/test.md << 'EOF'
## TASK-100
- **Type:** impl
- **File-count:** 1
- **Verify:** npm test
- **Model-hint:** nemotron  ← WRONG for impl
EOF

python3 ~/.claude/bin/validate-model-hint.py /tmp/test.md 2>&1
# Output: [model-hint] BLOCKED: ...should be qwen-coder
# Exit code: 1 (blocks write)
```

### Test 3: Correct Model-hint (Passes)
```bash
cat > /tmp/test.md << 'EOF'
## TASK-100
- **Type:** impl
- **File-count:** 1
- **Verify:** npm test
- **Model-hint:** qwen-coder  ← CORRECT
EOF

python3 ~/.claude/bin/validate-model-hint.py /tmp/test.md 2>&1
# Output: [model-hint] ✓ All Model-hints correct
# Exit code: 0 (write allowed)
```

### Test 4: Contradictory Flags (Blocked)
```bash
cat > /tmp/test.md << 'EOF'
## TASK-100
- **Type:** impl
- **File-count:** 1
- **Verify:** npm test
- **Large-context:** true  ← ERROR for impl
EOF

python3 ~/.claude/bin/validate-model-hint.py /tmp/test.md 2>&1
# Output: [model-hint] ERRORS...impl tasks cannot have large-context
# Exit code: 1 (blocks write)
```

---

## Files Changed

| File | Change | Effect |
|---|---|---|
| `validate-model-hint.py` | Returns 1 for suggestions (was 0) | Blocking behavior |
| `validate-model-hint.sh` | Exits 2 on error (was 0) | Blocks write on violations |
| `task-schema.md` | Added enforcement section, updated checklist | Documents blocking requirement |

---

## Impact

### For Elaboration Agents
- Model-hint is NOT set manually — auto-derived by validation
- If save fails: fix the task characteristics (Type, File-count, flags) to match desired model
- No guessing at Model-hint values

### For Executors (LLM Router)
- All queued tasks have correct Model-hint
- Zero fallback routing needed
- Optimal model selection on first try

### For the System
- Validation happens at queue time (not execution time)
- Contradictions caught early
- LLM router receives perfect data

---

## Rollout Timeline

**2026-04-04**: Enforcement enabled
- `validate-model-hint.py` now blocks on violations
- `validate-model-hint.sh` exits 2 to block writes
- Schema documentation updated

**Impact:** All new tasks queued after this date must have correct Model-hint, or write is blocked.

---

## FAQ

**Q: What if I don't know which Model-hint to use?**
A: You don't set it manually. Validation script auto-derives it from:
- Task Type (impl, research, gate)
- File-count (1-5)
- Optional flags (speed-critical, large-context)

Just fill in those fields, validation handles the rest.

**Q: My task is queued with "wrong" Model-hint according to the hook.**
A: Either:
1. Accept the suggestion — change task characteristics to match a different model
2. Or change the Model-hint to what the hook suggests

The hook is giving you two options. Pick one.

**Q: Can I override the Model-hint?**
A: No. If you believe the auto-derived hint is wrong, file an issue with why, and we'll update the derivation rules. The validation script is the source of truth.

**Q: What if I disagree with the contradictory flag error?**
A: Open an issue. But contradictions like impl+large-context are permanent design decisions in the OMS schema — they won't change.
