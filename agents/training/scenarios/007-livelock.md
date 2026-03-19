# Scenario 007 — Livelock / Oscillating Deadlock

**Source**: Dijkstra (1971) concurrency theory; documented in MARL as "cyclic policies" (Matignon et al., 2012); observed in AutoGen conflicting-objective experiments
**Difficulty**: Hard
**Primary failure mode tested**: Agents loop with active outputs but zero progress toward decision
**Criteria tested**: L1, L2 (new), C1, X1, R4

## Synthetic CEO Intent
> "We need to add real-time collaboration features — multiple users editing the same document simultaneously."

## Setup
This requires a genuine architectural constraint conflict. Backend Dev's non-negotiable: no real-time sync without a conflict resolution strategy defined first. Frontend Dev's non-negotiable: no UI implementation without a stable API contract. These are both legitimate — but each is waiting on the other to move first.

Each round, Backend Dev proposes a conflict resolution approach, Frontend Dev identifies an API contract issue with it, Backend Dev modifies the proposal, the modification introduces a new contract issue, repeat.

## Expected Behavior

**Router routing**:
- Complexity: complex (new technical domain, multiple non-negotiables in tension)
- Activated agents: cto, frontend-developer, backend-developer, engineering-manager
- Round cap: 4

**Rounds 1–4 (livelock pattern)**:
- Round 1: Backend Dev proposes OT (Operational Transformation). Frontend Dev: OT requires a specific event ordering API that doesn't exist yet.
- Round 2: Backend Dev proposes CRDTs instead. Frontend Dev: CRDT merge events need a different client-side state model, which requires the Backend Dev to define the event schema first.
- Round 3: Backend Dev defines event schema. Frontend Dev: schema doesn't handle offline conflict resolution, which Backend Dev needs to decide.
- Round 4: Backend Dev addresses offline conflicts. Frontend Dev: the offline solution requires a different auth scope model.
- Each round: `changed: true` for both agents. No monotonic progress. CTO should detect this pattern and call it.

**Correct resolution**:
- CTO or EM detects livelock by round 3 and explicitly names it: "We are in a dependency loop. This requires a joint architecture session, not another round of sequential proposals."
- Escalate or explicitly call convergence with a meta-decision: "We cannot resolve API contract and conflict resolution strategy in sequential rounds. Recommend: CTO decides the conflict resolution model as a constraint, then Frontend Dev designs against it."

## Failure Signals
- System runs all 4 rounds with `changed: true` on Backend Dev and Frontend Dev every round without any agent naming the loop → L1 fail
- Synthesis treats the final-round proposal as "the decision" despite it being the fourth iteration of an unresolved dependency → H1 fail (false convergence)
- No agent triggers escalation or meta-decision after detecting circular dependency → L2 fail
- Router does not flag that round cap was reached without genuine convergence → R4 fail

## Pass Conditions
By round 3 at latest, CTO or EM explicitly names the dependency loop, proposes a resolution mechanism (impose constraint, escalate, or joint design session), and the system does not synthesise the final-round proposal as a genuine decision.

## Detection Check
Measure semantic distance between agent positions across rounds. In livelock: Backend Dev and Frontend Dev positions change every round (high `changed: true` rate) but their positions are not converging — distance is non-decreasing. A monotonic convergence check should flag this.

## Trainer Evaluation Focus
Did any agent detect and name the loop? Did the system distinguish between "agents are producing outputs" (active) and "agents are making progress" (convergent)?
