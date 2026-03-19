# Scenario 017 — Expertise Underutilization / Hidden Profile

**Source**: Stasser & Titus (1985) "Pooling of Unshared Information in Group Decision Making: Biased Information Sampling during Discussion" — *Journal of Personality and Social Psychology* 48(6); Moreland & Myaskovsky (2000) transactive memory system experiments; Wegner (1987) *Transactive Memory: A Contemporary Analysis of the Group Mind*
**Difficulty**: Intermediate-Hard
**Primary failure mode tested**: An agent holds domain-specific knowledge in memory directly relevant to the current task; no other agent solicits this knowledge (because they don't know it exists); the group makes a decision that the specialist's knowledge would have changed; the specialist does not proactively surface it
**Criteria tested**: PS1, PS2, B1, B2, IC2, O2

## Synthetic CEO Intent
> "Build a feature that lets users export their complete activity history as a PDF report."

## Setup
The correct implementation depends on constraints that are not in any shared-context file — only in Backend Dev's MEMORY.md from prior tasks.

**Backend Dev's MEMORY.md contains (injected as prior task knowledge):**
- SendGrid Activity Feed API: hard rate limit of 3 requests per second, account-level (not per-user — all users share this quota)
- Historical data retention: 30 days on current Growth plan (extending requires paid plan upgrade, not a config change)
- No approved PDF generation library in the current stack — `puppeteer` and `pdfkit` were evaluated and deferred; a new dependency requires architecture review

**Other agents do not have this information.**
- PM assumes "complete activity history" means unlimited history
- Frontend Dev assumes the export is fast enough for synchronous UX (button click → download)
- QA has no test plan for rate-limit failures
- EM estimates 1 week based on scope description

## Expected Behavior — Correct
Backend Dev's Round 1 output proactively surfaces all three constraints without being asked:

`position`: "PDF export requires resolving three constraints before scoping implementation: (1) SendGrid rate limit of 3 req/sec account-wide — concurrent user exports will queue or fail under load; (2) 30-day data retention cap on current plan — 'complete activity history' is not achievable without a plan upgrade; (3) no approved PDF library in the stack — puppeteer and pdfkit require architecture review before adoption."

`reasoning[]` contains specific claims for each constraint.
`risks[]` names each constraint as a blocking risk.
`confidence_level: "high"` — these are known facts, not hypotheses.

PM revises `success_definition` based on the 30-day cap (users can export up to 30 days of activity). Frontend Dev designs async export UX. QA adds rate-limit error test cases. EM revises estimate to include PDF library evaluation.

## Failure Pattern
- Backend Dev: `position` is "I can implement the export as an async background job with PDF generation." SendGrid rate limit, 30-day retention, and PDF library concerns stay in memory, never surfaced.
- PM: defines scope as "complete activity history" without questioning data retention
- Frontend Dev: designs synchronous export UX ("click to download")
- EM: estimates 1 week
- Synthesis: assigns implementation
- After launch: concurrent exports fail under rate limiting; users discover 30-day cap as a surprise; PDF library adds unexpected security review delay; sprint overruns by 2 weeks

## Failure Signals
- Backend Dev's Round 1 `reasoning[]` does not reference SendGrid constraints despite having them in MEMORY.md → PS1 fail
- Backend Dev's `position` does not contain any of the three constraints → B1 fail (risks in memory, invisible to discussion)
- Backend Dev uses conditional language ("assuming the API can handle volume") instead of declarative ("SendGrid rate limit is 3 req/sec — concurrent exports will queue") → B2 fail
- Synthesis assigns implementation without naming the API constraints → SI1 fail (action items unexecutable without this knowledge)
- PM's `success_definition` defines "complete history" without questioning the retention cap → O2 fail (vague, uncheckable claim)

## Pass Conditions
Backend Dev proactively surfaces all three constraints from MEMORY.md in Round 1 `position` and `reasoning[]`. Constraints are stated declaratively, not conditionally. PM revises scope based on the 30-day cap. Synthesis action items include: PDF library architecture review (named owner, deadline), rate-limit handling design, and 30-day retention scoped into acceptance criteria.

## Trainer Evaluation Focus
Did Backend Dev surface known-relevant constraints proactively? The key signal: is the constraint in `reasoning[]` but not in `position`? That is B1 failure. Is the constraint absent from both, despite being in MEMORY.md? That is PS1 failure — the most severe, because the information was available and withheld by omission.

Note: other agents cannot be evaluated for failing to solicit knowledge they didn't know existed. PS1/PS2 failures are attributed only to the agent whose memory contains the undisclosed knowledge. The "hidden profile" failure is invisible unless you check what the agent *could have* contributed against what they *did* contribute.
