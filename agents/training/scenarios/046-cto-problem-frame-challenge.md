# Scenario 046 — CTO Challenges Router's Problem Framing When Frame Conceals Architectural Scope
**Source**: Schon (1983) *The Reflective Practitioner* — "problem framing as a design act"; PF2 criterion; architectural scope classification
**Difficulty**: Hard
**Primary failure mode tested**: CTO answering the question as framed ("add OAuth social login") without surfacing that the frame conceals an architectural decision — treating a Tier 3 auth architecture decision as a bounded feature addition
**Criteria tested**: PF2, D3, O2

## Synthetic CEO Intent
> "Add Google and GitHub OAuth login to our app."

## Setup
Three agents activated: CTO, Backend Developer, Engineering Manager.

**Router's framing (as dispatched to agents):**
> "Task: Add OAuth 2.0 social login with Google and GitHub providers."

**The CTO's domain knowledge must recognize:**

The current system uses session-based authentication:
- User logs in with email/password
- Server creates a session, stores session ID in a cookie
- Session is stored server-side (Redis or DB-backed)
- Every request is authenticated via session lookup

Adding OAuth 2.0 social login to this system creates an unresolved architectural conflict:

**Option A — Hybrid auth (bolt-on):**
Run OAuth alongside session auth. OAuth callback generates a local user record and creates a session (same mechanism as email/password). This maintains the session system but requires mapping OAuth identities to local accounts. Creates two identity systems: local email/password accounts and OAuth-connected accounts. Complexity: OAuth state management, account linking/merging, edge cases when a user's OAuth token is revoked.

**Option B — Migrate to token-based auth:**
Replace session-based auth entirely with JWT or opaque token auth. OAuth becomes the natural fit — tokens are stateless, no server-side session store required. This is a full auth layer migration affecting every endpoint, every middleware, every authenticated user's session.

**Why the Router's framing is wrong:**
"Add social login" implies Option A is the default — just bolt it on. But Option A is not simpler than Option B in the medium term: it creates two auth systems that must be maintained in parallel, with edge cases at the intersection (account merging, session expiry differences, token refresh vs session refresh). The Router's frame of "feature addition" conceals that the correct choice — which auth architecture to use going forward — is a Tier 3 decision that affects the entire system.

Answering "use Passport.js with Google and GitHub strategies" answers the OAuth implementation question but skips the auth architecture decision entirely. The implementation will proceed along Option A by default because Option A is what Passport.js makes easy — and the team will only discover the two-system complexity problem after it's built.

## Expected Behavior — Correct
CTO Round 1:

```json
{
  "position": "Before implementing OAuth, we must make an auth architecture decision. The Router's framing 'add social login' conceals this as a bounded feature when it is a Tier 3 architectural decision.",
  "frame_challenge": {
    "original_frame": "Add OAuth 2.0 social login",
    "frame_problem": "Assumes OAuth can be bolted onto the current session-based auth. This conceals a two-system architecture problem that must be decided before implementation.",
    "restated_question": "What is our auth architecture going forward — hybrid session+OAuth, or migrate to token-based auth — and how does that decision constrain the OAuth implementation?"
  },
  "reasoning": [
    "Current auth: session-based with server-side session store. Every authenticated request does a session lookup.",
    "Adding OAuth via Passport.js (the default path) creates Option A: two auth systems. OAuth users get a local account + session. Email/password users get a local account + session. But OAuth tokens have different expiry semantics than sessions, account linking is a manual implementation problem, and revocation behavior differs.",
    "Option B: Migrate to JWT/token-based auth first, then OAuth is the natural extension. All authenticated users use tokens. Session store removed. Simpler long-term, but a full migration affecting every endpoint and every active user session.",
    "The Router's frame 'add social login' makes Option A the path of least resistance — Passport.js implements it in 100 lines. Option B is invisible in the frame.",
    "If Option A is the correct decision (it may be — depends on timeline and team capacity), it should be a deliberate choice, not the accidental outcome of answering a mis-framed question."
  ],
  "architectural_decision_required": {
    "option_a": {
      "name": "Hybrid auth",
      "description": "Add OAuth alongside current session system. Passport.js handles OAuth, existing middleware handles session auth.",
      "complexity": "Medium now, High later — two identity systems, account linking edge cases",
      "migration_required": false,
      "delivery_estimate": "1-2 sprints"
    },
    "option_b": {
      "name": "Token-based migration",
      "description": "Migrate all auth to JWT or opaque tokens. Remove session store. OAuth becomes primary auth mechanism.",
      "complexity": "High now, Low later — single auth system",
      "migration_required": true,
      "delivery_estimate": "3-5 sprints"
    }
  },
  "recommendation": "This is a Tier 3 decision. Routing to full multi-agent discussion before implementation begins.",
  "confidence_pct": 88
}
```

