# Scenario 029 — Tier 1 Under-Escalation / QA Domain Omission

**Source**: Myers (2004) *The Art of Software Testing* — error visibility asymmetry between authors and testers; Sommerville (2011) *Software Engineering* Ch. 23 — test fixture maintenance as a distinct engineering concern
**Difficulty**: Basic-Intermediate
**Primary failure mode tested**: Router collapses a 2-domain task (Frontend + QA) to 1-domain by treating QA test fixture updates as implementation noise rather than a separate domain requiring dedicated analysis
**Criteria tested**: R2, R6, R7

## Synthetic CEO Intent
> "Add email validation error messages to the signup form — users need to know specifically what's wrong when their email fails validation."

## Setup
The signup form currently does no inline validation — it submits and returns a server error. The task requires:
1. Frontend Dev to implement inline validation error states (invalid format, duplicate email, empty field) with accessible error messages tied to form fields
2. QA to update test fixtures and E2E tests that currently assert on the form's happy-path submission — the new error states introduce new selectors, new copy strings, and new test branches that don't exist in the test suite

QA's test fixtures are not implementation details — they are a separate artifact that requires dedicated analysis: which existing tests will break on the new error selectors, which new branches need coverage, and whether the copy strings should be fixture-driven (for i18n resilience) or inline.

## Expected Behavior — Correct

**Router routing**:
```json
{
  "tier": 1,
  "complexity": "simple",
  "complexity_reasoning": "Complicated-low. Two domains: Frontend (validation logic, error rendering, accessibility) and QA (test fixture updates, new error state coverage). domain_breadth=1, reversibility=0, uncertainty=1, total=2 → Tier 1. Needs analysis — QA test impact is non-trivial.",
  "activated_agents": ["frontend-developer", "qa-engineer"],
  "round_cap": 1,
  "stage_gate": null,
  "locked": true
}
```

Frontend Dev: scopes validation logic (format regex, duplicate-check API call, empty-field guard), error message copy, ARIA association between error and field, and which component file to modify.

QA: independently enumerates which existing E2E tests will fail due to new error selectors, which new branches need coverage (each error state), and whether error copy should be parameterized in fixtures.

## Failure Pattern
Router classifies as Tier 0, activates Frontend Dev only:

```json
{
  "tier": 0,
  "complexity": "trivial",
  "complexity_reasoning": "Obvious domain. Single frontend change — add error messages to form validation. Known pattern, fully reversible.",
  "activated_agents": ["frontend-developer"],
  "round_cap": 1,
  "locked": true
}
```

No numeric score. QA domain not mentioned. Test fixture maintenance treated as implicit follow-on work rather than parallel scope. Result: Frontend Dev implements validation; existing E2E tests break on deploy; QA discovers the test gap in CI rather than during design.

## Failure Signals
- Router `complexity_reasoning` contains no numeric score (`domain_breadth + reversibility + uncertainty`) → R6 fail
- Router `activated_agents` contains only `frontend-developer` with no `qa-engineer` → R7 fail (Tier 1 allows 1-2 agents; QA domain is required here)
- Router `tier` is 0 and `complexity` is "trivial" despite the task requiring analysis of test fixture impact → R2 fail
- `complexity_reasoning` does not mention test fixtures, QA domain, or error state test coverage → R2 fail (domain_breadth undercounted)

## Pass Conditions
Router outputs `tier: 1`, `complexity: "simple"`, numeric score present with `domain_breadth=1`, `uncertainty=1`, `total=2`. Both `frontend-developer` and `qa-engineer` in `activated_agents`. `complexity_reasoning` explicitly names the QA test fixture update as the reason for the second domain.

## Trainer Evaluation Focus
The key discrimination: does the Router treat test fixture updates as a first-class domain requiring a dedicated agent, or as implementation noise the frontend developer will "handle"? QA's value here is not running tests after the fact — it is analyzing test impact during planning. If the Router cannot distinguish "implementation change" from "implementation change + test surface change," it will systematically under-escalate any task that touches existing test coverage.

Check `complexity_reasoning` specifically: the numeric score must be present and the QA domain must be named explicitly. A Router that produces correct `activated_agents` but incorrect numeric reasoning has partially failed R6 — it reached the right answer without the right process.
