---
title: GSC impression split (URL-A down / URL-B up) with 301 in place = consolidation in progress, not a broken redirect
source_mode: debugger
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.72
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-11
domain: diagnostics
topic: classification
tags: [api, quality-gate, grounding, metadata-filter]
related_entries:
  - diagnostics/2026-05-25_gsc-sitemap-indexed-count-unreliable-use-url-inspection-api.md
  - integration/2026-06-19_google-search-console-api-three-gotchas.md
---

# GSC Impression Split as Consolidation Signal

## Pattern

Google Search Console (GSC) Overview shows two performance entries for what should be a single page:
- `https://example.com/page` (no trailing slash) — impressions **DOWN** week-over-week
- `https://example.com/page/` (with trailing slash) — impressions **UP** week-over-week

And a 301 redirect from the no-slash URL to the slash URL is confirmed live (verified by `curl -sI`).

**Interpretation: this IS the consolidation process working, not a signal that the redirect is broken or missing.**

## Mechanism

When Google discovers two URL variants (typically via external links or historical indexing of the non-canonical form), it tracks performance data against the URL it originally crawled — even when a 301 immediately redirects to the canonical. Over multiple recrawl cycles, Google migrates crawl equity and impression data from the non-canonical (DOWN) to the canonical (UP). The split impression data is the visible trace of this migration.

The process typically resolves over weeks; the DOWN/UP trend is the resolution happening.

## How It Was Observed

Real case from semalytics.com session 2026-07-10:
- `/tools/disc-assessment` (no trailing slash) — DOWN 57% impressions week of 2026-06-30 to 2026-07-06
- `/tools/disc-assessment/` (with trailing slash) — UP impressions same period
- `curl -sI https://semalytics.com/tools/disc-assessment` returned `HTTP/2 301` → `/tools/disc-assessment/` — redirect confirmed working
- No server-config change was needed. The redirect was already correct via nginx `try_files $uri $uri/` directory fallback

## Diagnostic Decision Tree

When you see a GSC impression split with two URL variants:

1. **Verify the 301 is live**: `curl -sI <non-canonical-url>` — should return 301 pointing to canonical
2. **Verify canonical tag on the canonical page**: `<link rel="canonical" href="[canonical]">`
3. **Verify sitemap**: only canonical URL should appear
4. **Verify internal links**: all internal links should use the canonical form

If all 4 checks pass → **do nothing, wait**. The split will resolve over weeks as Google recrawls. The down/up trend IS the resolution.

If any check fails → fix the failing check and re-verify.

## Common Anti-Pattern to Avoid

Adding a new explicit 301 redirect rule in nginx (or other server config) when `try_files` is already handling it correctly. This is redundant and, for directory-style pages, can introduce redirect loops if the explicit rule is misconfigured (verified in [project] nginx config comment on the `/api/use-cases` route that caused a loop).

## When It Does NOT Apply

- When BOTH variants are stable or both growing — that's a true split with no consolidation happening
- When the redirect is absent or misconfigured (returns 200 or 302 instead of 301)
- When the canonical tag points to the non-canonical URL (contradicting the redirect)
- When internal links point to the non-canonical URL and Google has indexed those links — then you may need to update internal links AND wait for Google to recrawl them

## Connection to Related Patterns

This is a specific case of the broader principle in `diagnostics/2026-05-23_live-smoke-as-verification-gate-mocks-pass-prod-breaks.md`: **trust live verification signals over aggregated reports**. The GSC impression split is a live signal showing migration progress; mis-interpreting it as a failure can trigger unnecessary changes.

## Source Context

Discovered during [project] session 2026-07-10 while investigating why GSC Overview showed an impression split for `/tools/disc-assessment` (no slash) vs `/tools/disc-assessment/` (slash). Initial concern was a broken redirect or missing consolidation. Verification confirmed the redirect was live and working; the split was the consolidation process itself. No remediation needed — consolidation is on track.

## References

- Google Search Console redirect handling and canonicalization — implicit in GSC's multi-variant tracking behavior
- nginx `try_files $uri $uri/` pattern — automatically issues internal redirects (not external 301s) but Google crawls the final destination
