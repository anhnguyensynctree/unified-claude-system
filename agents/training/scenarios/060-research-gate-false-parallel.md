# Scenario 060 — Research Gate: False Parallel Path

**Difficulty**: Medium
**Primary failure mode tested**: Interface-contract agreed in feature discussion is not written into task Context fields; departments treated as sequential when they can run in parallel.
**Criteria tested**: RG2, FD3, SI1, SI2

## Synthetic CEO Intent

> `/oms FEATURE-004` — feature draft:
>
> ```
> ## FEATURE-004 — User Profile API + Profile Page
> - Status: draft
> - Milestone: chat-ui-rag
> - Type: cross-functional
> - Departments: [backend-developer, frontend-developer]
> - Research-gate: false
> - Why: Users need profile management; interface known upfront
> - Exec-decision: Profile API must be REST; no GraphQL for MVP
> - Acceptance: Users can view and edit display name, avatar, and timezone
> - Validation: cpo + cto
> ```

## Setup

Feature discussion runs. Backend Dev and Frontend Dev agree in the discussion:

**Interface-contract agreed:**
```
GET /api/profile → { id, display_name, avatar_url, timezone }
PATCH /api/profile → { display_name?, avatar_url?, timezone? } → 200 | 400 | 401
Authorization: Bearer <JWT>
```

## Expected Behavior

**Elaboration Agent — correct behavior:**

Both tasks elaborated fully (research_gate: false → parallel):

Backend task:
```
## TASK-004a — Profile API Implementation
- Status: queued
- Feature: FEATURE-004
- Department: backend
- Interface-contract: GET /api/profile → {id, display_name, avatar_url, timezone} | PATCH /api/profile → {display_name?, avatar_url?, timezone?} → 200|400|401 | Auth: Bearer JWT
- Context: src/routes/profile.ts, src/middleware/auth.ts — Interface-contract: [verbatim from above]
- Depends: none
```

Frontend task:
```
## TASK-004b — Profile Page UI
- Status: queued
- Feature: FEATURE-004
- Department: frontend
- Interface-contract: GET /api/profile → {id, display_name, avatar_url, timezone} | PATCH /api/profile → {display_name?, avatar_url?, timezone?} → 200|400|401 | Auth: Bearer JWT
- Context: src/components/ProfilePage.tsx, src/hooks/useProfile.ts — Interface-contract: [verbatim from above]
- Depends: none
```

Both tasks have `Depends: none` — they CAN run in parallel because the interface-contract is agreed.

## Failure Signals

- TASK-004b has `Depends: TASK-004a` — FD3 adjacent fail (treating parallel as sequential without justification); RG2 fail (interface-contract is agreed, parallel is correct)
- TASK-004b Context is missing the interface-contract → RG2 fail (contract not propagated)
- TASK-004a Context is missing the interface-contract → RG2 fail (backend also must have it)
- Frontend task says "consult backend team for API shape" → SI2 fail (interpretation left to implementer)
- Only one task produced for both departments (merged task) → FD3 fail
- Interface-contract appears in `Interface-contract:` field of task but NOT in `Context:` field → RG2 partial fail — Context is what the executor pre-loads; it must be there

## Pass Conditions

- Two separate queued tasks: one per department
- Both tasks have `Depends: none`
- Both tasks have the agreed interface-contract written verbatim in their `Context:` field
- Backend task's `Produces:` declares the API endpoints downstream task depends on
- Frontend task's `Context:` includes the `Produces:` value from the backend task (cross-reference)

## Note on Depends direction

If backend must be running first (e.g., frontend integration tests need a real API), it's acceptable to add `Depends: TASK-004a` to TASK-004b — but only if the Spec requires hitting a real backend. The Trainer must distinguish: (1) sequential because output→input → valid Depends, (2) sequential out of habit → RG2 fail, since interface is agreed and parallel is the default.

## Trainer Evaluation Focus

Two things to verify independently: (1) Was a separate task produced per department? (2) Does each task's Context field include the agreed interface-contract verbatim? A task that has the interface-contract in `Interface-contract:` but not in `Context:` is a partial pass — the executor won't pre-load it from `Interface-contract:`, only from `Context:`. RG2 requires Context, not just presence of the field.
