# Pipeline Init

Set up the 6-layer test standard for a multi-stage pipeline or multi-step process component.

Ask these questions first:

1. What are the stage names, in order? (e.g. `validate → check-availability → reserve → notify`)
2. What language/runtime? (TypeScript or Python)
3. Is this a new standalone pipeline, or a component inside an existing project?

Then execute ALL steps below in order.

---

## Step 1 — Create test directory structure

Create the following folders relative to the pipeline root (or component root if inside a larger project):

```
tests/
  <stage-1>/        ← one folder per stage for unit tests
  <stage-2>/
  <stage-N>/
  contracts/        ← schema/dataclass boundary tests
  seams/            ← stage N output → stage N+1 real run()
  resilience/       ← empty input, partial failure, all-fail
  invariants/       ← score bounds, enum sets, output shapes
  integration/      ← real 2+ stage chains, I/O mocked at boundary only
  helpers.ts        ← (TypeScript) canonical object builders for every stage type
  helpers.py        ← (Python) canonical object builders for every stage type
```

Create only the helpers file matching the chosen language. Leave a stub with clear section headings:

**TypeScript (`tests/helpers.ts`)**:
```typescript
// Canonical object builders — all test layers import from here.
// Update this file FIRST whenever a stage boundary type changes.

// Stage: [stage-1]
export const make[Stage1Output] = (overrides = {}) => ({
  // TODO: add fields matching [Stage1Output] shape
  ...overrides,
});

// Add one builder per stage boundary type below.
```

**Python (`tests/helpers.py`)**:
```python
# Canonical object builders — all test layers import from here.
# Update this file FIRST whenever a stage boundary type changes.

def make_[stage1]_output(**overrides):
    """Builder for [Stage1] output. Add fields matching the dataclass."""
    base = {
        # TODO: add fields
    }
    return {**base, **overrides}

# Add one builder per stage boundary type below.
```

---

## Step 2 — Add pipeline standard to project rules

Create `.claude/rules/pipeline.md` in the project root (or nearest `.claude/` folder) with path-scoping so it only loads when working on pipeline files:

```markdown
---
paths:
  - "src/**/[pipeline-folder]/**"
  - "tests/contracts/**"
  - "tests/seams/**"
  - "tests/resilience/**"
  - "tests/invariants/**"
  - "tests/integration/**"
---

@~/.claude/standards/testing-pipeline.md
```

Replace `[pipeline-folder]` with the actual folder name containing the pipeline stages (e.g. `pipeline`, `stages`, `workflow`, `process`).

---

## Step 3 — Print handoff message

After all files are created, print exactly:

```
Pipeline init complete.

Stages: [stage-1] → [stage-2] → ... → [stage-N]

Test structure:
  tests/
    [stage-1]/        ← unit tests
    [stage-2]/        ← unit tests
    contracts/        ← schema boundary tests
    seams/            ← inter-stage wiring tests
    resilience/       ← empty/partial/all-fail cases
    invariants/       ← bounds, enums, shapes
    integration/      ← full chain, I/O mocked at boundary
    helpers.[ext]     ← shared builders — update this first on type changes

Standard loaded:
  .claude/rules/pipeline.md → @~/.claude/standards/testing-pipeline.md
  (path-scoped: only loads when working on pipeline or test files)

Write tests in this order for each stage:
  1. Unit — internals and branches
  2. Contract — input/output schema
  3. Seam — wiring to next stage
  4. Resilience — run([]), run([a, FAIL, b]), run([FAIL, FAIL, FAIL])
  5. Invariant — score bounds, enum validity, output shape
  6. Integration — last, after all stages have unit + seam coverage
```
