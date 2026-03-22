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

The CEO Gate brief is distinct from a deadlock escalation. It fires proactively — before synthesis — when the decision crosses a CEO-ownership threshold, regardless of whether agents agreed or disagreed.

**CEO Gate triggers** (any one is sufficient):
1. Business model change
2. Market pivot / new customer segment
3. Strategic resource bet (>20% capacity or 12-month platform lock-in)
4. Vision conflict (contradicts company-belief.ctx.md)
5. External commitment to partner, customer, or regulator
6. Product direction change (closes off or adds strategic bets)
7. Ethics or values deadlock not resolved by any domain authority
8. Legal/compliance boundary — CLO critical risk or exec legal acceptance required
9. Kill decision (deprecating a capability users rely on)
10. C-suite irresolution at hard round cap

**CEO Gate brief format** (rendered as Markdown to CEO):

```markdown
---
## CEO Decision Required — [category]

**Decision:** [one sentence — the specific question CEO must answer]
**Why it's yours:** [which trigger fired, why delegation isn't appropriate]

### What agents concluded
- [position] *(supported by: [agents], confidence: [high|medium|low])*

### The real tension
[2–3 sentences — what makes this genuinely hard; the core tradeoff]

### Options

**Option A — [name]**
[one sentence outcome]
Upside: [points] | Risk: [points] | Supported by: [agents]

**Option B — [name]**
[one sentence outcome]
Upside: [points] | Risk: [points] | Supported by: [agents]

**Option C — Delegate with constraint**
Let agents decide, bounded by a constraint you set.

**Agents lean toward:** [Option X — one sentence why]

> Reply with: "A", "B", "C", or your own direction. OMS resumes from your choice.
---
```

**After CEO responds:**
1. Capture CEO's response verbatim as `ceo_decision`
2. Inject into Synthesizer as hard constraint: "CEO has decided: [verbatim]. Synthesize only within this constraint."
3. Log brief + response to task log under `## CEO Gate Decision`
4. Write decision + category to `ceo-gate/MEMORY.md`
5. Resume Step 4 — Synthesizer proceeds with constraint locked

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
