# OMS Train — Agent Validation Runner

Runs training scenarios against the agent system and produces a health report. Uses Claude Code runtime — no API key required.

## Usage
```
/oms-train              # run all scenarios
/oms-train 001          # run a specific scenario by number
/oms-train 001 002      # run specific scenarios
```

## Before Running
Load these files:
- `packages/agents/training/validation-criteria.md`
- All files listed in oms.md "Before Running" section

## Execution Per Scenario

### 1. Load the scenario
Read `packages/agents/training/scenarios/[NNN]-[name].md`.

### 2. Run the scenario through the full OMS flow
Use the scenario's synthetic CEO intent as the `/oms` input. Execute all steps from oms.md (Steps 1–5: pre-scope, rounds, synthesis, log). Write the log to `logs/tasks/train-[scenario-id]-[date].md`.

Do NOT run Step 6 (trainer evaluation) yet — that is replaced by the training evaluation below.

### 3. Run the Trainer against validation criteria
Trainer call:
- System prompt: `trainer.md` + trainer MEMORY.md
- Context: full discussion log + synthesis + scenario expected behavior + validation-criteria.md
- Instruction: "Evaluate this training run against the scenario's expected behavior and the validation criteria. For each criterion tested, state pass or fail with evidence."

### 4. Collect the training evaluation
The trainer outputs an extended schema for training runs:

```json
{
  "scenario_id": "001",
  "scenario_name": "simple-routing",
  "overall_result": "pass | partial | fail",
  "criteria_results": [
    {
      "criterion": "R2",
      "result": "pass | fail",
      "evidence": "EC classified as simple, activated frontend-developer only — correct"
    }
  ],
  "agent_evaluations": [...],
  "memory_facts": { "agent-role": ["fact 1", "fact 2"] },
  "criteria_gaps": ["description of behavior not covered by any criterion"],
  "recommended_persona_changes": [
    {
      "agent": "cto",
      "change": "description of suggested persona edit",
      "reason": "observed behavior that the current persona does not prevent"
    }
  ]
}
```

### 5. Write memory facts
For each agent with memory_facts, run:
```bash
python3 packages/agents/memory/agent-mem-extract.py inject [agent] "fact 1" "fact 2" ...
```

### 6. Append criteria gaps
If `criteria_gaps` is non-empty, append to `training/validation-criteria.md` under `## Criteria Gap Log`:
```
[date] Gap: [description] Suggested criterion: [draft from trainer]
```

### 7. Report to CEO
Present a health report:

```
Training Run: [date]
Scenarios: [list run]

RESULTS
[scenario 001]: pass — R1 ✓ R2 ✓ E1 ✓ D1 ✓
[scenario 002]: partial — E1 ✓ E2 ✗ (Backend Dev changed position without naming CTO's argument)
[scenario 003]: fail — D3 ✗ (PM accepted full scope without challenge)

AGENTS TO WATCH
[cto]: passed all criteria
[product-manager]: failed D3 in scenario 003 — review non-negotiables section

PERSONA CHANGES SUGGESTED
[product-manager]: [change description] — approve? (y/n)

CRITERIA GAPS FOUND
[gap description] — added to validation-criteria.md for review
```

### 8. Persona changes
Recommended persona changes are NOT applied automatically. Present them to the CEO with the evidence. If CEO approves, edit the relevant persona file directly.

## Running Cadence
- Run after any persona change to verify the change achieved the intended effect
- Run after 5+ real tasks to check if agent behavior has drifted from criteria
- Run when adding a new agent to validate it integrates correctly with existing agents
