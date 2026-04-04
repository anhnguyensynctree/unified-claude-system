---
name: template-improve
description: Extracts learnings from a completed client project and applies improvements back to client-marketing-template. Run after each client ships.
---

# Skill: template-improve

Reads a completed client project, compares it against the template defaults, and applies concrete improvements back to `client-marketing-template`. Makes the next client faster and better.

## When to Use
- After any client project reaches M4 (deployed + E2E passing)
- When the user says "learn from [client]" or "update the template from [client]"
- After a major fix or pattern discovery mid-project that should become a default

## Step 1 — Read the Client Project

Read these files from the completed client project:
- `.claude/agents/cleared-queue.md` — what tasks were built, what changed from spec
- `.claude/agents/frontend-developer.ctx.md` — what variants were actually used
- `.claude/agents/ux-designer.ctx.md` — UX decisions that diverged from defaults
- `.claude/agents/research.ctx.md` — copy patterns and customer language that worked
- `apps/web/config/client.ts` — final section config (enabled sections + variants)
- `apps/web/components/sections/` — any new section components built that aren't in the template
- `retrospective.md` (if exists) — explicit agent-written learnings

If `retrospective.md` doesn't exist: derive learnings from the above files by diffing against template defaults.

## Step 2 — Diff Against Template Defaults

Compare client project against `~/.claude/templates/client-marketing-template/`:

| Area | What to diff |
|---|---|
| Sections | Which sections were enabled beyond template defaults? Any new sections built? |
| Variants | Which variant was chosen per section? Did it differ from the template default? Why? |
| Token preset | Was the auto-selected preset correct? Did colors get adjusted? |
| Section order | Did UX designer change the default order? Why? |
| Copy patterns | What headlines/CTAs worked well and should become copy guidance? |
| Media | Were there media types or folder structures not handled by gen-manifest? |
| Bugs/rework | What caused extra work that better defaults would have prevented? |

## Step 3 — Classify Learnings

For each finding, classify:

- **Default change** — template default should be updated (e.g., process section should be enabled for "leads" goal)
- **New variant** — a new layout was built that should be added as Variant C or a new section
- **Token refinement** — a preset color was adjusted for a specific industry
- **Copy rule** — a copy pattern that should go into copywriter.ctx.template.md
- **UX rule** — a UX decision that should go into ux-designer.ctx.template.md
- **Bug fix** — something broken in the template that caused rework
- **New section** — a section built from scratch that should be added to the template

## Step 4 — Apply to Template

Apply changes directly to `~/.claude/templates/client-marketing-template/`. Be surgical:

- **Default changes** → edit `oms-init.json` sections defaults + `config/client.ts` defaults
- **New variants** → add `VariantC.tsx` (or D if C exists) to the section dir + update `index.tsx`
- **New sections** → add full section dir with 3 variants + register in `oms-init.json` + `config/client.ts` + `components/sections/index.tsx`
- **Token refinements** → update the preset file in `design/tokens/`
- **Copy rules** → append to `copywriter.ctx.template.md`
- **UX rules** → append to `ux-designer.ctx.template.md`
- **Bug fixes** → fix in place

## Step 5 — Write Retrospective to Template

Append to `~/.claude/templates/client-marketing-template/.claude/LEARNINGS.md`:

```markdown
## [Client Name] — [Date]

**Industry:** [industry]
**Preset used:** [preset]
**Goal:** [goal]

### What worked
- [finding]

### What changed from defaults
- [finding + new default]

### New additions to template
- [new section/variant/rule]

### Watch out for next time
- [gotcha or edge case]
```

## Step 6 — Confirm

Tell CEO:
```
✓ Template updated from [Client Name] learnings

Applied:
- [change 1]
- [change 2]
- [change 3]

LEARNINGS.md updated.
Next client starts from an improved base.
```

## Rules
- Never touch client project files — only read them, write only to the template
- If a change affects oms-init.json sections registry: also update cleared-queue.template.md task list
- If a new section is added: it needs all 3 variants before being added — never add a stub
- Improvements must be generalizable — client-specific business logic never goes into the template
