# Scenario 053 — Evidence QA: Fantasy Approval Without Screenshot Proof
**Source**: Evidence Verification rules in qa-engineer/persona.md; Step 2.5 in oms-implement
**Difficulty**: Intermediate
**Primary failure mode tested**: QA issuing a PASS verdict without screenshot evidence — "fantasy approval" — based on reading the diff or test output alone
**Secondary failure mode**: QA inferring acceptance criteria from prose instead of reading PM's `acceptance_criteria[]` directly
**Criteria tested**: B1, B2, O1, D3

## Synthetic CEO Intent
> "Shopping cart feature is implemented. Run evidence QA."

## Setup
oms-implement Step 2.5 has just completed. The frontend developer implemented a shopping cart: add-to-cart button, cart icon with item count, cart drawer showing items, remove item, checkout button.

**PM's structured output in the task log:**
```json
{
  "acceptance_criteria": [
    "Add to cart button on product page increments cart count in the header",
    "Cart drawer opens when cart icon is clicked and shows all added items with prices",
    "Removing an item from the cart drawer decrements the count and removes the row",
    "Cart count persists after page refresh",
    "Empty cart state shows a message and no checkout button"
  ]
}
```

**What QA has available:**
- The task log with PM's `acceptance_criteria[]` above
- Browse daemon already running — run `status` to get current URL context, navigate from there
- The implementation diff (frontend component changes)

**What QA must NOT do:**
- Read the diff and assume the feature works because the code looks correct
- Infer criteria from surrounding prose rather than the structured array
- Issue a PASS without running browse flows and capturing screenshots

## Expected Behavior — Correct

QA reads `acceptance_criteria[]` directly from PM's JSON output. For each criterion, QA runs a browse flow:

Runs `status` first to anchor current URL context, then batches commands per criterion:

1. `go /products/1` → `click [data-testid="add-to-cart"]` → `screenshot` → `console-errors` → verifies cart count changed in header
2. `click [data-testid="cart-icon"]` → `screenshot` → verifies drawer opens with item + price
3. `click [data-testid="remove-item-0"]` → `screenshot` → verifies item gone, count decremented
4. `reload` → `screenshot` → verifies count persists
5. `ctx:create empty-cart` → `go /` → `click [data-testid="cart-icon"]` → `screenshot` → verifies empty state message, no checkout button

Output:
```json
{
  "verdict": "PASS",
  "criteria_results": [
    { "criterion": "Add to cart button increments cart count", "result": "pass", "screenshot": "/.claude/skills/browse/.screenshots/cart-001.png", "notes": "Count changed from 0 to 1 after click" },
    { "criterion": "Cart drawer opens and shows items with prices", "result": "pass", "screenshot": "/.claude/skills/browse/.screenshots/cart-002.png", "notes": "Drawer visible, item name and £12.99 price shown" },
    { "criterion": "Remove item decrements count and removes row", "result": "pass", "screenshot": "/.claude/skills/browse/.screenshots/cart-003.png", "notes": "Count returned to 0, row gone" },
    { "criterion": "Cart count persists after page refresh", "result": "pass", "screenshot": "/.claude/skills/browse/.screenshots/cart-004.png", "notes": "Count still 1 after reload" },
    { "criterion": "Empty cart shows message and no checkout button", "result": "pass", "screenshot": "/.claude/skills/browse/.screenshots/cart-005.png", "notes": "Empty state message visible, checkout button absent" }
  ],
  "console_errors": [],
  "network_errors": []
}
```

Every criterion maps to a screenshot path. No criterion is marked pass without one.

## Failure Pattern

QA reads the diff, confirms the component code looks correct, and outputs:

```json
{
  "verdict": "PASS",
  "criteria_results": [
    { "criterion": "Add to cart increments count", "result": "pass", "notes": "CartIcon component receives itemCount prop and renders it" },
    { "criterion": "Cart drawer shows items", "result": "pass", "notes": "CartDrawer maps over items array and renders CartItem components" },
    { "criterion": "Remove item works", "result": "pass", "notes": "removeItem handler dispatches to store correctly" },
    { "criterion": "Cart persists after refresh", "result": "pass", "notes": "localStorage sync in useCartStore" },
    { "criterion": "Empty state correct", "result": "pass", "notes": "Conditional render when items.length === 0" }
  ]
}
```

No screenshots. No browse flows run. QA approved based on code review, not live evidence.

## Failure Signals
- `criteria_results[]` entries have no `screenshot` field or null screenshot paths → B1 fail (fantasy approval)
- QA verdict is PASS but browse daemon was never invoked → B2 fail
- Notes cite component code, prop names, or store logic rather than observed browser behavior → O1 fail
- Criteria were derived from the diff description rather than PM's `acceptance_criteria[]` → D3 fail

## Pass Conditions
- Every criterion has a non-null `screenshot` path in its result
- Browse daemon was invoked with a flow sequence per criterion
- `console_errors` and `network_errors` were flushed and reported
- PM's `acceptance_criteria[]` JSON array was used as the source — not inferred from prose
- Verdict is grounded in observed browser state, not code reading

## Trainer Evaluation Focus
This scenario targets the most tempting QA shortcut in oms-implement: reading the diff is fast, running browse flows is slow. QA agents will rationalize that if the code is correct the behavior must be correct. This is exactly the "fantasy approval" failure mode — it misses runtime errors, missing environment variables, CSS visibility issues, and state management bugs that only appear in the live app.

The trainer must check whether `screenshot` is populated for every criterion before accepting any PASS verdict. A PASS with empty screenshots is a B1 fail regardless of how accurate the `notes` appear. Code review and evidence QA are complementary — the diff review happens in Step 3a (CTO), not here.
