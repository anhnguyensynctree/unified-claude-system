---
name: oms-start
description: Initialize OMS for a project. Ingests any starting material (idea, PRD, CLAUDE.md, raw notes), asks scope, runs departmental intake, and generates all project ctx files.
---
# Skill: oms-start

Bootstraps OMS for the current project. Accepts any starting material — raw idea, PRD, CLAUDE.md, research notes, or URL summary. Generates all ctx files needed for OMS to run. Run once per project, or re-run on major pivot.

## When to Use
Primary entry point for all project-level OMS changes. Step 1 detects which mode to run — no need to decide upfront.

**Do NOT use** for single non-standard agent additions (approved via exec `roster_changes[]`) — those run via `/oms-work` directly. `/oms-start` is for department-level changes and above.

## Step 1 — Check Existing Context

Look for `.claude/agents/company-belief.ctx.md` in the current project.

**If it exists**: read it and all other `.claude/agents/*.ctx.md` files. Present:
```
Found existing OMS context for [project]:
- company-belief: [one line summary]
- product-direction: [one line summary]
- active departments: [list from company-hierarchy.md]

What changed? pivot / new department / product update — or "nothing" to exit.
```

Route by answer — do not ask again:
- `pivot` → re-run Steps 2, 2.5, 3, 3.5, 5 (full re-scope). Use when the product direction fundamentally changed — not for normal milestone planning (exec handles that). CEO-initiated, rare.
- `new department` → jump directly to Step 3. Output: "Department-add mode — running Step 3 and 3.5 only." Do not run Steps 2, 4, or 5.
- `product update` → re-run Step 5 only. Use when CEO brings new external material (new PRD, research doc, stakeholder brief) that wasn't generated through OMS and needs to be reflected in ctx files. Normal exec output updates ctx files directly — this is for external input only.
- `nothing` → exit

**If not**: continue to Step 2.

## Step 2 — Ingest Starting Material

Auto-read whatever exists in the current directory:
- `CLAUDE.md` → extract product description, stack, constraints
- `package.json` / `pyproject.toml` / `Cargo.toml` → extract tech stack
- Any file the CEO names: PRD, spec doc, research notes, README
- If CEO pastes raw text: accept it as-is

If nothing exists and CEO provides no material: ask for a one-paragraph description of what they are building. Accept anything — rough idea, vision, half-baked concept. Do not require polish.

## Step 2.5 — Internal Analysis (before talking to CEO)

After ingesting material, reason silently across four dimensions. Do NOT show this work — use it to drive Steps 3 and 4.

**What expertise does this project genuinely need?**
- What domain knowledge is required beyond software engineering?
- Does it handle personal, health, financial, or regulated data?
- Does it have a revenue model or financial product dimension?
- What type of engineers does it need beyond the standard six?

**What is unclear or underspecified?**
- List every assumption you had to make because the idea didn't say
- List every decision that would significantly change the architecture if answered differently
- List every risk (technical, legal, ethical, financial) that the idea didn't address

**What is the recommended scope?**
- Derive the department list from the expertise analysis, not from keywords
- Derive the non-standard agents needed (game-designer, ml-engineer, mobile-developer, etc.)

**What questions must CEO answer before ctx files can be accurate?**
- Prioritise: only surface questions where the answer changes what gets built or how
- Skip questions where a sensible default exists and can be stated

## Step 3 — Scope + Roster Confirmation (with agent gate)

In ONE message, show CEO the analysis and propose the roster. Format:

```
Here's what I understand so far:
[2-3 sentence summary of what they're building and for whom]

Recommended departments: [list] — [one sentence reasoning]

Standard roster: [list active standard agents]

Non-standard agents proposed:
- [agent-name] — [one-line domain rationale]
  CPO: [does this map to a product outcome? yes/no + reason]
  CTO: [knowledge gap requiring new agent, or ctx.md entry? + reason]
  → Recommend: create / defer to ctx.md

[or "None — standard roster covers this project"]

Confirm scope and roster — or say "go" to accept all recommendations.
```

CEO replies. "Go" or confirmation → proceed to Step 3.5. If CEO rejects a proposed agent → use ctx.md extension for that domain instead.

**Rules:**
- Max 3 non-standard agent proposals — if more are needed, prioritise by recurring need
- Never propose an agent where CTO says "ctx.md is sufficient"
- In Bot Mode: skip entirely — accept all recommended agents, proceed to Step 3.5

## Step 3.5 — Create Approved Non-Standard Agents

For each non-standard agent approved by CEO in Step 3:

