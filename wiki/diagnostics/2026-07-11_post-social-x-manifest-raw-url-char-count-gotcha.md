---
title: post-social.py X manifest — raw URL char count, not t.co 23-char shortening
source_mode: builder
novelty_type: reusable_diagnostic
grounding_score: 0.80
staleness_risk: slow_decay
importance: 2
pinned: false
created: 2026-07-11
domain: diagnostics
topic: tool-behavior-gotcha
tags: twitter, bluesky, social-automation, character-limit, post-social
related_entries: []
---

# post-social.py X Manifest — Raw URL Character Count Gotcha

The `scripts/post-social.py` dry-run reports raw character counts for X (Twitter) tweets. It does NOT apply Twitter's t.co URL shortening (which counts any URL as 23 chars regardless of length). This means dry-run char counts for tweets containing long URLs will read higher than the actual posted tweet length.

## When This Applies

- Writing X thread manifests for `post-social.py` in the semalytics-gtm repo
- Any tweet that contains a URL with UTM parameters (long URLs)
- Dry-run output showing tweet char count > 280
- Verifying that a tweet will post successfully without Twitter API rejection

## When This Does NOT Apply

- BlueSky posts — Bsky has a true 300-char grapheme limit with NO URL shortening. The full URL counts toward 300. Keep Bsky URLs short or drop UTMs.
- Tweets with no URL or very short URLs (< 23 chars) — shortening provides minimal difference
- Reading posted tweets (after they've successfully landed) — the actual posted length is final

## The Rule

**For X tweets:** The Twitter v2 API accepts the full-length URL and handles t.co shortening server-side. A tweet that reads 312 chars in the `post-social.py` dry-run will post successfully as long as the non-URL text portion is ≤ 257 chars (280 − 23 for the URL).

Formula:
```
safe_text_length = 280 - 23 = 257  (when tweet contains one URL)
safe_text_length = 280 - (23 × N)  (when tweet contains N URLs)
```

**For Bsky:** Count everything literally. Full URL + full text must be ≤ 300 chars. Use short URLs or omit UTMs for Bsky posts.

## Conservative Trim Strategy

When dry-run shows tweet N chars over 280:

1. Calculate excess: `excess = raw_count - 280`
2. Trim the tweet text by `excess + 5` chars (5-char buffer)
3. Re-run dry-run to confirm under 280

Do NOT trim the URL itself — UTM parameters matter for attribution tracking.

## Bsky Alternative

For Bsky, drop UTMs and use the bare canonical URL:
- `https://semalytics.com/blog/SLUG/` (50 chars) vs. `https://semalytics.com/blog/SLUG/?utm_source=bluesky&utm_medium=blog&utm_campaign=q3-2026&utm_content=SLUG` (100+ chars)
- Bsky link cards show the domain anyway; UTM on Bsky has low attribution value since Bsky doesn't pass referrer cleanly

## Verified Example (2026-07-11)

OCEAN blog launch manifest, tweet 3:
- Dry-run reported: 312 chars (full URL counted raw)
- Actual tweet chars with t.co shortening: ~134 chars (text) + 23 (URL) = 157 chars
- Fix applied: trimmed text to ensure raw count was under 280 as a conservative safety margin

## Source Context

From semalytics-gtm content production session 2026-07-11. The gotcha surfaced when producing X threads for the OCEAN personality-dimension blog launch. post-social.py's dry-run warned of 280+ char tweets, but the actual X API accepted them because server-side t.co shortening applied. Documented for future tweet-manifest verification passes.
