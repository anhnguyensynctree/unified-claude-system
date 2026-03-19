# Scenario 052 — Router Context Mode Detection + Dual Load

**Source**: OMS SKILL.md context mode spec; design-quality.md + ui-ux.md dual-load requirement added 2026-03-16
**Difficulty**: Intermediate
**Primary failure mode tested**: Router routes a UI/design task as `build` or `null` instead of `ui-ux`; or routes correctly but outputs `context_files: ["ui-ux"]` without `design-quality`; or Frontend Dev's briefing contains no visual engineering constraints from `design-quality.md`
**Criteria tested**: R5, R6, CM1 (new), CM2 (new)

## Synthetic CEO Intent
> "Redesign the onboarding flow — it feels generic. I want it to feel premium and considered, not like every other SaaS tool."

## Setup
Pure UI/design task. No backend changes. Frontend Dev is the domain agent. Router must:
1. Detect `task_mode: "ui-ux"` — not `build`, not `null`
2. Output `context_files: ["ui-ux", "design-quality"]` — both files
3. Read both context files and merge into Frontend Dev's `agent_briefings`
4. Frontend Dev briefing must contain: process/methodology signal (from ui-ux.md) AND visual constraint signal (from design-quality.md — banned patterns, typography, color rules)

## Expected Router Output

```json
{
  "task_mode": "ui-ux",
  "context_files": ["ui-ux", "design-quality"],
  "activated_agents": ["frontend-developer"],
  "agent_briefings": {
    "frontend-developer": "Approach onboarding as a flow design problem first — map the user's mental model before touching components (ui-ux.md). Visual constraints: no Inter/Roboto fonts, no centered hero + 3-column layout, no linear easing — use Geist/Satoshi, asymmetric grid, spring physics (design-quality.md)."
  }
}
```

**Key signals in a passing briefing:**
- References flow/user mental model OR interaction methodology → ui-ux.md loaded
- References specific banned patterns (fonts, layout, motion) OR permitted alternatives → design-quality.md loaded
- Both must appear — one alone is a CM2 fail

## Failure Patterns

**CM1 fail — wrong task_mode:**
- Router outputs `task_mode: "build"` → `context_files: ["dev"]` → design-quality.md never loaded
- Router outputs `task_mode: null` → no context files loaded at all

**CM2 fail — partial load:**
- Router outputs `context_files: ["ui-ux"]` only → design-quality.md missing
- Frontend Dev briefing references methodology (ui-ux.md signal) but no visual constraints → design-quality.md not distilled

**R5 fail — generic briefing:**
- Frontend Dev briefing: "You are the frontend developer. Design the onboarding flow." → no context distillation at all

## Pass Conditions
Router outputs `task_mode: "ui-ux"` AND `context_files: ["ui-ux", "design-quality"]`. Frontend Dev briefing contains at least one signal from each file. Trainer confirms both context files contributed to the briefing.

## New Criteria

**CM1**: Router correctly identifies `ui-ux` task_mode for tasks where UI design, interaction design, or visual implementation is the primary work — not incidental to a build task.

**CM2**: For `ui-ux` task_mode, Router outputs `context_files: ["ui-ux", "design-quality"]` and distills both into Frontend Dev's briefing. A briefing with only one file's content fails CM2.

## Trainer Evaluation Focus
Did Router reason from the nature of the work (design-first, no backend scope) to `ui-ux` — or did it default to `build` because "redesign" sounds like implementation? The tell is whether `context_files` is an array with both entries and whether the briefing contains visual constraint language that could only come from `design-quality.md`.
