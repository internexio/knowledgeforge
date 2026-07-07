---
title: Orchestra dual-endpoint gotcha — local dev vs. remote prod have independent state
source_mode: debugger
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-03
domain: integration
topic: orchestra-mcp
tags: orchestra, mcp, endpoints, dev-vs-prod, configuration, integration-gotcha
related_entries:
  - integration/2026-06-22_mcp-streamable-http-sessions-wiped-on-container-restart.md
  - patterns/2026-06-10_mcp-tool-response-shape-live-verification-before-parsing.md
  - patterns/2026-06-09_mcp-sse-starlette-class-based-asgi-endpoint.md
  - diagnostics/2026-05-21_test-wrapped-tool-directly-narrowing-search-space.md
---

# Orchestra dual-endpoint gotcha — two independent instances, one right answer

## The problem
When writing a new tool that talks to Orchestra (autopoll daemon, custom agent, integration test, etc.), it's easy to point at the wrong Orchestra instance and see empty/stale state that doesn't match what agents actually see. There are TWO Orchestra servers running on this laptop:

- **Local dev**: `http://localhost:8765/sse` — served by `~/Scripts/claude-orchestra-dev/claude-orchestra/.venv/bin/orchestra` (PID discoverable via `lsof -i :8765`). No authentication required. Independent inbox/artifact state. Used for Orchestra development and testing.
- **Remote prod**: `https://your-orchestra-host.example.com/sse` — hosted on the semalytics infra. Bearer-authenticated. The fleet source of truth. Every `mcp__orchestra__*` tool available in a normal Claude Code session hits THIS endpoint.

The two are NOT synced. Pushing to one has zero effect on the other. Bug pattern I hit 2026-07-03:

1. Wrote `orchestra-autopoll.py` using the DEFAULT_MCP_URL of `localhost:8765` (mirroring `orchestra-telegram-bridge.py`, which also uses local).
2. Dry-run reported "0 pending" across all agents.
3. Direct `mcp__orchestra__pull_pending` from Claude Code session showed "1 pending" for [project].
4. Assumed race condition. Retested — same discrepancy.
5. Discovered via `grep orchestra ~/.claude.json` that the Claude session's MCP config targeted the remote (Bearer-authed), while my script targeted local. Two independent worlds.

## How to know which one you want
- **Agent coordination / fleet work** → remote. All Claude sessions across the fleet use this; your tool almost certainly wants to see the same state.
- **Orchestra codebase development / integration testing** → local. Test new Orchestra features without disturbing production state.
- **[project] orchestra-telegram-bridge** → local. The bridge routes callbacks via the local instance because Orchestra-server-local proxies to remote (or is the source of truth for local-orchestrated flows — verify per case).

## The credentials
- Bearer token for remote is under key `mcpServers.orchestra.headers.Authorization` in `~/.claude.json` — 64-hex characters
- [project]'s `.env` has `ORCHESTRA_API_KEY` — a different string in base64-ish form, but ALSO accepted as Bearer against remote (tested 2026-07-03). Prefer this one for [project]-hosted tools; the `.env` is the [project]-scoped credential path.
- Local server accepts requests without any auth.

## Implementation pattern (Python + mcp SDK)
```python
from mcp import ClientSession
from mcp.client.sse import sse_client

# Remote (fleet source of truth)
url = "https://your-orchestra-host.example.com/sse"
headers = {"Authorization": f"Bearer {os.environ['ORCHESTRA_API_KEY']}"}
async with sse_client(url, headers=headers) as (r, w):
    async with ClientSession(r, w) as session:
        await session.initialize()
        result = await session.call_tool("pull_pending", arguments={"agent_id": "[project]", "limit": 20})
```

The `sse_client` accepts an optional `headers=` kwarg — pass an empty dict for local, real Bearer for remote.

## Related pitfalls
- **`pull_pending` output parser**: the tool returns lines like `📋 [art_xxx] P6 from ...` with an emoji prefix. A naive `line.strip().startswith("[")` fails because strip doesn't remove the emoji. Prefer parsing the header line `Pending artifacts for '<agent_id>' (<N>):` for the authoritative count. Also verified 2026-07-03.
- **`get_queue_summary` vs. `pull_pending`**: both are read-only per Orchestra's tool docs. Neither claims artifacts. Use `pull_pending` for per-agent detail (returns actual artifact rows); use `get_queue_summary` for cross-inbox aggregate view.

## Grounding
- Reproduced 2026-07-03 while writing `orchestra-autopoll.py` — same MCP call from same Python client to different endpoints returned different results
- Verified via `lsof -i :8765` (local Orchestra PID 1823) and `~/.claude.json` grep (remote URL + Bearer)
- Confirmed both endpoints run against the same tool implementation but independent state stores
- Both credentials tested via curl-equivalent Python MCP client — both authenticated successfully against remote
