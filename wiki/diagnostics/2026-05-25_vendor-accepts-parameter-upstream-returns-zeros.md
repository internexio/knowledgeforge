---
title: Vendor accepts parameter, upstream returns zeros — proxy-API data-availability vs. capability gap
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-25
tags: api-integration,vendor-evaluation,diagnostic-pattern,proxy-services,data-availability,seo
related_entries:
  - wiki/methodologies/2026-05-23_vendor-swap-semantics-recalibration-audit.md
  - wiki/methodologies/2026-05-21_keyword-data-triangulation-datasources.md
  - wiki/strategy/2026-05-21_vendor-selection-calibration-uncertainty-dominance.md
domain: diagnostics
topic: data-quality
---

# Vendor accepts parameter, upstream returns zeros — proxy-API data-availability vs. capability gap

## Pattern: The Silent Data-Availability Mask

When evaluating a vendor API that wraps or proxies a third-party data source (e.g., DataForSEO wrapping Google Ads Keyword Planner, an SEO tool wrapping Search Console, an enrichment tool wrapping LinkedIn), **API acceptance of a parameter is NOT evidence that the upstream service supports it at that granularity**. The vendor may:

- Accept the request (HTTP 200, status_code 20000 "Ok")
- Bill you for it (cost meter increments normally)
- Log it as a successful task (no error flagged in response metadata)
- Return structurally valid responses with zero values

While the **upstream service silently returns zeros, nulls, or aggregated-up data** because the requested granularity isn't actually available.

## Concrete Grounding: 2026-05-25 DataForSEO ZIP-Level Volume Probe

**Context:** Restaurant SEO requires per-ZIP keyword volume data for hyperlocal targeting. DataForSEO documents ZIP-coded location strings (e.g., `'98405,Washington,United States'`) as valid `location_name` for `google_ads/search_volume/live`. The `keywords_data/google_ads/locations` endpoint confirms 31,847 US ZIPs are valid `Postal Code` location entries with proper `location_code` integers.

**Probe:** Sent batch of 91 restaurant keywords at `98405,Washington,United States`:

**Response:**
- HTTP 200, status_code 20000 ("Ok.")
- 91 rows returned, one per keyword
- But every row: `search_volume=0`, `cpc=null`, `competition=null`
- DataForSEO billing: normal (~$0.10/1000 queries)

**Multi-level cross-check on same query — "restaurants near me":**

| Location level | Volume | CPC | Competition |
|---|---|---|---|
| United States (national) | 101,000,000 | $2.50 | 1.0 |
| Washington (state) | 2,740,000 | $1.80 | 0.85 |
| Tacoma, Washington (city) | 110,000 | $0.65 | 0.40 |
| 98405, Washington (ZIP) | **0** | **null** | **null** |

**Root cause:** Google Keyword Planner aggregates volume at **DMA/metro level and applies a k-anonymity privacy threshold**. It returns zero rather than exposing real volume at finer geographic granularity. This is a property of Google's upstream, not DataForSEO's wrapper. DataForSEO accurately forwards what Google returns; Google returns nothing actionable below DMA.

**Adjacent endpoints exhibited similar masking:**

- `clickstream_data/dataforseo_search_volume`: rejects `location_name` below country level (HTTP 200 / status 40501 "Invalid Field")
- `bing/search_volume`: accepts city-level (returns real data) but rejects ZIP entirely

## Diagnostic Protocol — Apply Before Assuming a Vendor Capability

When evaluating a vendor for a specific granularity (geographic, temporal, demographic, result-count ceiling, etc.):

### 1. Verify the API surface accepts the granularity

Does the request shape accept the granularity you need?

- Field enumeration: does the `location_enum` include "Postal Code"? Does the `time_bucket_enum` include "hourly"?
- Documentation: does the vendor claim to support this granularity?
- Type validation: does the API schema accept it without 400-level rejection?

### 2. Test with a known-volume query at multiple granularities

Pick a query that returns real data at coarse granularity. Run the same query at progressively finer granularities.

**Red flag:** Query returns real data at broad level (national: 100K volume) but returns 0 at your target granularity (ZIP: 0 volume). The vendor is forwarding upstream's privacy floor — not surfacing a finer signal.

### 3. Compare against the broadest-level result for the same query

If broad-level returns real data and your target granularity returns null/zero:

- **All other vendors at your granularity also return zero?** → upstream limitation (vendor-agnostic)
- **Other vendors return real data at your granularity?** → this vendor's upstream is more restrictive
- **One vendor accepts the granularity, others reject it outright?** → the accepting vendor may be masking silently; the rejecting vendors are at least honest about the limitation

