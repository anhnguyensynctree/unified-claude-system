# Scenario 059 — Research Gate: True Path

**Difficulty**: Medium
**Primary failure mode tested**: Elaboration Agent writes full OpenSpec for engineering tasks when research_gate is true; engineering tasks are elaborated before research findings are available.
**Criteria tested**: RG1, TS1, TS2

## Synthetic CEO Intent

> `/oms FEATURE-007` — feature draft:
>
> ```
> ## FEATURE-007 — Confidence Weighting for Synthesis Algorithm
> - Status: draft
> - Milestone: synthesis-algorithm
> - Type: cross-functional
> - Departments: [chief-research-officer, backend-developer]
> - Research-gate: true
> - Why: Must know which systems correlate before coding weights
> - Exec-decision: Independence weights are empirically derived — no hardcoded constants
> - Acceptance: Synthesis output weights reflect statistical independence between systems
> - Validation: cpo + cro + cto
> ```

## Expected Behavior

**Feature discussion result:**
- CRO + Backend Dev agree on interface: research output = `logs/research/TASK-NNN.md` with `independence_scores` field mapping system pairs to correlation coefficients
- interface-contract agreed: `{system_a: string, system_b: string, correlation: float}[]`

**Elaboration Agent — correct behavior:**

Research task (elaborated fully):
```
## TASK-007a — Independence Score Research
- Status: queued
- Feature: FEATURE-007
- Milestone: synthesis-algorithm
- Department: research
- Type: research
- Spec: The system SHALL produce independence correlation scores for all paired personality systems so that synthesis weights can be derived empirically.
- Scenarios: GIVEN research output WHEN reviewed THEN ≥3 system pairs have correlation coefficients with 95% CI bounds | GIVEN a system pair was excluded WHEN document read THEN exclusion reason documented
- Artifacts: logs/research/TASK-007a.md — sections: independence_scores[], methodology, excluded_pairs
- Produces: logs/research/TASK-007a.md — independence_scores: [{system_a, system_b, correlation}]
- Verify: test -f logs/research/TASK-007a.md
- Validation: researcher → cro → cpo
- Depends: none
```

Engineering task (HELD — not elaborated):
```
## TASK-007b — Synthesis Weight Calibration
- Status: draft
- Feature: FEATURE-007
- Milestone: synthesis-algorithm
- Department: backend
- Type: impl
- Depends: TASK-007a
- NOTE: Blocked: awaiting research findings from TASK-007a. Elaborate after CRO signs off on research.
```

RG1 pass: engineering task written as draft with blocked note, not elaborated into full OpenSpec.

## Failure Signals

- TASK-007b elaborated with full `Spec:`, `Scenarios:`, `Artifacts:` → RG1 fail (engineering task elaborated despite research_gate: true)
- TASK-007b has `Spec: The system SHALL weight systems based on independence scores` — this forward-references unknown research output → also fails Queue Gate Check 2 (Spec contains forward reference to unknown research output)
- Research task TASK-007a NOT elaborated — only the engineering task is → wrong direction; research elaborates first
- TASK-007b has `Status: queued` instead of `Status: draft` → RG1 fail (cannot be queued until research done + CRO sign-off)
- TASK-007b is missing the `Blocked:` note → engineers won't know why it's sitting as draft

## Pass Conditions

- TASK-007a has full OpenSpec, `Status: queued`
- TASK-007b has `Status: draft` with `NOTE: Blocked: awaiting research findings from TASK-007a`
- TASK-007b has NO Spec, Scenarios, Artifacts, or Verify fields
- TASK-007b has `Depends: TASK-007a`
- Elaboration Agent's routing note references `research_gate: true` as the reason for holding engineering

## Trainer Evaluation Focus

The key trap is that a "helpful" Elaboration Agent might write TASK-007b with a tentative Spec like "SHALL weight systems based on whatever research finds" — this fails both RG1 AND the Queue Gate's forward-reference check. The correct behavior is to write zero OpenSpec for engineering tasks when research_gate is true. Nothing tentative. Nothing that forward-references research output. Just: draft, blocked, depends.
