# Pipeline Test Rules — Multi-Stage Architecture

Applies to any project where data flows through a sequence of stages
(trend → match → generate → render, ingest → transform → serve, etc.).

## The Problem with Unit Tests Alone

Unit tests verify component internals but cannot catch:
- Wiring bugs (wrong argument order between stages)
- Shape drift (a field added to stage N not consumed by stage N+1)
- Cascade failures (stage N returns empty, stage N+1 crashes instead of returning [])
- Invariant drift (scores drift outside [0,1] across the full computation)

## Test Layers — All Required

| Layer | Location | Responsibility |
|---|---|---|
| Unit | `tests/<stage>/` | Component internals, all branches, error paths |
| Contract | `tests/contracts/` | Dataclass/schema field names, types, list validators |
| Seam | `tests/seams/` | Stage N output → stage N+1 real `run()` call, no full mocks |
| Resilience | `tests/resilience/` | Empty inputs, external service failures, partial batch failures |
| Invariant | `tests/invariants/` | Score bounds, closed enum/taxonomy sets, output shapes |
| Integration | `tests/integration/` | Real multi-stage chains, external I/O mocked at true boundary only |

## Change → Required Test Updates

| What changed | Layers to update |
|---|---|
| New field on a stage boundary type | contracts → invariants (shape) → seams (if load-bearing) |
| Field removed or renamed | contracts + seams + invariants |
| Stage `run()` signature changed | seams + integration |
| New internal function | unit suite for that stage |
| New failure/error path | resilience |
| New enum / category value | invariants (taxonomy/closed-set test) |
| New score / float field | invariants (bounds test) |
| New stage added | all 6 layers |

## Shared Fixtures Rule

Maintain a single `tests/helpers.py` (or equivalent) with canonical object builders for every stage boundary type.
**Always update helpers first** when a type changes — all layers import from it.

## Run Order After Any Stage Edit

```bash
pytest tests/<stage>/        # unit — fastest signal
pytest tests/contracts/      # if boundary type changed
pytest tests/seams/          # if input/output shape changed
pytest tests/resilience/     # if failure path changed
pytest tests/invariants/     # if score/enum/shape changed
pytest tests/integration/    # if stage wiring changed
```

## Enforcement Hooks

Wire two PostToolUse hooks to fire on every source file edit:

1. **Gap detector** — reads `git diff` on the changed file, classifies change type
   (dataclass field, signature, failure path, score field, enum string),
   outputs the exact layers that need new or updated tests.

2. **Test runner** — immediately runs the matching unit suite so regressions
   surface within seconds of the edit.

Gap detector classification patterns:
- `@dataclass` field lines (added/removed) → contracts + invariants + seams
- `async def run(` changed → seams + integration
- `raise|except|log.warning|continue` in new lines → resilience
- Enum/category string literals in new lines → invariants
- `: float =` or `score` field in new lines → invariants

## Integration Test Standard

The integration smoke test must:
- Call real `run()` functions across 2+ stages in sequence
- Mock only at the true external I/O boundary (network, DB, LLM API, filesystem writes)
- Assert data lineage is preserved: output[i].input_ref is input[i]
- Include a zero-input case: empty list cascades cleanly to empty output at every stage

## Resilience Standard

Every stage `run()` must satisfy:
- `run([])` → `[]` (never raises on empty input)
- `run([a, FAIL, b])` → `[result_a, result_b]` (failure on item N does not abort N+1)
- `run([FAIL, FAIL, FAIL])` → `[]` (all-fail is not an error state)

Write explicit tests for each of these three cases per stage.

## Invariant Standards

Score fields: always `[0.0, 1.0]` — test with 0, 1, -1, 2 as inputs to verify clipping.
Enum/category fields: define `VALID_VALUES` as a module-level set in the invariant test file.
  Any code that produces a category string must be tested against `VALID_VALUES`.
Output shapes: every field that downstream consumers read without null-checking must have
  an invariant test asserting it is non-null, non-empty, and the correct type.
