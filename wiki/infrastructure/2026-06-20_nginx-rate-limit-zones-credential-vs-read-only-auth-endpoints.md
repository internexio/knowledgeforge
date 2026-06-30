---
title: Nginx rate-limit zones must distinguish credential-bearing vs read-only auth endpoints
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic + new_pattern
grounding_score: 0.9
staleness_risk: stable
importance: 5
pinned: false
created: 2026-06-20
tags: nginx, rate-limiting, oauth, jwt, frontend-backend, web-deploy, ci-cd, auth, production-incident
related_entries: []
---

# Nginx rate-limit zones must distinguish credential-bearing vs read-only auth endpoints

## The pattern (and how it fails)

When configuring nginx rate limits to protect auth endpoints from brute force, it's tempting to apply ONE strict zone to all `/api/auth/*` paths. This fails subtly: read-only auth endpoints (GET `/me`, POST `/refresh`, POST `/logout`) that never accept credentials end up sharing the burst quota with credential-bearing endpoints (POST `/login`, POST `/oauth/callback`, POST `/recovery/update-password`).

Modern SPA frontends probe `/refresh` and `/me` on every page load to detect a stale session. A user landing on a protected page with a stale cookie triggers 2-3 401s in under 1 second. Those 401s saturate the burst quota. Then when the user actually clicks "Sign in", the credential-bearing POST gets `429`-d before the auth handler can even run. User-visible failure: a vague OAuth error like `?error=exchange_failed`, with no actual auth error on the backend.

## Why it's hard to detect

- Backend application logs show nothing — nginx rejects the request with 429 before forwarding.
- Frontend shows a generic OAuth error.
- Nginx ACCESS log reveals it (401→401→401→429 pattern from same IP within seconds), but only if you look at the right log file in the right time window.
- Application metrics (Prometheus/Sentry) may not flag this because it's nginx-level, not application-level.

## The fix

Two location blocks, more-specific regex first (nginx evaluates regex locations in source order):

```nginx
# Credential-bearing endpoints — strict rate limit, brute-force protection
location ~ ^/api/auth/(login|oauth/callback|recovery) {
    limit_req zone=auth burst=3 nodelay;   # e.g. 5r/m
    proxy_pass http://127.0.0.1:8000;
    # ... rest of proxy config
}

# Everything else under /api/auth — general API rate limit
location ~ ^/api/auth {
    limit_req zone=api burst=20 nodelay;   # e.g. 60r/m
    proxy_pass http://127.0.0.1:8000;
    # ... rest of proxy config
}
```

## Detection rule for code review

Any time you see an `auth` zone covering `^/api/auth` or similar broad regex in an nginx config, ask: does this zone also cover the read-style endpoints (`/me`, `/refresh`, `/logout`, `/session`)? If yes, expect this failure mode under any condition that triggers parallel auth probes from a frontend with stale session state.

## When this does NOT apply

- If your auth setup uses `Authorization: Bearer` headers on every request (rather than cookie + `/me` + `/refresh` token rotation), this pattern won't trigger because there's no read-style probe phase.
- If your rate limits are per-route at the application layer (e.g. FastAPI's `slowapi`) rather than at nginx, the zone-collapsing bug doesn't apply (but the same conceptual mistake — applying brute-force protection to read endpoints — can still happen).
- High-risk pattern: SPA + cookie auth + JWT refresh + nginx-level rate limits. Low-risk pattern: server-rendered + session cookies + per-request auth check.

## Grounding

Lived through this on cos-prod 2026-06-20, bead cos-p58y. Concrete trace (nginx access log, user IP 75.172.8.225):

```
17:47:57Z  POST /api/auth/refresh  → 401  (referrer /cos/chat)
17:47:57Z  GET  /api/auth/me        → 401  (referrer /cos/admin)
17:47:57Z  POST /api/auth/refresh  → 401  (referrer /cos/admin)
17:48:01Z  POST /api/auth/oauth/callback → 429  (referrer /cos/auth/callback?code=...)
17:48:04Z  POST /api/auth/oauth/callback → 429  (user retried with new code)
```

The 3 failed-401 probes at 17:47:57 consumed the burst (`burst=3`) of the `auth` zone (`rate=5r/m`). Four seconds later the real OAuth callback POST got 429-d. The user couldn't sign in.

**Hot patch** (scp + `nginx -s reload` on cos-prod): split the location block per the fix above. Post-patch verified — 8 rapid HEAD requests to `/api/auth/me` returned 405 (expected, endpoint is GET) with zero 429s; `/api/auth/oauth/callback` POST with smoke-test payload returned 401 (Supabase rejected as expected) instead of 429. User confirmed sign-in works.

Canonical commit 054d5cb on `SEMalytics/cos` master (+ same on internexio/cos for symmetry).
