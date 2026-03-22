# Decision Frameworks Reference

This file grounds OMS in established decision science. Each agent should cite relevant frameworks in their reasoning — not as decoration, but as epistemic scaffolding that makes positions auditable and challenges more precise.

**Load**: On-demand. Relevant agents: facilitator, path-diversity, synthesizer, ceo-gate, trainer.

---

## The Core Warning — LLM Trendslop Bias

Before frameworks: the documented failure mode this system must actively counter.

**Source:** "Researchers Asked LLMs for Strategic Advice. They Got 'Trendslop' in Return." — *Harvard Business Review*, March 2026

Researchers tested LLMs across thousands of business trade-offs (exploration vs. exploitation, differentiation vs. commoditization, automation vs. augmentation, centralization vs. decentralization). Across all models, LLMs consistently favored the same strategies regardless of context — the ones dominant in internet business writing: innovation, collaboration, differentiation, decentralization.

**What this means for every OMS agent:**
- Convergence on an "obviously good" answer (agile! ship fast! collaborate!) is a red flag, not validation
- The trendy option is often wrong — the right answer is context-specific, often unglamorous
- When all agents agree in Round 1 on a fashionable direction, the Facilitator must fire the Devil's Advocate protocol
- Path Diversity must actively seed the anti-consensus path: cost leadership, centralization, commoditization, constraint, reduction — not just innovation and growth

**Counter-measures already in OMS:**
- Path Diversity: assigns structurally distinct frames before discussion (one agent must hold the unglamorous path)
- Devil's Advocate: fires when Round 1 is unanimous — agents must argue against the consensus before Round 2
- Confidence calibration: high confidence on a trendy answer should be treated as a capitulation signal, not expertise
- CEO Gate research option: CEO can pause and ask "what do we know about this?" before committing to a fashionable direction

---

## Irreversibility — Bezos Type 1 / Type 2

**Source:** Jeff Bezos, Amazon 2015 Shareholder Letter

**Type 1 (one-way doors):** Irreversible or nearly irreversible. Require deliberation, deep analysis, multiple inputs. Mistakes are very hard to recover from.

**Type 2 (two-way doors):** Reversible, low-cost to undo. Should be made quickly by individuals or small teams. Over-applying Type 1 rigor to Type 2 decisions is the primary cause of organizational slowness.

**How OMS implements this:**
- Synthesizer's RAPID reversibility gate: irreversible + low/medium confidence → escalate, do not synthesize
- CEO Gate mandatory categories (1, 2, 4, 9) are all Type 1 decisions — they always surface to CEO
- CEO Gate bufferable categories (3, 5, 6, 7, 8) are conditionally Type 1 — their reversibility is assessed per context
- Agents must classify reversibility in every Round 1 output — this affects synthesis path
- `reopen_conditions[]` in synthesis = tripwires that convert a "resolved" decision back to open if conditions change

---

## Domain Classification — Cynefin

**Source:** Dave Snowden & Mary Boone, *Harvard Business Review*, November 2007

Five domains that determine decision approach:
- **Clear/Obvious:** Cause-effect is known. Best practice. Sense → Categorize → Respond.
- **Complicated:** Cause-effect requires analysis. Good practice. Sense → Analyze → Respond.
- **Complex:** Cause-effect only visible in hindsight. Emergent practice. Probe → Sense → Respond.
- **Chaotic:** No cause-effect. Novel practice. Act → Sense → Respond.
- **Disorder:** Domain unclear — most dangerous. Must break into component domains.

