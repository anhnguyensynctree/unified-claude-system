---
name: oms-start
description: Initialize OMS context for a project. Run once per project before using /oms. Writes company and product direction to project-scoped ctx files.
---
# Skill: oms-start

Bootstraps OMS for the current project by capturing CEO context and writing it to project-scoped ctx files. Run once before first `/oms` use, or to update existing context.

## When to Use
- First time using `/oms` in a project
- Project pivots or major scope change
- CEO explicitly wants to update OMS context

## Steps

### 1 — Check existing context

Look for `.claude/agents/company-direction.ctx.md` in the current project directory.

**If it exists:** read it, then present to CEO:
```
Found existing OMS context for this project:
[show current content summary]

Update it? (y/n)
```
If no → skip to done. If yes → continue to Step 2.

**If not:** continue to Step 2.

### 2 — Ask CEO context questions

Present all questions at once (single message, CEO answers in one reply):

```
Setting up OMS for this project. Answer these to initialize:

1. What are you building? (one sentence — product, service, or personal project)
2. Who is it for? (target user, or yourself)
3. Current phase? (idea / MVP / live / scaling)
4. Tech stack? (frameworks, database, deployment)
5. What is explicitly out of scope right now?
6. Strategic constraints? (solo builder, no external funding, specific timeline, etc.)
7. What is the product focus / top priorities right now? (2–3 bullet points)
```

### 3 — Write project-scoped ctx files

Write two files inside the **current project's** `.claude/agents/` directory:

**`.claude/agents/company-direction.ctx.md`**
```markdown
# Company Direction — [Project Name]

## What We Are Building
[Answer to Q1]

## Who It's For
[Answer to Q2]

## Current Phase
[Answer to Q3]

## Tech Stack
[Answer to Q4]

## Out of Scope
[Answer to Q5]

## Strategic Constraints
[Answer to Q6]
```

**`.claude/agents/product-direction.ctx.md`**
```markdown
# Product Direction — [Project Name]

## Current Priorities
[Answer to Q7]
```

### 4 — Confirm

Tell CEO:
```
OMS context initialized. Files written to .claude/agents/:
- company-direction.ctx.md
- product-direction.ctx.md

These load automatically in every /oms run via Phase 1 ctx file glob.
Run /oms <task> to start.
```

## Rules
- **Never write to `~/.claude/agents/shared-context/`** — those are global OMS system files
- **Always write to the current project's `.claude/agents/`** — never global
- If `.claude/agents/` does not exist in the current project, create it
- Keep files under 30 lines — dense and scannable, no filler
