---
title: Count by the refreshed field, not the preserved one, when measuring producer liveness on a dedup-in-place queue
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-12
domain: diagnostics
topic: liveness
tags: scheduling, grounding, confidence
related_entries: [diagnostics/2026-06-10_refresh-in-place-dedup-false-positive-silence-alarms.md, orchestration/2026-05-29_append-only-queue-fingerprint-dedup-reconcile-gc.md, methodologies/2026-05-29_dormant-subsystem-forensics-check-supervision-first.md]
---

# Count by the Refreshed Field, Not the Preserved One, When Measuring Producer Liveness on a Dedup-in-Place Queue

## Rule

When building a silence/heartbeat detector over a dedup-refresh queue, count by the **REFRESHED field**, not the preserved one. The refreshed field is the actual "the producer touched this envelope today" signal. The preserved field is meaningful for downstream consumers but useless as a liveness probe — by design, it doesn't move.

**Fallback semantics:** Prefer the refreshed field; fall back to the preserved field only when the refreshed one is missing (legacy/malformed envelopes). Not the other way around.

## Problem

A common pattern: a producer writes envelopes to an append-only JSONL queue with dedup-in-place — if a re-emitted envelope matches an existing fingerprint, the writer REPLACES that envelope rather than appending. The replacement typically updates one timestamp (e.g. `enqueued_at` = now) while PRESERVING another (e.g. `first_seen_at` = original surfacing time, untouched across re-emits). That preservation is intentional so downstream consumers can ask "when did this finding first appear?" without the answer drifting to today on every refresh.

A silence detector then walks the queue and counts how many envelopes "happened today" to detect a stalled producer. The trap: if the detector groups by the PRESERVED field (`first_seen_at`), a perfectly healthy producer that recycles the same N stable findings nightly produces zero new `first_seen_at` dates after the first surfacing, and the detector false-fires "no activity in N days" — conflating *no new findings* with *producer broken*.

## When This Applies

- Any silence detector over an append-only queue whose writer dedups in place.
- Health watchdogs that count "events per day" against a producer that may legitimately re-surface the same findings indefinitely.
- State files where producer presence is detected via timestamp grouping.
- Morning briefing / daily digest systems that need to distinguish "producer ran today" from "producer novelty today."

## When This Does NOT Apply

- Queues that append (no dedup) — every emission creates a new envelope; any field works for grouping because each envelope is per-emission.
- Detectors that want "novelty surfaced today" (NOT "producer ran today"). For that question, the preserved field IS correct — the question itself is different from liveness.
- Producers that always emit new findings (no recycling) — both fields drift together; the choice is moot.

## Edge Case: "Producer Ran But Found Nothing"

Even counting by the refreshed field, a fully-clean producer run (no envelopes touched at all) produces no refresh activity for that day. The detector still false-fires. Distinguishing "producer up" from "producer novelty" requires an **INDEPENDENT producer-heartbeat signal:** a scheduler-ran-today marker, a routing-log mtime, or a separate per-run audit envelope. The dedup-refresh queue alone cannot answer both questions.

## Concrete Grounding ([project], 2026-06-12)

`iteration_loop/orchestra.py` `enqueue_proposal` collapses same-fingerprint envelopes in place, refreshing `enqueued_at` while preserving `first_seen_at`. `iteration_loop/morning_silence.py` `count_baked_proposals_per_day` originally grouped by `first_seen_at` (with `enqueued_at` as fallback). Once wiki-linter hit its steady-state of 3 stable findings, the detector saw 0 baked envelopes per day past first_seen_at and tripped `consecutive_empty_mornings` on June 11. The fix (commit 1c6075c) flipped the preference order to `enqueued_at` first; the 571-test suite stayed green, the bug-enshrining test `test_first_seen_at_overrides_refreshed_enqueued_at` was replaced with `test_steady_state_loop_does_not_false_fire` mirroring the real Mini jsonl shape (first_seen=long-ago, enqueued=yesterday → streak=0).

## Diagnostic Signal

**False-positive "consecutive empty days / trailing silence" alarms on a queue that DOES contain active entries** is the smoking gun. Reproduction:

1. Count rows by the preserved-field date for the last N days
2. Observe: all entries land on their original insertion date
3. Conclude wrongly that no activity has occurred since
4. Verify: read the raw JSONL file; check whether the refreshed-field dates are all recent (indicating in-place refresh) while entry count is healthy (indicating the queue isn't actually empty)

## Related Patterns to Link

- `[[refresh-in-place-dedup-false-positive-silence-alarms]]` — the concrete diagnostic and schema fix; this entry provides the **decision rule** that guides field selection.
- `[[append-only-queue-fingerprint-dedup-reconcile-gc]]` — the dedup mechanism itself.
- `[[dormant-subsystem-forensics-check-supervision-first]]` — when a liveness detector false-fires, check the producer's supervision layer first.

## Source Context

Extracted as a transferable framework during [project] iteration-loop silence-detector field-choice analysis (2026-06-12). The rule distills the lesson from the 2026-06-10 concrete diagnostic into a reusable heuristic: when you have a dedup-in-place queue with dual-semantic timestamps, your liveness detector must count by the **moving** field, not the **static** one. This rule applies to any queue with the same structure, independent of the producer or consumer implementation details.
