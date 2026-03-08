#!/usr/bin/env bash
# Status line mirroring the robbyrussell oh-my-zsh theme
# Receives Claude Code JSON context via stdin

input=$(cat)

cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')
model=$(echo "$input" | jq -r '.model.display_name // ""')
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

# Basename of current directory (matches robbyrussell %c)
dir_name=$(basename "$cwd")

# Git branch and dirty state (skip locks to avoid contention)
git_info=""
if git_branch=$(git -C "$cwd" --no-optional-locks symbolic-ref --short HEAD 2>/dev/null); then
  if git -C "$cwd" --no-optional-locks diff --quiet 2>/dev/null && \
     git -C "$cwd" --no-optional-locks diff --cached --quiet 2>/dev/null; then
    git_info=" \033[1;34mgit:(\033[0;31m${git_branch}\033[1;34m)\033[0m"
  else
    git_info=" \033[1;34mgit:(\033[0;31m${git_branch}\033[1;34m)\033[0;33m ✗\033[0m"
  fi
fi

# Context usage indicator
ctx_info=""
if [ -n "$used_pct" ]; then
  used_int=${used_pct%.*}
  if [ "$used_int" -ge 80 ]; then
    ctx_info=" \033[0;31mctx:${used_int}%\033[0m"
  elif [ "$used_int" -ge 50 ]; then
    ctx_info=" \033[0;33mctx:${used_int}%\033[0m"
  else
    ctx_info=" \033[0;32mctx:${used_int}%\033[0m"
  fi
fi

# Model name (shortened)
model_info=""
if [ -n "$model" ]; then
  model_info=" \033[0;35m${model}\033[0m"
fi

printf "\033[0;36m%s\033[0m%s%s%s" "$dir_name" "$git_info" "$ctx_info" "$model_info"
