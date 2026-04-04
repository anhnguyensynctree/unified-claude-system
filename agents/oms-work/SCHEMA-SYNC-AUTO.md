# Schema Sync — Automatic Field Synchronization (BLOCKING)

**Status:** ✅ Automatic and Blocking as of 2026-04-04

REQUIRED_FIELDS in `validate-queue.py` automatically stay in sync with the task-schema.md "Task Queued Format" section.

---

## Before vs. After

### Before (Manual Sync)
```
Developer edits task-schema.md, adds new required field
    ↓
Developer manually updates REQUIRED_FIELDS in validate-queue.py
    ↓
Risk: Mismatch — task-schema.md and validate-queue.py out of sync
```

### After (Automatic Sync, Blocking)
```
Developer edits task-schema.md, adds new required field
    ↓
[schema-sync hook fires]
    ↓
Parses task-schema.md → extracts REQUIRED_FIELDS list
Compare with current validate-queue.py
    ↓
Mismatch detected!
    ↓
[schema-sync] added fields: New-Field
[schema-sync] validate-queue.py updated (17 required fields)
    ↓
✓ Write succeeds
Both files now in sync
```

**Guarantee:** Both files always match. Zero manual coordination needed.

---

## How It Works

### Hook Execution (PostToolUse)

When you edit/write `task-schema.md`:

```
1. Edit task-schema.md, add/remove required field
   ↓
2. [PostToolUse hook] schema-sync-hook.sh fires
   ↓
3. Hook calls: python3 ~/.claude/bin/sync-queue-schema.py
   ↓
4. Sync script:
   a) Parses task-schema.md "Task Queued Format" block
   b) Extracts field names (excludes Status, Script-*, omit fields)
   c) Compares with current REQUIRED_FIELDS in validate-queue.py
   d) If mismatch: auto-updates validate-queue.py
   e) If error: exits 1
   ↓
5. Hook checks exit code:
   - Exit 0 (success) → write succeeds ✓
   - Exit 1 (error) → write blocked (exit 2) ✗
   ↓
6. Result: Both files guaranteed in sync
```

---

## Field Extraction Rules

### What Gets Included

Fields listed in the "Task Queued Format" code block:
```markdown
- **Feature:** ...
- **Milestone:** ...
- **Department:** ...
...
```

**Are parsed and added to REQUIRED_FIELDS.**

### What Gets Excluded

1. **Status** — used for filtering, not validation
2. **Script-model, Script-timeout, Script-partial-results** — marked with "omit" option (optional)
3. Any field with "omit" in the line — explicitly optional

**Example exclusion:**
```markdown
- **Script-timeout:** 120s | 150s | 180s | omit
                                                  ↑
                                           Will be excluded
```

---

## Examples

### Example 1: Add a New Required Field

**Edit task-schema.md:**
```markdown
- **Model-hint:** ...
- **New-Field:** description  ← ADD THIS
- **Script-model:** ...
```

**Save → Hook fires:**
```
[schema-sync] added fields: New-Field
[schema-sync] validate-queue.py updated (18 required fields)
```

**Result:**
- validate-queue.py REQUIRED_FIELDS now includes "New-Field"
- Both files synced automatically
- Write succeeds

---

### Example 2: Remove a Required Field

**Edit task-schema.md:**
```markdown
- **Model-hint:** ...
- (delete Old-Field)  ← REMOVE THIS
- **Script-model:** ...
```

**Save → Hook fires:**
```
[schema-sync] removed fields: Old-Field
[schema-sync] validate-queue.py updated (16 required fields)
```

**Result:**
- validate-queue.py REQUIRED_FIELDS no longer includes "Old-Field"
- validate-queue.py validation updated automatically
- Write succeeds

---

### Example 3: Make Optional Field Required

**Edit task-schema.md:**
```markdown
- **Script-timeout:** 120s | 150s | 180s  ← Remove "omit"
```

