---
title: COS MCP endpoint auth/timeout — fall back to local cos-personality + cos-copy skills
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.7
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-06-19
tags: cos, mcp, fallback-pattern, skill-equivalence, diagnostic, semalytics
related_entries:
  - diagnostics/2026-05-19_cos-mcp-analyze-full-timeout-direct-curl-fallback.md
  - diagnostics/2026-05-20_cos-analyze-full-payload-ceiling-502.md
---

# COS MCP endpoint auth/timeout — fall back to local cos-personality + cos-copy skills

## Pattern

When the COS MCP server at claude.ai Agent OS returns errors, do not chase the auth or upstream issue inline. Fall back to the local COS skills, which run the same framework engine and produce equivalent output without network round-trips or auth tokens.

## When this applies

Observed failures (2026-06-19, `client-project` session, AI Tinkerers profile rewrite task):

- `mcp__claude_ai_Agent_OS__analyze_content` → `Analysis failed: {"detail":"Authentication required (service key or user token)"}`
- `mcp__claude_ai_Agent_OS__analyze_full_comms` → `Full comms analysis failed: {"detail":"Authentication required (service key or user token)"}`
- `mcp__claude_ai_Agent_OS__chat` → `Upstream request timed out, please retry`

Both auth errors and upstream timeouts are session-level signals to switch path, not to retry.

## The fallback

Invoke the local skills directly via the Skill tool:

- **`cos-personality`** — OCEAN profiling, the five-axis transformation framework, Cialdini principle mapping by trait, ELM route selection, moral foundations matrix. Full skill body loads inline.
- **`cos-copy`** — De-AI fingerprint rules, six-category cliché taxonomy, em-dash density rules (≥150 body words/dash floor), `DC:` mode for anti-cliché enforcement. Loads inline.
- **`cos-analysis`** (not used in source session but available) — 4-layer content audits, frame mapping.
- **`cos-strategy`**, **`cos-platforms`**, **`cos-validation`**, domain skills (business / health / politics / culture), **`cos-ethics`** — all available locally as skills.

The local skills are slugged under `~/.claude/skills/cos-*/`. They are the documentation engine; the MCP server is the API engine. Both reference the same framework definitions.

## When this does NOT apply

- If the user explicitly requires MCP-mediated output (e.g., they want the `analyze_full_comms` JSON schema for downstream tooling), the local fallback won't produce the structured response. Surface the MCP failure and ask whether to proceed with skill-form output or to triage the MCP issue first.
- If the MCP failure is suspected to be a real product bug (not auth/timeout transient), file a bead in the appropriate beads store (likely `[project]/cos/.beads`) rather than swallowing the symptom.

## Concrete grounding

Session 2026-06-19, `client-project`, AI Tinkerers profile rewrite:

1. Called `analyze_full_comms` with full profile content → auth error
2. Called `analyze_content` with single-section content → auth error
3. Called `chat` with rewrite request → upstream timeout
4. Loaded `cos-personality` skill → received full OCEAN profiling + transformation framework
5. Loaded `cos-copy` skill → received full De-AI rules + `DC:` manifest format
6. Produced AI-Tinkerers-targeted profile rewrite with OCEAN profile (O:0.85 C:0.7 E:0.5 A:0.4 N:0.3), DC manifest, em-dash density check (1 dash / 500 body words). Delivered.

Total fallback cost: two skill loads. Zero further triage of the MCP failure was needed to complete the user task.

## Reuse heuristic

Any session that asks COS to analyze, transform, or de-AI content: try MCP first if quick (one call), but if any of (auth error / upstream timeout / 500) returns, immediately switch to local skill invocation. Do not retry the same MCP call more than once unless the user explicitly requests MCP-form output.

## Relationship to prior entries

- The 2026-05-19 entry covers `analyze_full_comms` timeouts with a **direct curl fallback** that requires a `COS_API_KEY` bearer token. That path stays valid when the user needs the structured JSON.
- This entry adds an **auth-error** failure mode the curl path can't fix (the curl path requires the same auth that the MCP is failing) and proposes a **zero-network** fallback when the user only needs the framework output, not the JSON schema.
- The 2026-05-20 payload-ceiling entry is orthogonal — that's a request-size issue, not an auth/timeout one.
