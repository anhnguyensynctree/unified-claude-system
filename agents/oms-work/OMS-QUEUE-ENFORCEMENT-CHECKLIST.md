# OMS Queue Enforcement Checklist — All Systems Active

**As of:** 2026-04-04  
**Status:** ✅ All three validation layers implemented and blocking

When you edit/write `cleared-queue.md` or `task-schema.md`, automatic validation fires. All violations block the write.

---

## Developer Checklist: Before Saving a Task

When adding or updating a task in `cleared-queue.md`, ensure:

- [ ] **Status** is set: `draft` or `queued`
- [ ] **Feature** references a real FEATURE-NNN
- [ ] **Milestone** matches a milestone from product-direction.ctx.md
- [ ] **Department** is valid: backend, frontend, qa, data, research, cto
- [ ] **Type** is valid: impl, research, gate
- [ ] **Spec** is one sentence using SHALL language
  - Example: `The system SHALL add OAuth 2.0 authentication so that users can login securely.`
- [ ] **Scenarios** follow GIVEN/WHEN/THEN format (2–4 scenarios)
  - Example: `GIVEN user clicks login button WHEN they enter valid credentials THEN dashboard loads`
- [ ] **Artifacts** lists all files (pipe-separated, with exports or "exists with real impl")
  - Example: `src/auth/oauth.ts — exports: loginUser, logoutUser | src/auth/middleware.ts — modified`
- [ ] **Produces** declares downstream contract (or "none")
- [ ] **Verify** has non-empty test/build command (for impl tasks)
  - Example: `npm test src/auth`
- [ ] **Context** lists files that will be pre-loaded (must exist)
- [ ] **Activated** names the agents doing the work
- [ ] **Validation** chain: dev→qa→em or researcher→cro→cpo (auto-determined by Type)
- [ ] **Depends** lists upstream tasks (or "none")
- [ ] **File-count** ≤ 4 (oversized tasks must be split)
- [ ] **Model-hint** is set correctly (auto-derived by hook, but you can check)

**When you save:**
```
Layer 1: Schema validation   → ✓ All required fields, format correct
Layer 2: Schema sync        → ✓ REQUIRED_FIELDS in sync
Layer 3: Model-hint check   → ✓ Model-hint correct
    ↓
Write succeeds ✓
```

---

## What Blocks the Write

### Layer 1: Schema Violations
```
[queue-validator] Write blocked — fix violations before saving cleared-queue.md
  TASK-NNN: Missing required field: Spec
  TASK-NNN: File-count 5 exceeds max 4 — task must be split
  TASK-NNN: Scenarios don't follow GIVEN/WHEN/THEN format
```

**Fix:** Add missing fields, reformat, or split oversized tasks.

---

### Layer 2: Schema Sync Failure
```
[schema-sync] ⚠️  Schema validation failed — fix and try again
```

**When:** Editing `task-schema.md` and format is corrupted or validate-queue.py cannot be read.

**Fix:** Check task-schema.md syntax, or verify validate-queue.py is readable.

---

### Layer 3: Model-Hint Violations
```
[model-hint] BLOCKED: Model-hint violations in cleared-queue.md:
  TASK-NNN: Missing Model-hint → suggest qwen-coder
  TASK-NNN: Model-hint: gemma → should be qwen-coder
  TASK-NNN: ERROR: impl tasks cannot have large-context flag
[model-hint] Fix all suggestions above before queuing.
```

**Fix:** 
- Add suggested Model-hint
- Or change task Type/File-count/flags to match desired model
- Remove contradictory flags

---

## How Auto-Fixes Work

### Schema Sync Auto-Fix
When you edit `task-schema.md`:
1. Add/remove/modify required fields
2. Save → hook detects changes
3. Hook auto-updates `validate-queue.py` REQUIRED_FIELDS
4. Write succeeds

**You don't need to manually update validate-queue.py — hook does it.**

### Model-Hint Auto-Derivation
When you save `cleared-queue.md`:
1. Validation script examines each queued task
2. Reads: Type, File-count, optional flags
3. Derives correct Model-hint automatically
4. If missing → suggests it
5. If wrong → shows correction

**You don't need to manually calculate Model-hint — hook suggests it.**

---

## Quick Decision Trees

### Is My Model-Hint Correct?

```
Type: impl
├─ File-count ≤ 3 + Verify
│  ├─ speed-critical: true  → gemma ✓
│  └─ default             → qwen-coder ✓
├─ File-count = 4  → ERROR: must split
└─ File-count > 4  → ERROR: must split

Type: research
├─ File-count ≤ 3
│  ├─ large-context: true  → nemotron ✓
│  ├─ speed-critical: true → gemma ✓
│  └─ default             → qwen ✓
├─ File-count 4–5
│  ├─ large-context: true  → nemotron ✓
│  ├─ speed-critical: true → gemma ✓
│  └─ default             → gpt-oss ✓
└─ File-count > 5  → ERROR: must split

Type: gate OR Infra-critical: true
└─ sonnet ✓ (always)
```

---

### Can I Use These Flags Together?