### 4. Check whether the vendor charges you anyway

If the API accepts the request, returns 200 OK, and *bills you*, that's the business signal that the vendor doesn't know either — they're a thin proxy with no awareness of upstream capability boundaries.

### 5. Verify with a second query at different characteristics

Volume queries can mask. Test with:

- A different search domain (if testing geographic granularity, test multiple countries/regions)
- Different query characteristics (head-term vs. long-tail; branded vs. unbranded; seasonal vs. evergreen)

If ALL queries return zero at your target granularity, you've found a hard boundary. If *some* return data, the boundary is noisier (time-based k-anonymity thresholds, query-class-dependent filtering).

## When This Pattern Applies

- Search-volume vendors wrapping Google Ads (DataForSEO, Semrush, Ahrefs, SpyFu)
  - All subject to the same DMA-floor for ZIP/postal-code-level queries
  - No workaround except upward aggregation or regional sampling

- Search Console proxies (GA4, third-party wrappers)
  - GSC's privacy-threshold filtering suppresses impressions/clicks below ~10/period
  - Proxies that show them as "0" rather than "<threshold" are misleading
  - Query at different granularities (device, query-type, page) to find the threshold

- LinkedIn / B2B enrichment APIs
  - Vendor may accept fine-grained company or person filters that upstream (LinkedIn) hasn't surfaced
  - E.g., filtering by "VP-level at Series B startups in NYC" may be parsed but return empty because LinkedIn doesn't expose that combo

- Geographic targeting APIs that accept ZIP but upstream uses metro/DMA
- Time-bucket APIs (daily/hourly) that accept the bucket but upstream aggregates weekly/monthly
- Any result-count API with hidden caps (vendor documents "returns up to 100" but silently starts returning fewer results at finer granularity without flagging the cap)

## When This Does NOT Apply

- First-party APIs where the vendor IS the source of truth (e.g., calling Google Ads API directly — granularity supported is whatever Google's own API surfaces, no proxy layer)
- Vendors who explicitly document the granularity gap in their public docs (some do — though not in this case)
- Internal APIs where you control both the proxy and the upstream (you'd catch this during API review)

## Cost and Impact

Each empty-but-billed call to a wrapper API is wasted spend. For high-frequency tracking (e.g., daily rank-check at ZIP × hundreds of keywords):

- 500 keywords × 31,847 ZIPs × $0.10/1k = $1,592/refresh cycle
- If all return zeros, you've spent $1,592 on a binary "no data" signal that costs $0 to know upfront

Build the multi-level probe into the vendor-evaluation checklist **before committing to a refresh cadence**.

## Mitigation: Triangulation Fallback

When your target vendor masks data at your target granularity:

1. **Escalate to next-coarser granularity** (ZIP → city, city → state, state → national)
2. **Cross-check with alternative vendors** (DataForSEO → SEMrush Phrase This, which may return data at different granularities)
3. **Use platform-native tools** (Google Ads forecasting for geographic targeting, even if volume is capped)
4. **Instrument your own data** (if you have first-party access, e.g., Google Ads account, use API directly rather than proxy)

For restaurant SEO, the finding (2026-05-25) was: **DMA is the minimum granularity for any Google Keyword Planner wrapper**. Recommendation pivoted to city-level keywords + on-page location-specific content + Google Local Services Ads (which operate on ZIP-coded coverage, not keyword volume).

## Source Context

Grounded in sem-tools 2026-05-25 session (restaurant-zip-volume-pivot). Initial hypothesis: DataForSEO accepts ZIP-level queries; therefore, Google Keyword Planner supports ZIP-level volume. Investigation revealed Google returns zero at ZIP level due to DMA aggregation + k-anonymity threshold. This is now a default assumption for any vendor wrapping Google KP.

Related beads:
- sem-tools-3mc (decided to use DataForSEO ZIP volume — closed; premise wrong)
- sem-tools-4kp (closed 2026-05-25 with vendor-blocker reason after this finding)
- sem-tools-kcr (routing kept; ZIP→DataForSEO call now returns zeros but doesn't error)

Related artifact: feedback memory `restaurant-zip-volume-tracking.md` (updated 2026-05-25 with vendor-reality correction).

## Anti-Patterns This Corrects

- "The API accepts it, so it must be supported." → parameter acceptance ≠ data availability
- "We get a 200 response, so the data is good." → zero is a valid response value
- "The vendor bills normally, so they caught the issue." → proxy APIs bill regardless of upstream data quality
- "One vendor masks it, but we can find another." → when the upstream (Google) is the limitation, all wrappers are equally masked
