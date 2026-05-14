---
title: FastAPI StreamingResponse pre-flight gates must raise BEFORE construction
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.9
staleness_risk: stable
importance: 4
created: 2026-05-12
tags: api, quality-gate, empirical
related_entries: []
---

# FastAPI StreamingResponse Pre-Flight Gates Must Raise BEFORE Construction

## The Pattern

When a FastAPI endpoint returns `StreamingResponse(generator())`, any `raise HTTPException(...)` from inside the generator body is swallowed — the response headers (200 OK) have already been sent, and the exception surfaces only as a truncated stream or a generic ASGI error in logs.

**This means: pre-flight feasibility checks (409 Conflict, 422 Unprocessable, 403 Forbidden gates) MUST execute and raise BEFORE the `StreamingResponse(...)` constructor is called.** Not inside the generator function — inline in the endpoint, ahead of construction.

## Wrong

```python
@router.post("/rewrite")
async def rewrite(req: RewriteRequest):
    async def stream():
        check = run_pre_rewrite_check(req)   # too late — headers already sent
        if not check.ok:
            raise HTTPException(409, check.reason)
        async for chunk in llm.stream(...):
            yield chunk
    return StreamingResponse(stream(), media_type="text/event-stream")
```

The exception fires after the status line and headers have already been transmitted to the client. The client sees `200 OK` and begins buffering the stream body, but gets a truncated response or a cryptic ASGI error. The HTTPException payload never reaches the client.

## Right

```python
@router.post("/rewrite")
async def rewrite(req: RewriteRequest):
    check = run_pre_rewrite_check(req)       # synchronous gate, fires inline
    if not check.ok:
        raise HTTPException(409, check.reason)

    async def stream():
        async for chunk in llm.stream(...):
            yield chunk
    return StreamingResponse(stream(), media_type="text/event-stream")
```

The check runs synchronously before the StreamingResponse constructor. If it fails, the HTTPException is raised in the normal path — headers haven't been sent yet, and the client receives the correct 4xx status code with the error body.

## Why It Matters

**Client behavior depends on status codes, not stream content:**
- 4xx client errors are useless if the client sees `200 OK` + a half-rendered stream
- Frontend retry logic inspects `response.status_code`, not stream payload
- Without a proper status code, a retry handler can't distinguish "user input invalid" from "downstream service error"

**Observability breaks:**
- Sentry, structured logs, and APM systems group errors by status code
- A 409 Conflict inside a 200 OK stream gets logged as a 200, hiding the actual problem
- Dashboards querying `count(status_code=409)` miss this error entirely

**Testing becomes fragile:**
- Test assertions like `assert response.status_code == 409` will fail confusingly
- The test will hang or timeout waiting for a complete stream that never arrives
- The actual error (buried in logs or mid-stream) is hard to debug

## When This Applies

- Any FastAPI / Starlette endpoint returning `StreamingResponse` or `EventSourceResponse`
- Any endpoint with a deterministic pre-flight check: rate limit, feasibility, cost cap, feature flag, input validation, authorization
- **LLM-streaming endpoints especially** — pre-checks should validate:
  - Input format and constraints
  - User budget and quota
  - Feature flags (is streaming enabled for this user?)
  - Canary/rollout gates
  - All before the first token is generated

Pre-flight checks are those that can be evaluated **entirely before** streaming begins. If the check result doesn't depend on the stream itself, it belongs inline.

## When This Does NOT Apply

**Mid-stream errors** (e.g., upstream LLM returns 429 mid-generation):
- These can't be pre-flighted; you don't know they'll happen until you're already streaming
- Response: emit a structured error event in the stream itself — JSON `{"error": "rate_limit"}`, or a comment in the SSE stream
- The client receives `200 OK` but parses the stream payload to detect errors
- This is a different contract from pre-flight gates; document both clearly

**Non-streaming endpoints:**
- `raise HTTPException` works normally in sync/async endpoints
- No special care needed

**Streaming endpoints with no pre-flight logic:**
- If your endpoint has no deterministic checks, this pattern doesn't apply
- Consider whether you're missing a validation gate

## Async DI Ordering Subtlety

Route-level `Depends(...)` parameters (e.g., `FullyAuthenticatedUser`) fire **BEFORE** the function body executes. So a guard check inside the body cannot run for unauthenticated callers — they hit the auth dependency first and get `401`.

If you want a condition to surface as `404` (or another status) for unauthenticated probes, express the guard as its own `Depends(...)` dependency ahead of auth in the parameter list, not as a body statement. Example:

```python
# Wrong: this guard never runs for unauth'd users (they hit auth_dep first)
async def endpoint(auth: FullyAuthenticatedUser = Depends(...)):
    if not settings.feature_enabled:
        raise HTTPException(404, "Not found")

# Right: move the flag check to its own Depends that runs ahead of auth
async def check_feature_enabled():
    if not settings.feature_enabled:
        raise HTTPException(404, "Not found")

async def endpoint(
    _feature: None = Depends(check_feature_enabled),  # runs first
    auth: FullyAuthenticatedUser = Depends(...),       # runs second
):
    ...
```

This principle applies to streaming and non-streaming endpoints alike.

## Grounding

Verified in **COS SEO Planner Slice 4.5** (2026-05-08 to 2026-05-12). The `pre_rewrite_check` module in `cos/backend/routers/seo_planner.py` dispatches three deterministic checks:

1. **Duplicate:** is this URL already in the target segment?
2. **Cannibalization:** does this URL compete with another?
3. **AI-overview readiness:** is the input data sufficient for rewrite quality?

All three must raise `409 Conflict` before `stream_rewrite(...)` calls `StreamingResponse(...)`. Tests in `test_seo_planner_pre_rewrite.py` assert:

```python
response = client.post("/rewrite", json=duplicate_url_request)
assert response.status_code == 409  # Would silently pass with 200 OK + half stream if gate was inside generator
assert response.json()["reason"] == "duplicate"
```

This test **would silently pass** if the gate was moved inside the generator — the client would receive `200 OK`, the assertion would not catch the bug, and only end-to-end testing or user reports would surface the problem.

## Source Context

Discovered during pre-rewrite validation on the COS SEO Planner's `StreamingResponse` endpoint. The pattern generalizes to any FastAPI streaming use case where early validation is possible. Previously documented informally in code comments; formalized and filed as wiki entry on 2026-05-12.
