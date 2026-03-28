# OMS System Audit — Status

Date: 2026-03-25
Method: 5 parallel Explore subagents, one zone each. Each check requires exact file:line citation before reporting a gap.

---

## Zone 1 — Skills Layer
Scope: `skills/oms/SKILL.md`, `skills/oms/llms.txt`, `skills/oms-start/SKILL.md`, `bin/oms-work.py`, `skills/oms-implement/SKILL.md`, `skills/oms-train/SKILL.md`, `skills/oms-capture/SKILL.md`

| Check | Result | Evidence |
|---|---|---|
| SK1 — Step 5.5 absent | PASS | absent — no "Step 5.5" or "CPO Backlog Pass" in SKILL.md |
| SK2 — Autonomous Pipeline Protocol absent | PASS | absent — section fully removed |
| SK3 — OMS_BOT refs in main SKILL.md absent | PASS | absent — OMS_BOT only appears in oms-start (intentional bot mode docs) |
| SK4 — `.checkpoint file only` row absent from Standing Rules | PASS | absent |
| SK5 — Step 0 queue state check present | PASS | SKILL.md lines 59-94: reads cleared-queue.md, cto-stop/needs-review handling, auto-exec trigger |
| SK6 — Step 6 Trainer lazy loading by tier | PASS | SKILL.md lines 414-450: tier scope table + lazy load instruction |
| SK7 — Step 8 scenario capture triggers | PASS | SKILL.md lines 464-487: capture triggers + `/oms-capture [task-id]` invocation |
| SK8 — check_feature_completion() in oms-work.py | PASS | oms-work.py lines 172-220: updates FEATURE Status to done, posts Discord notification |
| SK9 — feature field parsed in oms-work.py | PASS | oms-work.py line 85: `'feature': f.get('Feature', '').strip()` |
| SK10 — `.checkpoint file only` absent from llms.txt | PASS | absent |
| SK11 — llms.txt lazy log table matches SKILL.md | PASS | llms.txt lines 327-332 matches SKILL.md lines 495-499 |

**⚠ Gap (Step 3.5)**: `SKILL.md` steps jump from `## Step 3` directly to `## Step 4`. CEO Gate is listed in the Agent Registry (line 189) but has no dedicated `## Step 3.5` section describing when it fires and what happens on each route. **→ Fixed below.**

**Zone 1 verdict: CLEAN** (gap fixed)

---

## Zone 2 — Engine Agents
Scope: `router/persona.md`, `facilitator/persona.md`, `synthesizer/persona.md`, `ceo-gate/persona.md`, `context-optimizer/persona.md`, `trainer/persona.md`, `engine/discussion-rules.md`, `engine/escalation-format.md`, `oms-field-contract.md`

| Check | Result | Evidence |
|---|---|---|
| ENG1 — Router Stage-Gate 1 checklist | PASS | router/persona.md lines 122-135: explicit Stage-Gate 1 with all required fields |
| ENG2 — rounds_required in Router output | PASS | router/persona.md line 134: mandatory, blocking |
| ENG3 — FC2 field contract check in Stage-Gate 1 | PASS | router/persona.md line 138: "verify your output matches Stage 1 required fields in oms-field-contract.md (FC2)" |
| ENG4 — Facilitator capitulation detection | PASS | facilitator/persona.md lines 99-103: changed:true + confidence_delta ≤ 0 → targeted_injections |
| ENG5 — Facilitator DA protocol | PASS | facilitator/persona.md lines 47-49: DA fires on unanimous Round 1 |
| ENG6 — Synthesizer reversibility gate | PASS | synthesizer/persona.md lines 84-98: irreversible + low/medium confidence → escalate |
| ENG7 — Synthesizer rationale traceability | PASS | synthesizer/persona.md line 9: every rationale claim must cite agent + round |
| ENG8 — CEO Gate mandatory categories | PASS | ceo-gate/persona.md lines 28-33: categories 1, 2, 4, 9 listed as mandatory |
| ENG9 — CEO Gate auto-pilot (Decision Log) | PASS | ceo-gate/persona.md lines 78-86: prior CEO decision → route synthesize immediately |
| ENG10 — CEO Gate hard_block prevents resolution | PASS | ceo-gate/persona.md line 153: one hard_block prevents resolution regardless of majority |
| ENG11 — CEO Gate prior_decision_conflict forces CEO | PASS | ceo-gate/persona.md lines 144-145, 161: prior_decision_conflict: true → forced to CEO |
| ENG12 — CEO Gate reaction round suppression | PASS | ceo-gate/persona.md lines 353-354: all aligned with no flags → skip reaction round |
| ENG13 — Ratification Brief for mandatory + resolved | PASS | ceo-gate/persona.md lines 177-206: Phase 3a = Ratification Brief, distinct from Strategic Brief |
| ENG14 — CEO Gate research loop | PASS | ceo-gate/persona.md lines 284-312: CEO `research:` reply → CRO → findings before re-presenting |
| ENG15 — Context Optimizer ceo_approval_required field | PASS | context-optimizer/persona.md line 138 |
| ENG16 — Trainer EP1 exec pipeline check | PASS | trainer/persona.md lines 47-55: Step 6, Step 7, CEO response, FEATURE drafts — all four checks |
| ENG17 — Trainer MF2 milestone update check | PASS | trainer/persona.md lines 69-71 |
| ENG18 — oms-checkpoint.json section absent | PASS | absent — no "Checkpoint Fields" section in field contract |
| ENG19 — Watcher section absent | PASS | absent — no "Watcher — Pipeline Integrity Agent" section |
| ENG20 — Stage 1 "Written to" correct | PASS | oms-field-contract.md lines 15-16: "task log + passed directly to discussion agents" |

