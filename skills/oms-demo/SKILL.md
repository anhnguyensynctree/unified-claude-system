---
name: oms-demo
description: oms-demo — CEO Milestone Walkthrough via Browse/Computer-use
---
# oms-demo — CEO Milestone Walkthrough

Walks through all completed tasks in a milestone on the live deployed URL.
Uses the browse daemon to navigate each feature, execute every scenario from the task spec, record video of each flow, and narrate results in CEO language.
Posts videos + screenshots + health summary to the Discord milestone thread.

**When to run:** after `/oms-work` milestone gate passes, before next milestone planning.
**Model:** Sonnet only — browse requires multi-step tool chains. Never route externally.
**Runs in:** interactive terminal SKILL path only. Not Discord bot path.

---

## Step 1 — Identify project + milestone

If `$ARGUMENTS` names a project slug, use it.
If run from inside a project directory (has `.claude/cleared-queue.md`), use that.
Read `~/.claude/oms-config.json` for `channel_id` and project path.

Read `[project]/.claude/cleared-queue.md`.
Find the milestone with the most recently completed tasks (most `Status: done` in one group).
If ambiguous: list milestone names, ask which to demo.

---

## Step 2 — Get the live URL

Check `[project]/.claude/product-direction.ctx.md` for a `Deployment:` or `Live URL:` line.
If not found: check `[project]/.vercel/project.json` + Vercel API for production alias.
If still not found: ask "What's the live URL for this milestone?"

---

## Step 3 — Collect UI tasks

Read all `Status: done` tasks in the milestone.
Filter to tasks with UI artifacts — Artifacts field contains `.tsx`, `.jsx`, `.html`, `.css`, or route paths (e.g. `app/login/page.tsx`, `pages/dashboard.tsx`).
Also include tasks whose Scenarios mention a page, form, button, route, or visual element.

If no UI tasks: "No UI tasks in [milestone] — no demo needed." and exit.

---

## Step 4 — Start browse session

Load and run the auto-start block from `~/.claude/skills/browse/llms.txt`.
Navigate to the live URL to confirm it loads.
Check `console-errors` — if critical errors on landing page, report and ask whether to continue.

Post to Discord milestone thread:
```
🎬 **oms-demo** — `[milestone]`
URL: [live url]
[N] features to walk through...
```

---

## Step 5 — Walk each UI task

For each UI task, in dependency order (no-depends tasks first):

### 5a — Read the test script

The task's `Scenarios:` field IS the test script. Parse each GIVEN/WHEN/THEN.
Also read `Acceptance:` criteria — these are the visual assertions.

Example scenarios → test actions:
- `GIVEN unauthenticated WHEN / THEN redirect to /login` → navigate to `/`, confirm URL changes to `/login`
- `GIVEN wrong password WHEN submit THEN error "Invalid credentials"` → fill wrong pw, submit, check error text visible
- `GIVEN empty list WHEN /dashboard THEN empty state component renders` → navigate while logged in with no data, screenshot
- `GIVEN valid form WHEN submit THEN confirmation toast appears` → fill correctly, submit, check toast

### 5b — Record each flow

For multi-step flows (2+ actions): use video.
For single-state checks (does X render): use screenshot.

```bash
# Video: multi-step flow
record:start qa/videos/demo-[task-id]-[flow-slug]
go [url]/[route]
fill [selector] [value]
click [selector]
screenshot qa/screenshots/demo-[task-id]-[state].png
record:stop

# Screenshot: single-state
go [url]/[route]
screenshot qa/screenshots/demo-[task-id]-[state].png
```

**Auth contexts** — if scenarios require different auth states, use multi-context:
```
ctx:create admin → login as admin role
ctx:create user  → login as regular user
ctx:switch admin → test admin-only views
ctx:switch user  → confirm access is correctly denied
```

**Edge cases to always check** (from the 5 E2E categories):
1. Happy path — complete the flow successfully, screenshot end state
2. Error state — trigger the error (wrong input, network state), screenshot error UI
3. Empty state — if the feature shows a list/feed, navigate with no data, screenshot
4. Auth edge — if the feature is auth-gated, confirm unauthenticated redirect works
5. Input edge — submit boundary input (empty required field, max-length), screenshot validation

Check `console-errors` and `network-errors` after each scenario. Any errors = note them.

### 5c — Narrate + post per-task result

After each task completes, collect media in preference order:
1. Videos from `qa/videos/demo-[task-id]-*.webm` — preferred, shows the full flow with timing
2. Screenshots from `qa/screenshots/demo-[task-id]-*.png` — for single-state checks

Post to Discord milestone thread using `post_media_to_thread` (handles both PNG + WebM):
- WebM under 8MB uploads directly and plays inline in Discord
- WebM over 8MB: Discord post notes "see qa/videos/" and attaches key screenshot instead

Narration message:
```
✅ **TASK-NNN** — [title]
• Happy path: [1 sentence — what the user sees]
• Error state: [1 sentence — error message renders correctly / or issue found]
• Empty state: [1 sentence — or N/A]
• Auth edge: [1 sentence — or N/A]
⚠️ Issues: [list any console errors or broken scenarios]
```

If a scenario failed (expected element not visible, wrong URL, console error): note it clearly. Do NOT fix it here — log it for CEO review.

---

## Step 6 — Milestone health summary

After all tasks, tally: N tasks demoed, N scenarios passed, N failed.

Post to Discord milestone thread:
```
📋 **Milestone Health** — `[milestone]`

✅ [N] features working on [live url]
⚠️ [N] issues found

Critical paths:
• [flow 1] — [1 sentence status]
• [flow 2] — [1 sentence status]

Issues requiring attention:
• TASK-NNN: [scenario] — [what's wrong]

Videos: qa/videos/demo-[milestone]/
Screenshots: qa/screenshots/

CEO action required: [yes — specific decision needed] or [no — all clear]
```

---

## Step 7 — Close browse session + output to terminal

Output the same summary to terminal.

Tip for CEO: videos in `qa/videos/` show the full flows. Open with any video player. Screenshots in `qa/screenshots/` are in Discord above.
