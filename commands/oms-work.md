# oms-work — Execute Cleared Task Queue

**Use `!work` in Discord.** The REPL is not the execution path.

All task execution runs through `oms-work.py` via Discord's `!work` command. This ensures:
- Free model routing via LiteLLM (zero subscription cost)
- Self-correcting retry loop (max 4 attempts with error feedback)
- Quality checks, Verify commands, browse visual verification
- Validator chain (gemma, free)
- Cost tracking, Discord notifications, worktree isolation

## If you need to run from terminal

```bash
# Single task
python3 ~/.claude/bin/oms-work.py <slug> TASK-NNN

# All ready tasks
python3 ~/.claude/bin/oms-work.py <slug> --all

# Dry run
python3 ~/.claude/bin/oms-work.py <slug> --dry-run
```

Always use the Python script directly — never implement task execution inline via Agent tool.
