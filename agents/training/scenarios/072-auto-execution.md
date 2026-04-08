---
id: 072
title: Elaboration Verify commands must use portable Python invocation
status: active
difficulty: Basic
---

# Scenario 072 — Elaboration: Non-Portable Python Verify Commands

**Difficulty**: Basic
**Primary failure mode tested**: Elaboration Agent writes `pip install` or bare `pip` in Verify commands for Python tasks, causing execution failures on systems where only `pip3` / `python -m pip` is available.
**Criteria tested**: LA1 (lesson acknowledgment), LA2 (lesson effect — lesson cited but not applied), QG2 (impl Verify must contain test runner)

## Synthetic CEO Intent

> `/oms all` on a Python project task: "Set up test suite for the authentication module — pytest, fixtures, CI-ready"

## Failure Pattern — Non-Portable Verify

Elaboration writes:
```
Verify: pip install -r requirements.txt | pytest tests/auth/
```

Two failures embedded:
1. `pip` may not exist on the executor's PATH — `pip3` or `python -m pip` is portable
2. Dependency installation in Verify is wrong — Verify tests completion, not setup. A `pip install` in Verify means the task hasn't confirmed the code works, only that dependencies install.

## Expected Behavior

Elaboration MUST write:
```
Verify: python -m pytest tests/auth/ -v
```

Or if requirements.txt creation is itself the task output:
```
Verify: test -f requirements.txt | python -m pip install -r requirements.txt --dry-run
```

Rules:
- Use `python -m pytest` not `pytest` (portable across environments)
- Use `python -m pip` not `pip` (portable across environments)
- Dependency installation is NOT a Verify command — it is executor setup. Verify confirms the task artifact works.
- `lessons.md` contains the pip portability lesson from TASK-001 failures. Elaboration must cite it with `Applying lesson:` and the observable change must be using `python -m pip` / `python -m pytest`.

## Failure Signals

| Signal | What went wrong |
|---|---|
| Elaboration output has no `Applying lesson:` for pip portability | LA1 fail — lesson in lessons.md not cited |
| `Applying lesson:` cited but Verify still uses bare `pip` or `pip install` | LA2 fail — lesson acknowledged but not applied |
| Verify is only `pip install -r requirements.txt` with no pytest | QG2 fail — validate-queue.py blocks at write time |

## Validation Criteria

- **LA1**: When `lessons.md` contains the pip portability lesson, Elaboration MUST include `Applying lesson:` citation. Missing citation fails LA1.
- **LA2**: The citation must produce an observable change — Verify uses `python -m pytest` not bare `pip install`. A citation with no change fails LA2.
- **QG2**: `type: impl` Verify must contain a test runner. `pip install -r requirements.txt` with no pytest fails QG2 — blocked by validate-queue.py.
