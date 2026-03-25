# Cleared Task Queue

Tasks written by the daily OMS session. Executed by `/oms-work`.
Schema: `~/.claude/agents/oms-work/task-schema.md`

All tasks here have passed the queue gate — no CEO input needed during execution.
One stop condition: `cto-stop` (surfaces at next daily session).

---

<!-- Example — delete before use

## TASK-001 — Add JWT refresh token rotation
- **Status:** queued
- **Type:** impl
- **Spec:** The system SHALL rotate refresh tokens on each use and invalidate the full token family on reuse detection so that stolen tokens cannot be replayed.
- **Scenarios:** GIVEN a valid refresh token WHEN POST /auth/refresh THEN response contains new access + refresh pair | GIVEN a reused refresh token WHEN POST /auth/refresh THEN all tokens in the family are invalidated and 401 returned | GIVEN a fresh session WHEN token expires at 15min THEN access token is rejected and requires refresh
- **Artifacts:** src/auth/tokens.ts — exports: generateToken, verifyToken, revokeFamily | src/auth/middleware.ts — updated to call verifyToken
- **Produces:** src/auth/tokens.ts — exports: generateToken, verifyToken, revokeFamily
- **Verify:** npm test src/auth | npm run lint
- **Context:** src/auth/tokens.ts, src/auth/middleware.ts
- **Activated:** backend-developer, qa-engineer, engineering-manager
- **Validation:** dev → qa → em
- **Depends:** none

## TASK-002 — Research user re-engagement patterns after onboarding drop-off
- **Status:** queued
- **Type:** research
- **Spec:** The system SHALL synthesise evidence-backed re-engagement hypotheses from behavioural psychology and product analytics so that a day-3 notification strategy can be prioritised.
- **Scenarios:** GIVEN the research output WHEN reviewed by CRO THEN ≥3 hypotheses each with a testable prediction are present | GIVEN the research output WHEN reviewed by CPO THEN at least one hypothesis maps to an existing product capability
- **Artifacts:** logs/research/TASK-002-reengagement.md — contains ≥3 hypotheses with testable predictions
- **Produces:** logs/research/TASK-002-reengagement.md — highest-confidence hypothesis with trigger condition
- **Verify:** test -f logs/research/TASK-002-reengagement.md
- **Context:** .claude/agents/product-direction.ctx.md
- **Activated:** human-behavior-researcher, chief-research-officer, cpo
- **Validation:** researcher → cro → cpo
- **Depends:** none

## TASK-003 — Implement day-3 re-engagement push notification
- **Status:** queued
- **Type:** impl
- **Spec:** The system SHALL fire a push notification exactly once at 72h post-onboarding if the user has not returned so that the highest-confidence re-engagement hypothesis from TASK-002 is tested.
- **Scenarios:** GIVEN a user who completed onboarding 72h ago and has not returned WHEN the scheduler runs THEN one push notification is sent | GIVEN a user who returned within 72h WHEN the scheduler runs THEN no notification is sent | GIVEN a notification already sent WHEN the scheduler runs THEN no duplicate is sent
- **Artifacts:** src/notifications/reengagement.ts — exports: scheduleReengagement, cancelReengagement | src/notifications/index.ts — wires scheduleReengagement into onboarding completion hook
- **Produces:** none
- **Verify:** npm test src/notifications | npm run lint
- **Context:** src/notifications/, logs/research/TASK-002-reengagement.md
- **Activated:** backend-developer, qa-engineer, engineering-manager
- **Validation:** dev → qa → em
- **Depends:** TASK-002

-->