CTO does NOT say "use Passport.js." CTO reframes the question, presents both options with explicit tradeoffs, and blocks implementation until the architectural decision is made.

## Failure Pattern
CTO Round 1:

```json
{
  "position": "Use Passport.js with the Google and GitHub OAuth strategies. This is straightforward to implement.",
  "reasoning": [
    "Passport.js is the standard Node.js OAuth library with Google and GitHub strategies available",
    "OAuth flow: redirect to Google/GitHub, receive callback with auth code, exchange for access token, create or update user record",
    "Implementation steps: install passport, passport-google-oauth20, passport-github2; configure callback routes; store OAuth provider ID in user table"
  ],
  "confidence_pct": 85
}
```

CTO answers the implementation question confidently, accurately, and completely — without ever recognizing that the auth architecture decision has not been made. The Passport.js recommendation implicitly commits the team to Option A (hybrid auth) without naming it as a choice. The two-system complexity problem will appear in sprint 3 when a user tries to log in with both methods.

A softer failure:
```json
{
  "position": "Use Passport.js for OAuth integration.",
  "reasoning": [
    "Passport.js handles Google and GitHub strategies",
    "Note: we should think about how this integrates with our current session system"
  ]
}
```

"We should think about" is a gesture at the problem without naming it. The CTO saw the issue but did not escalate it to a frame challenge. PF2 fail — the architectural decision remained implicit.

## Failure Signals
- CTO `position` recommends an OAuth library without raising the session/token architecture conflict → PF2 fail
- CTO `frame_challenge` field absent → PF2 fail
- CTO answers the "how to implement" question without first answering the "which auth architecture" question → PF2 fail
- CTO mentions the session/token issue in `reasoning[]` but does not escalate it to the `position` or a frame challenge → O2 fail (critical finding not surfaced to decision-making level)
- CTO correctly identifies the two-system problem but frames it as an "implementation note" rather than a blocking architectural decision → D3 fail (non-negotiable not invoked — auth architecture must be decided before implementation)

## Pass Conditions
- CTO `frame_challenge` field present and explains why the Router's framing is incomplete
- `position` explicitly states that an architectural decision is required before OAuth implementation begins
- Both Option A and Option B are described with concrete tradeoffs
- CTO does not recommend an OAuth library before the architectural decision is made
- The question is restated at the correct architectural scope
- Routing to Tier 3 discussion or equivalent escalation is recommended

## Trainer Evaluation Focus
Schon (1983) identifies problem framing as the most consequential act in design: "The framing of a problem determines what solutions are possible." The CTO's role is the most technically qualified agent — their domain expertise must recognize when a question's framing has concealed the actual decision space.

The failure is seductive because Passport.js is the correct implementation answer to the question as asked. CTO who answers with Passport.js is not wrong about Passport.js — they are wrong about the scope of the question. Technical competence applied to the wrong question is still a failure.

The trainer must distinguish:
1. CTO recognizes the framing problem and escalates it explicitly → PF2 pass
2. CTO mentions the framing problem in reasoning but still answers the framed question → PF2 fail (recognized but not acted on)
3. CTO does not recognize the framing problem → PF2 fail (missed entirely)

Pattern 2 is the hardest to catch and the most important to flag. It looks like awareness but it is not the same as the behavioral intervention required. A frame challenge in `reasoning[]` that doesn't change the `position` is not a frame challenge — it is a footnote.

Note: this scenario pairs with 039 (Trainer Specificity) — a trainer evaluating this discussion must cite specifically which round, which field, and what was in the CTO's `reasoning[]` that was not surfaced to `position`.
