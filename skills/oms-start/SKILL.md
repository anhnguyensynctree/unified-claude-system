---
name: oms-start
description: Initialize OMS for a project. Ingests any starting material (idea, PRD, CLAUDE.md, raw notes), asks scope, runs departmental intake, and generates all project ctx files.
---
# Skill: oms-start

Bootstraps OMS for the current project. Accepts any starting material — raw idea, PRD, CLAUDE.md, research notes, or URL summary. Generates all ctx files needed for OMS to run. Run once per project, or re-run on major pivot.

## When to Use
- First time using `/oms` in a project
- Major pivot or scope change
- Adding a new department to an existing project
- CEO wants to update company belief or product direction

## Bot Mode (OMS_BOT=1) — READ THIS FIRST

> **If `OMS_BOT=1` is set OR this is a `claude --print` session: skip ALL interactive steps. Execute rules below immediately before reading anything else.**

- **Write files now** — `--dangerously-skip-permissions` is active; all writes are pre-approved
- **Zero questions** — answer everything from files on disk (`README.md`, `IDEA.md`, `CLAUDE.md`, `package.json`, etc.)
- **Zero permission text** — never output "I need write access", "please approve", "grant permission", or any approval request
- **Zero confirmations** — do not ask to proceed, do not summarize what you're about to do, just do it
- **Scope detection** — reason about what expertise the project genuinely needs, don't pattern-match keywords. Ask: does this product depend on domain knowledge outside software engineering? Does it handle regulated data or operate in a regulated industry? Does it have a revenue model or financial product dimension? Activate Research, Legal, or Finance only when the answer is clearly yes. Examples: game → Engineering only (unless it involves behavioral psychology or monetization); personal finance app → Engineering + Finance + Legal; astrology/personality app → Engineering + Research; healthcare → Engineering + Research + Legal.
- **Roster detection** — standard engineering roster is a default, not a ceiling. Reason about whether the project needs specialists beyond cto, product-manager, backend-developer, frontend-developer, engineering-manager, qa-engineer. A game needs a game-designer. An ML product needs an ml-engineer. A mobile-first product needs a mobile-developer. Add only what's genuinely recurring across tasks, not one-off.
- **Placeholders for unknowns**: write `TBD — update via /oms-start` and continue
- **Single-pass output**: write all ctx files, then output exactly: `## OMS Update\n[one sentence: files written + active departments + any non-standard agents added]` — nothing else

---

## Step 1 — Check Existing Context

Look for `.claude/agents/company-belief.ctx.md` in the current project.

**If it exists**: read it and all other `.claude/agents/*.ctx.md` files. Present:
```
Found existing OMS context for [project]:
- company-belief: [one line summary]
- product-direction: [one line summary]
- active departments: [list from company-hierarchy.md]

Update it? (y/n) — or specify what changed: pivot / new department / product update
```
If no → skip to done.
If yes → determine what changed and jump to the relevant step.

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

## Step 3 — Present Analysis + Get CEO Alignment

In ONE message, show CEO the analysis and ask everything needed. Format:

```
Here's what I understand so far:
[2-3 sentence summary of what they're building and for whom]

Recommended scope: [departments] — [one sentence reasoning]
Non-standard agents needed: [list with one-line rationale each, or "none"]

Before I generate ctx files, I need answers to [N] open questions:

**Must answer (changes the architecture):**
1. [question]
2. [question]

**Good to answer (improves ctx quality):**
3. [question]

Confirm scope + answer any questions — or just say "looks right, go" to proceed with defaults.
```

CEO replies. If they say "go" or confirm: proceed to Step 4 with defaults for unanswered questions.
If they answer questions: incorporate answers, then proceed.

**Rules:**
- Max 5 questions total — ruthlessly cut anything that has a sensible default
- Never ask about things already stated in the idea
- Scope and roster proposals go here, not in a separate step
- In Bot Mode: skip entirely — use analysis results silently, write files with TBD for unknowns

## Step 4 — Departmental Intake (parallel)

Based on scope answer, run intake questions from each active department's lead. Present ALL questions in ONE message — CEO answers everything at once.

**Engineering (always — asked by CTO perspective):**
1. What are you building? (one sentence — core function)
2. Who is it for? (target user and their primary need)
3. Tech stack? (frameworks, database, AI services, deployment)
4. Current phase? (idea / prototype / MVP / live / scaling)
5. Biggest technical constraint right now?
6. What is explicitly out of scope?

**Domain specialist detection** (auto — no question needed, infer from stack + answers):
- Vercel detected (deployment answer or `vercel.json` / `next.config.js` present) → write `"deploy": "vercel"` to oms-config.json project entry, and add to `cto.ctx.md` under `## Deploy`
- iOS / React Native / Expo detected → write `"mobile": "ios"` to oms-config.json project entry; note in `cto.ctx.md` that mobile testing requires simulator or device
- GitHub Actions detected (`/.github/workflows/` exists) → note in `cto.ctx.md` under `## CI`; no separate Discord channel needed — engineering handles it
- Supabase detected → add to `backend-developer.ctx.md` under `## Database`

**Research (if active — asked by CRO perspective):**
7. What domains of knowledge does this product depend on? (e.g., behavioral psychology, content strategy, linguistics)
8. What is the core research question the product is trying to answer about its users?
9. Are there known risks to user wellbeing or safety that research should monitor?
10. Which of these researcher types are relevant? (human behavior, data intelligence, content/platform, clinical safety, language/communication, philosophy/ethics, cultural/historical, biological/evolutionary)

**Legal (if active — asked by CLO perspective):**
11. What jurisdictions will users be in? (affects privacy law)
12. Does the product collect personal data? If so, what kind?
13. What platforms will you distribute on? (App Store, YouTube, etc.)
14. Any known IP, licensing, or content rights considerations?

**Finance (if active — asked by CFO perspective):**
15. What is the revenue model? (subscription, ads, one-time, freemium, etc.)
16. What are the primary cost drivers? (API calls, infrastructure, content production)
17. What financial milestone would trigger a CEO milestone report?

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

Run /oms <task> to start.
Run /oms exec for a strategic C-suite discussion.
Run /oms-start again if the project pivots or a new department is needed.
```

## Rules
- **Never write to `~/.claude/agents/`** — all files go to the current project's `.claude/agents/`
- **Never write `company-direction.ctx.md`** — it is now `company-belief.ctx.md`
- **Never write `project-roster.md`** — it is now `company-hierarchy.md`
- If `.claude/agents/` does not exist: create it
- ctx.md files are living documents — no line cap, they grow as OMS learns the project
- `ceo-decisions.ctx.md` is append-only — never rewrite, only add entries
- `company-belief.ctx.md` and `product-direction.ctx.md` start dense (under 40 lines) but grow over time
- Do not generate files for inactive departments
