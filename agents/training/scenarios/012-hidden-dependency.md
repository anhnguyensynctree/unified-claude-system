# Scenario 012 — Hidden Dependency Propagation

**Source**: Amazon us-east-1 outage (2021) postmortem; AWS Lambda cascading failure (2020); ChatDev "interface assumption error" (Qian et al., 2023)
**Difficulty**: Intermediate-Hard
**Primary failure mode tested**: Two agents design against each other's systems with incompatible assumptions; neither detects the conflict; synthesis plans their simultaneous execution
**Criteria tested**: HD1, HD2 (new), E1, C4, O3

## Synthetic CEO Intent
> "Build the user notification system — email and in-app notifications when key events happen."

## Setup
This task has a hidden cross-domain dependency: the notification system requires both a backend event model (Backend Dev's domain) and a frontend real-time update mechanism (Frontend Dev's domain) that must agree on event schema, delivery guarantee, and client state model.

Seed them with independently reasonable but mutually incompatible designs:
- Backend Dev designs: webhook-based event system, events fire-and-forget, no delivery receipt, JSON payload with event_type + user_id + metadata
- Frontend Dev designs: WebSocket connection, expects delivery receipt for UI state sync, assumes payload includes event_id for deduplication

These are incompatible. Backend's fire-and-forget conflicts with Frontend's expectation of delivery guarantee. Backend's payload missing event_id breaks Frontend's deduplication requirement.

## Expected Behavior

**Router routing**:
- Complexity: complex (multi-agent system with cross-domain interface contract)
- Activated agents: backend-developer, frontend-developer, cto
- Round cap: 3

**Round 1**:
- Backend Dev: proposes webhook architecture, describes payload schema
- Frontend Dev: proposes WebSocket implementation, describes what it needs from the event stream
- CTO: should immediately flag that these two proposals need to be cross-checked for compatibility

**Round 2 — correct behaviour**:
- Frontend Dev explicitly references Backend Dev's Round 1 schema and states: "Backend's payload schema is missing event_id — my deduplication logic requires it. Backend's fire-and-forget model conflicts with my delivery receipt requirement."
- Backend Dev explicitly references Frontend Dev's requirements and either: (a) updates the proposal to add event_id and delivery receipt, or (b) explains why it's architecturally inappropriate and proposes an alternative

**Round 2 — failure pattern**:
- Frontend Dev: continues describing WebSocket implementation without referencing Backend's schema
- Backend Dev: continues refining webhook design without referencing Frontend's requirements
- CTO: does not flag the incompatibility
- Both agents have `changed: false` — falsely appearing to be stable

## Failure Signals
- Synthesis produces a plan that assumes both Backend's and Frontend's designs will work together, without noting the incompatibility → HD1 fail
- Neither agent's Round 2 output references the other agent's specific technical decisions → E1 fail
- CTO does not name the interface incompatibility between the two proposals → HD2 fail
- Synthesis action items assign Backend Dev and Frontend Dev to implement independently without requiring an interface alignment step first → C4 fail

## Pass Conditions
By Round 2, at least one agent (ideally Frontend Dev or CTO) explicitly names the schema incompatibility. Synthesis action items include a mandatory interface alignment step before parallel implementation begins, with a named owner.

## Trainer Evaluation Focus
Did any agent cross-check their design against the other's? The failure mode is two agents each producing internally coherent outputs that are externally incompatible. The trainer should check: does any agent's `reasoning[]` contain a reference to the other agent's specific technical decisions, not just their domain?
