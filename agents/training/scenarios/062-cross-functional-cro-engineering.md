# Scenario 062 — Cross-Functional Feature: CRO + Engineering Discussion

**Difficulty**: Advanced
**Primary failure mode tested**: CRO is absent from cross-functional feature discussion that requires research framing; interface-contract is not agreed before parallel elaboration; single merged task produced instead of per-department tasks.
**Criteria tested**: FD1, FD2, FD3, RG2, SI1, RM2, D1

## Synthetic CEO Intent

> `/oms FEATURE-011` — feature draft:
>
> ```
> ## FEATURE-011 — Big Five Questionnaire Scoring Engine
> - Status: draft
> - Milestone: question-bank-os
> - Type: cross-functional
> - Departments: [chief-research-officer, backend-developer]
> - Research-gate: false
> - Why: Scoring must be research-validated, not ad-hoc; interface agreed upfront
> - Exec-decision: Scoring algorithm must follow published NEO-PI-R norming methodology — no custom weighting
> - Acceptance: Given user's 30 questionnaire answers, backend produces Big Five scores with subscale breakdown
> - Validation: cpo + cro
> - Context-hints: .claude/agents/research.ctx.md, src/scoring/
> ```

## Setup

Research-gate is false — interface CAN be agreed upfront. CRO knows the NEO-PI-R scoring methodology; Backend Dev needs the formula and output shape.

## Expected Behavior

**Router — correct:**
- Reads `Departments: [chief-research-officer, backend-developer]`
- Applies Cynefin: cross-domain research+engineering, partially reversible (scoring formula change = data migration risk), uncertainty moderate
- Tier 2 (2-3 agents, 2 rounds)
- Activates: chief-research-officer + backend-developer — departments already cover both domains
- Does NOT activate product-manager or frontend (not in scope for this feature)
- FD1 pass: Router assessment aligned with Departments[] hint; no addition needed

**Round 1 (blind NGT):**
- CRO: states NEO-PI-R scoring formula (item weights per factor, subscale → domain mapping), names the normative dataset to use, defines output schema at framework level
- Backend Dev: states implementation approach (input schema, data types, output structure, error cases)

**Interface-contract agreed in Round 2:**
```
Input: { responses: [{item_id: string, score: 1|2|3|4|5}] } (30 items)
Output: {
  scores: { O: float, C: float, E: float, A: float, N: float },
  subscales: { [subscale_code]: float },
  percentiles: { O: float, C: float, E: float, A: float, N: float }
}
Scoring: NEO-PI-R norming table from Costa & McCrae 1992 — r values per item per factor
```

**Elaboration — correct (research_gate: false = parallel):**

Two tasks with interface-contract in both Context fields:

TASK-011a (CRO/research):
```
## TASK-011a — Big Five Scoring Methodology Documentation
- Department: research
- Context: .claude/agents/research.ctx.md — Interface-contract: [verbatim from above]
```

TASK-011b (backend impl):
```
## TASK-011b — Big Five Scoring Engine Implementation
- Department: backend
- Context: src/scoring/ — Interface-contract: [verbatim from above]
- Depends: none (can run parallel — methodology documented alongside implementation)
```

## Failure Signals

- CRO not activated → RM2 fail (research task without CRO)
- Backend Dev proposes custom scoring weights in Round 1 without flagging exec_decision_conflict → FD2 fail (Exec-decision violated)
- Single merged task: `TASK-011 — Big Five Scoring Engine (Research + Implementation)` → FD3 fail
- TASK-011b missing interface-contract in Context → RG2 fail
- TASK-011b has `Depends: TASK-011a` with note "backend waits for research" — fails if research_gate is false and the interface is already agreed (unnecessary sequencing = RG2-adjacent fail)
- CRO takes a position on implementation details (language choice, ORM) → D1 fail
- Backend Dev takes a position on whether NEO-PI-R is the correct framework → D1 fail (domain breach — CRO owns methodology)

## Pass Conditions

- CRO and Backend Dev both active, each in their domain only
- Interface-contract contains input schema, output schema, and named scoring methodology source
- Two queued tasks, one per department, both with interface-contract in Context
- Neither task depends on the other (parallel)
- No backend-level implementation details in CRO's position
- No methodology decisions in Backend Dev's position

## Trainer Evaluation Focus

Two separate failure modes to test: (1) Did Router correctly activate CRO for a research-flavored feature? (2) Did elaboration correctly produce two parallel tasks with shared interface-contract? A merged task is FD3. A task with missing interface-contract is RG2. These are independent failures — both must be checked separately.
