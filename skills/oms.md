# OMS — One Man Show

Orchestrates the one-man-show multi-agent discussion engine. Invoked via `/oms` followed by your intent in natural language.

## Before Running
Load these files as context before any agent calls:
- `packages/agents/engine/discussion-rules.md`
- `packages/agents/engine/synthesis-prompt.md`
- `packages/agents/engine/escalation-format.md`
- `packages/agents/shared-context/product/company-direction.md`
- `packages/agents/shared-context/product/product-direction.md`
- `packages/agents/shared-context/engineering/architecture.md`
- `packages/agents/shared-context/engineering/cross-agent-patterns.md`

## Agent Registry (V1 — Engineering Division)
| Role | Persona File | Memory File |
|------|-------------|-------------|
| executive-coordinator | `packages/agents/personas/executive-coordinator.md` | `.claude/agents/executive-coordinator/MEMORY.md` |
| cto | `packages/agents/personas/cto.md` | `.claude/agents/cto/MEMORY.md` |
| product-manager | `packages/agents/personas/product-manager.md` | `.claude/agents/product-manager/MEMORY.md` |
| engineering-manager | `packages/agents/personas/engineering-manager.md` | `.claude/agents/engineering-manager/MEMORY.md` |
| frontend-developer | `packages/agents/personas/frontend-developer.md` | `.claude/agents/frontend-developer/MEMORY.md` |
| backend-developer | `packages/agents/personas/backend-developer.md` | `.claude/agents/backend-developer/MEMORY.md` |
| qa-engineer | `packages/agents/personas/qa-engineer.md` | `.claude/agents/qa-engineer/MEMORY.md` |
| trainer | `packages/agents/personas/trainer.md` | `.claude/agents/trainer/MEMORY.md` |

## Task ID and Log Naming
Every task gets an ID at the start: `YYYY-MM-DD-short-slug`

The slug is a kebab-case commit-message-style summary of the CEO's intent (max 6 words):
- "add google auth login" → `2026-03-10-add-google-auth-login`
- "fix checkout payment error" → `2026-03-10-fix-checkout-payment-error`
- "refactor api rate limiting" → `2026-03-10-refactor-api-rate-limiting`

The EC generates the slug as part of its routing output. Log path: `logs/tasks/[task-id].md`

## Step 1 — Executive Coordinator: Pre-Scope
Run the Executive Coordinator as a subagent:
- System prompt: contents of `executive-coordinator.md` + EC's MEMORY.md (if exists)
- Task: parse CEO intent → TRIZ contradiction scan → generate task slug → assess complexity → designate Domain Lead → prepare pre-mortem failure modes → identify agents to activate → lock roster → Stage-Gate 1

EC output must include: `task_id`, `activated_agents`, `domain_lead`, `complexity`, `round_cap`, `triz_contradiction`, `premortem_failure_modes`, `stage_gate`.

**If EC returns clarifying questions**: present them to CEO, collect answers, re-run EC with answers included.
**If EC's `stage_gate` is `failed`**: do not proceed — fix the noted gap and re-run EC.
**If EC returns a passing routing decision**: proceed to Step 2.

## Step 2 — Round 1: NGT Blind Submission
Run all activated agents **in parallel** (single message, multiple Agent tool calls). Parallel execution enforces NGT blindness — agents cannot see each other's Round 1 outputs.

Each agent call receives:
- System prompt: persona file contents + agent's MEMORY.md (if exists)
- Context: CEO intent + task description + all engineering shared-context files
- Pre-mortem injection: the EC's `premortem_failure_modes` block:
  ```
  Pre-mortem for this task — plausible failure modes, not predictions. Address them in your reasoning.
  1. [failure mode 1]
  2. [failure mode 2]
  3. [failure mode 3]
  ```
- Instruction: "Post your Round 1 initial position. You have not seen other agents' positions yet."

**Stage-Gate 2 (after Round 1 collected)**: check every agent's output for populated `warrant` and non-empty `reasoning[]`. Any agent failing this check: re-run that agent with reminder to populate all required fields before proceeding to Round 2.

Display on screen after Round 1:
```
Round 1
[Agent Name]: [position field]
[Agent Name]: [position field]
```

