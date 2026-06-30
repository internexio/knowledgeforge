---
title: Google Search Console API — three gotchas (property form mismatch, deprecated ping, contents.submitted type cast)
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic + transferable_framework
grounding_score: 0.85
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-06-19
domain: integration
topic: external-tools
tags: google-search-console, gsc, sitemap, seo, python, oauth-service-account, google-api, api-gotchas
related_entries:
  - diagnostics/2026-05-25_gsc-sitemap-indexed-count-unreliable-use-url-inspection-api.md
---

# Google Search Console API — three gotchas in one script

Three subtleties in Google's Search Console API surface that are easy to miss and silently break sitemap-submission tools. All three encountered together while fixing a single script (cos-oh69, 2026-06-19), each producing a different misleading failure mode.

## 1. Property registration form matters — mismatching it returns 403 that LOOKS like authorization failure

GSC properties are registered as either **URL-prefix** (`https://example.com/`) or **domain property** (`sc-domain:example.com`). The API uses the same endpoint shape (`webmasters/v3/sites/{siteUrl}/...`) for both, but the `siteUrl` path parameter must EXACTLY match the registered form, including the scheme and trailing slash for URL-prefix or the `sc-domain:` prefix for domain properties.

Mismatching the form returns:

```
HTTP 403
User does not have sufficient permission for site 'https://example.com/'.
See also: https://support.google.com/webmasters/answer/2451999.
```

This **sounds like an authorization issue** (and Google's documentation reinforces that read), but is actually a property-not-found error. The service account may have full Owner permission on the property as registered, just in a different form.

**Detection.** Call `svc.sites().list()` first. The returned `siteEntry` array contains the registered form verbatim:

```python
sites = svc.sites().list().execute()
# Returns: {"siteEntry": [{"siteUrl": "sc-domain:example.com", "permissionLevel": "siteFullUser"}, ...]}
```

Use the value of `siteUrl` from that response. Don't reconstruct it from scheme + hostname.

**Preference.** For portfolio-scale tools, register domain properties (`sc-domain:`) since they cover all subdomains and schemes under the apex. URL-prefix properties are narrower and force per-scheme config.

## 2. The ping endpoint is dead since 2023-06-26

Many old GSC scripts use `https://www.google.com/ping?sitemap=URL` to nudge Google's crawler after content changes. Google [deprecated this](https://developers.google.com/search/blog/2023/06/sitemaps-lastmod-ping) on 2023-06-26. All requests now return:

```
HTTP 404
Sitemaps ping is deprecated. See https://developers.google.com/search/blog/2023/06/sitemaps-lastmod-ping.
```

**No supported replacement at the page level exists.** Sitemap submission via the still-active `webmasters/v3/sites/{siteUrl}/sitemaps/{feedpath}` PUT endpoint is sufficient — Google re-crawls within 24-48h via that path. The deprecation notice explicitly says page-level pinging is gone; lastmod attributes in the sitemap itself signal freshness.

**Fix.** Drop ping code entirely. Use only the sitemap-submission PUT for re-crawl signaling. If your script reported "Pinged N pages" in its output, that's a tell that it predates the deprecation; check the actual HTTP response codes — most likely they're all 404s and the script just doesn't notice.

## 3. `contents.submitted` is a string, not an int

The GSC sitemap **verification** API (`GET webmasters/v3/sites/{siteUrl}/sitemaps/{feedpath}`) returns:

```json
{
  "isPending": true,
  "errors": 0,
  "warnings": 0,
  "contents": [
    {"type": "web", "submitted": "84", "indexed": "30"}
  ],
  "lastSubmitted": "2026-06-20T17:45:53.525Z"
}
```

`submitted` and `indexed` inside each `contents` item are **strings**, not integers, in the API response. Code that does:

```python
total_urls = sum(c.get("submitted", 0) for c in contents)
```

…raises `TypeError: unsupported operand type(s) for +: 'int' and 'str'` because the default value (`0`) is int but the actual values are strings. The default is only returned if the key is missing — when present, the value is always a string.

**Fix.** Cast to int:

```python
total_urls = sum(int(c.get("submitted", 0)) for c in contents)
```

Other top-level fields (`errors`, `warnings`) ARE returned as ints, so don't blindly cast everything — just the per-content counters.

## When all this applies

Any programmatic interaction with GSC's `webmasters/v3` sitemap surface. Auth requires a Google service account with the SA email added as Owner / Full User on the target property in the GSC UI (manual setup, can't be automated via API since it's a permission grant).

## When this does NOT apply

- Read-only Performance/Analytics data via `searchanalytics.query` — different endpoint shape, same property-form rule applies but no sitemap-submission gotchas.
- The Indexing API (`indexing.googleapis.com`) is a different service for instant page-level indexing of structured-data pages (JobPosting, BroadcastEvent only) — not a general sitemap or page-discovery API.

## Grounding

All three bugs encountered in sequence on a single script (`[project]/scripts/submit_sitemap_gsc.py`, later moved to `sem-tools/scripts/submit_sitemap_gsc.py` and integrated as the `sem.gsc.sitemap` module + `sem gsc submit-sitemap` CLI). Each fix verified end-to-end against the real semalytics.com GSC property:

- Property form: HTTP 403 before fix → HTTP 204 (sitemap accepted) after fix
- Ping: HTTP 404 on all 18 hardcoded pages before fix → removed entirely after fix
- Type cast: `TypeError` before fix → "URLs submitted: 84" after fix

Service account used: `sem-tools-gsc@semalytics-cos.iam.gserviceaccount.com`, with access to 7 portfolio properties (semalytics, tuannorthwest, lacabar, internexio, joeymasciotra, lacacafe, laca38th) all registered as `sc-domain:` form.

Beads: cos-oh69 (the fix), cos-p51d (the sitemap re-submit that surfaced the bugs).

## Related

- `diagnostics/2026-05-25_gsc-sitemap-indexed-count-unreliable-use-url-inspection-api.md` — separate GSC gotcha: the `indexed` count in the sitemap-status response is stale/unreliable. Use URL Inspection API for ground truth on per-URL indexing state.
