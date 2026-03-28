# Shared Lessons: Schema Patterns

Cross-project lessons for database schema design, migrations, and data modeling.

2026-03-23 | 2026-03-23-schema-cultural-context-confidence | importance:high | Per-user aggregate table pattern for multi-dimension systems: (1) Identify logical home — per-user state vs per-dimension state. (2) Include cadence/tracking columns (e.g., turn_count for re-estimation thresholds). (3) Use consistent numeric types across dimension tables (NUMERIC(4,3) for confidence). (4) Include constraint validation at DB layer (CHECK on ranges). (5) Enable RLS immediately — no backfill needed in pre-production. (6) Document default semantics clearly — defaults are placeholders, not confirmed signals; extraction logic branches on confidence or validation states, not enum values.
Surfaces when: adding a new aggregate state table to a multi-table schema where dimension data is distributed across typed tables and user-level state (confidence, classification) must be centralized.
