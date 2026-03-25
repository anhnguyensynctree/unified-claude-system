# OMS + OMS-Work — System Overview

Two separate loops. OMS decides. OMS-Work executes.
They share one artifact: `[project]/.claude/cleared-queue.md`

---

## Context Diagram

```
╔══════════════════════════════════════════════════════════════════╗
║  OMS DAILY SESSION  (CEO present — interactive)                  ║
║                                                                  ║
║  Step 0    First-Run Check                                       ║
║            → router.ctx.md missing → run /oms discover          ║
║            → company-belief.ctx.md missing → run /oms-start     ║
║                                                                  ║
║  Step 1    Router (Haiku)                                        ║
║            → tier, activated agents, briefings                   ║
║  Step 1.5  Path Diversity (Tier 2+)                              ║
║  Step 2    Round 1 — agents in parallel (blind NGT)              ║
║  Step 3    Rounds 2+ — Pre-Facilitator → Facilitator (Tier 2+)   ║
║  Step 3.5  CEO Gate → C-suite blind NGT if triggered             ║
║  Step 4    Synthesizer (Sonnet/Opus)                             ║
║            → decision, rationale, dissent                        ║
║            → action_items[] with:                                ║
║               type | infra_critical | depends_on | chain_type    ║
║  Step 5    Log → logs/tasks/[date-slug].md                       ║
║  Step 6    Trainer                                               ║
║            → scores discussion quality                           ║
║            → scores task spec quality (SHALL/scenarios/          ║
║               artifacts/produces) → task-elaboration/lessons.md  ║
║  Step 7    Context Optimizer                                     ║
║  Step 8    CEO feedback                                          ║
║                                                                  ║
║  Step 8.5  Queue Commit ──────────────────────────────────────── ║
║                                                                  ║
║   1. Classify                                                    ║
║      executable → proceed                                        ║
║      strategic  → ceo-decisions.ctx.md, stop                     ║
║                                                                  ║
║   2. Chain pre-check (if depends_on non-empty)                   ║
║      chain_type: value_substitution → both tasks elaborate       ║
║      chain_type: direction_selection → research only;            ║
║                  impl held until CEO reviews findings             ║
║                                                                  ║
║   3. Elaborate  (Task Elaboration Agent — Sonnet)                ║
║      Spec Exploration checklist (5 questions)                    ║
║      Loads task-elaboration/lessons.md first                     ║
║      Drafts: Spec(SHALL) · Scenarios(GIVEN/WHEN/THEN)            ║
║              Feature · Artifacts · Produces · Verify · Context   ║
║      Produces→Context wiring for chained tasks                   ║
║                                                                  ║
║   4. Review (one reviewer per task, in parallel)                 ║
║      impl + infra_critical → CTO                                 ║
║      research → CPO  (CTO if feeds infra-critical downstream)    ║
║      impl standard → EM                                          ║
║      CLO/CFO override if activated in discussion                 ║
║      APPROVE or REWORK (re-draft once, else surface to CEO)      ║
║                                                                  ║
║   5. Queue Gate (8 checks)                                       ║
║      SHALL · no forward-reference · GIVEN/WHEN/THEN              ║
║      Artifacts · Produces · Context exists · no cross-task       ║
║      decisions · one-session scope                               ║
║                                                                  ║
║   6. Write → cleared-queue.md                                    ║
╚══════════════════════════════════════════════════════════════════╝
                          │
                          │  cleared-queue.md
                          ▼
╔══════════════════════════════════════════════════════════════════╗
║  OMS-WORK  (no CEO — passive, autonomous)                        ║
║  Trigger: /oms-work in Discord · CLI: oms-work.py <slug>         ║
║                                                                  ║
║  1. Parse queue → find ready tasks (Depends resolved)            ║
║     --all: loops all ready tasks                                 ║
║     TASK-NNN: run specific task                                  ║
║                                                                  ║
║  2. git worktree add                                             ║
║     branch: oms-work/task-nnn                                    ║
║     path:   .claude/worktrees/TASK-NNN                           ║
║                                                                  ║
║  3. exec_prompt (Sonnet)                                         ║
║     Context files inlined — no cold reads                        ║
║     Spec + Scenarios + Artifacts + Produces in prompt            ║
║     "Make all changes to satisfy every scenario"                 ║
║                                                                  ║
║  4. Hallucination guard                                          ║
║     git status --porcelain → empty on impl = CTO-STOP            ║
║                                                                  ║
║  5. Validation chain (Haiku per step)                            ║
║     research    →  researcher → cro → cpo                        ║
║     engineering →  dev → qa → em                                 ║
║     infra       →  dev → cto                                     ║
║     Each validator sees: Spec + Scenarios + Artifacts + summary  ║
║                                                                  ║
║  6. Shell verify                                                 ║
║     Runs Verify: commands — exit code 0 = pass                   ║
║     Deterministic; no LLM judgment                               ║
║                                                                  ║
║  7a. PASS → commit worktree → remove worktree                    ║
║      → auto-merge to main (--no-ff)                              ║
║      → delete branch                                             ║
║      → Discord: ✓ TASK-NNN done (feature thread or main)        ║
║                                                                  ║
║  7b. FAIL → log spec lesson (if spec-related)                    ║
║             leave worktree open for review                       ║
║             → Discord: ⚑ TASK-NNN cto-stop (with reason)        ║
║             dependent tasks: blocked                             ║
║             other tasks: continue                                ║
╚══════════════════════════════════════════════════════════════════╝
         │                              │
         ▼                              ▼
  done branches                   cto-stop branches
  merged to main                  review at next OMS session
  automatically                   → re-spec → new TASK-NNN
         │
         ▼
╔══════════════════════════════════════════════════════════════════╗
║  TRAINING LOOP  (improves spec quality over time)                ║
║                                                                  ║
║  Source 1 — Trainer (Step 6, every session)                      ║
║    Scores new tasks: SHALL clarity · scenario completeness       ║
║    artifact precision · produces usability (1–5 each)           ║
║    Score ≤ 2 → lesson written to task-elaboration/lessons.md     ║
║                                                                  ║
║  Source 2 — oms-work (on validation fail)                        ║
║    Checks reason for spec signals: "ambiguous", "edge case"...   ║
║    Match → lesson appended to task-elaboration/lessons.md        ║
║                                                                  ║
║  Next session: Elaboration agent loads lessons.md first          ║
║  → past failures prevent same spec errors                        ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Project Initialization — /oms-start

Run once per project before the first `/oms` session.

```
/oms-start
```

What it does:
1. Asks: project name, type (app/service/research), target users, north-star metric
2. Reads any supplied material: PRD, CLAUDE.md, raw notes, links
3. Runs departmental intake: CTO (architecture constraints), CPO (product direction), CLO (legal/compliance), CFO (financial model)
4. Generates all project ctx files:
   - `.claude/agents/company-belief.ctx.md` — why this exists, core assumptions
   - `.claude/agents/product-direction.ctx.md` — milestones, priorities, success criteria
   - `.claude/agents/architecture.ctx.md` — tech stack, constraints, patterns
   - `.claude/agents/tech-stack.ctx.md` — languages, frameworks, dependencies
   - `.claude/agents/ceo-mandate.ctx.md` — non-negotiables, hard constraints
   - `.claude/agents/ceo-decisions.ctx.md` — strategic items pending CEO decision
5. Creates `cleared-queue.md` (empty, ready for tasks)
6. Writes `router.ctx.md` (marks initialization complete)

After `/oms-start`: every subsequent `/oms <task>` in this project proceeds without the bootstrap step.

---

## Day-to-Day Workflow

### Running a session

```bash
/oms <task>          # in the project directory — runs a full discussion session
```

OMS checks `company-belief.ctx.md` first. If missing → tells CEO to run `/oms-start` and stops.

The Router determines tier (0–3) based on task complexity, domain count, and reversibility.
Tier drives: how many agents activate, how many rounds, whether C-suite gates fire.

### Surfacing questions to CEO

CEO Gate (Step 3.5) fires when:
- A domain agent raises a blocking constraint with no clear resolution
- CLO flags a legal risk at `high` or `critical`
- Agents disagree on an irreversible architectural choice

Phase 1 (Haiku): classifies whether CEO input is genuinely required.
Phase 2 (if triggered): C-suite NGT round → inject constraint if resolved, else → CEO Brief + PAUSE.

When OMS pauses for CEO input, it posts the question to Discord and waits.
CEO replies in Discord → bot injects into pipeline → discussion resumes from Step 4.

### When CEO has no questions

OMS proceeds directly to Synthesis (Step 4) → Step 8.5 Queue Commit.
Action items are elaborated, reviewed, gate-checked, and written to `cleared-queue.md`.
No CEO interaction needed beyond the initial task statement.

### Generating a task or feature list without a question

```bash
/oms roadmap for [feature or milestone]
```

Runs at Tier 1–2 with CPO + CTO. Synthesis produces action_items[]. Step 8.5 queues them all.
CEO sees: `Queue Commit: X tasks queued. Queued: TASK-001 — title, TASK-002 — title`

---

## OMS-Work — Autonomous Execution

### CLI trigger (terminal — leave your Mac and walk away)

```bash
python3 ~/.claude/bin/oms-work.py <project-slug> --all
```

Loops all ready tasks in dependency order. Posts to Discord on every task completion.
Terminal output also shows progress. Safe to run overnight.

```bash
python3 ~/.claude/bin/oms-work.py <project-slug> TASK-003   # run one specific task
python3 ~/.claude/bin/oms-work.py <project-slug> --dry-run  # show plan, no execution
```

### Discord trigger

```
!oms-work <project-slug>
!oms-work <project-slug> --all
!oms-work <project-slug> TASK-003
```

Both triggers post to Discord identically. The Discord bot does not need to be the trigger
for Discord notifications to appear — oms-work.py handles Discord directly via `oms_discord.py`.

---

## Discord Notification Model

### Feature threads

Each task has a `Feature:` field. All tasks in the same feature share one Discord thread.

```
#project-channel
├── Thread: Feature: auth-revamp
│     ✓ TASK-001 — JWT refresh rotation  done
│     ✓ TASK-002 — Token family revoke   done
│     ⚑ TASK-003 — Redis session store  cto-stop
│                  > FAIL (cto): SessionStore interface not exported
│
└── Thread: Feature: re-engagement
      ✓ TASK-004 — Research notification timing  done
      ✓ TASK-005 — Push notification impl        done
