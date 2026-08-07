---
title: X API v2 returns 403 Forbidden when tweet exceeds 280 effective characters
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-21
domain: diagnostics
topic: tool-behavior-gotcha
tags: x-api, twitter, social-posting, debugging, character-limit
related_entries: diagnostics/2026-07-11_post-social-x-manifest-raw-url-char-count-gotcha.md
---

# X API v2 Returns 403 Forbidden When Tweet Exceeds 280 Effective Characters

When posting to X (Twitter) via API v2, a 403 "You are not permitted to perform this action" error is returned when the tweet exceeds 280 effective characters. The error message is misleading — it reads as a permissions/authentication failure, not a content-length failure.

## Root Cause

X API v2 counts URLs via t.co shortening (always 23 characters regardless of actual URL length). The raw character count reported by local scripts or dry-runs includes the full URL length, which can be 100–170+ characters for UTM-tagged URLs. This inflates the apparent count.

Effective character count formula:
```
effective_chars = raw_chars - actual_url_length + 23
```

## Example from This Session

- Raw tweet text: 461 chars
- URL: 169 chars (semalytics.com/blog/... with full UTM params)
- Effective count: 461 - 169 + 23 = 315 chars → OVER 280 → 403 returned
- After trimming body text: 384 raw chars → 384 - 169 + 23 = 238 chars → UNDER 280 → success

## Diagnosis Path

1. If X API returns 403 on tweet post (but media upload succeeded), suspect tweet length before assuming credential/permission failure.
2. Run dry-run to see raw char count.
3. Calculate effective count using the formula above.
4. Trim body text until effective count < 275 (leave a small buffer).

## When This Applies

- Posting to X via API v2 with a URL in the tweet
- Raw character count appears to exceed 280 in tooling (post-social.py, custom scripts, or manual counting)
- 403 error is returned without other symptoms of auth failure (media upload succeeded, account has write permissions)

## When This Does NOT Apply

- Genuine 403 permission errors (app lacks write scope, account suspended, read-only mode) — these also return 403 but media upload will also fail or the account will show visible restrictions
- Rate limit errors return 429, not 403
- Tweets with no URL or URLs shorter than 23 chars — shortening provides negligible difference
- Other social platforms (BlueSky, LinkedIn) — Bsky counts full URL length against its 300-char limit; LinkedIn has different limits

## Distinction from Related Gotcha

The existing entry "post-social.py X manifest — raw URL char count gotcha" (2026-07-11) documents how the dry-run reporting tool under-counts effective characters. This entry documents the **API-level consequence** when that miscalculation isn't caught: a 403 error that masquerades as a permissions failure.

## Verified

2026-07-21 in semalytics-gtm content operations session. Media upload (media_id returned successfully) confirmed credentials were valid; the 403 was exclusively on the tweet post call. Trimming the tweet body from 461 raw chars to 384 raw chars resolved it. Subsequent post succeeded with effective count of 238 chars.

## Source Context

From semalytics-gtm content operations session 2026-07-21. The error surfaced when posting an X thread with a long URL and body copy that appeared under 280 in the raw count but exceeded it after applying t.co shortening. Documented to prevent future misdiagnosis of this 403 as a credential failure.
