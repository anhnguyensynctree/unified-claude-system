Review the current branch diff against main.
Run: git diff main..HEAD

Check for:
  - Logic bugs and edge cases
  - Security issues (injection, auth gaps, exposed secrets)
  - Missing error handling
  - Test coverage gaps
  - Performance concerns (N+1s, unnecessary re-renders, expensive ops)
  - Naming clarity
  - Unnecessary complexity

Structure output as:
  🚨 Blockers (must fix before merge)
     - [file:line] description
  ⚠️  Suggestions (should fix, not blocking)
     - [file:line] description
  ✅  Looks Good
     - Call out what's done well

Be specific — always include file and line number.
