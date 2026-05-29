---
title: Append-only queue with re-running producer — fingerprint dedup + clean-run-only reconcile-GC
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.9
grounding_source: "Implemented 2026-05-29 in [project] iteration_loop/pending-suggestions.jsonl (bead [project]-w0hb, commits a5bf4b1 + af60812). Forensics: 6 stale queue lines from 2 already-fixed orphan-link findings, accumulated across 3 consecutive nightly runs (4×/2× pileup). Confirmed not re-detection (linter found 0 orphans). 12 new unit tests + 2 gating tests in test_orchestra.py and test_scheduler.py, 490/490 passing."
staleness_risk: stable
importance: 5
pinned: true
created: 2026-05-29
domain: orchestration
topic: orchestration
tags: append-only-queue, fingerprint, dedup, garbage-collection, idempotent-producer, declarative-reconcile, jsonl, fcntl, observability, schema-evolution
related_entries: [orchestration/2026-05-13_coalesce-at-enqueue-every-coalesce-gets-a-row.md, orchestration/2026-05-13_one-reconciliation-pipeline-called-twice.md, infrastructure/2026-05-13_posix-append-pipe-buf-concurrent-jsonl-writers.md, methodologies/2026-05-29_deterministic-first-debugging.md]
---

# Append-Only Queue with Re-Running Producer — Fingerprint Dedup + Clean-Run-Only Reconcile-GC

## The Pattern

A common data-pipeline shape: a **producer** (nightly scanner, linter, audit) emits zero-or-more **findings/suggestions/proposals** on each run. They land in an **append-only queue** (JSONL file, Kafka topic, table with insert-only rows). A **consumer** (morning brief, dashboard, dispatcher) reads the queue and surfaces entries to a human or downstream system.

This shape has **two distinct failure modes** that are easy to miss:

1. **Accumulation.** The producer re-emits the same still-open finding on every run. Without dedup, N runs → N copies of the same entry. The consumer shows duplicates; users see noise growing with time.
2. **Persistence after resolution.** A finding is *fixed* — the producer correctly stops emitting it on subsequent runs. But the previously-enqueued entry has no automatic retirement; it lingers in the queue until its TTL backstop fires (typically 7–14 days). The consumer keeps surfacing the now-resolved finding, "crying wolf."

The TTL backstop alone is insufficient: it's slow (days), and it doesn't address accumulation at all.

## The Two-Part Fix (one primitive: stable fingerprint)

Both failure modes are addressed by the same primitive — a **stable fingerprint** keyed to the finding's identity, not its timestamp.

`fingerprint = hash(source_id || canonical_content)`

For an orphan-link finding: `hash(worker_bd_id || rule || source_path || link_target)`. For a duplicate-file finding: `hash(detector_id || canonical_path)`. The fingerprint must be **stable across producer runs** for the same finding, and **distinct** for genuinely different findings.

### Part 1: Dedup on enqueue (fixes accumulation)

`enqueue_proposal(p)` becomes a locked read-modify-write rather than a blind append:

- Compute `fp = fingerprint(p)`.
- Read current queue under exclusive lock (fcntl LOCK_EX on JSONL, or equivalent DB lock).
- Find any existing un-expired entry with `fp`.
- If found: **refresh in place** (update `enqueued_at` to now; keep other fields), drop any further duplicates of the same `fp`.
- If not found: **append** a new entry carrying the fingerprint.
- Write back under the same lock.

Effect: a still-open finding occupies **exactly one** active queue entry regardless of how many times the producer re-emits it. Existing pre-fingerprint duplicates are self-healed on the next enqueue of the same fingerprint.

### Part 2: Reconcile-GC on producer run (fixes persistence after resolution)

After each producer **run** (not per-finding), the producer's runner calls:

`reconcile(producer_scope, live_fingerprints)`

where `producer_scope` identifies the producer's domain (a worker `bd_id`, a detector name) and `live_fingerprints` is the set of fingerprints actually emitted in this run.

`reconcile` under exclusive lock: drop any queue entries whose scope matches `producer_scope` AND whose fingerprint is NOT in `live_fingerprints`. Those are findings the producer no longer reports — they're resolved. Other scopes' entries are untouched.

**The critical gate:** reconcile MUST only run when the producer run **completed cleanly** — no short-circuit (budget cap hit mid-run), no halt, no error, no partial scan. Otherwise the "live set" is incomplete and reconcile would wrongly retire still-open findings. The runner exposes a `dispatch && reconcile && !short_circuited && !halt && error is None` gate to enforce this.

## Why This Is Safe (and the "wrong" branches are recoverable)

Proposals/findings in this shape are **derived data** — regenerable by the next producer run. If reconcile over-retires due to a missed gating condition, the next clean run re-emits and re-enqueues the still-live findings via dedup-on-enqueue. The system self-heals on the next iteration. This makes the pattern much safer than it would be for primary data; you can be aggressive with reconcile without risking irrecoverable loss.

## Schema Migration (the dedup adds a field)

