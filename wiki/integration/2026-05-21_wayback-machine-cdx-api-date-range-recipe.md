---
title: Wayback Machine CDX API recipe — earliest snapshot in date range
source_mode: builder
novelty_type: reusable_diagnostic
grounding_score: 0.8
staleness_risk: slow_decay
importance: 2
pinned: false
created: 2026-05-21
tags: api,retrieval,empirical
related_entries: []
domain: integration
topic: external-tools
---

# Wayback Machine CDX API — earliest snapshot in a date range

## What it is

The Internet Archive's Wayback Machine exposes two free public endpoints useful for "did this domain exist before date X, and what did it look like?" workflows.

## CDX search endpoint

```
GET https://web.archive.org/cdx/search/cdx
    ?url={url}
    &output=json
    &to={YYYYMMDD}            # upper bound on snapshot timestamp
    &limit=1                  # earliest one only
    &filter=statuscode:200    # skip 404s, redirects, etc.
```

- No API key required.
- Response is a JSON list. The **first row is the header**: `["urlkey","timestamp","original","mimetype","statuscode","digest","length"]`. Subsequent rows are data.
- "No snapshot ≤ cutoff" returns just the header row (len == 1), not an empty list. Check `len(rows) < 2` to detect no-match.
- `timestamp` is `YYYYMMDDhhmmss`. Slice `[:4]` for the year.
- The `from=YYYYMMDD` parameter exists too — combine with `to=` to bound the window.

## Fetching the archived content

```
https://web.archive.org/web/{timestamp}id_/{original_url}
```

- The `id_` modifier between timestamp and URL strips the Wayback navigation toolbar from the response, returning the page roughly as it was served originally. Use it whenever you'll parse the HTML programmatically — otherwise the toolbar's HTML and JS will pollute your text extraction.
- The plain form (no `id_`) returns the page with the Wayback toolbar injected; useful for human viewing.

## Use cases

- **Domain-age checks:** "is this domain at least N years old?" → query CDX with `to={today - N years}&limit=1`. If 1 data row → old enough.
- **Topic-shift detection:** pull earliest snapshot's content, compare vocabulary to current.
- **Pre-acquisition due diligence:** see what content used to live on a domain you're considering buying.
- **Detecting hosting changes vs. content changes:** mimetype shifts in the CDX timeline.

## Grounding

Used in `check_expired_domain_rebuild(url, soup)` in `sem/seo/spam_risk.py` (sem-tools F10.2c, sem-tools-6cb). Cutoff calculated as `datetime.utcnow() - timedelta(days=365*5)`. Confirmed empty-result behaviour (header-only response) via a unit test that supplies a CDX response with one row and asserts the detector returns `None`. Archive content fetched with the `id_` modifier so the Wayback toolbar HTML doesn't leak into the topic-comparison vocabulary set.

## Gotchas

- CDX rate-limits aren't published but are real — for multi-page audits cache results per host (see related: per-host caching for per-page detectors).
- Archive content for a given `timestamp` may redirect (302) to a slightly different timestamp if that exact snapshot is unavailable. Follow redirects on the HTTP client.
- "Earliest snapshot" doesn't mean "earliest the domain existed" — Wayback only knows what it crawled. Brand-new domains can have no snapshots at all; very old domains can have gaps.
- The CDX endpoint occasionally returns plain text instead of JSON if the `output=json` query param is dropped or misspelled. Always send it.

## When NOT to use

- **Need authoritative ownership history** → use WHOIS/SecurityTrails instead, CDX only tells you what content existed when.
- **Need real-time data** → CDX is content-as-archived, not content-as-it-is.

## When This Applies

- You need to verify a domain existed and capture its content state at a point in the past.
- You're auditing whether a domain is genuinely aged or recently acquired and retrofitted.
- You're comparing vocabulary/topics across archival snapshots to detect pivots.
- You're doing domain-age verification without access to premium WHOIS tools.

## When This Does NOT Apply

- You need legally authoritative domain ownership records (use WHOIS/SecurityTrails).
- You need current/real-time content (use direct HTTP GET, not archived snapshots).
- You need content before Wayback began archiving (1996 on most sites, but earlier for some).

## Source Context

sem-tools F10.2 spam risk batch. Extracted from `check_expired_domain_rebuild` detector in spam_risk.py, which uses CDX to detect domains repurposed after > 5 years of inactivity.
