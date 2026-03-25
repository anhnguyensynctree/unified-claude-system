# OMS + OMS-Work — System Overview v0.6

Two separate loops. OMS decides. OMS-Work executes.
They share one artifact: `[project]/.claude/cleared-queue.md`

Every task in the queue traces back through a three-level hierarchy:

```
Milestone          product-direction.ctx.md — named product goal with success criteria
    └── Action Item    Synthesizer output — concrete action advancing that milestone
              └── Task     cleared-queue.md — one-session unit with full OpenSpec
```

The Synthesizer enforces the link: every action_item must carry a `feature` field matching
a named milestone. The Elaboration Agent reads it verbatim — never invents a milestone name.

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
║            Reads: company-belief.ctx.md + product-direction.ctx.md
║            → decision, rationale, dissent                        ║
║            → action_items[], each tagged with:                   ║
║               feature (from product-direction milestones)        ║
║               type | infra_critical | depends_on | chain_type    ║
║  Step 5    Log → logs/tasks/[date-slug].md                       ║
║  Step 6    Trainer                                               ║
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
║      value_substitution → both tasks elaborate                   ║
║      direction_selection → research only; impl held              ║
║                                                                  ║
║   3. Elaborate  (Task Elaboration Agent — Sonnet)                ║
║      Loads task-elaboration/lessons.md first                     ║
║      Reads feature from Synthesizer output — never invents it    ║
║      Spec Exploration checklist (5 questions)                    ║
║      Drafts: Spec · Scenarios · Feature · Artifacts              ║
║              Produces · Verify · Context                         ║
║      Produces→Context wiring for chained tasks                   ║
║                                                                  ║
║   4. Review (one reviewer per task, in parallel)                 ║
║      impl + infra_critical → CTO                                 ║
║      research + feeds infra → CTO                                ║
║      research (standard) → CPO                                   ║
║      impl standard → EM                                          ║
║      CLO/CFO if activated in discussion                          ║
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
║  Trigger: Discord !oms-work · CLI: oms-work.py <slug>            ║
║  Always posts to Discord regardless of trigger.                  ║
║                                                                  ║
║  1. Parse queue → find ready tasks (Depends resolved)            ║
║     --all: loops all ready tasks in dependency order             ║
║     TASK-NNN: run specific task                                  ║
║                                                                  ║
║  2. git worktree add                                             ║
║     branch: oms-work/task-nnn                                    ║
║     path:   .claude/worktrees/TASK-NNN                           ║
║                                                                  ║
║  3. exec_prompt (Sonnet)                                         ║
║     Context files inlined — no cold reads                        ║
║     Spec + Scenarios + Artifacts + Produces in prompt            ║
║                                                                  ║
║  4. Hallucination guard                                          ║
║     git status --porcelain empty on impl = CTO-STOP              ║
║                                                                  ║
║  5. Validation chain (Haiku per step)                            ║
║     research    → researcher → cro → cpo                         ║
║     engineering → dev → qa → em                                  ║
║     infra       → dev → cto                                      ║
║                                                                  ║
║  6. Shell verify                                                 ║
║     Runs Verify: commands — exit code 0 = pass                   ║
║                                                                  ║
║  7a. PASS → commit → remove worktree                             ║
║      → auto-merge to main (--no-ff) → delete branch             ║
║      → Discord: ✓ TASK-NNN done (in feature thread)             ║
║                                                                  ║
║  7b. FAIL → spec lesson if reason matches signals                ║
║      → leave worktree open for review                            ║
║      → Discord: ⚑ TASK-NNN cto-stop (in feature thread)        ║
║      → dependent tasks blocked; other tasks continue            ║
╚══════════════════════════════════════════════════════════════════╝
         │                              │
         ▼                              ▼
  merged to main                  cto-stop branches
  automatically                   review at next OMS session
                                  → re-spec → new TASK-NNN
