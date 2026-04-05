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

**Model routing per task** — read `Model-hint` and `Type` from the task block.

**IMPORTANT: Prefer `!work` from Discord over `/oms-work` in REPL.** Discord runs `oms-work.py` which routes all free models via `llm-route.sh` natively. The REPL skill path below is a fallback only.

**Route 1 — Bash → llm-route.sh (ALL task types with free model hints):**
Both impl and research tasks use Bash → llm-route.sh when Model-hint is a free model:
```bash
printf '%s' "<full exec prompt>" | ~/.claude/bin/llm-route.sh <model-hint>
```
- Free model hints: `qwen-coder`, `qwen`, `llama`, `gpt-oss`, `nemotron`, `gemma`, `stepfun`
- llm-route.sh handles fallback chains automatically (model unavailable → next in chain)
- For impl tasks: llm-route.sh generates code → you write the files using Edit/Write tools → run tests
- For research tasks: capture stdout as task output directly
- If exit code non-zero or empty output → retry once with next model in chain, then fall back to Agent tool with `model: "haiku"`

**Route 2 — Agent tool (subscription models only):**
- `Model-hint: sonnet` → Agent tool with `model: "sonnet"` (gate tasks, infra-critical)
- `Model-hint: haiku` → Agent tool with `model: "haiku"`
- `Model-hint: missing` → use Bash → `llm-route.sh qwen` (defensive — validation should prevent this)

**Route 3 — Validation (pass/fail judges):**
- All validators: Bash → `llm-route.sh gemma` first (fastest free, ~70s)
- Fallback to subscription haiku only if gemma fails or returns empty output

**CRO research failure retry:**
- Retry with `llm-route.sh qwen` (free, 1M context). If qwen also fails → escalate to sonnet as last resort.

**Optional task flags** — check before routing:

If the task contains these flags, log them in the running message:
- `speed-critical: true` → Executor has hard time constraint; model-hint already respects this
- `large-context: true` → Executor needs to process 50K+ tokens; model-hint already respects this

Example notification to Discord:
```
▶ TASK-100 — Analyze user patterns [speed-critical] `running`
```

Flags do NOT change routing — they are author's constraints that the Model-hint derivation already respects. Log them for visibility only.

Each subagent receives this prompt:

