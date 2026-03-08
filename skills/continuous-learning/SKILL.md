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
Learned skills: ~/.claude/skills/learned/[pattern-name].md
Session logs: ~/.claude/sessions/YYYY-MM-DD-[topic].tmp

## Session Log Format
Each .tmp file should contain:
- What approaches WORKED (with evidence)
- What approaches did NOT work
- What hasn't been attempted yet
- What's left to do
- Key decisions and why they were made

Create one file per session. Do not append to old session files.

## Manual Extraction
Run /learn mid-session to extract a pattern immediately.
Use this right after solving something non-trivial — don't wait for session end.
