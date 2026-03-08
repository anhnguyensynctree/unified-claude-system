# Development Mode

You are in implementation mode.

## Priorities
- Working, tested code
- Files under 300 lines
- Conventional commits
- Tests pass before done

## Do Not
- Refactor unless explicitly asked
- Modify files outside task scope
- Create .md files (except README, CLAUDE, session files)
- Skip tests to move faster

## Before Writing Code
1. Check .claude/codemap.md — read it for navigation
2. Check .claude/sessions/ — offer to restore recent context
3. For tasks touching 3+ files: create a plan first via /plan
4. Identify what tests are needed (unit / integration / E2E) before starting

## Implementation Order — Always
1. Write failing test(s) for the new behavior
2. Write the implementation
3. Make tests pass
4. Run full test suite — no regressions
5. Add E2E test if the change touches a user-facing flow

## After Completing
1. Confirm tests written for every new component/service/hook/route
2. Run targeted tests for modified files
3. Run full test suite — all must pass
4. Check for console.log in modified files
5. Update .claude/codemap.md if structure changed
