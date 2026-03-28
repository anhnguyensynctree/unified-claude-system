# Scenario 065 — Milestone Completion and Product Direction Update

**Difficulty**: Medium
**Primary failure mode tested**: All features in a milestone complete but product-direction.ctx.md is not updated; CPO fails to update the milestone status; next exec session reads stale milestone as still active.
**Criteria tested**: MF1, MF2, EX2

## Setup

Project: daily-cosmos. product-direction.ctx.md has:
```
| system-roster | Define all 21 interpretation systems + independence weights |
| synthesis-algorithm | Build weighted synthesis engine |
```

cleared-queue.md contains:
```
## FEATURE-001 — System Roster Definition
- Status: done
- Milestone: system-roster

## FEATURE-002 — Independence Weight Research
- Status: done
- Milestone: system-roster

## TASK-001 ... TASK-006: all Status: done
```

All features in `system-roster` milestone are `done`. Sign-offs are complete.

## Expected Behavior

**CPO trigger — MF2:**
When the last feature in a milestone transitions to `done`, CPO updates product-direction.ctx.md:
- Marks `system-roster` milestone as complete (adds completion date or removes from active list)
- Does NOT invent new milestones
- Does NOT alter the next milestone's scope

**What the update looks like:**
```
## Milestones

| Name | Description | Status |
|---|---|---|
| system-roster | Define all 21 interpretation systems + independence weights | ✅ complete (2026-03-24) |
| synthesis-algorithm | Build weighted synthesis engine | active |
```

Or if product-direction.ctx.md doesn't track status inline: CPO adds a completion note and logs it in the task log.

**Next exec session picks up correctly:**
- When exec fires next, CPO reads product-direction.ctx.md
- Sees `system-roster` as complete — does NOT re-propose it
- Gaps: only `synthesis-algorithm` and later milestones remain
- CPO selects `synthesis-algorithm` as the next milestone to advance

## Failure Signals

- product-direction.ctx.md not updated after all system-roster features complete → MF2 fail
- Next exec session re-selects `system-roster` milestone because it still appears active → MF2 downstream failure
- CPO adds a completion date but to the wrong milestone → data integrity fail
- CPO updates product-direction.ctx.md without recording which feature sign-offs triggered it → EX2 fail (product_direction_update missing rationale)
- CPO renames or re-scopes `synthesis-algorithm` while updating `system-roster` → out-of-scope change

## Pass Conditions

- product-direction.ctx.md shows `system-roster` as complete with date
- `synthesis-algorithm` milestone is unchanged
- Next exec session CPO reads the updated file and skips `system-roster` in milestone gap report
- CPO's `product_direction_update` in exec synthesis references the completed milestone by name

## Note on Triggering

MF2 is triggered by CPO, not by OMS engine. The trigger is: "last feature in milestone transitions to done." In manual sessions, the Trainer flags if CPO doesn't update after this event. In autonomous sessions, the CPO backlog pass (Step 5.5) handles this check.

## Trainer Evaluation Focus

MF2 can only be evaluated in a session where a milestone completion event occurred. Trainer must first check: did any milestone have all features reach `done` in this session? If yes, check product-direction.ctx.md for the update. If MF2 fires but CPO didn't update, it's a lesson candidate for CPO: "milestone completion must update product-direction.ctx.md immediately — stale milestone data causes exec to re-select completed work."
