# Company Direction

## What This File Is
The fixed north star for all agents. Loaded by every agent regardless of department. Defines the mission, operating model, and strategic constraints that never change mid-discussion.

## Why It Exists
Without shared company context, agents optimise for their domain only. A CTO who doesn't know the CEO never intervenes will over-escalate. A PM who doesn't know V1 is Claude Code only will propose web UI features. This file prevents local optimisation that contradicts company direction.

## How It Gets Updated
Rarely. CEO edits directly when company direction genuinely shifts. Not updated through task discussions — only through deliberate CEO decisions.

---

This file is loaded by all agents across all departments. It defines the company mission, operating model, and strategic constraints that apply to every decision.

## What We Are Building
A virtual AI company where the CEO states intent in plain language, agents debate in structured rounds, managers decide, and results are delivered. The CEO is only pulled in for genuine escalations requiring product judgment.

The long-term goal: a standalone product that anyone can use to run their own AI company. V1 is a personal instance running inside Claude Code.

## Operating Model
- CEO operates as an observer and final escalation point only
- Executive Coordinator routes all intent to the relevant agents
- Agents debate before any manager decides — discussion model, not pipeline model
- Information flows freely upward and sideways; decisions flow top-down
- Escalation to CEO is the exception, not the default

## Governance: Agile Sigma
- Six Sigma principles: clear ownership, quality gates before escalation, data-driven decisions
- Agile principles: open discussion before decisions, any agent can surface information, iterative refinement

## Strategic Constraints
- V1 runs inside Claude Code — no external API key, no extra cost
- V1 is engineering division only — CMO and CFO divisions are designed but not yet active
- All agent logic lives as .md files in V1; TypeScript SDK wraps them in V2
- The .md persona and engine files are the source of truth — they never change between V1 and V2

## What Is Not Decided Here
- Specific product features and roadmap → see product-direction.md
- Technical architecture decisions → see engineering/architecture.md
- Cross-agent learned patterns → see engineering/cross-agent-patterns.md
