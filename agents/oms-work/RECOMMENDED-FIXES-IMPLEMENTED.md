# Recommended Fixes for Optional Flags — Status: ✅ COMPLETE

All four recommended fixes have been implemented to enable OMS system understanding of optional task flags.

---

## 1. ✅ Update Elaboration Agent Briefing

**File:** `~/.claude/agents/task-elaboration/persona.md`

**Changes:** Added new section "Optional Task Flags — when to add them"

**Content:**
- `speed-critical: true` guidance:
  - When: task must complete in <5 min for synchronous/interactive use case
  - Examples: dashboard briefing (CEO waiting), critical-path blocker (team waiting)
  - Do NOT set for: async work, non-critical features, long-form research

- `large-context: true` guidance:
  - When: task requires reading >50K tokens of context at once
  - Examples: multi-doc synthesis (3+ large docs), historical data analysis
  - Do NOT set for: incremental processing, current-state research, code tasks

- `infra-critical: true` note: Already set by Synthesizer, do not modify

**Effect:** Elaboration agents now understand WHEN to set optional flags based on OMS discussion context.

---

## 2. ✅ Update Router Briefing

**File:** `~/.claude/agents/router/persona.md`

**Changes:** Added new section "Task Characteristics — Optional Flags"

**Content:**
- `speed-critical: true` definition:
  - Task has hard time constraint — result needed <5 min (synchronous/interactive)
  - Example: executive briefing request, critical-path blocker
  - Implication: Router may note this but tier/roster are unaffected
  - Model-hint routing respects flag automatically

- `large-context: true` definition:
  - Task requires processing >50K tokens of context at once
  - Example: multi-document synthesis, historical analysis with 3+ sources
  - Implication: Router may note this but tier/roster are unaffected
  - Model-hint routing respects flag automatically

- Handling rule:
  - Router does NOT change tier or roster based on optional flags
  - Router DOES surface them in agent briefing as context
  - If contradictory flags detected → flag as Stage-Gate warning

**Effect:** Router now surfaces optional flags in briefings without changing task classification. Flags are transparent constraints, not complexity drivers.

---

## 3. ✅ Update OMS-Work Executor

**File:** `~/.claude/skills/oms-work/SKILL.md`

**Changes:** Updated "Model routing per task" section with optional flags documentation

**Content:**
- New subsection: "Optional task flags — check before routing"
- What to log:
  - `speed-critical: true` → Executor has hard time constraint
  - `large-context: true` → Executor needs to process 50K+ tokens
- How to log:
  ```
  ▶ TASK-100 — Analyze user patterns [speed-critical] `running`
  ```
- Clarification: Flags do NOT change routing — they are author's constraints already respected by Model-hint derivation

**Effect:** OMS-work executor now logs optional flags in Discord notifications and understands their purpose (context only, no routing change).

---

## 4. ✅ Update Validation Script

**File:** `~/.claude/bin/validate-model-hint.py`

**Changes:** Added contradictory flag detection to `derive_model_hint()` function

**Content:**
- Validation Rule 1: impl tasks cannot have large-context flag
  ```python
  if task_type == 'impl' and large_context:
      return None, 'ERROR: impl tasks cannot have large-context flag...'
  ```
  Reason: Code models handle context natively; flag is research-only

- Validation Rule 2: speed-critical + large-context + ≥4 files is contradictory
  ```python
  if speed_critical and large_context and file_count >= 4:
      return None, 'ERROR: ...contradictory (large context requires depth...)'
  ```
  Reason: Large context needs depth; speed sacrifices depth. Fundamentally opposed.

**Effect:** Validation script automatically:
- Derives correct Model-hint based on flags
- Detects contradictory flag combinations
- Blocks queuing if contradictions found
- Provides clear error messages for correction

---

## Testing & Validation

### Test 1: Valid speed-critical flag
```markdown
Type: research
File-count: 2
Speed-critical: true
```
**Result:** ✓ Suggests `gemma` (Research + speed-critical)