```

Tasks with `Feature: none` post directly to the main project channel (no thread).

### What CEO sees

- One message per task: `✓ TASK-NNN — title  done` or `⚑ TASK-NNN — title  cto-stop`
- On `cto-stop`: the failure reason is appended (max 180 chars)
- No step-by-step updates, no intermediate logs, no validator names
- At the end of a `--all` run: nothing extra — the individual task messages are the summary

### Thread persistence

Thread IDs are stored in `[project]/.claude/oms-work-threads.json`.
On next run, existing threads are reused. New features get a new thread created automatically.

---

## Merge Flow

```
worktree (oms-work/task-nnn) → all validators pass → shell verify pass
  → git commit in worktree
  → git worktree remove
  → git checkout main
  → git merge --no-ff oms-work/task-nnn -m "oms-work: TASK-NNN — title"
  → git branch -d oms-work/task-nnn
  → Discord: ✓ TASK-NNN done
```

Auto-merge fails gracefully in two cases:
- Working tree not clean → leaves branch open, posts `branch ready — merge manually`
- Merge conflict → runs `git merge --abort`, leaves branch open, posts `merge conflict, merge manually`

In both cases the task is still marked `done` in the queue (work passed validation).
The CEO merges manually at the next session.

---

## What Changed This Session

### Task Schema — `cleared-queue.md` format

| Field | Before | After |
|---|---|---|
| `Spec:` | 1–3 sentence prose | `The system SHALL [verb] [object] so that [outcome].` |
| `Acceptance:` | pipe-separated text | Renamed to `Scenarios:` — `GIVEN/WHEN/THEN` per scenario |
| `Feature:` | — | New: Discord thread grouping key |
| `Artifacts:` | — | New: `path/file — exports: x, y` — executor knows exactly what to produce |
| `Produces:` | — | New: downstream contract wired into dependent task's `Context:` |
| `Verify:` | — | New: shell commands run after agent chain (deterministic) |
| Queue gate | 5 checks | 8 checks — adds SHALL enforcement, forward-reference guard, Artifacts, Produces |

### oms-work.py execution

| Mechanism | Before | After |
|---|---|---|
| Context loading | `Read first: path/to/file` (cold reads) | Files inlined into prompt at execution time |
| Executor knows what to produce | Nothing — agent guesses | Artifacts field in prompt |
| Change detection | None | Hallucination guard: `git status --porcelain` empty = CTO-STOP |
| Verification | Agent chain only | Agent chain → shell verify (sequential) |
| Merge | Manual | Auto-merge to main after all validation passes |
| Discord | Only when triggered via Discord bot | Always — oms_discord.py posts regardless of trigger |
| Failure learning | Nothing logged | Spec-related failures → `task-elaboration/lessons.md` |

### Step 8.5 — Queue Commit pipeline

| Before | After |
|---|---|
| classify → queue gate → write | classify → chain pre-check → elaborate → review → queue gate → write |
| No intermediate artifacts | Spec Exploration checklist before every field |
| Reviewer inferred from text | Reviewer derived from `type` + `infra_critical` + activated C-suite |
| Chain type inferred at elaboration | `chain_type` set by Synthesizer during discussion |

### Synthesizer `action_items[]`

```
Before: { action, owner, priority }

