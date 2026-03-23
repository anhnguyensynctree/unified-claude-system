# OMS Agent Creation Rules

Read this file during `/oms-start` whenever a new agent persona is proposed or approved.

## The Core Question

Before creating any new agent: **does this role require knowledge or reasoning that no existing agent can do without degrading their primary output?**

If yes → create. If no → extend an existing agent's ctx.md with domain notes instead.

## When To Create a New Agent

All three conditions must be met:
1. **Specialized knowledge domain** — expertise structurally different from any existing agent (mobile UX ≠ web UX; game AI ≠ backend engineering)
2. **Distinct workflow** — inputs, reasoning process, and outputs differ meaningfully from existing agents
3. **Recurring involvement** — the domain appears in 3+ tasks per project cycle, not a one-off need

## Research Agents — Same Pattern as Research Questions

One agent per distinct research domain — mirrors how each research question is its own discussion thread. Two distinct domains = two agents. Never bundle unrelated research domains into one persona.

**Trigger**: Router identifies a discussion requires domain knowledge no active researcher holds → propose to CEO before proceeding.

## The Balance Rule

**Too many (anti-pattern)**:
- Agent for every sub-topic (iOS + Android + RN → one mobile agent covers all)
- Agents with identical reasoning patterns but different subjects → use ctx.md instead
- Agents that only ever activate together → merge or redraw the boundary

**Too few (anti-pattern)**:
- One agent handling 3+ unrelated domains → output quality degrades
- C-suite agents doing specialist execution → C-suite directs, specialists execute
- Single researcher across all research domains → depth collapses to breadth

**Right size heuristic**: an agent should produce high-quality output without needing another agent's domain knowledge to complete its own work. If it constantly borrows from another agent's domain, merge them or redraw the boundary.

## C-Suite Narrowing Gate — Required Before Any Persona Is Written

1. **CPO**: does this role map to a product outcome? If the agent's work never surfaces in a synthesis recommendation → overhead, reject.
2. **CTO**: is this a knowledge gap (→ new agent) or a tooling/context gap (→ ctx.md entry)?
3. **CEO**: approve / defer (use existing agent + ctx.md for now) / reject.

New agents are never created autonomously. Gate always runs in OMS discussion first.

## Agents Are Project-Agnostic

Agent personas carry **domain knowledge only** — never project-specific knowledge. A backend-developer agent knows how to reason about APIs, databases, and service design across any project. It does not know your schema, your stack choices, or your product constraints.

**Project-specific knowledge always lives in the project's ctx.md file**, not in the persona. This keeps agents reusable across every project OMS runs on.

- ✓ Persona: "prefer idempotent API design"
- ✗ Persona: "this project uses Supabase with a users table"
- ✓ ctx.md: "Database: Supabase — users, sessions, events tables"

When writing a new persona: if a sentence only makes sense for one project, it belongs in that project's ctx.md, not the persona.

## Persona Design Constraints

- **Single primary responsibility** — one sentence defining what the agent decides or produces
- **Activation condition** — Router must evaluate it in <10 tokens
- **Output contract** — defined format before writing the persona (JSON schema, markdown section, structured list)
- **Line target from day one** — engineering: 70, researcher: 65, C-suite: 60, engine: 80
- **No cross-domain authority** — advises in its domain, escalates cross-domain decisions to C-suite

## Persona File Structure

Every new persona must have these sections in order:
1. `## Identity` — role, model, one-line purpose
2. `## Activation Condition` — when Router includes this agent
3. `## Primary Output` — what this agent produces and in what format
4. `## Non-Negotiables` — hard constraints (Context Optimizer never touches this section)
5. `## Working Guidelines` — domain-specific approach (subject to dedup/upgrade pipeline)

## Reference Calibration

Reviewed: Claude Code Game Studios, Agency Agents (msitarzewski), Awesome AI Agents (e2b).

Adapted principles:
- Vertical specialization within domains beats horizontal generalism
- New agent requires specialized knowledge + distinct workflow + recurring need — all three
- Router proposes, CEO gates — never autonomous spawning
- Regional/cultural variants that have fundamentally different rules justify separate personas
- Agents never make binding cross-domain decisions autonomously — always escalate to C-suite
