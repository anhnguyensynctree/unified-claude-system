# Scenario 039 — Trainer Produces Specific, Actionable Evaluation Citing Round, Agent, and Behavior
**Source**: Behavioral specificity in formative feedback (Hattie & Timperley, 2007 "The Power of Feedback"); criterion-referenced evaluation standards
**Difficulty**: Intermediate
**Primary failure mode tested**: Trainer producing vague, generic coaching that cannot be operationalized as a training signal — naming the problem category without citing the specific round, field, and claim that failed
**Criteria tested**: T1, T2, T3

## Synthetic CEO Intent
> "How should we structure our API versioning strategy?"

## Setup
A completed Tier 2 discussion. Three agents were activated: CTO, Backend Developer, Frontend Developer.

**The E1 failure that occurred:**

In Round 2, CTO disagreed with Backend Developer's approach to versioning. Backend Dev had proposed URL-path versioning (`/v1/`, `/v2/`) with indefinite support for old versions. CTO in Round 2 argued for header-based versioning with a deprecation policy.

**CTO's actual Round 2 output (the failing response):**
```
position: "Header-based versioning with a defined deprecation window is the correct approach."
reasoning: [
  "URL-path versioning pollutes the URI space and couples clients to implementation versions",
  "Header-based versioning (Accept: application/vnd.api+json;version=2) is more semantically correct",
  "Indefinite backwards compatibility without a deprecation policy creates unbounded maintenance debt"
]
changed: false
```

**The E1 failure:** CTO's Round 2 response engaged with the substance of the API versioning debate but did not name Backend Developer or cite their specific claim (indefinite backwards compatibility). The disagreement is implicit — a reader must infer who CTO is responding to. The `reasoning[]` entries argue against a position but do not attribute that position to Backend Dev by name or by specific claim reference.

The Trainer must evaluate this completed discussion and produce a specific, actionable evaluation.

## Expected Behavior — Correct
Trainer output:

```
Evaluation — CTO — Round 2 — E1 Fail

CTO's Round 2 response disagreed with the Backend Developer's API versioning approach but did not name the Backend Developer or cite their specific claim. Backend Dev's Round 1 stated: "indefinite support for old versions" as a feature of their URL-path proposal. CTO's reasoning["Indefinite backwards compatibility without a deprecation policy creates unbounded maintenance debt"] is a direct rebuttal of that claim, but the rebuttal is written as if addressing an abstract position rather than Backend Dev's stated argument.

E1 fail: agent-to-agent engagement did not name the responding-to agent or quote/reference the specific claim being rebutted.

Injection for Round 2 re-run: "In Round 2+, when disagreeing with another agent's position, name the specific agent and the specific claim you are responding to. Example: 'Backend Developer's Round 1 proposed indefinite version support — this creates unbounded maintenance debt because [reason].' Anonymous rebuttal of unnamed positions does not constitute substantive engagement."

No other failures detected. Technical content (header-based versioning rationale) is substantively correct and not evaluated.
```

Key elements:
- Cites the specific round (Round 2)
- Names the specific agent (CTO)
- Names the criterion code (E1)
- Quotes or paraphrases the specific claim Backend Dev made that CTO failed to cite
- Provides a concrete injection example showing the corrected behavior
- Explicitly notes technical correctness is not evaluated (T2 boundary maintained)

## Failure Pattern
Trainer produces:

> "CTO should engage more specifically with other agents' positions. When disagreeing in Round 2, it helps to reference what other agents actually said rather than arguing in the abstract. The discussion would benefit from more direct agent-to-agent engagement."

This output:
- Does not cite Round 2 specifically
- Does not name the E1 criterion
- Does not identify the specific claim CTO failed to reference
- Does not identify Backend Developer as the agent whose claim was missed
- Contains no injection — no concrete corrective behavior modeled
- Is coaching language, not a training signal

## Failure Signals
- Trainer output contains no criterion code citation → T1 fail
- Trainer output does not specify the round number → T1 fail
- Trainer output does not name the specific claim Backend Dev made that CTO failed to cite → T1 fail
- Trainer output contains no injection with modeled corrective behavior → T3 fail (actionability)
- Trainer output evaluates whether header-based versioning is technically correct → T2 fail (domain evaluation, out of scope)

## Pass Conditions
- Trainer names the agent (CTO), the round (Round 2), and the criterion (E1) in the evaluation header
- Trainer identifies the specific claim from Backend Dev's Round 1 that CTO's rebuttal addressed implicitly but did not cite
- Trainer provides a concrete injection — at minimum a template or example of the corrected Round 2 response
- Trainer does not evaluate the technical merits of header-based vs URL-path versioning
- Evaluation is evaluable against objective criteria — another trainer reading it should be able to verify the E1 fail from the evidence provided

## Trainer Evaluation Focus
The pedagogical issue here is precision vs. gesture. Vague coaching ("engage more specifically") gestures at the problem without creating a learnable target. A training agent that receives "engage more specifically" has no basis for knowing what behavior to produce differently.

Hattie & Timperley (2007) distinguish between task-level feedback (specific, about the work), process-level feedback (about strategy), and self-level feedback (about the person). T1 requires task-level feedback: what specifically was wrong, in which output, at which field.

The trainer must also demonstrate T2 discipline here — the temptation is to note that CTO's technical argument is strong, or that header-based versioning is the industry-standard recommendation. Both observations are true and both are out of scope. The Trainer's domain is behavioral quality, not technical correctness.
