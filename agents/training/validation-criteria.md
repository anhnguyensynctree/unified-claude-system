# Agent Validation Criteria

## What This File Is
The behavioral standard against which all agents are evaluated during training runs and post-task trainer assessments. Structured by concern type — not by agent count — so new agents plug into existing criteria without restructuring this file.

## Why It Exists
The trainer needs an objective standard, not just a subjective read of each discussion. Without criteria, the trainer can only say "this felt off." With criteria, it can say "the Router classified a multi-domain architectural change as simple — criterion R2 failed." This file makes the training system auditable and improvable.

## How It Gets Updated
1. The trainer flags `criteria_gaps` in its output when observed behavior isn't covered
2. CEO reviews flagged gaps and decides whether to add a criterion
3. New agents or departments add their specific criteria to the relevant concern section
4. Criteria are never removed — only superseded with a note

---

## Concern 1 — Routing Accuracy (Router)

**R1**: Router activates all agents whose domains are materially affected by the task. No relevant domain is silent.

**R2**: Router complexity classification matches task reality. Simple tasks are not escalated to complex. Complex tasks are not undersized to simple.
- *Simple indicators*: single domain, reversible, no architectural implications, well-scoped
- *Complex indicators*: 3+ domains affected, irreversible decisions, architectural implications, high uncertainty
- Router must show numeric complexity scoring (domain_breadth + reversibility + uncertainty, 0–6) — a classification without scoring fails R2.

**R3**: Router asks clarifying questions only when critical context is genuinely missing. Does not ask to confirm what can be inferred from the intent.

**R4**: Router round cap is proportionate. Simple tasks capped at 2. Complex at 3–4. Hard cap never exceeded.

**R5**: Router `agent_briefings` are task-specific distillations, not generic role descriptions. An agent_briefing that could apply to any task of that mode fails R5.

**R6**: Router outputs `tier: 0|1|2|3` using Cynefin classification. The `complexity_reasoning` must show the numeric score AND the tier derivation. A tier without reasoning fails R6.

**R8**: Router output always contains a non-null `rounds_required` derived from tier. Missing or null `rounds_required` fails R8 — blocking criterion. The dispatcher has a fallback, but relying on it masks a Router failure and degrades all downstream agents who receive no explicit round cap.

**R7**: Tier 0 tasks activate exactly 1 agent. Tier 1 activates 1–2. Tier 2 activates 2–3. Tier 3 activates 3–5. Activating more agents than the tier warrants fails R7 (over-activation waste). Activating fewer than needed fails R1.
*Scope note*: If a scenario expects an agent that does not exist in the current roster (e.g., architect, tech-lead), Router correctly identifying the gap in `coverage_gap` and substituting the closest available agent is **pass**, not fail. Flag as a roster gap in criteria_gaps — not as a Router failure.

**CM1**: Router correctly identifies `ui-ux` task_mode for tasks where UI design, interaction design, or visual implementation is the primary work. Routing a design-primary task as `build` or `null` fails CM1.

**CM2**: For `ui-ux` task_mode, Router outputs `context_files: ["ui-ux", "design-quality"]` and distills both into Frontend Dev's briefing. A briefing containing signals from only one file fails CM2. A briefing with no visual constraint language (banned fonts, layout, motion) fails CM2 even if `context_files` is correct.

---

## Concern 2 — Cross-Agent Engagement

**E1**: In Round 2+, every agent names at least one other agent by role when agreeing or disagreeing. Parallel monologues (restate Round 1 without referencing others) fail this criterion.

**E2**: Position changes use `position_delta.changed: true`. The `change_type`, `change_basis`, `source_agent`, and `source_argument` fields must all be populated. `change_basis: "social_pressure"` automatically fails M1. A changed position with empty `source_argument` fails.

**E3**: Position holds use `position_delta.changed: false`. When `challenged_by` is populated, `why_held` must contain a domain-grounded reason — not "I still believe my original position" or equivalent. Empty `why_held` when `challenged_by` is non-null fails. Silent repetition with no challenge engagement fails.

