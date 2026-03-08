# Consolidate Memory

Compress and improve all memory files using a Haiku agent. Routes demoted content to the correct topic file rather than compressing everything into one file.

## Steps

1. **Read all memory files:**
   - `~/.claude/projects/-Users-Lewis/memory/MEMORY.md`
   - All files in `~/.claude/projects/-Users-Lewis/memory/topics/`
   - `~/.claude/projects/-Users-Lewis/memory/insights.md`
   - If in a project: `~/.claude/projects/[encoded-cwd]/memory/MEMORY.md` and its topics/

2. **Launch a Haiku agent** with this task:

   > You are a memory consolidation agent. You receive a set of memory files from a Claude Code tiered memory system. Your job:
   >
   > **MEMORY.md (index file — keep under 80 lines):**
   > - Keep only: user preferences, memory system rules, Topic Index, active context
   > - Move anything domain-specific to the correct topic file
   > - Tag every `##` header with `| importance:high/medium/low`
   >
   > **Topic files (each keep under 100 lines):**
   > - `topics/hooks.md` — hook config, fixes, patterns
   > - `topics/scaffold.md` — scaffold workflow, stack decisions
   > - `topics/agents.md` — agent patterns, model selection, delegation
   > - `topics/debugging.md` — format: `[context] Problem → Cause → Fix`
   > - `topics/patterns.md` — API patterns, architecture decisions
   > - `topics/projects.md` — per-project blocks with stack/status/decisions
   >
   > **insights.md:**
   > - Add any cross-topic patterns that emerged from reviewing all files
   > - Example: "Auth solved same way in 3 projects — see patterns.md"
   >
   > **Rules:**
   > - Merge duplicates across files
   > - Prune: completed one-time setup, superseded decisions, stale tool notes
   > - Never remove: active user preferences, ongoing workflow rules, anything that changes Claude's behaviour
   > - Return each file's new content clearly labelled: `=== MEMORY.md ===`, `=== topics/hooks.md ===`, etc.

   Pass the labelled contents of all files in the agent prompt. Use `model: "haiku"`.

3. **Parse the agent output** and write each section back to its file.

4. **Report:** for each file, lines before → lines after. List what was pruned and what insights were added.
