---
name: oms-work
description: oms-work — Execute Cleared Task Queue
---
# oms-work — Execute Cleared Task Queue

Runs pre-cleared tasks from `[project]/.claude/cleared-queue.md`.
No CEO gate. Each task runs in an isolated git worktree. Validation chain runs per task.
One stop: `cto-stop` (branch left open, surfaces next daily session).

Schema: `~/.claude/agents/oms-work/task-schema.md`
Background trigger: send `/work` in any project Discord channel.

---

## Step 0 — Identify project

If `$ARGUMENTS` names a project slug, use it.
If run from inside a project directory (has `.claude/cleared-queue.md`), use that project.
If ambiguous, list projects from `~/.claude/oms-config.json` and ask.

Read `channel_id` for this project from `~/.claude/oms-config.json` — used for Discord notifications throughout.

---

## Step 1 — Read queue

Read `[project]/.claude/cleared-queue.md`. Parse all tasks.

If the file does not exist:
```
No cleared queue found for [project]. Run the daily /oms session first to generate tasks.
```

Compute:
- **ready**: status=queued AND all Depends are done
- **blocked**: status=queued AND at least one Depends not yet done
- **done**: status=done
- **cto-stop**: status=cto-stop

Show a status table:
```
TASK-001  Add JWT refresh rotation    queued     ready      dev → qa → em
TASK-002  Research drop-off patterns  queued     ready      researcher → cro → cpo
TASK-003  Implement re-engagement     queued     blocked    TASK-002
```

If no ready tasks: report status and exit.

---

## Step 2 — Execute ready tasks

Group ready tasks into:
- **Independent**: no shared context files (can run in parallel)
- **Chains**: tasks where one depends on another already-ready task

For independent tasks: use Agent tool, one subagent per task, all launched in the same message.
For chains: run in dependency order (N-1 completes before N starts).

**Before launching each task** — post running signal to Discord:
```bash
python3 -c "
import sys; sys.path.insert(0, '$HOME/.claude/bin')
import oms_discord as d, json
from pathlib import Path
cfg = json.loads(Path('$HOME/.claude/oms-config.json').read_text())
proj = list(cfg['projects'].values())[0]  # replaced per task
tf = Path(proj['path']) / '.claude/oms-work-threads.json'
d.notify_task(proj['channel_id'], tf, 'MILESTONE', 'TASK-ID', 'TITLE', None, 'running')
"
```
Replace MILESTONE, TASK-ID, TITLE with actual values. Use `get_or_create_thread` + `post_to_thread` for the `▶ TASK-ID — title \`running\`` message.

Each subagent receives this prompt:

```
OMS work task ([task-id]): [spec]

Acceptance criteria:
- [criterion]
- [criterion]

Context files: [comma-separated paths]

Instructions:
1. Read context files.
2. Complete the task fully. For impl: make all file changes. For research: write findings to logs/research/[task-id].md.
3. Run package installs if the task requires them. Do NOT re-run builds or installs to verify — make your changes, run installs once if needed, then stop.
4. Run validation chain: [agent → agent → agent]
   For each validator, use their role below to assess the output:
   - dev: correctness, completeness, code quality. Always run: `git ls-files | grep -E "node_modules|coverage|\.next|dist/|\.env$"` — any results = FAIL (IQ1). Not scaffold-specific; runs on every task.
   - qa: each acceptance criterion — pass or fail? Also verify: `git status --short` shows only source files — no build artifacts, no dependency dirs. For any task that adds or changes a user-facing flow: confirm an E2E spec exists under `e2e/<flow>.spec.ts` and passes (`pnpm exec playwright test`). Missing E2E for a UI/flow task = FAIL.
     **Browse evidence QA — required for every UI/flow task:** After E2E passes, use `/browse` to screenshot each acceptance criterion for this task only (not the full E2E suite) against the live deployed URL (Vercel production or localhost if not yet deployed). Navigate to the relevant page, take a screenshot, confirm the criterion is visually met. Save to `qa/screenshots/TASK-NNN-<criterion>.png`. If the page shows an error state, wrong content, or a console/network error: FAIL. No screenshot evidence = FAIL.
   - em: final approval — spec met, ready to merge? Confirm git diff is scoped to task deliverables only — no unintended files.
   - researcher: methodology sound, findings complete?
   - cro: findings rigorous and actionable?
   - cpo: output creates clear product direction?
   - cto: architectural soundness, no blocking technical risk?
5. **Before outputting the final line** — write the quality record:
   ```bash
   python3 -c "
   import json, datetime
   from pathlib import Path
   costs_dir = Path.home() / '.claude' / 'oms-costs'
   costs_dir.mkdir(exist_ok=True)
   record = {
       'task_id': 'TASK-NNN',
       'slug': 'SLUG',
       'title': 'TITLE',
       'type': 'TYPE',
       'milestone': 'MILESTONE',
       'date': datetime.datetime.utcnow().isoformat() + 'Z',
       'passed': PASSED_BOOL,
       'fail_at': FAIL_AT_OR_NONE,
       'validators': VALIDATORS_DICT,
       'cost_usd': None,
       'total_usd': None,
       'notes': 'NOTES',
   }
   (costs_dir / 'SLUG-TASK-NNN.json').write_text(json.dumps(record, indent=2))
   proj_path = Path('PROJECT_PATH')
   mf = proj_path / '.claude' / 'oms-metrics.json'
   rows = json.loads(mf.read_text()) if mf.exists() else []
   rows.append({'task_id': record['task_id'], 'slug': record['slug'], 'title': record['title'],
                'date': record['date'], 'passed': record['passed'], 'fail_at': record['fail_at'], 'cost_usd': None})
   mf.write_text(json.dumps(rows, indent=2))
   "
   ```
   Replace all placeholders with actual values. `cost_usd`/`total_usd` are `null` on the skill path — Agent tool does not expose usage data.
6. Output for each validator: "[validator]: PASS" or "[validator]: FAIL — [reason]"
7. Final line: "DONE — [1 sentence summary]" or "CTO-STOP — [validator]: [reason]"
```

