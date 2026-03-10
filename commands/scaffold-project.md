# Scaffold Project

Bootstrap a new monorepo project. Ask me these questions first:

1. Project name (kebab-case, e.g. `my-app`)
2. Primary purpose (one sentence: what does this do)
3. Key external services (e.g. Stripe, GitHub API — Supabase and Next.js are always included)
4. Any additional apps or packages beyond the defaults? (e.g. `apps/api`, `packages/analytics`)

Then execute ALL steps below in order.

---

## Monorepo Structure (Always This Layout)

Industry standard: `apps/` for deployable applications, `packages/` for shared code.

```
[project-name]/
  CLAUDE.md
  package.json                   <- workspace root (pnpm workspaces)
  pnpm-workspace.yaml
  turbo.json
  .claude/
    settings.json                <- root: hookify + context7 + mgrep only
    sessions/
    codemap.md
    memory/
      MEMORY.md                  <- project index (always loaded)
      insights.md                <- cross-topic insights from consolidation
      topics/
        debugging.md             <- [context] Problem → Cause → Fix
        patterns.md              <- architecture decisions
        projects.md              <- (optional, for multi-service repos)

  apps/
    web/                         <- Next.js app
      CLAUDE.md
      package.json
      .claude/
        settings.json            <- typescript-lsp + code-review

  packages/
    ui/                          <- Reusable styled components (shadcn/ui base)
      CLAUDE.md
      package.json
      .claude/
        settings.json            <- typescript-lsp

    database/                    <- Supabase client, schema, migrations
      CLAUDE.md
      package.json
      .claude/
        settings.json            <- typescript-lsp + security-guidance

    config/                      <- Shared tsconfig, eslint, prettier configs
      package.json
      tsconfig.base.json
      .eslintrc.base.js
```

If the user requested additional apps or packages, add them following the same pattern.

**Whenever a package is added at any point in the project's life, the root `CLAUDE.md` Packages table must be updated to include it.** This is the single source of truth for monorepo structure.

---

## Step 1 — Create directory structure and config files

Create all directories and the following files:

### Root `package.json`
```json
{
  "name": "[project-name]",
  "private": true,
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint",
    "format": "prettier --write \"**/*.{ts,tsx,js,jsx,json,md}\""
  },
  "devDependencies": {
    "turbo": "latest",
    "prettier": "latest",
    "typescript": "latest"
  },
  "packageManager": "pnpm@latest"
}
```

### `pnpm-workspace.yaml`
```yaml
packages:
  - "apps/*"
  - "packages/*"
```

### `turbo.json`
```json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": { "dependsOn": ["^build"], "outputs": [".next/**", "dist/**"] },
    "dev": { "cache": false, "persistent": true },
    "test": { "dependsOn": ["^build"] },
    "lint": {}
  }
}
```

### Root `CLAUDE.md`
```markdown
# Project: [project-name]

## Purpose
[one sentence from answers]

## Packages

<!-- KEEP THIS SECTION IN SYNC — update whenever a package is added or removed -->

| Path | Name | Purpose |
|------|------|---------|
| `apps/web` | `@[project-name]/web` | Next.js frontend |
| `packages/ui` | `@[project-name]/ui` | Shared component library (shadcn/ui base) |
| `packages/database` | `@[project-name]/database` | Supabase client, schema, migrations |
| `packages/config` | `@[project-name]/config` | Shared tsconfig, eslint, prettier |

## Stack
- Runtime: Node.js, TypeScript
- Frontend: Next.js (App Router), Tailwind CSS
- UI: shadcn/ui (packages/ui)
- Database: Supabase (Postgres + Auth + Storage)
- Monorepo: pnpm workspaces + Turborepo
- Services: [services from answers, or "none beyond Supabase"]

## Commands
- Install: `pnpm install`
- Dev: `pnpm dev`
- Test: `pnpm test`
- Lint: `pnpm lint`
- Build: `pnpm build`

## Conventions
- Branch naming: `feat/`, `fix/`, `chore/`, `refactor/`
- Imports: always use package name (`@[project-name]/ui`) — never relative cross-package
- Components: PascalCase files in `packages/ui/src/components/`
- DB types: generated from Supabase in `packages/database/src/types.ts`

## Key Files
- `apps/web/app/layout.tsx` — root layout
- `packages/ui/src/index.ts` — UI package entry point
- `packages/database/src/client.ts` — Supabase client singleton

## What Claude Often Gets Wrong Here
[populate as issues arise]
```

