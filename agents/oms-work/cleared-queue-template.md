# Cleared Task Queue

Tasks written by the daily OMS session. Executed by `/oms-work`.
Schema: `~/.claude/agents/oms-work/task-schema.md`

All tasks here have passed the queue gate — no CEO input needed during execution.
One stop condition: `cto-stop` (surfaces at next daily session).

---

<!--
╔══════════════════════════════════════════════════════════════════════════════════╗
║  EXAMPLES — delete this entire comment block before adding real tasks           ║
║  Four types: impl · research · cto-critical · chained (research → impl)         ║
╚══════════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TYPE 1 — Engineering (impl)
Chain: dev → qa → em
Use for: any feature, bug fix, refactor, or API change
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## TASK-001 — Add JWT refresh token rotation
- **Status:** queued
- **Type:** impl
- **Spec:** The system SHALL rotate refresh tokens on each use and invalidate the full token family on reuse detection so that stolen tokens cannot be replayed.
- **Scenarios:** GIVEN a valid refresh token WHEN POST /auth/refresh THEN response contains new access + refresh pair | GIVEN a reused refresh token WHEN POST /auth/refresh THEN all tokens in the family are invalidated and response is 401 | GIVEN an access token older than 15 minutes WHEN any protected endpoint is called THEN response is 401 with WWW-Authenticate header
- **Artifacts:** src/auth/tokens.ts — exports: generateToken, verifyToken, revokeFamily | src/auth/middleware.ts — modified: calls verifyToken on all protected routes
- **Produces:** src/auth/tokens.ts — exports: generateToken, verifyToken, revokeFamily
- **Verify:** npm test src/auth | npm run lint
- **Context:** src/auth/tokens.ts, src/auth/middleware.ts
- **Activated:** backend-developer, qa-engineer, engineering-manager
- **Validation:** dev → qa → em
- **Depends:** none


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TYPE 2 — Research
Chain: researcher → cro → cpo
Use for: any synthesis, investigation, or hypothesis-generation task
Scenarios test OUTPUT QUALITY, not implementation behavior.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## TASK-002 — Research user re-engagement patterns after day-3 drop-off
- **Status:** queued
- **Type:** research
- **Spec:** The system SHALL synthesise evidence-backed re-engagement hypotheses from behavioural psychology and product analytics so that the highest-confidence trigger strategy can be selected for implementation.
- **Scenarios:** GIVEN the research output WHEN reviewed by CRO THEN ≥3 hypotheses are present each with a testable prediction | GIVEN the research output WHEN reviewed by CPO THEN at least one hypothesis maps to an existing product capability | GIVEN a hypothesis was excluded WHEN the document is read THEN the exclusion reason is documented
- **Artifacts:** logs/research/TASK-002-reengagement.md — sections: hypotheses (≥3) each with evidence and testable prediction, excluded approaches with reasons, recommended implementation order
- **Produces:** logs/research/TASK-002-reengagement.md — highest-confidence hypothesis with trigger condition and predicted lift
- **Verify:** test -f logs/research/TASK-002-reengagement.md
- **Context:** .claude/agents/product-direction.ctx.md, .claude/agents/company-belief.ctx.md
- **Activated:** human-behavior-researcher, chief-research-officer, cpo
- **Validation:** researcher → cro → cpo
- **Depends:** none


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TYPE 3 — CTO / infra-critical
Chain: dev → cto
Use for: new services, DB schema changes, auth architecture, API contracts,
         anything irreversible or with system-wide blast radius
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## TASK-003 — Add Redis session store for horizontal scaling
- **Status:** queued
- **Type:** impl
- **Spec:** The system SHALL replace the in-process session store with Redis so that multiple API instances share session state without sticky routing.
- **Scenarios:** GIVEN two API instances running WHEN a user authenticates on instance A THEN instance B accepts their session token | GIVEN Redis is unavailable WHEN any authenticated request arrives THEN the API returns 503 and logs a structured error | GIVEN a session expires WHEN the TTL elapses in Redis THEN subsequent requests return 401
- **Artifacts:** src/session/store.ts — exports: createSessionStore, SessionStore (interface) | src/session/redis-store.ts — exports: RedisSessionStore implements SessionStore | src/app.ts — modified: passes createSessionStore(config) to session middleware | docker-compose.yml — modified: adds redis service with healthcheck
- **Produces:** src/session/store.ts — SessionStore interface (consumed by any service needing session access)
- **Verify:** npm test src/session | docker compose up -d redis && npm run test:integration
- **Context:** src/session/, src/app.ts, docker-compose.yml, .claude/agents/architecture.ctx.md
- **Activated:** backend-developer, cto
- **Validation:** dev → cto
- **Depends:** none


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TYPE 4 — Chained: research → impl
Research task runs first; impl task reads its Produces as Context.
Note how TASK-005 Context includes TASK-004's Produces verbatim.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## TASK-004 — Research notification timing for day-3 re-engagement
- **Status:** queued
- **Type:** research
- **Spec:** The system SHALL identify the optimal send-time and message framing for a day-3 re-engagement push notification so that TASK-005 can implement with a specific trigger condition and copy.
- **Scenarios:** GIVEN the research output WHEN reviewed by CRO THEN a recommended send-time window is present with supporting evidence | GIVEN the research output WHEN reviewed by CPO THEN the recommended copy variant is testable as an A/B experiment | GIVEN the research output WHEN reviewed THEN one primary recommendation is ranked above all alternatives
- **Artifacts:** logs/research/TASK-004-notification-timing.md — sections: timing analysis, copy variants ranked by predicted CTR, implementation spec (trigger condition + message body)
- **Produces:** logs/research/TASK-004-notification-timing.md — primary recommendation: trigger condition, send-time window, message body
- **Verify:** test -f logs/research/TASK-004-notification-timing.md
- **Context:** .claude/agents/product-direction.ctx.md, logs/research/TASK-002-reengagement.md
- **Activated:** human-behavior-researcher, chief-research-officer, cpo
- **Validation:** researcher → cro → cpo
- **Depends:** TASK-002

## TASK-005 — Implement day-3 re-engagement push notification
- **Status:** queued
- **Type:** impl
- **Spec:** The system SHALL fire a push notification exactly once at 72h post-onboarding using the trigger condition and message body from TASK-004 so that the highest-confidence re-engagement strategy is active in production.
- **Scenarios:** GIVEN a user who completed onboarding 72h ago and has not returned WHEN the scheduler runs THEN exactly one push notification is sent with the TASK-004 message body | GIVEN a user who returned within 72h WHEN the scheduler runs THEN no notification is sent | GIVEN a notification was already sent WHEN the scheduler runs again THEN no duplicate is sent | GIVEN the scheduler fires outside the TASK-004 send-time window THEN notification is queued until the window opens
- **Artifacts:** src/notifications/reengagement.ts — exports: scheduleReengagement, cancelReengagement | src/notifications/scheduler.ts — modified: calls scheduleReengagement on onboarding-complete event | src/notifications/index.ts — re-exports scheduleReengagement, cancelReengagement
- **Produces:** none
- **Verify:** npm test src/notifications | npm run lint
- **Context:** src/notifications/, src/notifications/scheduler.ts, logs/research/TASK-004-notification-timing.md
- **Activated:** backend-developer, qa-engineer, engineering-manager
- **Validation:** dev → qa → em
- **Depends:** TASK-004

-->
