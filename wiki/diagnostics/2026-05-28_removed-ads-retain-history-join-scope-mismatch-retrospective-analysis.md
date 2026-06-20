---
title: Retrospective ad-performance analysis must include removed ads and verify score↔performance linkage before correlating
source_mode: builder
novelty_type: reusable_diagnostic
grounding_score: 0.8
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-05-28
domain: data-analysis
topic: retrospective-analysis
tags: google-ads, gaql, data-pipeline, retrospective-analysis, correlation, data-integrity, diagnostic-pattern
related_entries:
  - diagnostics/2026-05-25_vendor-accepts-parameter-upstream-returns-zeros.md
  - diagnostics/2026-05-23_threshold-tune-illusion-data-caps-flatline-sensitivity.md
  - methodologies/2026-05-28_feasibility-gate-validation-thesis-defer-untestable.md
  - methodologies/2026-05-27_read-ground-truth-not-surface-signals-universal-antipattern.md
---

# Retrospective Ad-Performance Analysis Must Include Removed Ads and Verify Score↔Performance Linkage Before Correlating

## Two Linked Data Gotchas

A retrospective correlation study attempting to validate whether ad-scoring correlates with historical Google Ads performance nearly produced a false "no analyzable data" conclusion. Two distinct data-integrity failures, when combined, silently collapsed the analysis sample from 26 analyzable ads down to an inconclusive subset.

### Gotcha 1: Removed Ads Hold Most of the History

**The Problem:** The default ad-pull filters enabled ads only (`WHERE ad_group_ad.status != 'REMOVED'` in GAQL) / (`include_removed=False` in the Python client). Removed and paused ads remain invisible in the enabled-only pull.

**But the historical performance tables do NOT filter by status.** Impressions, clicks, and conversions accumulated by removed ads are still queryable and report accurately. So the set of ads you CAN score (the currently-enabled set) is NOT the same set that accumulated the traffic.

**Concrete Grounding:** An enabled-only pull yielded only 2 ads clearing the ≥100-impression floor, rendering the sample size too small to support any correlation analysis. A second pull with `include_removed=True` recovered high-impression ads that had been removed, expanding the analyzable sample from 2 → 26 ads. The single top ad alone carried ~829 impressions and had been a removed ad, representing the majority of historical performance data.

**The Fix:** For any RETROSPECTIVE analysis (as opposed to "what's live now" dashboards), pull ads WITH removed=True. The live-operational set is a subset; the historical set is what you need for correlation.

### Gotcha 2: Verify the Score↔Performance JOIN Before Correlating

**The Problem:** The scored-ad set and the performance-row set were misaligned even after including removed ads. Scopes differed:
- Ad pull: enabled ads + removed ads within a specific date range (22 ads)
- Performance pull: all performance rows available (broader scope, possibly spanning different date ranges or account boundaries)
- Score dataset: subset of 14 ads with any performance row + subset of ~2 above the impression floor

A naive "join ads → performance → scores and correlate" silently collapsed to a tiny n, the join surface not reporting the effective sample size until after the analysis ran.

**Concrete Grounding:** After inclusion of removed ads: 22 ads scored, but only 14 had ANY associated performance rows, and only ~2 cleared the impression floor. A count-of-counts revealed the orphan rows: 26 high-impression performance rows had no match in the scored ad table because the performance pull drew from a broader scope than the ad pull.

**The Fix:** Before running correlation, explicitly reconcile the three sets:
- How many ads are in the scored set?
- How many of those ads have ANY performance row?
- How many clear your noise floor (e.g., ≥100 impressions)?
- Report all three before running the analysis so a join/scope mismatch is caught immediately rather than misread as "genuine sparsity."

## Symptom Pattern

When building a retrospective correlation between a derived score (LLM score, quality metric, classifier output) and historical platform performance, you observe:

- **Symptom 1:** "No analyzable data" or "sample size too small for statistical power" despite the platform's historical records showing substantial traffic.
- **Symptom 2:** Reconciliation query shows high-impression performance rows with no corresponding entry in the scored-ad set.

Both symptoms often co-occur because:
1. Removing the "exclude removed ads" filter might increase n by an order of magnitude, unblocking Gotcha 1.
2. Explicitly counting the joined set before correlating catches Gotcha 2 and prevents the correlation from running on orphaned or mismatched rows.