```
OMS work task ([task-id]): [spec]

Acceptance criteria:
- [criterion]
- [criterion]

Context files: [comma-separated paths]

Working directory: [worktree_path]
ALL file reads and edits MUST use absolute paths under [worktree_path].
Never read or edit files outside [worktree_path]. If a context file path does not start
with [worktree_path], prepend [worktree_path] to it before reading.

Instructions:
1. Read context files from [worktree_path].
2. Complete the task fully. For impl: make all file changes. For research: write findings to logs/research/[task-id].md.
3. Run package installs if the task requires them. Do NOT re-run builds or installs to verify — make your changes, run installs once if needed, then stop.
4. Run validation chain: [agent → agent → agent]
   For each validator, use their role below to assess the output:
   - dev: correctness, completeness, code quality. Always run: `git ls-files | grep -E "node_modules|coverage|\.next|dist/|\.env$"` — any results = FAIL (IQ1). Not scaffold-specific; runs on every task.
   - qa: each acceptance criterion — pass or fail? Also verify: `git status --short` shows only source files — no build artifacts, no dependency dirs. For any task that adds or changes a user-facing flow: confirm an E2E spec exists under `e2e/<flow>.spec.ts` and passes (`pnpm exec playwright test`). Missing E2E for a UI/flow task = FAIL. For any task that removes or replaces a component: run `grep -rl 'data-testid' e2e/` and check that no remaining spec references a testid belonging to the removed component — stale specs that would fail CI = FAIL.
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
   rows.append({
       'task_id': record['task_id'], 'slug': record['slug'], 'title': record['title'],
       'date': record['date'], 'passed': record['passed'], 'fail_at': record['fail_at'],
       'cost_usd': None, 'validators': record['validators'],
       'milestone': record['milestone'], 'type': record['type'],
       'first_pass': None, 'notes': record['notes'],
   })
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

## Step 3.5 — Visual QA (automated via E2E screenshots)

Visual QA runs automatically as part of the E2E suite (Step 3.6 milestone gate). No separate browse session needed.

**Primary path (both SKILL and Python/Discord):**
E2E specs call `page.screenshot()` at each key state and save to `qa/screenshots/<flow>-<state>.png`.
Milestone gate posts these to the Discord milestone thread automatically. CEO sees visual proof without any manual step.

**Browse QA (SKILL path only, use only when E2E coverage is insufficient):**
If a UI route is not covered by E2E specs yet, run a single browse session:
1. Navigate to the route
2. Screenshot: `qa/screenshots/TASK-NNN-<criterion>.png`
3. Check: renders without error, no console errors, layout matches spec
4. Fix inline if issue found (max 2 cycles), then re-screenshot
5. Close session

**Cost:** Browse adds ~20K tokens. Skip if E2E screenshots already cover the route.

---

## Step 3.6 — Milestone Gate (every milestone, both paths)

After all tasks are done, run the milestone gate before the CEO brief. This is an integration check — confirms all merged changes work together on main, not just in isolated worktrees.

**What runs:**
1. All unique `Verify:` commands from completed tasks (unit tests, lint, type checks)
2. Full E2E suite — if `playwright.config.ts` exists, runs automatically
3. All against main branch post-merge

**If all pass:** update `product-direction.ctx.md` (see below), then proceed to Step 4 (Final Report) and Step 5 (CEO Brief).
**If any fail:** do NOT run CEO brief. Post failure to milestone thread. Fix and re-run.

**Milestone completion — update `product-direction.ctx.md` (mandatory, always):**
After milestone gate passes, before Step 4:
1. Move the completed milestone from `## Active Milestone` to `## Completed Milestones` with `✅ Complete [date] | [N]/[N] tasks`
2. Set the next planned milestone (from `## Next Milestone`) as the new `## Active Milestone` — or write `## Active Milestone\nNone — run /oms-exec to plan next milestone` if none planned
3. Clear the `## Current Priorities` section — it belongs to the new milestone, not the old one
4. Commit the ctx update as part of the milestone gate commit

This step has no exception. A milestone that passes gate but whose ctx is not updated is incomplete.

**Python/Discord path:** `run_milestone_gate()` in `oms-work.py` handles this automatically when `--all` is used. No action needed here.

**SKILL path (here):** run manually with Bash tool:
```bash
# unit/verify checks — use Verify: fields if present; fallback if tasks predate the field:
~/.claude/bin/ctx-exec "failing tests" pnpm test
~/.claude/bin/ctx-exec "type error" npx tsc --noEmit
~/.claude/bin/ctx-exec "lint error" pnpm run lint
# E2E (if playwright configured)
pnpm exec playwright test  # or npx/bunx
```

**Verify field fallback:** if completed tasks have no `Verify:` field (pre-schema tasks), run the three fallback commands above. All Verify commands and fallbacks MUST be wrapped in ctx-exec — the PreToolUse hook blocks unwrapped test/build/tsc/lint commands.

**After E2E passes — post grouped visual QA report to Discord (SKILL path, mandatory):**

