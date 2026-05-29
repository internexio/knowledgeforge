---
title: GSC Sitemap report indexed-count is unreliable — use URL Inspection API for ground truth
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.88
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-05-25
domain: debugging
topic: data-validation
tags: [api, quality-gate, empirical]
related_entries:
  - diagnostics/2026-05-23_live-smoke-as-verification-gate-mocks-pass-prod-breaks.md
---

# GSC Sitemap report `indexed=0` is unreliable — use URL Inspection API for ground truth

## Problem

Google Search Console's Sitemap report exposes per-sitemap `contents[]` showing "submitted" and "indexed" counts via the API (`webmasters.sitemaps.get(siteUrl, feedpath)`). These counts are aggregated/stale and can show `indexed=0` even when the underlying URLs are actually indexed and serving in Google search.

Treating the Sitemap report's `indexed` count as authoritative leads to wild-goose-chase investigations: "why are zero pages indexed?" when the real answer is "they are indexed; the report just hasn't caught up."

## When to apply

- Any time GSC's Sitemap report shows `indexed < submitted` and you're about to investigate URL-level indexability.
- Before recommending fixes to noindex tags, robots.txt, canonicals, or schema markup based on the Sitemap count.
- During SEO health audits where the Sitemap report's coverage is one of many signals.

## When NOT to apply

- When you have already confirmed via URL Inspection that pages are NOT indexed — at that point the Sitemap count is consistent with reality.
- When the sitemap is genuinely new (<7 days submitted) and Google hasn't had time to process it.

## Ground truth alternative

`urlInspection.index.inspect(body={"inspectionUrl": url, "siteUrl": site, "languageCode": "en-US"})` returns the real per-URL indexing state. Key fields:

- `verdict`: PASS / PARTIAL / FAIL / NEUTRAL
- `coverageState`: human-readable ("Submitted and indexed", "Excluded by noindex tag", etc.)
- `robotsTxtState`: ALLOWED / DISALLOWED / DISALLOWED_VIA_ROBOTS_PROTOCOL_HEADER
- `indexingState`: INDEXING_ALLOWED / BLOCKED_BY_META_TAG / ...
- `pageFetchState`: SUCCESSFUL / SOFT_404 / ACCESS_DENIED / ...
- `crawledAs`: MOBILE / DESKTOP
- `lastCrawlTime`: ISO timestamp
- `googleCanonical` / `userCanonical`: canonical mismatch detection

This API is real-time and authoritative. When it disagrees with the Sitemap report, trust URL Inspection.

## Grounding (sem-tools session 2026-05-25)

User report: "lacabar.com submitted 5 URLs, indexed 0; lacacafe.com submitted 4, indexed 0" — surfaced via `webmasters.sitemaps.get` showing `contents[].indexed = 0` for both restaurant sites. Triggered a 30-min indexability investigation: page fetches, robots.txt check, canonical inspection, meta-tag check. All looked fine. URL Inspection API call settled it:

```
inspecting: https://lacabar.com/menu
  verdict:        PASS
  coverageState:  Submitted and indexed
  robotsTxtState: ALLOWED
  indexingState:  INDEXING_ALLOWED
  pageFetchState: SUCCESSFUL
  lastCrawlTime:  2026-05-25T04:29:33
```

Pages were indexed. The Sitemap report's `indexed=0` was stale/buggy. The 30 minutes of investigation found one unrelated cleanup item (a robots.txt 404 served with valid content — also harmless per URL Inspection's `robotsTxtState: ALLOWED`), but no real indexing problem.

## Anti-patterns

- Treating Sitemap report `indexed` count as a real-time metric for indexability decisions.
- Filing remediation work (noindex audits, canonical fixes, sitemap re-submissions) before checking URL Inspection.
- Comparing Sitemap submitted vs indexed counts and assuming the delta represents un-indexed pages.

## Connection to broader pattern

This is a specific case of the more general principle filed in `diagnostics/2026-05-23_live-smoke-as-verification-gate-mocks-pass-prod-breaks.md`: **trust live diagnostics over aggregated/derived reports**. Sitemap report is aggregated; URL Inspection is live.

## Source Context

Discovered during sem-tools session 2026-05-25 while investigating indexability status for lacabar.com and lacacafe.com restaurant sites. GSC Sitemap report showed zero indexed pages despite successful site fetches. URL Inspection API revealed all pages were indexed and serving — the report lag was the only issue.