### `apps/web/CLAUDE.md`
```markdown
# apps/web — Next.js App

## Purpose
Main user-facing web application.

## Stack
Next.js App Router, TypeScript, Tailwind CSS, `@[project-name]/ui`

## Commands
- Dev: `pnpm dev`
- Build: `pnpm build`
- Test: `pnpm test`
- Lint: `pnpm lint`

## Conventions
- Pages in `app/` using App Router conventions
- Server Components by default — mark `"use client"` only when necessary
- Import UI from `@[project-name]/ui`, DB utils from `@[project-name]/database`

## Key Files
- `app/layout.tsx` — root layout and providers
- `app/page.tsx` — home page

## What Claude Often Gets Wrong Here
[populate as issues arise]
```

### `packages/ui/CLAUDE.md`
```markdown
# packages/ui — Component Library

## Purpose
Shared, reusable styled components consumed by all apps.

## Stack
React, TypeScript, Tailwind CSS, shadcn/ui primitives

## Commands
- Build: `pnpm build`
- Dev (watch): `pnpm dev`

## Conventions
- One component per file in `src/components/`
- Export everything from `src/index.ts`
- No app-specific logic — this package must stay generic
- Variants via `cva` (class-variance-authority)

## Key Files
- `src/index.ts` — package entry point
- `src/components/` — all components

## What Claude Often Gets Wrong Here
[populate as issues arise]
```

### `packages/database/CLAUDE.md`
```markdown
# packages/database — Supabase Layer

## Purpose
Supabase client, type-safe schema, and shared DB utilities.

## Stack
Supabase JS SDK, TypeScript, generated types from `supabase gen types`

## Commands
- Generate types: `pnpm supabase gen types typescript --local > src/types.ts`
- Migrations: `pnpm supabase db push`

## Conventions
- Single client singleton in `src/client.ts`
- All DB queries go through typed helpers — never raw SQL strings in apps
- RLS must be configured for every table — never bypass
- Never expose service-role key outside this package

## Key Files
- `src/client.ts` — Supabase client
- `src/types.ts` — generated DB types
- `supabase/migrations/` — schema migrations

## What Claude Often Gets Wrong Here
[populate as issues arise]
```

---

## Step 2 — Create per-package `.claude/settings.json`

### Root `.claude/settings.json` — context tools only, no LSP
```json
{
  "enabledPlugins": {
    "hookify@claude-plugins-official": true,
    "context7@claude-plugins-official": true,
    "mgrep@Mixedbread-Grep": true,
    "typescript-lsp@claude-plugins-official": false,
    "pyright-lsp@claude-plugins-official": false,
    "code-review@claude-plugins-official": false,
    "security-guidance@claude-plugins-official": false,
    "commit-commands@claude-plugins-official": false
  }
}
```

### `apps/web/.claude/settings.json` — TS + code review
```json
{
  "enabledPlugins": {
    "hookify@claude-plugins-official": true,
    "context7@claude-plugins-official": true,
    "mgrep@Mixedbread-Grep": true,
    "typescript-lsp@claude-plugins-official": true,
    "pyright-lsp@claude-plugins-official": false,
    "code-review@claude-plugins-official": true,
    "security-guidance@claude-plugins-official": false,
    "commit-commands@claude-plugins-official": false
  }
}
```

### `packages/ui/.claude/settings.json` — TS only
```json
{
  "enabledPlugins": {
    "hookify@claude-plugins-official": true,
    "context7@claude-plugins-official": true,
    "mgrep@Mixedbread-Grep": true,
    "typescript-lsp@claude-plugins-official": true,
    "pyright-lsp@claude-plugins-official": false,
    "code-review@claude-plugins-official": false,
    "security-guidance@claude-plugins-official": false,
    "commit-commands@claude-plugins-official": false
  }
}
```

