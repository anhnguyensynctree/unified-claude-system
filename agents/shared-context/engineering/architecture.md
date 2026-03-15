# Engineering Architecture

## What This File Is
Settled architectural decisions for the engineering division. Loaded by all engineering agents. Distinct from tech-stack.md (which lists tools) — this file records *decisions* about how those tools are used together.

## Why It Exists
Architecture decisions made in one task must constrain future tasks. Without this, agents re-litigate the same decisions every discussion. A CTO who doesn't know cross-package imports must use workspace names will approve code that breaks the monorepo. This file is the institutional memory for engineering structure.

## How It Gets Updated
After each task where a new architectural decision is reached. The synthesising agent appends the decision with a one-line rationale. Never edited to remove decisions — superseded decisions are marked with a date and replacement.

---

This file is loaded by all engineering agents. It records active architectural decisions that constrain how engineering work is approached.

## Stack
- Runtime: Node.js, TypeScript
- Frontend: Next.js (App Router), Tailwind CSS
- UI components: shadcn/ui (`packages/ui`)
- Database: Supabase (Postgres + Auth + Storage)
- AI: Anthropic Claude API (agent orchestration)
- Monorepo: pnpm workspaces + Turborepo

## Package Structure
| Package | Purpose |
|---------|---------|
| `apps/web` | Next.js CEO dashboard — dormant in V1 |
| `packages/agents` | Agent personas, discussion engine, escalation logic |
| `packages/ui` | Shared component library |
| `packages/database` | Supabase client, schema, migrations |
| `packages/config` | Shared tsconfig, eslint, prettier |

## Active Architectural Constraints
- Cross-package imports always use package names (`@one-man-show/agents`), never relative paths
- Agent personas and engine files are `.md` — no TypeScript in V1 agent layer
- Discussion logs written to `logs/tasks/[task-id].md` from the project root
- Agent memory lives in `.claude/agents/[role]/MEMORY.md` at the monorepo root

## API Standards
- All API responses: `{ data: T | null, error: string | null, meta?: object }`
- Error objects always include: type, message, context
- No unhandled promise rejections

## What Gets Updated Here
Architectural decisions made during task discussions are appended here after synthesis. This file is the engineering division's source of truth for settled technical direction.
