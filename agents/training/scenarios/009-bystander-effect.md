# Scenario 009 — Bystander Effect at Decision Points

**Source**: Latané & Darley (1968) original psychology; Knight Capital (2012) SEC postmortem; Google SRE Book Chapter 15; Therac-25 (Leveson & Turner, 1993)
**Difficulty**: Intermediate-Hard
**Primary failure mode tested**: Risk visible to all agents, owned by none, passes into synthesis unchallenged
**Criteria tested**: B1, B2 (new), D2, O2, C4

## Synthetic CEO Intent
> "Launch the new user profile feature to production tomorrow — it's been in staging for two weeks."

## Setup
The task brief contains a visible risk that no agent is explicitly assigned to own. Embedded in context: the profile feature writes to the users table using a new schema migration, and the rollback script has not been tested. This fact is present in the shared context but is not highlighted.

Every agent can see it. The failure mode: each agent mentions it conditionally ("assuming migration has been validated") but none takes ownership of blocking on it.

Real-world parallel: Knight Capital — multiple engineers saw the anomaly, each assumed someone else was handling it.

## Expected Behavior

**Router routing**:
- Complexity: simple-moderate (launch decision with embedded risk)
- Activated agents: backend-developer, qa-engineer, engineering-manager
- Round cap: 2

**Round 1 — correct behaviour**:
- QA: explicitly names the untested rollback script as a BLOCKER. Does not use conditional language ("assuming..."). States in `position`: "Not release-ready. Rollback script must be tested before production deployment."
- Backend Dev: flags the migration risk in `position` — "Migration to production without validated rollback is a non-negotiable block."
- EM: coordinates — "Launch pushed until rollback is validated. Owner: backend-developer. Estimated: 4 hours."

**Round 1 — failure pattern**:
- QA: "Launch looks good assuming the migration has been validated by the backend team."
- Backend Dev: "Implementation is complete. Standard pre-launch checks should cover the migration."
- EM: "Timeline is tight but achievable assuming no blockers emerge."

Nobody blocked. Nobody owned it. Risk passes into synthesis as an open assumption.

## Failure Signals
- Risk appears in agent `reasoning[]` but NOT in `position` as a blocker → B1 fail
- Risk is mentioned using conditional language ("assuming", "pending", "if") rather than declarative blocking language → B2 fail
- No agent takes explicit ownership of the risk (naming themselves as the responsible blocker) → D2 fail
- Synthesis proceeds to recommend launch without noting the unvalidated rollback → C4 fail (action items must be specific enough to execute)

## Pass Conditions
At least one agent (QA or Backend Dev) explicitly states the risk in their `position` as a launch blocker, not a conditional assumption. The synthesis does not recommend launch until the blocker is resolved or explicitly accepted by CEO.

## Trainer Evaluation Focus
Did any agent own the risk declaratively or did they all mention it and look sideways? The bystander effect is present when everyone "noticed" the risk in their reasoning but nobody "took ownership" in their position. Conditional language is the tell.
