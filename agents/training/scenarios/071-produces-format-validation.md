# Scenario 071 — Produces Field: Prose vs File Path (Tier 0)

**Difficulty**: Easy
**Primary failure mode tested**: Elaboration Agent writes a prose description in the Produces field instead of a resolvable file path, and the queue validator catches it.
**Criteria tested**: PV1 (Produces format), QG1 (queue gate enforcement)

## Synthetic CEO Intent

> `/oms all` on a FEATURE with two tasks: a research task that produces findings, and an impl task that depends on those findings.

## Input Action Items

```
action_item_1:
  action: "Research optimal caching strategy for API responses"
  type: research
  depends_on: []
  chain_type: null

action_item_2:
  action: "Implement API response caching based on research findings"
  type: impl
  depends_on: [action_item_1]
  chain_type: value_substitution
```

## Correct Elaboration

Research task:
```
Produces: logs/research/TASK-001.md — sections: findings, cache-strategy recommendation, TTL values
```

Impl task:
```
Context: logs/research/TASK-001.md — sections: findings, cache-strategy recommendation, TTL values
Depends: TASK-001
```

Produces is a **file path** with structure annotation. Context copies it verbatim. Downstream executor can load the file.

## Failure Pattern — Prose Produces

Research task:
```
Produces: optimized caching strategy with TTL recommendations
```

This is prose — not a file path. It has no `/` or `.` character. The downstream impl task's Context would say `Context: optimized caching strategy with TTL recommendations` — which the executor cannot load as a file.

## Expected Behavior

**Queue validator (validate-queue.py) BLOCKS the write**:
- Produces format check: each pipe-separated segment must contain `/` or `.` (file path indicators)
- `"optimized caching strategy with TTL recommendations"` has neither
- Error: `TASK-001: Produces 'optimized caching strategy...' is not a file path — must be a resolvable path or 'none'`

**Elaboration Agent should have written a file path in the first place** — persona.md says:
- "What the next task in the dependency chain needs. Be specific — this becomes the downstream task's Context: field verbatim."
- Example: `logs/research/TASK-NNN.md — highest-confidence hypothesis with trigger condition`

## Failure Signals

| Signal | What went wrong |
|---|---|
| Queue write succeeds with prose Produces | QG1 fail — validator didn't check Produces format |
| Elaboration wrote prose despite persona guidance | PV1 fail — elaboration didn't follow field rules |
| Downstream Context is prose (not loadable) | PV1 fail — Produces→Context wiring broken |
| `none` used but downstream task exists with Depends | PV1 fail — Produces should reference output file |

## Validation Criteria

- **PV1**: Produces field must be a file path (contains `/` or `.`) or `none`. Prose descriptions are blocked by queue validator.
- **QG1**: Queue validator catches the violation at write time. Task never reaches `Status: queued` with prose Produces.

## Edge Cases

1. **Produces: `none` when downstream exists** — validator should warn (not block) that a task with Depends pointing to this task exists but Produces is `none`. The downstream task has no interface to consume.
2. **Produces with annotations** — `src/cache/config.ts — exports: CacheStrategy, DEFAULT_TTL` is valid (path + exports). The path portion contains `/` and `.`.
3. **Multiple Produces segments** — `src/cache/config.ts | src/cache/middleware.ts` — each segment checked independently.
