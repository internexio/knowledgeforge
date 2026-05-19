---
title: Composite vs atomic MCP tool design for agent and CRM integrations
source_mode: strategist
novelty_type: transferable_framework
grounding_score: 0.75
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-18
tags: mcp, api, latency, token-cost, empirical
related_entries: []
---

# Composite vs atomic MCP tool design for agent and CRM integrations

## Pattern

When designing MCP tools that integrate with CRMs or any agent workflow, prefer ONE server-orchestrated composite tool over MULTIPLE atomic tools that the client must chain.

## When This Applies

- User's job-to-be-done requires 3+ atomic steps to produce a single output (e.g. profile audience → score draft → suggest rewrites → format output)
- The integration target is an LLM agent (Claude Desktop, Claude Code, ChatGPT MCP connectors) or a CRM/agentic platform
- You control both the MCP and the backend it proxies to

## When This Does NOT Apply

- Atomic tools that users genuinely call standalone (e.g. simple `get_templates`, `health_check`)
- Cases where the orchestration belongs in the user's workflow (e.g. user explicitly wants to inspect intermediate results, fork, iterate)
- Backend lacks an orchestration endpoint and adding one would block faster shipping

## The Three Forces

### 1. Schema Budget

Every MCP tool description is loaded into the model's context EVERY turn. With ~15+ tools, tool-selection reasoning degrades. Hard cap: ~15 tools per MCP server. Each new tool must justify the slot.

### 2. Round-Trip Latency

N atomic tools = N HTTP round-trips. A composite endpoint runs orchestration in-process, often with `asyncio.gather` for parallelizable sub-steps. Empirically: composite tool with internal Anthropic call + 2 parallel analyzers = ~45s vs 60–90s if chained from MCP.

### 3. Dev Friction

No CRM dev or agent will reliably chain 5 tools to do one job. They will bounce, or worse, build a buggy chain on their side. The composite call matches how agents actually consume the data.

## Backend Architecture (The Not-Obvious Part)

The backend should expose BOTH the atomic endpoints AND the composite endpoint. Atomic endpoints stay because they're useful for the web UI, for testing, and for power-user direct API calls.

The composite endpoint reuses the atomic endpoints' inline logic via shared `_run_*` helpers — NOT via HTTP self-loops. This keeps Anthropic prompt-caching keys stable and avoids re-auth overhead.

The MCP layer exposes ONLY the composite (and a few genuinely-atomic utilities). Schema budget preserved.

## Grounding from Session

**COS optimize_email_for_prospect tool (8 credits)** backed by `POST /analyze/optimize-email`. Composite orchestrates: audience profile → optional agent profile → draft generation → persuasion + platform scoring in parallel → consolidated rewrites + one_thing.

**Strategy session reframing:** Initially scoped 11 missing MCP tools for "parity"; reframe to "demo-driven" cut to 4 tools (one of them a composite). Schema budget went from "bloated" to "tight, ~13 tools".

**Smoke test on staging:** HTTP 200 in 47s (later improved to 5.5s with smart-default scoring policy). Production deploy verified same day.

## Counterexample / Failure Mode to Watch

If the composite's failure modes are opaque (one sub-step fails silently and returns degraded output), debuggability suffers. Mitigation: return the full sub-step breakdowns IN the composite response (don't hide them) so callers can inspect when something's off.

The `optimize_email_for_prospect` response includes the full `persuasion` + `platform` breakdowns alongside the consolidated `rewrites` for this reason.

## Cross-References

Anthropic's prompt-caching pricing (~90% reduction for cached content) is the economic backbone — composite endpoints with stable system prompts benefit disproportionately. Sister pattern: "Default policy diverges by path" (tri-state params) gives composite endpoints fast-path defaults without losing override-ability.

## Source Context

Built `optimize_email_for_prospect` MCP tool during cos-mcp-clarify-integration-phase2-3 session. Initial strategy asked for 11 new tools; reframing to demo-driven reduced scope to 4 (one composite). Empirical latency win: composite ~5–45s vs ~60–90s for chained atomic calls. Production deployed and verified same day.
