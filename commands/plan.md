Create a phased implementation plan for: $ARGUMENTS

Write the plan to .claude/sessions/plan-$ARGUMENTS.md

## Phase 1: RESEARCH
Goal: understand current state before changing anything
- Read relevant existing files
- Identify patterns already in use
- Note any constraints or dependencies
Output: .claude/sessions/research-$ARGUMENTS.md

## Phase 2: PLAN
Goal: detailed implementation plan with tasks
- Read research output
- List every task needed
- Note dependencies between tasks
- Flag consistency-critical tasks
Output: .claude/sessions/plan-$ARGUMENTS.md

## Phase 3: IMPLEMENT
Goal: write tests first, then implementation
- Read plan file
- TDD: test → implement → verify
Output: code changes + passing tests

## Phase 4: REVIEW
Goal: verify quality before finishing
- Check all changes against original objective
- Look for missing edge cases
Output: .claude/sessions/review-$ARGUMENTS.md

## Phase 5: VERIFY
Goal: confirm everything works
- Run full test suite
- Run lint and typecheck
- If failures: loop back to Phase 3
Output: done, or loop

Rules:
- Store all phase outputs as files
- Never skip phases
- /compact between phases if context is heavy
- Each phase: one clear input, one clear output
