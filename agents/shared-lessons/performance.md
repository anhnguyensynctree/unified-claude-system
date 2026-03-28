# Shared Lessons: Performance Patterns

Cross-project lessons for performance-critical architectural and code decisions.

2026-03-23 | 2026-03-23-schema-cultural-context-confidence | importance:high | Integer counters beat timestamp queries for cadence-triggered operations: For N-periodic actions (re-estimate every 5 turns, run cleanup every 100 events), store an INTEGER counter column that increments on each triggering event. Check cadence in-memory with counter % N == 0. Alternative (timestamp-based): store last_action_at and query NOW() - last_action_at > INTERVAL creates overhead: comparison on every event, timezone handling, index contention on timestamp ranges. Counter pattern: O(1) check, no DB overhead until threshold, scales to dozens of per-user cadence rules.
Surfaces when: designing a background job, rate limiter, or re-estimation pipeline that fires at regular intervals (every N events, N turns, N sessions); pre-production schema is being designed and the operation will be on a hot path (checked on every turn or high-frequency operation).
