---
title: Pre-flight cred-gap detection in /bead-build — halt + checklist or decompose, never ship dead-code stubs
source_mode: direct
novelty_type: workflow_pattern
grounding_score: 0.70
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-05-30
tags: bead-pipeline, pre-flight-checks, scope-decomposition, build-halt, orchestration
domain: orchestration
topic: multi-stage-issue-workflow
related_entries:
  - wiki/orchestration/2026-05-30_bead-tracker-workflow-pipeline-triage-decisions-build-deploy.md
  - wiki/patterns/2026-05-12_fastapi-streaming-preflight-gates.md
  - wiki/methodologies/2026-05-18_reframe-stated-scope-to-actual-goal-strategist-heuristic.md
  - wiki/methodologies/2026-05-23_vendor-swap-semantics-recalibration-audit.md
  - wiki/methodologies/2026-05-27_supervise-first-real-data-run-autonomous-loops.md
---

# Pre-flight cred-gap detection in /bead-build — halt + checklist or decompose, never ship dead-code stubs

## Pattern

Before spawning a build agent for an ISOLATED multi-file bead, run a cred-gap check: for each external service the bead's adapters depend on, verify creds plumbing exists in the project (grep for the corresponding Config dataclass + env var). For each service with NO plumbing, two options:

1. **Halt the build**, surface the gap, ask user to set up creds before re-queuing.
2. **Decompose the bead** into Phase 1a (services-with-creds + scaffolding) and Phase 1b (services-without-creds as a follow-up bead).

Option 1 is honest — Option 2 ships partial code. **Default to Option 1 when the missing-cred service is a meaningful slice of the bead's value.**

## Concrete instance (2026-05-30)

sem-tools-svo's queue entry called for 3 API adapters: GMB, Facebook Graph, Yelp Fusion. Pre-flight revealed:
- GMB: `GMBConfig` exists at `sem/core/config.py:46`, access granted ✓
- Anthropic (drafter): `AnthropicConfig` wired at `config.py:260` ✓
- Facebook Graph: NO plumbing — no `FacebookConfig`, no `FB_PAGE_TOKEN` env var, no `sem/` reference
- Yelp Fusion: NO plumbing — no `YelpConfig`, no `YELP_API_KEY` env var

User opted to halt rather than ship FB/Yelp stubs. Bead annotated with concrete checklist for re-queue. Subsequently, Yelp investigation surfaced $299+/mo pricing and a separate Chrome-MCP-based bead (sem-tools-9ay) absorbed the Yelp scope.

## When this pattern applies

- Any bead spec listing ≥2 external service integrations
- Any bead where the spec was filed weeks/months ago and credentials may have evolved since
- Any bead routed through /bead-build with **Files:** containing multiple new adapter files

## When this pattern does NOT apply

- Single-service beads (the cred check is trivial)
- Beads where the adapter is mock-only (test fixtures, no real API)
- Beads where all services share a single API key (e.g., one provider)

## Verification commands

For each external service in the spec:
1. `grep -rnE "<ServiceName>Config|<SERVICE>_API_KEY|<service_url_domain>" sem/core/config.py sem/`
2. `grep -i "<SERVICE>" .env env-example.txt 2>/dev/null`
3. Confirm the env var actually has a value (not just an empty placeholder)

If any service comes back empty, halt and surface the gap before spawning the build agent.

## Anti-pattern: shipping dead-code stubs

The temptation is to spawn the agent with "build all the adapters; the FB/Yelp ones can be stubs until creds land." This produces:

- Dead code that's hard to verify is still correct when creds arrive (no end-to-end test possible at build time)
- Schema fields written for sources that never get data
- Operator confusion (the CLI advertises capabilities that don't work)
- Increased merge surface area when the real adapter finally lands

Better: halt, file a focused follow-up bead, ship the rest cleanly.

## Bead annotation format (when halting on cred gap)

Bead notes should include:
1. Explicit `PRE-FLIGHT HALT` header with date and trigger.
2. Numbered checklist of what's needed (one item per missing service, plus any content/seed dependencies like restaurant_facts JSON in the svo case).
3. The exact env-var names + config-class names + setup script paths if any.
4. A note that the build is one-pass-ready once 1-N are in place.

This makes the bead self-contained — when the user returns, they don't need to re-derive what's missing. Build-queue entry separately annotated with `[BLOCKED-BY: external-creds]` and a pointer to the bead notes for the full checklist.

## Companion to existing patterns

Pairs with the bead-pipeline philosophy: triage verifies premise; decisions clear ambiguity; build assumes verified+approved+buildable. Pre-flight cred check is the last guard before the build agent commits API time. The check belongs in /bead-build because triage doesn't typically grep config.py for env vars — it verifies the artifact-claim premise instead.

## Adjacent: capacity for scope reduction during pre-flight

Pre-flight is also the right moment to surface and propose scope reductions if external constraints shift. In the svo instance, Yelp's pricing was discovered during pre-flight to have moved to paid-only ($299+/mo flat) — leading to dropping Yelp from svo's scope entirely and filing a follow-up bead using a different mechanism (Chrome MCP). Pre-flight is not just "are creds plumbed" but also "is the original spec still economically and operationally viable given current vendor pricing and tooling."

## Source Context

Pattern emerged 2026-05-30 during sem-tools-svo bead-build pre-flight in the `/bead-build` orchestration flow (see 2026-05-30_bead-tracker-workflow-pipeline). Grounding: one concrete instance (svo cred gaps on FB/Yelp, halt decision, checklist annotation); staleness risk = slow_decay because the pattern is workflow-specific and stale if the bead-pipeline schema changes (e.g., pre-flight hooks replaced by a different agent-handoff contract).
