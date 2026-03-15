# Skill: oms-capture

Captures a real-life OMS failure as a structured training scenario.

## Trigger Conditions
1. CEO stopped a task mid-way to correct routing/tier
2. Trainer flagged `channel: "scenario"` for a `lesson_candidate`
3. Same lesson appears 2+ times in an agent's `lessons.md`

## Usage
```
/oms-capture                    # capture from current/last task
/oms-capture [task-id]          # capture from a specific task log
```

## Before Running
Load:
- Task log at `logs/tasks/[task-id].md` (full)
- `~/.claude/agents/training/index.md` (check for overlap with existing scenarios)
- The relevant agent's `lessons.md` (check if this is a repeat pattern)

## Step 1 — Extract the failure
From the task log and/or CEO correction, identify:
- **What happened**: which agent, which round, what output field, what the behavior was
- **What should have happened**: correct behavior per agent persona or OMS rules
- **Trigger condition**: what input/context caused the agent to produce this behavior
- **Correction signal**: how the failure was detected (CEO stopped task / trainer flagged / synthesis overridden)

## Step 2 — Check for existing scenario overlap
Scan `training/index.md`. Ask: does an existing scenario already test this specific failure mode for this agent?

**If overlap found:**
- Present to CEO: "This matches [scenario NNN — name]. Options: (a) update that scenario to also cover this case, (b) create a new scenario if the failure mode is sufficiently distinct."
- If updating: edit `training/scenarios/[NNN]-[name].md` — add the new failure signal and update criteria tested if needed. Do NOT change existing expected behavior.
- If creating new: proceed to Step 3.

**If no overlap:** proceed to Step 3.

## Step 3 — Generate the scenario
Produce a scenario file in the standard format:

```markdown
# Scenario [NNN] — [Short Name] ([Tier N])

**Difficulty**: Basic | Medium | Advanced
**Primary failure mode tested**: [one sentence]
**Criteria tested**: [R1, D3, etc. — match to validation-criteria.md]

## Synthetic CEO Intent
> "[realistic CEO task description that would trigger this failure]"

## Expected Behavior

**Router routing**:
- Tier: N
- [routing expectations]

**Round 1**:
- [agent]: [what they should do]

**Round 2**:
- [expected behavior]

**Synthesis**:
- [expected synthesis behavior]

## Failure Signals
- [specific observable failure in output field → criterion code fail]

## Trainer Evaluation Focus
[What trainer should specifically check to confirm the failure was avoided]
```

Rules for scenario generation:
- CEO intent must be **realistic** — something an actual OMS user would type
- Do not use the exact task that generated the failure as the CEO intent — generalize it
- Failure signals must be **specific and observable** — wrong field value, wrong agent activated, wrong tier — not vague descriptions
- Criteria codes must match existing codes in `validation-criteria.md` OR propose a new code with format `[Letter][Number]`

## Step 4 — Determine scenario number
Check existing scenarios in `training/scenarios/` to find the next available number (current max + 1).

## Step 5 — Present to CEO
Show the generated scenario and ask: "Does this capture the failure correctly? Approve to add to training library, or suggest edits."

Do not write files until CEO approves.

## Step 6 — Write on approval
On CEO approval:
1. Write `training/scenarios/[NNN]-[name].md`
2. Update `training/index.md` — add scenario to the correct package table, following the existing format
3. Tell CEO: "Scenario [NNN] added. Run `/oms-train [NNN]` to validate the system passes this scenario."

## Step 7 — Check lessons.md
If capture was triggered by a repeat pattern in lessons.md (same lesson 2+ times):
- The lesson that triggered it stays in lessons.md — it is still valid lived experience
- Note to CEO: "The recurring pattern in [agent]'s lessons.md has been promoted to a training scenario. Consider running `/oms-train [NNN]` to validate the persona now handles this correctly."

## Standing Rules
- One scenario per capture session — if multiple failures exist in one task, run `/oms-capture` separately for each
- Never auto-write scenarios without CEO approval
- A scenario that cannot be generalized (too specific to a one-off task) should remain a lesson, not a scenario
- New criteria codes (if proposed) must be reviewed — propose them in `## Criteria Gap Log` in `validation-criteria.md` first