### `packages/database/.claude/settings.json` — TS + security (handles auth + PII)
```json
{
  "enabledPlugins": {
    "hookify@claude-plugins-official": true,
    "context7@claude-plugins-official": true,
    "mgrep@Mixedbread-Grep": true,
    "typescript-lsp@claude-plugins-official": true,
    "pyright-lsp@claude-plugins-official": false,
    "code-review@claude-plugins-official": false,
    "security-guidance@claude-plugins-official": true,
    "commit-commands@claude-plugins-official": false
  }
}
```

For any additional packages added by the user, apply this rule table:

| Package type                        | Plugins to enable beyond base     |
|-------------------------------------|-----------------------------------|
| Any app (`apps/*`)                  | typescript-lsp, code-review       |
| UI / design package                 | typescript-lsp                    |
| Auth, payments, data, storage       | typescript-lsp, security-guidance |
| API / server package                | typescript-lsp, security-guidance |
| Config / tooling only               | (none beyond base)                |

---

## Step 3 — Initialize project memory

Determine the absolute path of the project root. Compute the encoded path:
- Take the absolute path, replace each `/` with `-`
- Example: `/Users/Annie/projects/my-app` → `-Users-Annie-projects-my-app`
- Memory root: `~/.claude/projects/[encoded-path]/memory/`

Create the full tiered memory structure:

**`~/.claude/projects/[encoded-path]/memory/MEMORY.md`**
```markdown
# Memory Index: [project-name]

Always loaded at session start. Read Topic Index and load relevant files before starting work.

## Identity | importance:high
- Stack: Next.js, TypeScript, Supabase, Tailwind CSS, shadcn/ui
- Monorepo: pnpm workspaces + Turborepo
- Purpose: [purpose]
- Services: [services]
- Packages: apps/web, packages/ui, packages/database, packages/config

## Active Context | importance:high
- Status: just scaffolded
- What's next: pnpm install, then begin first feature

## Topic Index | importance:high
Load with Read tool when task domain matches:

| When... | Load |
|---|---|
| Hitting errors, non-obvious fixes | `~/.claude/projects/[encoded-path]/memory/topics/debugging.md` |
| Architecture or API decisions | `~/.claude/projects/[encoded-path]/memory/topics/patterns.md` |
| Cross-topic insights (from consolidation) | `~/.claude/projects/[encoded-path]/memory/insights.md` |
```

**`~/.claude/projects/[encoded-path]/memory/topics/debugging.md`**
```markdown
# Debugging: [project-name]

## Format
`[context] Problem → Cause → Fix`

## Entries
<!-- Populated as non-obvious bugs are solved -->
```

**`~/.claude/projects/[encoded-path]/memory/topics/patterns.md`**
```markdown
# Patterns: [project-name]

## Architecture Decisions
<!-- Populated as decisions are made -->

## What Works
<!-- Confirmed patterns for this project -->

## Known Gotchas
<!-- Non-obvious behaviour specific to this stack/project -->
```

**`~/.claude/projects/[encoded-path]/memory/insights.md`**
```markdown
# Insights: [project-name]

Cross-topic patterns generated by /consolidate-memory.

## Insights
<!-- Populated by consolidation agent -->
```

---

## Step 4 — Print handoff message

After all files are created, print exactly:

```
Scaffold complete: [project-name]

Monorepo layout:
  apps/web              → Next.js (typescript-lsp + code-review)
  packages/ui           → Components (typescript-lsp)
  packages/database     → Supabase (typescript-lsp + security-guidance)
  packages/config       → Shared tooling

Memory initialized at:
  ~/.claude/projects/[encoded-path]/memory/
    MEMORY.md        ← index, always loaded
    insights.md      ← cross-topic insights
    topics/
      debugging.md   ← errors + fixes
      patterns.md    ← architecture decisions

Next:
  1. cd [project-name] && pnpm install
  2. Open a new Claude Code session in the project directory
  3. Run /fork as your first command — it loads CLAUDE.md, memory, and session context
  4. Tell it what to work on first
```
