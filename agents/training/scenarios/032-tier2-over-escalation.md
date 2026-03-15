# Scenario 032 — Tier 2 Over-Escalation / Index Additive Signal Misread

**Source**: PostgreSQL documentation §11 (indexes) — additive, reversible, non-blocking with CONCURRENTLY flag; Kleppmann (2017) *Designing Data-Intensive Applications* Ch. 3 — index structures and their operational properties; Kahneman (2011) *Thinking Fast and Slow* — availability heuristic (salient keywords inflate perceived risk)
**Difficulty**: Intermediate
**Primary failure mode tested**: Router over-weights the keyword "database change" as an architectural/irreversibility signal, escalating to Tier 3 when the actual change (adding an index, implementing sort state) is additive, reversible, and bounded to 2 domains
**Criteria tested**: R2, R6, R7

## Synthetic CEO Intent
> "Add column sorting to the admin users table — users should be able to click column headers to sort by name, email, or created_at."

## Setup
The task has two domains:
1. **Backend Dev**: add a `sort_by` / `sort_dir` query parameter to the users list endpoint; add a database index on `name`, `email`, and `created_at` to support efficient sorting; update the query builder to apply `ORDER BY` from validated params
2. **Frontend Dev**: add sort icons to column headers; manage sort state (active column, direction); pass sort params to API on column click; update table render

The database index addition is the critical calibration point. Adding an index in PostgreSQL is:
- **Additive**: does not change existing data, schema, or query behavior for non-sorting queries
- **Reversible**: `DROP INDEX` removes it cleanly with no data loss
- **Non-breaking**: existing queries unaffected; no migration of existing data required
- **Non-blocking** (with `CREATE INDEX CONCURRENTLY`): does not lock the table during creation

This is categorically different from a schema-breaking change (adding a NOT NULL column without a default, changing a column type, removing a column). The Router must distinguish additive schema changes from destructive ones.

## Expected Behavior — Correct

**Router routing**:
```json
{
  "tier": 2,
  "complexity": "compound",
  "complexity_reasoning": "Complicated-high. Two domains: Backend (query parameter handling, ORDER BY logic, index creation) and Frontend (sort state, column header UI, API parameter passing). domain_breadth=2; reversibility=0 (index addition is fully reversible via DROP INDEX — additive schema changes do not constitute irreversibility; no data migration required); uncertainty=1 (Backend must validate sort_by param against allowlist to prevent injection; index strategy for composite vs per-column is a genuine design choice). Total=3 → Tier 2. Note: 'database change' is additive here — index addition is not an architectural event.",
  "activated_agents": ["backend-developer", "frontend-developer"],
  "round_cap": 2,
  "stage_gate": "Backend must define sort parameter contract (field names, direction values, default) before Frontend implements sort state",
  "locked": true
}
```

Backend Dev notes the `CREATE INDEX CONCURRENTLY` option for production safety and defines the allowlist validation for `sort_by` to prevent ORDER BY injection.

Frontend Dev scopes sort state management (controlled component, URL-persisted or local), icon states (unsorted / asc / desc), and API call structure.

## Failure Pattern
Router classifies as Tier 3, activates 4+ agents:

```json
{
  "tier": 3,
  "complexity": "complex",
  "complexity_reasoning": "Complex domain. Database schema change required — index additions have architectural implications and are difficult to reverse once in production with live data. Multiple domains: Backend, Frontend, Database/Infrastructure, QA. Irreversibility score is high — schema changes in production databases require DBA review. domain_breadth=3, reversibility=2, uncertainty=1, total=6 → Tier 3.",
  "activated_agents": ["backend-developer", "frontend-developer", "qa-engineer", "architect"],
  "round_cap": 3,
  "locked": true
}
```

The error: `reversibility=2` is wrong. Index addition is additive and reversible. The Router has activated an Architect and QA for a 2-domain bounded task, wasted 2 additional agent calls, and introduced unnecessary coordination overhead. The `stage_gate` and multi-round structure add process friction that slows a straightforward implementation.

## Failure Signals
- Router `tier` is 3 and `complexity` is "complex" for a 2-domain additive task → R2 fail (task reality is Complicated-high, not Complex)
- Router `complexity_reasoning` scores `reversibility=2` for index addition → R6 fail (index is additive and reversible; miscounted dimension)
- Router `activated_agents` contains 4+ agents including Architect → R7 fail (Tier 2 = 2-3 agents; Architect activation not warranted for additive index)
- Router `complexity_reasoning` uses "architectural implications" or "DBA review required" for a standard B-tree index → R2 fail (availability heuristic on "database change" keyword)
- Router `round_cap` is 3 or higher → over-processing for a 2-domain bounded task

## Pass Conditions
Router outputs `tier: 2`, `complexity: "compound"`, `reversibility=0` with explicit reasoning that index addition is additive and reversible. Exactly 2 agents activated (Backend Dev, Frontend Dev). `complexity_reasoning` explicitly addresses why "database change" does not imply irreversibility in this case. `stage_gate` captures the Backend-to-Frontend parameter contract dependency.

## Trainer Evaluation Focus
This scenario tests whether the Router applies Cynefin reasoning to the actual change characteristics or pattern-matches on surface keywords. "Database change" is a high-salience keyword that triggers an architectural caution reflex — but not all database changes are equal. Additive changes (indexes, new nullable columns with defaults, new tables) are fundamentally different from destructive changes (dropping columns, changing types, NOT NULL without defaults).

The Router must demonstrate that it can reason about the specific nature of a database change, not just flag the category. A Router that automatically escalates any task containing "database" to Tier 3 will systematically over-escalate a large class of routine tasks.

Watch for `reversibility` scoring. If the Router assigns reversibility=1 or reversibility=2 to index addition, it has failed to distinguish additive schema changes from destructive ones — this is a teachable moment about what "irreversible" means in the Cynefin framework for software systems.
