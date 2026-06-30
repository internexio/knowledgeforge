---
title: COS MCP analyze_full_comms timeout — direct curl fallback
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-19
tags: diagnostics, mcp, cos, timeout, fallback, curl, transport-layer, api-health
related_entries: []
domain: diagnostics
topic: liveness
---

# COS MCP analyze_full_comms timeout — direct curl fallback

## Problem

The `cos-mcp` MCP server's `analyze_full_comms` tool returns:

```
Error: Upstream request timed out, please retry
```

within 30-60 seconds, before the underlying COS API has time to complete the 7-framework analysis (typical runtime: 120-180 seconds). The timeout is **transport-layer, not backend**. The API itself is healthy and returns full results when called directly.

## Root cause

The MCP wrapper's stdio buffer or async timeout window is shorter than the 7-framework analysis path requires. Single-framework MCP calls work (complete within 60s), but full analysis does not.

## Direct fix — bypass MCP, use curl

POST directly to the COS backend API at `https://semalytics.com/cos/api/analyze/full`:

```bash
curl -sS --max-time 180 \
  -X POST https://semalytics.com/cos/api/analyze/full \
  -H "Authorization: Bearer $COS_API_KEY" \
  -H "Content-Type: application/json" \
  -d @payload.json
```

**Payload schema** (matches `analyze_full_comms` MCP tool):

```json
{
  "content": "<text to analyze>",
  "platform": "general",
  "target_audience": "<audience description>"
}
```

Returns full 7-framework JSON in ~120-180 seconds:
- HAPE (Engagement)
- Big Five (Personality)
- Strategic Clarity
- Framing Strategy
- Persuasion
- Platform
- Quality

All results land well under the 180-second curl max-time.

## Observational evidence

Session: COS MCP clarify-integration content-scoring phase (2026-05-19)

| Call type | Status | Time | Result |
|-----------|--------|------|--------|
| Single framework via MCP | 200 | 18s | Full response |
| Full (7-framework) via MCP | Timeout | 45s | "Upstream request timed out" |
| Full (7-framework) via curl | 200 | 140s | Full 7-framework JSON |

The asymmetry is diagnostic: MCP transport bottleneck, not backend degradation.

## When to apply

- `analyze_full_comms` consistently times out with "Upstream request timed out"
- Iterative COS-validated copy cycles (each iteration requires full 7-framework re-scoring)
- Production debugging where you need to confirm API health independently of MCP health
- Backend is responding (single-framework MCP calls work, or health endpoint is 200)

## When this does NOT apply

- Single-framework MCP calls are also timing out (suggests backend issue, not transport)
- Health endpoint is down or returning non-200 (suggests infrastructure or availability issue)
- You're hitting rate limits (check COS rate-limit headers in response)

## Related transport-layer pattern

The `cos-mcp` health endpoint can return 200 even when full-flow tools are silently degraded. **Do not trust MCP health alone** — always test the specific tool path you need.

Test pattern:
1. Check MCP health endpoint (quick, single-framework, typically 18s)
2. Test `analyze_full_comms` via MCP (can timeout even when health is 200)
3. Fall back to curl if MCP times out
4. Confirm health vs. full-flow separately — they're independent

## Source context

Observed during content-scoring iteration cycle in cos-mcp clarify-integration work (2026-05-19). Three consecutive `analyze_full_comms` MCP timeouts triggered investigation. Curl fallback confirmed backend health and 7-framework availability within expected 120-180s window. Grounding: 0.9 (high confidence from direct observation of transport asymmetry, concrete working solution, and reproducible condition isolation).
