---
title: HTTP/2 HPACK dynamic-table desync masquerades as "Invalid API key" in PostgREST
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-18
tags: empirical, grounding, api, stable
related_entries: [diagnostics/2026-05-18_flaky-endpoint-cluster-shared-backend-dependency.md]
domain: diagnostics
topic: root-cause-analysis
---

# HTTP/2 HPACK dynamic-table desync masquerades as "Invalid API key" in PostgREST

## Symptom

The backend service (Python/FastAPI) intermittently fails with 500s on endpoints that depend on a long-lived httpx client connection to a remote HTTPS API (Supabase PostgREST, or similar). The 500s are **intermittent** and **uncorrelated** — some requests succeed, some fail, retrying often works.

When you examine the access log, you see:

```
postgrest.exceptions.APIError: {
  'message': 'JSON could not be generated',
  'code': 401,
  'hint': '...',
  'details': 'b\'{"message":"Invalid API key","hint":"Double check your API key."}\''
}
```

Or, in httpx logs:

```
httpcore.RemoteProtocolError: <ConnectionTerminated error_code:9>
```

The API key is **valid** — other requests through the same connection succeed. The error is not a credential rotation issue.

---

## The Trap

When you see "Invalid API key" in the error, you think:
1. The API key rotated
2. The key leaked and was revoked
3. The key is malformed or has characters that need escaping

So you:
- Check the key in the config
- Rotate it
- Retry
- Find nothing changed

The actual cause is upstream in the HTTP/2 protocol layer, not the credential itself. The bogus 401 is a **symptom** of header corruption, not a credential failure.

---

## Diagnosis

Look for **GOAWAY frames with error_code=9** in the connection logs around the same timestamp as the 401s.

From RFC 7540 § 6.9: `error_code=9` is `COMPRESSION_ERROR`, meaning the HTTP/2 HPACK dynamic header table state diverged between the client and server.

**Correlation > causation:** If you see `GOAWAY error_code:9` within 10–20 milliseconds of the `Invalid API key` 401s **on the same connection**, HPACK desync is the culprit.

Specific indicators:
1. The 401s appear on a **long-lived connection** with connection pooling enabled (default in httpx).
2. The 401s are **intermittent**, not 100% failure.
3. The API key is **valid** — confirmed by checking config, testing with a fresh key, or seeing successful requests on the same key.
4. The error occurs behind a **load balancer, reverse proxy, or Cloudflare** (these often mux/demux HTTP/2 frames and can trigger desync bugs in older versions).
5. Retrying the request **sometimes works** (because the connection is recycled or the retry hits a different upstream server).

---

## Root Cause

HTTP/2 uses HPACK (RFC 7541) to compress headers. HPACK maintains a **dynamic table** — a stateful history of recently-sent headers — to reduce payload size.

When the client sends a request:
1. Client compresses the request headers using its local HPACK table.
2. Server decompresses using its local HPACK table.
3. Both update their tables identically (in theory).
4. Next request: both start from the updated state.

**Desync happens when:**
- The client sends a header sequence that assumes the table is in state T.
- The proxy/server's table is in state T-1 or T+1 (due to a lost frame, reordered frame, or proxy bug).
- The decompression produces garbage — e.g., the `authorization: Bearer [key]` header decodes as `x-forwarded-for: [random data]`.
- The downstream service (PostgREST) receives a mangled auth header and rejects the request.

The specific observed pattern in COS:
- A long-lived pooled httpx connection to Supabase PostgREST in HTTP/2 mode.
- Periodically (38 events/hour observed), the connection received a GOAWAY frame from the Supabase edge (likely Cloudflare).
- In-flight requests on that connection corrupted: the `apikey` header (a custom header) was decoded as garbage.
- PostgREST saw the garbage and returned 401 "Invalid API key" because the decoded header didn't match the expected format.

This is **not a PostgREST bug** — it's a client-upstream handshake issue.

---

## Fix

**Switch to HTTP/1.1 on the long-lived connection.** You lose HTTP/2 multiplexing, but you eliminate HPACK state altogether.

For `supabase-py` (version 2.30+), configure the httpx client:

