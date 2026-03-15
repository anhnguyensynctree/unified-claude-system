# OMS Train — Agent Validation Runner

Runs training scenarios against the agent system and iterates until all scenarios pass. Each run feeds Channel 2 (lessons.md) just like real tasks do.

## Usage
```
/oms-train              # run all 46 scenarios, loop until all green
/oms-train 001          # run a specific scenario by number
/oms-train 001 002 003  # run specific scenarios
/oms-train --failing    # re-run only scenarios that failed last run
```

## Before Running
Load:
- `~/.claude/agents/training/validation-criteria.md`
- `~/.claude/agents/shared-context/discussion-schema.md`
- All agent personas + lessons.md for agents in scope

## results.tsv
Location: `~/.claude/agents/training/results.tsv`

Create if missing. Append one row per scenario per run:
```
date	run	scenario_id	scenario_name	overall_result	criteria_results
2026-03-14	1	001	simple-routing	pass	R1:pass,R2:pass,E1:pass
2026-03-14	1	003	scope-conflict	fail	D3:fail,D1:pass
2026-03-14	2	003	scope-conflict	pass	D3:pass,D1:pass
```

`run` increments each time a full or partial pass is completed in the same session.

---

## Execution Per Scenario

### 1. Load the scenario
Read `~/.claude/agents/training/scenarios/[NNN]-[name].md`.

### 2. Run through OMS flow
Use the scenario's synthetic CEO intent as the `/oms` input. Execute Steps 1–5 from oms.md (Router → rounds → synthesis → log). Write the log to `~/.claude/logs/tasks/train-[scenario-id]-[date].md`.

Do NOT run Step 6 trainer yet — replaced by the training evaluation below.

### 3. Run trainer evaluation
Trainer call:
- Input: `~/.claude/agents/trainer/persona.md` + `trainer/lessons.md` + `trainer/MEMORY.md` + full discussion log + scenario expected behavior + `validation-criteria.md`
- Instruction: "Evaluate this training run against the scenario's expected behavior and validation criteria. For each criterion tested, output pass or fail with evidence. Also produce lesson_candidates for any agent that deviated from expected behavior."

### 4. Collect trainer output

Extended training schema (trainer produces this format for training runs):
```json
{
  "scenario_id": "001",
  "scenario_name": "simple-routing",
  "overall_result": "pass | partial | fail",
  "criteria_results": [
    {
      "criterion": "R2",
      "result": "pass | fail",
      "evidence": "Router classified as simple, activated frontend-developer only — correct"
    }
  ],
  "agent_evaluations": [
    {
      "agent": "router",
      "engagement_quality": "good | mixed | poor",
      "lesson": "one-line behavioral rule — null if no lesson this scenario"
    }
  ],
  "lesson_candidates": [
    {
      "agent": "product-manager",
      "lesson": "Hold scope position when challenged — state the user need the scope serves, not just the scope boundary.",
      "retrieval_trigger": "Surfaces when: scope is challenged by CTO or Backend Dev under timeline pressure",
      "channel": "lesson | scenario",
      "evidence": "Round 2 — PM accepted reduced scope without naming the user need it sacrificed"
    }
  ],
  "recommended_persona_changes": [
    {
      "agent": "product-manager",
      "change": "specific suggested edit to persona file",
      "reason": "observed behavior the current persona does not prevent",
      "evidence": "cite the round and specific output"
    }
  ],
  "criteria_gaps": ["description of behavior not covered by any criterion"]
}
```

### 5. Write Channel 2 — lessons from training
For each `lesson_candidates` entry with `channel: "lesson"`:
- Check `~/.claude/agents/[agent]/lessons.md` for a matching rule (4-word fingerprint match)
- If not present: append `[date] | train-[scenario-id]: [lesson]` to that agent's `lessons.md`
- If already present: upgrade to `channel: "scenario"` — log as a scenario candidate

For each `lesson_candidates` entry with `channel: "scenario"`: collect for the final report.

### 6. Append criteria gaps
If `criteria_gaps` non-empty, append to `~/.claude/agents/training/validation-criteria.md` under `## Criteria Gap Log`:
```
[date] Gap: [description] Suggested criterion: [draft]
```

### 7. Write results.tsv
Append one row per scenario to `~/.claude/agents/training/results.tsv`.

---

## Training Loop — Iterate Until Green

After running all scenarios (or the specified subset):

### Report format
```
Training Run [N] — [date]
Scenarios: [total run] | Pass: [X] | Partial: [Y] | Fail: [Z]

RESULTS
[001] simple-routing: pass — R1 ✓ R2 ✓ E1 ✓
[003] scope-conflict: fail — D3 ✗ (PM accepted reduced scope without naming sacrificed user need)
[005] majority-cascade: partial — M1 ✓ M2 ✗ (Backend Dev capitulated in Round 3 citing round count)

AGENTS TO WATCH
[product-manager]: failed D3 in scenario 003
[backend-developer]: partial M2 in scenario 005

PERSONA CHANGES SUGGESTED
[product-manager — scenario 003]: add non-negotiable: scope reduction must name the user need being deferred
  Approve? (y/n)
[backend-developer — scenario 005]: strengthen majority-pressure resistance instruction in Discussion section
  Approve? (y/n)

SCENARIO CANDIDATES (lessons that appeared 2+ times)
[none this run]
```

### Loop logic
```
If all pass: "All scenarios green ✓ — system ready."

If any fail or partial:
  Present persona changes → CEO responds to each:
    (y) approve → apply change, re-run scenario
    (n) decline → ask: "Why? (a) wrong diagnosis  (b) right direction, wrong wording  (c) skip"
      (a) wrong diagnosis → trainer re-analyzes failure, proposes alternative change
      (b) wrong wording  → CEO provides correct phrasing → apply that, re-run scenario
      (c) skip           → mark scenario as accepted-failure, remove from loop
  Re-run only failing/partial scenarios that were not skipped
  Increment run number in results.tsv
  Repeat report → loop
```

**Accepted-failure**: a scenario the CEO has consciously decided not to enforce. Logged in `results.tsv` as `accepted-failure` with a note. Does not block "all green" — excluded from the convergence check.

**Convergence rule**: loop terminates when all non-skipped scenarios pass, or a full run produces zero new approved or re-proposed changes (genuine plateau).

### Persona change application
When CEO approves a change, edit the relevant `~/.claude/agents/[role]/persona.md` directly. Changes go to:
- `## Non-Negotiables` — if the failure was a hard rule violation
- `## Discussion` — if the failure was a round behavior issue
- `## Callout Protocol` — if the failure was a missed mandatory callout

Never edit the JSON output schema during training — schema changes require manual review.

---

## Running Cadence
- First run: all 46 scenarios, loop until all green
- After any persona edit: run the scenarios that test that agent
- After 5+ real OMS tasks: run `--failing` to catch behavioral drift
- After `/oms-capture` adds a new scenario: run that scenario number to validate the fix
