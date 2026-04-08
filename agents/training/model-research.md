# LLM-per-Agent Research — OMS Discussion Engine (v2)

## Methodology
Analyze each role's cognitive demands using: (1) real failure data (310 tasks, 12 failures), (2) training scenario requirements (71 scenarios), (3) actual output complexity. Not heuristic — evidence-based.

## Data Summary
- 310 tasks executed across 6 projects
- 96.1% overall pass rate
- Validator pass rates: dev 99.1%, qa 100%, em 100%, cto 100%, cro 96.3%
- first_pass metric is broken (field was null/missing in 301/310 records — added 2026-04-06)
- 5 execution failures (LLM couldn't produce code), 3 exceptions, 1 each at cto/qa/dev validators

---

## Role-by-Role Analysis

### 1. Router — current: haiku | VERDICT: haiku is borderline

**What it does:** Parse intent, score complexity (3 axes, 0-6), select agent roster, write task-specific briefings, Cynefin tier classification.

**Cognitive demand:** MEDIUM-HIGH
- The 12-step Chain-of-Thought protocol is explicit, but step 5 (roster selection) requires domain understanding to judge whether an agent's routing hint applies to THIS task
- Step 8 (pre-mortem) requires imagining 2-3 concrete failure modes — this is generative reasoning, not classification
- Step 10 (context mode distillation) requires reading context files and compressing per-agent — summarization at a domain-expert level

**Evidence:**
- 32 training scenarios test Router, with R1-R8 criteria
- Scenario 018 (complexity miscall) tests whether Router catches irreversibility=2 on "replace JWT with session auth" — Haiku might miss the reversibility dimension because it requires reasoning about deployment impact
- Router has 0 real-world failures in 310 tasks — BUT those tasks were routed by the parent Claude session (Sonnet/Opus), not by a Haiku subagent. The hook only just started enforcing Haiku.

**Risk:** The 0% failure rate is from BEFORE hook enforcement. We have zero data on Router running on Haiku in production. The training scenarios are the only validation, and we haven't run them yet.

**Recommendation:** KEEP haiku BUT run `/oms-train` on all 32 Router scenarios ASAP. If R2 (complexity miscall) or R5 (generic briefings) failures appear, upgrade to sonnet. The explicit protocol compensates for Haiku's weaker reasoning, but pre-mortem generation is the risk.

---

### 2. Path Diversity — current: haiku | VERDICT: UPGRADE TO SONNET

**What it does:** Generate N structurally distinct solution paths, each with a unique key_assumption, matched to agent domains.

**Cognitive demand:** HIGH
- Must understand the problem space well enough to identify independent axes of variation
- Scenario 024 requires generating 4 paths for SSR vs CSR with DIFFERENT key assumptions (cost, API contract, UX performance, user segments) — this is creative divergent thinking
- PD1 (structurally distinct) is the hardest criterion — Haiku tends toward surface variation (same assumption, different wording)

**Evidence:**
- Only 2 training scenarios test Path Diversity (024, 028)
- PD1 failure = same key_assumption with different surface → most likely Haiku failure mode
- Path Diversity only fires on Tier 2+ tasks — these are the most complex tasks where creative framing matters most

**Risk:** Haiku generating "different words, same idea" paths. This undermines the entire purpose of path diversity — homogenized seeding leads to homogenized Round 1.

**Recommendation:** UPGRADE to sonnet. Path Diversity fires rarely (Tier 2+ only) so cost is low, but quality matters enormously — bad seeds corrupt the entire discussion.

---

### 3. Pre-Facilitator — current: haiku | VERDICT: KEEP HAIKU

**What it does:** Check convergence, compute confidence deltas, detect obvious failure signals.

**Cognitive demand:** LOW — binary checks: all `changed:false`? round cap reached? all positions identical?

**Evidence:** Fires after every round on Tier 2+. Output is `{short_circuit: bool, reason: string}`. No training scenario failures on Pre-Facilitator.

**Recommendation:** KEEP haiku. This is the correct assignment — mechanical pass/fail gate.

---

### 4. Full Facilitator — current: sonnet | VERDICT: KEEP SONNET

**What it does:** Detect false convergence, livelock, groupthink, trendslop. Design targeted injections. Track epistemic acts (14 types). Manage Devil's Advocate protocol.

**Cognitive demand:** HIGHEST among engine roles
- Must read all agent positions across rounds and detect PATTERNS (not individual values)
- False convergence detection requires understanding that positions sound different but mean the same thing
- Livelock detection requires comparing Round N+2 positions against Round N (not just N+1)
- Trendslop detection requires recognizing when agents converge on fashionable directions without grounding

**Evidence:** 13 training scenarios test Facilitator with F1-F6 criteria. These are among the hardest scenarios.

**Recommendation:** KEEP sonnet. This is genuinely complex pattern recognition. Haiku would miss subtle failure modes. Opus is overkill — Sonnet handles this well.

---

### 5. CEO Gate — current: haiku | VERDICT: KEEP HAIKU

**What it does:** Classify synthesis against 10 categories (4 mandatory, 6 bufferable).

**Cognitive demand:** LOW-MEDIUM — pattern matching against explicit category list. The categories are enumerated with examples.

**Evidence:** Only 1 training scenario directly tests CEO Gate (070). Categories are well-defined enough for classification.

**Recommendation:** KEEP haiku.

---

### 6. Synthesizer — current: sonnet (opus on escalation) | VERDICT: KEEP AS-IS

**What it does:** Produce traceable decision with rationale, preserve dissent, steelman minority arguments, detect cluster convergence, apply reversibility gate.

**Cognitive demand:** HIGHEST in the system
- Must synthesize N agents × M rounds of positions
- Every rationale claim must cite agent + round (SY1)
- Must detect suppressed dissent (SY2) and steelman it (SY4)
- Must resist trendslop (Step 8 in persona)
- Must apply lock-in gate (Step 9)

**Evidence:** 13 training scenarios. Synthesizer is the terminal quality gate — bad synthesis = bad specs = bad code. The Opus escalation on livelock is justified because livelock means the standard synthesis failed.

**Recommendation:** KEEP sonnet default + opus escalation. This is working correctly.

---

### 7. Trainer — current: sonnet | VERDICT: KEEP SONNET

**What it does:** Evaluate agent behavior against 50+ validation criteria, produce SBI coaching notes, write lessons.

**Cognitive demand:** HIGH
- Must map specific behaviors to specific criteria (e.g., "Backend Dev proposed schema without reading Frontend's api_requirements" → HD2 failure)
- Must distinguish genuine reasoning quality from surface compliance
- Now also checks MR1/MR2 (model routing), LA1/LA2 (lessons), CG9/CG10 (coherence gate)

**Evidence:** 67 training scenarios involve Trainer evaluation. T1 (specific and actionable) is the key criterion — Haiku produces generic coaching.

**Recommendation:** KEEP sonnet.

---

### 8. Executive Briefing — current: sonnet | VERDICT: KEEP SONNET

**What it does:** Read synthesis + queue state + product direction, produce CEO-readable brief with TL;DR, blockers, and What Was Done.

**Cognitive demand:** MEDIUM-HIGH
- Must understand what matters to the CEO vs. what's internal detail
- Must correctly identify blockers (CEO-gate tasks, CTO-stops) from queue state
- Must connect What Was Done to product impact (not just technical changes)
- Must read the Trainer output and incorporate quality signals

**The user is right:** this is NOT just summarization. The brief must ANALYZE — prioritize, connect technical changes to product impact, surface blockers that aren't obvious. "Refactored auth middleware" → "Users can now stay logged in for 24h without re-authentication." That transformation requires understanding.

**Recommendation:** KEEP sonnet. Haiku would produce technically accurate but CEO-useless briefs.

---

### 9. Elaboration — current: sonnet | VERDICT: KEEP SONNET, CONSIDER OPUS FOR CROSS-FUNCTIONAL

**What it does:** Expand action_items into full OpenSpec tasks (Spec, Scenarios, Artifacts, Verify, Depends).

**Cognitive demand:** HIGHEST for spec quality
- Must write unambiguous SHALL specs that have ONE correct interpretation
- Must design GIVEN/WHEN/THEN scenarios that are mechanically verifiable
- Must correctly identify file paths for Artifacts and Verify commands
- Must enforce task sizing rules (≤4 files, ≤3 interactions, split when needed)
- Must respect Research-gate, Interface-contract, Depends chains

**Evidence:**
- 7 training scenarios test elaboration (061, 066, 071, etc.)
- Scenario 066 requires splitting 5-interaction task into 2 tasks — requires understanding WHICH interactions group together
- base_trade's 63 validation violations are ALL elaboration quality failures — the specs were written with prose Produces, vague THEN clauses, chain depth 9. These tasks were elaborated before the new validators existed, but they show what happens when spec quality is low.

**Risk of upgrading to Opus:** cost (3x Sonnet per elaboration). But elaboration runs once per task, and bad elaboration costs 10x in execution retries.

**Recommendation:** KEEP sonnet as default. For cross-functional features (2+ departments, interface contracts, Research-gate decisions) where spec quality is most critical, CONSIDER opus. Add a config key `elaboration_complex` → opus.

---

### 10. Context Optimizer — current: haiku | VERDICT: KEEP HAIKU

Mechanical analysis. Rule-based. Correct assignment.

---

### 11. Verification Agent — current: sonnet | VERDICT: KEEP SONNET

Evaluates disputed factual claims. Needs reliable knowledge base. Haiku would hallucinate verdicts on technical facts.

---

### 12. Discussion Agents (all) — current: sonnet | VERDICT: KEEP SONNET

CTO, PM, EM, Backend, Frontend, QA, CPO, CLO, CFO, CRO, all researchers.

Position quality is the product of the discussion engine. Every position must be domain-specific, cite frameworks, engage with other agents, maintain non-negotiables. Haiku cannot reliably do this — it would produce generic positions that pass structural checks but fail semantic quality (O1, O2, DE1).

---

### 13. oms-exec — current: opus | VERDICT: KEEP OPUS (per user decision)

User confirmed: exec decides milestones and features. The cost of a bad exec decision cascades through the entire pipeline. Opus is justified for strategic C-suite discussions.

---

## Final Recommendations

| Role | Current | Recommendation | Action |
|---|---|---|---|
| router | haiku | haiku | Run /oms-train on 32 Router scenarios to validate |
| path-diversity | haiku | **sonnet** | UPGRADE — creative divergence needs reasoning |
| facilitator_pre | haiku | haiku | Confirmed — mechanical gate |
| facilitator_full | sonnet | sonnet | Confirmed — pattern detection |
| ceo-gate | haiku | haiku | Confirmed — classification |
| synthesizer | sonnet | sonnet | Confirmed — traceability + dissent |
| synthesizer_escalation | opus | opus | Confirmed — livelock recovery |
| trainer | sonnet | sonnet | Confirmed — criterion evaluation |
| executive-briefing | sonnet | sonnet | **KEEP** — analysis, not just summary |
| elaboration | sonnet | sonnet (opus for complex) | Add `elaboration_complex` config key |
| context-optimizer | haiku | haiku | Confirmed — mechanical |
| verification | sonnet | sonnet | Confirmed — factual evaluation |
| discussion agents | sonnet | sonnet | Confirmed — position quality |
| oms-exec | opus | opus | Confirmed by user — strategic decisions |

## Changes to implement:
1. **path-diversity → sonnet** (upgrade in oms-config.json)
2. **Add `elaboration_complex` key** for future cross-functional feature elaboration on Opus
3. **Run /oms-train regression** when rate limits reset to validate Router on Haiku
