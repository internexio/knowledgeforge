---
title: MCP-over-SSE Starlette routing — use class-based ASGI endpoint, not function
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.95
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-06-09
domain: integration
topic: mcp-protocol
tags: mcp, api, asgi, starlette, sse, http-response-lifecycle
related_entries:
  - patterns/2026-05-18_composite-vs-atomic-mcp-tool-design.md
  - infrastructure/2026-05-18_editable-venv-mcp-server-installation.md
---

# MCP-over-SSE Starlette Routing — Use Class-Based ASGI Endpoint, Not Function

## The Problem

When wiring a Python MCP server to expose an SSE transport via Starlette (`mcp.server.sse.SseServerTransport` + Starlette routes), the official SDK docstring example shows:

```python
async def handle_sse(request: Request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())
    return Response()  # SDK says: "to avoid NoneType error"
```

This pattern is wrong for any real client. The transport's `connect_sse` spawns an `EventSourceResponse` inside an anyio task group that writes the full HTTP response (status + body) via the ASGI `send` channel. By the time the `async with` context exits, `http.response.start` and body have already been delivered.

Starlette's `request_response` decorator then awaits `Response()(scope, receive, send)` — which sends a **SECOND** `http.response.start` message. Uvicorn's h11 layer rejects this with:

```
RuntimeError: Unexpected ASGI message 'http.response.start' sent, after response already completed.
```

Client-side this surfaces as `httpx.ReadError` mid-stream during JSON-RPC `initialize`, killing the whole exchange. Every MCP-over-SSE client hits this unless the routing is fixed.

## The Fix

Make the SSE endpoint a class instance with `__call__`, not an async function. Starlette's `Route` class inspects the endpoint at construction time:

```python
if inspect.isfunction(endpoint) or inspect.ismethod(endpoint):
    self.app = request_response(endpoint)   # Wraps in Response() call
else:
    self.app = endpoint                      # Used as raw ASGI app
```

A class instance bypasses `request_response` entirely. The transport remains in sole control of the HTTP response lifecycle.

### Working Pattern

```python
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from mcp.server.sse import SseServerTransport

sse_transport = SseServerTransport("/messages/")

class _SseAsgiApp:
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return
        async with sse_transport.connect_sse(scope, receive, send) as streams:
            await server.run(streams[0], streams[1], server.create_initialization_options())

sse_asgi_app = _SseAsgiApp()

routes = [
    Route("/sse", endpoint=sse_asgi_app, methods=["GET"]),
    Mount("/messages/", app=sse_transport.handle_post_message),
]
```

**Key details:**

- POST handling uses `Mount` because `handle_post_message` also writes its own ASGI response (mcp 1.4.x lines 247–249 of `mcp.server.sse`). `Mount` delegates the ASGI cycle without wrapping.
- Why not use `Mount("/sse")`? A mount with prefix `/sse` (no trailing slash) triggers a 307 redirect `/sse` → `/sse/`, which breaks existing clients hardcoded to `GET /sse`. The `Route` + class-endpoint combination preserves the exact path.

## When This Applies

- Any Starlette-based MCP server using `SseServerTransport`
- Verified against mcp 1.4.x and starlette 0.41.x on uvicorn 0.32.x
- The `request_response` behavior in Starlette is stable across at least 0.30–0.41 (unlikely to change as it's core routing logic)

## When This Does NOT Apply

- Pure stdio MCP servers (no HTTP transport)
- Servers using only the streamable-HTTP transport (a later MCP addition)
- Starlette WebSocket endpoints (entirely different lifecycle)
- Non-Starlette ASGI frameworks (FastAPI does the same `request_response` wrapping; pattern applies; others vary)

## Grounding

**Discovered and fixed in:** claude-orchestra commit 2b9d249 (claude-orchestra-l3d bead).

**Verification:**

1. **Code inspection:** Read mcp 1.4.x source at `.venv/lib/python3.11/site-packages/mcp/server/sse.py` (lines 122–199 `connect_sse`, lines 201–249 `handle_post_message`).

2. **Reproduction:** End-to-end test with uvicorn server + `mcp.client.sse` client:
   - Before fix: h11 `RuntimeError` on stderr, `httpx.ReadError` on client
   - After fix: clean connection, all RPC calls succeed

3. **Regression tests:** Three tests added in `tests/test_http_server.py`:
   - `TestSseRoutingShape` × 2 structural tests
   - `TestSseEndpointDoesNotDoubleWrite` × 1 live uvicorn integration test
   - All 366→375 tests pass

4. **Manual verification:** Manual repro of `initialize() + list_tools()` returns 22 registered tools without raising exceptions.

## Source Context

Discovered during MCP-over-SSE integration for claude-orchestra. Initial implementation used the SDK's docstring example (function-based endpoint). Integration tests against a real uvicorn + mcp.client.sse client failed with `httpx.ReadError` mid-initialize. Root cause: double `http.response.start`. Refactored endpoint to class-based ASGI app, which bypasses Starlette's `request_response` wrapper. All integration tests now pass. Pattern is now the canonical approach for any Starlette MCP-over-SSE server.
