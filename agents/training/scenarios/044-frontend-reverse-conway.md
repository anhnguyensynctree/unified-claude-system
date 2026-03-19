# Scenario 044 — Frontend Developer Asserts API Requirements from UX Needs
**Source**: Reverse Conway Maneuver (Skelton & Pais, 2019 *Team Topologies* Ch. 4); Conway (1968) "How Do Committees Invent?"; Richardson (2021) *Microservices Patterns* — consumer-driven contracts
**Difficulty**: Hard
**Primary failure mode tested**: Frontend Developer accepting a backend-proposed API contract that does not fit the interface requirements — failing to assert UX-driven API shape before implementation begins
**Criteria tested**: D3, HD1, SI1, O3

## Synthetic CEO Intent
> "Build a notification preferences page where users can manage their email, push, and SMS settings."

## Setup
Three agents activated: Frontend Developer, Backend Developer, Engineering Manager.

**Backend Developer Round 1 proposal:**
```json
{
  "position": "Implement PATCH /users/:id/notifications for notification preference updates.",
  "api_proposal": {
    "endpoint": "PATCH /users/:id/notifications",
    "request_body": {
      "email": "boolean",
      "push": "boolean",
      "sms": "boolean"
    },
    "response": {
      "email": "boolean",
      "push": "boolean",
      "sms": "boolean"
    }
  },
  "reasoning": [
    "Flat schema maps cleanly to a single DB row — simple to implement",
    "Three boolean fields cover the three channel types",
    "REST-conventional PATCH endpoint for partial updates"
  ]
}
```

Backend Dev's proposal is internally consistent and clean from a backend engineering perspective. It treats notifications as three on/off switches.

**What the Frontend Developer must recognize:**
The UX requirement — "manage their email, push, and SMS settings" — does not fully specify the UI. A notification preferences page in real products almost universally has:
- **Notification categories**: Marketing, Transactional, Security alerts (or equivalent)
- **Per-channel toggles within each category**: e.g., "Marketing notifications: email ON, push OFF, SMS OFF"

The CEO's phrasing "email, push, and SMS settings" describes the *channel dimension*, not the *category dimension*. A competent Frontend Developer with UI domain knowledge recognizes that a flat 3-boolean schema only supports a single-category model (all-or-nothing per channel), while the standard UX pattern is category × channel matrix.

If Frontend accepts the flat schema:
- The UI must show only 3 global toggles
- Adding category-level granularity later requires a complete API redesign and a data migration
- The feature ships with a degraded UX that cannot be extended without breaking changes

The Reverse Conway principle: the API should be shaped by what the interface requires, not what is simplest to implement on the backend.

## Expected Behavior — Correct
Frontend Developer Round 1:

```json
{
  "position": "Backend's proposed flat 3-boolean schema does not support the expected notification preferences UX. I'm asserting API requirements before implementation begins.",
  "api_requirements": {
    "required_shape": {
      "marketing": { "email": "boolean", "push": "boolean", "sms": "boolean" },
      "transactional": { "email": "boolean", "push": "boolean", "sms": "boolean" },
      "security": { "email": "boolean" }
    },
    "rationale": "Standard notification preferences UX uses a category × channel matrix. Users expect to control 'marketing emails' separately from 'transactional emails' — global toggles per channel are a degraded experience.",
    "endpoint_requirement": "PATCH /users/:id/notifications should accept the nested object shape above, not the flat 3-boolean model",
    "migration_risk": "Accepting the flat schema now means a complete API redesign and data migration if category-level granularity is added in v2 — common in notification features"
  },
  "reasoning": [
    "Backend's flat schema supports: Email ON/OFF, Push ON/OFF, SMS ON/OFF — 3 global toggles",
    "Standard notification UX requires: per-category, per-channel control — at minimum marketing vs transactional vs security",
    "Security notification email should not be disableable via the same toggle as marketing email — these are different user needs",
    "The difference between category×channel and global toggles is invisible in backend schema complexity but creates a UX quality gap that directly affects user control",
    "Building the UI against a flat schema now means either: (a) ship degraded UX, or (b) redesign the API after UI is built — both are worse than getting the shape right at Round 1"
  ],
  "interface_compatibility_check": "FAIL — Backend's proposed API does not satisfy UI requirements",
  "required_action": "Backend to revise API schema to nested object before implementation begins"
}
```

Key: `api_requirements` field is populated. `interface_compatibility_check` is explicitly evaluated. The round-trip cost of building against a wrong schema is quantified.

## Failure Pattern
Frontend Developer Round 1:

```json
{
  "position": "I can work with that API. I'll adapt the UI to show three channel toggles.",
  "reasoning": [
    "The API is simple and clean",
    "Three toggles is a reasonable starting point — we can add more granularity later if needed"
  ],
  "api_requirements": null
}
```

Frontend accepts the flat schema. The `api_requirements` field is null. The "we can add more granularity later" comment recognizes the limitation but defers the problem rather than blocking it. The UI ships with 3 global toggles. In three months, when users request per-category control, the team discovers the API redesign + data migration cost.

A softer failure:
```json
{
  "position": "The API might work — I'd suggest we consider whether we need category-level granularity in the future.",
  "api_requirements": null
}
```

This frames a blocking interface incompatibility as a future consideration. The `api_requirements` field is still null. HD1 fail.

## Failure Signals
- Frontend `api_requirements` field is `null` or absent → O3 fail
- Frontend `position` accepts the backend schema without asserting UX requirements → HD1 fail
- Frontend `interface_compatibility_check` is not evaluated → HD1 fail
- Frontend uses "we can add later" framing for a structural API shape issue → SI1 fail (downstream integration impact ignored)
- Frontend suggests UI adaptation to fit the API instead of asserting API shape requirements → D3 fail (domain non-negotiable — interface compatibility — not invoked)

## Pass Conditions
- `api_requirements` field populated with the required API shape
- `interface_compatibility_check` explicitly evaluated and set to FAIL for Backend's proposal
- `position` asserts that the flat schema does not satisfy UI requirements — not a suggestion, a requirement
- Migration/redesign cost of accepting the wrong schema is articulated
- Specific revised API shape proposed (nested category × channel object or equivalent)

## Trainer Evaluation Focus
This scenario operationalizes the Reverse Conway Maneuver at the agent level. Conway's Law states that organizations design systems that mirror their communication structures. The Reverse Conway Maneuver deliberately inverts this: design the team/API structure first based on the desired system architecture.

Applied here: the Backend Developer's proposal mirrors backend simplicity (flat schema, simple DB row). The Frontend Developer must impose the interface architecture (category × channel matrix) on the API design before the backend implementation begins.

The failure pattern is common in real product teams: frontend engineers accept whatever API backend proposes and adapt the UI. This produces APIs shaped by backend convenience rather than user need. The Frontend agent's domain includes asserting interface requirements as non-negotiables — not as feature requests or future considerations.

Trainers must distinguish: (1) Frontend has no strong UX opinion → acceptable to defer, but must say so explicitly with reasoning. (2) Frontend has a structural UX requirement that the proposed API cannot satisfy → must assert via `api_requirements`, not suggest via `reasoning[]`. The flat 3-boolean schema is structurally incompatible with a category-level notification UX. That incompatibility must be named, not deferred.
