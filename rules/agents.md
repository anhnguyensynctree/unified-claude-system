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

