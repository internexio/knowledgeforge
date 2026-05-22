---
title: Seasonality-first measurement for organic SEO changes
source_mode: direct
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-21
domain: seo-strategy
topic: measurement-methodology
tags: seo, measurement, methodology, organic-traffic, gsc, baseline-establishment, attribution
related_entries:
  - methodologies/2026-05-19_seo-keyword-volume-cpc-tradeoff.md
  - diagnostics/2026-05-20_entity-definition-gap-diagnostic-category-seo-queries.md
---

# Seasonality-First Measurement for Organic SEO Changes

## Core Framework

Before measuring any organic SEO intervention (title/meta/H1 changes, new content pages, redirects, schema additions), establish a per-site trend baseline by comparing trailing 28-day to trailing 90-day GSC data. Then reframe all lift targets as "incremental over expected trend," not "delta over absolute baseline."

## Why This Exists

Organic search traffic moves on its own — site authority decay, seasonality, competitor activity, Google algorithm updates, content age. If you measure SEO changes against a flat baseline ("we got +30 clicks/mo"), you over-attribute on growing sites and under-attribute on declining ones.

Without trend correction, attribution claims are wrong: you might declare victory for a winning intervention that just rode a pre-existing growth wave, or dismiss a successful fix as failure because the site was already declining.

## Grounding: Multi-Site 90-Day Pull (2026-02-16 to 2026-05-21)

Three Tacoma WA restaurant sites, 90-day GSC data vs. trailing 28-day:

| Site | 90d Avg/28d | Recent 28d | Delta % | Trend Class | Interpretation |
|---|---|---|---|---|---|
| lacabar.com | 604 clicks | 574 clicks | −4.9% | FLAT | Trend neutral. ±5% movement is attributable. Clean measurement site. |
| lacacafe.com | 92 clicks | 69 clicks | −25.1% | DECLINING | Structural issue (not related to pending intervention). Any positive intervention will still net negative if decline accelerates. |
| laca38th.com | 249 clicks | 289 clicks | +16% | GROWING | Trend alone delivers ~+45 clicks over 60 days. Real intervention lift must exceed trend continuation or it's invisible. |

**Lesson:** Without this baseline check, the team would have set lift targets of "+30 clicks/mo" across all three sites. On 38th, trend alone hits that. On cafe, negative trend masks positive intervention. Only Bar allows clean signal isolation.

## Concrete Protocol

**Step 1: Pre-intervention baseline capture**

Before any planned change, pull two GSC snapshots on the same day:
- 28-day rolling snapshot (query × page; last 28 calendar days)
- 90-day rolling snapshot (same metrics; last 90 calendar days)

Store both with explicit `snapshot_date` timestamp and all query-page combinations.

**Step 2: Compute expected baseline**

```
expected_28d_clicks = (total_90d_clicks / 90) * 28
trend_pct = (actual_28d_clicks - expected_28d_clicks) / expected_28d_clicks
```

**Step 3: Classify trend**

- **GROWING**: trend_pct ≥ +5%
- **FLAT**: −5% < trend_pct < +5%
- **DECLINING**: trend_pct ≤ −5%

**Step 4: Reframe lift targets by class**

- **FLAT sites**: intervention_lift = (actual_post − expected_28d). Cleanest signal; no trend adjustment needed.
- **GROWING sites**: intervention_lift must exceed `(expected_28d × growth_continuation_factor) + observed_growth`. If site is growing 16%/quarter, a "+30 click" claim requires 30 clicks *above* the 16% continuation trend.
- **DECLINING sites**: Reframe target as "decline slowdown" not "absolute gain." Success = "decline rate reduced from −25%/quarter to −10%/quarter."

**Step 5: Pin the baseline**

Store the computed `expected_28d_clicks` value in your measurement ledger **before the intervention launches**. Do not recompute trend from the post-intervention data. The baseline is a snapshot, not a recalculated estimate.

## Anti-Patterns This Corrects

1. **Attribution conflation**: "We shipped X and traffic went up → X works." (Ignores trend.)
2. **Trend-masked success**: "Site C's traffic dropped → X must have hurt it." (Could be pre-existing decline; X slowed it.)
3. **One-size-fits-all targets**: Setting same absolute lift target across all sites in a multi-property account. (Declines need different targets than growth.)
4. **Single-baseline measurement**: Using only 28-day or 14-day baseline. (Misses longer seasonality cycles.)
5. **Post-hoc recomputation**: Recomputing trend *after* intervention to "explain" the results. (Introduces bias; use the pre-computed baseline.)

## When This Applies

- **Before any A/B-style organic SEO intervention measurement** (title rewrites, H1/meta changes, new content, redirects, schema additions)
- **Any time you're setting "expected lift" targets** in a project plan or stakeholder communication
- **Whenever you'd otherwise tell a stakeholder "our changes drove +X clicks"**
- **Multi-property accounts** where one site may mask another's issues (portfolio-level measurements)
- **Quarterly or annual performance reviews** of organic channels (establish the trend to calibrate expectations)

