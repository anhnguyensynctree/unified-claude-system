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

Summarise what was ingested in one sentence before proceeding.

## Step 3 — Scope Declaration

Ask ONE question. Present as a numbered list:

```
What departments are active in this project?

[1] Engineering only — software product, no research dimension
[2] Engineering + Research — requires domain expert knowledge (behavioral science, content strategy, platform research, etc.)
[3] Engineering + Research + Legal — has compliance, privacy, or platform ToS exposure
[4] All departments — Engineering, Research, Legal, Finance
[5] Custom — describe which departments

Note: Engineering is always included. Legal and Finance can be added to any combination.
```

CEO answers with a number or description. Router enforces activation from this point.

## Step 4 — Departmental Intake (parallel)

Based on scope answer, run intake questions from each active department's lead. Present ALL questions in ONE message — CEO answers everything at once.

**Engineering (always — asked by CTO perspective):**
1. What are you building? (one sentence — core function)
2. Who is it for? (target user and their primary need)
3. Tech stack? (frameworks, database, AI services, deployment)
4. Current phase? (idea / prototype / MVP / live / scaling)
5. Biggest technical constraint right now?
6. What is explicitly out of scope?

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

### Generate only if engineering ctx makes sense (project has a meaningful stack):

**`cto.ctx.md`**, **`backend-developer.ctx.md`**, **`frontend-developer.ctx.md`** — brief project-specific context per agent, max 10 lines each.

## Step 6 — Confirm

Tell CEO:
```
OMS initialized for [project name].

Files written to .claude/agents/:
[list files written]

Active departments: [list]
[If research] Rostered researchers: [list agent names]

Run /oms <task> to start.
Run /oms exec for a strategic C-suite discussion.
Run /oms-start again if the project pivots or a new department is needed.
```

## Rules
- **Never write to `~/.claude/agents/`** — all files go to the current project's `.claude/agents/`
- **Never write `company-direction.ctx.md`** — it is now `company-belief.ctx.md`
- **Never write `project-roster.md`** — it is now `company-hierarchy.md`
- If `.claude/agents/` does not exist: create it
- Keep all generated files under 40 lines — dense and scannable
- Do not generate files for inactive departments
