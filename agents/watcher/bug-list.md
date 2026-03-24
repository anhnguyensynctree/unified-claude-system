# Watcher Bug List

Living document. Add entries only when a fix is fully deterministic — if the fix requires judgment it belongs in CEO escalation, not here.

**Entry format**:
```
## BUG-NNN — [name]
Signature: [what pattern triggers this]
Frozen step: [which step was frozen]
Missing/invalid: [what field or value caused it]
Fix: [exact checkpoint change to apply]
Rerun step: [what next is reset to]
Responsible agent: [whose Stage-Gate should have caught this]
Lesson: [one imperative sentence written to responsible agent's lessons.md]
```

---

## BUG-001 — Router missing rounds_required
Signature: pre-step validation fails on `round_*` with `rounds_required` in missing list
Frozen step: `round_1` (or any `round_N`)
Missing/invalid: `rounds_required` null or absent in checkpoint
Fix: reset checkpoint `next` to `router`, clear `frozen_step`
Rerun step: `router`
Responsible agent: `router`
Lesson: rounds_required must be non-null before setting stage_gate: passed — R8 blocking failure; derived from tier (Tier 0→1, Tier 1→2, Tier 2→2, Tier 3→3)

## BUG-002 — Router missing activated_agents
Signature: pre-step validation fails on `round_*` with `activated_agents` in missing list
Frozen step: `round_1` (or any `round_N`)
Missing/invalid: `activated_agents` null or empty in checkpoint
Fix: reset checkpoint `next` to `router`, clear `frozen_step`
Rerun step: `router`
Responsible agent: `router`
Lesson: activated_agents must be written to checkpoint before advancing to round_1 — Stage-Gate 1 must verify this field is non-null before passing

## BUG-003 — Router did not run (both fields missing)
Signature: pre-step validation fails on `round_1` with both `rounds_required` and `activated_agents` missing
Frozen step: `round_1`
Missing/invalid: both `rounds_required` and `activated_agents` absent — router step was skipped or failed silently
Fix: reset checkpoint `next` to `router`, clear `frozen_step`
Rerun step: `router`
Responsible agent: `router`
Lesson: Router must complete fully and write all required fields before pipeline advances — silent Router failure leaves checkpoint empty

## BUG-004 — Invalid next value in checkpoint
Signature: post-write next validation catches a value not in the allowlist
Frozen step: value of `frozen_step` (the bad next value that was written)
Missing/invalid: `next` not in `{router, round_N, ceo_gate, synthesis, implement, log, cpo_backlog, trainer, compact_check, mark_done, transition, waiting_ceo, pipeline_frozen, complete, done}`
Fix: reset `next` to `frozen_step` value if it is a valid step; otherwise reset to `router`
Rerun step: the step that produced the bad next (re-runs it with force-advance catching the output)
Responsible agent: whichever step last ran (recorded in dispatcher logs)
Lesson: written only if the bad value is traceable to a specific agent output

## BUG-005 — task_id missing in checkpoint
Signature: pre-step validation fails with `task_id` in missing list on any content step
Frozen step: any of `round_*, synthesis, implement, cpo_backlog, trainer, compact_check, mark_done`
Missing/invalid: `task_id` absent from checkpoint
Fix: **no auto-fix** — task_id cannot be safely inferred; escalate to CEO immediately
Rerun step: N/A
Responsible agent: dispatcher (`_auto` fallback failed to extract task_id)
Lesson: N/A — escalation only

## BUG-006 — Synthesizer missing action_items
Signature: implement step runs but task log synthesis section contains `action_items: []`
Frozen step: `implement`
Missing/invalid: `action_items` empty array in synthesis log
Fix: reset checkpoint `next` to `synthesis`, clear `frozen_step` — Synthesizer reruns with instruction to derive action_items from the decision
Rerun step: `synthesis`
Responsible agent: `synthesizer`
Lesson: action_items[] must be non-empty — derive from decision even if agents did not enumerate explicitly; Stage-Gate 4 must verify before passing

---

## Criteria Gap Log

*Append entries here when Watcher fires on a pattern not covered above.*
