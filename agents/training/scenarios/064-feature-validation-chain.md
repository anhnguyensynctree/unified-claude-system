# Scenario 064 — Feature Validation Chain

**Difficulty**: Basic
**Primary failure mode tested**: Wrong validation chain assigned to feature based on type; task-level validation chain mismatches feature type; cross-functional feature gets single-department sign-off.
**Criteria tested**: MF1, FD3 (sign-off dimension), EP2

## Validation Chain Reference

| Feature Type | Sign-off Required |
|---|---|
| product | cpo |
| engineering | cpo + cto |
| research | cpo + cro |
| cross-functional | cpo + cto (minimum; + cro if research involved) |

| Task Type | Validation Chain |
|---|---|
| research | researcher → cro → cpo |
| Engineering (standard) | dev → qa → em |
| Engineering (infra_critical) | dev → cto |

## Scenario A — Engineering Feature, Wrong Validation

**Setup:** FEATURE-005:
```
- Type: engineering
- Validation: cpo
```

**Expected behavior:**
- Trainer flags: engineering feature requires `Validation: cpo + cto`
- `cpo` alone is only valid for `product` type features
- EP2 fail: FEATURE block has wrong Validation field

---

## Scenario B — Research Feature, Missing CRO

**Setup:** FEATURE-008:
```
- Type: research
- Validation: cpo + cto
```

**Expected behavior:**
- Trainer flags: research feature requires `Validation: cpo + cro`
- CTO is not a research sign-off authority
- EP2 fail

---

## Scenario C — Cross-Functional, Missing CTO

**Setup:** FEATURE-011 (cross-functional with backend+CRO departments):
```
- Type: cross-functional
- Validation: cpo + cro
```

**Expected behavior:**
- Trainer flags: cross-functional feature with engineering tasks requires `cpo + cto` minimum
- If CRO is involved: `cpo + cro + cto`
- EP2 partial fail — CTO missing from cross-functional validation

---

## Scenario D — Correct Feature Done → MF1 Pass

**Setup:** FEATURE-003:
```
- Type: engineering
- Status: in-progress
- Tasks: TASK-003a (done), TASK-003b (done)
- Validation: cpo + cto
```
CPO and CTO have both signed off. Status not yet updated.

**Expected behavior:**
- Trainer flags: all tasks done, sign-off complete → Status must be updated to `done`
- MF1 fail if Status remains `in-progress`

**Pass condition:** cleared-queue.md shows `Status: done` after CPO + CTO sign-off is recorded.

---

## Pass Conditions (across all scenarios)

- Engineering features: `Validation: cpo + cto`
- Research features: `Validation: cpo + cro`
- Cross-functional features: `Validation: cpo + cto` (+ cro if research dept involved)
- Product features: `Validation: cpo`
- Task-level Validation chain matches task type and infra_critical flag
- Feature Status updates to `done` when all tasks done + sign-off complete

## Trainer Evaluation Focus

Validation routing is a structural check, not a behavioral one. Trainer must match the feature `Type:` field against the validation chain table — no judgment call. A mismatch between `Type:` and `Validation:` is an EP2 fail regardless of whether the wrong reviewer would have caught the issue anyway. Sign-off chain correctness is non-negotiable.
