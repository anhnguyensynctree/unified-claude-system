# Scenario 061 — Task Sizing Split Enforcement

**Difficulty**: Medium
**Primary failure mode tested**: Elaboration Agent produces an oversized task instead of splitting; split tasks lack correct Depends wiring.
**Criteria tested**: TS1, TS2

## Synthetic CEO Intent

> `/oms FEATURE-009` — feature action_item from synthesis:
> ```
> action: "Research optimal geocoding provider and implement HD lookup for Human Design birth data"
> type: impl
> infra_critical: true
> depends_on: []
> chain_type: null
> ```

This action_item violates the sizing rules in two ways:
1. Research + impl mixed in one task
2. Spec would require two sentences (research question + implementation detail)

## Expected Behavior

**Elaboration Agent reasoning (pre-flight):**
- Sizing check: "research optimal geocoding provider" = research task; "implement HD lookup" = impl task — mixed research+impl = split required (TS1 rule: no research+impl mix)
- Split into: TASK-009a (research) → TASK-009b (impl with Depends: TASK-009a)
- chain_type derived from context: research could change the provider choice → `direction_selection` → impl held as draft

Wait — chain_type is null on the input action_item. Elaboration agent must re-classify:
- Research could select or rule out providers → impl cannot be Spec'd without knowing the provider
- chain_type should be `direction_selection` — impl is held, research elaborated only

**Correct output:**

TASK-009a (elaborated):
```
## TASK-009a — Geocoding Provider Research
- Status: queued
- Type: research
- Spec: The system SHALL evaluate geocoding providers for Human Design birth location lookup so that an implementation-ready selection with API cost, coverage, and accuracy data can be delivered.
- Scenarios: GIVEN research output WHEN reviewed THEN ≥3 providers evaluated with: API cost per request, global city coverage %, accuracy validation methodology | GIVEN a provider was excluded WHEN document read THEN exclusion reason documented
- Artifacts: logs/research/TASK-009a.md — sections: candidates, evaluation_matrix, recommendation, excluded_options
- Produces: logs/research/TASK-009a.md — recommended provider with API endpoint, auth method, cost per request
- Verify: test -f logs/research/TASK-009a.md
- Validation: researcher → cro → cpo
- Depends: none
```

TASK-009b (HELD — direction_selection):
```
## TASK-009b — Human Design Geocoding Implementation
- Status: draft
- Type: impl
- Infra-critical: true
- NOTE: HOLD: implement HD geocoding — queued after CEO reviews research findings from TASK-009a
- Depends: TASK-009a
```

## Failure Signals — oversized task (TS1 fail)

```
## TASK-009 — HD Geocoding Research and Implementation
- Status: queued
- Type: impl
- Spec: The system SHALL research and implement geocoding for Human Design birth location lookup so that users can enter a city name and receive precise coordinates.
- Artifacts: logs/research/geocoding-research.md | src/utils/geocoding.ts — exports: lookupCoordinates | src/components/LocationInput.tsx — modified: uses lookupCoordinates | src/api/synthesis.ts — modified: passes coordinates to HD calculator
```

This fails TS1: research+impl mixed, Spec has two verbs ("research and implement"), 4 files listed (at the boundary), one session scope questionable.

## Failure Signals — split with broken Depends (TS2 fail)

```
## TASK-009b — HD Geocoding Implementation
- Status: queued
- Depends: none
```

TS2 fail: impl task has no Depends pointing to the research task. Queue could run them in parallel — impl would start without knowing which provider to use.

## Pass Conditions

- Two tasks produced: TASK-009a (research, queued) and TASK-009b (impl, draft/held)
- TASK-009a Spec has one verb: "evaluate geocoding providers"
- TASK-009b has `Depends: TASK-009a`
- TASK-009b has `Status: draft` with HOLD note (direction_selection chain)
- TASK-009a `Produces:` declares the specific output TASK-009b needs

## Trainer Evaluation Focus

The trap is an Elaboration Agent that writes a valid-looking single task by using research findings AS the artifacts (e.g., "Artifacts: logs/research/geocoding.md | src/utils/geocoding.ts"). This looks split but isn't — it mixes research output and code output in one task. Trainer must check: if `Artifacts:` contains both a log path AND source code paths, it's a mixed task → TS1 fail.
