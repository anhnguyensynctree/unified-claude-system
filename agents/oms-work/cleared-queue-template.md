# Cleared Task Queue

Tasks written by the daily OMS session. Executed by `/oms-work`.
Schema: `~/.claude/agents/oms-work/task-schema.md`

All tasks here have passed the queue gate — no CEO input needed during execution.
One stop condition: `cto-stop` (surfaces at next daily session).

---

<!-- Example — delete before use

## TASK-001 — Add sliding window refresh token rotation
- **Status:** queued
- **Type:** impl
- **Spec:** Add JWT refresh token rotation to the auth service. Tokens expire at 15 min; refresh tokens rotate on each use with a 7-day window. Invalidate entire token family on reuse detection.
- **Acceptance:** POST /auth/refresh returns new access + refresh pair | Reused token invalidates full family | Unit tests cover rotation and reuse detection
- **Context:** src/auth/tokens.ts, src/auth/middleware.ts
- **Activated:** backend-developer, qa-engineer, engineering-manager
- **Validation:** dev → qa → em
- **Depends:** none

## TASK-002 — Research user re-engagement patterns after onboarding drop-off
- **Status:** queued
- **Type:** research
- **Spec:** Investigate why users who complete onboarding fail to return after day 3. Synthesise findings from behavioural psychology and product analytics angles. Output actionable re-engagement hypotheses.
- **Acceptance:** Minimum 3 evidence-backed hypotheses | Each hypothesis has a testable prediction | Output written to logs/research/TASK-002-reengagement.md
- **Context:** .claude/agents/product-direction.ctx.md, logs/tasks/
- **Activated:** human-behavior-researcher, chief-research-officer, cpo
- **Validation:** researcher → cro → cpo
- **Depends:** none

## TASK-003 — Implement push notification for day-3 re-engagement
- **Status:** queued
- **Type:** impl
- **Spec:** Implement the highest-confidence re-engagement hypothesis from TASK-002 as a push notification trigger. Fire at day 3 if user has not returned since onboarding completion.
- **Acceptance:** Notification fires exactly once at 72h post-onboarding | No notification if user returned | Integration test confirms trigger condition
- **Context:** src/notifications/, logs/research/TASK-002-reengagement.md
- **Activated:** backend-developer, qa-engineer, engineering-manager
- **Validation:** dev → qa → em
- **Depends:** TASK-002

-->
