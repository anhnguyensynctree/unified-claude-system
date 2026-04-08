---
id: 073
title: qwen-coder downgrade for TypeScript interface tasks
status: active
difficulty: Basic
---

# Scenario 073 — Elaboration: Model-hint Downgrade for TypeScript Interface Tasks

**Difficulty**: Basic
**Primary failure mode tested**: Elaboration assigns `qwen-coder` to a TypeScript interface impl task despite a lessons.md entry documenting that qwen-coder struggles with cross-module type wiring. Lesson teaches: use `gpt-oss` (free, 120B) for TypeScript interface complexity.
**Criteria tested**: LA1 (lesson acknowledgment), LA2 (lesson effect — model-hint change observable)
**Criteria note**: MR1 covers engine model routing. LA1/LA2 test whether Elaboration applies lessons to task queue model-hint selection. Both `qwen-coder` and `gpt-oss` are free — this is a quality routing decision, not a subscription vs free decision.

## Synthetic CEO Intent

> `/oms all` on a TypeScript impl task: "Extract auth middleware into a shared package — move session validation, JWT decode, and role checks out of apps/web into packages/auth — create typed exports"

## Context

`lessons.md` contains the `qwen-coder-borderline-downgrade` lesson:
- When: impl task with TypeScript interfaces across modules, 2–3 files with complex type wiring
- Do instead: `Model-hint: gpt-oss` not `qwen-coder`

Elaboration sees this task (2–3 files, TypeScript interface exports, cross-package type wiring) and must recognize it matches the lesson condition.

## Expected Behavior

Elaboration MUST cite the lesson and adjust:
1. Cite: `Applying lesson: qwen-coder-borderline-downgrade → TypeScript cross-module interface extraction → Model-hint: gpt-oss`
2. Write `Model-hint: gpt-oss`

## Failure Signals

| Signal | What went wrong |
|---|---|
| `Model-hint: qwen-coder` on this TypeScript interface task | LA2 fail — lesson not applied |
| No `Applying lesson:` citation | LA1 fail — lesson not cited |
| `Applying lesson:` cited but Model-hint still `qwen-coder` | LA2 fail — citation without observable change |

## Validation Criteria

- **LA1**: When `lessons.md` contains the qwen-coder-borderline-downgrade lesson, Elaboration MUST include `Applying lesson:` citation for a TypeScript cross-module interface task. Missing citation fails LA1.
- **LA2**: The citation must produce an observable change — `Model-hint: gpt-oss` not `qwen-coder`. Citation with no change fails LA2.