```python
from supabase import create_client, ClientOptions
import httpx

client = create_client(
    url="https://your-supabase-url.supabase.co",
    key="your-api-key",
    options=ClientOptions(
        httpx_client=httpx.Client(http2=False, timeout=120),
    ),
)
```

**In any other Python service** using httpx for a long-lived connection:

```python
import httpx

client = httpx.Client(http2=False, timeout=120)
response = client.get("https://api.example.com/endpoint")
```

The `http2=False` parameter disables HTTP/2; requests fall back to HTTP/1.1.

**Verification:** After deploying this fix, monitor for:
- `GOAWAY error_code:9` events → should drop to zero.
- `ConnectionTerminated` exceptions → should drop to zero.
- Intermittent 401s on valid credentials → should drop to zero.

In COS production (post-deploy, commit cc84829):
- Zero HPACK-related GOAWAY frames across ~15 min of production traffic.
- Zero `ConnectionTerminated` exceptions.
- Zero spurious 401s on the affected endpoints.

---

## Cost of the Fix

**Downside:** No HTTP/2 multiplexing on that connection. Multiple concurrent requests to the same upstream must open separate TCP connections (or wait for serial response).

**When this costs you:**
- High-concurrency scenarios where you stream many requests through a single client over HTTP/2.
- Long-lived streaming connections (e.g., Server-Sent Events, WebSockets tunneled via HTTP/2).

**When this costs nothing:**
- Bursty, short-lived request patterns (common in backend-to-API integration).
- Request concurrency ≤ 6–8 (modern TCP handles this efficiently).
- Latency matters more than throughput (HTTP/1.1 has one concurrent request at a time, but each request is simpler to debug).

For COS, the Supabase client makes short, bursty requests — typically 1–3 concurrent requests per user action. HTTP/1.1 is a negligible downgrade.

---

## Generalization

This pattern is not Supabase-specific. **Suspect HPACK desync in any Python service that:**
1. Uses a long-lived httpx connection to a remote HTTPS endpoint.
2. That endpoint is behind a load balancer, Cloudflare, or other proxy.
3. You see intermittent 401/403 errors on otherwise-valid credentials.
4. Restarting the connection (or retrying) sometimes fixes it.

Check:
- Does your service use `httpx.Client()` or similar connection pooling?
- Is the upstream behind a proxy?
- Do you see `GOAWAY error_code:9` or `RemoteProtocolError` in logs?
- Are the 401s intermittent, not 100%?

If yes to all: flip `http2=False` and re-test.

---

## References

- **RFC 7540 (HTTP/2), § 6.9, § 7:** HPACK state machine and error codes.
- **RFC 7541 (HPACK):** Dynamic header table specification. Sections § 2.3–2.4 cover state synchronization.
- **Cloudflare HPACK bugs:** Multiple versions of Cloudflare's HTTP/2 implementation have had HPACK desync bugs. This fix sidesteps them entirely.
- **COS incident:** Commit `cc84829` in `internexio/cos` (internal). Affected endpoints: `/api/projects/<id>/personas`, `/api/projects/<id>/campaigns`, `/api/projects/<id>/conversations`, `/api/projects/<id>/suggestions`. Beads cos-p9a, cos-324, cos-16h, cos-5in were all manifestations of the same root cause.

---

## Source Context

Discovered during investigation of intermittent 500s on COS project-page subresources (cos-p9a, filed 2026-05-17). The initial hypothesis was that four separate backend endpoints were failing independently (Personas, Campaigns, Recent Chats, Suggestions). Triage via the **flaky-endpoint-cluster** pattern revealed a shared backend dependency. Stack traces pointed at Supabase client calls, not the endpoints themselves. Log analysis surfaced the correlation: `GOAWAY error_code:9` (HTTP/2 COMPRESSION_ERROR) appearing 5–15ms before the 401s. Root cause identified as HPACK dynamic-table state desync in HTTP/2 connections to Supabase PostgREST. Fix validated in staging (2026-05-18) and production (2026-05-18). Zero regressions post-deploy. Grounding: direct observation of error frames, HPACK state analysis, and post-fix validation. Confidence: 0.9 (empirical confirmation; 0.1 reserved for undiscovered edge cases involving HTTP/2 variants or Cloudflare updates).
