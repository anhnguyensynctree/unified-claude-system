# Task Elaboration Lessons

Spec-writing failures captured from real oms-work task runs.
Written by: Trainer (Step 6 spec review) + oms-work validation failures.
Consolidated when this file exceeds 50 lines.

<!-- lessons append below -->

## Lesson: pip-portability
**When**: Writing Verify for any Python impl task
**Do instead**: Use `python -m pytest` not bare `pytest`; use `python -m pip` not bare `pip`. Dependency installation (`pip install`) is NOT a Verify command — it belongs in executor setup. Verify confirms the task artifact works.
**Correct pattern**: `Verify: python -m pytest tests/auth/ -v`
**Wrong pattern**: `Verify: pip install -r requirements.txt | pytest tests/auth/`
**Source**: TASK-001 — repeated CTO-STOP failures (`pip install -r requirements.txt exits 0`) on executor where only `python -m pip` was available
**Affected**: Verify field on all Python impl tasks

## Lesson: qwen-coder-borderline-downgrade
**When**: Impl task involves TypeScript interfaces across modules, or 2–3 files with complex type wiring (generics, discriminated unions, shared schemas)
**Do instead**: Write `Model-hint: gpt-oss` instead of `qwen-coder`. `gpt-oss` (120B, free) handles TypeScript interface complexity better than qwen-coder (code-focused, weaker on cross-file type reasoning).
**Correct pattern**: 2-file TypeScript interface extraction → `Model-hint: gpt-oss`
**Wrong pattern**: 2-file TypeScript interface extraction → `Model-hint: qwen-coder`
**Source**: TASK-001, TASK-046 — qwen-coder failed on tasks with cross-module TypeScript interfaces; retries consumed extra budget before succeeding on gpt-oss
**Affected**: Model-hint field on impl tasks with TypeScript interface complexity (not all impl — single-file pure code still uses qwen-coder)
