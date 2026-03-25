# OMS + OMS-Work — System Overview

Two separate loops. OMS decides. OMS-Work executes.
They share one artifact: `[project]/.claude/cleared-queue.md`

---

## Context Diagram

```
╔══════════════════════════════════════════════════════════════════╗
║  OMS DAILY SESSION  (CEO present — interactive)                  ║
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
║              Artifacts · Produces · Verify · Context             ║
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
║      status: done | branch ready to merge                        ║
║                                                                  ║
║  7b. FAIL → log spec lesson (if spec-related)                    ║
║             leave worktree open for review                       ║
║             status: cto-stop                                     ║
║             dependent tasks: blocked                             ║
║             other tasks: continue                                ║
╚══════════════════════════════════════════════════════════════════╝
         │                              │
         ▼                              ▼
  done branches                   cto-stop branches
  merge manually                  review at next OMS session
                                  → re-spec → new TASK-NNN
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

## What Changed This Session

### Task Schema — `cleared-queue.md` format

| Field | Before | After |
|---|---|---|
| `Spec:` | 1–3 sentence prose | `The system SHALL [verb] [object] so that [outcome].` |
| `Acceptance:` | pipe-separated text | Renamed to `Scenarios:` — `GIVEN/WHEN/THEN` per scenario |
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
