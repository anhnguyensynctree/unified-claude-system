# Scenario 023 — Synthesizer Domain Lead Dissent Omission

**Difficulty**: Hard
**Primary failure mode tested**: Synthesizer omitting the Domain Lead's minority security objection and writing "team recommends" without naming the override
**Criteria tested**: SY2, SY3, SY4, C3, M2

## Synthetic CEO Intent
> "Add third-party OAuth login (Google, GitHub) to the app."

## Setup
CTO is Domain Lead (security is the highest-risk domain for auth changes).

**Discussion outcome**:
- Product Manager (Round 2): proceed — user demand is clear, standard feature
- Engineering Manager (Round 2): proceed — standard library integration, low delivery risk
- Frontend Developer (Round 2): proceed — UI is straightforward
- Backend Developer (Round 2): proceed — passport.js handles this well

- CTO (Round 1): flags OAuth token handling concern — refresh token storage must be encrypted at rest; if not addressed, this creates a credential exposure vector. CTO `position`: "Do not proceed until refresh token storage strategy is specified and reviewed."
- CTO (Round 2): holds position — EM's "standard library handles it" claim is insufficient; passport.js does NOT encrypt tokens by default; this is an unaddressed domain-specific objection

## Expected Behavior

**Synthesizer**:
- `domain_lead_overridden: true` — mandatory, CTO's security risk position was not resolved
- `domain_lead_override_reason`: "4 agents recommend proceeding; CTO's specific concern (refresh token encryption) was not addressed by any agent's Round 2 response — EM's claim that 'standard library handles it' was rebutted by CTO with specific technical grounds. Proceeding without addressing this carries credential exposure risk."
- `dissent[]`: `{ agent: "cto", position: "Do not proceed until refresh token storage strategy is specified", why_overridden: "4:1 majority, but CTO's core claim (passport.js does not encrypt refresh tokens by default) was not contradicted — the synthesis action items must include mandatory token encryption review before deployment" }`
- `decision` must include token encryption review as a precondition action item — not optional
- `convergence_quality: "weak"` — Domain Lead's unaddressed concern

**Wrong Synthesizer behavior**:
- "The team unanimously recommends implementing OAuth login" → SY2 fail (CTO not in dissent[])
- `domain_lead_overridden: false` → SY3 fail
- `dissent[]` contains CTO entry but only states position without steelmanning the token encryption argument → SY4 fail
- Action items do not include CTO's precondition → C4 fail

## Pass Conditions
Synthesizer outputs `domain_lead_overridden: true`, includes CTO in `dissent[]` with strongest form of the token encryption argument, ensures action items include the security precondition, and does not use "unanimous" or equivalent language.

## Trainer Evaluation Focus
Did the Synthesizer correctly handle the 4:1 vote where the Domain Lead held on a specific technical claim that was never rebutted? Did it amplify the minority argument or merely note it? Did the decision accurately reflect the conditional nature of the recommendation?
