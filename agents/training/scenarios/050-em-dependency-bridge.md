# Scenario 050 — EM Proactive Dependency Bridge

**Source**: Conway (1968) "How Do Committees Invent?" — organizational structure mirrors system design; Skelton & Pais (2019) *Team Topologies* — interaction modes and cognitive load; Brooks (1975) *The Mythical Man-Month* — interface specification as primary coordination task
**Difficulty**: Intermediate-Hard
**Primary failure mode tested**: Two domain agents design interacting systems independently; EM does not proactively name the inter-agent dependency; CTO has to do it instead — or nobody does and it reaches synthesis unresolved
**Criteria tested**: D4 (EM domain bridge, not just delivery estimate), B1, B2, HD1 (EM-triggered), C4

## Synthetic CEO Intent
> "Build the order tracking feature — customers should see their order status update in real time after purchase."

## Setup
CTO is **not activated** in this scenario. Activated agents: Backend Developer, Frontend Developer, Engineering Manager.

Backend Dev and Frontend Dev will design their parts independently in Round 1. The hidden dependency: Backend Dev's event model must be consumed by Frontend Dev's real-time UI. If EM does not name this dependency and enforce interface alignment before synthesis, both agents will proceed with incompatible assumptions.

**Round 1 (seeded designs):**

Backend Dev: "Implement order status events — write status changes to an `order_events` table and expose GET /orders/{id}/events for polling. Statuses: placed, processing, shipped, delivered."

Frontend Dev: "Implement real-time order status UI — WebSocket connection to status stream, render status timeline with live updates. Assumes server pushes events on status change."

**The incompatibility:**
- Backend Dev: polling endpoint (GET /events) — pull model
- Frontend Dev: WebSocket push model — assumes server initiates delivery

These are incompatible. Frontend Dev expects push; Backend Dev built pull. Neither can detect this without reading the other's design — or without EM naming the dependency.

## Expected Behavior

**EM Round 1 — correct (bridge function):**
Position: "Backend Dev and Frontend Dev are designing against the same order status interface with incompatible delivery models — Backend Dev proposes polling (pull), Frontend Dev expects WebSocket push. These must be aligned before implementation. I'm naming this as a sequencing constraint: interface contract must be agreed in Round 2 before either agent begins implementation."

Reasoning:
- "Backend Dev Round 1: GET /orders/{id}/events — client pulls on demand"
- "Frontend Dev Round 1: WebSocket push — server initiates on status change"
- "These are incompatible delivery models — polling does not satisfy real-time push requirements"
- "Delivery is blocked until delivery model is agreed — parallel implementation on current designs will produce a broken integration"

EM does not pick which model is correct (that's a CTO/Backend Dev decision). EM names the dependency and blocks parallel implementation.

**EM failure pattern:**
- EM provides delivery estimate only: "4–6 days for backend + 3–4 days for frontend. Total: 7–10 days." → does not cross-reference the designs at all
- EM notes the designs exist but doesn't check compatibility: "Both Backend Dev and Frontend Dev have proposals — delivery seems feasible." → passive acknowledgment, no bridge function
- EM defers compatibility check: "CTO should review whether these designs are compatible." → correct direction but wrong — CTO is not activated; EM owns sequencing in CTO's absence

## Failure Signals
- EM Round 1 position provides only a delivery estimate without referencing Backend Dev's polling model vs Frontend Dev's WebSocket model → B1 fail (inter-agent dependency is a blocker that must appear in position)
- EM Round 1 defers compatibility check to CTO who is not in the discussion → D2 fail (wrong deferral — CTO not activated)
- Synthesis assigns parallel implementation to Backend Dev and Frontend Dev without naming the interface alignment step → HD2 fail
- Neither agent's Round 2 output cross-references the other's design → HD1 fail

## Pass Conditions
EM Round 1 position names the pull-vs-push incompatibility explicitly and blocks parallel implementation until alignment is reached. Synthesis action items include an interface alignment step before parallel implementation begins, with EM or Backend Dev as owner.

## Trainer Evaluation Focus
Did EM read both agents' Round 1 outputs and cross-reference them for compatibility — or did EM only assess delivery feasibility for each agent independently? The bridge function requires EM to read across agents, not just down each agent's output.

In CTO's absence, EM is the only agent with an explicit dependency management mandate. If EM doesn't catch the pull/push incompatibility, it reaches synthesis unresolved. That's not a CTO failure — it's an EM failure.
