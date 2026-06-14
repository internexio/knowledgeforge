---
title: Refresh-in-place dedup creates false-positive silence alarms — pin first_seen_at separately from enqueued_at
source_mode: debugger
source_session: redacted
novelty_type: reusable_diagnostic, new_pattern
grounding_score: 0.95
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-10
domain: diagnostics
topic: queue-observability-pitfall
tags: queue, dedup, ttl, observability, false-positive, schema-evolution, additive-optional, fingerprint
related_entries: [orchestration/2026-05-29_append-only-queue-fingerprint-dedup-reconcile-gc.md, architecture/2026-05-15_schema-marker-multi-producer-jsonl-contract.md, migrations/2026-05-20_idempotent-additive-column-sqlite-migrations.md]
---

# Refresh-in-place Dedup Creates False-Positive Silence Alarms — Pin first_seen_at Separately from enqueued_at

## Pattern

When an append-only queue uses fingerprint-dedup-by-replace semantics (each re-emit of the same finding REPLACES the existing envelope with one bearing a fresh `enqueued_at` timestamp, to keep still-open findings alive against a TTL backstop), any downstream consumer that groups by `enqueued_at` to answer "did we surface anything yesterday?" will see ALL entries collapsed onto today's date — producing false-positive "trailing empty days" alarms even when the queue is continuously full of relevant findings.

## Concrete Grounding

Verified 2026-06-09 in [project]'s `iteration_loop`:

- `orchestra.enqueue_proposal()` collapses any prior same-fingerprint envelope and writes a fresh one with `enqueued_at = _utc_now()`. Docstring: "in-place refresh, drop later dups ... refreshing enqueued_at keeps a still-open finding alive against the TTL backstop."
- `morning_silence.count_baked_proposals_per_day()` grouped by `enqueued_at` and computed "trailing empty days."
- Result: a `consecutive_empty_mornings` watchdog fired 7 days in a row while the queue continuously held 3 active baked_proposals — every day's re-emit was relabelled "today" by the dedup write.

Proof on the live queue file (`~/agent-workflow/pending-suggestions.jsonl`):
- 17 total `baked_proposal` entries across history
- All 3 surviving entries carried the SAME `enqueued_at=2026-06-09` despite originating ~weeks earlier
- The routing log (`~/.claude/wiki/operations/routing-log/2026-06.md`) showed `emitted=6` on prior days, but those emissions had been overwritten in place

## Root Cause Chain

1. **The dedup write refreshes `enqueued_at`** (correct for TTL semantics): keeps a still-open finding alive against expiry.
2. **Consumer groups by `enqueued_at`** to compute "activity per day": reasonable for a timestamp meant to mark when a finding entered the queue.
3. **Gap:** The timestamp has **dual semantics** — "when did it enter the queue?" (first appearance, never changes) vs. "when was it last touched?" (refreshes on dedup, needed for TTL).
4. **Result:** Grouping by a "last touched" timestamp produces collapsed groups, and trailing-empty-days logic fires on false premises.

## Fix

Additive-optional schema bump: add a `first_seen_at` field stamped once at initial insert and inherited (never refreshed) through dedup. Downstream consumers read `first_seen_at` with tolerant `enqueued_at` fallback (so pre-fix envelopes still count). `enqueued_at` retains TTL-refresh semantics for the TTL backstop.

**Implementation:** In the dedup closure, when an existing envelope is matched on fingerprint:
1. BUILD A COPY of the new envelope
2. Overwrite ITS `first_seen_at` with the matched envelope's `first_seen_at`
3. Use `enqueued_at` fallback for pre-fix data: `first_seen_at = existing.get("first_seen_at") or existing.get("enqueued_at")`

Append-only consumers reading the JSONL get the correct first-sighting date without any migration script. Pre-fix envelopes self-heal on next dedup touch.

**Reference commit:** 8f0a5bb ([project]).

## When This Applies

Any append-only queue where:
1. Dedup is by fingerprint and REPLACES rather than skipping duplicates.
2. A TTL backstop or "still alive?" check needs `enqueued_at` to keep refreshing.
3. Some other consumer asks "what was newly surfaced in window W?" or "how many days have been silent?"

Examples:
- orchestra-style baked-proposal queues
- alarm-debounce queues
- open-incident tables
- any "drift-from-yesterday" reporter
- Morning briefing / daily digest systems

## When This Does NOT Apply

- Queues that don't dedup-by-replace (single-insert immutable rows). The `enqueued_at` already means first-sighting there.
- Queues with no TTL (no reason to refresh). Can use `enqueued_at` directly for grouping.
- Consumers that only ask "is this finding still open?" rather than "when did it first appear?". `enqueued_at` is sufficient.
- Queues where re-emits should change the timestamp (e.g., alert flap detection where "touched at N" is the signal). In that case, separate concerns: `first_seen_at` for forensics, `last_touched_at` for TTL, and choose the right one for your consumer query.

## Diagnostic Signal

**False-positive "consecutive empty days / trailing silence" alarms on a queue that DOES contain active entries** is the smoking gun. Reproduction:

1. Count rows by `enqueued_at` date for the last N days
2. Observe: all entries land on today
3. Conclude wrongly that yesterday-and-earlier were empty

**Verification:** Read the raw JSONL file and check whether `enqueued_at` dates are all recent (indicating in-place refresh) while entry count is healthy (indicating the queue isn't actually empty).

## Root-Cause Checklist

When "consecutive empty mornings" alarms fire on a healthy queue:

- [ ] Read the raw queue file (`pending-suggestions.jsonl`, `open_incidents.json`, etc.)
- [ ] Check entry count: is it healthy? (If zero, silence is real; skip to infra.)
- [ ] Check `enqueued_at` distribution: do all surviving entries have today's timestamp?
- [ ] Check existing entry creation dates: are there entries with logical creation dates weeks ago?
- [ ] Trace the consumer's grouping logic: does it use `enqueued_at`?
- [ ] Trace the producer's dedup logic: does it refresh `enqueued_at`?
- [ ] If all above are true, apply the fix: add `first_seen_at` as additive-optional.

## Related Entries

- [[append-only-queue-fingerprint-dedup-reconcile-gc]] — the dedup mechanism itself; this entry covers the observability pitfall created by that mechanism.
- [[schema-marker-multi-producer-jsonl-contract]] — multi-producer design for append-only queues.
- [[idempotent-additive-column-sqlite-migrations]] — the schema-evolution pattern used to add `first_seen_at`.

## Source Context

Root-cause analysis during [project] iteration-loop debugging (2026-06-09). A `consecutive_empty_mornings` watchdog had fired 7 days in a row, indicating no activity across an entire week. Manual inspection revealed the queue held 3 actively-updated baked_proposals, all bearing identical `enqueued_at=2026-06-09` despite being weeks older. The producer (`orchestra.enqueue_proposal`) was correctly implementing dedup-by-refresh to keep findings alive against TTL expiry, but the consumer (`morning_silence.count_baked_proposals_per_day`) was grouping by `enqueued_at`, collapsing all entries onto the refresh date. The fix is a schema evolution: pin the original timestamp as `first_seen_at` and use it for consumer grouping instead.
