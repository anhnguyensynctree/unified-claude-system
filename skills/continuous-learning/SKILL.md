---
name: continuous-learning
description: Automatically extract reusable patterns from sessions and save as skills. Fires at session end via Stop hook. Also available manually via /learn command.
---

# Continuous Learning

## How It Works
At every session end, evaluate-session.sh runs via the Stop hook.
It logs session metadata and prompts for pattern extraction.

Patterns worth extracting:
- Error resolutions that were non-trivial
- Debugging techniques discovered during the session
- Workarounds for known issues
- Project-specific patterns Claude didn't know about
- Corrections you had to make to Claude's default approach

## Output Location
Learned skills: `~/.claude/skills/learned/[pattern-name].md`
Session logs: `~/.claude/sessions/YYYY-MM-DD-session.tmp` (auto-populated by mem0 handoff)

## Observation Routing — Always Follow
When extracting patterns, route to the correct topic file:

| Content type | Target file |
|---|---|
| Hook fix, hook config change, hook pattern | `~/.claude/projects/-Users-Lewis/memory/topics/hooks.md` |
| Project scaffold, stack decision, monorepo setup | `~/.claude/projects/-Users-Lewis/memory/topics/scaffold.md` |
| Agent delegation, model selection, subagent pattern | `~/.claude/projects/-Users-Lewis/memory/topics/agents.md` |
| Bug fix insight, non-obvious diagnosis, debugging technique | `~/.claude/projects/-Users-Lewis/memory/topics/debugging.md` |
| API design, architecture decision, code pattern | `~/.claude/projects/-Users-Lewis/memory/topics/patterns.md` |
| Project history, stack, status, per-project decision | `~/.claude/projects/-Users-Lewis/memory/topics/projects.md` |
| Cross-project patterns, insights spanning multiple topics | `~/.claude/projects/-Users-Lewis/memory/insights.md` |
| User preference, workflow change | `~/.claude/projects/-Users-Lewis/memory/MEMORY.md` |

Never write to MEMORY.md for domain-specific content — route to topic files. MEMORY.md is the index only.

Before writing to any topic file, grep the target file for semantically similar content. If a match exists, UPDATE the existing entry rather than appending a new one.

## Manual Extraction
Run /learn mid-session to extract a pattern immediately.
Use this right after solving something non-trivial — don't wait for session end.
