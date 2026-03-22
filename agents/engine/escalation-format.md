# Escalation Format

This file defines how a CEO escalation is packaged when the system cannot resolve a decision internally.

## Escalation Criteria
Escalate only when:
- The decision requires product or company direction that the system cannot make internally
- A non-negotiable deadlock exists that only the CEO can break
- Agents have reached the hard round cap without convergence on a consequential decision

Do NOT escalate for:
- Ambiguity — ask a clarifying question first
- Technical disagreements within the engineering domain — CTO resolves
- Scope disagreements within reasonable bounds — PM and EM resolve

## Escalation Artifact

```json
{
  "escalation_type": "strategic | tactical",
  "context_summary": "2–3 sentences: what was discussed and why the system cannot resolve it",
  "options": [
    {
      "option": "Option A label",
      "description": "one sentence",
      "pros": ["pro 1", "pro 2"],
      "cons": ["con 1"],
      "agent_support": ["cto", "product-manager"]
    }
  ],
  "recommended_option": "Option A",
  "recommendation_reasoning": "one sentence explaining why this option is recommended",
  "resumption_plan": "how discussion resumes after CEO decides"
}
```

## After CEO Decision
**Strategic escalation**: CEO direction is locked in. Task restarts with new constraints applied. OMS writes the decision and reasoning to Router memory and relevant agent memory files.

**Tactical escalation**: discussion resumes mid-round with CEO input incorporated as a constraint. Agents re-run the current round with the new information.

---

## CEO Gate Brief (Step 3.5)

CEO Gate is handled by `~/.claude/agents/ceo-gate/persona.md`. That file is authoritative for: trigger categories, delegation levels, C-suite buffer round format, Ratification Brief, Strategic Brief, research loop, C-suite reaction round, and Decision Log.

This file does not duplicate CEO Gate content. When implementing CEO Gate behavior, read `ceo-gate/persona.md` directly.

---

## CEO Correction Feedback Loop
If the CEO cancels a task, rejects the complexity assessment, or corrects the system's routing decision, the correction is written to Router memory and the relevant agent memories:

```
## Correction: [date]
Task: [brief task description]
System assessment: [what was decided — complexity, routing, escalation trigger]
CEO correction: [what the CEO said]
Lesson: [one sentence — what this means for future assessments]
```

This is the primary mechanism by which the system improves its judgment over time. Every correction is a training signal.
