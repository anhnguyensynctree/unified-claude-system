# Training Scenario Index

## Coverage Matrix

Each scenario tests a primary agent (or engine component) against specific validation criteria. Scenarios are ordered by difficulty within each package: basic → medium → advanced.

---

## Router Package
*Goal: accurate tier classification, proportionate roster selection, specific briefings*

| # | Scenario | Difficulty | Criteria | What it tests |
|---|---|---|---|---|
| 001 | simple-routing | Basic | R1, R2, R3, R6, R7, D1, O1 | Tier 1 classification, single-domain restraint (E1 not testable — agreement path skips Round 2) |
| 018 | router-complexity-miscall | Medium | R2, R6 | Tier under-call: auth change classified as simple |
| 019 | router-roster-over-activation | Medium | R1, R7 | Roster bloat: pagination task, no CTO/PM needed |
| 028 | tier-zero-trivial | Basic | R2, R6, R7, D1, O1 | Tier 0 fast path: button text change, 1 agent max |
| 029 | tier1-under-escalation | Basic | R2, R6, R7 | Tier 0 mis-call: email validation misses QA domain |
| 030 | tier2-golden-path | Medium | R2, R4, R6, R7 | Tier 2 positive: Stripe integration, 2–3 agents |
| 031 | tier2-under-escalation | Medium | R2, R6 | Tier 1 mis-call: forgot password misses security |
| 032 | tier2-over-escalation | Medium | R2, R6 | Tier 3 mis-call: column sort, index ≠ irreversible |
| 033 | tier3-golden-path | Advanced | R2, R4, R6, R7 | Tier 3 positive: REST→GraphQL, 3+ domains |
| 034 | disorder-decomposition | Advanced | R2, R6 | Bundled intent: must decompose, output highest tier |
| 035 | mid-discussion-tier-escalation | Advanced | R2, R4, R6 | Tier escalation mid-run: Tier 1 → Tier 2 |

---

## Facilitator Package
*Goal: process integrity — DA protocol, false convergence detection, livelock resolution, capitulation detection*

| # | Scenario | Difficulty | Criteria | What it tests |
|---|---|---|---|---|
| 020 | facilitator-false-convergence | Medium | F1, F3, C1 | Unanimous Round 1 without substantive reasoning |
| 021 | facilitator-livelock | Advanced | F4, L1, L2 | Same pair oscillates two rounds without convergence |
| 036 | facilitator-da-protocol | Medium | F2, F1 | DA protocol fires on genuine unanimity |
| 037 | facilitator-capitulation-detection | Advanced | F6, CD2, M1 | `changed: true` + confidence_delta ≤ 0 → inject challenge |

---

## Synthesizer Package
*Goal: traceable rationale, steelmanned dissent, reversibility gate, correct reopening conditions*

| # | Scenario | Difficulty | Criteria | What it tests |
|---|---|---|---|---|
| 022 | synthesizer-traceability-failure | Medium | SY1, H1, H2 | Rationale without agent+round citation |
| 023 | synthesizer-dissent-omission | Medium | SY2, SY4, C3 | Minority position suppressed, not steelmanned |
| 026 | reversibility-gate | Advanced | RV1, RV2, RV3 | Irreversible + medium confidence → escalate |
| 027 | reopen-conditions | Medium | RV3, SY1, C4 | Derive reopen conditions from agent-stated concerns |

---

## Path Diversity Agent Package
*Goal: structurally distinct paths, correct assignment, skip for single-agent tasks*

| # | Scenario | Difficulty | Criteria | What it tests |
|---|---|---|---|---|
| 024 | path-diversity-seeding | Medium | PD1, PD2, PD3, PD4 | Multi-path seeding, single-agent skip |

---

## Verification Agent Package
*Goal: factual claims only, honest uncertainty, no opinion evaluation*

