---
title: COS analyze_full payload size ceiling — 26K chars triggers 502, ~2.6K succeeds in 130s
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-05-20
domain: debugging
topic: error-classification
tags: api, latency, infrastructure
related_entries: ["diagnostics/2026-05-19_cos-mcp-analyze-full-timeout-direct-curl-fallback.md"]
---

# COS analyze_full payload size ceiling — 26K chars triggers 502, ~2.6K succeeds in 130s

## Problem

The COS `POST /api/analyze/full` endpoint has a payload size / processing time ceiling that triggers an nginx 502 Bad Gateway **before the backend returns a result**. This is distinct from the MCP transport timeout documented in the related entry. That entry suggested direct curl as a fallback; this entry documents that **direct curl ALSO fails above a certain payload threshold**.

## Observed behavior (2026-05-20)

| Payload size | Result | Latency |
|---|---|---|
| 26,298 chars (~26K) | HTTP 502 (nginx upstream) | 65s |
| 2,606 chars (~2.6K) | HTTP 200, valid full-framework JSON | 131s |

The 502 page is the standard `nginx/1.18.0 (Ubuntu)` upstream-timeout page. No JSON error body. No diagnostic metadata in the response.

## Root cause

The backend timeout (likely set in nginx or upstream gunicorn/uvicorn) is approximately 60 seconds. A 26K payload exceeds the per-framework analysis time budget — the 7 frameworks running sequentially or with partial concurrency take longer than the upstream allows.

The 2.6K payload returns in ~130s, which means the request itself can wait past 60s if it's making forward progress. The 60-second ceiling may be specifically on the **time-to-first-byte** rather than total request time. (Untested hypothesis — would need backend logs to confirm.)

## Practical guidance

When validating long-form content (full page bodies, multi-section guides):

1. **Don't try to score the full 26K-char page in one call.** It will 502.
2. **Score representative excerpts** of 2–5K chars. Pick the surfaces most relevant to the validation question:
   - Bolster validation → hero + new additions
   - Value-prop validation → full body intro + CTA
3. **Slice with awareness of artifacts.** A slice that omits the CTA section will get CTA Effectiveness 2/10 — but that's an artifact of slicing, not a real signal about the full page. Note this in any decision derived from the score.
4. **Score in 2–3 passes** for comprehensive coverage (hero/lead, body H2s, FAQ+CTA). Combine subjective interpretation rather than trying to feed everything at once.

## Endpoint and auth details

**Endpoint base:** `https://semalytics.com/api/analyze/full` (NOT `https://semalytics.com/cos/api/analyze/full` — that path was incorrect in the related MCP timeout entry. This entry supersedes that detail.)

**Auth header:** `Authorization: Bearer <key>` (not `X-API-Key: <key>`). Confirmed by reading cos-mcp source (`server.py` builds the header as `Bearer`). Sending `X-API-Key` returns 401 immediately.

## When this ceiling does NOT apply

- Single-framework endpoints (`/api/analyze/hape`, `/api/analyze/big-five`, etc.) — each one runs ~15–25s, well under the 60s ceiling.
- The MCP `analyze_full_comms` tool has its own (lower) timeout that fires before the backend ceiling. See related entry for fallback guidance.

## Relationship to the related MCP timeout entry

The related entry (`diagnostics/2026-05-19_cos-mcp-analyze-full-timeout-direct-curl-fallback.md`) documented MCP transport timeout and suggested direct curl as a workaround. **This entry reveals that direct curl is also subject to the backend 60s ceiling when payloads exceed ~20K chars.** Both the MCP timeout AND this payload-size ceiling must be worked around separately:

- MCP timeout → use direct curl (per related entry)
- Direct curl + large payload → slice the payload first (per this entry)

The two issues are orthogonal. You may encounter one or both depending on payload size and endpoint access method.

## Future remediation (out of scope)

The backend could:
- Chunk the analysis across frameworks and return streaming results
- Split into per-framework parallel calls fronted by a composite endpoint
- Increase the upstream timeout

The current monolithic `/api/analyze/full` will continue to hit this ceiling until refactored.

## Source context

Observed during content-analytics validation in the 2026-05-20_content-analytics-cos-validation session. Direct curl testing with payloads ranging from 2.6K to 26K chars revealed the size-to-latency relationship and the 60-second upstream timeout boundary. Grounding: 0.9 (high confidence from direct observation, concrete payload thresholds, reproducible condition isolation, and working mitigation).

## Related session artifacts

- `/tmp/cos-payload.json` — 26K char payload that 502'd
- `/tmp/cos-delta-payload.json` — 2.6K char excerpt that succeeded
- `/tmp/cos-delta-result.json` — full scoring response from successful small-payload call
