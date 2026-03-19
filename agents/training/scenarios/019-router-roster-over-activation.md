# Scenario 019 — Router Roster Over-Activation

**Difficulty**: Basic
**Primary failure mode tested**: Router activates all agents as a hedge rather than reasoning about smallest sufficient roster
**Criteria tested**: R1, R2, R5, D1

## Synthetic CEO Intent
> "Add cursor-based pagination to the GET /users API endpoint."

## Expected Behavior

**Router routing**:
- Complexity: simple
- Numeric score: domain_breadth=0 (single backend domain), reversibility=0 (reversible — additive change), uncertainty=0 (standard pattern)
- Total score: 0 → simple
- Activated agents: backend-developer, qa-engineer
- Reasoning per excluded agent must be explicit:
  - cto: not activated — standard API pattern, no architectural decision
  - product-manager: not activated — no product scope question
  - engineering-manager: not activated — no timeline constraint stated
  - frontend-developer: not activated — backend endpoint change with stable contract
- Round cap: 2

**Round 1**:
- Backend Dev: cursor encoding approach (opaque cursor vs explicit ID+timestamp), page_size limits, null cursor behavior
- QA: test cases — first page, mid-page, last page, empty dataset, invalid cursor

**Round 2**:
- Should converge quickly — both agents on standard ground

**Synthesis**:
- One-sentence decision on cursor implementation
- Action item: backend-developer
- Optional: qa-engineer for test coverage

## Failure Signals
- Router activates cto → R1 fail (domain contribution cannot be stated for this task)
- Router activates product-manager → R1 fail
- Router activates engineering-manager → R1 fail (no timeline constraint)
- Router activates frontend-developer → R1 fail (API contract is additive, no breaking change)
- `agent_briefings` for backend-developer reads as a generic "you are the backend developer" statement → R5 fail
- Complexity classified as complex → R2 fail

## Pass Conditions
Router activates exactly backend-developer + qa-engineer (or backend-developer alone if Router explicitly reasons QA is optional for a standard additive endpoint). Every excluded agent has an explicit non-activation reason.

## Trainer Evaluation Focus
Did the Router resist the hedge of activating everyone? Did it explicitly reason about what each potentially-activated agent would contribute — and conclude there was nothing?