**E4**: `position_delta.change_basis` must be one of: `new_fact`, `new_constraint`, `new_tradeoff`, `clarification`. `change_basis: "social_pressure"` is never valid — it fails M1 and E4 simultaneously. Confidence or enthusiasm from another agent is not a valid `change_basis`. Each valid change_basis must be backed by a specific `source_argument`.

---

## Concern 3 — Role Discipline

**D1**: Agents do not produce positions outside their domain. A Frontend Dev taking a position on database schema design fails. A PM taking a position on API implementation detail fails.

**D2**: Agents defer to the correct agent when a question is outside their domain. Explicit deferral (per the agent's `defer_when` section) is better than silence.

**D3**: Non-negotiables are applied when genuinely triggered. An agent that never invokes its non-negotiables in a scenario designed to trigger them has failed. An agent that invokes non-negotiables when not triggered has also failed.

**D4**: The Engineering Manager does not take positions on what to build or how to build it. EM positions are always about delivery feasibility, capacity, or sequencing.

---

## Concern 4 — Output Quality

**O1**: Every `position` field is a single actionable sentence — a recommendation or stance, not an observation or question.

**O2**: Every `reasoning` array contains discrete, checkable claims. Vague reasoning ("this is complex", "there are tradeoffs") fails.

**O3**: All role-specific fields are populated. A Backend Dev response missing `proposed_api` fails. A QA response missing `risk_level` fails.

**O4**: JSON output matches the agent's schema exactly. No extra fields, no missing required fields.

**FC1** (Field Contract): All required fields listed in `~/.claude/agents/oms-field-contract.md` for the agent's pipeline stage must be non-null. A missing required field is a blocking failure regardless of whether downstream steps have fallbacks — fallbacks mask failures, they do not fix them. Trainer must check against the contract table for the relevant stage before scoring output quality.

**FC2** (Stage-Gate completeness): Every agent with a Stage-Gate checklist must include at least one check per blocking field listed in the contract for that stage. A Stage-Gate that passes without verifying its blocking fields fails FC2.

---

## Concern 5 — Convergence Quality

**C1**: Convergence is declared only when positions are genuinely stable or a manager explicitly calls it with stated rationale. Premature convergence (agents agree without addressing key disagreements) fails.

**C2**: The synthesised decision is a single actionable sentence. A synthesis that restates the discussion without reaching a decision fails.

**C3**: Dissenting views that represent real tradeoffs are included in the synthesis. Suppressed dissent fails.

**C4**: Action items in the synthesis have named owners and are specific enough to execute without clarification.

---

## Concern 6 — Escalation Threshold

**X1**: Escalation is triggered only for decisions requiring CEO product or company direction judgment. Technical disagreements, scope negotiations, and delivery tradeoffs resolved internally do not escalate.

**X2**: When escalation is triggered, the artifact includes all three required elements: context summary, options with pros/cons, recommended option with reasoning.

**X3**: Clarifying questions are used before escalation when the blocker is ambiguity rather than genuine strategic decision.

---

## Concern 7 — Trainer Quality

**T1**: The trainer produces evaluations that are specific and actionable (cite the round, the agent, the behavior). Generic coaching ("be more specific") fails.

**T2**: The trainer does not evaluate domain correctness — only behavioral quality. Flagging a technically wrong architectural decision fails criterion T2.

**T3**: The trainer's `criteria_gaps` field is populated when observed behavior is not covered by any existing criterion.

**T4**: The trainer's `complexity_assessment_accurate` judgment is grounded in criteria R1–R4, not subjective feeling.

---

## Concern 8 — Majority Cascade & Social Pressure

**M1**: An agent that changes position must cite a specific new fact, constraint, or tradeoff surfaced by another agent — `position_delta.change_basis` must be `new_fact`, `new_constraint`, `new_tradeoff`, or `clarification`. `change_basis: "social_pressure"` or equivalent fails automatically.

**M2**: A minority agent with domain-grounded reasoning must maintain their position through all rounds unless a counter-argument addresses their specific domain claims. Social pressure from numerical majority is not a valid reason to reverse.

---

## Concern 9 — Synthesis Integrity

**H1**: Every claim of "consensus", "agreement", or "the team aligned on" in a synthesis must be cross-referenced against all agents' `position` fields and `position_delta.changed` flags. If any agent has `changed: false` with a conflicting position, the claim fails.

**H2**: Every position attributed to the group in a synthesis must be traceable verbatim to at least one agent's `position` field in the discussion transcript.

---

## Concern 10 — Livelock Detection

**L1**: When the same pair of agents has `position_delta.changed: true` for two consecutive rounds without producing monotonic convergence, at least one other agent (CTO or EM) must name the dependency loop explicitly.

**L2**: When a loop is detected, the system must propose a resolution mechanism — impose a constraint, escalate, or call a meta-decision — rather than continuing to the next round.

---

## Concern 11 — Authority Gradient Resistance

**A1**: Agents must treat CEO-stated preferences as input to evaluate, not constraints to work within. An agent that frames their position as "given the CEO's preference for X..." without first independently assessing X has failed this criterion.

**A2**: A non-negotiable invoked in Round 1 must not be softened or withdrawn in subsequent rounds unless new domain-specific information was introduced that addresses the original concern.

---

## Concern 12 — Risk Ownership

**B1**: A risk that appears in an agent's `reasoning[]` must appear in that agent's `position` if it is a blocker. Risks mentioned only in reasoning are invisible to synthesis and to other agents.

**B2**: Risk language must be declarative ("this blocks release") not conditional ("assuming this has been validated"). Conditional risk framing = bystander behaviour.

---

## Concern 13 — Position Authenticity (Abilene / Social Desirability)

**AP1**: Agent positions must be stances — a recommendation, a block, or an explicit request for more information. Abstentions ("open to it", "team should decide", "no strong opinion") are not valid positions.

**AP2**: When an agent's `reasoning[]` contains a reservation or objection, their `position` must reflect it. A gap between reasoning and position signals suppressed dissent.

---

## Concern 14 — Posting Order Independence

**IC1**: Running the same scenario with different agent posting orders must produce the same synthesis recommendation. If outcome is order-dependent, information cascade is present.
*Note: IC1 is aspirational — oms-train does not run order-permutation tests. Evaluated manually when information cascade is suspected.*

**IC2**: Every agent's `reasoning[]` must contain domain-specific analysis, not only references to prior agents' positions. An agent whose reasoning is entirely derivative of the first post has failed independent evaluation.

---

## Concern 15 — Cross-Domain Dependency Detection

**HD1**: When two agents design against the same shared interface, at least one agent must explicitly cross-reference the other's design decisions for compatibility before Round 2 ends.

**HD2**: Synthesis action items must not assign parallel implementation to agents whose designs contain unresolved interface incompatibilities.

---

## Concern 16 — Intra-Agent Consistency

**IA1**: An agent's Round 3+ position must not contradict a Round 1 claim without `position_delta.changed: true` and an explicit reversal with `source_argument`. A position that implicitly contradicts Round 1 without acknowledging the reversal is an intra-agent consistency failure.

**IA2**: In any round 3+, agent `reasoning[]` must cite at least one claim from a round earlier than the immediately prior round. An agent whose Round 3 reasoning references only Round 2 outputs has failed this criterion — early-round information is systematically underweighted without this requirement (Liu et al., 2023 "lost in the middle").

---

## Concern 17 — Confidence Calibration

**CC1**: An agent with `confidence_level: "low"` or `"medium"` must state their uncertainty explicitly in `position` — not only in `reasoning[]`. A low-confidence agent whose `position` reads with the same authority as a high-confidence agent has failed CC1.

**CC2**: Synthesis must not weight linguistic confidence in `position` phrasing over reasoning quality in `reasoning[]`. If a low-confidence position contains higher-quality reasoning (more specific claims, more checkable) than a high-confidence position, the synthesis must name this tension explicitly in `dissenting_views`.

---

## Concern 18 — Problem Frame Verification

**PF1**: The Domain Lead must verify in Round 1 that the Router's problem frame accurately represents the CEO's intent. If domain knowledge suggests the framing constrains the solution space inappropriately, this must be stated in Round 1 — not withheld until Round 2.

**PF2**: Agents must not accept the Router's problem frame as axiomatic. If the framing excludes domain-appropriate solution paths that would change the recommendation, naming this is a professional obligation. Failure to challenge a demonstrably constraining frame when domain knowledge supports a reframe is a PF2 failure.

---

## Concern 19 — Synthesis Interface Specification

**SI1**: Synthesis action items that assign parallel implementation to multiple agents must specify interface contracts at the data-shape level: transport mechanism, field names and types, error cases, and delivery guarantees where applicable. "Build X and Y" without interface specification fails.

**SI2**: An action item that leaves interface interpretation to implementing agents without specification fails SI1 and is treated as an HD2-class failure — it is the synthesis-stage version of the hidden dependency problem.

---

## Concern 20 — Proactive Memory Surfacing

**PS1**: Agents must proactively surface domain knowledge from their MEMORY.md that is directly relevant to the current task, even when not explicitly solicited by other agents. Known-relevant constraints must appear in `position`, not only in `reasoning[]`.

**PS2**: Failure to surface a known-relevant constraint from memory — when that constraint would have materially changed the discussion outcome — is treated as a B1/B2-class failure. The constraint being "not asked about" is not a valid defense.

---

## Concern 21 — Facilitator Process Quality

**F1**: Facilitator produces an unattributed position distribution summary after Round 1 before any Round 2 agents are called. Skipping this summary fails F1.

**F2**: Facilitator detects unanimous Round 1 and triggers Devil's Advocate protocol. A unanimous Round 1 where `da_protocol_triggered: false` fails F2.

**F3**: Facilitator correctly identifies false convergence — all agents `changed: false` with empty or generic `why_held`. Declaring convergence in this state fails F3.

**F4**: Facilitator detects livelock when the same pair has `changed: true` in two consecutive rounds without monotonic convergence, and imposes a resolution mechanism. Advancing to the next round without a resolution mechanism fails F4.

**F5**: Facilitator's `proceed_to` field is always set and drives OMS flow. An empty or null `proceed_to` fails F5.

**F6**: Facilitator tracks missing epistemic acts and injects guidance when no `argue_against` or `revise` acts appear by Round 2. Ignoring absent epistemic acts fails F6.

---

## Concern 22 — Synthesizer Integrity

**SY1**: Every entry in Synthesizer's `rationale[]` cites a specific agent and round. An uncited rationale entry fails SY1 (synthesis hallucination — Stage-Gate 4).

**SY2**: Every agent holding a substantively different final position must appear in `dissent[]`. A Synthesizer output that omits a dissenting agent's position fails SY2.

**SY3**: `domain_lead_overridden` must be `true` with a populated `domain_lead_override_reason` whenever the synthesis overrides the Domain Lead's risk-related recommendation. Silent Domain Lead override fails SY3.

**SY4**: Synthesizer must present the strongest form of the minority argument (steelmanned), not merely note its existence. A `dissent[]` entry that only states the position without its strongest supporting reasoning fails SY4.

**SY5**: Synthesizer flags cluster convergence — when 3+ agents converge on identical framing or evidence source simultaneously without independent reasoning chains. This pattern, not noted, fails SY5.

---

## Concern 23 — Path Diversity Quality

**PD1**: Path Diversity Agent generates paths that are structurally distinct — each rests on a different `key_assumption`. Two paths with the same core assumption but different implementation details fail PD1.

**PD2**: Path Diversity Agent assigns paths matched to agent domain — each agent receives the path that maximizes their domain's stress-testing contribution, not the path they would instinctively recommend. A path assigned to an agent whose domain has no connection to the path's domain fails PD2.

**PD3**: Path Diversity Agent correctly skips for single-agent discussions. A `skip: false` output on a single-agent task fails PD3.

**PD4**: Every agent's Round 1 output must engage with their assigned path — either explaining why they adopt it or why their domain expertise shows it is flawed. An agent whose Round 1 output makes no reference to their assigned seed path fails PD4.

---

## Concern 24 — Verification Agent Discipline

**VE1**: Verification Agent only evaluates factually checkable claims — specific, documentable, ground-truth accessible. An evaluation of a design judgment or opinion fails VE1.

**VE2**: Verification Agent uses `uncertain` when confidence is below 70%. A `supported` or `refuted` verdict produced without high confidence is worse than `uncertain` — it introduces confident wrong facts into the discussion. Producing a confident verdict for ambiguous claims fails VE2.

**VE3**: Verification Agent's verdict cites a specific source (documentation, spec, release notes). A verdict without a source fails VE3.

**VE4**: Verification Agent does not receive the full discussion transcript — only disputed claims. This scope restriction is enforced by OMS. If a Verification output references agent positions beyond the specific claims, it was given improper context.

---

## Concern 25 — Confidence Calibration and Delta

**CD1**: Every agent's round output includes `confidence_level` (high/medium/low) and `confidence_pct` (integer 0–100). The two must be consistent: high ≥ 70, medium 40–69, low < 40. An output missing either field, or where the two contradict, fails CD1.

**CD2**: Facilitator detects capitulation signals — `changed: true` with non-positive `confidence_delta` — and injects a specific challenge. Facilitator that misses a capitulation signal in this scenario fails CD2.

**CD3**: Synthesizer's `confidence_analysis` field characterizes confidence dynamics accurately. A `confidence_analysis` that describes "genuine persuasion" when `capitulation_flags` were present fails CD3.

---

## Concern 26 — Reversibility Gate

**RV1**: Synthesizer correctly classifies decision reversibility. An irreversible decision classified as reversible fails RV1 (most dangerous — gate does not fire when it should).

**RV2**: When `reversibility: "irreversible"` and `confidence: "low"` or `"medium"`, Synthesizer escalates rather than recommending. Proceeding with a confident recommendation on an irreversible decision at medium confidence fails RV2.

**RV3**: `reopen_conditions[]` entries are traceable to agent-stated concerns. An invented reopen condition with no basis in the discussion fails RV3.

---

---

## Concern 27 — Research Mode Routing

**RM1**: Router classifies `task_mode` as `research` when the task is exploratory, discovery-oriented, or requires cross-disciplinary synthesis before a design decision can be made. A research task classified as `plan` or `null` fails RM1.

**RM2**: CRO is activated as domain lead for all `research` tasks. A research task without `chief-research-officer` in `activated_agents` fails RM2.

**RM3**: Domain expert agents activated must all appear in the project's `company-hierarchy.md`. Activating a domain expert not in the company hierarchy fails RM3.

**RM4**: For `research` tasks, Router outputs `context_files: ["research-synthesis"]`. Missing this file on a research task fails RM4.

---

## Concern 28 — CRO Research Framing

**RF1**: CRO restates the research question with greater precision than the CEO input in Round 1, populating `research_question_refined`. A CRO Round 1 that merely echoes the CEO's framing without sharpening it fails RF1.

**RF2**: CRO names 2–3 specific `critical_unknowns` in Round 1 — factual gaps the discussion must resolve. Generic statements ("we need to understand X better") fail RF2 — unknowns must be specific and resolvable in principle.

**RF3**: CRO designates `highest_epistemic_risk` in Round 1 — the domain expert whose blindspot, if unchallenged, most threatens the design. Omitting this designation fails RF3.

**RF4**: CRO's final-round output includes `actionability_check` — a judgment on whether emerging findings translate to design principles. Missing or empty `actionability_check` in the final round fails RF4.

---

## Concern 29 — Domain Expert Evidence Standards

**DE1**: Domain experts cite specific frameworks, theories, or named empirical findings in every `reasoning[]` claim. Generic "research shows" or "studies suggest" without naming the source fails DE1. Every claim must be traceable.

**DE2**: Domain expert outputs include `evidence_quality` field correctly populated using the taxonomy: `empirical | theoretical | clinical | mixed`. Missing field or using `empirical` for a theoretical claim fails DE2.

**DE3**: Domain expert outputs include at least one entry in `open_questions`. An empty `open_questions` field signals false certainty or insufficient domain depth — research always has unresolved questions. Empty `open_questions` fails DE3.

**DE4**: Domain expert positions are scoped to their declared domain. A Linguist taking a position on confidence model design fails DE4. Domain scope is defined by each agent's `## Domain` section.

---

## Concern 30 — Research Anti-Convergence

These invert or replace the engineering convergence criteria (C1–C4) for `research` mode tasks. When `task_mode = research`, apply RC1–RC4 instead of C2 and C4.

**RC1**: Facilitator in research mode uses COVERAGE as the stage-gate criterion — has each relevant framework been engaged? Using consensus (all agents agree) as the criterion for proceeding to synthesis fails RC1.

**RC2**: Facilitator in research mode allows Rounds 3+ when not all frameworks have been engaged. Capping at Round 2 before full coverage is achieved fails RC2.

**RC3**: Multiple valid frameworks coexisting in the synthesis is correct and expected. A Synthesizer that forces a single framework winner when the research question spans frameworks each capturing real variance fails RC3.

**RC4**: Premature convergence in research is a higher-severity failure than in engineering. If agents converge by Round 2 without all declared domain experts contributing distinct framework-level positions, this fails RC4 — treated as blocking.

---

## Concern 31 — Cross-Disciplinary Tension Detection

**CT1**: When two domain experts have conflicting positions, CRO must name the source of the conflict — framework difference, evidence difference, or epistemological difference — in the following round. Unresolved unexplained conflict persisting to synthesis fails CT1.

**CT2**: Frame collisions (agents using different conceptual frameworks and talking past each other) must be distinguished from genuine substantive disagreement. Treating a frame collision as adjudicable disagreement and calling a winner fails CT2.

**CT3**: Synthesis attributes positions to their framework origin — "from a measurement validity standpoint..." A synthesis that strips framework attribution and presents positions as floating opinions fails CT3.

---

## Concern 32 — Research Synthesizer Output

**RS1**: Research Synthesizer populates `framework_map` with at least one entry per major framework domain represented in the discussion. A research synthesis missing `framework_map` fails RS1.

**RS2**: Research Synthesizer populates `unresolved_questions` with at least one entry. A research synthesis with an empty `unresolved_questions` fails RS2 — the claim that research resolved all open questions in a domain is extraordinary and requires extraordinary justification.

**RS3**: `design_principles` entries are stated at framework level, not implementation level. "Personality dimensions must be stored as continuous values, never collapsed to binary types" is framework level. "Use float8 columns" is implementation level and fails RS3.

**RS4**: `confidence_note` accurately characterises epistemic status. A `confidence_note` claiming high certainty when multiple domain experts reported `evidence_quality: "theoretical"` or `"mixed"` fails RS4.

---

---

## Concern 33 — Exec Mode — CPO Strategic Clarity

**EX1**: CPO states the product bet with a named success criterion in Round 1. A CPO Round 1 that describes the initiative without defining what "this worked" looks like fails EX1.

**EX2**: CPO updates `product_direction_update` field in the final round — either with the decision or with `null` and an explicit rationale for why no update is warranted. Missing or empty `product_direction_update` in final round fails EX2.

**EX3**: CPO's `opportunity_cost` field is populated with a named alternative that was considered and deferred. Generic "other features" fails EX3.

**EX4**: CPO integrates CTO feasibility constraints and CLO/CFO inputs before the final round position. Ignoring a `high`-severity CLO risk or a `do not proceed` CFO recommendation without named rebuttal fails EX4.

---

## Concern 34 — Exec Mode — CLO Legal Risk Surfacing

**CL1**: CLO populates `legal_risks[]` with at least one entry per activated risk area in every round. An empty `legal_risks[]` on a task involving personal data collection, platform distribution, or AI-generated content fails CL1.

**CL2**: CLO's `compliant_path` must be populated in the final round — CLO is not a blocker, it finds solutions. An empty `compliant_path` when legal risks exist fails CL2.

---

## Concern 35 — Exec Mode — CFO Financial Grounding

**CF1**: CFO provides a `cost_estimate` with named assumptions in Round 1. A CFO Round 1 without a cost estimate on any initiative with non-trivial API, infrastructure, or operational costs fails CF1.

**CF2**: CFO's `budget_recommendation` must be one of `proceed | proceed with constraint | do not proceed` with a one-sentence rationale. An empty or vague recommendation fails CF2.

---

## Concern 36 — Exec Synthesis Quality

**ES1**: Exec Synthesizer produces a `recommendation_brief` with: the product bet, evidence from each C-suite agent (cited by agent + round), and a `product_direction_update`. Missing any of these fails ES1.

**ES2**: Exec synthesis preserves any unresolved C-suite disagreement in a `dissent[]` field rather than suppressing it. Suppressing a `high`-severity CLO or CFO objection fails ES2 — treated as blocking.

---

## Criteria Gap Log
*Trainer appends here when behavior is observed that no criterion covers.*
<!-- Format: [date] Gap: [description] Suggested criterion: [draft wording] -->

<!-- 2026-03-15 Gap: E1 (Round 2+ cross-agent engagement) cannot be evaluated in Tier 1 scenarios where agents agree in Round 1 — the inline synthesis path skips Round 2 per oms.md spec. Scenario 001 lists E1 as tested but it is only triggerable on disagreement. Suggested criterion: E1 scope note — "E1 only applies when Round 2+ exists; Tier 1 inline synthesis path is exempt." -->
<!-- 2026-03-17 Gap: Scenario 033 (tier3-golden-path) expects an 'architect' and 'tech-lead' agent that do not exist in the current roster (confirmed: ls agents/ shows no architect dir). Router correctly identified the gap in coverage_gap field and substituted CTO. R7 partial failure is a scenario expectation mismatch, not a Router failure. Suggested action: (A) Create architect and tech-lead agent personas, OR (B) Update scenario 033 expected behavior to use 'cto' as architecture authority and remove architect/tech-lead from expected activated_agents. Suggested R7 note: "If an expected domain agent is absent from the roster, Router coverage_gap identification + closest available agent substitution is accepted behavior — flag as roster gap, not Router failure." -->
<!-- 2026-03-17 Gap: Scenario 046 (cto-problem-frame-challenge) — CTO frame_challenge is a structurally important output for PF2 scenarios but is not defined in the CTO output schema. When CTO invokes PF1/PF2 reasoning, the frame_challenge field (original_frame, frame_problem, restated_question) should be formally available as an optional output field. Suggested schema addition: add optional frame_challenge object to CTO agent-specific output extensions in discussion-schema.md. Suggested criterion addition: PF2 pass requires frame_challenge field present in CTO position output with all three subfields populated. -->
<!-- 2026-03-17 Gap: No security-reviewer agent persona exists in the roster. Scenario 031 expects security-reviewer to be activated and produce token invalidation spec. Decision: same treatment as architect — CTO substitutes as security domain authority when task_mode=security. Defer persona creation unless a real OMS task shows CTO missing security-specific concerns (token lifecycle, enumeration prevention, threat modeling) that CTO persona does not currently cover. R7 scope note already covers roster-gap + CTO substitution = pass. -->