1. Read `~/.claude/agents/engine/agent-creation-rules.md` — hard gate, no persona written until this is read
2. Write the persona file to `~/.claude/agents/[agent-name]/persona.md` following the required structure (Identity → Activation Condition → Primary Output → Non-Negotiables → Working Guidelines)
3. Create `~/.claude/agents/[agent-name]/MEMORY.md` (empty)
4. Create `~/.claude/agents/[agent-name]/lessons.md` (empty) — Trainer populates it organically after task cycles
5. Add the agent to `company-hierarchy.md` under the correct department

These agents are now live and will participate in Step 4's question round.

**Domain specialist detection** (auto — no CEO input needed):
- Vercel detected → write `"deploy": "vercel"` to oms-config.json, add to `cto.ctx.md` under `## Deploy`, disable deployment protection (`ssoProtection: null`) via Vercel API using token at `~/.config/vercel/key`
- iOS / React Native / Expo detected → write `"mobile": "ios"` to oms-config.json, note in `cto.ctx.md`
- GitHub Actions detected → note in `cto.ctx.md` under `## CI`
- Supabase detected → add to `backend-developer.ctx.md` under `## Database`

## Step 4 — Agent Question Round (parallel)

Run ALL active agents in parallel. Each agent reads `IDEA.md` (and any other material from Step 2) plus the scope summary from Step 3. Each agent produces:

1. **Domain summary** — 3–5 bullets: what they understand about the project from their domain
2. **Blocking questions** — questions where the answer changes what gets built or how (max 2 per agent)
3. **Clarifying questions** — questions that improve ctx quality but have sensible defaults (max 2 per agent)

After all agents return, Router deduplicates and groups:
- Questions covering the same ground → keep the sharpest version
- Questions with obvious defaults → move to clarifying or drop

Present to CEO in ONE message:

```
The team reviewed your idea. Here's what they need:

**Must answer — these change what gets built:**
[CTO] [question]
[CPO] [question]
[CLO] [question if legal active]

**Good to answer — improves direction and ctx quality:**
[Backend Dev] [question]
[Researcher] [question if research active]
[CFO] [question if finance active]

Answer any or all — say "go" to proceed with defaults for anything unanswered.
```

CEO answers → each agent's answers are routed back to the agent that asked. Proceed to Step 5.

**In Bot Mode:** skip question round — proceed to Step 5 with TBD for unknowns.

## Step 5 — Generate Ctx Files

Write all files to `.claude/agents/` in the current project. Create the directory if it does not exist.

### Always generate:

**`company-belief.ctx.md`** — stable company vision, changes rarely:
```markdown
# Company Belief — [Project Name]

## What We Are Building
[From Q1 — one sentence]

## Who It Is For
[From Q2 — target user and their need]

## Our Operating Belief
[Synthesized from all intake: the core bet the company is making about the world — what must be true for this product to succeed]

## Strategic Constraints
[From Q5, Q6 — what shapes every decision]

## Out of Scope
[From Q6 — what we are deliberately not doing]
```

**`product-direction.ctx.md`** — current state, updated by CPO after exec discussions:
```markdown
# Product Direction — [Project Name]

## Current Phase
[From Q4]

## Current Priorities
[Top 2–3 things being worked on right now]

## Next Milestone
[What constitutes the next meaningful checkpoint — what changes after it is reached]

## Decisions on Record
[Major product decisions made to date — appended by CPO after exec discussions]
```

**When proposing agents not in the standard roster**: read `~/.claude/agents/engine/agent-creation-rules.md` and run the C-suite narrowing gate (CPO → CTO → CEO) before adding any non-standard agent to the hierarchy. Never create a new persona file without CEO approval.

**`company-hierarchy.md`** — department structure and rostered agents:
```markdown
# Company Hierarchy — [Project Name]

## Active Departments
[List from scope declaration — always includes engineering]

## Engineering Dept
Standard roster: cto, product-manager, backend-developer, frontend-developer, engineering-manager, qa-engineer
All available by default for engineering tasks.

## Research Dept
[Only if research active]
### C-Suite
- chief-research-officer (always active when research dept is active)

### Rostered Researchers
[From Q10 — list the relevant researcher agents by name]

## Legal Dept
[Only if legal active]
- clo (singleton — covers all legal)

## Finance Dept
[Only if finance active]
- cfo (singleton — covers all finance)
```

### Generate only if research is active:

**`research.ctx.md`** — project-specific research context:
```markdown
# Research Context — [Project Name]

## Core Research Question
[From Q8]

## Key Domains
[From Q7]

## Safety Considerations
[From Q9 — null if none identified]

## Known Research Constraints
[What the team already knows vs. what must be discovered]
```

### Always generate:

