# Next Session: Agent Loop for Free Models in oms-work.py

## Context
Read memory: `~/.claude/projects/-Users-Lewis--claude/memory/project_llm_router_oms_work.md` and `project_enforcement_gap.md`

Current oms-work.py uses batch mode: generate all files → extract → verify → retry. This works for code-generation tasks but fails for scaffold/infra tasks that need runtime feedback (pip install, mkdir, etc.).

## What to build
Add `_agent_loop()` to `bin/oms-work.py` as an alternative execution mode for tasks that need tool access. Route infra-critical tasks and scaffold tasks through the agent loop instead of batch mode.

### Architecture
```python
def _agent_loop(task, wt, model, max_steps=15):
    """Step-by-step execution: LLM proposes one action, we execute it, feed result back."""
    history = []  # accumulated action/result pairs
    
    for step in range(max_steps):
        prompt = build_agent_prompt(task, wt, history)
        response = _call_litellm(model, prompt)
        action = parse_action(response)  # loose parsing with fallbacks
        
        if action.type == 'write':
            write file to worktree
            history.append(f"Wrote {path} ({n} chars)")
        elif action.type == 'run':
            execute shell command (with zshrc source)
            history.append(f"Ran: {cmd}\nExit {code}: {output[:500]}")
        elif action.type == 'done':
            break
        else:
            # Format violation — re-prompt with stricter instruction
            history.append("Invalid action format. Use WRITE, RUN, or DONE.")
```

### Key decisions
- Agent loop for: infra-critical=true, scaffold tasks, tasks with many directories/files
- Batch mode for: regular impl (code gen), research
- Agent loop uses same quality checks + verify commands after completion
- Validators still run on output (haiku first, gemma fallback)
- Max 15 steps per task, ~30-60s per step = 5-15 min total
- Parse loosely: code blocks → WRITE, shell lines → RUN, completion words → DONE
- System context (Python/Node version) included in first prompt

### Files to modify
- `bin/oms-work.py` — add _agent_loop(), parse_action(), build_agent_prompt()
- Update execute_task() to route infra-critical tasks to agent loop
- Same quality checks + verify + browse + validators run after agent loop completes

### Also fix in this session
- Pre-execution dry-run: run Verify commands in check mode before first LLM call
- CTO elaboration enforcement: add system context to elaboration prompts
- Test with base-trade TASK-001 (infra-critical scaffold)

### Rate limit mitigation
- Each agent loop step is ~500 tokens (small prompt + short response)
- 15 steps × 500 tokens = ~7500 tokens total (same as 2 batch attempts)
- Use same model fallback chains if primary rate-limited
- Agent loop calls are shorter so individual rate limit recovery is faster

### Format violation handling
- Primary: parse WRITE/RUN/DONE keywords
- Fallback 1: detect code blocks → WRITE, shell patterns → RUN
- Fallback 2: "I've completed" / "done" / "finished" → DONE  
- Fallback 3: re-prompt with "Respond with exactly: WRITE path, RUN cmd, or DONE"
- Max 2 format violations before falling back to batch mode