---

## Step 3 — Process results

After each subagent returns:

**If DONE**:
- Run pre-commit sanity check (blocks commit if any fail):
  ```bash
  FAIL=0
  # No dependency or build dirs tracked
  git ls-files | grep -qE "^node_modules/|^\.next/|^dist/|^out/|^coverage/|^\.pnpm-store/" && echo "BLOCKED: build/dependency dir in git index" && FAIL=1
  # No .env files with real values (allow .env.example)
  git diff --cached --name-only | grep -qE "^\.env$|^\.env\." | grep -qv "example" && echo "BLOCKED: .env file staged" && FAIL=1
  # No files over 500KB
  git diff --cached --name-only | while read f; do [ -f "$f" ] && [ $(wc -c < "$f") -gt 512000 ] && echo "BLOCKED: large file staged: $f" && FAIL=1; done
  [ $FAIL -eq 1 ] && exit 1 || true
  ```
- Commit all changes in the worktree: `git add -A && git commit -m "oms-work: TASK-NNN — title"`
- Remove the worktree (branch stays for merge): `git worktree remove --force .claude/worktrees/TASK-NNN`
- Update `cleared-queue.md`: Status: done, Notes: branch name
- Post to Discord: `✓ TASK-NNN — title \`done\``

**If CTO-STOP**:
- Leave the worktree open — CTO or CEO reviews the branch directly
- Update `cleared-queue.md`: Status: cto-stop, Notes: stop reason + branch name
- Do NOT merge. Do NOT delete the worktree.
- Post to Discord: `⚑ TASK-NNN — title \`cto-stop\` — [reason]`

For Discord posts use:
```bash
python3 -c "
import sys; sys.path.insert(0, '$HOME/.claude/bin')
import oms_discord as d, json
from pathlib import Path
cfg = json.loads(Path('$HOME/.claude/oms-config.json').read_text())
proj = cfg['projects']['SLUG']
tf = Path(proj['path']) / '.claude/oms-work-threads.json'
d.notify_task(proj['channel_id'], tf, 'MILESTONE', 'TASK-ID', 'TITLE', PASSED, 'NOTES')
"
```

After a task completes (done), check if any blocked tasks are now unblocked.
If yes: run them immediately (they become the next wave of parallel agents).

---

## Step 4 — Final report

```
## OMS Work — [project]

Completed:
  ✓ TASK-001 — Add JWT refresh rotation — all validators passed
  ✓ TASK-002 — Research drop-off patterns — researcher → cro → cpo passed

Stopped:
  ⚑ TASK-003 — Implement re-engagement — CTO-STOP: conflicts with pending session store refactor

Blocked (unmet deps):
  ○ TASK-004 — depends on TASK-003

Next daily session: resolve TASK-003 (CTO-STOP) before requeueing.
```

If everything passed: "Queue clear — all tasks done."

---

## Step 5 — CEO Executive Brief

After all tasks complete, invoke the Executive Briefing Agent:

**1. Write the briefing file** — write `[project]/.claude/oms-briefing.md` using the schema at `~/.claude/agents/executive-briefing-agent/briefing-schema.md`.
Populate from: completed/stopped task list, `cleared-queue.md` state, `product-direction.ctx.md`, any CTO-stop reasons, and `[project]/.claude/oms-metrics.json` for the `## Task Quality` section (validator pass/fail per task).

**2. Invoke the agent** — load `~/.claude/agents/executive-briefing-agent/persona.md` + `executive-briefing-agent/lessons.md`.
The agent reads `oms-briefing.md` and outputs the executive brief to the CEO (terminal).

**3. Post to milestone thread** — extract TL;DR bullets and What Was Done items from the brief, post both to the milestone thread (same thread where task statuses appeared):
```bash
python3 -c "
import sys; sys.path.insert(0, '$HOME/.claude/bin')
import oms_discord as d, json
from pathlib import Path
cfg = json.loads(Path('$HOME/.claude/oms-config.json').read_text())
proj = cfg['projects']['SLUG']
tf = Path(proj['path']) / '.claude/oms-work-threads.json'
d.post_brief_to_thread(
    proj['channel_id'], tf, 'MILESTONE',
    ['TLDR_LINE_1', 'TLDR_LINE_2', 'TLDR_LINE_3'],
    ['ITEM_1 — impact', 'ITEM_2 — impact'],
)
"
```

**4. Append to daily log** — write both sections to `[project]/.claude/oms-daily-log.md`:
```
## YYYY-MM-DDTHH:MMZ | oms-work
• [tl;dr bullet 1]
• [tl;dr bullet 2]
• [tl;dr bullet 3 — CEO action or "No decision required"]
Built: [item 1] — [impact on product/users]
Built: [item 2] — [impact on product/users]
```

---

## Merge guidance (after /oms-work completes)

Done tasks have committed branches named `oms-work/task-nnn`.
To merge all done tasks into main:
```
git merge oms-work/task-001 oms-work/task-002 ...
```
Or review each branch first: `git diff main oms-work/task-001`

CTO-stop branches: do not merge. Resolve at next daily session, re-spec the task, re-queue.

---

## Session cleanup

After the final report, run:
```bash
touch ~/.claude/.skip-handoff
```

This signals the session-end hook to skip mem0 extraction — oms-work sessions are execution only.
