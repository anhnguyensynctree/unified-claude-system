# Product Direction

## What This File Is
The current product phase, active scope, and what is explicitly out of scope. Loaded by every agent. Changes more frequently than company direction as the product evolves.

## Why It Exists
Agents need to know what is actively being built vs. what is deferred. A Backend Dev who doesn't know the web dashboard is dormant will design for it. A PM who doesn't know CMO division isn't active yet will route tasks to it. This file keeps all agents aligned on the current build state.

## How It Gets Updated
After each strategic decision — either via CEO direct edit or after an escalation that changed product direction. Task-level decisions (features, scoping) are logged in the decisions section below.

---

This file is loaded by all agents across all departments. It defines current product priorities, active scope, and what is out of scope for V1.

## Current Phase: V1 — Engineering Division
Proving the round-based discussion model before expanding to CMO and CFO divisions.

## V1 Scope — Active
- Executive Coordinator
- CTO
- Product Manager
- Engineering Manager
- Frontend Developer
- Backend Developer
- QA Engineer

## V1 Interface
- CEO interface: Claude Code chat only (`/oms` command)
- CEO sees: final decision + one-line summary per round on screen
- Full discussion log written to: `logs/tasks/[task-id].md`
- No interrupts in V1 — complex tasks use two-phase flow: discuss → plan → approve → execute

## V1 Out of Scope
- CMO division (Brand, Growth, Content)
- CFO division (Finance, Pricing)
- Next.js web dashboard (`apps/web` dormant)
- Multi-tenancy and org chart customization
- TypeScript SDK layer (V2)

## Product Decisions on Record
- Agents debate before any manager decides — discussion model, not pipeline
- C-suite self-activates via LLM judgment, no hardcoded keyword routing
- Max rounds: dynamic cap set by Router based on task complexity, hard cap of 5
- Convergence: positions stable across two rounds OR manager calls it
- Memory: three layers — agent own memory, persona.md additive updates, shared-context/
- Escalation format: structured brief + decision card with options and recommendation

## What Gets Updated Here
Product decisions made by the CEO or via escalation are appended to this file's decisions log section above. This file grows over time as the product evolves.
