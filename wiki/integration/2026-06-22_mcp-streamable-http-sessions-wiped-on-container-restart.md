---
title: MCP Streamable-HTTP sessions are wiped on container restart
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.7
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-06-22
domain: integration
topic: mcp-protocol
tags: mcp, api, deployment, sidecar, empirical
related_entries:
  - diagnostics/2026-06-19_cos-mcp-auth-timeout-fallback-to-local-skills.md
  - diagnostics/2026-05-19_cos-mcp-analyze-full-timeout-direct-curl-fallback.md
  - patterns/2026-06-09_mcp-sse-starlette-class-based-asgi-endpoint.md
  - patterns/2026-06-10_mcp-tool-response-shape-live-verification-before-parsing.md
  - diagnostics/2026-05-21_server-side-state-outlives-client-fixes-saas-wrappers.md
---

# MCP Streamable-HTTP sessions are wiped on container restart

## Problem

MCP servers using the Streamable HTTP transport keep per-client session
state in-memory. When the container hosting the MCP server restarts
(deploy, OOM kill, host reboot), all sessions are lost. Clients
connected at the time receive HTTP 404 wrapping a JSON-RPC error:

```json
{"jsonrpc":"2.0","id":"server-error","error":{"code":-32600,"message":"Session not found"}}
```

## Critical UX gotcha — Claude.ai connector "Refresh tools"

On Claude.ai Agent-OS connectors specifically: the **"Refresh tools"**
button in the connector settings does NOT re-establish the session. It
uses the cached (now-invalid) session ID to re-fetch the tool list, gets
the same Session-not-found error, and silently fails.

Only a full **Disconnect + Reconnect** (or Remove + Re-add when
Disconnect is grayed out) triggers a new MCP `initialize` handshake → new
session ID → working tool calls.

## Symptoms that disambiguate this from auth/network problems

1. The MCP `/health` endpoint returns 200 (server is up).
2. Some OTHER client's tool calls work — visible as 200/202 traffic in
   server access logs at the moment of failure.
3. YOUR client's `POST /mcp` consistently 404s with the
   `Session not found` payload — your session is the stale one.

Server-side logs to look for (uvicorn / equivalent):

```
172.20.0.1:NNNNN - "POST /mcp HTTP/1.1" 200 OK         # another client's working session
172.20.0.1:MMMMM - "POST /mcp HTTP/1.1" 404 Not Found  # your stale session
```

## Resolution paths (priority order)

1. **Force reconnect on the client side.** Disconnect+Reconnect in
   connector UI, or restart the local agent process if it manages its
   own MCP client.
2. **If Disconnect is grayed out** (Claude.ai web bug observed during
   this grounding session), Remove the integration entirely and Re-add
   it.
3. **Server-side fix.** Persistent session storage (Redis, SQLite)
   survives restarts — implement if frequent redeploys are expected.

## When this applies

Any MCP server using Streamable HTTP transport (the current standard)
deployed in a stateless container (Docker, Kubernetes, Lambda, etc.)
without persistent session storage.

## When this does NOT apply

- MCP servers using **stdio** transport — one local process per client,
  no shared session state to lose.
- MCP servers with **Redis/SQL-backed session persistence** configured —
  state survives restarts.

## Concrete grounding

cos-yb1i e2e verification (2026-06-22, `[project]` session). The COS MCP
container (`semalytics/cos/mcp` at `mcp.semalytics.io`) was redeployed by
a CI cycle. Subsequent claude.ai Agent-OS tool calls returned the
`Session not found` error. Server logs showed simultaneous successful
sessions from other clients. Operator's claude.ai connector showed
Disconnect grayed out; Remove + Re-add unblocked it.

Note: in this session's case the issue manifested AS the cos-yb1i auth
bug originally reported, but the `Session not found` was a separate,
transport-layer issue exposed only during the verification attempt. Two
defects, one symptom surface — a recurring pattern with MCP triage.

## Relationship to prior entries

- The 2026-06-19 entry covers auth/timeout failures with a local-skills
  fallback. The Session-not-found failure looks similar at the call
  site (tool call returns an error) but the wrong-fix path diverges:
  reconnecting fixes session-loss, not auth-failure.
- The 2026-05-21 SaaS server-side state entry generalizes the same
  shape: encrypted/private server-side state can outlive every
  client-side fix. Streamable HTTP session loss is the inverse —
  ephemeral server-side state dies under the client's still-valid
  identity. Both classes are "client UI lies about what's recoverable."