| # | Scenario | Difficulty | Criteria | What it tests |
|---|---|---|---|---|
| 025 | verification-agent-dispute | Medium | VE1, VE2, VE3 | Verdict with source; confident on checkable claims |
| 038 | verification-epistemic-honesty | Medium | VE2, VE3 | `uncertain` when <70% confidence — no false verdict |

---

## Trainer Package
*Goal: specific behavioral citations, no domain correctness judgments, criteria gap logging*

| # | Scenario | Difficulty | Criteria | What it tests |
|---|---|---|---|---|
| 039 | trainer-evaluation-specificity | Medium | T1, T4 | Cite round/agent/field — no generic feedback |
| 040 | trainer-domain-neutrality | Medium | T2, T3 | Flag behavior, not technical correctness |

---

## CTO Package
*Goal: architecture risk ownership, problem frame challenge, non-negotiable invocation*

| # | Scenario | Difficulty | Criteria | What it tests |
|---|---|---|---|---|
| 002 | cross-domain-tension | Medium | D1, D2, D3, E1 | Architecture vs. delivery tension, deferral |
| 004 | escalation-trigger | Advanced | X1, X2, X3 | CTO escalation path for strategic decisions |
| 014 | framing-lock-in | Advanced | PF1, PF2, A1 | Reframe problem when Router framing constrains solution |
| 046 | cto-problem-frame-challenge | Advanced | PF2, D3, A2 | Challenge Router frame when domain knowledge conflicts |

---

## Product Manager Package
*Goal: position authenticity, no implementation drift, user value framing*

| # | Scenario | Difficulty | Criteria | What it tests |
|---|---|---|---|---|
| 003 | scope-conflict | Medium | D1, D4, E3 | PM holds scope position under technical pressure |
| 010 | abilene-paradox | Advanced | AP1, AP2, M2 | PM states genuine position despite group pressure |
| 045 | pm-position-authenticity | Medium | AP1, AP2, D1 | PM abstention = AP1 fail; survey data = position |

---

## Engineering Manager Package
*Goal: delivery scope only, no technology recommendations, capacity framing*

| # | Scenario | Difficulty | Criteria | What it tests |
|---|---|---|---|---|
| 043 | em-domain-discipline | Medium | D4, D1, D2 | EM must not recommend Redis; defer to CTO/Backend |

---

## Frontend Developer Package
*Goal: UI/UX implementation positions, API requirements from design, no backend scope*

| # | Scenario | Difficulty | Criteria | What it tests |
|---|---|---|---|---|
| 001 | simple-routing | Basic | D1, O1 | Scoped to frontend, actionable position |
| 016 | implementation-handoff-failure | Advanced | HD1, HD2, SI1 | Cross-agent interface spec — frontend drives API shape |
| 044 | frontend-reverse-conway | Advanced | HD1, SI1, D1 | `api_requirements` field drives backend contract |

---

## Backend Developer Package
*Goal: API design, data model, no frontend scope, cross-domain dependency detection*

| # | Scenario | Difficulty | Criteria | What it tests |
|---|---|---|---|---|
| 012 | hidden-dependency | Advanced | HD1, HD2, IA1 | Interface incompatibility detection before Round 2 |
| 016 | implementation-handoff-failure | Advanced | HD2, SI1, SI2 | Backend must not proceed without interface spec |

---

## QA Engineer Package
*Goal: risk surfaced in position (not reasoning), release blocking, MEMORY surfacing*

| # | Scenario | Difficulty | Criteria | What it tests |
|---|---|---|---|---|
| 009 | bystander-effect | Advanced | B1, B2, D3 | QA owns risk — cannot defer to other agents |
| 041 | qa-release-blocker | Medium | B1, B2, D3 | Risk must appear in `position`, not only `reasoning[]` |
| 042 | qa-domain-expertise | Advanced | PS1, PS2, B1 | Surface known constraint from MEMORY proactively |

---

## Cross-Agent / Discussion Integrity Package
*Goal: engagement, independence, convergence quality, cascade resistance*

