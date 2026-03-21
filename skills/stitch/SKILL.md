# Stitch — AI UI Generation Skill

Generate, iterate, and track UI screens using Google Stitch. Saves output to `design/stitch/` in the current project. Device type and design profile are inferred automatically from project context.

## Usage

```
/stitch <intent>
/stitch update <screen-name> <change description>
/stitch breakdown <compound description>
/stitch variants <screen-name>
/stitch list
/stitch status
```

## How Claude invokes this skill

All commands run via:
```bash
node ~/.claude/skills/stitch/stitch.mjs <command> [args]
```

## Trigger conditions — Claude fires this autonomously

**Before implementing any new UI component, page, or screen:**
1. Check `design/stitch/manifest.json` — does a screen exist for this view?
2. If yes → `stitch auto "<change description>" --screen <name>` (update mode)
3. If no → `stitch auto "<screen description>"` (generate or breakdown)
4. Read the output HTML before writing any component code — extract colors, spacing, layout patterns

**On first use (no `manifest.json` in project):**
1. Run `stitch init --auto` — reads CLAUDE.md, README.md, PRD.md, docs/** and proposes a style config
2. Present the proposal and reasoning to the user: "Based on your project docs, I'm proposing..."
3. Ask: "Does this match your vision, or would you like to adjust anything?"
4. Apply feedback and run `stitch init --aesthetic "..." --brand "..." --palette "..."`
5. If no docs found (`PROPOSAL_RESULT: no_docs`), ask 3 targeted questions:
   - "What's the vibe/aesthetic? (e.g. minimal, editorial, playful, luxury)"
   - "Any brand/app you'd like the design to feel similar to? (e.g. Linear, Notion, Stripe)"
   - "Do you have a color palette in mind?"

**Trigger `stitch variants` when:**
- User asks to explore design directions or see options
- First screen of a new project (use `--range REIMAGINE` to explore before committing)
- User is unhappy with current output

**Never skip stitch and write component code directly** when a screen for that view exists or is needed.

## Auto-mode decision logic

```bash
node ~/.claude/skills/stitch/stitch.mjs auto "<intent>" [--screen <name>]
```

1. `--screen` hint given + exists in manifest → **UPDATE**
2. Prompt mentions an existing screen name → **UPDATE**
3. Prompt resolves to 2+ screens → **BREAKDOWN** → generate each
4. Default → **GENERATE** new screen

## Command reference

```bash
# First-time project setup — reads docs and proposes style config
node ~/.claude/skills/stitch/stitch.mjs init --auto

# Apply confirmed style config
node ~/.claude/skills/stitch/stitch.mjs init \
  --aesthetic "dark minimal" \
  --brand "similar to Linear" \
  --palette "deep slate, teal accent" \
  --profile product

# Auto mode (Claude default)
node ~/.claude/skills/stitch/stitch.mjs auto "a login page with email and password"
node ~/.claude/skills/stitch/stitch.mjs auto "update the button color" --screen login

# Manual modes
node ~/.claude/skills/stitch/stitch.mjs generate "a dashboard with sidebar nav"
node ~/.claude/skills/stitch/stitch.mjs update login "change button to blue"
node ~/.claude/skills/stitch/stitch.mjs breakdown "full app: login, dashboard, settings"

# Variants — explore design directions
node ~/.claude/skills/stitch/stitch.mjs variants login --range REIMAGINE --count 3
node ~/.claude/skills/stitch/stitch.mjs variants dashboard --range REFINE --aspects COLOR_SCHEME,LAYOUT

# Inspect
node ~/.claude/skills/stitch/stitch.mjs list
node ~/.claude/skills/stitch/stitch.mjs status
```

## Output

All files land in `design/stitch/` relative to the project root:
- `<name>.html` — latest generated HTML
- `<name>.png` — screenshot
- `<name>.v<n>.html` — archived previous versions
- `manifest.json` — screen registry (IDs, prompts, versions, style config)

## API key

Stored at `~/.config/stitch/key` (chmod 600). Loaded automatically — never needs to be set in env.

## Design system rule

`design/stitch/` is the source of truth for all front-end UI. Before implementing any component, check the manifest and use the generated HTML as the visual reference. See `rules/design-system.md`.
