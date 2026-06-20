---
title: Verify MCP tool response shape live before writing parsing code — spec assumption costs revision passes
source_mode: critic
novelty_type: reusable_diagnostic, transferable_framework
grounding_score: 0.9
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-06-10
domain: integration
topic: mcp
tags: mcp, integration, parsing, verification, spec, defensive-coding, empirical, live-testing, shape-discovery
related_entries:
  - patterns/2026-05-22_spec-to-implementation-gap-distinct-review-pass.md
  - diagnostics/2026-05-23_live-smoke-as-verification-gate-mocks-pass-prod-breaks.md
  - diagnostics/2026-05-25_http-adapter-silent-failure-integration-test-mandatory.md
  - patterns/2026-05-14_claude-cli-structured-output-vs-result-routing.md
revises: null
superseded_by: null
---

# Verify MCP tool response shape live before writing parsing code — spec assumption costs revision passes

## Problem

When integrating with an MCP server tool, the tool's **response shape is NOT inferable** from:
- (a) tool name
- (b) tool description  
- (c) argument schema

Tool authors frequently format responses as **human-readable plain text** rather than structured JSON — even when arguments are accepted as JSON. Writing a parser against speculated JSON shapes will fail at runtime against the actual response, producing silent no-ops or catastrophic mis-parsing.

The cost manifests as multiple revision passes to a spec: v1 makes assumptions, v2 discovers the assumptions are wrong, v3 re-architects around the actual shape.

## Concrete grounding — jyku.3 PDIA v2 delta review (2026-06-09)

During kf-critic delta review of [project] `jyku.3` (Step-4 executor PDIA v2):

The spec assumed orchestra's `list_tasks` and `get_task` MCP tools returned **structured JSON**. The proposed parser `_parse_first_task(raw: str)` was written to tolerantly handle three speculative JSON shapes:
- JSON array: `[{...}, {...}]`
- Keyed object: `{"tasks": [...]}`
- Single-task dict: `{...}`

Live invocation against the running `com.orchestra.server` MCP at `localhost:8765/sse` revealed the **actual response shapes**:

### `list_tasks` response (assumed JSON, actual plain text)

```
Tasks (1 of 3):
  [199d8c70] P3 pending    claude   No-op — this is a smoke test of the orch...
```

### `get_task` response (assumed JSON, actual plain text with key=value lines)

```
Task 2fd4855a:
  Spec: echo 'jyku.2 verify ...
  Status: pending
  Priority: 3
  Backend: claude
  Attempts: 0/3
  Created: 2026-06-09 19:42:30.222692
```

**All three speculated JSON shapes were wrong.** The spec would have produced a silently no-op daemon: every poll returns `None` → no work ever drained → production completely broken, surfaced only by integration tests.

### Cost of shape discovery

The spec went through **v1 → v2 → v3 revisions**. The third revision was driven **entirely by the live-verification finding**:
- v1: assumed JSON, wrote tolerant parser for three shapes
- v2: discovered actual shape via live invocation, completely rewrote parser with regex extraction
- v3: abandoned MCP for reads (writes already went through SQLite → abstraction layer was half-bypassed), migrated to SQLite-symmetric design (single coupling boundary, no redundant abstraction)

Without live verification at the spec stage, the parsing bug would have shipped, been discovered in integration tests, and required a hotfix mid-execution.

## Fix: Live-verification protocol before parsing code

Before writing parsing code against an MCP tool result:

1. **Invoke the tool live** using the host's MCP client (e.g., `mcp.client.sse` or the orchestrator's ClientSession) with realistic arguments.
2. **Print the raw `result.content[i].text` payload** to inspect the shape directly.
3. **Determine the actual format**: is it JSON-parseable? If not, what's the human-readable structure and can you regex/parse it stably?
4. **Write the parser against the verified shape.** Comment with the verification date so future drift is traceable:
   ```python
   # Verified 2026-06-09 against com.orchestra.server:8765
   # Response format: plain text, "Task <id>:\n  Key: value\n  ..."
   # Do not assume JSON structure; this tool returns formatted text.
   def parse_task_status(raw: str) -> Optional[TaskStatus]:
       # regex extraction, not JSON parsing
   ```

## Single-coupling-boundary corollary

In the jyku.3 case, the alternative was **dropping MCP from the read path** because writes already bypassed it (went straight to SQLite). The principle: **when reads AND writes both bypass an abstraction, don't half-abstract.**

Evaluate whether the MCP layer is actually needed for integration, or whether a symmetric design (both read and write through a single boundary) is cheaper.

## When this applies

- Any MCP integration where **production code parses tool responses programmatically**
- The **tool author and the consumer are different parties** (less predictable response contracts)
- **Schema-as-documentation is the only contract** (no formal schema validation or type-generated clients)
- Especially relevant for:
  - orchestra/gastown orchestration tools
  - Claude.ai Agent OS consumer agents
  - Third-party MCP servers consumed by automation code (not interactive Claude)

## When this does NOT apply

- **Interactive consumption** where Claude reads the formatted text directly in conversation — plain-text formatting is preferable for human-in-the-loop
- MCP tools with **strict schema-validated responses** (extremely rare in practice; most tools document expected shape but don't enforce it at wire-format level)
- Tools where the spec AND implementation come from the same author team with tight coupling (e.g., co-located in same codebase) — the spec authors have already verified the integration works

## Anti-patterns

- **Writing parser code before invoking the tool** — the speculative JSON shape is guesswork until you see the actual wire format
- **Trusting tool descriptions alone** — "Returns task info" doesn't specify JSON vs plain text vs custom format
- **Testing parsers against hand-written fixtures** — fixtures tend to match your assumptions; real live data reveals shape drift
- **Assuming success shape from a mocked/stubbed MCP client** — mocks can return anything; real servers emit their actual format
- **Skipping the verification step in code review** — "looks reasonable" is not verification; live invocation is the only ground truth

## Diagnostic signal

A spec or PR that:
- Introduces parsing code for an MCP tool result
- Contains NO evidence of having invoked the tool live (no `mcp_client` call, no response snapshot, no date comment)
- Features "tolerant" or "speculative" shape handling (e.g., "handles three possible JSON shapes") — usually indicates guessing rather than grounding

## Related patterns

- **Spec-to-implementation gap (2026-05-22)**: Addresses spec-code fidelity. This pattern is earlier in the pipeline — it catches shape assumptions before they're even implemented.
- **Live-smoke as verification gate (2026-05-23)**: Emphasizes empirical testing AFTER code is written. This pattern applies BEFORE parsing is written — it's a discovery gate, not a validation gate.
- **HTTP adapter shape contracts (2026-05-25)**: Covers vendor API shape drift after deployment. Similar principle (shapes change, verify empirically) but applied at integration-test scope.
- **Claude CLI structured-output vs result routing (2026-05-14)**: Addresses Claude CLI response routing surprises — another case where response shape assumptions cost a revision pass.

## Source Context

Discovered during [project] jyku.3 PDIA v2 delta review (kf-critic mode, 2026-06-09). The executor spec assumed orchestra MCP tools returned structured JSON; live invocation revealed plain-text responses. The gap forced three revision passes and ultimately led to abandoning the MCP read layer entirely in favor of symmetric SQLite coupling. The grounding score of 0.9 reflects direct observation in a concrete arena ([project] orchestrator), with clear causality between the shape discovery and the revision passes. The pattern generalizes to any third-party MCP integration where response parsing is on the critical path.
