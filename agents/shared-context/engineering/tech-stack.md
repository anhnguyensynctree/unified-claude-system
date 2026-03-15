# Engineering Tech Stack

## What This File Is
The canonical reference for the one-man-show technology stack. All engineering agents load this file. It defines what tools, frameworks, and services are in use — so agents reason about real constraints, not hypothetical ones.

## Why It Exists
Without this, agents invent stack assumptions mid-discussion. A Frontend Dev who doesn't know we use Next.js App Router will give wrong API shape advice. A Backend Dev who doesn't know we're on Supabase will propose the wrong migration strategy. This file anchors all technical reasoning to the actual project.

## How It Gets Updated
When a technology decision is made through an `/oms` task, the synthesizing agent or CTO appends the change here. This file reflects settled decisions only — proposals belong in the discussion log.

---

## Runtime
- Node.js (server runtime)
- TypeScript (all packages)

## Frontend
- Next.js 14+ with App Router
- Tailwind CSS
- shadcn/ui component library (`packages/ui`)
- React Server Components where appropriate

## Backend / API
- Next.js API routes (App Router) for lightweight endpoints
- Supabase Edge Functions for heavier server logic

## Database
- Supabase (Postgres)
- Supabase Auth for authentication
- Supabase Storage for file assets
- Row Level Security (RLS) enforced on all user-scoped tables

## AI / Agent Layer
- Anthropic Claude API (Layer 2, V2+)
- Claude Code Agent tool (Layer 1, V1 runtime — no API key)
- Agent personas: `.md` files in `~/.claude/agents/[role]/persona.md`

## Monorepo
- pnpm workspaces
- Turborepo for build orchestration
- Package imports always use workspace names (`@one-man-show/agents`), never relative cross-package paths

## Testing
- Vitest for unit and integration tests
- Playwright for E2E
- 80% coverage minimum enforced

## Deployment (V2+, not yet active)
- Vercel (frontend + API routes)
- Supabase hosted (database + auth + storage)
