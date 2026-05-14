---
title: Conditional UPDATE for atomic queue claim
source_mode: code-dive
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.95
grounding_source: "Direct code reference: paperclip server/src/services/heartbeat.ts:5778 claimQueuedRun(). UPDATE with WHERE predicate + RETURNING for single-row claim atomicity."
staleness_risk: stable
importance: 5
pinned: false
created: 2026-05-13
domain: patterns
topic: orchestration
tags: quality-gate, latency, throughput, empirical, stable
related_entries: [orchestration/2026-05-13_one-reconciliation-pipeline-called-twice.md]
---

# Conditional UPDATE for Atomic Queue Claim

## Pattern

A worker claims a queued task by issuing `UPDATE runs SET status='running', claimed_by=$me WHERE id=$id AND status='queued'` and checking the affected-row count. Exactly one worker gets `1`; everyone else gets `0` and skips. **Postgres MVCC + row locking handles the race entirely** — no `SELECT FOR UPDATE`, no advisory locks, no application-level mutex.

## Code Reference

```ts
// server/src/services/heartbeat.ts:5778 — claimQueuedRun
const result = await tx
  .update(runs)
  .set({ status: 'running', claimedBy: workerId, claimedAt: now })
  .where(and(eq(runs.id, id), eq(runs.status, 'queued')))
  .returning({ id: runs.id });

if (result.length === 0) {
  // someone else already claimed it; abort silently
  return null;
}
```

## Why It Works

1. Postgres serializes row-level writes via the MVCC row version. Two concurrent UPDATEs of the same row get queued; the second sees the new row version and the `status='queued'` predicate fails.
2. `RETURNING` lets the application learn whether *this transaction* did the update — distinguishing "I claimed it" from "someone else did."
3. No prior `SELECT` is needed. Reading the row to "check if it's queued" is the classic race; the predicate inside the UPDATE itself is the atomicity.

## When to Use

- Any work queue where multiple workers poll the same table.
- Any state transition that must happen exactly once (e.g., `pending → sent`, `draft → published`).
- Anywhere you'd otherwise reach for advisory locks or `SELECT FOR UPDATE SKIP LOCKED`.

## When This Does NOT Apply

- Multi-row claims (need `SELECT ... FOR UPDATE SKIP LOCKED` instead).
- Non-Postgres backends without equivalent row-version semantics. SQLite is fine (serial writer); MySQL works with InnoDB; MongoDB needs `findOneAndUpdate` with filter.

## Trap: WHERE Predicate Must Include Source State

The `WHERE` predicate must include the source state, not just the id. `WHERE id=$id` alone races; `WHERE id=$id AND status='queued'` is the bug fix.

Example of the race:
```
Worker A: UPDATE runs SET status='running' WHERE id=123              -- assumes 123 is queued
Worker B: UPDATE runs SET status='running' WHERE id=123              -- also assumes 123 is queued

Both fire at nearly the same time. If 123 was already 'running', both updates
succeed (status doesn't change), and both workers think they claimed it.
Only happens if an earlier claim failed to set status properly.
```

With the predicate included, at most one succeeds:
```
Worker A: UPDATE runs SET status='running' WHERE id=123 AND status='queued' -- succeeds, affects 1 row
Worker B: UPDATE runs SET status='running' WHERE id=123 AND status='queued' -- fails, affects 0 rows (123 is now 'running')
```

## Related

- **[[one-reconciliation-pipeline-called-twice]]** — higher-level pattern that uses this primitive to safely transition work through state machines
- **[[lazy-locking-with-idempotency-guard]]** — alternative: stamping `lock_owner` at claim time with `WHERE lock IS NULL OR lock = $me`
- **[[coalesce-at-enqueue]]** — what to do when a duplicate enqueue arrives mid-flight

## Source Context

Identified during code dive into paperclip queue claim logic, 2026-05-13. The system uses Postgres row MVCC to implement lock-free queue claiming across distributed workers. No explicit locking primitives — the conditional UPDATE is the entire synchronization mechanism. Used in the reconciliation pipeline (see related) to claim runs for recovery processing. Grounding: direct read of paperclip `heartbeat.ts` line 5778, pattern validated against Postgres documentation and empirical testing in the codebase.
