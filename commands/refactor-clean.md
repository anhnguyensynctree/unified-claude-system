Analyze and clean the codebase.

Find and propose removal/refactoring of:
  - Unused imports, functions, variables, types
  - Duplicate logic that can be extracted to shared utility
  - Files over 300 lines (propose split plan)
  - console.log statements
  - Commented-out code blocks
  - Loose .md files that shouldn't exist
  - Dead code paths

Rules:
  - Show a summary of ALL proposed changes before applying anything
  - Never change behavior — only structure
  - Apply changes in small batches
  - Run tests after each batch
  - Flag anything uncertain rather than guessing
