# Lesson System — Two-Layer Architecture

## Structure

```
~/.claude/agents/[role]/lessons.md     ← global: applies across all projects
[project]/.claude/agents/[role]/lessons.md  ← project: this project only
```

Every agent has both layers. Trainer writes to both. OMS loads both when building agent prompt.

## Load order

Agent effective prompt = persona.md → global lessons.md → project lessons.md → ctx.md → MEMORY.md → agent_briefing

Project lessons are appended after global — they narrow global behavior to this project's context.

## Lesson format

Every lesson must include:
```
[date] | [task-id] | importance:[critical|high|medium|low] | [one imperative sentence]
Surfaces when: [condition that makes this lesson relevant]
```

Examples:
```
2026-03-22 | 2026-03-22-auth-flow | importance:high | Validate JWT expiry before assuming token is active.
Surfaces when: auth, session management, token validation tasks

2026-03-22 | 2026-03-22-auth-flow | importance:medium | Prefer refresh token rotation over long-lived access tokens for mobile clients.
Surfaces when: mobile auth, React Native, Expo projects
```

## Trainer write rules

**After every task:**
- Task-specific lesson → project lessons.md first
- If the same lesson already exists in project lessons.md (4-word fingerprint match) → upgrade importance, do not duplicate
- If the lesson has appeared in 3+ different projects → promote to global lessons.md, remove from project files
- Never write to persona.md directly

**Importance assignment:**
- `critical` — violates a non-negotiable or caused a task failure
- `high` — would have meaningfully changed the outcome
- `medium` — useful context, improves future performance
- `low` — minor nuance, nice-to-know

## Token Optimizer rules

**Safe (auto, no CEO notification):**
1. Dedup: two lessons with 4-word fingerprint match → merge into stronger single rule, keep highest importance
2. Upgrade: 3+ lessons teaching same principle → collapse to one canonical lesson flagged `importance:high`
3. Archive: `importance:low` lessons older than 60 days with zero activation → move to `lessons-archive.md`

**Critical (flag to CEO via Discord, do not act):**
- Any `importance:high` or `importance:critical` lesson would be removed or significantly altered
- Format: `[agent] lessons.md at [N] lines — critical trim needed, [lesson preview]. Approve? Reply y/n`
- OMS never pauses for this — it is a non-blocking Discord update

## Persona promotion (rare)

Only Trainer may propose persona changes. Requirements:
- The same principle has appeared as `importance:critical` across 5+ consecutive tasks
- CEO must approve via Discord before Trainer writes to persona.md
- Persona additions go to `## Non-Negotiables` or `## Discussion` only — never to output schema

## File size targets

| Layer | Soft limit | Action at limit |
|---|---|---|
| Global lessons.md | 80 lines | Optimizer runs dedup + archive cycle |
| Project lessons.md | 40 lines | Optimizer merges project-only duplicates |
| lessons-archive.md | No limit | Never loaded into context |