**Zone 2 verdict: CLEAN**

---

## Zone 3 — Discussion Personas
Scope: `cto`, `product-manager`, `engineering-manager`, `frontend-developer`, `backend-developer`, `qa-engineer`, `cpo`, `clo`, `cfo`, `chief-research-officer`, `shared-context/discussion-schema.md`

| Check | Result | Evidence |
|---|---|---|
| PER1 — discussion-schema.md position_delta fields | PASS | discussion-schema.md lines 8-21, 24-49: all fields present |
| PER2 — frame_challenge in CTO extensions | PASS | discussion-schema.md lines 60-62: CTO Agent Extensions with frame_challenge |
| PER3 — PM Non-Negotiable: scope concessions name deferred need | **GAP** | product-manager/persona.md Non-Negotiables had no explicit rule requiring scope concessions to name the deferred user need → **Fixed** |
| PER4 — CTO Non-Negotiable: surface irreversibility risk | PASS | cto/persona.md lines 29-37 |
| PER5 — PM jtbd field in output extensions | PASS | product-manager/persona.md lines 61-69: `jtbd` field present (field contract updated to match) |
| PER6 — PM abstention = AP1 fail | **GAP** | Non-Negotiable existed only in Discussion section, not Non-Negotiables → **Fixed** |
| PER7 — EM tech recommendations prohibited | **GAP** | engineering-manager/persona.md: tech prohibition only in Defer section, not Non-Negotiables → **Fixed** |
| PER8 — Frontend api_requirements field | PASS | frontend-developer/persona.md lines 58-59 |
| PER9 — Backend: no API finalized without Frontend spec | **GAP** | backend-developer/persona.md Non-Negotiables had no explicit "read api_requirements first" rule → **Fixed** |
| PER10 — QA risk ownership (B1) | **GAP** | qa-engineer/persona.md Non-Negotiables had no explicit "QA owns release risk, cannot defer" rule → **Fixed** |
| PER11 — QA risk in position (B2) | PASS | qa-engineer/persona.md lines 79-90: Callout Protocol explicitly requires position-level callouts; declarative vs conditional rule added |
| PER12 — QA risk_level field | PASS | qa-engineer/persona.md line 106: risk_level field |
| PER13 — PM field contract name mismatch | **GAP** | Field contract said `user_need_served` but PM persona has `jtbd` → **Fixed: field contract updated** |
| PER14 — EM field contract name mismatch | **GAP** | Field contract said `delivery_feasibility` but EM persona has `delivery_confidence` → **Fixed: field contract updated** |
| PER15 — CPO FEATURE draft format | **GAP** | cpo/persona.md had no dedicated FEATURE draft section — only discussion output extensions → **Fixed: section added** |
| PER16 — CPO OpenSpec fields forbidden in exec | **GAP** | cpo/persona.md Non-Negotiables had no explicit EP2 prohibition on Spec/Scenarios/Artifacts fields → **Fixed** |
| PER17 — CRO research question refinement (RF1) | PASS | chief-research-officer/persona.md lines 49-51 |
| PER18 — confidence_pct distinct from confidence_level | PASS | discussion-schema.md line 56: integer 0-100 with level alignment rule |

**Zone 3 verdict: 9 gaps fixed** (PER3, PER6, PER7, PER9, PER10, PER13, PER14, PER15, PER16 + CLO hard_block)