### Test 2: Valid large-context flag
```markdown
Type: research
File-count: 4
Large-context: true
```
**Result:** ✓ Suggests `nemotron` (Research + large-context)

### Test 3: Contradictory impl + large-context
```markdown
Type: impl
Large-context: true
```
**Result:** ✗ ERROR: impl tasks cannot have large-context flag

### Test 4: Contradictory speed + context + large files
```markdown
Type: research
File-count: 5
Speed-critical: true
Large-context: true
```
**Result:** ✗ ERROR: contradictory constraints

---

## System Flow After Implementation

### 1. Task Elaboration
Elaboration agent reads OMS discussion context, decides:
- "Is this time-sensitive?" → Set `speed-critical: true` if <5 min needed
- "Is this context-heavy?" → Set `large-context: true` if >50K tokens needed

### 2. Router Processing
Router parses task, surfaces flags in briefing:
```
Agent briefing: "Speed-critical requirement noted — task has <5 min time constraint"
```
Tier/roster remain unchanged. Flags are informational only.

### 3. Validation
Before queuing, validation script checks:
- Contradictory flags → ERROR (halt queuing, show correction)
- Valid flags → Auto-derive Model-hint respecting constraints
- Examples:
  - `research + speed-critical` → `Model-hint: gemma`
  - `research + large-context` → `Model-hint: nemotron`

### 4. OMS-Work Execution
Executor logs flags in Discord:
```
▶ TASK-050 — Analyze churn spike [speed-critical] running
  Model-hint: gemma (70s latency, ⭐⭐⭐ quality)
  Reason: Research + speed-critical forces faster model
```

### 5. Model Selection (Automatic)
Model-hint derivation already includes flags:
```python
if speed_critical:
    return 'gemma'  # 70s, trade depth for speed
if large_context:
    return 'nemotron'  # 262K context for large docs
# default → qwen (1M context, best reasoning)
```

---

## Documentation

### New Files Created
- `~/.claude/agents/oms-work/OPTIONAL-FLAGS.md` — Comprehensive guide with examples, workflow scenarios, and trade-offs

### Files Updated
1. `~/.claude/agents/task-elaboration/persona.md` — Elaboration guidance
2. `~/.claude/agents/router/persona.md` — Router handling
3. `~/.claude/skills/oms-work/SKILL.md` — Executor logging
4. `~/.claude/bin/validate-model-hint.py` — Flag validation logic

---

## Summary Table

| Component | Responsibility | Implementation | Status |
|---|---|---|---|
| **Elaboration Agent** | Decide IF flags apply | Added "Optional Task Flags" section to persona | ✅ |
| **Router** | Surface flags contextually | Added flag handling section to persona | ✅ |
| **OMS-Work Executor** | Log flags in notifications | Updated skill with flag documentation | ✅ |
| **Validation Script** | Detect contradictions | Added contradiction detection logic | ✅ |
| **Documentation** | Explain system behavior | Created OPTIONAL-FLAGS.md comprehensive guide | ✅ |

---

## How to Use

### For Elaboration Agents
When writing tasks, ask:
1. "Does this need <5 min result?" → Add `speed-critical: true`
2. "Does this read >50K tokens?" → Add `large-context: true`
3. "Do both apply together?" → Check if contradictory

### For Teams
- Flags are optional — use only when constraints are real
- Contradictions are caught at validation time, before queuing
- Model-hint respects flags automatically — no manual override needed
- See OPTIONAL-FLAGS.md for examples and trade-offs

### For Executors (OMS-Work)
- Log flags in Discord: `[flag-name]` in the running message
- Model-hint already respects flags — no routing changes needed
- Flags are purely informational context for the executor

---

## Commits

All changes committed as:
```
feat(oms): add optional flags support for task characteristics
docs(oms): add comprehensive optional flags guide
```

Validation tested with contradictory and valid flag combinations. All tests pass.