Build a `groups` list by reading the E2E spec files under `e2e/` — for each spec, extract the `test.describe` block names and map them to screenshots. Each group should have:
- `title`: human-readable flow name (e.g. "Home Entry", "Questionnaire Flow")
- `description`: one-line summary of the E2E scenarios covered (from the spec's describe blocks)
- `paths`: list of `qa/screenshots/<flow>-*.png` files that belong to that flow

```bash
python3 -c "
import sys; sys.path.insert(0, '$HOME/.claude/bin')
import oms_discord as d, json, re
from pathlib import Path

cfg = json.loads(Path('$HOME/.claude/oms-config.json').read_text())
proj = cfg['projects']['PROJECT_SLUG']
tf = Path(proj['path']) / '.claude/oms-work-threads.json'
qa = Path('qa/screenshots')
if not qa.exists():
    print('No qa/screenshots dir')
    exit(0)

# Group screenshots by filename prefix (part before second dash segment)
# e.g. home-entry-initial.png → prefix 'home-entry'
from collections import defaultdict
groups_map = defaultdict(list)
for p in sorted(qa.glob('*.png')):
    if p.stem.startswith('TASK-'):
        continue
    parts = p.stem.split('-')
    # Use first two segments as prefix key, or first if single-word
    prefix = '-'.join(parts[:2]) if len(parts) > 2 else parts[0]
    groups_map[prefix].append(p)

# Build group dicts — read describe block names from matching e2e spec
FLOW_META = FLOW_META_PLACEHOLDER  # replaced below with actual values
groups = []
for prefix, paths in groups_map.items():
    meta = FLOW_META.get(prefix, {})
    groups.append({
        'title': meta.get('title', prefix.replace('-', ' ').title()),
        'description': meta.get('description', 'E2E coverage'),
        'paths': paths,
    })

d.post_visual_qa_report(proj['channel_id'], tf, 'MILESTONE_NAME', groups)
print(f'Posted {sum(len(g[\"paths\"]) for g in groups)} screenshots in {len(groups)} groups')
"
```

Before running: replace `FLOW_META_PLACEHOLDER` with a Python dict mapping prefix → `{title, description}` derived from reading `e2e/*.spec.ts` describe blocks. Example:
```python
{
    'home-entry':    {'title': 'Home Entry',         'description': 'initial render + validation error on empty submit'},
    'questionnaire': {'title': 'Questionnaire Flow', 'description': 'loaded, turn progression, empty state, API error'},
    'confirm':       {'title': 'Confirm → Output',   'description': 'loaded, empty state, error, successful navigation to output'},
    'sim-panel':     {'title': 'Simulation Panel',   'description': 'hidden by default, expand/collapse, error state, long input'},
    'rate-limit':    {'title': 'Rate Limit UX',      'description': 'absent (normal flow), output page under rate limit'},
    'happy-path':    {'title': 'Full Happy Path',    'description': 'home → questionnaire → confirm → output end-to-end'},
}
```

Replace `MILESTONE_NAME` and `PROJECT_SLUG` with actual values. This is a required step — if no screenshots exist, it means `page.screenshot()` calls are missing from the specs.

**HARD GATE — archive is blocked until Discord post confirms success:**
The `post_visual_qa_report` call above must print `Posted N screenshots in N groups` before the archive step runs. If it prints nothing, errors, or posts 0 screenshots — STOP. Fix the post first. Never run the archive command if the post did not succeed. This order is non-negotiable: Discord post → archive. Never archive → post.

**After posting confirms success — archive screenshots and delete browse QA evidence (mandatory):**
```bash
python3 -c "
import shutil, os
from pathlib import Path
milestone = 'MILESTONE_NAME'
src = Path('qa/screenshots')
if not src.exists():
    print('No qa/screenshots dir — nothing to archive')
    exit(0)
# Archive E2E flow screenshots to qa/milestones/<milestone>/
dest = Path('qa/milestones') / milestone
dest.mkdir(parents=True, exist_ok=True)
flow_shots = [p for p in src.glob('*.png') if not p.stem.startswith('TASK-')]
for p in flow_shots:
    shutil.move(str(p), str(dest / p.name))
# Delete browse QA evidence (TASK-NNN-*.png)
for p in src.glob('TASK-*.png'):
    p.unlink()
print(f'Archived {len(flow_shots)} screenshots to qa/milestones/{milestone}/')
print(f'qa/screenshots/ is now clear')
"
```
Replace `MILESTONE_NAME` with the actual milestone name. This step ensures `qa/screenshots/` is empty for the next milestone and browse QA evidence (TASK-NNN-*.png) is not accumulated. Archived flow screenshots are committed to git under `qa/milestones/`.

**Discord posts automatically:**
- Pass: `✅ Milestone gate [milestone] — unit + E2E pass`
- Fail: `⚠️ Milestone gate [milestone] — N check(s) failed on main` with tail output

**Visual QA** (Step 3.5) is the only check that stays SKILL-only — it requires browse screenshots and cannot run as a subprocess.

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