**Save → Hook fires:**
```
[schema-sync] added fields: Script-timeout
[schema-sync] validate-queue.py updated (17 required fields)
```

**Result:**
- Script-timeout now validated as required
- All existing tasks without Script-timeout will fail validation
- Write succeeds, but Schema Gate now enforces new requirement

---

## Blocking Behavior

### When Write Is Blocked

Hook blocks write (exit 2) if:
1. **Schema parsing error** — task-schema.md format corrupted
2. **Validator reading error** — validate-queue.py corrupted
3. **Regex substitution failure** — REQUIRED_FIELDS format unexpected

**Output:**
```
[schema-sync] ⚠️  Schema validation failed — fix and try again
(write blocked)
```

### When Write Succeeds

Write succeeds (exit 0) if:
1. **Already in sync** — no changes needed
2. **Changes applied** — validate-queue.py updated successfully

**Output:**
```
[schema-sync] REQUIRED_FIELDS already in sync
```
or
```
[schema-sync] added fields: Field1, Field2
[schema-sync] validate-queue.py updated (18 required fields)
```

---

## Three-Layer Validation Order

All validators fire on every Edit/Write to `cleared-queue.md`:

```
1. SCHEMA VALIDATION (validate-queue.sh)
   ↓ Checks: required fields, format, sizing
   ↓ Blocks: ✅ exit 2 on violations

2. SCHEMA SYNC (schema-sync-hook.sh)
   ↓ Checks: REQUIRED_FIELDS match between files
   ↓ Auto-fixes: updates validate-queue.py if mismatch
   ↓ Blocks: ✅ exit 2 on error

3. MODEL-HINT VALIDATION (validate-model-hint.sh)
   ↓ Checks: all queued tasks have correct Model-hint
   ↓ Detects: contradictory flags
   ↓ Blocks: ✅ exit 2 on violations

All three must pass for write to succeed.
```

---

## Testing Schema Sync

### Test 1: Verify Current Sync Status
```bash
python3 ~/.claude/bin/sync-queue-schema.py 2>&1
```

**Output (if in sync):**
```
[schema-sync] REQUIRED_FIELDS already in sync
```

---

### Test 2: Test Sync Script Directly

```bash
# Check current fields in validate-queue.py
grep -A 20 "REQUIRED_FIELDS = " ~/.claude/bin/validate-queue.py

# Run sync (should report no changes if in sync)
python3 ~/.claude/bin/sync-queue-schema.py 2>&1
```

---

## How Developers Use This

### Add a New Field to Task Schema

1. Edit `task-schema.md`
   ```markdown
   - **New-Field:** description (required)
   ```

2. Save the file

3. Hook fires automatically:
   ```
   [schema-sync] added fields: New-Field
   [schema-sync] validate-queue.py updated
   ```

4. Done — both files in sync, no manual steps

---

### Make Optional Field Required

1. Edit `task-schema.md`
   ```markdown
   - **Script-timeout:** 120s | 150s | 180s  ← Remove "omit"
   ```

2. Save the file

3. Hook fires:
   ```
   [schema-sync] added fields: Script-timeout
   ```

4. Now all new tasks must include Script-timeout
   (Existing tasks won't fail until they're edited)

---

## Files Involved

| File | Role | Who Updates |
|---|---|---|
| `task-schema.md` | Schema definition (source of truth) | Developer edits manually |
| `validate-queue.py` | Validation script (consumer of schema) | Hook auto-updates |
| `schema-sync-hook.sh` | Hook that triggers sync | System (automatic) |
| `sync-queue-schema.py` | Script that parses & updates | System (runs via hook) |

---

## Summary

**Schema sync is now:**
- ✅ Automatic — no manual field updates needed
- ✅ Blocking — write fails if sync can't succeed
- ✅ Transparent — hook output shows what changed
- ✅ Bidirectional — parses task-schema.md, updates validate-queue.py

**Guarantee:** REQUIRED_FIELDS in validate-queue.py always matches the "Task Queued Format" in task-schema.md. Zero drift possible.
