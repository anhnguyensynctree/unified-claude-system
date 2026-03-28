# Shared Lesson: Questionnaire-System Tiering in Hybrid (Birth + Self-Report) Pipelines

**Task Source**: 2026-03-23-system-roster-definition (Daily Cosmos)  
**Date**: 2026-03-23  
**Agent**: systems-researcher (research task)

## Pattern

Hybrid systems that combine birth-data (deterministic) and self-report (questionnaire) signals often conflate them into a single roster, causing:

1. **False confidence from sparse coverage** — birth-data only (no questionnaire) provides incomplete personality profile, yet system presents reading as complete
2. **Wrong questionnaire trigger logic** — treats missing questionnaire data as "not yet gathered" rather than "not yet needed"
3. **Unfair system weighting** — empirically-strongest systems (Big Five, Attachment Theory) are questionnaire-only, so birth-data users never see them in agreement scoring

## Solution

Explicitly tier systems by input requirement:

**Tier 1**: Birth-data primary (deterministic from birth datetime + location ± gender)
- Western Astrology, BaZi, Tử Vi, Vedic, Human Design, Numerology, Lunar Calendar, Feng Shui Kua
- Active at onboarding. Full output generated from birth data alone.

**Tier 2**: Questionnaire-validated (self-report questionnaire required)
- Big Five, Enneagram, MBTI, DISC, StrengthsFinder, Attachment Theory, Holland Codes, Wealth Psychology, Jungian Archetypes, Ayurveda, TCM
- **Empty at onboarding** — this is correct. Slots filled as user completes targeted questionnaire.
- Dynamic questionnaire generation logic: "Which Tier 2 systems have empty slots? Prioritize by domain coverage gaps."

**Tier 3**: Extended/optional (high self-report burden, overlapping coverage)
- Ikigai, Spiral Dynamics, I Ching, Shadow Work — post-MVP

## Data Model Implications

```
User Profile Structure:
├── Birth Data (static at onboarding)
│   ├── DateTime
│   ├── Location (geocoded lat/long)
│   └── Gender (optional, for Tử Vi + Kua)
├── Tier 1 Systems Output (computed from birth data)
│   ├── Western Astrology: {sun_sign, moon_sign, rising, chart_aspects, ...}
│   ├── BaZi: {day_master, 10_gods, element_balance, ...}
│   └── ... (8 systems total)
├── Tier 2 Systems Output (empty at onboarding, filled by questionnaire)
│   ├── big_five: null → {O, C, E, A, N} after questionnaire
│   ├── attachment_theory: null → {anxiety, avoidance} after questionnaire
│   └── ... (11 systems total)
└── Questionnaire Metadata
    ├── completed_systems: [big_five, enneagram, ...] (filled)
    └── pending_systems: [holland_codes, ...] (empty slots)
```

## Prevents

- Presenting incomplete readings as complete (Tier 2 slots have known-absent handling)
- Wrong questionnaire targeting (missing data is not failure; it's the questionnaire's job)
- Unfair system weighting in agreement scoring (questionnaire systems not compared until they have data)

## Implementation Checklist

- [ ] Database schema reflects three-tier structure
- [ ] Birth-data pipeline marks all Tier 2 fields as `null` at onboarding
- [ ] Confidence scoring explicitly excludes null Tier 2 systems from agreement counts
- [ ] Questionnaire generator reads pending_systems from user profile
- [ ] Reading presentation includes domain coverage disclosure ("Personality: 5/9 systems active, 4 pending questionnaire")

## Generalization

Any hybrid deterministic+self-report system should tier explicitly to avoid false confidence from sparse coverage.
