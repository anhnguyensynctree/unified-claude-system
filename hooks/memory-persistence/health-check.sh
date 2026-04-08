#!/bin/bash
# health-check.sh — validates structural integrity of the unified Claude system
# Runs on every SessionStart. Prints nothing if healthy. Warns loudly on failure.
# Never blocks context output — all output goes to stderr.

CLAUDE_DIR="$HOME/.claude"
HOOKS_DIR="$CLAUDE_DIR/hooks/memory-persistence"
SETTINGS="$CLAUDE_DIR/settings.json"
PASS=0
FAIL=0

warn() { echo "[HealthCheck] WARN: $*" >&2; ((FAIL++)); }
ok()   { ((PASS++)); }

# ── 0. mem0 retry — re-run any steps that failed last session ────────────────
RETRY_FILE="$HOME/.claude/logs/mem0-retry.json"
if [ -f "$RETRY_FILE" ]; then
  FAILED_STEPS_LIST=$(python3 -c "import json; d=json.load(open('$RETRY_FILE')); print(', '.join(d.get('failed_steps', [])))" 2>/dev/null)
  warn "mem0 steps failed last session: ${FAILED_STEPS_LIST:-unknown} — retrying now"

  RETRY_RESULT=$(python3 - "$RETRY_FILE" "$HOOKS_DIR/mem0.py" 2>&1 <<'PYEOF'
import json, subprocess, sys, os

retry = json.load(open(sys.argv[1]))
mem0  = sys.argv[2]
tp    = retry.get("transcript_path", "")
proj  = retry.get("project", "")
date  = retry.get("date", "")
steps = retry.get("failed_steps", [])

if not os.path.exists(tp):
    print(f"SKIP: transcript no longer available ({tp})")
    sys.exit(0)

args_map = {
    "handoff":      ["handoff", tp, date, proj],
    "extract":      ["extract", tp],
    "learn":        ["learn",   tp],
    "check-memory": ["check-memory"],
}

still_failing = []
for step in steps:
    if step not in args_map:
        print(f"FAIL: unknown step '{step}'")
        still_failing.append(step)
        continue
    r = subprocess.run(["python3", mem0] + args_map[step], capture_output=True, text=True, timeout=20)
    if r.returncode != 0:
        print(f"FAIL: {step} — {r.stderr.strip()[:200]}")
        still_failing.append(step)
    else:
        print(f"OK: {step}")

if still_failing:
    sys.exit(1)
PYEOF
  )

  if echo "$RETRY_RESULT" | grep -q "^FAIL:"; then
    while IFS= read -r line; do
      [[ "$line" == FAIL:* ]] && warn "mem0 retry ${line#FAIL: }"
    done <<< "$RETRY_RESULT"
  else
    echo "[HealthCheck] mem0 retry complete — all steps recovered" >&2
    ((PASS++))
  fi

  rm -f "$RETRY_FILE"
fi

# ── 1. settings.json — exists and is valid JSON ──────────────────────────────
if [ ! -f "$SETTINGS" ]; then
  warn "settings.json not found at $SETTINGS"
else
  if ! python3 -c "import json; json.load(open('$SETTINGS'))" 2>/dev/null; then
    warn "settings.json is not valid JSON"
  else
    ok

    # ── 2. Hook structure — every hook object must have 'matcher' and 'hooks' ─
    python3 - "$SETTINGS" <<'PYEOF' 2>&1 | while IFS= read -r line; do warn "$line"; done
import json, sys
settings = json.load(open(sys.argv[1]))

for event, entries in settings.get("hooks", {}).items():
    if not isinstance(entries, list):
        print(f"hooks.{event} must be an array")
        continue
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            print(f"hooks.{event}[{i}] must be an object")
            continue
        if "matcher" not in entry:
            print(f"hooks.{event}[{i}] missing 'matcher' field")
        if "hooks" not in entry:
            print(f"hooks.{event}[{i}] missing 'hooks' field")
            continue
        for j, h in enumerate(entry.get("hooks", [])):
            if "type" not in h:
                print(f"hooks.{event}[{i}].hooks[{j}] missing 'type'")
            if h.get("type") == "command" and "command" not in h:
                print(f"hooks.{event}[{i}].hooks[{j}] type=command but no 'command' field")
