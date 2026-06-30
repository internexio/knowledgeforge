---
title: Vendor swap implies semantics-recalibration audit — "same thing" rarely is
source_mode: strategist+builder
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-23
tags: vendors,integration,methodology,calibration,migrations
related_entries:
  - wiki/methodologies/2026-05-21_saas-migration-pre-cancel-checklist-silent-failure-config-pointer-risk.md
  - wiki/strategy/2026-05-21_vendor-selection-calibration-uncertainty-dominance.md
  - wiki/diagnostics/2026-05-21_server-side-state-outlives-client-fixes-saas-wrappers.md
  - wiki/methodologies/2026-05-20_primary-source-vendor-guidance-reanchor.md
domain: methodologies
topic: trade-off-analysis
---

# Vendor swap implies semantics-recalibration audit — "same thing" rarely is

## Problem

When swapping vendors that nominally provide "the same thing" (e.g., SERP search APIs, video search APIs, geocoders, sentiment classifiers, embedding models), downstream calibrations of thresholds, scoring weights, and confidence cutoffs **do not carry over**. Each vendor has slightly different:

- Query semantics (exact-match vs. loose-match; fielded vs. across-all-fields; tokenization)
- Result-shape (count caps, field availability, ranking ordering, latency)
- Failure modes (empty result vs. error code; rate-limit semantics)
- Auth/quota model (per-key vs. per-IP; per-call vs. per-result-row)

A swap that "looks like" a drop-in (the response object has the same keys; the docstring says "search returns results") will silently break thresholds calibrated against the old vendor's semantics.

## When to Apply

Apply this audit whenever a feature's primary external dependency changes:

- SERP vendor swap (Serper → DataForSEO, Serper → native API, etc.)
- LLM swap (GPT-3.5 → Claude, OpenAI → Gemini, etc.)
- Geocoder swap (Google Maps → Mapbox, open-source → commercial, etc.)
- Wrapper-to-native migration (e.g., scraper-based Reddit search → PRAW native search)
- Paid vendor swap (premium tier → free tier; paid service → self-hosted)
- Any commit message containing "swap" + a vendor name → trigger a follow-up bead for semantics audit

## When NOT to Apply

