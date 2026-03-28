# Shared Lesson: Non-Independent Systems Weighting in Cross-Validation

**Task Source**: 2026-03-23-system-roster-definition (Daily Cosmos)  
**Date**: 2026-03-23  
**Agent**: systems-researcher (research task)

## Pattern

When designing a cross-validation algorithm that synthesizes signals from multiple systems, some system pairs share underlying input data or computation. Their apparent "agreement" may reflect input correlation rather than independent validation.

**Example**: BaZi and Tử Vi both derive core personality signals from the Four Pillars (birth year, month, day, hour). When they both predict "career: entrepreneurial direction," the agreement may be input-correlated rather than independent evidence amplification.

## Solution

Classify system pairs by independence:

| Cluster | Systems | Shared Input | Independence Weight | Rationale |
|---|---|---|---|---|
| Four Pillars cluster | BaZi, Tử Vi | Four Pillars | 0.6× | Same input, distinct interpretive frameworks (10 Gods vs. 12 Palaces) → partial independence |
| Planetary position cluster | Western Astrology, Vedic Astrology | Birth datetime → planetary positions | 0.7× | Same input positions, different zodiac (tropical vs. sidereal) + house systems → partial independence |
| Cross-cluster agreement | Any system from cluster A agreeing with system from cluster B | Different input sources | 1.0× | Genuinely independent inputs → full independence weight |

**Application**: In confidence scoring, weight cluster-internal agreement at partial coefficient (0.6× or 0.7×), not 1.0×. Prevents systematic overconfidence when multiple systems agree due to shared input.

## When to Apply

- Hybrid systems combining deterministic (birth-data) and self-report signals
- Any cross-validation where multiple predictors derive from the same underlying computation
- Confidence scoring that amplifies agreement signals — must account for input correlation

## When NOT to Apply

- Systems with genuinely independent input sources (different self-report, different base calculation)
- Single-system prediction (no cross-validation)
- Systems designed as intentional interpretive pairs (e.g., Gene Keys explicitly derived from Human Design for narrative extension)

## Generalization

Any multi-system synthesis should perform an input dependency audit before designing agreement scoring. Unmapped shared inputs lead to systematically inflated confidence signals.
