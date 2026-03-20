---
name: consolidate-facts
description: Consolidate bloated facts.json files across all projects. Run when health check warns about facts over threshold.
---
# Consolidate Facts

Merges and deduplicates facts.json files that have grown past the 40-fact threshold.

## Usage
```
/consolidate-facts          # consolidate all bloated projects
```

## Steps

### 1. Find bloated projects
```bash
find ~/.claude/projects -name "facts.json" | while read f; do
  count=$(python3 -c "import json; print(len(json.load(open('$f'))))" 2>/dev/null)
  [ "$count" -gt 40 ] && echo "$count $f"
done | sort -rn
```

### 2. Consolidate each bloated file
```bash
python3 ~/.claude/hooks/memory-persistence/mem0.py consolidate <facts_path> --force
```

If the call fails with a JSON parse error (very large files), the issue is output truncation.
This is already fixed with `max_tokens: 4096` in `api_call()` — a single `--force` call should
always succeed now.

### 3. Verify result
```bash
python3 -c "import json; d=json.load(open('<facts_path>')); print(len(d), 'facts remaining')"
```

### 4. Confirm health check passes
Re-run health check to confirm no more bloat warnings:
```bash
~/.claude/hooks/memory-persistence/health-check.sh
```

## Notes
- Consolidation target: 25 facts max per project
- Uses Haiku — costs ~$0.001 per consolidation run
- Safe to run anytime — existing facts.json is overwritten only on success
- If API fails, facts.json is left unchanged
