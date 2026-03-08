Look at `git diff --staged`.
If nothing is staged, run `git status` and show the user what's unstaged.
Ask which files to stage — never use `git add -A` or `git add .` without confirmation.

Write a conventional commit message:
  Format: <type>(<scope>): <subject>
  Types: feat|fix|chore|docs|refactor|test|perf
  Subject: under 72 chars, imperative mood
  Add body paragraph if the change needs explanation
  Add "fixes #N" footer if issue number is known

Before committing:
  - Verify no console.log, secrets, or commented-out code in staged files
  - Show the full commit message for approval
  - Do not run git commit without explicit confirmation