## When This Applies

- Retrospective analysis correlating a derived score against historical performance pulled from an ad platform (Google Ads, Meta, etc.) where entities can be removed/paused but retain historical metrics
- Any join of three+ sets (ads, performance, scores) where pull scopes are controlled independently
- Analyses where the "current state" (enabled ads) differs meaningfully from the "historical state" (all ads that ever accumulated performance)

## When This Does NOT Apply

- Live/current-state dashboards — you WANT enabled-only there; removed ads are irrelevant for "what's running now"
- Analyses where scoring and performance come from the same single extract (single pull scope, single date range) — join scope mismatch is impossible if both tables come from the same source
- Analyses on accounts with negligible churn (removed ads are rare) — the improvement from including removed ads is marginal

## Practical Implementation Checklist

### Step 1: Pull Ads with `include_removed=True` for Retrospective Work

**Python (google-ads client):**
```python
# Instead of:
# query = 'SELECT ad_group_ad.ad.id, ad_group_ad.status FROM ad_group_ad WHERE ad_group_ad.status != "REMOVED"'

# Use:
query = 'SELECT ad_group_ad.ad.id, ad_group_ad.status FROM ad_group_ad'
# Result includes ENABLED, PAUSED, REMOVED, all with historical metrics available
```

### Step 2: Before Correlating, Emit a Reconciliation One-Liner

After joining ads → performance, count:
```python
ads_in_pull = len(scored_ads_set)
ads_with_perf = len(scored_ads_set & performance_rows_set)
ads_above_floor = len([a for a in scored_ads_set & performance_rows_set if perf[a]['impressions'] >= FLOOR])

print(f"Reconciliation: {ads_in_pull} ads | {ads_with_perf} with-perf | {ads_above_floor} above-floor | {ads_above_floor}/{ads_in_pull} = {100*ads_above_floor/ads_in_pull:.1f}%")
# Example output:
# Reconciliation: 22 ads | 14 with-perf | 2 above-floor | 2/22 = 9.1%
```

If the percentage is surprisingly low (e.g., < 50%), halt and investigate:
- Are the performance rows genuinely sparse, or is there a scope mismatch?
- Did the performance pull include a different date range than the ad pull?
- Is the performance table filtering by ad group, campaign, or account scope?

### Step 3: Log Orphan Rows (Optional, But Recommended)

```python
orphan_perf_rows = performance_rows_set - scored_ads_set
if len(orphan_perf_rows) > 0:
    print(f"WARNING: {len(orphan_perf_rows)} performance rows found with no matching scored ad")
    print(f"  Top 3 orphans (by impressions): {sorted(orphan_perf_rows, key=lambda p: perf[p]['impressions'], reverse=True)[:3]}")
```

High orphan count signals a pull-scope mismatch. Investigate before correlating.

## Related Patterns

- **Vendor-accepts-parameter, upstream-returns-zeros** (`diagnostics/2026-05-25...`) — vendor API masks data unavailability at fine granularities; here, the platform's own API masks it via default-filter scopes
- **Feasibility-gate validation thesis** (`methodologies/2026-05-28...`) — power analysis should catch "too small n" before building the harness; this pattern catches the ROOT CAUSE (scope mismatch) of the small n
- **Read ground truth, not surface signals** (`methodologies/2026-05-27...`) — don't infer "no data" from empty result set; query the actual database to discover if the pull scope was wrong

## Source Context

Grounded in cos-on-ads-wedge-validation session (client-project Phase 0b) while building a retrospective correlation analysis to validate whether COS-derived audience scoring improves Google Ads performance. Phase 0b started with only 2 analyzable ads from a naive enabled-only pull, rendering the sample size insufficient for statistical power. Investigation revealed Gotcha 1: removed ads carried the majority of historical impressions but were filtered out by default. After including removed ads, n=26 became feasible. However, post-join reconciliation revealed Gotcha 2: the scored-ad set and performance-row set were misaligned due to independent pull scopes, with high-impression orphan rows indicating a scope boundary that wasn't visible until explicit reconciliation. The pattern emerged from explicitly auditing the join surface before running the correlation, preventing a silent collapse to an inconclusive n and surfacing the root cause (scope mismatch) rather than the symptom (small n).
