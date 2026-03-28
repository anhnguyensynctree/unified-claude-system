# Scenario 066 — Impl Task Oversized at Elaboration (Tier 1)

**Difficulty**: Medium
**Primary failure mode tested**: Elaboration Agent writes a ⚠ LARGE impl task to cleared-queue.md instead of splitting it at elaboration time.
**Criteria tested**: TS1, TS2, TS3

## Synthetic CEO Intent

> `/oms all` on a FEATURE block with the following action_item from exec synthesis:
> ```
> action: "Build account settings page — change email, change password, notification preferences, billing info, danger zone (delete account)"
> type: impl
> departments: [frontend-developer]
> depends_on: []
> ```

Five distinct user interactions in one impl task — well over the sizing threshold for a single task.

## Expected Behavior

**Elaboration Agent sizing check (pre-flight):**
- Count distinct user interaction surfaces: (1) change email form, (2) change password form, (3) notification preferences toggles, (4) billing info section, (5) danger zone / delete account
- 5 interactions → ≥3 Scenarios per interaction → combined Scenarios would exceed 10
- TS3 rule: impl tasks spanning >3 distinct user interactions must be split at elaboration time
- Do NOT write a single LARGE task; split into 2 tasks at elaboration time

**Correct output — 2 tasks:**

TASK-NNN (settings shell + read-only sections):
```
Status: queued
Type: impl
Spec: The account settings page SHALL be implemented as a client component shell with read-only display of current email, current notification preferences, and billing info.
Scenarios: ≤3 GIVEN/WHEN/THEN covering: page loads with current values, unauthenticated redirect, billing placeholder renders
Artifacts: app/(app)/settings/page.tsx | components/settings/SettingsShell.tsx
Depends: [auth task]
```

TASK-NNN+1 (mutative forms — change email, change password, danger zone):
```
Status: queued
Type: impl
Spec: The account settings page SHALL add change-email form, change-password form, and danger-zone delete-account button with confirmation dialog.
Scenarios: ≤3 GIVEN/WHEN/THEN covering: email update submits and shows success, password mismatch error shown, danger zone requires confirmation before delete fires
Artifacts: app/(app)/settings/page.tsx (extended) | components/settings/ChangeEmailForm.tsx | components/settings/ChangePasswordForm.tsx | components/settings/DangerZone.tsx
Depends: TASK-NNN
```

## Failure Signals

**TS3 fail — oversized task written as-is:**
```
## TASK-NNN — Account Settings Page
Status: queued
Type: impl
Spec: The account settings page SHALL implement change email, change password, notification preferences, billing info, and danger zone delete account.
⚠ LARGE — consider splitting before execution
```
Any `⚠` annotation, "consider splitting", or "LARGE" note in a queued task's fields is a TS3 fail — the task should never have been written to the queue in this state.

**TS3 fail — flagged and deferred instead of split:**
The Elaboration Agent flags the task as oversized and adds a note saying "recommend splitting before /oms-work" but writes the single task to cleared-queue.md anyway. The flag is useless — it produces the same outcome as no flag. Split must happen during elaboration, not during execution.

**TS2 fail — split pair with broken Depends:**
```
## TASK-NNN+1 — Account Settings Mutative Forms
Depends: none
```
When a task is split, the downstream task must have `Depends: TASK-NNN` pointing to the upstream task. `Depends: none` on the second task of a split pair fails TS2.

## Pass Conditions

- Two tasks produced — neither contains more than 3 Scenarios
- Neither task has a ⚠ annotation, "LARGE" label, or "consider splitting" note
- TASK-NNN+1 has `Depends: TASK-NNN`
- Each task's Spec has exactly one SHALL clause covering its scoped interactions only
- Artifacts in each task do not overlap

## Trainer Evaluation Focus

The trap is an Elaboration Agent that writes the single large task to the queue with a ⚠ flag, treating the flag as sufficient. Trainer must check: if any queued task contains the words "LARGE", "⚠", "consider splitting", or "recommend splitting", that is a TS3 failure regardless of any other quality in the task. The flag is not a mitigation — it is the failure.