| # | Scenario | Difficulty | Criteria | What it tests |
|---|---|---|---|---|
| 005 | majority-cascade | Advanced | M1, M2, E4 | Position holds under numerical pressure |
| 006 | hallucinated-consensus | Advanced | H1, H2, C1 | Synthesis attributes consensus not in transcript |
| 007 | livelock | Advanced | L1, L2, F4 | Loop detection and resolution mechanism |
| 008 | authority-gradient | Advanced | A1, A2, E4 | CEO preference as input, not constraint |
| 011 | information-cascade | Advanced | IC1, IC2 | Order-independent reasoning |
| 013 | confidence-miscalibration | Medium | CC1, CC2, CD1 | Low-confidence agent = uncertainty in position |
| 015 | synthesis-paralysis | Advanced | C1, C2, C3 | Synthesis decides — does not restate discussion |
| 017 | expertise-underutilization | Medium | IA2, PS1 | Early-round information weighted in late rounds |
| 047 | tier1-escalation-e1 | Medium | E1, R2, R6, D1, O1 | Tier 1 disagreement → escalation → Round 2 fires → E1 tested |

---

---

## Research Package
*Goal: research mode routing, CRO framing quality, domain expert evidence standards, anti-convergence discipline, cross-disciplinary tension detection, research synthesis integrity*

**Seeding strategy:** Research scenarios are NOT written synthetically. They are captured from real research sessions via `/oms-capture` after the discussion completes. Synthetic scenarios are unreliable because evaluating domain expert evidence quality requires genuine domain knowledge — a synthetic scenario cannot know whether a cited framework is correctly applied.

**First scenarios:** Seed from the first real Sonai question bank research session. Run `/oms` on "design the TELOS question bank", then `/oms-capture` on any behavioral failures observed.

**Expected behavior format for research scenarios:** Unlike engineering scenarios (which test for a specific correct answer), research scenarios test only behavioral compliance:
- Did CRO refine the question in Round 1? (RF1)
- Did domain experts cite specific frameworks? (DE1)
- Did the Facilitator protect discussion space rather than push convergence? (RC1)
- Did the Synthesizer produce a framework map with unresolved questions? (RS1, RS2)

| # | Scenario | Difficulty | Criteria | What it tests | Source |
|---|---|---|---|---|---|
| R01 | *(pending — capture from first real research session)* | — | RM1–RM4, RF1–RF4, DE1–DE3 | Research routing + CRO framing + evidence standards | First real /oms research session |
| R02 | *(pending)* | — | RC1–RC4, RS1–RS4 | Anti-convergence + research synthesizer output | — |
| R03 | *(pending)* | — | CT1–CT3, D3 | Cross-disciplinary tension detection + domain expert non-negotiables | — |

---

## Difficulty Distribution
| Difficulty | Count |
|---|---|
| Basic | 4 |
| Medium | 23 |
| Advanced | 20 |

## Criteria Coverage
Engineering criteria from `validation-criteria.md` (Concerns 1–26) are covered by at least one scenario. Concerns with multi-scenario coverage: R2/R6 (10 scenarios), D1 (8), B1/B2 (4), AP1/AP2 (3), HD1/HD2 (3), E1 (5 scenarios covering 4 variants: parallel monologue, implicit disagreement, missing claim, Tier 1 escalation path).

Research criteria (Concerns 27–32) are pending — scenarios R01–R03 will cover them once seeded from real research sessions. RM1–RM4, RF1–RF4, DE1–DE3, RC1–RC4, CT1–CT3, RS1–RS4 are currently untested.

## E1 Variant Coverage
| Variant | Scenario |
|---|---|
| Fail: parallel monologue (agents don't reference each other at all) | 002 |
| Fail: implicit disagreement (substance engaged, agent not named) | 012 |
| Fail: missing specific claim attribution | 005 |
| Fail: named but claim not cited (trainer test) | 039 |
| Pass + Fail: Tier 1 disagreement escalation path | 047 |
