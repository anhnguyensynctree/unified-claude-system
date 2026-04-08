#!/usr/bin/env bash
# PostToolUse hook: run Discord integration tests when discord-related files change.
# Matches: discord-bot.py, oms_discord.py, oms-brief.py, discord-create-channel.py
FILE=$(jq -r '.tool_input.file_path // ""' 2>/dev/null)
echo "$FILE" | grep -qE '(discord-bot|oms_discord|oms-brief|discord-create-channel)\.py$' || exit 0

echo "[hook] Discord file changed — running integration tests..." >&2
cd ~/.claude && python3 -m pytest tests/test_discord.py tests/test_brief.py tests/test_discord_e2e.py -q 2>&1 | tail -5 >&2
EXIT=${PIPESTATUS[0]}
if [ "$EXIT" -ne 0 ]; then
  echo "[⛔ BLOCKED] Discord tests failed — fix before continuing" >&2
  exit 2
fi
