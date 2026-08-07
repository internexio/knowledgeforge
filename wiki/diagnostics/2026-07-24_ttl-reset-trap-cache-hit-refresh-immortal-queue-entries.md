---
title: TTL reset trap in cache-hit refresh paths makes queue entries immortal
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-24
domain: diagnostics
topic: queue-observability-pitfall
tags: cache, grounding, measurement-logic, workflow-discipline
related_entries: []
---

# TTL reset trap in cache-hit refresh paths makes queue entries immortal

## Anti-pattern: Cache-hit paths that refresh TTL timestamps make entries immortal

### What happened (grounding)

The [project] baking pipeline (`iteration_loop/baking_pipeline.py`) has a 7-day TTL on pending proposals. The TTL mechanism exists and works correctly:

- `orchestra.py:28`: `DEFAULT_TTL_SECONDS = 7 * 86400`
- `morning_briefing.py:116-123`: TTL filter drops expired entries on read

However, the cache-hit path at `baking_pipeline.py:386-417` calls `orchestra.refresh_envelope_enqueued_at(fingerprint)` on every cache hit. This RESETS the `enqueued_at` timestamp to now, restarting the 7-day TTL clock.

**Consequence:** If a worker (e.g. project-reviewer) re-generates the same proposal headline for a CLOSED bead every night (because the LLM reads stale signals), the envelope's TTL never expires. The proposal becomes immortal — it will surface in the morning brief indefinitely, even after the underlying bead is closed. This was documented as bead `[project]-4z47`.

The `reconcile_proposals` path does NOT help: it only retires fingerprints absent from the worker's current `live_fingerprints` set. Since the LLM re-generates the same headline from stale signals, `live_fingerprints` keeps it alive.

### Root cause pattern

When a cache-hit path calls a "refresh" operation (reset timestamp, extend lease, update last-seen), it breaks the TTL's intent: entries that would naturally expire are artificially kept alive. This is the **TTL reset trap**: the system appears to have expiry logic, but the cache-hit refresh defeats it for any entry that generates regular cache hits.

### When this occurs

- Append-only queues or caches with TTL expiry
- Workers that generate proposals by reading signals (not just re-querying a fixed set of items)
- Cache-hit paths that call any variant of "refresh last-seen / reset enqueued_at / extend lease"
- LLM-based workers where the same headline can be re-generated from stale signals after the source bead is closed

### The fix pattern

The cache-hit refresh should be conditional: only refresh `enqueued_at` if the source record is still valid/live. For bead-sourced proposals: add a bead-status pre-check before the cache-hit short-circuit. If `source_beads_issue_id` resolves to a closed bead, return rejected without calling `refresh_envelope_enqueued_at` — the envelope will then naturally expire within one TTL window.

Alternative: separate the "this is a fresh proposal" refresh from the "this source is still valid" check. Do not conflate cache-hit (proposal already baked) with source-still-valid (should still surface).

### When this does NOT apply

- Caches where the source data is always live (e.g. caching a database query result — the row still exists, so refreshing the cache is correct)
- TTL used purely as a memory budget (evict stale entries to free space) rather than as a validity signal — refreshing on access is correct in that case
- Non-LLM workers where live_fingerprints is the authoritative source of truth for what's currently valid (reconcile_proposals handles this correctly)

### Diagnostic signal

"Proposals for work we already did keep showing up in the morning brief." Check whether the cache-hit path calls any refresh/extend operation. If yes and the source records can be closed or invalidated, this anti-pattern is likely the cause.

## When This Applies

- Queue-based proposal systems with TTL expiry
- Any workflow where LLM-generated cache keys can be re-produced after their source is invalidated
- Morning-brief / notification surfaces that de-duplicate on cached fingerprints

## When This Does NOT Apply

- Pure database caches where cache-hit refresh is appropriate (the underlying data is still valid)
- Non-proposal workers that don't re-generate from stale signals
- Queues where the refresh gate is upstream of the LLM, not downstream

## Source Context

Documented during [project] overnight 2026-07-23 iteration-loop review. The pattern emerged from `[project]-4z47` (bead: bead-status pre-check before cache-hit refresh).

Reference: `docs/planning/[project]-4z47-proposal.md` in [project] repo.
