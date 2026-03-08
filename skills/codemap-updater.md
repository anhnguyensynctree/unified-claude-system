---
name: codemap-updater
description: Update project codemaps for fast navigation. Use at session start, after major refactors, and before context compaction to keep Claude's navigation reference current without burning context on re-exploration.
---

# Codemap Updater

## Purpose
Codemaps let Claude navigate a codebase without re-exploring every session.
A stale codemap wastes tokens. An up-to-date one saves them.

## When To Update
- Session start (check date — if older than 2 days, refresh)
- After adding new modules or directories
- After significant refactors
- Before running /compact

## Output Format
Write to .claude/codemap.md (max 100 lines):

```
# Codemap — [Project Name] — [YYYY-MM-DD]

## Entry Points
- [file]: [purpose]

## Key Directories
- [dir/]: [what lives here]

## Architecture
[How the pieces connect — 5-10 lines]

## Key Files
- [file]: [why it matters]

## Recently Changed
- [file]: [what changed]
```

## Do Not Include
- Every file in the project (only key ones)
- Implementation details
- Content that belongs in README
