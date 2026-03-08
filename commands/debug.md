Systematic debug for: $ARGUMENTS

## Step 1: Gather Context
- Read full error message and stack trace
- Identify affected files and functions
- Check recent git changes that may have introduced this
- Run: git log --oneline -10

## Step 2: Form Hypotheses
- List 3 most likely causes ranked by probability
- Explain reasoning for each hypothesis

## Step 3: Test Hypotheses In Order
- Test most likely cause first
- If wrong, move to next
- Never try more than one fix at a time
- Do not suppress errors — fix root causes

## Step 4: Verify Fix
- Run full test suite
- Confirm original error is gone
- Confirm no regressions introduced

## Step 5: Document
If this was non-trivial: run /learn to save the pattern