```

---

## Project Initialization — /oms-start

Run once per project before the first `/oms` session.

1. Asks: project name, type, target users, north-star metric
2. Reads supplied material: PRD, CLAUDE.md, raw notes
3. Runs departmental intake: CTO, CPO, CLO, CFO
4. Generates all project ctx files:
   - `company-belief.ctx.md` — why this exists, core assumptions
   - `product-direction.ctx.md` — **named milestones and features** — every future task Feature: field comes from here
   - `architecture.ctx.md` — tech stack, constraints, patterns
   - `tech-stack.ctx.md` — languages, frameworks, dependencies
   - `ceo-mandate.ctx.md` — non-negotiables, hard constraints
   - `ceo-decisions.ctx.md` — strategic items pending CEO decision
5. Creates `cleared-queue.md` (empty)
6. Writes `router.ctx.md` (marks init complete)

---

## Alignment: How Tasks Stay Tied to Product Direction

The alignment chain runs through every step:

```
product-direction.ctx.md          ← source of truth for milestones
         │
         ▼
Synthesizer (Step 4)              ← reads product-direction; tags each action_item
  action_item.feature = "auth-revamp"   with the exact milestone name
         │
         ▼
Task Elaboration Agent (Step 8.5) ← reads feature from action_item; writes Feature: verbatim
  Feature: auth-revamp                  never invents a name; flags if milestone unknown
         │
         ▼
cleared-queue.md                  ← every task has Feature: tied to product-direction
         │
         ▼
Discord feature thread            ← one thread per milestone; CEO sees progress per feature
  Thread: Feature: auth-revamp
    ✓ TASK-001 done
    ⚑ TASK-002 cto-stop
```

**If an action item doesn't map to any milestone in `product-direction.ctx.md`:**
- Synthesizer uses `feature: "none"` — rare, for truly standalone ops tasks
- This signals the CEO that the work is drifting from roadmap
- At the next session, CPO should either add the milestone or question the task

---

## Day-to-Day Workflow

### Running a session

```bash
/oms <task>    # in the project directory
/oms           # no task — triggers queue check then exec if queue empty
```

Step 0 always runs a queue check before accepting any task:

```
cto-stop tasks exist?
  → yes → brief CEO: "⚑ N tasks blocked: TASK-NNN, TASK-NNN. Re-spec or skip?"
           re-spec inline → new TASK-NNN queued → oms-work picks up next run

queue empty AND no task given?
  → auto-trigger exec session (CPO + CTO + CFO + CLO + PM)
  → PM reports milestone coverage gaps
  → C-suite agrees next sprint priorities
  → Step 8.5 queues next batch of tasks