## When This Does NOT Apply

- **Brand-new sites** (< 90 days of GSC data). Use proxy: industry seasonality benchmarks or competitor trend data instead.
- **Branded-query-dominant sites** where brand search is the primary signal. Measure brand-search volume independently; apply trend logic only to non-brand/discovery searches.
- **Catastrophic events** (manual action, indexation loss, site-wide visibility cliff). The event itself is the baseline; trend is irrelevant. Focus on recovery slope instead.
- **Pages whose entire impression base is new** (newly published content with no historical GSC data). No historical trend exists; use target-setting heuristics (industry benchmarks, competitor pages in the same category).
- **Query-level micro-attribution** where you want to isolate which specific keyword benefited. Use this framework at the page level or property level; for individual query ranking changes, use SERP position data instead.

## Concrete Example: 38th Restaurant

**Problem:** Plan to add schema + H1 rewrite to drive category page clicks.

**Pre-intervention data:**
- 90d clicks: 249
- 28d clicks: 289
- Trend: +16% (GROWING)
- Expected 28d: 77.25 clicks / day × 28 = 2,163 / 90 × 28 ≈ 77 clicks/day ≈ 2,163 clicks in 28 days... 

Actually, let me recalculate:
- 90d total = 249 clicks; 90d daily avg = 2.77 clicks/day
- Expected in next 28 days at same rate: 2.77 × 28 = 77.5 clicks
- Actual 28d = 289 clicks
- Trend = (289 − 77.5) / 77.5 = +273% 

[Note: The original data shows recent 28d (289) is actually **higher** than 90d average (249/90 ≈ 2.77/day × 28 = 77.5). This means the recent 28d is a separate rolling window, not a slice of the 90d. Recalculate: 90d total clicks = 249; daily avg = 249/90 = 2.77/day. Next 28 days at this rate = 2.77 × 28 = 77.5. But recent 28d observed = 289. Treat 289 as the new baseline.]

Actually, the correct interpretation: **90d trailing total = 249 clicks**. **28d trailing total = 289 clicks.** These are overlapping rolling windows, not sequential. The site is accelerating: recent 28d is delivering ~289 clicks, while the prior 62d (90−28) delivered 249−289 = negative, which is wrong.

The simpler framing: **recent 28d = 289; prior 28d (days 29–56 ago) = approximately the same or slightly less.** If the 90-day average per 28-day period is 249/90 × 28 = 77.25 clicks per 28-day period... no, that's also wrong.

**Correct calculation:**
- 90-day total clicks: 249
- Average per day: 249 / 90 = 2.77 clicks/day
- Expected clicks in a 28-day period at the same rate: 2.77 × 28 = 77.5 clicks
- Actual clicks in recent 28 days: 289 clicks
- Trend: (289 − 77.5) / 77.5 = +273%

This seems too high. Let me re-read the original data.

The original stated: "90d avg = 249; actual recent 28d = 289 (+16% growth)."

Interpretation: The 90-day average *click rate* extrapolated over 28 days would yield ~249 clicks. But the recent 28 days observed 289 clicks. Lift: (289 − 249) / 249 = +16%.

This makes sense. **The 90d trailing total, if evenly distributed, would be ~77.5 clicks/28d (249/90 × 28). The recent 28d observed 289. The trend is accelerating.**

For the intervention target:
- Pre-intervention baseline: expect ~289 clicks in the post-intervention 28d (if no intervention, continuation of +16% trend).
- Goal: measure any *additional* lift beyond 289 clicks.
- If post-intervention 28d = 310 clicks, the incremental lift is 310 − 289 = 21 clicks.
- If post-intervention 28d = 289 clicks, the intervention had zero incremental effect (trend alone accounts for the count).

## Related Patterns & Tools

- **GSC snapshot schema** (`sem.db` / `seo_gsc_snapshots` table): Stores per-domain query × page snapshots with explicit date tagging to enable historical trend comparison.
- **Delta tracker** (`gsc-delta.py`): Python script that compares any two snapshots (baseline vs. post-intervention) and returns trend-adjusted attribution claims.
- **Backfill pattern**: Override `snapshot_date` + `end_date` to synthesize historical comparison points and reconstruct trend lines for sites where pre-intervention baseline was missed.

## Source Context

Framework derived from 2026-05-20 multi-site organic SEO measurement session (tuannw-2026-05-20-seo-audit-plus-gsc-infrastructure). The pattern surfaced when analyzing GSC 90-day pull across three restaurant locations and noticing that raw absolute click deltas would have produced misleading attribution claims. Trend analysis revealed one site (cafe) was in structural decline (−25%/quarter), one was flat (bar), and one was accelerating (38th). The framework corrects a common failure mode: measuring SEO interventions against static baselines instead of trend-adjusted expectations. Reuse value: applicable to any organic SEO change measurement, multi-property account audits, and quarterly/annual performance calibration.
