---
title: TTL drain — source-lifecycle-gated proposal expiry without active cleanup
source_mode: strategist → builder
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-08-03
domain: orchestration
topic: queue-pattern
tags: decay, grounding, routing, quality-gate
related_entries: []
---

# TTL Drain — Source-Lifecycle-Gated Proposal Expiry Without Active Cleanup

## Context

In a baking pipeline where proposals (baked envelopes) derive from source beads, a closed source bead should cause derived proposals to stop being refreshed. If the pipeline calls `refresh_envelope_enqueued_at(raw)` on cache hits to keep active proposals from expiring, this call must be skipped when the source bead is closed — otherwise a stale proposal outlives its source indefinitely.

## The TTL Drain Pattern

Instead of actively retiring derived proposals (which requires tracking all proposal IDs per bead, a complex join), skip the `enqueued_at` refresh when the source is closed. The proposal's TTL clock continues ticking from its last refresh, and the entry naturally expires from the queue.

```python
def _source_bead_is_closed(raw: dict) -> bool:
    """Return True if this envelope's source bead is closed."""
    bead_id = raw.get("bead_id")
    if not bead_id:
        return False
    status = bd_update.get_status(bead_id)  # error-tolerant: returns "unknown" on failure
    return status == "closed"


# In bake_and_route, at the cache-hit branch (~line 384):
if _source_bead_is_closed(raw):
    return PipelineResult(
        stage="stage_0",
        outcome="rejected",
        trigger="source_bead_closed",
        # No refresh — TTL drains naturally
    )
# else: normal cache hit, refresh enqueued_at
refresh_envelope_enqueued_at(raw)
```

## Companion: Error-Tolerant Status Lookup

The `get_status(bead_id: str) -> str` helper returns the bead's status string or `"unknown"` on any error (subprocess failure, bd not found, JSON parse error). This prevents a bd connectivity blip from incorrectly blocking the refresh path — an `"unknown"` status is treated as `not closed`.

```python
def get_status(bead_id: str) -> str:
    try:
        result = subprocess.run(
            ["bd", "show", bead_id, "--json"],
            capture_output=True, text=True, timeout=5
        )
        data = json.loads(result.stdout)
        return data[0]["status"]
    except Exception:
        return "unknown"
```

## When This Applies

- A pipeline that produces derived artifacts (proposals, summaries, cache entries) from source entities with their own lifecycle
- The derived artifact has a TTL / enqueued_at clock that is refreshed on each hit to keep it active
- The source entity's lifecycle (open/closed/deleted) should govern whether the derived artifact continues to live
- Queue entries are deduplicated on fingerprints; the same fingerprint can re-appear from stale signals even after the source is invalidated

## When This Does NOT Apply

- When proposals must be retired immediately on source closure (latency requirement). TTL drain has up to one TTL period of lag.
- When downstream consumers should not receive expired proposals (add an active retirement pass instead, or reduce TTL significantly).
- When the source entity doesn't have a queryable status (no bd or equivalent).
- When the derived artifact's freshness is independent of source lifecycle (e.g., cached database query results where the row still exists after being "closed" in a metadata sense).

## Trade-offs vs. Active Retirement

| Aspect | TTL Drain | Active Retirement |
|--------|-----------|------------------|
| Implementation | Trivial (one status check per cache hit) | Complex (scan all proposals per bead, track proposal IDs per bead) |
| Lag to expiry | Up to 1 TTL period | Near-zero |
| Risk of cleanup bugs | None (just don't refresh) | Yes (missed entries, double-retire, bloom-filter cascades) |
| Best when | TTL is short, lag is acceptable | Immediate expiry required |
| Operational overhead | Status query per hit (~1ms for error-tolerant bd call) | Full table scan + update sweep per closure event |

## Grounding

Implemented 2026-08-02 in `[project]/iteration_loop/baking_pipeline.py` (bead [project]-4z47, commit a1ecfcf). The decision was reached via explicit trade-off analysis against an "active-retirement helper" option during the review of the TTL reset trap (diagnostic 2026-07-24_ttl-reset-trap-cache-hit-refresh-immortal-queue-entries.md).

Test coverage: `test_baking_pipeline.py` — 3 unit tests covering `_source_bead_is_closed` True/False paths and `bake_and_route` closed-bead rejection. Companion: `bd_update.get_status()` with error-tolerant fallback tested against subprocess timeout, JSON parse error, and missing bead cases.

## When This Applies

Source-derived proposal pipelines where:
- Proposals are fingerprint-deduplicated
- The same fingerprint can regenerate from stale signals after source closure
- TTL expiry is the intended cleanup mechanism, not queue size
- A short TTL (hours to days) makes lag acceptable

## When This Does NOT Apply

- Immediate expiry required (minutes). TTL drain's lag is too long.
- No queryable source status (can't check if source is closed).
- Derived artifact is independent of source lifecycle.

## Source Context

[project] iteration-loop baking-pipeline (2026-08-02). Emerged from trade-off analysis: "TTL drain" (passive, no cleanup code) vs "active-retirement helper" (active, scan all proposals per bead, track IDs). The TTL drain approach avoids the cleanup-bug surface while accepting up-to-TTL lag. Grounded in working code with test coverage; verified via integration tests on cache-hit paths.

Related diagnostic: 2026-07-24_ttl-reset-trap-cache-hit-refresh-immortal-queue-entries.md (the problem this pattern solves).
