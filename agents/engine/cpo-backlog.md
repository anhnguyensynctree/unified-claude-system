# CPO Backlog — Format and Rules

## File location

```
[project]/.claude/agents/backlog/priority-queue.md
```

Created by CPO after every synthesis. Read by OMS dispatcher to determine next task.

## Entry format

```markdown
## [priority-number] [task-slug] | source:[cpo|cro|exec|ceo] | status:[queued|running|done]
Why: [one sentence — what user need or milestone this serves]
Owner: [dept: engineering|research|exec]
Approved by: [cto|cpo|clo|cfo] ✅ | pending: [role]
Dependencies: [task-slug or none]
Details:
  - [action item 1]
  - [action item 2]
  - [action item 3]
```

Example:
```markdown
## 1 notification-system | source:cpo | status:queued
Why: Users miss time-sensitive updates — core retention driver for MVP
Owner: engineering
Approved by: cto ✅ cpo ✅ | pending: none
Dependencies: 2026-03-22-auth-flow
Details:
  - Add push notification service (FCM)
  - Notification preferences in user settings
  - In-app notification feed with read/unread state
```

## CPO generation rules

After every synthesis, CPO runs a backlog pass:
- Input: synthesis `action_items[]` + `product-direction.ctx.md` + completed task log
- Add next 1–3 tasks ordered by product impact
- Mark completed tasks `status:done`
- Never remove done entries — archive marker only

## C-suite approval requirement

Any task added by CRO or exec must show approval from at least CTO + CPO before `status:queued`.
Tasks added by CPO directly: CPO approval implicit, CTO approval required for engineering tasks.
Tasks added by CEO (via Discord): immediate queue, no approval gate.

## Dispatcher read rules

On `_auto` prompt with checkpoint `next:done`:
1. Read priority-queue.md
2. Find first entry with `status:queued` and `dependencies` all marked `status:done`
3. Start that task via `/oms [task details]`
4. Update entry to `status:running`

If no queued tasks → write non-blocking Discord update: `[project] CPO backlog empty — awaiting new tasks or exec direction`

## Research-to-backlog flow

CRO completes synthesis → proposes milestone to exec → exec approves → CPO breaks milestone into tasks → adds to backlog with `source:exec` + full approval chain. CEO sees outcome in `#oms-updates` only.
