# Optional Task Flags — OMS System Guide

Flags that modify task execution characteristics without changing tier or roster.

---

## Quick Reference

| Flag | Use When | Effect | Example |
|---|---|---|---|
| **speed-critical: true** | Need result in <5 min (sync/critical-path) | Model-hint → gemma (70s latency) | Executive briefing, blockers |
| **large-context: true** | Need to process >50K tokens at once | Model-hint → nemotron (262K context) | Multi-doc synthesis, history analysis |

---

## Flag: speed-critical: true

### When to set
- **Interactive result needed** — CEO is waiting for the answer (not async)
- **Critical path** — 3+ other tasks blocked waiting on this one
- **Time-sensitive briefing** — executive meeting, board presentation in <5 min
- Research task that needs fast reasoning over deep analysis

### When NOT to set
- Async work (overnight batch, scheduled report)
- Non-critical features, optional refinements
- Long-form research requiring depth
- Any impl task (code doesn't benefit from speed penalty)

### Model-hint impact
```
Research + speed-critical → gemma (70s, ⭐⭐⭐ quality)
           (no flag)      → qwen  (130s, ⭐⭐⭐⭐⭐ quality, best reasoning)
```

Trade: 60s faster, accept 15% lower quality reasoning.

### Example task definition
```markdown
## TASK-050 — Brief CEO on user churn spike
- **Type:** research
- **File-count:** 2
- **Speed-critical:** true
- **Spec:** CRO SHALL analyze churn spike from Q4 data and produce top 3 hypotheses with confidence scores within 4 minutes.
```

Result: Model-hint = `gemma` (70s latency instead of 130s).

---

## Flag: large-context: true

### When to set
- **Multi-document analysis** — reading 3+ large documents side-by-side (>30K total)
- **Historical data** — full user journey logs, complete audit trails, long conversations
- **Comparative research** — contrasting ≥5 different systems or frameworks
- Context exceeds 50K tokens

### When NOT to set
- Processing context incrementally (iterate over N small docs separately)
- Current-state analysis (no historical depth needed)
- Code tasks (code models handle large context natively)
- Implementing features (impl tasks don't use this flag)

### Model-hint impact
```
Research + large-context → nemotron (262K context, ⭐⭐⭐⭐⭐)
           (no flag)      → qwen     (1M context, ⭐⭐⭐⭐⭐ reasoning)
```

**Trade-off:** nemotron has 262K context (vs qwen's 1M), but different optimization focus. For <100K context, qwen is better. For 100K-262K, nemotron is specialized.

### Example task definition
```markdown
## TASK-051 — Compare 5 LLM architectures for selection decision
- **Type:** research
- **File-count:** 5
- **Large-context:** true
- **Spec:** CRO SHALL read Llama, Qwen, Nemotron, GPT-OSS, and Gemma whitepapers (~80K combined) and produce a comparison matrix with selection recommendation.
```

Result: Model-hint = `nemotron` (262K context, optimized for large documents).

---

## Contradictory Flags — Validation Errors

The validation system catches invalid flag combinations:

### Error 1: impl + large-context
```
ERROR: impl tasks cannot have large-context flag 
(code models handle context well; this flag is for research only)
```

**Why:** Implementation tasks use qwen-coder or gemma, both designed for code. They don't have context limitations. Large-context flag only applies to research.

**Fix:** Remove `large-context: true` from impl tasks.

### Error 2: speed-critical + large-context + file-count ≥ 4
```
ERROR: Research task with file-count 5 + large-context + speed-critical 
is contradictory (large context requires depth, speed requires heuristics)
```

**Why:** 
- `large-context` = "I need to reason deeply over lots of information"
- `speed-critical` = "I need a fast answer, trade depth for speed"
- These are fundamentally opposed when combined with 4+ files (very large context)

**Fix:** Choose ONE:
- Remove `speed-critical: true` if you really need depth (large-context remains)
- Remove `large-context: true` if you really need speed (speed-critical remains)
- Split into two tasks: one for deep analysis, one for fast synthesis

---

## How Each Component Handles Flags

### Elaboration Agent
- **Role:** Decide IF a task needs a flag based on author's OMS discussion notes
- **Process:** Read action_item context, determine if speed/context matter, set flag
- **Validation:** Run before queuing to catch contradictions

### Router
- **Role:** Surface flags in briefing but DON'T change tier/roster
- **Process:** Note in agent briefing: "speed-critical requirement noted", "large-context flag set"
- **Effect:** Zero routing impact — flags influence only Model-hint, not complexity classification

### OMS-Work Executor
- **Role:** Log flags in task progress notifications
- **Process:** Extract flags from task definition, include in Discord message
- **Example:** `▶ TASK-050 — Brief CEO on churn [speed-critical] running`
- **Effect:** Zero execution impact — Model-hint derivation already respects flags

### Validation Script
- **Role:** Catch contradictory combinations before queuing
- **Process:** Detect impl+large-context, speed+context+large-files, etc.
- **Effect:** Block queuing if contradictions found; suggest corrections

---

## Model-Hint Routing with Flags

The validation script automatically selects the right model based on flags:

### Research + speed-critical
```python
if speed_critical:
    return 'gemma'  # 70s, ⭐⭐⭐
# else → qwen (130s, ⭐⭐⭐⭐⭐ reasoning)
```

### Research + large-context
```python
if large_context:
    return 'nemotron'  # 262K context
# else → qwen (1M context, better reasoning)
```

### Both flags set + ≥4 files
```python
# ERROR — contradictory
```

### Impl + speed-critical (allowed)
```python
return 'gemma'  # ≤3 files + speed-critical → gemma (fastest)
```

---

## Workflow Example

### Scenario: User churn analysis + executive briefing

**Action item from OMS:** "Analyze Q4 churn spike + brief CEO by 3pm"

**Elaboration agent decision:**
```markdown
## TASK-050 — Analyze Q4 churn spike
- Type: research
- File-count: 2 (user events + cohort data)
- Speed-critical: true  ← Added: CEO needs answer in <5 min
- (no large-context: only 2 files, ~20K tokens)
```

**Router decision:**
- Tier: 1 (single domain — analytics, known analysis approach)
- Roster: CRO (lead), data analyst (supplementary)
- Briefing: "Speed-critical requirement: result needed within 5 minutes for executive briefing"

**Validation script:**
```
✓ Model-hint: gemma (Research + speed-critical → gemma)
```

**OMS-work execution:**
```
▶ TASK-050 — Analyze Q4 churn spike [speed-critical] running
  Model: gemma (70s latency)
  Context: user_events.json, cohort_analysis.json
```

**Result:** 
- Executive gets briefing in 80s wall-clock (gemma executes in 70s + overhead)
- Quality: 85% accuracy (vs 95% with qwen), sufficient for "why are we losing users?"
- Cost: $0.01 (gemma is free tier)

---

## Testing Flags

Run the validation script to test flag combinations:

```bash
# Valid: speed-critical alone
python3 ~/.claude/bin/validate-model-hint.py queue.md

# Valid: large-context alone
# (same script)

# Invalid: impl + large-context
# → ERROR: impl tasks cannot have large-context flag

# Invalid: speed + context + large files
# → ERROR: contradictory constraints
```

---

## Summary

| Component | Responsibil | Behavior |
|---|---|---|
| **Elaboration Agent** | Decide IF flags apply | Read OMS notes, set flags before queuing |
| **Router** | Surface flags | Log in briefing, no tier/roster change |
| **Executor** | Log flags | Include in Discord notifications, respect Model-hint |
| **Validator** | Guard against errors | Block contradictory combos, auto-derive Model-hint |

**Key principle:** Flags do NOT change task scope, complexity, or routing. They only inform Model-hint selection, which is already automatic. Flags are author's constraints that the system respects.
