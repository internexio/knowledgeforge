---
title: Self-referential proposal rejection loop — pipeline friction signals blocked by the validator they critique
source_mode: diagnostics
novelty_type: reusable_diagnostic
grounding_score: 0.82
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-24
domain: diagnostics
topic: ops
tags: routing, classification, quality-gate
related_entries: []
---

# Self-referential Proposal Rejection Loop

## Pattern

When a pipeline generates proposals based on its own operational friction signals, and the validator that accepts/rejects proposals uses the same classification schema that the friction signals are criticizing, a self-referential rejection loop emerges. The proposals cannot pass because they describe a problem in the very schema used to evaluate them.

## Concrete Example ([project] baking pipeline, 2026-07-23)

The `project-reviewer` worker scans routing logs and detects friction patterns (wrong topic labels, rejected classification attempts). It generates LLM proposals describing the friction and suggesting fixes to the routing/classification system. These proposals route through `bake_and_route()`, which evaluates them against the same topic/tag taxonomy that the proposals are trying to fix. Because the proposals reference non-approved topics (`routing-friction`) and non-approved tags (`pipeline-observability`, `project-reviewer`), they fail schema validation and are rejected with `schema_violation`.

Result: the pipeline systematically rejects all proposals about fixing its own classification — a diagnostic blind spot where self-generated improvement signals are silenced by the defect they describe.

## Observed in

- [project] routing log `~/.claude/wiki/operations/routing-log/2026-07.md`: 3 of 4 proposals rejected in a single project-reviewer session were about fixing the routing schema
- `rejected_proposals.jsonl` (shipped 2026-07-23, [project]-o30x): makes the rejection pattern observable

## Detection

Look for:

1. High rejection rate in `rejected_proposals.jsonl` from a single worker session
2. Rejection reasons clustering on `schema_violation` with `topic` or `tags` fields
3. Proposal headlines referencing "routing", "classification", "schema", or "validator" — the same system doing the rejecting

## When This Applies

- A self-describing worker (one that analyzes the pipeline itself) generates LLM proposals
- Proposals are routed through validation gates that enforce the same taxonomy the worker is critiquing
- The worker has sufficient autonomy to produce structured output (not just debug logs)

## When This Does NOT Apply

- When rejection is due to low confidence or substance (not schema mismatch) — that's the validator working correctly
- When a single proposal fails taxonomy — only becomes a loop pattern when multiple consecutive proposals from the same worker fail the same schema check

## Resolution Approaches

**Option A — Schema-first:** When a friction signal surfaces a topic or tag that doesn't exist in the taxonomy, treat that as a taxonomy extension request, not a proposal rejection. Route to a human gate.

**Option B — Exempt self-critique:** Add a proposal classifier that detects "self-critique" proposals (proposals about the pipeline itself) and routes them to a separate queue exempt from taxonomy validation.

**Option C — Taxonomy correction loop:** After N consecutive `schema_violation` rejections from the same worker, emit a meta-signal to the operator indicating the taxonomy may need extension.

**Option D (used in this case):** Manually correct the taxonomy at the wiki-filing layer (use `ops` topic, `routing`/`classification`/`quality-gate` tags) and resubmit. This resolves the immediate instance but not the structural pattern.

## Source Context

Surfaced during [project] nightly routing-log review (2026-07-23 session), [project]-2026-07-23-routing-friction bead. The `project-reviewer` worker was attempting to file a self-critical proposal about classification schema drift; the proposal was rejected by the same validation gate it was critiquing. The pattern is structural and will recur whenever a self-analyzing pipeline grows sophisticated enough to generate proposals.