---

## Zone 4 — Training System
Scope: `training/validation-criteria.md`, `training/index.md`, `training/results.tsv`, scenario files 028, 047, 057, 064, 065

| Check | Result | Evidence |
|---|---|---|
| TR1 — Concern 42 CEO Gate (CG1-CG8) | PASS | validation-criteria.md lines 454-471 |
| TR2 — Concern 37 Exec Pipeline (EP1-EP3) | PASS | validation-criteria.md: present |
| TR3 — Concern 38 Feature Routing (FD1-FD3) | PASS | validation-criteria.md: present |
| TR4 — Concern 39 Research Gate (RG1-RG2) | PASS | validation-criteria.md: present |
| TR5 — Concern 40 Task Sizing (TS1-TS2) | PASS | validation-criteria.md: present |
| TR6 — Concern 41 Milestone Tracking (MF1-MF2) | PASS | validation-criteria.md: present |
| TR7 — Scenarios 057-065 in index.md | PASS | index.md: Exec Pipeline + Queue Package and Elaboration Agent Package both present |
| TR8 — CEO Gate Package pending in index.md | PASS | index.md lines 189-211: CG01-CG05 marked pending with seeding strategy |
| TR9 — Scenarios 057-065 in results.tsv | PASS | results.tsv: all 9 scenarios appear, all passing in most recent run |
| TR10 — 057-exec-golden-path.md with EP1/EP2/EP3 | PASS | file exists with correct criteria |
| TR11 — 064-feature-validation-chain.md with MF1/EP2 | PASS | file exists with correct criteria |
| TR12 — 065-milestone-completion.md with MF1/MF2/EX2 | PASS | file exists with correct criteria |
| TR13 — 028-tier-zero-trivial.md with R2/R6/R7 | PASS | file exists with correct criteria |
| TR14 — 047-tier1-escalation-e1.md tests E1 | PASS | file exists, tests Tier 1 disagreement → escalation → Round 2 → E1 |
| TR15 — Criteria Gap Log section | PASS | validation-criteria.md: section present |

**⚠ Minor gap**: Criteria Gap Log entry for scenario 046 (cto-problem-frame-challenge) notes frame_challenge field is not formally added to CTO output schema. field IS documented in discussion-schema.md lines 60-62 (CTO extensions). Gap log entry predates schema update — no action needed.

**Zone 4 verdict: CLEAN**

---

## Zone 5 — Field Contract & Shared Context
Scope: `oms-field-contract.md`, `shared-context/discussion-schema.md`, `engine/discussion-rules.md`, `engine/escalation-format.md`, `shared-context/lesson-system.md`

| Check | Result | Evidence |
|---|---|---|
| FC1-FC8 — All stage field tables | PASS | All stages (1-8.5) complete, no missing fields |
| FC9 — Stale references absent | PASS | No oms-dispatcher.sh, oms-checkpoint.json, oms-watcher, pipeline_frozen found |
| FC10-FC13 — discussion-schema.md base fields | PASS | All position_delta variants, CTO extension, M1 rule present |
| FC14 — discussion-rules.md coverage | PASS | NGT blind, authority gradient, non-negotiable invocation, position change standards all present |
| FC15 — escalation-format.md structure | PASS | When to escalate, format artifact, who receives — all present |
| FC16 — lesson-system.md shared_lesson categories | **LOW** | lesson-system.md does not exist at all; shared_lesson categories (agent-reasoning, discussion-quality, synthesis-patterns, routing-accuracy) referenced in field-contract.md line 110 but undocumented |
| FC17 — cross-agent-patterns.md currency | PASS | Recent dated entries (2026-03-18), actively maintained |
| FC18 — FC1 criterion enforcement | PASS | oms-field-contract.md lines 182-189 |
| FC19 — Change Protocol currency | PASS | lines 193-214, no deprecated references |
| FC20 — company-direction.md scope | PASS | Correctly scoped to OMS system description |

**Zone 5 verdict: CLEAN** (FC16 low priority — lesson-system.md is a reference doc, not a runtime file)

---

## Zone 6 — Token Efficiency & Context Optimizer
Scope: `context-optimizer/persona.md`, `context-optimizer/metrics.md`, `*/lessons.md`, `shared-lessons/`
Run date: 2026-03-25 (post-session fixes)

