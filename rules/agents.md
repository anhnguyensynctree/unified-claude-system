# Agent Delegation Rules — Always Follow

## When To Delegate
- Task requires deep focus on one domain (security, testing, design)
- Task is long enough to consume too much main context
- Task can run in parallel without code overlap

## Dispatch Protocol
When delegating to a subagent, ALWAYS include:
1. The specific query (what to do)
2. The broader objective (WHY — what this feeds into)
3. Expected output format and file path

## Evaluation Protocol
When a subagent returns, ALWAYS:
1. Evaluate: is this sufficient for the objective?
2. If not: ask specific follow-up questions
3. Subagent fetches answers and returns updated result
4. Max 3 evaluation cycles — then accept best available
Never accept a summary without checking it against the objective.

## Model Selection Per Task
- Haiku: repetitive tasks, clear instructions, "worker" in multi-agent
- Sonnet: default for 90% of coding tasks
- Opus: first attempt failed, spans 5+ files, architectural decisions, security-critical
Haiku vs Sonnet ≈ 20x cheaper. Haiku vs Opus ≈ 60x cheaper. Default to Haiku for mechanical work.

## Default Behavior
Prefer parallel subagents whenever a task can be split, even small ones — never ask the user to specify this.
Dispatch concurrent Agent calls in a single message when workstreams are independent. Serial only when order is required.

## Skill Contracts — llms.txt
Every skill must have a `llms.txt` in its directory. This is the machine-readable contract agents use to understand when and how to invoke it.

**Before cross-referencing a skill in an agent briefing:** read its `llms.txt` — never assume invocation syntax or trigger conditions from the skill name alone.

**When creating a new skill:** write `llms.txt` before or alongside `SKILL.md`. Minimum content:
- Trigger conditions (when to use this skill)
- Invocation syntax (exact command forms)
- What it reads and writes (key files)
- What it does NOT do

`llms.txt` path: `~/.claude/skills/<skill-name>/llms.txt` (global) or `.claude/skills/<skill-name>/llms.txt` (project-scoped).

