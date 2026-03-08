# Fork Init — Load project context in this session

Run in the NEW fork session as your first command to initialize context.

## Steps (execute all, in order)

1. **Read project CLAUDE.md** — look for CLAUDE.md in the current working directory. If found, read it and apply all instructions in it.

2. **Read global CLAUDE.md** — read `~/.claude/CLAUDE.md` and confirm all global rules are active.

3. **Read project memory** — check if `~/.claude/projects/[encoded-cwd]/memory/MEMORY.md` exists and read it. Encode current directory by replacing `/` with `-`.

4. **Load relevant topic files** — read the Topic Index in MEMORY.md and use the Read tool to load any topic files relevant to the current task or project before proceeding.

5. **Read latest session** — find the most recent `.tmp` file in `~/.claude/sessions/` and read it if it has content beyond template headers.

6. **Report loaded context** — output a brief summary:
   - Project name and purpose
   - Current stack
   - What was last worked on (if session had content)
   - What to work on next (based on memory/session)

Then ask: "What do you want to work on?"
