---
title: Identity registry + append-only event log — separate "who/what" from "what happened"
source_mode: direct
novelty_type: new_pattern
grounding_score: 0.75
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-14
domain: architecture
topic: layering
tags: patterns, architecture, state-machines, audit-trails, atomic-write, posix-append, separation-of-concerns
related_entries:
  - infrastructure/2026-05-13_posix-append-pipe-buf-concurrent-jsonl-writers.md
  - patterns/2026-05-11_atomic-write-stubs-for-readwrite-pipelines.md
  - patterns/2026-05-11_audit-log-event-vocabulary-mismatch.md
  - patterns/2026-05-13_conditional-update-for-atomic-queue-claim.md
---

# Identity Registry + Append-Only Event Log — Separate "Who/What" From "What Happened"

## The Pattern

State machines that need BOTH (a) a stable identity surface — durable, queryable, human-inspectable — AND (b) a mutating-state record — atomic, recoverable, concurrent-safe — should split these into two artifacts:

1. **Identity registry**: one record per entity, holding *static* fields only. The kind of thing you query, list, label, share. Backed by a system with query semantics (bd, SQL table, key-value store).
2. **Append-only event log**: per-entity JSONL, holding the mutating values as a sequence of events. Reader folds events into current state. Backed by POSIX-atomic-append on a regular file.

The boundary: identity-registry rows NEVER change after creation (or change only via deliberate identity migrations). All mutation happens in the event log. The reader composes a "current state" by joining identity with the folded event tail.

## Why Split

Conflating identity + state on a single record forces every mutation to use the registry's update primitive. For systems whose update primitive is not truly atomic across the read-modify-write boundary (most JSON-blob "update notes" patterns), this is the classic lost-update race trap.

By contrast:
- The identity registry is mutated at most once (at create time). No lost updates possible because no concurrent updates.
- The event log is append-only. POSIX guarantees atomic-append for writes under PIPE_BUF (512B on macOS, 4096B on Linux). Two writers cannot interleave bytes mid-line. Order-independent folding makes concurrent appends safe without locks.

Net: lost-update concurrency safety without transactions, without locks, without giving up audit-trail.

## Concrete Grounding ([project] iteration-loop v0 Phase 1, commit fe56f3d)

The cost-meter primitive implements this exact split:

- **Identity registry:** one `bd` issue per `worker_session_id`. Holds `session_id`, `work_type`, `beads_issue_id`. Static. Never updated post-create. `bd show` returns identity for human inspection / runbooks.

- **Event log:** `~/.[project]/cost-meter/<session_id>.jsonl`. Each line is one event:
  ```json
  {"op":"reserve","usd":0.50,"expiry_mono_ns":...,"mono_ns":...,"ts_utc":"..."}
  {"op":"spend","usd":0.18,"mono_ns":...}
  {"op":"release","usd":0.32,"mono_ns":...}
  ```
  POSIX-atomic-append under the 480-byte budget (macOS PIPE_BUF=512 - 32B headroom). Worker writes; polecat-watchdog (separate process) also writes `expired-release` events on orphan sweep. No interleave, no race.

- **State derivation:** `cost_meter.snapshot(session_id)` reads the JSONL once, folds events into a `CostState` dataclass: reserved / spent / released / expired_released / is_open / is_orphaned. Pure function of the event log content.

The amendment to the baking-pipeline contract (§11.4) explicitly forbids `bd update --notes` with R-M-W at the application layer, naming it as the classic lost-update trap. Identity-only on bd, mutation-only on JSONL is the precise corollary.

## When This Applies

- State machines with N concurrent writers/readers + an identity surface humans want to query.
- Cost meters, quota counters, lease registries (worker session leases).
- Audit-trail-mandatory systems where mutation history must survive replay.
- Queue claim systems where claim acquisition + release fire from different processes.
- Any case where the natural identity surface (bd, JIRA, SQL row) lacks atomic R-M-W primitives across separate calls.

## When This Does NOT Apply

- The identity surface DOES support transactions across update boundaries (e.g., Postgres row with `SELECT ... FOR UPDATE`). Then a single record with mutating fields is fine — primitive (i) per the design primitives.
- Single-writer-only workflows (concurrency=1 forever). No race to prevent; the simpler single-table form is preferable.
- Mutation rate is so high the event log grows unbounded faster than you compact. (Compaction is possible — periodic snapshot-then-truncate — but adds complexity. Consider the simpler primitive if rate is in that range.)
- The mutations are non-commutative AND non-foldable (e.g., "rename to X" followed by "rename to Y" — replay-order matters and isn't naturally expressed as event fold). Fold-incompatible state machines need a true transactional store.

## Forward-Compat Note

This pattern composes cleanly with idempotency. When the event log is shared across multiple writers that may both detect the same condition (e.g., two polecat instances both sweeping the same orphaned reservation), each appended event SHOULD carry an `event_id = sha256(deterministic_key)`, and readers MUST dedupe on `event_id` before folding. Phase 1 of the [project] cost-meter ships WITHOUT this (single-machine, single-polecat). Phase 4 wiring (extending `polecat-watchdog.sh`) must add the dedupe before multi-instance polecat becomes plausible. This follows the forward-compat discipline documented elsewhere: verify audit claims before designing fixes.

## Source Context

Discovered while implementing iteration-loop v0 Phase 1 (commit fe56f3d, 2026-05-14). The baking-pipeline contract amendment from the prior session authorised primitive (ii) (append-only event log); Phase 1 code made the identity/state split concrete. Generalising the design choice once it had real code grounding produced this pattern entry.

Source session: 2026-05-14_iteration-loop-v0-phase-1-impl.
