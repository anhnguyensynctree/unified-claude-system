# Scenario 016 — Implementation Handoff Failure

**Source**: Brooks (1975) *The Mythical Man-Month* — interface specification failures; Yourdon & Constantine (1979) structured design coupling/cohesion theory; ChatDev "interface assumption error" (Qian et al., 2023)
**Difficulty**: Intermediate
**Primary failure mode tested**: C-suite synthesis underspecifies an interface; two implementation agents proceed with incompatible interpretations; conflict is invisible until integration — distinct from Scenario 012 (hidden dependency between agents designing simultaneously), this is about plan-to-implementation ambiguity in a sequential handoff
**Criteria tested**: SI1, SI2, HD1, HD2, C4, O3

## Synthetic CEO Intent
> "Add a real-time activity feed to the dashboard — users should see recent events as they happen."

## Setup
C-suite synthesizes: "Implement a real-time activity feed. Backend Dev builds the event delivery system. Frontend Dev builds the feed UI. Target: 2-week sprint."

The synthesis does not specify:
- Transport mechanism (WebSocket vs. Server-Sent Events vs. polling)
- Event payload schema (field names, types, required vs. optional)
- Delivery guarantee (at-most-once vs. at-least-once vs. exactly-once)
- Connection lifecycle (who initiates, how reconnection is handled)

**Seeded incompatible assumptions:**
- **Frontend Dev** assumes WebSocket with payload: `{ event_id, event_type, user_id, message, timestamp }`. Uses `event_id` for deduplication to prevent duplicate event rendering in the feed.
- **Backend Dev** assumes Server-Sent Events (SSE) with payload: `{ type, actor_id, description, created_at }`. No `event_id` — SSE handles ordering natively, no deduplication needed.

These are incompatible:
- Frontend's WebSocket client fails against Backend's SSE endpoint (different protocol)
- Frontend's deduplication logic breaks without `event_id`
- Field name mismatches (`event_type` vs. `type`, `user_id` vs. `actor_id`, `message` vs. `description`)

## Expected Behavior — Correct
If routed correctly as complex (multi-domain, interface dependency), both Frontend Dev and Backend Dev participate from Round 1.

**Round 1**: Each agent states their transport and payload assumptions explicitly:
- Frontend Dev: `api_requirements` lists `event_id`, `event_type`, `user_id`, `message`, `timestamp` with types; states WebSocket assumption
- Backend Dev: `proposed_api` states SSE, lists payload fields with types

**Round 2**: Frontend Dev and Backend Dev explicitly cross-reference each other's designs, name the incompatibility, and propose a resolution.

**Synthesis action items** include: "Before parallel implementation begins: Frontend Dev and Backend Dev agree on transport mechanism and payload schema (owner: CTO, due: Day 1 of sprint). Implementation does not begin until interface contract is documented."

## Failure Pattern
C-suite synthesis assigns parallel implementation without interface specification. Frontend Dev and Backend Dev begin work against their own assumptions. Two weeks later: integration fails, full sprint lost, deduplication logic must be rewritten, reconnection handling duplicated.

## Failure Signals
- Synthesis action items assign parallel implementation without transport mechanism or payload schema → SI1, SI2 fail
- Frontend Dev's `api_requirements` field is empty, vague ("standard event format"), or missing field names → O3 fail
- Backend Dev's `proposed_api` field does not specify transport mechanism → O3 fail
- Neither agent cross-references the other's design by Round 2 → HD1 fail
- CTO does not flag the interface incompatibility → HD2 fail
- Synthesis action items have no interface alignment step before parallel implementation → C4 fail

## Pass Conditions
By Round 2, Frontend Dev and Backend Dev have each explicitly stated their transport and payload assumptions. At least one agent names the incompatibility if their designs differ. CTO or Facilitator flags the dependency as requiring resolution before parallel work begins. Synthesis action items include a mandatory interface alignment step — transport mechanism agreed, payload schema documented with field names and types — with a named owner and deadline, before parallel implementation is assigned.

## Trainer Evaluation Focus
Did any agent treat the synthesis's "build X" action item as complete implementation instructions, or did they surface the missing interface specification? The characteristic failure is two agents producing perfectly coherent outputs that are mutually incompatible — each internally consistent, together broken. Check Frontend Dev's `api_requirements` field: does it list specific field names? Check Backend Dev's `proposed_api`: does it specify transport mechanism? If both fields are vague, SI1/SI2/O3 all failed. If they're specific but incompatible and no agent named the conflict, HD1 failed.
