Extract a reusable pattern from what was just solved.

Steps:
  1. Identify: what was the non-trivial problem just solved?
  2. Document: what was the solution approach?
  3. Generalize: how does this apply to similar future problems?
  4. Write to ~/.claude/skills/learned/[pattern-name].md
  5. Ask for confirmation before saving

Skill file format:
---
name: [pattern-name]
description: When to use this. Trigger phrases that should activate it.
---
## Problem
[what the problem looks like]

## Solution
[the approach that works]

## Example
[concrete code or steps]

## When NOT To Use This
[important exceptions]
