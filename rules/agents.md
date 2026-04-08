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

## Model Selection Per Task [ENFORCED: enforce-agent-model.sh]

Every Agent tool call MUST include an explicit `model:` param. The hook blocks calls without one.

| Role | Model | When to use |
|---|---|---|
| **Judge** | Haiku | Validation (pass/fail), extraction, slug generation, fact extraction, format checks |
| **Worker** | Haiku | Clear instructions, single-file mechanical edits, repetitive structured output |
| **Builder** | Sonnet | Default for all code generation, multi-file impl, research synthesis, briefings |
| **Architect** | Opus | Failed first attempt, 5+ files, architecture decisions, security-critical, strategic planning |

### Agent Type → Model Mapping

| Agent type | Model | Rationale |
|---|---|---|
| Explore | Haiku (hardcoded) | File search, keyword lookup — no reasoning needed |
| Plan | Sonnet | Architecture reasoning, not full Opus |
| general-purpose (research) | Sonnet | Search + read + synthesize |
| general-purpose (code) | Sonnet | Code gen sweet spot |
| claude-code-guide | Haiku (hardcoded) | Docs lookup |
| Judge/validator | Haiku | Binary pass/fail |

Hardcoded agents (Explore, claude-code-guide, statusline-setup) bypass the hook — they set their own model internally.

Cost: Haiku ≈ 20x cheaper than Sonnet ≈ 60x cheaper than Opus.

**Decision rule:** If the agent's output is binary (pass/fail) or follows a rigid template → Haiku. If the agent must reason across files, synthesize, or write quality prose → Sonnet. If it failed on Sonnet or the blast radius is high → Opus.

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

