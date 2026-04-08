# Coding Style Rules — Always Follow

## File Size [ENFORCED: warn-file-size.sh]
- Max 300 lines per file — if approaching, split before continuing
- Max 50 lines per function — extract helpers aggressively
- One responsibility per file
- Never add to a bloated file — refactor first
- Long files force multiple read tool calls and risk losing information mid-read

## Code Quality
- Comments explain WHY not WHAT
- No emojis in codebase
- Never leave console.log in committed code [ENFORCED: block-console-log.sh]
- Never commit commented-out code blocks
- Prefer explicit over clever
- Immutability first — avoid mutation where possible

## Architecture
- Modular: files in hundreds of lines, not thousands
- Reusable utilities, functions, hooks extracted to shared locations
- Entry points stay lean — delegate to modules

## Naming
- Variables and functions: camelCase
- Components and classes: PascalCase
- Constants: UPPER_SNAKE_CASE
- Files: kebab-case (except components: PascalCase)
- Be descriptive — avoid abbreviations unless universally known

## Markdown Quality
Every .md file that exists must meet this standard:
- Must have a # heading
- Minimum 5 lines of substantive content — no stub files
- No unfilled placeholders ([empty], TODO, ...) — complete or remove
- Dense and scannable: no filler, no padded sections
- Each section must earn its place — cut anything decorative