PYEOF

    # ── 3. Command paths — every hook command must point to an existing file ──
    python3 - "$SETTINGS" <<'PYEOF' 2>&1 | while IFS= read -r line; do warn "$line"; done
import json, sys, os, re, shutil
settings = json.load(open(sys.argv[1]))
home = os.path.expanduser("~")

for event, entries in settings.get("hooks", {}).items():
    for entry in entries if isinstance(entries, list) else []:
        for h in entry.get("hooks", []) if isinstance(entry, dict) else []:
            cmd = h.get("command", "")
            if not cmd:
                continue
            # Extract the first token (the executable), expand ~ and $HOME
            first = cmd.split()[0]
            first = first.replace("$HOME", home).replace("~", home)
            # Skip inline shell expressions
            if first.startswith(("jq", "echo", "osascript", "git", "npx",
                                  "notify-send", "powershell", "python3",
                                  "FILE=", "rm", "grep", "find", "bash")):
                continue
            if first.startswith("/") and not os.path.exists(first):
                print(f"hooks.{event} command path not found: {first}")
            elif first.startswith("/") and not os.access(first, os.X_OK):
                print(f"hooks.{event} command not executable: {first}")
PYEOF
  fi
fi

# ── 4. Shell scripts — syntax and permissions ─────────────────────────────────
for dir in "$HOOKS_DIR" "$CLAUDE_DIR/hooks"; do
  for script in "$dir"/*.sh; do
    [ -f "$script" ] || continue
    name=$(basename "$script")
    if ! bash -n "$script" 2>/dev/null; then
      warn "$name has bash syntax errors"
    else
      ok
    fi
    if [ ! -x "$script" ]; then
      warn "$name is not executable (run: chmod +x $script)"
    else
      ok
    fi
  done
done

# ── 4b. Enforcement hooks — verify required hooks are registered ──────────────
REQUIRED_HOOKS=(
  "enforce-bare-model.sh"
  "enforce-commit-format.sh"
  "block-coauthor.sh"
  "enforce-llms-read.sh"
  "enforce-test-exists.sh"
  "enforce-plan-mode.sh"
  "smart-grep-route.sh"
  "warn-file-size.sh"
  "block-console-log.sh"
)
for hook in "${REQUIRED_HOOKS[@]}"; do
  HOOK_PATH="$CLAUDE_DIR/hooks/$hook"
  if [ ! -f "$HOOK_PATH" ]; then
    warn "Required enforcement hook missing: $hook"
  elif ! grep -q "$hook" "$SETTINGS" 2>/dev/null; then
    warn "Hook exists but not registered in settings.json: $hook"
  else
    ok
  fi
done

# ── 5. mem0.py — Python syntax valid ─────────────────────────────────────────
MEM0="$HOOKS_DIR/mem0.py"
if [ ! -f "$MEM0" ]; then
  warn "mem0.py not found at $MEM0"
elif ! python3 -c "import ast; ast.parse(open('$MEM0').read())" 2>/dev/null; then
  warn "mem0.py has Python syntax errors"
else
  ok
fi

# ── 6. Auth mode — subscription (keychain) or API key ───────────────────────
KEY_FILE="$HOME/.config/anthropic/key"
if [ -f "$KEY_FILE" ] && [ -s "$KEY_FILE" ]; then
  ok  # API key user — mem0 will load from ~/.config/anthropic/key
else
  ok  # Subscription user — mem0 uses claude keychain OAuth (no key file needed)
fi

# ── 7. facts.json — valid JSON + consolidation check (current project + global only) ──
CWD_ENCODED=$(python3 -c "import sys; print('$(pwd)'.replace('/', '-').replace('.', '-'))")
PROJECT_FACTS="$CLAUDE_DIR/projects/$CWD_ENCODED/memory/facts.json"
HOME_ENCODED=$(echo "$HOME" | sed 's|/|-|g')
GLOBAL_FACTS="$CLAUDE_DIR/projects/$HOME_ENCODED/memory/facts.json"

for f in "$PROJECT_FACTS" "$GLOBAL_FACTS"; do
  [ -f "$f" ] || continue
  result=$(python3 -c "
import json
try:
    d = json.load(open('$f'))
    if not isinstance(d, list):
        print('corrupted')
    elif len(d) > 40:
        print(len(d))
    else:
        print('ok')
except Exception:
    print('corrupted')
" 2>/dev/null)
  if [ "$result" = "corrupted" ]; then
    warn "Corrupted facts.json: $f"
  elif [ "$result" != "ok" ]; then
    project=$(basename "$(dirname "$(dirname "$f")")")
    warn "facts.json bloated ($result facts, threshold 40): $project — run /consolidate-facts"
  fi
done

# ── 7b. Memory topic files — check for bloat (>100 lines threshold) ──────────
for dir in "$CLAUDE_DIR/projects/$CWD_ENCODED/memory/topics" "$CLAUDE_DIR/projects/$HOME_ENCODED/memory/topics"; do
  [ -d "$dir" ] || continue
  for topic in "$dir"/*.md; do
    [ -f "$topic" ] || continue
    TLINES=$(wc -l < "$topic" | tr -d ' ')
    TNAME=$(basename "$topic")
    if [ "$TLINES" -gt 100 ]; then
      warn "Memory topic bloated ($TLINES lines, threshold 100): $TNAME — run /consolidate-memory"
    fi
  done
done

# ── 7c. Dedup scan — detect repeated content across memory, rules, contexts ──
python3 - "$CLAUDE_DIR" "$HOME" <<'PYEOF' 2>&1 | while IFS= read -r line; do warn "$line"; done
import os, sys, re, hashlib
from collections import defaultdict

claude_dir, home = sys.argv[1], sys.argv[2]

# Collect all .md files from memory topics, rules, contexts
scan_dirs = [
    os.path.join(claude_dir, "rules"),
    os.path.join(claude_dir, "contexts"),
]
# Add memory topic dirs (global + project-scoped)
for d in os.listdir(os.path.join(claude_dir, "projects")):
    topics = os.path.join(claude_dir, "projects", d, "memory", "topics")
    if os.path.isdir(topics):
        scan_dirs.append(topics)
    # Also scan loose memory .md files
    mem = os.path.join(claude_dir, "projects", d, "memory")
    if os.path.isdir(mem):
        scan_dirs.append(mem)

# Extract meaningful phrases (>30 chars) from each file
file_phrases = {}
for d in scan_dirs:
    if not os.path.isdir(d):
        continue
    for f in os.listdir(d):
        if not f.endswith(".md"):
            continue
        fp = os.path.join(d, f)
        try:
            lines = open(fp).readlines()
        except:
            continue
        phrases = set()
        for line in lines:
            line = line.strip()
            # Skip headers, empty lines, short lines, format markers
            if not line or line.startswith("#") or line.startswith("--") or len(line) < 35:
                continue
            # Normalize whitespace and case for comparison
            norm = re.sub(r'\s+', ' ', line.lower().strip())
            # Use first 60 chars as fingerprint (catches same concept, different tail)
            fp_key = norm[:60]
            phrases.add(fp_key)
        rel = os.path.relpath(fp, claude_dir)
        file_phrases[rel] = phrases

# Find duplicates: same phrase in 2+ files
phrase_to_files = defaultdict(list)
for fname, phrases in file_phrases.items():
    for p in phrases:
        phrase_to_files[p].append(fname)

dupes = {}
for p, files in phrase_to_files.items():
    if len(files) > 1:
        key = tuple(sorted(files))
        if key not in dupes:
            dupes[key] = []
        dupes[key].append(p[:50])

# Report (max 3 warnings to keep output small)
reported = 0
for files, phrases in sorted(dupes.items(), key=lambda x: -len(x[1])):
    if reported >= 3:
        break
    # Skip self-duplication within same directory
    dirs = set(os.path.dirname(f) for f in files)
    if len(dirs) == 1 and len(files) == 1:
        continue
    count = len(phrases)
    if count >= 2:
        print(f"Dedup: {count} shared phrases between {' & '.join(files)} — run /consolidate-memory")
        reported += 1
PYEOF

# ── 8. Project path encoding — encoded dir must match Claude Code's scheme ────
# Claude Code encodes paths: slashes→hyphens, dots→hyphens, double-slash→double-hyphen
# e.g. /Users/username/.claude → -Users-username--claude (dot becomes hyphen, / becomes -)
ENCODED_DIR=$(echo "$CLAUDE_DIR" | sed 's|/|-|g; s|\.|_|g' | sed 's|_|-|g')
# Simpler: just derive expected name from $CLAUDE_DIR directly
EXPECTED_DIR=$(python3 -c "
import sys
path = '$CLAUDE_DIR'
# Claude Code encoding: replace / with -, replace . with -
encoded = path.replace('/', '-').replace('.', '-')
print(encoded)
")
PROJECTS_DIR="$CLAUDE_DIR/projects"
if [ -d "$PROJECTS_DIR/$EXPECTED_DIR" ]; then
  ok
else
  warn "Expected project dir not found: $PROJECTS_DIR/$EXPECTED_DIR — mem0 may be writing to wrong path"
fi

# Check for stale bad-encoding dirs (dots not converted) — warn if any exist
python3 - "$PROJECTS_DIR" "$EXPECTED_DIR" <<'PYEOF' 2>&1 | while IFS= read -r line; do warn "$line"; done
import sys, os, re
projects_dir, expected = sys.argv[1], sys.argv[2]
if not os.path.isdir(projects_dir):
    sys.exit(0)
for entry in os.listdir(projects_dir):
    if entry == expected:
        continue
    # Flag dirs that look like path-encoded names but contain literal dots (bad encoding)
    if entry.startswith('-') and '.' in entry:
        print(f"Stale bad-encoding project dir found: {entry} — consider removing it")
PYEOF

# ── 9. Claude Code version — check for updates (cached 24h) ──────────────────
VERSION_CACHE="$CLAUDE_DIR/.version-cache"
INSTALLED=$(claude --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)

if [ -n "$INSTALLED" ]; then
  # Read cache: "timestamp|installed|latest"
  CACHE_TS=0
  CACHED_LATEST=""
  if [ -f "$VERSION_CACHE" ]; then
    CACHE_TS=$(cut -d'|' -f1 "$VERSION_CACHE" 2>/dev/null)
    CACHED_LATEST=$(cut -d'|' -f3 "$VERSION_CACHE" 2>/dev/null)
  fi

  NOW=$(date +%s)
  AGE=$(( NOW - CACHE_TS ))

  if [ "$AGE" -gt 86400 ]; then
    # Cache stale — check npm in background, update cache
    (
      LATEST=$(npm view @anthropic-ai/claude-code version 2>/dev/null)
      if [ -n "$LATEST" ]; then
        echo "$(date +%s)|$INSTALLED|$LATEST" > "$VERSION_CACHE"
      fi
    ) &
    CACHED_LATEST=""  # Don't warn this session — will warn next session
  fi

  if [ -n "$CACHED_LATEST" ] && [ "$INSTALLED" != "$CACHED_LATEST" ]; then
    # Only warn if available version is strictly newer (semver compare)
    NEWER=$(printf '%s\n%s\n' "$INSTALLED" "$CACHED_LATEST" | sort -V | tail -1)
    if [ "$NEWER" = "$CACHED_LATEST" ] && [ "$NEWER" != "$INSTALLED" ]; then
      warn "Claude Code update available: $INSTALLED → $CACHED_LATEST (run: brew upgrade claude-code)"
    fi
  fi
fi

# ── 10. System dependencies ──────────────────────────────────────────────────
command -v bun >/dev/null 2>&1 && ok || warn "bun not installed — required for browse and stitch skills: curl -fsSL https://bun.sh/install | bash"
command -v jq  >/dev/null 2>&1 && ok || warn "jq not installed — required by hooks and scripts: brew install jq"
command -v node >/dev/null 2>&1 && ok || warn "node not installed — required by browse skill: brew install node"

# ── 11. Daemon skills — node_modules + Playwright browsers ───────────────────
SKILLS_DIR="$CLAUDE_DIR/skills"
for pkg in "$SKILLS_DIR"/*/package.json; do
  [ -f "$pkg" ] || continue
  skill_dir=$(dirname "$pkg")
  skill_name=$(basename "$skill_dir")
  if [ ! -d "$skill_dir/node_modules" ]; then
    warn "Skill '$skill_name' needs setup: cd $skill_dir && bun install"
  else
    ok
    # Check Playwright browser binaries if this skill uses Playwright
    if grep -q '"playwright"' "$pkg" 2>/dev/null; then
      if [ ! -d "$HOME/Library/Caches/ms-playwright" ] && [ ! -d "$HOME/.cache/ms-playwright" ]; then
        warn "Skill '$skill_name': Playwright browsers not installed — run: cd $skill_dir && bunx playwright install chromium"
      else
        ok
      fi
    fi
  fi
