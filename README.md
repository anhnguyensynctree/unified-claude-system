# unified-claude-system

A production-grade configuration layer for Claude Code CLI. Treats Claude like a senior engineer on a real team: opinionated, consistent, memory-persistent, and cost-aware.

> Built and maintained by [@anhnguyensynctree](https://github.com/anhnguyensynctree)

---

## What This Is

Out of the box, Claude Code is powerful but stateless. Every session starts cold. It doesn't know your project, your conventions, what you fixed yesterday, or what you prefer not to do.

This system solves that:

- **Persistent memory** — Claude remembers what it learned last session
- **Enforced conventions** — rules load automatically, not trusted to per-prompt engineering
- **Automated quality gates** — hooks catch `console.log`, run TypeScript checks, validate .md quality in real time
- **Cost control** — token usage minimized by design throughout every file
- **Skill accumulation** — patterns discovered during work are extracted and reused

The result: Claude behaves like a developer who has worked in your codebase for months.

---

## Directory Structure

```
~/.claude/
├── CLAUDE.md                    ← Global operating instructions (always loaded)
├── settings.json                ← Hook wiring + plugin config + model
├── keybindings.json             ← Custom keyboard shortcuts
├── policy-limits.json           ← Safety constraints
├── statusline-command.sh        ← Custom status line (dir + git branch + ctx%)
│
├── rules/                       ← Domain-specific rules (loaded on demand)
│   ├── coding-style.md          ← File size, naming, quality standards
│   ├── testing.md               ← TDD, 80% coverage, consistency-critical
│   ├── git-workflow.md          ← Conventional commits, branch naming
│   ├── security.md              ← Secrets, injection, immune system pattern
│   ├── performance.md           ← Model selection, token minimization
│   ├── patterns.md              ← API shapes, async, error handling
│   ├── agents.md                ← Delegation, model tiers, dispatch protocol
│   └── hooks.md                 ← Hook reference and documentation
│
├── contexts/                    ← Mode-specific prompts
│   ├── dev.md                   ← Implementation mode
│   ├── review.md                ← Code review mode
│   └── research.md              ← Exploration mode
│
├── commands/                    ← Slash command definitions (/command-name)
│   ├── tdd.md                   ← RED → GREEN → IMPROVE workflow
│   ├── commit.md                ← Conventional commit with safety checks
│   ├── plan.md                  ← 5-phase implementation planning
│   ├── scaffold-project.md      ← Full monorepo bootstrap
│   ├── breakdown.md             ← Task decomposition with model tiers
│   ├── fork.md                  ← Context initialization in new session
│   ├── consolidate-memory.md    ← Haiku-powered memory compression
│   ├── review-pr.md             ← Structured PR review
│   ├── e2e.md                   ← E2E test generation
│   ├── debug.md                 ← Systematic debugging workflow
│   ├── learn.md                 ← Pattern extraction
│   ├── standup.md               ← Git log standup report
│   ├── refactor-clean.md        ← Codebase cleanup
│   ├── test-coverage.md         ← Coverage analysis
│   └── update-codemaps.md       ← Codemap regeneration
│
├── hooks/
│   └── memory-persistence/      ◄★ the memory engine lives here
│       ├── session-start.sh     ← Injects context at session open
│       ├── session-end.sh       ← Persists state at session close
│       ├── pre-compact.sh       ← Saves state before context compaction
│       └── mem0-extract.sh      ← Extracts structured facts from transcripts
│
├── skills/
│   ├── continuous-learning/
│   │   ├── SKILL.md             ← Skill definition
│   │   └── evaluate-session.sh  ← Pattern extraction on Stop hook
│   ├── strategic-compact.md
│   └── codemap-updater.md
│
└── projects/[encoded-path]/memory/   ◄★ per-project persistent memory
    ├── MEMORY.md                ← Always loaded index (<80 lines)
    ├── insights.md              ← Cross-topic patterns from consolidation
    ├── facts.json               ← Structured facts extracted from transcripts
    └── topics/
        ├── agents.md, hooks.md, patterns.md
        ├── scaffold.md, debugging.md, projects.md
        └── archived.md          ← Decayed/contradicted entries (never deleted)
```

---

## ★ Memory Layer — The Core

> Every other component enforces standards. The memory layer is what makes Claude *continuous* — able to carry context, decisions, and learned patterns across sessions without manual re-briefing.

```
Session Start
│
├── MEMORY.md injected (index, <80 lines)
│   └── Topic Index routes full topic files on demand
│
├── ctx: always entries injected inline (zero extra file load)
│   └── model selection, API shapes, error handling, preferences
│
├── facts.json injected (structured facts from past transcripts)
│
└── Previous session notes injected (last 7 days)
```

| Component | What it does | Benefit |
|---|---|---|
| **MEMORY.md index** | Lean routing index | Claude knows what exists without loading everything |
| **Topic files** | Domain-specific memory, loaded on demand | Token cost scales with task, not total knowledge |
| **ctx: always injection** | Critical entries injected at session start without a file load | Always-relevant knowledge in context at near-zero cost |
| **Entry schema** (`importance`, `updated`, `ctx`) | Every entry tagged with priority, age, and scope | Enables automated decay and targeted projection |
| **Decay pruning** | `importance:low` + >90 days → archived, not deleted | Memory stays lean; history is preserved |
| **Dedup + contradiction archiving** | Consolidation merges duplicates, moves old contradicted entries to `archived.md` | No silent overwrites; memory stays coherent |
| **mem0 fact extraction** | Haiku reads session transcript at end, extracts and deduplicates facts | Structured facts persist without manual writes |
| **Session hooks** | Start injects full context; end persists state and warns on size | Every session starts warm; nothing lost between sessions |
| **/consolidate-memory** | Haiku agent merges, prunes, archives, surfaces cross-topic insights | Routine maintenance is automated and cheap |
| **Continuous learning** | Pattern extraction at session end + `/learn` for immediate capture | Non-trivial solutions accumulate as reusable skills |

**Entry schema** — every `##` header in every topic file carries four tags:

```
## Section Name | importance:high | updated: 2026-03-07 | ctx: always
```

`ctx` values: `always` · `agent` · `debug` · `scaffold` · `hook` · `pattern` · `project`

Entries tagged `ctx: always` are extracted and injected at session start without loading their full file. All other entries load only when their domain is active.

---

## Core Components

### CLAUDE.md — The Global Brain

Always loaded. Sets operating mode, token minimization rules, memory routing, context fork strategy, before/after task checklists.

Key behaviors it enforces:
- No preamble, no restating the task, no post-task summaries
- Read files at line ranges, not full files
- Load rules only when domain is active
- Compact after each major phase
- Write tests before marking any task done

### Rules System

Seven domain files, loaded on demand:

| File | Covers |
|---|---|
| `coding-style.md` | Max 300 lines/file, max 50 lines/function, naming conventions |
| `testing.md` | TDD mandatory, 80% coverage, consistency-critical pass^3 rule |
| `git-workflow.md` | Conventional commits, never commit to main |
| `security.md` | No hardcoded secrets, immune system pattern — appends every incident as a new rule |
| `performance.md` | Haiku/Sonnet/Opus tier selection, token minimization |
| `patterns.md` | `{ data, error, meta }` API shape, async/await, import ordering |
| `agents.md` | Delegation protocol, model selection per task type |

### Context Modes

**Directory:** `~/.claude/contexts/`
Loaded by CLAUDE.md when the work type changes. Each file sets Claude's priorities and constraints for that mode.

| Mode | File | Loaded when |
|---|---|---|
| Development | `dev.md` | implementing or building |
| Review | `review.md` | reviewing code or a PR |
| Research | `research.md` | exploring, investigating, planning |

**dev.md** enforces: tests before implementation, no files outside task scope, no skipping tests, TDD order always.

**review.md** enforces structured output:
```
🚨 Blockers  — [file:line] must fix before merge
⚠️  Suggestions — [file:line] should fix
✅  Looks Good  — call out what's done well
```

**research.md** enforces: no file modifications during research phase, saves findings to `sessions/research-[topic].md`, ends every research session with a structured summary (known / unknown / assumptions / next step).

---

### Hooks System

Automated behaviors wired to lifecycle events in `settings.json`:

**PreToolUse:**
- Long-process reminder when npm/pnpm/yarn/cargo/pytest are run
- Hard blocks (exit 2) creating loose `.md` files outside allowed paths
- Git push reminder to run `/review-pr` first

**PostToolUse:**
- Prettier auto-format on every `.ts/.tsx/.js/.jsx` edit
- TypeScript check (`tsc --noEmit`) on every `.ts/.tsx` edit
- Pyright check on every `.py` edit
- `console.log` warning on every file edit
- Markdown quality check (heading, line count, no placeholders)
- mgrep nudge when `grep -r` is used

**Stop / SessionEnd:**
- Session state written to `sessions/YYYY-MM-DD-session.tmp`
- Continuous learning evaluation runs
- `console.log` audit across all modified files
- mem0 fact extraction from session transcript (async)

**SessionStart:**
- Injects project `CLAUDE.md` if found in cwd
- Loads retrieved mem0 facts
- Loads project `MEMORY.md`
- Loads last session notes (within 7 days)

### Memory System — Tiered

```
~/.claude/projects/[encoded-project-path]/memory/
├── MEMORY.md          ← Always loaded (kept under 80 lines)
├── insights.md        ← Cross-topic patterns from consolidation
└── topics/
    ├── debugging.md   ← [context] Problem → Cause → Fix
    ├── patterns.md    ← Architecture decisions, confirmed patterns
    ├── projects.md    ← Per-project blocks
    ├── hooks.md       ← Hook config and fixes
    ├── scaffold.md    ← Scaffold workflow decisions
    ├── agents.md      ← Agent patterns, model selection
    └── archived.md    ← Decayed or contradicted entries (never deleted)
```

MEMORY.md is a lean index. Topic files load only when the domain matches the current task. Memory is compressed by `/consolidate-memory` using a Haiku agent (cost-efficient).

**Entry schema** — every `##` header carries four tags:
```
## Section Name | importance:high | updated: 2026-03-07 | ctx: always
```

| Tag | Values | Purpose |
|---|---|---|
| `importance` | `high/medium/low` | Prune priority — low pruned first |
| `updated` | `YYYY-MM-DD` | Decay tracking — entries not updated in 90+ days and tagged `low` are archived |
| `ctx` | `always`, `agent`, `debug`, `scaffold`, `hook`, `pattern`, `project` | Projection scope |

**Context projection** — entries tagged `ctx: always` are injected at session start without loading their full topic file. All other entries load only when the domain is active. This means critical preferences and patterns are always in context at near-zero token cost.

**Decay and deduplication** — `/consolidate-memory` runs the Haiku agent with three additional passes:
- **Decay prune**: archives entries that are `importance:low` and `updated:` older than 90 days
- **Dedup merge**: finds semantically similar entries across files and merges them into the more recent one
- **Contradiction archive**: when conflicting information is found, keeps the newer version and moves the old to `archived.md` with a timestamp — nothing is silently deleted

### Slash Commands

| Command | What it does |
|---|---|
| `/tdd <task>` | RED → GREEN → IMPROVE with 80% coverage check |
| `/commit` | Conventional commit — stages specific files, shows message for approval |
| `/plan <task>` | 5-phase: research → plan → implement → review → verify |
| `/scaffold-project` | Full monorepo (Next.js + Supabase + pnpm workspaces + Turborepo) |
| `/breakdown <task>` | Decompose into subtasks with model tiers and parallelization flags |
| `/fork` | Initialize context in a new session (loads memory, session, CLAUDE.md) |
| `/review-pr` | Structured review: Blockers / Suggestions / Looks Good with file:line |
| `/pr` | Generate PR description (Summary, Changes, Testing, Breaking Changes) — shows for approval before creating |
| `/consolidate-memory` | Haiku agent compresses all memory files |
| `/learn` | Extract and save a reusable pattern immediately |
| `/debug <issue>` | Systematic debugging workflow |
| `/e2e <flow>` | Playwright E2E tests — data-testid selectors, waitFor patterns, no flakiness |
| `/refactor-clean` | Find unused imports, duplicate logic, oversized files, dead code — proposes before applying |
| `/standup` | `git log --since=yesterday` → Yesterday / Today / Blockers format, max 5 bullets |
| `/test-coverage` | Run coverage report, list files below 80%, write tests for highest-priority gaps |
| `/update-codemaps` | Scan project and write/update `.claude/codemap.md` (max 100 lines, navigation only) |

### mem0 — Structured Fact Extraction

**File:** `memory/mem0.py`
**Requires:** `ANTHROPIC_API_KEY` set in your shell environment

mem0 is a lightweight memory extraction script that runs at session end. It reads the session transcript, uses the Anthropic API (Haiku model) to extract memorable facts, deduplicates them against existing memory, and writes them to `facts.json`. At next session start, those facts are injected into context automatically.

**What it extracts:**
- User preferences and workflow decisions
- Technical choices (tools, frameworks, patterns selected)
- Project context (what you're building, constraints)
- Problems solved or discovered

**How facts are stored:**
```json
[
  {
    "id": "uuid",
    "content": "Prefers pnpm over npm in all projects",
    "created_at": "2026-03-07T...",
    "updated_at": "2026-03-07T..."
  }
]
```

Facts live in `~/.claude/projects/[encoded-project-path]/memory/facts.json` — excluded from this repo by `.gitignore`.

**Setup — required for mem0 to work:**

```bash
# Add to ~/.zshrc or ~/.bashrc
export ANTHROPIC_API_KEY="sk-ant-..."
```

Then reload: `source ~/.zshrc`

Without `ANTHROPIC_API_KEY`, mem0 silently skips extraction (you'll see `[mem0] Set ANTHROPIC_API_KEY in ~/.zshrc to enable extraction` in stderr). The rest of the system works fine without it — only automated fact extraction is disabled.

**Cost:** mem0 uses `claude-haiku-4-5` — the cheapest available model. Extraction runs on the last 80 messages, capped at 600 chars each. Typical cost per session: fractions of a cent.

**Deduplication logic:**
Each new fact is classified as `ADD` (genuinely new), `UPDATE` (refines existing), or `NOOP` (already captured). This prevents duplicate facts from accumulating across sessions.

---

### Skills

**Directory:** `~/.claude/skills/`

Skills are always-available internal behaviors — not slash commands, but loaded context that shapes how Claude operates during sessions.

#### `skills/continuous-learning/`

The pattern extraction system. At every session end, `evaluate-session.sh` fires via the Stop hook, logs session metadata, and prompts for pattern extraction. `SKILL.md` defines what patterns are worth capturing:
- Error resolutions that were non-trivial
- Debugging techniques discovered mid-session
- Project-specific patterns Claude didn't know about
- Corrections you had to make to Claude's default behavior

Learned patterns are saved to `skills/learned/[pattern-name].md` and available in future sessions. Use `/learn` to extract a pattern immediately rather than waiting for session end.

#### `skills/strategic-compact.md`

Documents **when and why** to manually compact context — rather than letting auto-compact fire at arbitrary points mid-task.

When to compact:
- After the exploration phase, before implementation begins
- After a milestone completes, before starting the next
- After 50+ tool calls in a session
- When switching between major features

**Critical:** before running `/compact`, write state to a session file — what was built, what failed, what's pending, key decisions. The session file provides re-entry context after compaction.

#### `skills/codemap-updater.md`

Defines the codemap format and update triggers. Codemaps (`~/.claude/codemap.md`) are project navigation files — max 100 lines, updated at session start, after major refactors, and before compaction.

Format:
```
# Codemap — [Project] — [Date]
## Entry Points   — key files and their purpose
## Key Directories — what lives where
## Architecture   — how pieces connect (5-10 lines)
## Key Files      — files that matter most
## Recently Changed — from git log
```

Why this matters: without a codemap, Claude re-explores the project on every session. A current codemap eliminates that overhead entirely.

---

### Status Line

**File:** `statusline-command.sh`
**Config:** `settings.json` → `statusLine`

Displays a live status bar inside Claude Code, styled after the robbyrussell oh-my-zsh theme:

```
my-project  git:(feat/auth) ✗  ctx:34%  claude-sonnet-4-6
```

- **Directory name** — current working directory basename
- **Git branch** — current branch with dirty state indicator (`✗` if uncommitted changes)
- **Context usage** — percentage of context window used (green < 50%, yellow < 80%, red ≥ 80%)
- **Model name** — active model

Color coding on context usage lets you know when to manually compact before auto-compact fires mid-task.

---

### Policy Limits

**File:** `policy-limits.json`

```json
{
  "restrictions": {
    "allow_remote_control": { "allowed": false }
  }
}
```

Disables remote control of Claude Code — prevents any external process or MCP server from programmatically driving Claude actions without your direct involvement. Security constraint, not a workflow setting.

---

### Plugins (Active)

| Plugin | Purpose |
|---|---|
| `hookify` | GUI for creating and managing hooks |
| `context7` | Up-to-date library documentation in context |
| `mgrep` | Semantic search — replaces `grep -r`, ~50% token reduction |
| `pyright-lsp` | Python type checking on edit |

TypeScript LSP, code-review, and security-guidance plugins are scoped **per package** in per-project `settings.json` — only loaded where needed.

---

## The Philosophy

**1. Rules enforced > rules asked for**
Putting standards in CLAUDE.md + hooks + checklists means they apply even when you forget to say them. No per-prompt reminders needed.

**2. Separation of concerns on context cost**
Every file loaded costs tokens. Rules load on demand. Memory is tiered. Plugins are scoped per package. The overhead at session start is minimal; richness is available when needed.

**3. Context forking as a first-class tool**
Long conversations drift. `/fork` treats context as a resource. When work branches, fork, flush state to memory, start lean.

**4. The system learns**
Security incidents get appended to `rules/security.md`. Bug fixes go to `topics/debugging.md`. Non-trivial solutions are extracted with `/learn`. The configuration becomes an immune system.

**5. Cost-tiered agents**
- Haiku — repetitive tasks, worker agents, memory consolidation (5x cheaper than Opus)
- Sonnet — default for 90% of coding tasks
- Opus — first attempt failed, 5+ files, architectural decisions, security-critical

---

## Setup

Choose your platform:
- [macOS](#macos-setup)
- [Windows (via WSL2)](#windows-setup-via-wsl2)

> **Note:** Claude Code has no native Windows binary. Windows users must run it inside WSL2 (Ubuntu). All bash hooks and scripts work inside WSL.

---

## macOS Setup

### Step 1 — Install Claude Code CLI

Go to [claude.ai/code](https://claude.ai/code) and follow the install instructions for macOS.

Verify it works:
```bash
claude --version
```

### Step 2 — Install prerequisites

```bash
# Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Required tools
brew install jq          # JSON parsing used by all hooks
brew install gh          # GitHub CLI (for /pr, /review-pr workflows)
brew install node        # Node.js — for prettier + tsc
brew install python3     # Python 3 — for mem0 fact extraction
```

Verify:
```bash
jq --version && gh --version && node --version && python3 --version
```

### Step 3 — Back up your existing ~/.claude (if any)

```bash
[ -d ~/.claude ] && mv ~/.claude ~/.claude.backup && echo "Backed up to ~/.claude.backup"
```

Skip this step if `~/.claude` doesn't exist yet.

### Step 4 — Clone this repo into ~/.claude

```bash
git clone https://github.com/anhnguyensynctree/unified-claude-system.git ~/.claude
```

### Step 5 — Make hooks executable

```bash
chmod +x ~/.claude/hooks/memory-persistence/*.sh
chmod +x ~/.claude/skills/continuous-learning/evaluate-session.sh
```

### Step 6 — Set your ANTHROPIC_API_KEY (for mem0)

mem0 fact extraction calls the Anthropic API directly using Haiku. Without this key, fact extraction is silently skipped — everything else works fine.

```bash
# Add to your shell config
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.zshrc
source ~/.zshrc
```

Replace `sk-ant-...` with your actual key from [console.anthropic.com](https://console.anthropic.com).

### Step 7 — Initialize your global memory

```bash
mkdir -p ~/.claude/projects/-Users-$(whoami)/memory/topics
```

Create the memory index file:
```bash
cat > ~/.claude/projects/-Users-$(whoami)/memory/MEMORY.md << 'EOF'
# Memory Index

Always loaded at session start. Read the Topic Index and load relevant files before starting work.

## User Preferences | importance:high
- [Add your preferences here — e.g. "Prefers pnpm over npm"]

## Active Context | importance:high
- Setup complete

## Topic Index | importance:high
Load with Read tool when task domain matches:

| When... | Load |
|---|---|
| Hitting errors, non-obvious fixes | topics/debugging.md |
| Architecture or API decisions | topics/patterns.md |
EOF
```

Create empty topic files:
```bash
cat > ~/.claude/projects/-Users-$(whoami)/memory/topics/debugging.md << 'EOF'
# Debugging

## Format
`[context] Problem → Cause → Fix`

## Entries
<!-- Populated as non-obvious bugs are solved -->
EOF

cat > ~/.claude/projects/-Users-$(whoami)/memory/topics/patterns.md << 'EOF'
# Patterns

## Architecture Decisions
<!-- Populated as decisions are made -->

## What Works
<!-- Confirmed patterns -->

## Known Gotchas
<!-- Non-obvious behaviour -->
EOF
```

### Step 8 — Install Claude Code plugins

Open Claude Code and run:
```
/plugins
```

Install these plugins:
- `hookify@claude-plugins-official`
- `context7@claude-plugins-official`
- `mgrep@Mixedbread-Grep`
- `pyright-lsp@claude-plugins-official` (if you use Python)

The `settings.json` already has these configured — installing them activates them.

### Step 9 — Verify hooks are wired

Open Claude Code. You should see in the session start output:
```
## Project Memory
...
```

If you see that block, the session-start hook is running correctly.

### Step 10 — First session

Run your first command:
```
/fork
```

Claude loads all context (global CLAUDE.md + memory + any recent session) and asks what you want to work on. You're live.

---

## Windows Setup (via WSL2)

Claude Code runs inside WSL2 on Windows. All bash hooks, scripts, and tools run in the Linux environment.

### Step 1 — Enable WSL2

Open PowerShell as Administrator and run:
```powershell
wsl --install
```

This installs WSL2 with Ubuntu by default. Restart your machine when prompted.

Open the Ubuntu app from the Start menu and complete the Ubuntu setup (create a username and password).

Verify:
```bash
wsl --version
```

### Step 2 — Install Claude Code CLI inside WSL

Open your Ubuntu terminal and follow the Linux install instructions at [claude.ai/code](https://claude.ai/code).

Verify:
```bash
claude --version
```

> All remaining steps run **inside the Ubuntu/WSL terminal**, not in PowerShell or CMD.

### Step 3 — Install prerequisites inside WSL

```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# jq — JSON parsing used by all hooks
sudo apt install -y jq

# Python 3 — for mem0 fact extraction
sudo apt install -y python3 python3-pip

# Node.js — for prettier + tsc
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# GitHub CLI
sudo apt install -y gh
gh auth login
```

Verify:
```bash
jq --version && gh --version && node --version && python3 --version
```

### Step 4 — Back up your existing ~/.claude (if any)

```bash
[ -d ~/.claude ] && mv ~/.claude ~/.claude.backup && echo "Backed up to ~/.claude.backup"
```

### Step 5 — Clone this repo into ~/.claude

```bash
git clone https://github.com/anhnguyensynctree/unified-claude-system.git ~/.claude
```

### Step 6 — Make hooks executable

```bash
chmod +x ~/.claude/hooks/memory-persistence/*.sh
chmod +x ~/.claude/skills/continuous-learning/evaluate-session.sh
```

### Step 7 — Disable the macOS notification hook

The `Notification` hook in `settings.json` uses `osascript`, which is macOS-only. On WSL you need to remove it or it will throw errors silently.

Open the settings file:
```bash
nano ~/.claude/settings.json
```

Find and delete this entire block:
```json
"Notification": [
  {
    "matcher": "",
    "hooks": [
      {
        "type": "command",
        "command": "osascript -e 'display notification \"Claude needs your attention\" with title \"Claude Code\"' 2>/dev/null || true"
      }
    ]
  }
],
```

Save and exit (`Ctrl+X`, then `Y`, then `Enter`).

> Optional: replace it with a WSL-compatible notification using `notify-send` if you want alerts:
> ```bash
> "command": "notify-send 'Claude Code' 'Claude needs your attention' 2>/dev/null || true"
> ```
> Requires `sudo apt install -y libnotify-bin`.

### Step 8 — Set your ANTHROPIC_API_KEY (for mem0)

```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.bashrc
source ~/.bashrc
```

Replace `sk-ant-...` with your actual key from [console.anthropic.com](https://console.anthropic.com).

### Step 9 — Initialize your global memory

On WSL/Linux, your home path is `/home/username` — the encoded memory path uses `-home-` not `-Users-`.

```bash
mkdir -p ~/.claude/projects/-home-$(whoami)/memory/topics
```

Create the memory index file:
```bash
cat > ~/.claude/projects/-home-$(whoami)/memory/MEMORY.md << 'EOF'
# Memory Index

Always loaded at session start. Read the Topic Index and load relevant files before starting work.

## User Preferences | importance:high
- [Add your preferences here]

## Active Context | importance:high
- Setup complete

## Topic Index | importance:high
| When... | Load |
|---|---|
| Hitting errors, non-obvious fixes | topics/debugging.md |
| Architecture or API decisions | topics/patterns.md |
EOF
```

Create empty topic files:
```bash
cat > ~/.claude/projects/-home-$(whoami)/memory/topics/debugging.md << 'EOF'
# Debugging

## Format
`[context] Problem → Cause → Fix`

## Entries
<!-- Populated as non-obvious bugs are solved -->
EOF

cat > ~/.claude/projects/-home-$(whoami)/memory/topics/patterns.md << 'EOF'
# Patterns

## Architecture Decisions
<!-- Populated as decisions are made -->

## What Works
<!-- Confirmed patterns -->

## Known Gotchas
<!-- Non-obvious behaviour -->
EOF
```

### Step 10 — Fix the session-start memory path

The `session-start.sh` hook reads global facts from a hardcoded path pattern. On Linux/WSL it will encode your home as `-home-username`, which the script handles automatically — no change needed.

Verify the hook runs correctly after setup:
```bash
bash ~/.claude/hooks/memory-persistence/session-start.sh
```

You should see `## Project Memory` in the output with no errors.

### Step 11 — Install Claude Code plugins

Open Claude Code (inside WSL) and run:
```
/plugins
```

Install:
- `hookify@claude-plugins-official`
- `context7@claude-plugins-official`
- `mgrep@Mixedbread-Grep`
- `pyright-lsp@claude-plugins-official` (if you use Python)

### Step 12 — First session

Run:
```
/fork
```

Claude loads all context and asks what you want to work on.

---

## Verify Your Installation

Run this checklist after setup on either platform:

```bash
# 1. Hooks are executable
ls -la ~/.claude/hooks/memory-persistence/
# All .sh files should show -rwxr-xr-x

# 2. Memory directory exists
ls ~/.claude/projects/
# Should show your encoded home path directory

# 3. MEMORY.md is readable
cat ~/.claude/projects/*/memory/MEMORY.md
# Should show the Memory Index content

# 4. ANTHROPIC_API_KEY is set (optional but recommended)
echo $ANTHROPIC_API_KEY
# Should show your key (sk-ant-...)

# 5. Prerequisites installed
jq --version && node --version && python3 --version
```

---

## Keeping Your Config Up to Date

This repo evolves. Pull updates without losing your personal memory:

```bash
cd ~/.claude
git pull origin main
```

Your `projects/` directory (personal memory and sessions) is gitignored — it will never be touched by a pull.

If you've customized `settings.json` or `CLAUDE.md`, review the diff before pulling:
```bash
cd ~/.claude
git fetch origin
git diff origin/main -- settings.json CLAUDE.md
```

---

## Workflows

```bash
# Start a new day
/fork

# Implement a feature with TDD
/tdd add payment webhook handler

# Plan a complex task
/plan refactor authentication system

# Commit cleanly
/commit

# Review a PR before merge
/review-pr

# Extract a pattern you just solved
/learn

# Compress memory when it grows
/consolidate-memory
```

---

## Iterating and Contributing

This repo **is** `~/.claude`. Updating the system:

```bash
cd ~/.claude
# make changes to any config file
git add rules/testing.md  # or whichever file changed
git commit -m "feat(testing): raise coverage threshold to 85%"
git push
```

PRs and issues welcome. If you adapt this for a different stack, open a PR — especially for non-Next.js/Supabase scaffold variants.

---

## License

MIT
