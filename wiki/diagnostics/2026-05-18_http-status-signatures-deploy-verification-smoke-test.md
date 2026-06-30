---
title: HTTP status signatures (404 vs 405 vs 401) as positive deploy-verification signals
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.7
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-18
tags: diagnostics, http, deployment-verification, smoke-testing, nginx, fastapi, route-registration
related_entries: [diagnostics/2026-05-15_rest-client-tolerance-http-status.md, diagnostics/2026-05-18_http2-hpack-desync-bogus-401-from-postgrest.md]
domain: diagnostics
topic: ops
---

# HTTP status signatures (404 vs 405 vs 401) as positive deploy-verification signals

## Pattern

During post-deploy smoke testing, treat HTTP status codes as diagnostic signatures with distinct meanings. A failing call is not always a deploy failure — read the failure mode.

## The signature table

| Status | Meaning during smoke test | Action |
|--------|---------------------------|--------|
| **200** | Route registered, auth satisfied, handler returned successfully | Continue to response-shape validation |
| **401 Unauthorized** | Route is REGISTERED. Auth dependency rejected the call. **Positive signal — your endpoint deployed.** | Provide credentials and re-try |
| **404 Not Found** | Either route NOT registered (deploy failed, wrong path) or path-rewrite (nginx, base-path) misconfiguration | Check `/api/openapi.json` or `/api/docs` for the canonical path |
| **405 Method Not Allowed** | nginx routing problem (most common) OR FastAPI route registered for different verb. Usually a proxy/nginx mismatch, NOT a backend bug | Try alternate path prefixes; check nginx config |
| **502/503/504** | Backend up but failing under load, OR backend down | Check container health, dependent services |

## Why this matters

The most common smoke-test mistake is reading 401 or 405 as "my deploy is broken" and rolling back. In reality:

- **401 confirms route registration** — strongest positive signal short of a 200
- **405 usually means nginx routing, not your code** — fixing the wrong layer wastes 15+ minutes

## Grounding from session

After pushing `feat(mcp,api): add audience_profile + optimize_email_for_prospect` to origin master, smoke test went:

1. `POST /cos/api/analyze/audience-profile` → 405 (nginx HTML error page). Initial read: "my route is broken."
2. `OPTIONS /cos/api/analyze/full` (existing prod route) → also 405. Realization: nginx layer, not backend.
3. `POST /api/analyze/audience-profile` (without `/cos/` prefix) → 401 (JSON, FastAPI). Realization: **route IS registered.** The test environment serves API at the bare `/api/*` path; the `/cos/api/*` path is for UI-side fetches and 405s on POST.
4. Added Bearer token from staging `.env` → 200, full JSON response.

Without the signature read, would have lost 15+ minutes debugging the "wrong" layer. With it, the path was: 405 → check other routes → also 405 → nginx hypothesis → bypass /cos/ → 401 (positive) → add auth → 200 in under 3 minutes.

## When this applies

- Any post-deploy smoke test against a proxied FastAPI / Express / Rails backend
- Multi-tenant or path-prefixed deployments (especially nginx + Docker)
- Verifying a new endpoint exists before debugging its logic
- Debugging "why did my deploy fail?" when the response is non-200

## When this does NOT apply

- 401 from a service you've never deployed — could be a default deny, not a registered route
- Single-tier deployments without a proxy layer (raw uvicorn) — 405 there usually IS a route-method bug

## Failure mode to watch

Some auth middlewares return 401 BEFORE route lookup. A 401 in that case does NOT confirm registration.

**Test:** Hit a known-bogus path; if it also 401s, the middleware is the source and you've lost the diagnostic.

**Workaround:** Check `/openapi.json` or `/api/docs` for canonical paths instead of relying on the 401.

## Source Context

Discovered during post-deploy smoke testing after pushing feature to origin master in session `cos-mcp-clarify-integration-phase2-3` (2026-05-18). The signature table emerged from a real incident: three failed smoke-test hits (405, 401, 200) across a 3-minute diagnosis window. Grounding reflects direct observation of the multi-status pattern and the timing impact of correct vs. incorrect interpretation. Confidence: 0.7 (high observational fidelity; 0.3 reserved for edge cases in exotic middleware stacks or auth frameworks not encountered in the grounding context).