`fingerprint` is added as an **optional** envelope field. Old envelopes (pre-fingerprint) lacking the field still get compared at runtime by computing `_envelope_fingerprint(env)` as `env.get("fingerprint") or _compute_from_body(env["proposal"])`. This is the "additive optional fields + tolerant reads" schema-evolution pattern — zero migration script, mixed-version files coexist freely.

## When It Applies

- **Producers that emit full scans** (not incremental/partial scans). The "live set" reflects the complete state the producer found.
- **Derived-data queues** where entries are regenerable by a subsequent producer run. Safe to GC aggressively.
- **Append-only queues with re-running producers** where the same producer is scheduled repeatedly (nightly scanner, periodic audit, hourly detector).
- **Findings/proposals/suggestions** where duplicates are noise and resolved entries should retire quickly rather than linger for days.

## When This Does NOT Apply

- **Pure event logs** (audit logs, telemetry) where duplicate occurrences are themselves the signal. Don't dedup events you want a count of.
- **Producers that emit incremental/partial scans** rather than full scans. Reconcile would wrongly retire findings the producer didn't re-scan this run. For these, gate per producer via a `reconcile: bool` config flag (default true for documented full-scan producers, false for incremental).
- **Queues without an exclusive lock primitive** (raw S3 object writes, etc.) — read-modify-write requires serialization; if the storage doesn't support it cheaply, this pattern needs adaptation (compaction job, etc.).
- **Primary data** (mutable core state) rather than derived/regenerable data. The schema-evolution pattern (optional fingerprint) works fine; the GC-aggressiveness logic doesn't.

## Observability

Expose `reconciled_retired` as a per-run counter on the producer's run summary (the runner's JSON output / metrics). When the system is healthy, this counter equals the number of findings resolved since the last run. A persistent zero indicates either nothing is being fixed *or* reconcile isn't running (check the clean-run gate). A persistent high value indicates churn worth investigating.

## Concrete Grounding (the source session)

Implemented 2026-05-29 in [project] for the `iteration_loop/pending-suggestions.jsonl` queue (bead `[project]-w0hb`, commits `a5bf4b1` + `af60812`). The producer is the iteration-loop scheduler running per-worker scans (wiki-linter, code-audit); consumers are `nw-morning.py` (the 06:05 morning brief) and downstream `gt_brief.py`. The forensics that motivated the fix:

- 6 stale queue lines from 2 already-fixed orphan-link findings, accumulated across 3 consecutive nightly runs (4×/2× pileup) under a 7-day TTL.
- Last emission of each was 2026-05-26 ~09:00, the linter correctly stopped emitting them after the underlying fix landed that day — but they showed in the 2026-05-29 morning brief because the TTL hadn't expired.
- Confirmed not re-detection (the linter found 0 orphans against the fixed wiki). Pure persistence-after-resolution + accumulation, the two failure modes this pattern fixes.

Implementation: `iteration_loop/orchestra.py` got `_proposal_fingerprint`, `_envelope_fingerprint`, `proposal_fingerprint` (public), `_rewrite_locked(transform)` (fcntl LOCK_EX read-modify-write with mangled-line preservation), `enqueue_proposal` switched to dedup-on-enqueue, and a new `reconcile_proposals(source_bead, live_fingerprints)`. `iteration_loop/scheduler.py` got `live_fingerprints` collection during the per-worker loop, the clean-full-scan gate, the reconcile call, a per-worker `reconcile` config flag (default true), and a `reconciled_retired` stat in the summary JSON. 12 new unit tests in `test_orchestra.py` (fingerprint stability, dedup-across-runs, collapsing pre-existing duplicates, reconcile retire/keep/scope, tolerant of pre-fingerprint rows, preserves unparseable lines) + 2 gating tests in `test_scheduler.py` (clean run reconciles, short-circuit skips). 490/490 tests passing.

## Source Context

**Brief:** Designed and implemented during [project] iteration-loop debugging (2026-05-29). Motivated by forensic discovery of 6 stale queue entries from 2 fixed findings, accumulated over 3 nights despite the linter correctly stopping emission. The two failure modes (accumulation + persistence) are structurally independent but share a single two-part fix: fingerprint-based dedup on enqueue + reconcile GC on clean producer completion.

**Module context:** The pattern directly implements the "deterministic-first debugging" methodology — the forensics traced the exact two mechanisms that caused the stale entries before designing the fix.

## Cross-References

- [[deterministic-first-debugging]] — the diagnostic process that traced the 6 stale lines to the precise accumulation+persistence mechanism rather than the easier-but-wrong "the linter must be re-detecting" hypothesis.
- [[coalesce-at-enqueue-every-coalesce-gets-a-row]] — related pattern for dedup *at enqueue time* when multiple triggers fire close together (complementary: coalesce handles in-flight duplication, fingerprint handles across-run accumulation).
- [[one-reconciliation-pipeline-called-twice]] — related pattern for idempotent reconciliation; this pattern is narrower (queue GC only) but shares the "safe to run repeatedly" discipline.
- [[schema-evolution-additive-optional-fields]] — the envelope-field addition pattern used for backward-compatible fingerprint introduction.
