---
title: Score calibration methodology for two-model pipelines
source_mode: builder
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-08-04
domain: diagnostics
topic: calibration
tags: empirical, grounding, quality-gate, measurement-logic, adversarial
related_entries:
  - diagnostics/2026-05-24_threshold-vs-empirical-calibration-gap-similarity-systems.md
  - diagnostics/2026-05-31_per-entity-status-classifier-unmeasured-vs-measured-null.md
  - methodologies/2026-05-28_feasibility-gate-validation-thesis-defer-untestable.md
revises: null
superseded_by: null
---

# Score Calibration Methodology for Two-Model Pipelines

## Problem

When a fast/cheap model (Phase 1) and a full framework pipeline (Phase 2) both produce scores on the same 0–100 scale, systematic bias is expected and measurable. Fast models doing surface-level extraction consistently score 10–20 points higher than full-framework analysis on the same content. If users see Phase 1 = 78 and Phase 2 = 54, they feel misled — trust is destroyed even though both scores are technically correct at their respective depth levels.

This entry provides a deterministic calibration protocol to detect, measure, and correct the systematic offset so users perceive consistency despite the inherent methodological gap.

## Calibration Protocol

### 1. Build a calibration corpus

- ~120 content pieces (enough for reliable variance estimates)
- Stratify by content type (6 types × 20 pieces) and quality tier (low/mid/high within each type)
- Include only pieces with documented performance evidence (conversion data, open rates, etc.) — you need ground truth to validate signal quality later
- **No synthetic content** — calibrating against LLM-generated copy trains on its own artifacts and produces illusory alignment

### 2. Run paired analyses

- Pin both model versions before starting; record exact model IDs
- Set temperature = 0 on both phases for the calibration run (removes stochastic variance from the delta signal)
- Run each piece twice (two independent passes); take the mean; flag pieces where two runs differ by >5 points as unstable
- Record: raw score (both phases), dominant frame match (bool), archetype match (bool)

### 3. Compute bias metrics

```
μΔ = mean(P1_raw - P2_raw)        # systematic offset
σΔ = stdev(all deltas)            # consistency of the offset
```

Run segmented analysis: by content type, by P2 score range (5 buckets: 0-39, 40-54, 55-69, 70-84, 85-100), by dominant frame.

### 4. Apply calibration offset

- **Location:** API post-processing layer, NOT the model prompt. Prompt-level adjustment is invisible to future diagnosis and interacts unpredictably with model reasoning.
- **Resolution order** (most specific wins): 
  - type-specific offset (if σΔ_type < 8 and n ≥ 15)
  - → score-range bucket offset
  - → global μΔ fallback
- **Clamp always:** `calibrated = max(0, min(100, raw - offset))`
- **Log separately:** both raw and calibrated scores for audit trail

### 5. Pass/fail thresholds

| Metric | Pass | Fail |
|---|---|---|
| Global μΔ | ≤ ±15 | > ±15 |
| Global σΔ | ≤ 14 | > 14 |
| Frame match rate | ≥ 75% | < 65% |
| Archetype match rate | ≥ 70% | < 60% |
| Pieces with \|Δ\| > 20 | ≤ 10% | > 20% |

If a specific content type has σΔ > 20, suppress the score for that type in Phase 1 output — show "preliminary assessment" label instead. A wrong number is worse than no number.

### 6. Production monitoring

- Log per-analysis: `p1_score_raw`, `p1_score_calibrated`, `p2_score_raw`, `delta`, `frame_match`, `arch_match`
- Rolling 200-pair delta query weekly; alert at |mean delta| > 5, mandatory re-calibration at > 10
- Frame accuracy alert at < 72% on rolling 200
- **Re-calibrate on:** model update, prompt change, new content type, production drift alert, or every 6 months

## UX Communication of the Offset

Consider surfacing: "Preliminary score: 68 (refined by full analysis)" rather than bare "68". This primes the user for a possible Phase 2 difference without suggesting error.

Alternatively, in the UI: "Quick scan estimated 68 · Full analysis: 61" — frames the delta as revelation, not contradiction.

## When This Applies

- Two or more models in sequence that produce the same-scale metric
- Phase 1 is a faster/cheaper proxy for Phase 2's gold standard
- Users see both scores and need to trust they're consistent
- Systematic offset is detectable and stable (σΔ < 14) within content types

## When This Does NOT Apply

- Scores are on different scales (no direct comparison required)
- Only one model/phase in the pipeline
- The two scores intentionally measure different things (no expectation of alignment)
- Offset is erratic across content types (suggests the pipeline methodologies are fundamentally misaligned; fix methodology, not scores)

## Practical Constraints

**Calibration corpus size:** 120 pieces is a floor, not a ceiling. With fewer than 50 pieces per content type, type-specific offsets become unreliable; fall back to global μΔ. With 200+ pieces, segment at finer granularity (7 score buckets instead of 5).

**Temperature pinning:** Turning off randomness during calibration is non-negotiable. Stochastic scoring introduces artificial delta noise that masks or inflates the real offset. Once calibrated, you can relax temperature for production, but the calibration measurement must see zero-temperature baseline.

**Post-processing location:** Prompt-level offsets corrupt the signal for future diagnosis and training data. A negative Phase 1 score that's been bumped upward by prompt engineering looks identical to a legitimately high score to downstream consumers. Always correct after scoring.

## Source Context

Derived from designing Phase 1 (Haiku-based pre-scan) vs Phase 2 (full COS framework) score alignment for the COS analysis tool, August 2026. The full 120-piece calibration protocol, segment analysis formulas, and production monitoring queries were worked out in detail during the cos-progressive-analysis-ux-redesign session. The specific pass/fail thresholds and re-calibration cadence reflect empirical experience with two-model scoring pipelines in measurement-sensitive domains.