```
speed-critical + large-context?
├─ File-count < 4
│  └─ ✓ Allowed (but pick one to avoid ambiguity)
└─ File-count ≥ 4
   └─ ✗ ERROR: contradictory

impl + large-context?
└─ ✗ ERROR: impl handles context natively, flag is research-only

impl + speed-critical?
├─ File-count ≤ 3
│  └─ ✓ Allowed (forces gemma)
└─ File-count > 3
   └─ ✗ ERROR: must split first
```

---

## Example: Complete Task (Will Pass All Validations)

```markdown
## TASK-100 — Add JWT token refresh rotation
- **Status:** queued
- **Feature:** FEATURE-050
- **Milestone:** auth-security
- **Department:** backend
- **Type:** impl
- **Infra-critical:** false
- **Spec:** The system SHALL implement JWT refresh token rotation so that expired tokens cannot be reused.
- **Scenarios:** GIVEN a valid refresh token WHEN it's used to get a new access token THEN a new refresh token is issued and the old one is invalidated | GIVEN an expired refresh token WHEN a new access token is requested THEN HTTP 401 is returned
- **Artifacts:** src/auth/tokens.ts — exports: refreshToken, revokeToken | src/auth/middleware.ts — modified
- **Produces:** exports: refreshToken, revokeToken
- **Verify:** npm test src/auth
- **Context:** src/auth/types.ts, lib/db.ts
- **Activated:** backend-developer
- **Validation:** dev → qa → em
- **Depends:** TASK-099
- **File-count:** 2
- **Model-hint:** qwen-coder
```

**When saved:**
```
[queue-validator] ✓ All fields present, format valid
[schema-sync] REQUIRED_FIELDS already in sync
[model-hint] ✓ Model-hint correct: impl ≤3 files + verify → qwen-coder

Write succeeds ✓
```

---

## Example: Task With Issues (Will Be Blocked)

```markdown
## TASK-101 — Add user authentication (missing fields + wrong hint)
- **Status:** queued
- **Feature:** FEATURE-051
(missing Milestone, Department, Spec, etc.)
- **Type:** impl
- **Artifacts:** src/auth/
- **File-count:** 6
- **Model-hint:** nemotron
```

**When saved:**
```
[queue-validator] Write blocked — fix violations
  TASK-101: Missing required field: Milestone
  TASK-101: Missing required field: Department
  TASK-101: Missing required field: Spec
  TASK-101: File-count 6 exceeds max 4 — task must be split

(write blocked, before Layer 2 & 3 even run)

FIX: Add missing fields, split into multiple tasks
```

---

## Documentation Index

For more details, see:

1. **VALIDATION-ENFORCEMENT-SUMMARY.md**
   - Three-layer blocking architecture
   - What each layer checks and blocks
   - Side-by-side comparison (before/after)

2. **SCHEMA-SYNC-AUTO.md**
   - How automatic field synchronization works
   - Field extraction rules
   - Examples: add/remove/make-required fields
   - Testing schema sync

3. **MODEL-HINT-ENFORCEMENT.md**
   - Model-hint validation rules
   - Auto-derivation logic
   - Contradictory flag detection
   - Comprehensive testing guide

4. **OPTIONAL-FLAGS.md**
   - When to set speed-critical
   - When to set large-context
   - Impact on Model-hint routing
   - Workflow examples with trade-offs

5. **task-schema.md** (this file, section "Queue Gate")
   - Master schema definition
   - All required/optional fields
   - Validation rules
   - Model-hint derivation

---

## Quick Reference: Fields Always Required

```
Feature      — FEATURE-NNN from your feature list
Milestone    — milestone name from product-direction.ctx.md
Department   — backend, frontend, qa, data, research, cto
Type         — impl, research, gate
Spec         — one sentence, SHALL language
Scenarios    — GIVEN/WHEN/THEN format
Artifacts    — files to create/modify
Produces     — downstream contract
Verify       — test/build command (for impl)
Context      — files to pre-load
Activated    — agents doing the work
Validation   — validation chain (auto: dev→qa→em or researcher→cro→cpo)
Depends      — upstream tasks (or "none")
File-count   — number of artifacts (must be ≤ 4)
Model-hint   — auto-derived: qwen-coder | qwen | ... | sonnet
```

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `Missing required field: Spec` | Spec not filled | Add Spec using SHALL language |
| `File-count 5 exceeds max 4` | Oversized task | Split into 2–3 smaller tasks |
| `Model-hint: gemma → should be qwen-coder` | Wrong model selected | Use suggested model, or change Type/File-count |
| `impl tasks cannot have large-context flag` | Contradictory flag | Remove large-context (impl doesn't use it) |
| `Schema validation failed` | task-schema.md corrupted | Check syntax in Task Queued Format section |

---

## Key Points

1. **All validations run automatically** — no manual steps
2. **All violations block writes** — zero gaps allowed
3. **Auto-fixes where possible** — schema sync, Model-hint suggestion
4. **Clear error messages** — fix suggestions included
5. **Parallel hooks** — all three check on every save

**Result:** Perfect queue data. Every task has correct fields, synced schema, and optimal model routing.

✅ **You're protected by three layers of blocking validation.**
