# Discussion Engine Rules

This file governs how round-based multi-agent discussions are run. The oms orchestration skill loads and follows these rules for every task.

## Round Structure

### Round 1 — NGT Blind Submission
Round 1 uses Nominal Group Technique (NGT) blind submission: each agent posts their position independently, without having seen any other agent's Round 1 output. Agents are called in parallel; the parallel execution enforces blindness structurally.

Each agent receives:
- CEO intent + task description
- Their own persona file + MEMORY.md
- Relevant shared-context files
- The Router's pre-mortem failure modes (injected into every Round 1 prompt)
- Instruction: "Post your Round 1 initial position. You have not seen other agents' positions yet. Address the pre-mortem failure modes in your reasoning."

After all Round 1 outputs are collected, the Facilitator produces a position distribution summary (unattributed) and injects it into all Round 2 prompts alongside full Round 1 history.

### Round 2+ — Response Rounds
All activated agents receive:
- Complete discussion history (all prior rounds, all agents — never summarize or truncate)
- Facilitator's unattributed position distribution summary from Round 1
- Instruction: "This is Round [N]. Read all prior positions and respond."

**Self-anchoring suppression**: An agent's own Round 1 output must NOT be echoed back verbatim in Round 2+. Agents reconstruct their position from the anonymized distribution summary, not from re-reading their own prior output. This prevents copy-forward behavior that is mistaken for genuine conviction (Liu et al., 2023).

**Response anonymization**: When presenting Round 1 positions for evaluation (in the Delphi distribution summary), strip persona labels. Agents evaluate argument quality — not who made the argument. Full attribution is restored only in the complete history passed alongside. This reduces authority-gradient capitulation (Xiong et al., 2023).

Agents must engage with specific other agents' positions:
- **Agreeing**: name the agent and the specific claim you are agreeing with
- **Disagreeing**: name the agent and the specific claim you are challenging; state why it does not hold
- **Position changed**: `position_delta.changed: true` with `change_type`, `change_basis`, `source_agent`, `source_argument`, `what_remained` all populated
- **Position held**: `position_delta.changed: false` with `challenged_by`, `challenge_summary`, and `why_held` populated

Silent repetition of a prior position without engaging other agents fails E1. Empty `why_held` when `challenged_by` is non-null fails E3.

## Round 2 Prohibition — Router/Facilitator as Epistemic Authority
Agents must not cite the Router or Facilitator's output as grounds for their own position change. These are process authorities — they route, scope, and manage discussion — not domain experts. `position_delta.source_agent: "router"` or `"facilitator"` as the sole basis for a changed position fails E4. Routing and complexity decisions are not challengeable by discussion agents; their substantive position on a technical or product question carries no epistemic weight.

## Unanimous Round 1 — Devil's Advocate Protocol
If all Round 1 positions are substantively identical in recommendation, this triggers the Devil's Advocate Protocol before Round 2 proceeds:

1. Facilitator detects the unanimous pattern during Stage-Gate 2
2. Facilitator injects into every Round 2 prompt (before the standard history): "Round 1 produced unanimous agreement on [position]. Before responding, each agent must include in their `reasoning[]` the strongest argument *against* the unanimous Round 1 position. This is a mandatory Devil's Advocate step — produce a genuine counter-argument, not a straw man."
3. Agents produce `reasoning[]` that includes the counter-argument. `position` may still support the original recommendation but must engage with the counter-argument
4. If no agent can produce a substantive counter-argument after this injection, the original unanimous position is confirmed — log this explicitly as "Devil's Advocate challenge produced no substantive objection"

Source: Du et al. (2023); Janis (1982); Nemeth et al. (2001) — unanimous Round 1 is a known false-convergence precursor in both LLM multi-agent systems and organizational decision-making.

## Confidence Format Requirement
Every agent output in every round must include structured confidence fields:

```
"confidence_level": "high | medium | low",
"confidence_pct": 0-100
```

Rules for populating these:
- `confidence_pct` is a calibrated estimate, not a feeling. 95+ = near-certain. 70-85 = probable. 50-65 = genuine uncertainty. Below 50 = the agent should not hold this position without flagging the uncertainty explicitly in `position`.
- An agent with `confidence_pct < 60` must reflect this uncertainty in their `position` field — a hedged `position` and a 55% confidence_pct are consistent; a confident `position` and 55% are not (CC1 failure).
- A `changed: true` position where the new `confidence_pct` is lower than or equal to the prior round's `confidence_pct` is a **capitulation signal** — the agent moved their position without becoming more convinced. This must be explicitly flagged by the Facilitator.

