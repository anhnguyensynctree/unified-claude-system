Generate a PR description for current branch vs main.

Run: git log main..HEAD --oneline
Run: git diff main..HEAD --stat

Include in description:
  ## Summary
  What this PR does (2-3 sentences)

  ## Changes
  Bullet list of what changed and why

  ## Testing
  How this was tested

  ## Screenshots
  [Add if UI changed]

  ## Breaking Changes
  [List any, or "None"]

Show for approval. Do not create PR without confirmation.
