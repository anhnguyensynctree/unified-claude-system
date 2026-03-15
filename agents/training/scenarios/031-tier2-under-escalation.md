# Scenario 031 — Tier 2 Under-Escalation / Security Domain Omission

**Source**: OWASP Authentication Cheat Sheet (2023) — password reset token requirements: single-use, short TTL, invalidation on use and on new-request; NIST SP 800-63B §5.1.1.2 — memorized secret reset; Ferguson & Schneier (2003) *Practical Cryptography* Ch. 15 — token lifecycle
**Difficulty**: Intermediate-Hard
**Primary failure mode tested**: Router classifies a 3-domain task as 2-domain by treating security constraints as implementation details of the Backend domain rather than as a separate domain requiring dedicated Security analysis
**Criteria tested**: R2, R6, R7

## Synthetic CEO Intent
> "Build a forgot password flow — users should be able to request a password reset by email and follow a link to set a new password."

## Setup
Password reset spans three distinct domains that each carry independent failure modes:

1. **Backend Dev**: token generation (cryptographically random, sufficient entropy), token storage (hashed, not plaintext), reset endpoint logic, email send via provider
2. **Frontend Dev**: forgot-password form, reset form (new password + confirm), success/error states, redirect after reset
3. **Security**: token invalidation rules — token must be invalidated on use, on new reset request, and must expire (short TTL, e.g., 15 minutes); email link must not be cacheable (token in path, not query param for some implementations); account enumeration via timing or error message difference; rate limiting on the request endpoint

The Security domain is not a subset of Backend — it requires dedicated analysis of threat models that Backend Dev does not own: what happens if a reset link is intercepted? What if a user requests reset twice? What if an attacker enumerates valid emails via error message differences? These are Security questions, not implementation questions.

**Partial irreversibility**: once a reset flow is live, reset tokens are in flight in user inboxes. A schema or token-format change mid-deploy invalidates outstanding tokens without warning — users following already-sent links get broken flows. This is not fully reversible without a coordinated invalidation and re-send strategy.

## Expected Behavior — Correct

**Router routing**:
```json
{
  "tier": 2,
  "complexity": "compound",
  "complexity_reasoning": "Complicated-high. Three domains: Backend (token generation, storage, email dispatch), Frontend (request and reset forms, redirect logic), Security (token invalidation lifecycle, account enumeration prevention, rate limiting, TTL). domain_breadth=2; reversibility=1 (live reset tokens in user inboxes cannot be safely migrated mid-deploy — outstanding links break on token format change); uncertainty=1 (security threat model for reset flows has non-obvious enumeration and timing attack vectors). Total=4 → Tier 2. Security is a first-class domain, not a Backend implementation detail.",
  "activated_agents": ["backend-developer", "frontend-developer", "security-reviewer"],
  "round_cap": 2,
  "stage_gate": "Security must define token invalidation rules and TTL before Backend implements token lifecycle logic",
  "locked": true
}
```

Security agent explicitly addresses: single-use enforcement, TTL (15-minute recommendation with reasoning), invalidation on new request, account enumeration via error message parity, rate limiting on the /forgot-password endpoint.

Backend scopes token generation (CSPRNG, 256-bit entropy minimum, stored as bcrypt hash), storage schema, invalidation logic aligned with Security spec.

Frontend scopes forms, error states, and confirms error messages are identical for "email found" and "email not found" responses (account enumeration prevention).

## Failure Pattern
Router classifies as Tier 1, activates Backend Dev + Frontend Dev:

```json
{
  "tier": 1,
  "complexity": "simple",
  "complexity_reasoning": "Complicated-low. Standard backend feature (token generation + email) plus frontend form. domain_breadth=1, reversibility=0, uncertainty=0, total=2 → Tier 1. Known pattern.",
  "activated_agents": ["backend-developer", "frontend-developer"],
  "round_cap": 1,
  "locked": true
}
```

No numeric score. Security treated as implicit. Token invalidation rules not discussed. Account enumeration not considered. Backend implements a token that is not invalidated on second request (race condition: attacker requests reset, user requests reset, attacker's first link still valid). Frontend shows "Email not found" for unknown addresses, enabling account enumeration.

## Failure Signals
- Router `complexity_reasoning` contains no numeric score → R6 fail
- Router `activated_agents` omits `security-reviewer` → R7 fail (3 domains present, Security domain omitted)
- Router `complexity_reasoning` describes security as "standard backend implementation" rather than a separate domain → R2 fail (domain_breadth undercounted at 1 instead of 2)
- Router `reversibility` scored as 0 despite live tokens in user inboxes during deploy → R6 fail (reversibility dimension miscounted)
- No `stage_gate` despite Security-to-Backend dependency on token invalidation spec → Tier 2 coordination signal absent

## Pass Conditions
Router outputs `tier: 2`, `complexity: "compound"`, numeric score `total=4` with `reversibility=1` explicitly reasoned against live-token migration risk. `security-reviewer` in `activated_agents`. `stage_gate` names the Security-to-Backend dependency on token invalidation rules. `complexity_reasoning` explicitly argues Security is a first-class domain, not a Backend subset.

## Trainer Evaluation Focus
The discrimination tested here is whether the Router treats security constraints as an implementation checklist (Backend Dev will "handle security") versus a domain requiring dedicated threat model analysis. A Router that activates Backend + Frontend but not Security has implicitly assumed that implementation correctness subsumes security correctness — a category error.

Watch for `complexity_reasoning` that uses the phrase "standard pattern" or "known flow" for password reset. Password reset is a well-understood feature but a frequently misimplemented one precisely because the security threat model is non-obvious to backend developers. If the Router classifies it as low-uncertainty because it is "well-known," it is conflating familiarity with correctness.

The reversibility score is a secondary signal: zero-scoring reversibility on a flow that puts tokens into user inboxes indicates the Router is not modeling state that exists outside the codebase.
