---
name: oms-train
description: Run OMS training scenarios against agent personas and iterate until all pass. Usage: /oms-train [scenario ids] or /oms-train --failing
---
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

SCENARIO CANDIDATES (lessons that appeared 2+ times)
[none this run]

--- Reviewing failures with trainer ---
```

### Failure review — menu + discussion, one failure at a time

For each failing or partial scenario, the trainer presents a structured menu:

```
[003] scope-conflict — D3 fail
What happened: PM accepted scope reduction in Round 2 without naming the user
need being deferred.

Options:
  A) Add to Non-Negotiables: "scope reduction must name the user need it defers"
     → Hard rule — PM cannot concede scope without naming what user value is deferred
  B) Add to Discussion (Round 2): "when conceding scope, state which user need is deferred"
     → Softer — guides behavior without making it an absolute
  C) Update the scenario — expected behavior is too strict for PM's role
     → If PM should be allowed to concede scope without this requirement
  D) Skip — accept this failure, don't enforce
     → Consciously excluded from convergence check
  E) Discuss

Choice:
```

You pick a letter. If you pick E, the trainer answers questions, explains its reasoning, or works through alternatives with you — then re-presents the menu (possibly with updated options based on the discussion) for a final decision.

The trainer stays on this failure until you land on A, B, C, or D. Then moves to the next.

### Loop logic
```
All failures reviewed → apply all agreed changes → re-run affected scenarios
Increment run number in results.tsv
Repeat until all non-skipped scenarios pass (convergence)
```

**Accepted-failure**: a scenario consciously excluded. Logged in `results.tsv` as `accepted-failure` with your stated reason. Does not block convergence.

**Scenario edit during training**: if you decide a scenario's expected behavior is wrong, the trainer drafts the correction and presents it for approval before writing. The scenario file is updated, then re-run immediately to confirm the fix.

**Convergence rule**: loop terminates when all non-skipped scenarios pass, or a full pass produces no changes of any kind (genuine plateau — trainer flags this explicitly).

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
