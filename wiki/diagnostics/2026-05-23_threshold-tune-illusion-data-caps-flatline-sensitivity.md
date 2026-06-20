---
title: Threshold-tune illusion when results are capped — flatline sensitivity hides the real problem
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.88
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-23
domain: diagnostics
topic: threshold-tuning
tags: diagnostics, data-analysis, calibration, methodology, debugging
related_entries:
  - methodologies/2026-05-14_healthy-system-gate-trap-empirical-thresholds.md
  - strategy/2026-05-21_vendor-selection-calibration-uncertainty-dominance.md
---

# Threshold-Tune Illusion When Results Are Capped — Flatline Sensitivity Hides the Real Problem

## Problem

When data has a hard cap (e.g., `LIMIT 100` on a query, `num=30` on an API page-size), threshold-tuning analyses become misleading. Multiple distinct ranges of threshold produce identical flag counts because the underlying data clusters at the cap. The analyst believes the threshold is "calibrated" when really the threshold is *irrelevant* — the cap is doing all the work.

The diagnostic shape: monotonic threshold sensitivity that flatlines across a wide range is a red flag that the data is capped and the metric isn't measuring what you think it is. The right move when you see this is to look at the **match semantics**, not the threshold values.

## When to Apply

- Any time you're tuning a threshold against count-data from an API or query with a result-cap.
- When threshold sensitivity tables look "flat" across multiple values — investigate before declaring the threshold "robust to small changes."
- During vendor swaps where the result-shape might have changed (e.g., a SERP API that returned ≤10 organic results swapped for one with a `depth=100` parameter).

## When This Does NOT Apply

- When you have access to true counts (e.g., aggregations over a complete corpus you control). Caps only matter when they're imposed by external data sources.
- When the cap is far above the threshold's working range. A cap of 1000 doesn't bias decisions about a threshold of 5.

## Grounding: F9 YouTube Brand Monitor (sem-tools)

F9 monitors third-party YouTube brand mentions. After swapping from Serper to YouTube Data API (`num=YOUTUBE_RESULTS_PER_QUERY=30`), live smoke produced this distribution across 5 brands × 2 topic types each:

| Threshold | Pairs flagged LOW (`count < threshold`) |
|-----------|------------------------------------------|
| 5         | 3/10 |
| 10        | 6/10 |
| 15        | 6/10 |
| 20        | 6/10 |
| 25        | 6/10 |

The flatline between thresholds 10–25 was the diagnostic tell. The raw counts revealed why: 5 of 10 pairs hit exactly 30 — the `num=30` API cap. Anything that returned 30 actually represented N≥30 real matches, and the cap erased the differentiation.

The real problem wasn't the threshold — it was the **match semantics**. YouTube native search OR-matches across title + description + tags, so quoted-brand queries returned generic topical videos that merely mentioned the brand in passing. The fix was a brand-in-title post-filter; threshold-of-5 then behaved correctly (10/10 pairs flagged LOW, which is true: all 5 tracked restaurants have minimal *dedicated* YouTube presence).

If we had pattern-matched on "raise threshold from 5 to 10 and ship," we would have shipped a worse detector. The flatline-after-10 pattern forced investigation into the underlying semantics.

## Diagnostic Checklist

When tuning a threshold against data from a capped source:

1. **Plot the raw distribution before plotting threshold sensitivity.** Look for spikes at the cap value.
2. **Compute the fraction of observations at the cap.** If >20%, the cap is biasing your analysis.
3. **Walk the threshold from low to high.** If sensitivity flatlines across a wide range, suspect a cap rather than a robust threshold.
4. **Investigate the underlying matching/filtering logic.** The fix is usually upstream of the threshold.

## Anti-Patterns

- **"Threshold of 15 vs 25 makes no difference, so 15 is robust."** → It's not robust, the data is censored.
- **Raising threshold to hit the desired flag rate** without investigating why low thresholds were too permissive in the first place.
- **Treating "capped at N, so the true count must be at least N" as definite finding** — it could mean ≥N, but the distribution at the cap tells you nothing about which observations are 30 vs which are 300.

## Relationship to Related Patterns

This diagnostic complements two other threshold-related issues:

- **Healthy-system gate trap:** A threshold can fail to fire because the system is too healthy (no failure data accumulates). Flatline cap-induced censorship is the opposite: the threshold always fires (or never fires) because the data is artificially truncated.
- **Vendor calibration dominance:** When choosing between vendors, calibration uncertainty dominates measurement uncertainty. But once a vendor is chosen, flatline sensitivity is a signal that the vendor's cap is the constraint — fix upstream (match logic, post-filter), not in the threshold.

## Source Context

Discovered during F9 YouTube monitor live smoke testing (sem-tools-f10.2-batch-and-vendor-eviction). The user observed identical flag counts across thresholds 10–25 in a sensitivity table and asked why the threshold seemed "robust." Investigation revealed the `num=30` cap was clustering observations; post-filter fix (brand-in-title) restored differentiation and validated threshold-of-5 was appropriate for the actual (filtered) distribution.