otherwise → proceed with stated task
```

OMS checks `company-belief.ctx.md` first. Missing → tells CEO to run `/oms-start`.

### When CEO has no blocking questions

OMS proceeds directly to Synthesis → Step 8.5 Queue Commit → `cleared-queue.md`.
CEO sees: `Queue Commit: X tasks queued. Queued: TASK-001 — title, TASK-002 — title`

### When CEO Gate fires

OMS posts the question to Discord and pauses.
CEO replies → bot injects response → discussion resumes from Step 4.

### Exec session — always CPO + CTO + CFO + CLO

Fires when: milestone reached, queue empty (CEO runs /oms with no task), or Router
detects a cross-department decision.

| Agent | Exec responsibility |
|---|---|
| CPO | Milestone priorities, roadmap sequencing, what gets built next |
| CTO | Arch prerequisites, technical risk of prioritization order |
| CFO | Cost of sprint priorities, unit economics, budget constraints |
| CLO | Legal/compliance flags on upcoming milestones before they hit the queue |
| PM | Milestone health, gap analysis (milestones with no queued tasks), acceptance intent |
| CRO | Conditional — activates only when a research gap is blocking a milestone |

CFO and CLO must be in every exec session — sprint priorities have cost and legal implications
that are far cheaper to surface now than after tasks are elaborated and queued.

### Generating a feature list or roadmap breakdown

```bash
/oms roadmap for [feature or milestone]
```

Runs as an exec session. CPO + CTO + CFO + CLO always active. CRO if research gap blocking
a milestone. PM always active for milestone gap analysis.
Synthesis maps all action_items to milestones. Step 8.5 queues them all grouped by feature.

---

## OMS-Work — Autonomous Execution

### CLI (terminal — safe to leave running)

```bash
python3 ~/.claude/bin/oms-work.py <slug> --all       # all ready tasks
python3 ~/.claude/bin/oms-work.py <slug> TASK-003    # one specific task
python3 ~/.claude/bin/oms-work.py <slug> --dry-run   # show plan only
```

Loops tasks in dependency order. Posts to Discord on every outcome. Safe overnight.

### Discord trigger

```
!oms-work <slug>
!oms-work <slug> --all
!oms-work <slug> TASK-003
```

Both triggers post to Discord identically — `oms_discord.py` handles this directly,
not the bot. No double-posting. Token read from `~/.config/discord/token`.

---

## Discord Notification Model

One message per task. Grouped into feature threads from `product-direction.ctx.md`.

```
#project-channel
├── Thread: Feature: auth-revamp
│     ✓ TASK-001 — JWT refresh rotation  done
│     ⚑ TASK-002 — Redis session store  cto-stop
│                  > FAIL (cto): SessionStore interface not exported
│
└── Thread: Feature: re-engagement
      ✓ TASK-003 — Research notification timing  done
      ✓ TASK-004 — Push notification impl        done
```

Tasks with `Feature: none` post directly to the main channel (no thread).
Thread IDs persisted in `[project]/.claude/oms-work-threads.json` — reused across runs.

CEO sees only: `✓ done` or `⚑ cto-stop [reason]`. No step names, no validator names.

---

## Merge Flow

```
All validation + shell verify pass
  → git commit in worktree
  → git worktree remove
  → git merge --no-ff oms-work/task-nnn -m "oms-work: TASK-NNN — title"
  → git branch -d oms-work/task-nnn
  → Discord: ✓ TASK-NNN done
```

Auto-merge fails gracefully:
- Working tree not clean → leaves branch, posts `branch ready — merge manually`
- Merge conflict → `git merge --abort`, leaves branch, posts `merge conflict, merge manually`

Task is still `done` in queue — work passed. CEO merges the branch at next session.

---

## Task Types Reference

| Type | Validation chain | Reviewer | Scenarios test |
|---|---|---|---|
| `impl` standard | dev → qa → em | EM | System behavior (HTTP, state, output) |
| `impl` infra-critical | dev → cto | CTO | System behavior + irreversibility |
| `research` | researcher → cro → cpo | CPO | Output document quality |
| `research` → infra impl downstream | researcher → cro → cpo | CTO | Output document quality |

## Chain Rule Reference

| chain_type | What it means | Action |
|---|---|---|
| `value_substitution` | Research fills in a value; impl direction already decided | Both tasks queued with `Depends:` |
| `direction_selection` | Research could change or cancel the impl | Research only; impl held in `ceo-decisions.ctx.md` |
| `null` | No dependency | Single task |

## CLI Reference

| Command | What it does |
|---|---|
| `/oms-start` | Initialize a new project — generates all ctx files including product-direction milestones |
| `/oms <task>` | Full discussion session → action_items[] → queue commit |
| `/oms exec` | C-suite strategic session (auto-triggered at milestones) |
| `/oms audit` | Force full context optimizer audit |
| `oms-work.py <slug>` | Run first ready task |
| `oms-work.py <slug> --all` | Run all ready tasks in order |
| `oms-work.py <slug> TASK-NNN` | Run one specific task |
| `oms-work.py <slug> --dry-run` | Show plan without executing |