## Step 3 — Rounds 2+: Response Rounds
For each subsequent round:
1. Build full discussion history: all prior rounds, all agents — never summarize or truncate
2. Run all activated agents in parallel
3. Each agent call includes the full history + instruction: "This is Round [N]. Read all prior positions and respond. Name specific agents when agreeing or disagreeing."
4. Collect outputs
5. Check convergence per `discussion-rules.md` — distinguish true convergence from false convergence (all `changed: false` with no explicit challenge responses)
6. Display round summary: one line per agent showing position and whether it changed

If false convergence detected: inject challenge prompt before declaring convergence. If livelock detected: EC names the loop and imposes a resolution constraint.

**Stage-Gate 3 (after final round, before synthesis)**: confirm no unresolved cross-domain interface incompatibilities. If any exist, inject a compatibility check prompt and run one additional targeted round before synthesis.

Continue until true convergence or hard cap (5 rounds).

## Step 4 — Synthesis
**Stage-Gate 4 check will be applied after synthesis.**

Identify the synthesizing agent per `synthesis-prompt.md`.
Pass the full discussion history to the synthesizing agent.
Collect the synthesis artifact.

**Stage-Gate 4**: verify the synthesis decision is traceable to at least one agent's `position` field. If the synthesis introduces a new position not present in the discussion, reject it and re-run the synthesizing agent with the instruction: "Your synthesis must be traceable to agents' stated positions — do not introduce new positions."

If `escalation_required: true`: package per `escalation-format.md` and present to CEO.
If no escalation: present decision, rationale, and action items to CEO.

## Step 5 — Log
Write the full discussion log to `logs/tasks/[task-id].md`.

Log structure:
```
# [task-id]: [CEO intent verbatim]
Date: YYYY-MM-DD
Complexity: simple | complex
Domain Lead: [role]
Activated: executive-coordinator, cto, ...
Round cap: N
Pre-mortem: [failure mode 1], [failure mode 2]

## Round 1 (NGT Blind)
### executive-coordinator
[full JSON output]
### cto
[full JSON output]

## Round 2
...

## Synthesis
[synthesis artifact JSON]
```

## Step 6 — Trainer Evaluation + Memory Write
After synthesis, run the Trainer as a subagent — always, every task. Uses Claude Code runtime tokens.

Trainer call:
- System prompt: contents of `trainer.md` + trainer's MEMORY.md (if exists)
- Context: full discussion log + synthesis + CEO feedback (approval / correction / cancellation)
- Instruction: "Evaluate this completed task. Assess each participating agent."

Collect the trainer's JSON output. Then for each agent in `agent_evaluations`:

1. Read the agent's current MEMORY.md to check what's already known
2. From the trainer's evaluation for that agent, identify new behavioral facts not already captured
3. Inject the new facts:
```bash
python3 packages/agents/memory/agent-mem-extract.py inject [agent] "fact 1" "fact 2" ...
```

If `cross_agent_patterns` is non-empty: append them to `shared-context/engineering/cross-agent-patterns.md` under `## Learned Patterns`.

If `complexity_assessment_accurate: false`: inject the `complexity_note` to EC memory:
```bash
python3 packages/agents/memory/agent-mem-extract.py inject executive-coordinator "[complexity_note]"
```

If `meta_retrospective_due: true`: notify CEO — "Trainer flags a pattern-level retrospective is due for [agent]. Run `/oms-train` to generate it."

## Step 7 — Compact Check
After all memory writes:
```bash
python3 packages/agents/memory/agent-mem-extract.py check
```

If any agent is over threshold, tell the CEO: "[role] memory is [N] lines — run `/compact-agent-memory [role]` when convenient."

## Step 8 — CEO Feedback Loop
After CEO reviews the output:
- If CEO corrects complexity, routing, or escalation: write the correction to EC + relevant agent memories using `engine/escalation-format.md` correction format, then re-run trainer with the CEO's correction as additional context
- If CEO cancels: record the cancellation reason in EC memory as a future complexity training signal

## Error Handling
- Agent returns invalid JSON: re-run that agent with a reminder to match its output schema exactly
- Agent fails Stage-Gate 2 (missing warrant/reasoning): re-run that agent before Round 2
- EC cannot determine routing: ask CEO for more context before proceeding
- Synthesis fails Stage-Gate 4: re-run synthesizing agent with traceability instruction
- Discussion exceeds hard cap: synthesize what exists, note unresolved disagreements, escalate if consequential
- Memory extraction fails (no API key, network error): log the skip, continue — memory is non-blocking