done

# ── 12. mem0 wiring — required hooks registered in settings.json ─────────────
if [ -f "$SETTINGS" ] && python3 -c "import json; json.load(open('$SETTINGS'))" 2>/dev/null; then
  python3 - "$SETTINGS" "$HOOKS_DIR" <<'PYEOF' 2>&1 | while IFS= read -r line; do warn "$line"; done
import json, sys, os
settings = json.load(open(sys.argv[1]))
hooks_dir = sys.argv[2]

required = {
    "SessionStart": os.path.join(hooks_dir, "session-start.sh"),
    "SessionEnd":   os.path.join(hooks_dir, "mem0-extract.sh"),
    "Stop":         os.path.join(hooks_dir, "session-end.sh"),
}

for event, expected_path in required.items():
    entries = settings.get("hooks", {}).get(event, [])
    all_cmds = [
        h.get("command", "")
        for entry in entries if isinstance(entry, dict)
        for h in entry.get("hooks", []) if isinstance(h, dict)
    ]
    tilde_path = expected_path.replace(os.path.expanduser("~"), "~")
    if not any(expected_path in cmd or tilde_path in cmd for cmd in all_cmds):
        print(f"mem0 hook not registered: {event} → {expected_path}")
        print(f"  settings.json may have been modified — restore with: git checkout settings.json")
