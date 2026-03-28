# oms-briefing.md — Schema

Every OMS workflow writes this file to `.claude/oms-briefing.md` before calling the Executive Briefing Agent.
The agent reads only this file — no other context needed.

## Format

```markdown
# OMS Briefing
Workflow: [task | exec | all | work]
Date: YYYY-MM-DD
Project: [slug]

## What Happened
[Plain description of what the workflow did — decisions made, tasks run, features drafted]

## Queue State
- Done: N
- Queued: N
- Blocked: N (waiting on deps)
- CTO-Stop: N ([task-id]: reason)

## Milestone
- Name: [milestone name]
- Progress: X/N tasks done
- Stage: [not started | in-progress | complete]

## Product Direction
[2-3 sentences from product-direction.ctx.md — current goal and next milestone]

## Decisions Made
- [Decision 1 + what was traded off]
- [Decision 2 + what was traded off]

## Risks & Unresolved
- [Risk or open question 1]
- [Risk or open question 2]

## Task Quality
- Passed: N/N validators passed
- Failed: [TASK-NNN] — failed at [validator] — [reason]
- CTO-Stop: [TASK-NNN] — [reason]

## Session Cost
$X.XX (if available from oms-budget.json)
```

## Rules
- Written by OMS at the end of every workflow, before invoking the Executive Briefing Agent
- Overwritten each run — one file per project, always current
- Never written by the Executive Briefing Agent itself
- If a section has no content, omit it
