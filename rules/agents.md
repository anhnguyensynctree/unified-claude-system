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
Haiku vs Opus = 5x cost difference — the meaningful optimization split.

## Agent Abstraction Tiers
Tier 1 — start here, low complexity:
  Subagents, metaprompting, asking clarifying questions upfront

Tier 2 — only after mastering Tier 1:
  Long-running agents, parallel multi-agent, role-based multi-agent