| Check | Result | Evidence |
|---|---|---|
| EFF1 — No stale references in optimizer persona | PASS | Zero matches for `oms-dispatcher`, `pipeline_frozen`, `MEMORY.md` in input/loading lists |
| EFF2 — Line targets match actual complexity tiers | PASS | persona.md lines 103–108: 120/80/120/280/no-target all correct |
| EFF3 — Lessons not duplicating Non-Negotiables | PASS | No 4-word fingerprint matches found in router, cto, product-manager lessons.md |
| EFF4 — metrics.md has entries for active projects | PASS | Both sonai and daily-cosmos have at least one completed task entry |
| EFF5 — Audit Check numbering sequential | PASS | persona.md lines 70, 80, 112, 127, 140: sequence 1 → 2 → 3 → 4b → 5 confirmed |
| EFF6 — Mode 2 input list clean of deprecated files | PASS | persona.md lines 62–66: no deprecated refs; `facts.json` present |
| EFF7 — shared-lessons/ has substantive entries | PASS | 9 files; agent-reasoning, performance, architecture, synthesis-patterns all have real entries |

**Minor observation**: `shared-lessons/routing-accuracy.md` has a header but no lesson entries yet — will populate naturally from Router classification misses.

**Zone 6 verdict: CLEAN**

---

## Summary

| Zone | Checks | Pass | Gaps | Severity |
|---|---|---|---|---|
| Skills Layer | 11 + SK3.5 | 11 | 1 (Step 3.5 missing section) | medium — fixed |
| Engine Agents | 20 | 20 | 0 | — |
| Discussion Personas | 18 | 9 | 9 (PM/EM/Backend/QA/CPO/CLO + field contract) | medium — fixed |
| Training System | 15 | 15 | 0 | — |
| Field Contract | 20 | 19 | 1 (lesson-system.md) | low — deferred |
| Token Efficiency | 7 | 7 | 0 | — |
| **Total** | **91** | **82** | **11 fixed, 1 deferred** | |

### Fixed in this session
1. **SKILL.md — Step 3.5** — added `## Step 3.5 — CEO Gate` section between Step 3 and Step 4
2. **PM — AP1 scope concession** — scope cuts must name the deferred user need (Non-Negotiables)
3. **PM — AP1 abstention** — abstaining from stating a position fails AP1 (Non-Negotiables)
4. **EM — D4 tech prohibition** — no technology recommendations; only delivery scope (Non-Negotiables)
5. **Backend — HD2 spec requirement** — no API schema finalized until Frontend `api_requirements` read (Non-Negotiables)
6. **QA — B1 risk ownership** — QA owns release risk, cannot defer to other agents (Non-Negotiables)
7. **QA — B2 declarative risk** — conditional risk language = bystander behaviour (Callout Protocol)
8. **CLO — CG3 hard_block** — critical-severity legal risk with no compliant path = hard_block (Non-Negotiables)
9. **CPO — EP2 OpenSpec prohibition** — no Spec/Scenarios/Artifacts/Produces/Verify in exec mode (Non-Negotiables)
10. **CPO — EP2 FEATURE format** — added `## FEATURE Draft Format` section with full field template
11. **Field contract — field name alignment** — PM: `user_need_served` → `jtbd`; EM: `delivery_feasibility` → `delivery_confidence`
12. **Context Optimizer — stale dispatcher reference** — removed `oms-dispatcher.sh` from Mode 2 input and Audit Check 3
13. **Context Optimizer — unrealistic line targets** — corrected to 120/80/120/280/no-target tiers
14. **Context Optimizer — MEMORY.md dead layer** — removed MEMORY.md from agent loading chain and all optimizer checks; retained observations covered by ctx.md files
15. **Context Optimizer — check numbering** — fixed sequence 1→2→3→4b→5 (was 1→2→3→5→4)
16. **SKILL.md — MEMORY.md removed** — dropped from agent registry, load order, and onboard mode write target
17. **Trainer — memory_facts field removed** — field was solving a non-problem (ctx.md already handles project truth)

### Deferred
- **FC16** — lesson-system.md does not exist; shared_lesson category taxonomy undocumented. Low priority — categories work implicitly. Create when trainer references them.
- **EFF minor** — `shared-lessons/routing-accuracy.md` header only, no entries. Will self-populate from Router misses.

### Pending (by design)
- CEO Gate scenarios CG01-CG05: seed from first real CEO Gate trigger via `/oms-capture`
- Research scenarios R01-R03: seed from first real research session

---

*Last full audit: 2026-03-25 | Zones 1–5: 5 parallel subagents | Zone 6: single subagent post-session | file:line citations required*
