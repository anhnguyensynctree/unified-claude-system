# Scenario 063 — Queue State Check: All Three Paths

**Difficulty**: Basic
**Primary failure mode tested**: OMS skips queue state check; cto-stop tasks not briefed to CEO; exec not auto-triggered on empty queue; auto-picking from queue instead of stopping.
**Criteria tested**: EP1 (queue gate aspect), R1 (exec auto-trigger)

## Path A — Draft Feature Listing

**Setup:** cleared-queue.md contains 3 FEATURE-NNN blocks with `Status: draft` and no queued tasks.

**CEO intent:** `/oms [some new task]` — CEO provides a task.

**Expected behavior:**
1. OMS reads cleared-queue.md
2. Detects: no `cto-stop` or `needs-review` tasks — no briefing needed
3. Detects: CEO provided a task → proceed normally to Step 1 (Router)
4. Queue state line shown: `Queue: 3 features in draft (FEATURE-001, FEATURE-002, FEATURE-003). Proceeding with: [CEO task].`
5. Does NOT auto-pick FEATURE-001 as the next task
6. Routes CEO's explicit task normally

**Failure signals:**
- OMS routes to FEATURE-001 instead of CEO's task → auto-pick fail (CEO task always wins)
- OMS shows no queue state line → silent queue check (user can't see thought process)
- OMS errors because no queued tasks exist → wrong — draft features don't block new tasks

---

## Path B — cto-stop Tasks Present

**Setup:** cleared-queue.md contains:
```
## TASK-003 — Auth Middleware Refactor
- Status: cto-stop
- Reason: Token revocation strategy uses in-memory blacklist — will not scale past 1 node. Re-spec required.
```

**CEO intent:** `/oms` with or without a task.

**Expected behavior:**
1. OMS reads cleared-queue.md
2. Detects: `cto-stop` on TASK-003
3. **Before any routing**, briefs CEO:
   `"⚑ 1 task needs attention: TASK-003 (cto-stop — Token revocation strategy uses in-memory blacklist, will not scale past 1 node)"`
4. Offers inline re-spec: writes new TASK-003a with the fix
5. CEO can say "skip" → OMS proceeds to routing the new task or exec
6. CEO cannot be left unaware of the cto-stop

**Failure signals:**
- OMS proceeds to routing new task without mentioning TASK-003 → cto-stop invisible
- OMS shows cto-stop but does not include the reason → CEO can't act without re-reading the queue
- OMS re-specs TASK-003 without CEO input → EP3-adjacent (blocking action without acknowledgment)

---

## Path C — Empty Queue, No CEO Task → Exec Auto-Trigger

**Setup:** cleared-queue.md has no `queued` tasks (all done, or file empty).

**CEO intent:** `/oms` with NO task argument.

**Expected behavior:**
1. OMS reads cleared-queue.md — no queued tasks
2. CEO gave no task
3. **Automatically triggers exec session**: reads product-direction.ctx.md, builds milestone gap report, fires exec discussion (CPO + CTO + CFO + CLO + CRO)
4. Does NOT ask CEO "what's the task?" — exec fires silently
5. Queue state line shown before exec fires: `Queue: empty. Auto-triggering exec session.`

**Failure signals:**
- OMS asks CEO: "What would you like to work on?" → wrong; exec auto-fires
- OMS silently does nothing on empty queue + no task → wrong; exec must fire
- OMS picks a done task and re-runs it → wrong
- OMS runs exec but skips milestone gap report in CPO briefing → EP1-adjacent (exec missing context)

---

## Trainer Evaluation Focus

Three independent paths, each testing a different queue gate decision. A trainer evaluating a real session that hits one of these paths should only test that path — don't require all three to be present in a single session. The key cross-path rule: CEO task always wins over queue state (Path A). cto-stop always briefs before routing (Path B). Empty+no-task always auto-triggers exec (Path C). "Otherwise" routing (queue has tasks AND CEO has task) is NOT in this scenario — that's normal routing.
