# OMS Task Schema Update — Dynamic Model Routing (2026-04-04)

## Summary of Changes

Updated OMS task schema to support dynamic routing across all available free OpenRouter models, removing Eastern/Western domain silos and enabling efficient task distribution by characteristics.

---

## Before → After

### Model-hint Options

**Before:**
```
qwen | haiku | sonnet
- qwen: code generation only (impl ≤3 files)
- haiku: fallback/judge
- sonnet: large impl (4+ files), gate, infra-critical
```

**After:**
```
qwen-coder | qwen | llama | gpt-oss | nemotron | gemma | stepfun | sonnet
- qwen-coder: code generation (impl ≤3 files, primary)
- qwen: research/analysis (best reasoning, 1M context)
- gpt-oss: research/analysis (120B params, general)
- nemotron: research/analysis (262K context, large)
- llama: general purpose (proven, fallback)
- gemma: speed-critical (fastest, ~70s)
- stepfun: medium complexity (fallback)
- sonnet: quality gates only (subscription, gate + infra-critical)
```

---

## Model-Hint Derivation Rules (New)

### Code Generation & Implementation

| Condition | Model-hint | Route | Cost | Use Case |
|---|---|---|---|---|
| File-count ≤ 3 + Type: impl + Verify | `qwen-coder` | LiteLLM → qwen3-coder:free | Free | Primary for code |
| File-count ≤ 3 + Type: impl + speed-critical | `gemma` | LiteLLM → gemma-3-27b:free | Free | Fastest option |

### Analysis & Reasoning

| Condition | Model-hint | Route | Cost | Use Case |
|---|---|---|---|---|
| Type: research + file-count ≤ 3 | `qwen` | LiteLLM → qwen3.6-plus:free | Free | Best reasoning (1M ctx) |
| Type: research + file-count 4-5 | `gpt-oss` | LiteLLM → gpt-oss-120b:free | Free | Large model (120B) |
| Type: research + large-context flag | `nemotron` | LiteLLM → nemotron-3-super:free | Free | Max context (262K) |
| Type: research + speed-critical flag | `gemma` | LiteLLM → gemma-3-27b:free | Free | Fast reasoning |

### Subscription Routes (Quality Gates)

| Condition | Model-hint | Route | Cost | Use Case |
|---|---|---|---|---|
| Type: gate | `sonnet` | claude -p --model sonnet | Subscription | Milestone validation |
| Infra-critical: true | `sonnet` | claude -p --model sonnet | Subscription | Critical reliability |

---

## Fallback Chains (Automatic Escalation)

If a model times out or errors, oms-work automatically tries the next option:

**Code tasks:**
```
qwen-coder → llama → gemma → [timeout]
```

**Research tasks:**
```
qwen → gpt-oss → nemotron → llama → gemma → [timeout]
```

**Speed-critical:**
```
gemma → stepfun → llama → [timeout]
```

**Large context (>100K tokens):**
```
nemotron (262K) → qwen (1M) → gpt-oss (131K) → [timeout]
```

---

## Breaking Changes

### Removed from OMS
- `haiku` — No longer used in OMS tasks (stays available on Anthropic subscription)
- `qwen36` reference → Now just `qwen` (maps to qwen3.6-plus:free internally)
- 30s/60s timeouts → All OpenRouter models now 120-180s (fair-use queueing)

### New Requirements for Tasks

When elaborating `Type: research` tasks, agents may now specify additional flags:
- `speed-critical: true` → Forces `Model-hint: gemma` (fastest)
- `large-context: true` → Forces `Model-hint: nemotron` (262K context, largest)

Without flags, research tasks auto-hint to `qwen` (best reasoning).

---

## Performance Expectations