After:  { action, owner, priority,
          type,           // impl | research
          infra_critical, // true only on impl, never research
          depends_on,     // upstream items this needs
          chain_type }    // value_substitution | direction_selection | null
```

### New components

| Component | Purpose |
|---|---|
| `agents/task-elaboration/persona.md` | Drafts full OpenSpec tasks; runs 5-question Spec Exploration checklist; loads lessons first |
| `agents/task-elaboration/lessons.md` | Accumulates spec failures from Trainer + oms-work; read each session |
| `bin/oms_discord.py` | Discord helper: create/find feature threads, post final task status |
| Trainer `task_spec_review` output | Scores 4 spec dimensions per task; writes lessons on weak scores |

---

## Task Types Reference

| Type | Validation chain | Reviewer | Scenarios test |
|---|---|---|---|
| `impl` standard | dev → qa → em | EM | System behavior (HTTP, state, output) |
| `impl` infra-critical | dev → cto | CTO | System behavior + irreversibility |
| `research` | researcher → cro → cpo | CPO | Output document quality |
| `research` → infra impl | researcher → cro → cpo | CTO | Output document quality |

## Chain Rule Reference

| chain_type | What it means | Action |
|---|---|---|
| `value_substitution` | Research fills in a value; impl is already decided | Both tasks queued with `Depends:` |
| `direction_selection` | Research could redirect or cancel the impl | Research only; impl held in `ceo-decisions.ctx.md` |
| `null` | No dependency | Single task, no chain |

## CLI Reference

| Command | What it does |
|---|---|
| `/oms-start` | Initialize a new project — generates all ctx files |
| `/oms <task>` | Run a full discussion session — produces action_items[] |
| `/oms exec` | C-suite strategic session (auto-triggered at milestones) |
| `/oms audit` | Force a full context optimizer audit |
| `/oms-implement` | Execute action_items[] directly (skips discussion) |
| `oms-work.py <slug>` | Run first ready task in project queue |
| `oms-work.py <slug> --all` | Run all ready tasks in order |
| `oms-work.py <slug> TASK-NNN` | Run one specific task |
| `oms-work.py <slug> --dry-run` | Show plan without executing |