**How OMS implements this:**
- Router's tier classification is Cynefin: Tier 0 = Clear, Tier 1 = Complicated-low, Tier 2 = Complicated-high, Tier 3 = Complex
- Agents should name the domain when their reasoning differs based on uncertainty vs. complexity
- Complex domain tasks (Tier 3) require probing (more rounds, devil's advocate, verification) — not "analyze harder"
- Disorder/chaotic signals: Router cannot route → ask CEO for more context, stop

---

## Decision Participation — Vroom-Yetton-Jago

**Source:** Vroom & Yetton (1973), *Leadership and Decision-Making*; updated Vroom & Jago (1988)

Prescribes decision style based on problem attributes: quality requirement, leader's information, problem structure, acceptance need, conflict risk. Five styles: Autocratic I/II, Consultative I/II, Group II.

**Key principle:** Match participation level to the decision. Over-participation wastes time. Under-participation kills buy-in.

**How OMS implements this:**
- CEO Gate delegation levels (autonomous/selective/engaged) implement VYJ prescriptions
- `autonomous` = Autocratic II: C-suite decides, no CEO involvement for bufferable decisions
- `selective` = Consultative II: C-suite consulted, CEO decides on hardest calls
- `engaged` = Group II: all stakeholders involved, CEO stays informed on every strategic call
- Vroom-Yetton criterion "acceptance need" maps to `hard_block` in C-suite round — an agent who can't accept the decision flags it, preventing false consensus

---

## Role Clarity — RAPID Framework

**Source:** Paul Rogers & Marcia Blenko, *Harvard Business Review*, January 2006 (Bain & Company)

Five roles clarify decision accountability:
- **R**ecommend: drives the decision process, gathers input, proposes
- **A**gree: must approve (veto power) before decision finalizes
- **P**erform: implements after decision is made
- **I**nput: provides expertise and data, no veto
- **D**ecide: single point of final authority, breaks ties

**How OMS maps to RAPID:**
- **Recommend** = team discussion agents (CTO, PM, QA, etc.) — they drive the analysis and propose
- **Input** = domain research agents — expertise provided, no position authority
- **Agree** = C-suite buffer round — they must not hard-block before synthesis proceeds
- **Decide** = CEO (mandatory categories) or C-suite consensus (bufferable categories resolved)
- **Perform** = oms-implement — executes after decision, does not re-open strategic questions

**Critical:** Once Decide fires, Perform does not re-litigate. "Disagree and commit" — agents who held dissenting positions implement fully within the decided constraint.

---

## Timing — Last Responsible Moment

**Source:** Mary & Tom Poppendieck, *Lean Software Development*, 2003

Delay commitment until the cost of making a wrong decision exceeds the cost of delay. Decision quality improves with facts. Over-early commitment forecloses options; over-late commitment makes options impossible.

**How OMS implements this:**
- CEO Gate research option (`research: [question]`) = explicit last responsible moment mechanism. CEO can pause and gather facts before committing to an irreversible direction.
- `reopen_conditions[]` in synthesis = the system signals in advance when a decision should be revisited (when new facts arrive that change the calculus)
- Agents with `confidence_pct < 60` on a consequential decision should recommend deferral or research rather than forcing a choice under uncertainty
- The Facilitator should name explicitly when agents are being asked to decide before enough information is available — this is a valid escalation reason

---

## Organizational Memory — Architecture Decision Records (ADRs)

**Source:** Michael Nygard, Cognitect Blog, November 2011

Record decisions like code. Fields: Title, Status (proposed → accepted → deprecated), Context, Decision, Consequences. Create organizational memory. Prevent re-deciding the same question.

**How OMS implements this:**
- CEO Decision Log in `ceo-mandate.ctx.md` = ADR system for strategic decisions
- CEO Gate Phase 1 checks Decision Log before classifying: if prior decision covers the territory, inject it as constraint and route to synthesize directly
- Status lifecycle: CEO decides (accepted) → written to log → auto-enforced forward → superseded only if CEO explicitly overrides
- Every CEO Gate decision includes a `Consequences` equivalent: "What this forecloses" in the brief

**The auto-pilot mechanism:** The Decision Log + Phase 1 check is what converts the CEO's decisions into standing constraints that gate all future synthesis. CEO decides once. Every future task that falls inside that decision flows to synthesis directly without re-asking.

---

## Problem Clarity — Toyota A3 Thinking

**Source:** John Shook, Lean Enterprise Institute; Taiichi Ohno (Toyota Production System origin)

One-page discipline: problem statement → current state analysis → root cause → target state → action plan → follow-up. Forces clarity by constraint. Originated from Ohno refusing to read past page one.

**How OMS implements this:**
- CEO Brief format mirrors A3: Context (current state) → What changes/what we lose (target state analysis) → Options (action paths) → What this forecloses (consequences) → CEO decision (action)
- Ratification Brief is intentionally short — if C-suite aligned, CEO gets the A3 version, not a full investigation
- Agent `reasoning[]` arrays implement A3 discipline: discrete claims, each earning its place, no padding

---

## Bias Countermeasures — LLM Research Summary

**Sources:**
- PNAS (2024): LLMs exhibit positivity bias, decision aversion, overconfidence in high-stakes decisions
- MIT Computational Linguistics (2024): 89.4% of bias mitigation papers show persistent bias in deployed systems
- HBR (2026): Trendslop — LLMs favor innovation/collaboration/differentiation regardless of context

**What agents must actively counter:**

| Bias | Manifestation | Countermeasure |
|---|---|---|
| Trendslop | Unanimous Round 1 convergence on fashionable strategy | Devil's Advocate protocol fires; Path Diversity must include unglamorous options |
| Positivity bias | All options sound like wins; no agent names a realistic failure mode | Synthesizer requires `strongest_argument` for dissent; pre-mortem failure modes in every Round 1 |
| Overconfidence | High `confidence_pct` without evidence | Confidence calibration rules: 95+ = near-certain; 50-65 = genuine uncertainty; must match `position` hedging |
| Decision aversion | Vague positions that don't recommend anything | Round 1 instruction: "Post your position — single actionable sentence. A hedged non-position fails." |
| Authority gradient | Agents defer to CTO or CPO without engaging their argument | Response anonymization in Round 1 distribution; agents evaluate arguments, not sources |

**The structural fix:** OMS's multi-agent blind NGT design is itself a bias countermeasure. Individual LLM calls produce trendslop. Structured disagreement between agents with distinct mandates, blind first rounds, and facilitated convergence produces context-specific recommendations — provided agents are not allowed to hedge.