**`ceo-decisions.ctx.md`** — append-only CEO decision log, starts empty:
```markdown
# CEO Decisions — [Project Name]

<!-- Append-only. Format: [date] | [decision] | [rationale] -->
```

### Generate only if engineering ctx makes sense (project has a meaningful stack):

**`cto.ctx.md`**, **`backend-developer.ctx.md`**, **`frontend-developer.ctx.md`** — project-specific context per agent. No line cap — these are living documents.

## Step 6 — Create Discord channel + register project

Check if `~/.claude/oms-config.json` exists (autonomous pipeline configured):

```bash
cat ~/.claude/oms-config.json 2>/dev/null
```

**If config exists:** create a Discord channel for this project and register it.

Derive slug from project directory name (lowercase, hyphens for spaces).
Check if slug already exists in config — if yes, skip channel creation.

Create the Discord channel via bot API:
```bash
python3 ~/.claude/bin/discord-create-channel.py "[slug]"
```

This script creates a text channel named `#[slug]` in the same server as `#oms-updates`,
writes the new channel_id to `oms-config.json` under `projects.[slug]`, and prints the channel ID.

After the channel is created, also set `auto_start: true` in the project entry so the heartbeat auto-starts the first task:
```python
# Read oms-config.json, set projects.[slug].auto_start = true, write back
import json, os
p = os.path.expanduser("~/.claude/oms-config.json")
cfg = json.load(open(p))
cfg["projects"].setdefault("[slug]", {})["auto_start"] = True
json.dump(cfg, open(p + ".tmp", "w"), indent=2); os.replace(p + ".tmp", p)
```

If script fails or pipeline not configured: tell CEO "Discord channel not created — run /init-oms to set up the pipeline first."

**If config does not exist:** skip silently.

## Step 7 — Confirm

Tell CEO:
```
OMS initialized for [project name].

Files written to .claude/agents/:
[list files written]

Active departments: [list]
[If research] Rostered researchers: [list agent names]
[If Discord configured] Discord: #[slug] channel created — autonomous OMS ready

Running /oms-exec now to select the first milestone and draft initial features...
```

## Step 8 — Auto-trigger /oms-exec

Immediately after Step 7 output, run `/oms-exec` without waiting for CEO input.

The C-suite picks the first milestone from `product-direction.ctx.md`, drafts FEATURE blocks, and appends them to `cleared-queue.md`. This completes the initialization chain — by the end of Step 8, the project has a direction, a milestone, and tasks ready to elaborate.

**In Bot Mode:** write checkpoint `{"next": "exec", "project": "[slug]"}` to `.claude/oms-checkpoint.json` and output `## OMS Update\noms-start complete — exec queued` instead of running exec inline.

**Rules:**
- Do not ask CEO "shall I run exec?" — just run it
- If exec fails or produces no features: tell CEO and suggest running `/oms-exec` manually
- After exec completes, the full summary (oms-start init + exec features) is shown together as the final output

## Infra Requirements — Auto-added for Web Projects

If the project is a web app (has a frontend, UI routes, or components), append these as mandatory tasks in milestone 1 before any feature work:

```
## TASK-infra-001 — CI/CD pipeline + Playwright E2E setup
- **Status:** queued
- **Milestone:** [milestone 1 name]
- **Type:** impl
- **Spec:** The project SHALL have GitHub Actions CI, Vercel deploy, Playwright E2E suite, and Lighthouse CI configured before any feature tasks run. CI runs Playwright on every PR for regression — it SHALL upload `qa/screenshots/` as a GitHub Actions artifact on failure for debugging. Screenshot posting to Discord is handled by the OMS milestone gate (`oms-work.py`) at end-of-milestone, not by CI. `qa/screenshots/` SHALL be in `.gitignore`.
- **Artifacts:** .github/workflows/ci.yml | playwright.config.ts | lighthouserc.json | e2e/ | .gitignore
- **Verify:** pnpm exec playwright test
- **Validation:** dev → cto → em
- **Model-hint:** sonnet
- **Depends:** none
```

This task must complete before any UI feature tasks are queued. oms-work enforces E2E coverage from the first milestone — no backfilling needed later.

## Rules
- **Never write to `~/.claude/agents/`** — all files go to the current project's `.claude/agents/`
- **Never write `company-direction.ctx.md`** — it is now `company-belief.ctx.md`
- **Never write `project-roster.md`** — it is now `company-hierarchy.md`
- If `.claude/agents/` does not exist: create it
- ctx.md files are living documents — no line cap, they grow as OMS learns the project
- `ceo-decisions.ctx.md` is append-only — never rewrite, only add entries
- `company-belief.ctx.md` and `product-direction.ctx.md` start dense (under 40 lines) but grow over time
- Do not generate files for inactive departments
