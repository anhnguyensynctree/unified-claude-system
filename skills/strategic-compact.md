---
name: strategic-compact
description: Suggest context compaction at logical phase transitions. Use to prevent context rot during long sessions.
---

# Strategic Compact

## Why Manual Over Auto
Auto-compact fires at arbitrary points, often mid-task.
Strategic compacting preserves context through complete phases.

## When To Compact
- After exploration phase ends, before implementation begins
- After a milestone completes, before starting the next
- After 50+ tool calls in a session
- When switching from one major feature to another
- Before starting a new agent delegation

## Before Compacting: Save State
Write to .claude/sessions/[date]-[topic].tmp:
- What was built or decided this session
- Approaches that did NOT work (important — prevents re-trying them)
- What is pending / left to do
- Key decisions made and why

Then run: /compact

## After Compacting
Continue from the plan file.
The session state file provides re-entry context if needed.
