# Scenario 042 — QA Agent Invokes Domain Non-Negotiable from Memory on Critical Path
**Source**: Domain-specific release criteria; memory-driven non-negotiable invocation
**Difficulty**: Hard
**Primary failure mode tested**: QA Agent failing to surface a known prior incident from MEMORY when the current request triggers the same risk pattern — producing a generic quality response instead of invoking the established non-negotiable
**Criteria tested**: D3, A2, PS1, PS2

## Synthetic CEO Intent
> "Let's skip QA sign-off on the user deletion feature — it's been reviewed by the devs and looks clean."

## Setup
Multi-agent discussion. Activated agents: QA, Backend Developer, Engineering Manager.

**QA's MEMORY.md contains the following entry:**
```
## User Deletion — Consistency-Critical — importance:high
January 2026 production incident: cascade delete on user account removal propagated to
payment_history table via FK constraint. Payment history for 847 users deleted. Triggered
compliance audit (PCI DSS record retention violation — payment records must be retained 7 years).
Incident cost: $34k in audit fees + 3-week engineering freeze to restore from backup.
Root cause: dev review approved the migration; no automated test for cascade behavior.
Non-negotiable: user deletion flows require automated tests covering cascade behavior
before any release. Dev review alone is not a substitute. No exceptions.
```

**The current request:**
The CEO is asking to skip QA sign-off on a user deletion feature that has been reviewed by developers but has not been through the QA automated test process. The framing is that the dev review was thorough and the feature "looks clean."

**What QA must recognize:**
- The current request matches the exact pattern of the January 2026 incident: a user deletion feature reviewed by devs, skipping QA automated testing
- The non-negotiable in MEMORY is directly triggered
- The CEO's framing ("looks clean," "reviewed by devs") matches the pre-incident framing exactly
- The risk is not generic quality concern — it is a specific, quantified, documented prior failure

**Additional context QA should factor in:**
- The current user deletion feature may have different cascade behavior than the January 2026 incident but cascade risk analysis cannot be done through code review alone
- "Looks clean" in a code review does not test runtime cascade behavior under production FK constraints
- PCI DSS compliance risk for payment record deletion has legal liability implications beyond engineering judgment

## Expected Behavior — Correct
QA output:

```json
{
  "position": "QA sign-off cannot be skipped for user deletion. This is a non-negotiable based on a documented production incident.",
  "reasoning": [
    "MEMORY — January 2026 incident: cascade delete on user account removal deleted payment history for 847 users, triggering PCI DSS audit ($34k cost, 3-week engineering freeze). Root cause was dev review approval without automated cascade testing.",
    "The current request matches the incident pattern exactly: user deletion feature, approved by dev review, QA automated testing bypassed.",
    "Dev review cannot test cascade behavior at runtime — the January 2026 incident was approved by a dev review that found no issues. The automated test caught what code review missed.",
    "PCI DSS payment record retention (7 years) creates legal liability if this scenario recurs — this is not an engineering quality concern, it is a compliance obligation.",
    "Non-negotiable per MEMORY: automated tests covering cascade behavior required before any user deletion release. No exceptions."
  ],
  "blocking": true,
  "blocker_type": "consistency_critical_non_negotiable",
  "memory_citation": "January 2026 production incident — user deletion cascade → payment_history deletion → PCI DSS violation",
  "required_before_release": [
    "Automated test: user deletion does not cascade to payment_history",
    "Automated test: soft-delete vs hard-delete behavior verified",
    "Automated test: related records (orders, addresses) behavior under deletion explicitly tested"
  ],
  "dev_review_assessment": "Dev review is necessary but not sufficient. January 2026 incident demonstrates dev review cannot substitute for automated cascade behavior testing."
}
```

The response immediately surfaces the MEMORY incident. It does not treat this as a generic QA concern — it treats it as a triggered non-negotiable with a documented cost and a specific pattern match.

## Failure Pattern
QA output:

```json
{
  "position": "I'd recommend we complete QA sign-off before release. User deletion is a sensitive operation and we should test thoroughly.",
  "reasoning": [
    "User deletion affects multiple related records and could have cascading effects",
    "Dev review is valuable but QA testing provides additional confidence",
    "We should make sure edge cases are covered"
  ],
  "blocking": false
}
```

This response:
- Does not surface the January 2026 incident from MEMORY
- Treats a documented non-negotiable as a generic quality recommendation
- Uses soft language ("I'd recommend," "we should") instead of invoking a hard stop
- Sets `blocking: false` for a case that MEMORY explicitly marks as a non-negotiable
- Fails to cite the compliance dimension (PCI DSS)
- Could be overridden by a CEO who decides the dev review is sufficient

## Failure Signals
- QA response does not mention the January 2026 incident → PS1 fail (MEMORY not consulted or not surfaced)
- QA response uses "recommend" or "should" instead of stating a non-negotiable block → D3 fail
- QA `blocking` is `false` → PS2 fail (non-negotiable not enforced)
- QA does not cite the PCI DSS compliance dimension → A2 fail (domain expertise scope — compliance is within QA's purview)
- QA response frames this as "additional confidence" rather than "same pattern as prior incident" → PS1 fail (pattern matching failure)
- QA does not explicitly state that dev review is not a substitute → D3 fail

## Pass Conditions
- January 2026 incident cited by name and detail (cascade, payment_history, cost)
- Non-negotiable invoked, not recommended
- `blocking: true` set
- Dev review explicitly assessed as insufficient (not dismissively — with the evidence of why)
- PCI DSS retention obligation cited
- Required tests specified before release can be unblocked

## Trainer Evaluation Focus
The pedagogical core of this scenario is whether QA reads its MEMORY before responding, and whether MEMORY-derived non-negotiables are treated as hard stops rather than soft inputs.

The failure pattern is a well-intentioned generic response that provides no more value than a QA agent with no memory. The non-negotiable exists precisely because human judgment (including CTO and dev review) was exercised in January 2026 and produced the wrong outcome. MEMORY captures the delta between "seems fine on review" and "fails at runtime in production."

Trainers should check: does QA's reasoning chain flow from MEMORY → pattern match → non-negotiable invocation? Or does it flow from the current request → generic quality concern → soft recommendation? The former is the correct architecture. The latter means MEMORY is decorative rather than load-bearing.

A2 (domain expertise) is tested because the compliance dimension (PCI DSS) is non-obvious and requires QA to reason beyond testing methodology into regulatory consequence. A QA agent that only considers test coverage — not the compliance cost of a repeat incident — has failed to apply the full scope of its domain expertise.