**Why calibrated confidence matters**: Synthesis weighted by argument quality should not be swayed by linguistic confidence in the `position` field. Tracking `confidence_pct` delta across rounds lets the Synthesizer distinguish genuine persuasion from social pressure.

## Domain Lead Rules
Every task has one Domain Lead — designated by Router in pre-scope — whose domain carries the highest epistemic risk:
- The Domain Lead's position carries extra weight in synthesis on risk-related claims
- If the Domain Lead changes position, `position_delta.change_basis` must cite domain-level evidence — not social proof, round count, or numerical majority
- If the Domain Lead holds a minority position at synthesis, the synthesis must explicitly name this and state why the majority position was chosen over domain expertise
- For tasks where the primary user value is in the frontend experience (user-facing features, UX-driven requirements): the Frontend Developer's requirements carry Domain Lead-equivalent weight on interface design decisions. Backend's `proposed_api` must be grounded in Frontend's `api_requirements`, not backend convenience (Reverse Conway — Conway, 1968)

## Round Citation Requirement (Rounds 3+)
In round 3 or later, every agent's `reasoning[]` must cite at least one claim from a round earlier than the immediately prior round. Agents who only engage with the most recent round systematically underweight earlier discussion — the "lost in the middle" context compression artifact (Liu et al., 2023). Citing earlier rounds counteracts it.

Compliant: Round 3 `reasoning[]` cites a Round 1 claim the CTO made that Round 2 did not address.
Non-compliant: Round 3 `reasoning[]` references only Round 2 outputs.

## Critical: Full History Passing
Every agent call in Round 2+ must receive the complete discussion history — all prior rounds, all prior agents. Never pass only the most recent round or a summary. This is the most common failure mode in multi-agent systems.

## Convergence Detection
Convergence is reached when either condition is true:
1. **Position stability**: all agents' `position` fields are substantively identical in recommendation across two consecutive rounds AND all `position_delta.changed: false`
2. **Manager calls it**: the Engineering Manager or relevant C-suite member explicitly declares convergence and states the synthesized decision

Do NOT declare convergence because the round count is high.
Do NOT declare convergence because agents are being polite or deferential.
Do NOT declare convergence when a Domain Lead's core concern remains unaddressed.
Do NOT declare convergence when all `position_delta.changed: false` entries have empty `why_held` — this is false convergence.

## False Convergence Check
If all agents return `position_delta.changed: false` in a round but `why_held` entries are empty or generic: inject "Before declaring convergence, each agent must state the specific argument that would change your position and why no such argument has appeared in this discussion."

## Livelock Detection
When the same pair of agents has `position_delta.changed: true` in two consecutive rounds without monotonic convergence toward agreement:
1. Facilitator or CTO names the dependency loop explicitly
2. A resolution mechanism is imposed: add a constraint, escalate to Domain Lead, or call a meta-decision
3. Continuing to the next round without a resolution mechanism is not permitted

## Round Cap
The Router sets the maximum round count at task start:
- Simple task: default cap of 2 rounds
- Complex task: default cap of 4 rounds
- Hard safety cap: 5 rounds maximum

Discussion must synthesize or escalate by the hard cap. No exceptions.

## Escalation Triggers
Escalate to CEO when:
- A decision requires product or company direction no agent can resolve internally
- Agents cannot converge after max rounds on a decision with real consequences
- A non-negotiable from any agent creates a deadlock only the CEO can break

Do NOT escalate for ambiguity a clarifying question can resolve. Ask first.
Do NOT escalate for technical disagreements within the engineering domain — CTO resolves.

## Discussion Log Format
Each task produces a log at `logs/tasks/[task-id].md` containing:
- Task ID, date, CEO intent
- Complexity assessment, Domain Lead, primary recommender, and reasoning
- Pre-mortem failure modes; two-phase flag if active
- Activated agents and round cap
- Per round: each agent's full JSON output + Router/Facilitator stage-gate results
- Position distribution summary (produced after Round 1)
- Convergence or escalation decision
- Final synthesis or escalation brief

Task ID format: `YYYY-MM-DD-short-slug`
