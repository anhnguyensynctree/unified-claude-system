# Discussion Output Schema

Shared by all OMS discussion agents. Each agent references this file for base schema and universal rules.

## Base JSON Schema

```json
{
  "position": "single actionable sentence — agent's assessment or stance",
  "reasoning": ["discrete claim 1", "discrete claim 2", "discrete claim 3"],
  "confidence_level": "high | medium | low",
  "confidence_pct": 75,
  "position_delta": {
    "changed": false,
    "challenged_by": null,
    "challenge_summary": null,
    "why_held": null
  },
  "warrant": "why these grounds logically support this position — not a restatement of the grounds",
  "anticipated_rebuttals": ["the strongest objection to this position and why it does not hold"]
}
```

## position_delta — Round 1

`changed` is always `false`; all other fields are `null`.

## position_delta — Round 2+ (position changed)

```json
{
  "changed": true,
  "change_type": "full_reversal | partial_revision | confidence_update | scope_adjustment",
  "change_basis": "new_fact | new_constraint | new_tradeoff | clarification",
  "source_agent": "[agent name]",
  "source_argument": "[specific claim that caused the shift]",
  "what_remained": "[what from prior position still holds]"
}
```

## position_delta — Round 2+ (position held under challenge)

```json
{
  "changed": false,
  "challenged_by": "[agent name]",
  "challenge_summary": "[brief summary of their challenge]",
  "why_held": "[domain-grounded reason the challenge did not shift your position]"
}
```

## Universal Rules

**`confidence_level` rule**: `"low"` or `"medium"` must be stated explicitly in `position` wording — do not project false certainty when uncertainty is genuine.

**`confidence_pct` rule**: integer 0–100. Must be consistent with `confidence_level`: high ≥ 70, medium 40–69, low < 40. Used by Facilitator to compute confidence delta between rounds.

**`change_basis: "social_pressure"`** fails M1 automatically. Position changes must be grounded in new facts, constraints, tradeoffs, or clarifications — never in who said it or how forcefully.