PYEOF
fi

# ── 13. Google Stitch API key — exists and non-empty ─────────────────────────
STITCH_KEY_FILE="$HOME/.config/stitch/key"
if [ ! -f "$STITCH_KEY_FILE" ]; then
  warn "Google Stitch API key not found at $STITCH_KEY_FILE — /stitch skill will not work. Get your key at stitch.withgoogle.com → Settings → API Keys, then: mkdir -p ~/.config/stitch && echo 'your-key' > ~/.config/stitch/key && chmod 600 ~/.config/stitch/key"
elif [ ! -s "$STITCH_KEY_FILE" ]; then
  warn "Google Stitch API key file is empty at $STITCH_KEY_FILE — get your key at stitch.withgoogle.com → Settings → API Keys"
else
  ok
fi

# ── 14. OMS model routing — every oms-config.json key reachable by hook ───────
OMS_CONFIG="$HOME/.claude/oms-config.json"
OMS_HOOK="$HOME/.claude/hooks/enforce-oms-model.sh"
if [ -f "$OMS_CONFIG" ] && [ -f "$OMS_HOOK" ]; then
  python3 - "$OMS_CONFIG" "$OMS_HOOK" <<'PYEOF' 2>&1 | while IFS= read -r line; do warn "$line"; done
import json, sys, re

