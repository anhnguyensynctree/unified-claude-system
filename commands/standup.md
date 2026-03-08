Run: git log --since="yesterday" --author="$(git config user.name)" --oneline

Summarize into standup format:
  Yesterday: [what was done]
  Today: [what is planned]
  Blockers: [any blockers, or "None"]

Max 5 bullet points total. Be concise.
