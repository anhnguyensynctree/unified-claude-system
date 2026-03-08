TDD workflow for: $ARGUMENTS

## Step 1: Define Interface
What are the inputs? What are the outputs?
Write the function/component signature first.

## Step 2: Write Failing Tests (RED)
- Happy path test
- Edge case tests
- Error case tests
Run tests — they should all fail.

## Step 3: Implement (GREEN)
Write minimal code to make tests pass.
Do not over-engineer. Make it pass, then make it good.

## Step 4: Refactor (IMPROVE)
Clean up code. Extract helpers. Improve naming.
Run tests after every change — must stay green.

## Step 5: Verify Coverage
Run coverage report. Must be 80%+.
If below: add tests for uncovered branches.
