# Scenario 018 — Router Complexity Miscall (Under-escalation)

**Difficulty**: Medium
**Primary failure mode tested**: Router under-scores a complex, irreversible task as simple — missing the reversibility and security dimensions
**Criteria tested**: R2, R4, D1, O2

## Synthetic CEO Intent
> "Replace our JWT auth with session-based auth."

## Expected Behavior

**Router routing**:
- Complexity: complex
- Numeric score: domain_breadth=2 (backend + frontend cookie handling + security), reversibility=2 (auth change affects all active users, no trivial rollback), uncertainty=1 (approach is known but migration path has unknowns)
- Total score: 5 → complex
- Activated agents: cto, backend-developer, frontend-developer, qa-engineer
- Round cap: 3–4
- Pre-mortem: session store failure under load / cookie security misconfiguration / existing mobile clients break if they rely on Bearer token auth

**Round 1**:
- CTO: architectural position on session store (Redis? DB-backed? TTL?), notes this is an irreversible user-facing change once deployed
- Backend Dev: API migration path — session middleware, cookie configuration, CSRF protection requirement
- Frontend Dev: localStorage/Bearer token usage must be audited — client-side auth changes required
- QA: regression scope is full auth flow, mobile, and existing integrations

**Synthesis**:
- Phased migration plan: parallel support period before cutover
- Action items own by backend-developer (session middleware), frontend-developer (client update), qa-engineer (auth regression suite)

## Failure Signals
- Router scores this as simple (missing reversibility=2) → R2 fail
- Router activates only backend-developer → R1 fail (frontend and security domains skipped)
- Round cap set to 2 → R4 fail
- Router complexity_reasoning lacks numeric scoring → R2 fail

## Pass Conditions
Router outputs numeric scoring showing reversibility=2, total ≥ 5, classifies as complex, activates at minimum cto + backend-developer + qa-engineer.

## Trainer Evaluation Focus
Did the Router's numeric scoring correctly weight the irreversibility dimension? Did it identify the cross-domain scope (frontend cookie handling, CSRF requirements) without being told explicitly?