| Model | Latency | Quality | Cost | When to use |
|---|---|---|---|---|
| qwen-coder | ~100s | ⭐⭐⭐⭐⭐ | Free | Code, default |
| qwen | ~130s | ⭐⭐⭐⭐⭐ | Free | Research, best reasoning |
| gpt-oss | ~130s | ⭐⭐⭐⭐⭐ | Free | Research, large model |
| nemotron | ~120s | ⭐⭐⭐⭐⭐ | Free | Research, large context |
| llama | ~120s | ⭐⭐⭐⭐ | Free | General purpose |
| gemma | ~70s | ⭐⭐⭐ | Free | Speed-critical |
| stepfun | ~90s | ⭐⭐⭐ | Free | Medium complexity |
| sonnet | ~20-30s | ⭐⭐⭐⭐⭐ | Subscription | Quality gates only |

---

## Task Schema File Changes

**File:** `~/.claude/agents/oms-work/task-schema.md`

### Sections Updated

1. **Task Queued Format** (line 92-94)
   - Changed Model-hint options
   - Changed Script-model options
   - Changed Script-timeout values (→ 120-180s)

2. **Gate Task Format** (line 128)
   - Clarified: gate always uses sonnet (subscription)

3. **Model-Hint Derivation** (line 183-199)
   - Completely rewritten for 7 free models + sonnet
   - Added speed-critical and large-context flags
   - Removed file-count 4+ rule (now must split)

4. **Model Routing Rules** (line 244-277)
   - New comparison table with all 7 free models
   - New fallback chains for code, research, speed-critical, and large-context
   - Clarified quality gates (subscription only)

5. **Field Definitions** (line 164)
   - Updated Script-timeout explanation

6. **Gate Rules** (line 125-131)
   - Clarified sonnet is subscription, not OpenRouter

---

## Migration Path

### For Existing Tasks in Queue

Tasks with old Model-hint values (`qwen`, `haiku`, `sonnet`):
- `qwen` → Keep as-is (auto-maps to qwen-coder for impl, qwen for research)
- `haiku` → Re-spec; move to Anthropic subscription if needed
- `sonnet` → Keep as-is (gate and infra-critical unaffected)

### For New Feature Elaboration

OMS elaboration agents will auto-derive Model-hint based on:
1. Task type (impl vs research)
2. File count (≤3 vs 4-5)
3. Optional flags: speed-critical, large-context

No manual Model-hint assignment needed — it's auto-derived.

---

## Cost Impact

### OpenRouter Free Tier (No Change)
- All 7 models cost $0
- Fair-use queueing (120-180s latency expected)
- Fallback chains prevent timeouts when possible

### Subscription (Sonnet Only)
- Gate tasks: small number, fast execution (~20-30s)
- Infra-critical tasks: rare, only when quality is paramount
- CRO validation retry: only if initial free-tier research fails validation

**Expected:** Same or lower cost than before (more free tier usage, fewer sonnet fallbacks).

---

## Examples

### Code Implementation Task

**Elaboration:**
```
Type: impl
File-count: 2
Verify: pnpm test

→ Auto-derived: Model-hint: qwen-coder
→ Route: LiteLLM → qwen3-coder:free
→ Timeout: 120s
→ Fallback: llama → gemma
```

### Research Task (Fast)

**Elaboration:**
```
Type: research
File-count: 2
speed-critical: true

→ Auto-derived: Model-hint: gemma
→ Route: LiteLLM → gemma-3-27b:free
→ Timeout: 120s
→ Fallback: stepfun → llama
```

### Research Task (Deep Analysis)

**Elaboration:**
```
Type: research
File-count: 3
large-context: true

→ Auto-derived: Model-hint: nemotron
→ Route: LiteLLM → nemotron-3-super:free (262K context)
→ Timeout: 150s
→ Fallback: qwen → gpt-oss
```

### Milestone Gate

**Auto-appended:**
```
Type: gate
Milestone: reading-quality-ux

→ Fixed: Model-hint: sonnet
→ Route: claude -p --model sonnet
→ Timeout: 30-60s (subscription)
→ No fallback (gate is critical path)
```

---

## References

- **llm-route.llms.txt** — User guide for all 28+ OpenRouter models
- **llm-router.yaml** — LiteLLM config with 7 preferred models + fallback chains
- **sync-openrouter-models.py** — Auto-discovery script (run monthly to stay current)
