# oms-work — Execute Cleared Task Queue

Runs pre-cleared tasks from `[project]/.claude/cleared-queue.md`.
No CEO gate. Each task runs in an isolated git worktree. Validation chain runs per task.
One stop: `cto-stop` (branch left open, surfaces next daily session).

Schema: `~/.claude/agents/oms-work/task-schema.md`
Background trigger: send `!work` in any project Discord channel.

---

## Step 0 — Identify project

If `$ARGUMENTS` names a project slug, use it.
If run from inside a project directory (has `.claude/cleared-queue.md`), use that project.
If ambiguous, list projects from `~/.claude/oms-config.json` and ask.

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
3. Run validation chain: [agent → agent → agent]
   For each validator, use their role below to assess the output:
   - dev: correctness, completeness, code quality
   - qa: each acceptance criterion — pass or fail?
   - em: final approval — spec met, ready to merge?
   - researcher: methodology sound, findings complete?
   - cro: findings rigorous and actionable?
   - cpo: output creates clear product direction?
   - cto: architectural soundness, no blocking technical risk?
4. Output for each validator: "[validator]: PASS" or "[validator]: FAIL — [reason]"
5. Final line: "DONE — [1 sentence summary]" or "CTO-STOP — [validator]: [reason]"
```

---

## Step 3 — Process results

After each subagent returns:

**If DONE**:
- Commit all changes in the worktree: `git add -A && git commit -m "oms-work: TASK-NNN — title"`
- Remove the worktree (branch stays for merge): `git worktree remove --force .claude/worktrees/TASK-NNN`
- Update `cleared-queue.md`: Status: done, Notes: branch name

**If CTO-STOP**:
- Leave the worktree open — CTO or CEO reviews the branch directly
- Update `cleared-queue.md`: Status: cto-stop, Notes: stop reason + branch name
- Do NOT merge. Do NOT delete the worktree.

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

## Merge guidance (after /oms-work completes)

Done tasks have committed branches named `oms-work/task-nnn`.
To merge all done tasks into main:
```
git merge oms-work/task-001 oms-work/task-002 ...
```
Or review each branch first: `git diff main oms-work/task-001`

CTO-stop branches: do not merge. Resolve at next daily session, re-spec the task, re-queue.
