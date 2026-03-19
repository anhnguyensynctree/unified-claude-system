# Scenario 049 — EM Silent Scope Absorption

**Source**: Brooks (1975) *The Mythical Man-Month* — "adding manpower to a late software project makes it later"; Weinberg (1971) *The Psychology of Computer Programming*; project post-mortems where EM absorbed scope silently
**Difficulty**: Intermediate
**Primary failure mode tested**: CTO adds scope in Round 2 without flagging delivery impact; EM does not update the delivery estimate explicitly; synthesis inherits the original timeline with the expanded scope
**Criteria tested**: D4, B1, B2, E3, C4

## Synthetic CEO Intent
> "Add user roles to the app — admin, member, and viewer — with appropriate permissions on each page."

## Setup
Round 1 establishes a baseline scope and estimate. CTO adds scope in Round 2 without explicitly flagging it as a timeline change. EM must detect the scope increase and update the delivery estimate explicitly — not absorb it silently.

**Round 1 baseline:**
- Backend Dev: "3 roles, RLS policies per role, role assignment on user profile — 4–5 days."
- CTO: "Recommend Supabase RLS with role column on users table. Standard pattern."
- EM Round 1: "Delivery estimate: 5–7 days including QA. Confidence: medium."

**Scope addition in Round 2 (CTO adds without flagging delivery impact):**
CTO Round 2: "We should also add an audit log — every permission check and role change should be logged for compliance. This is the right time to build it alongside roles."

Audit log is 2–3 additional days of Backend Dev work. It was not in the original scope.

**EM failure pattern:**
- EM Round 2: "Noted — we'll incorporate the audit log into the delivery plan." → silent absorption
- EM Round 2: "Timeline remains 5–7 days, we'll fit audit log in." → scope increase absorbed into original estimate (impossible)
- EM Round 2: "CTO's audit log addition is a good idea — delivery should still be feasible." → no updated estimate

**Correct EM behavior:**
EM Round 2 explicitly names the scope increase and updates the estimate:
"CTO added audit log in Round 2 — this is a scope increase not in the Round 1 estimate. Updated delivery estimate: 8–10 days (original 5–7 plus 2–3 days for audit log implementation and test coverage). Original estimate no longer applies. If audit log is required for this sprint, the timeline extends. If not, it should be scoped to a separate ticket."

## Expected Behavior

**EM Round 2 — correct:**
- Names the scope addition explicitly: "CTO added audit log — this was not in Round 1 scope"
- Updates estimate: original 5–7 days → 8–10 days with audit log
- Offers a decision: include now (8–10 days) or defer to separate ticket (5–7 days, original scope)
- Does not absorb silently or say "we'll fit it in"

## Failure Signals
- EM Round 2 position does not update the delivery estimate after CTO's scope addition → B1 fail (scope increase is a delivery blocker; must appear in position)
- EM Round 2 position absorbs audit log without naming it as a scope increase → B2 fail (conditional framing: "we'll incorporate" vs. "this extends the estimate by 2–3 days")
- EM Round 2 `position_delta.changed: false` when scope has increased — if EM doesn't update position when scope changes, this is a false hold → E3 fail
- Synthesis assigns both roles and audit log to the original 5–7 day estimate → C4 fail

## Pass Conditions
EM Round 2 explicitly names the scope increase and provides an updated delivery range. Synthesis either: (a) uses the updated estimate with both features, or (b) assigns audit log to a separate ticket with the original estimate maintained. Either way, the original estimate is not used for the expanded scope.

## Trainer Evaluation Focus
Silent scope absorption is the EM equivalent of bystander effect: EM sees the scope change, notes it in reasoning, but position says "we'll manage." The test is whether the scope increase appears in `position` as a named change with updated numbers — not in `reasoning[]` as an acknowledged but unquantified addition.

Watch for the "we'll incorporate" pattern — it is always scope absorption. The correct pattern is "CTO added [X] — updated estimate is [Y]."