config_path, hook_path = sys.argv[1], sys.argv[2]
overrides = json.load(open(config_path)).get("model_overrides", {})
hook = open(hook_path).read()

# Keys that are intentionally indirect (resolved via a different mechanism at runtime)
# oms-work: model comes from task spec model-hint, not the hook
# synthesizer_escalation, elaboration_complex: looked up as fallback inside their parent role
INDIRECT = {"synthesizer_escalation", "elaboration_complex", "oms-work"}

dead_keys = []
for key in overrides:
    if key in INDIRECT:
        continue
    # Accept hyphen or underscore variants in the hook
    pattern = re.compile(re.escape(key).replace(r"\-", r"[\-_]"), re.IGNORECASE)
    if not pattern.search(hook):
        dead_keys.append(key)

for key in dead_keys:
    print(f"oms-config key '{key}' has no detection branch in enforce-oms-model.sh — model routing silently dead for this role")
    print(f"  Fix: add a detection pattern that sets OMS_ROLE=\"{key}\"")
PYEOF
else
  [ ! -f "$OMS_CONFIG" ] && warn "oms-config.json not found at $OMS_CONFIG"
  [ ! -f "$OMS_HOOK" ]   && warn "enforce-oms-model.sh not found at $OMS_HOOK"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
if [ "$FAIL" -gt 0 ]; then
  echo "[HealthCheck] $FAIL issue(s) found — run ~/.claude/hooks/memory-persistence/health-check.sh to see details" >&2
fi
