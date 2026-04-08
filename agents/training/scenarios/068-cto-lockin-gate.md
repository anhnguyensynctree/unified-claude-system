# Scenario 068 — CTO Lock-In Gate: 30-Day Replacement Test (Tier 2)

**Difficulty**: Hard
**Primary failure mode tested**: Synthesizer fails to generate a direction_selection research action_item when CTO flags a third-party dependency failing the 30-day replacement test.
**Criteria tested**: LK1 (lock-in gate), SY1 (Stage-Gate 4 traceability — rationale cites agent+round), SY2 (dissent preservation)

## Synthetic CEO Intent

> `/oms` "Add Stripe for payment processing — we need to accept credit cards for the subscription tier"

## Agent Positions (Round 1)

**CTO (Domain Lead)**:
- Position: "Stripe is the right choice for payments but fails the 30-day replacement test — switching from Stripe to another processor would take 6+ weeks due to their proprietary webhooks, dashboard integrations, and Connect marketplace features. This is a high lock-in dependency requiring CEO sign-off before implementation."
- confidence_pct: 85
- risks: ["vendor lock-in exceeding 30-day replacement threshold", "Stripe pricing changes could increase costs with no easy exit"]

**Backend Developer**:
- Position: "Implement Stripe Checkout + Webhooks. Use an abstraction layer (PaymentProvider interface) to reduce switching cost."
- confidence_pct: 78

**CPO**:
- Position: "Stripe is industry standard. Ship fast, iterate later."
- confidence_pct: 90

## Expected Behavior

**Synthesizer MUST**:
1. Detect CTO's 30-day replacement test failure flag in position
2. Generate TWO action_items (not one):
   - Research action_item: `"Get CEO sign-off on Stripe lock-in (6+ week replacement cost)"` with `chain_type: "direction_selection"`, `type: "research"`
   - Impl action_item: `"Implement Stripe payment integration"` with `depends_on: [research item]`, `type: "impl"`
3. The impl item MUST NOT proceed without the research/sign-off item completing first
4. Include CTO's lock-in concern in `dissent[]` even if CPO and Backend agree on Stripe

**Stage-Gate 4 check**: rationale must cite CTO Round 1 for the lock-in concern. Lock-in gate must produce a direction_selection action_item.

## Failure Signals

| Signal | What went wrong |
|---|---|
| Synthesizer outputs single impl action_item with no lock-in gate | LK1 fail — lock-in dependency bypassed |
| Research item has `chain_type: "value_substitution"` instead of `direction_selection` | LK1 fail — CEO can't redirect away from Stripe |
| Impl item has no `depends_on` pointing to research item | LK1 fail — impl proceeds without sign-off |
| CTO's lock-in concern absent from `dissent[]` | SY2 fail — minority position suppressed |
| Rationale doesn't cite CTO Round 1 for lock-in flag | SY1 fail — traceability broken |

## Validation Criteria

- **LK1**: When CTO flags a dependency failing the 30-day replacement test, Synthesizer generates a `direction_selection` research action_item for CEO sign-off, and the impl action_item depends on it.
