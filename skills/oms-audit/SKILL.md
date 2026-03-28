# OMS Audit — System Health Check

Audits the OMS system for correctness and consistency. Runs structured checks across 5 zones, fixes confirmed gaps, and updates `~/.claude/agents/oms-audit/audit-status.md`.

## Usage
```
/oms-audit              # full audit — all 5 zones
/oms-audit personas     # zone 3 only (discussion personas)
/oms-audit engine       # zone 2 only (engine agents)
/oms-audit skills       # zone 1 only (skills layer)
/oms-audit training     # zone 4 only (training system)
/oms-audit contract     # zone 5 only (field contract)
/oms-audit --quick      # critical invariants only (5 min, no subagents)
```

---

## When to Run
- After any persona or SKILL.md change
- After adding new validation criteria
- After a major OMS session produces unexpected behavior
- Monthly (full audit)

---

## Audit Zones

### Zone 1 — Skills Layer
Files: `skills/oms/SKILL.md`, `skills/oms/llms.txt`, `skills/oms-start/SKILL.md`, `bin/oms-work.py`, `skills/oms-work/SKILL.md`, `skills/oms-train/SKILL.md`, `skills/oms-capture/SKILL.md`

Key checks:
- Deprecated sections absent (Step 5.5, Autonomous Pipeline Protocol, OMS_BOT in main SKILL.md, .checkpoint-only)
- Step 3.5 section present with CEO Gate routes
- Step 0 queue state logic present
- oms-work.py: check_feature_completion() function present + feature field parsed

### Zone 2 — Engine Agents
Files: `router/persona.md`, `facilitator/persona.md`, `synthesizer/persona.md`, `ceo-gate/persona.md`, `context-optimizer/persona.md`, `trainer/persona.md`, `engine/discussion-rules.md`, `engine/escalation-format.md`, `oms-field-contract.md`

Key checks:
- Router Stage-Gate 1 checklist present with FC2 reference
- rounds_required present and marked blocking
- Facilitator: capitulation detection, DA protocol
- Synthesizer: reversibility gate, rationale traceability
- CEO Gate: all 3 phases, mandatory categories (1,2,4,9), auto-pilot, hard_block, reaction round suppression, Ratification Brief, research loop
- Trainer: EP1/EP2/EP3 exec checks, MF2 milestone check, FEATURE block validation
- Field contract: no stale checkpoint/watcher references

### Zone 3 — Discussion Personas
Files: all 10 persona files + `shared-context/discussion-schema.md`

Key checks (Non-Negotiables specifically):
- PM: scope concessions name deferred need; abstention fails AP1
- EM: no technology recommendations (D4)
- Backend: no API finalized until Frontend api_requirements read (HD2)
- QA: owns release risk (B1); declarative not conditional risk language (B2)
- CLO: critical severity = hard_block
- CPO: FEATURE draft format section present; OpenSpec fields forbidden (EP2)
- Field contract names match persona field names (PM: jtbd, EM: delivery_confidence)

### Zone 4 — Training System
Files: `training/validation-criteria.md`, `training/index.md`, `training/results.tsv`, sample scenario files

Key checks:
- Concerns 37–42 all present (EP, FD, RG, TS, MF, CG)
- Scenarios 057–065 in index + results.tsv + filesystem
- CEO Gate + Research scenarios correctly marked pending
- Criteria Gap Log section present

### Zone 5 — Field Contract
Files: `oms-field-contract.md`, `shared-context/discussion-schema.md`, `engine/discussion-rules.md`, `engine/escalation-format.md`

Key checks:
- All stage field tables complete (Stages 1–8.5)
- No stale references (oms-checkpoint, oms-dispatcher, watcher, pipeline_frozen)
- discussion-schema: position_delta variants, CTO extension, M1 rule
- FC1/FC2 enforcement criteria present

### Zone 6 — Token Efficiency & Context Optimizer
Files: `context-optimizer/persona.md`, `context-optimizer/metrics.md`, all `*/lessons.md`

Key checks:
- **EFF1** — No stale references in optimizer persona (oms-dispatcher.sh, oms-post-step.py, pipeline_frozen)
- **EFF2** — Line targets in optimizer match actual persona sizes (not aspirational targets that flag every agent)
- **EFF3** — Lessons not duplicating Non-Negotiables: any lesson with 4-word fingerprint match to a Non-Negotiable in the same persona = redundant load. List for removal.
- **EFF4** — metrics.md has entries for both active projects (sonai, daily-cosmos) with at least one completed task each
- **EFF5** — Audit Check numbering in optimizer is sequential (1, 2, 3, 4b, 5)
- **EFF6** — Mode 2 input list does not reference deprecated files
- **EFF7** — shared-lessons/ directory exists; if it does, check it has entries (not just headers)

---

## Execution

### Full audit
Launch 5 parallel Explore agents, one per zone. Each agent:
1. Reads all files in its zone
2. Runs numbered checks (cite exact file:line; never report gap unless confirmed absent)
3. Returns structured table: `| Check | File | Result | Evidence |`

Collect all results → fix confirmed gaps (edit persona files directly) → update `~/.claude/agents/oms-audit/audit-status.md`.

### Quick mode (`--quick`)
Run inline without subagents. Check only critical invariants:
1. Does field contract have Stage 1–8.5 tables? (scan for `## Stage` headings)
2. Does router/persona.md have Stage-Gate 1? (scan for `Stage-Gate 1`)
3. Does SKILL.md have Step 3.5? (scan for `## Step 3.5`)
4. Are deprecated sections absent? (scan for `Autonomous Pipeline`, `Step 5.5`, `oms-checkpoint.json`)
5. Do PM/QA/CLO Non-Negotiables have the critical rules? (scan for AP1, B1, hard_block)

Quick mode produces a 10-line pass/fail summary, not a full report.

---

## Output
After running:
1. Update `~/.claude/agents/oms-audit/audit-status.md` with new run date + results
2. Show CEO: pass count / total, any confirmed gaps, any fixes applied
3. If fixes applied: list what changed and which personas/files were modified

---

## Fix Protocol
Confirmed gaps (content verified absent) → fix inline during audit run.
Ambiguous findings (rule exists in wrong section, or semantically equivalent) → flag to CEO, do not auto-fix.
False positives (rule exists but in different section than checked) → mark PASS with note on where rule lives.

Never auto-delete content. Never change JSON output schemas during audit. Schema changes require CEO review.
