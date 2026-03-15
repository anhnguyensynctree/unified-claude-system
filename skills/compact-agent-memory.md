# Compact Agent Memory

Consolidates agent memory files when they grow too large. Uses Claude Code runtime — no API key required.

## When to Run
- After an `/oms` task when any agent MEMORY.md exceeds 80 lines (oms skill will flag this)
- Manually when an agent's memory feels noisy or redundant
- After a major system change where old patterns are no longer relevant

## Usage
```
/compact-agent-memory              # compact all agents over threshold
/compact-agent-memory cto          # compact a specific agent
```

## Steps

### 1. Check which agents need compacting
```bash
python3 ~/.claude/agents/memory/agent-mem-extract.py check
```

### 2. For each agent to compact — read their current facts
```bash
python3 ~/.claude/agents/memory/agent-mem-extract.py read [role]
```

### 3. Consolidate in context (Claude runtime — no API call)
Read the facts list and consolidate it:
- Merge facts that say the same thing
- Remove facts that are now outdated or superseded
- Tighten wording to under 25 words per fact
- Preserve every unique, actionable insight
- Return the consolidated list as a JSON array of strings

### 4. Write the consolidated facts back
```bash
python3 ~/.claude/agents/memory/agent-mem-extract.py reset [role] "fact 1" "fact 2" ...
```

This replaces all facts with the consolidated set and rebuilds MEMORY.md.

### 5. Spot-check
Read the new MEMORY.md and confirm no important facts were lost. If anything is missing, inject it back:
```bash
python3 ~/.claude/agents/memory/agent-mem-extract.py inject [role] "recovered fact"
```

## Notes
- Uses Claude Code runtime tokens — zero extra API cost
- Safe to run anytime — always spot-check after reset
- For the trainer: compact after it has evaluated 5+ tasks to keep coaching patterns clean
