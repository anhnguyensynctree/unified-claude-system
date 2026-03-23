# Session Opening

You are greeting the user at the start of a new Claude Code session. Follow these steps exactly.

## Step 0: Check for active OMS session

Run this to detect if OMS is running autonomously in the current project:

```bash
cat "$(pwd)/.claude/oms.lock" 2>/dev/null
```

**If the lock file exists:**
Read it and display before anything else:

```
⚡ OMS is running in this project
   Step: [step from lock]  |  Started: [X mins ago]  |  PID: [pid]

   a) Observe — keep running, I'll answer questions from logs
   b) Pause after this step — then I'll take over
   c) Just show me the recap — I'll decide later
```

Wait for the user to pick a/b/c before continuing.
- **a**: proceed normally, do not write any lock — observer mode
- **b**: write `$(pwd)/.claude/manual.lock` after confirming step completion
- **c**: continue to Step 1 without locking

**If no lock file:** continue to Step 1.

---

## Step 1: Find the latest handoff

Run this bash command to locate the most recent handoff file:

```bash
ls -t ~/.claude/handoffs/*.tmp 2>/dev/null | head -1
```

## Step 2: Determine session state

**If no handoff file exists OR the file is older than 7 days:**
→ Go to Step 4 (joke mode)

**If a handoff file is found and recent:**
→ Read it, then go to Step 3

## Step 3: Show session recap (rich context)

Extract and display the following in a compact, friendly format:

- **Project** — from the filename (strip date prefix and `-session.tmp`)
- **Last session** — the `## Session Summary` narrative (first non-empty line after the heading, before `---`)
- **Next step** — the `Next:` line from that summary block; fallback to `**Next step:**` line in the handoff tail
- **Left off at** — last user message from the `### Session Tail` block if the summary is sparse

Output format (keep it under 6 lines):

```
Hey! Welcome back.

Project  → [project name]
Last     → [what was done]
Next     → [next step]

Type anything to continue, or /hey again to refresh.
```

Then stop — do not ask questions, do not start working.

## Step 4: No session / fresh start (joke mode)

No prior context found. Greet warmly and tell ONE short developer joke. Keep it under 4 lines total. Examples of good tone (do not copy verbatim — generate a fresh one):

- "Why do programmers prefer dark mode? Because light attracts bugs."
- "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'"
- "There are 10 types of people: those who understand binary and those who don't."

After the joke, output:

```
No recent sessions found. Start fresh — what are we building?
```

## Rules
- Never fabricate session content — only show what's in the file
- If the handoff exists but has no Summary or Next line, fall back to joke mode
- Keep the total output short — this is a greeting, not a report