- Trivial library upgrades within the same vendor (e.g., httpx 0.26 → 0.27)
- Vendor sub-product swaps where the underlying engine is identical (e.g., the same provider's "basic" vs. "premium" tier — usually just quota differs, not semantics)
- Shadow-mode rollouts where the new vendor has already run in parallel for a validation window (semantics divergence would have shown up)

## Concrete Examples (sem-tools session 2026-05-23)

### Example 1: Serper → PRAW Native Search (F10.2b)

**Old:** Serper `"brand" site:reddit.com` returned Google-SERP-indexed Reddit threads. Match semantics: Google's quoted-brand exact-match.

**New:** PRAW `subreddit("all").search(brand, sort='new', time_filter='week')` returns Reddit's native search results. Match semantics: Reddit's first-party search ranking (different ranking model, different recall).

**Behavior change:** Native search hits Reddit's own corpus directly, no Google indexing latency, but returns submissions where the brand appears in title OR body OR (rarely) tags. For F10.2b's downstream comment-cluster analysis, this didn't break anything — the downstream filter was on commenters, not submission discovery — but it would have broken a "count threads mentioning brand" detector calibrated against Google SERP.

### Example 2: Serper → DataForSEO SERP (F10.2a)

**Old:** Serper organic results with `link` field.

**New:** DataForSEO `/serp/google/organic/live/regular` items with `url` field (renamed) and a different status_code-to-error mapping. Empty-result responses come back with a non-20000 status code that *looks* like a failure but isn't.

**Required fix:** Thin adapter to translate field names. Less obvious: DataForSEO blocks all API calls unless the caller's IP is in the user-side whitelist — a quiet auth model that surfaces only when you make the first live call.

### Example 3: Serper → YouTube Data API Direct (F9)

**Old:** Serper `site:youtube.com "brand" topic` returned Google-SERP-indexed YouTube pages.

**New:** YouTube Data API `search.list(q='"brand" topic', type='video')` returns YouTube's native search results.

**Semantics shift that broke the downstream threshold:** YouTube native search OR-matches across title + description + tags, even with quoted terms. Google SERP `site:youtube.com "brand"` only indexed pages where the brand was prominent (typically title). So `count_third_party_mentions` started returning 30-result-capped responses for brands that previously returned 0-2 — same query intent, vastly different recall.

**Required follow-up:** Brand-in-title post-filter (sem-tools-pwl). Threshold-of-5 was correct against the new vendor *after* the semantics were realigned.

## Semantics-Recalibration Checklist

Run this BEFORE declaring the swap "shipped":

### 1. Re-read the old vendor's calibration sources

Where did the thresholds, weights, or scoring constants come from? What did they assume about the old vendor's semantics?

Examples:
- "THRESHOLD=5 — came from tuning against Serper's Google SERP ranking"
- "WEIGHT=0.8 — Ahrefs study on YouTube prominence"
- "CONFIDENCE_CUTOFF=0.6 — calibrated against GPT-3.5 accuracy floor"

### 2. Live-smoke the new vendor against the same inputs

Compare not just "does it return data" but "does it return *the same kind of* data."

- **Query semantics:** If the feature involves quoted-brand searches, verify the new vendor honors quotes the way the old vendor did. If the feature involves field-specific filtering, verify the new vendor offers equivalent filters.
- **Result shape:** Is the count capped? Are there fields present/absent? Does ranking order matter?
- **Failure modes:** Does "no results" come back as a 200 OK with empty array, or as a 404? Does rate-limiting surface as error or silent throttle?

### 3. Audit downstream constants

Any threshold, weight, or scoring constant calibrated against the old vendor's output is presumed-broken until proven otherwise.

Run grep/search on:
- Python: numeric constants in conditional branches (if count < 5, if score > 0.7, etc.)
- SQL: numeric thresholds in WHERE clauses (WHERE rank <= 10, WHERE confidence >= 0.6)
- Config files/env vars: any numeric setting tied to the old vendor

### 4. Document the calibration source in the constant's comment

Future you (and future maintainers) should know whether `THRESHOLD=5` came from:
- "Ahrefs research on Google SERP" (vendor-specific, needs audit)
- "Empirical tuning against Serper; do not reuse if vendor changes" (explicit)
- "Industry consensus, vendor-agnostic" (can carry over)

Example good comment:
```python
# Threshold calibrated against Serper SERP ranking. When vendor changed to 
# DataForSEO, this was re-tuned on 2026-05-23 to account for different 
# result capping. Do not assume this carries to future vendors.
RESULT_COUNT_THRESHOLD = 5
```

### 5. (If threshold-dependent) Run comparative smoke tests

- Feed the new vendor the same test inputs (brand queries, locale combos, topic slices)
- Capture counts, scores, or distributions
- Compare to baseline from the old vendor
- Flag any divergence > 10% as a recalibration candidate

Example: If old vendor returned avg. 3 results per query and new vendor returns avg. 7, then thresholds tuned for "< 5 means weak signal" are now inverted — you'll flag strong signals as weak.

## Anti-Patterns

- **"Same shape response, must be drop-in."** Field renames, status code differences, and matching semantics are not visible in the response shape.
- **Trusting that "vendor B is more accurate" without recalibrating thresholds.** The thresholds were tuned for vendor A's accuracy floor. Vendor B's higher accuracy will trigger more false positives under the old thresholds.
- **Shipping the swap, watching tests pass, declaring victory.** The semantics breakage only shows under live data with real-world distributions.
- **Treating vendor-swap commits as low-risk because they don't introduce "new logic."** They introduce *new behavior in old logic*.

## When This Applies

- Any time a feature's primary external dependency changes
- When swapping a paid vendor for a free one, or vice versa (cost model often correlates with semantics differences)
- When swapping a wrapper-API for the underlying platform's native API
- After ANY commit message that contains "swap" + a vendor name (add a follow-up bead for this audit)

## When This Does NOT Apply

- Trivial library upgrades within the same vendor
- Vendor sub-product swaps where the underlying engine is identical
- Already-validated shadow-mode rollouts

## Source Context

This framework emerged during sem-tools session 2026-05-23 (batch-and-vendor-eviction). Three vendor swaps in one session exposed three different semantics drift patterns:

1. **F10.2b (Serper → PRAW):** Query semantics divergence (exact-match vs. OR-match)
2. **F10.2a (Serper → DataForSEO):** Field rename + status code semantics (benign from downstream view; auth model silent)
3. **F9 (Serper → YouTube Data API):** Recall divergence that broke downstream thresholds (30 results when expecting <5)

Only the third example required threshold recalibration in live deployment. The first two exposed the broader risk: even when thresholds don't break, the audit itself is required to confirm it.

## Related Entries

- **SaaS migration pre-cancel checklist** — covers data-export and config-pointer risks; this entry covers semantics validation
- **Vendor selection — calibration uncertainty dominates** — how to choose vendors upfront; this entry is the follow-up when the choice has been made and execution reveals semantics drift
- **Primary-source vendor guidance reanchor** — when to reanchor tooling on vendor primary sources; semantics recalibration is an upstream step that may trigger this
