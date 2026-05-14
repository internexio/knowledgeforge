---
title: Coalesce at enqueue, every coalesce gets a row
source_mode: code-dive
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.95
grounding_source: "Direct code trace: paperclip server/src/services/heartbeat.ts lines 8541 (enqueueWakeup decision tree) and 8948-8980 (coalesce audit row write). Shows branch logic and database write."
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-13
domain: orchestration
topic: orchestration
tags: routing, classification, latency, tier-0, empirical, stable
related_entries: [orchestration/2026-05-13_one-reconciliation-pipeline-called-twice.md]
---

# Coalesce at Enqueue, Every Coalesce Gets a Row

## Pattern

When a request to enqueue work arrives and a run for the same logical key is already running, **don't queue a new run** — instead, fold the new context into the existing run and write an audit row marked `status='coalesced'` referencing both.

Two principles:
1. **Coalesce at enqueue, not at dequeue.** The decision happens when the duplicate arrives, not when the worker is about to pick it up. State of the world is more current; debounce is cheaper.
2. **Every coalesce is a first-class row, not a silent drop.** Same shape as a normal run row, just with `status='coalesced'` and a pointer to the real run that absorbed it.

## Code Reference

From `server/src/services/heartbeat.ts`:

**enqueueWakeup decision tree (lines 8541-8580, simplified):**
```ts
if (existingRun.status === 'running' && policy === 'coalesce_if_active') {
  // Merge the new context snapshot into the running run
  await mergeContextSnapshot(existingRun.id, incomingContext);

  // Write a row for the coalesce itself
  await db.insert(runs).values({
    id: newId,
    agentId,
    status: 'coalesced',
    coalescedInto: existingRun.id,
    contextSnapshot: incomingContext,
    createdAt: now,
  });

  return { runId: newId, status: 'coalesced', mergedInto: existingRun.id };
}
```

**Audit row write (lines 8948-8980):**
The coalesce row is written atomically with the context merge, ensuring the audit trail and the merged state stay in sync.

## Why "Every Coalesce Gets a Row"

Silent dedup looks free in the happy path and is catastrophic in the unhappy path:

- **Debugging lost requests:** "Why didn't this fire?" — without a row, no record. With a row: `SELECT * FROM runs WHERE coalescedInto = $X` answers it immediately.
- **Monitoring dedup rates:** "How often is this debouncing?" — without rows, no metric. With rows, `COUNT(*) GROUP BY hour` becomes a dashboard query.
- **Preserving lost context:** "What context did we lose?" — without rows, gone forever. With rows, the snapshot is preserved for audit and recovery.

The cost is one extra row per coalesce. Tiny insertion and storage cost. The observability and debuggability lift is enormous.

## When to Coalesce vs When to Queue

Three concurrency policies, each appropriate in different situations:

| Policy | Behavior | Use case |
|--------|----------|----------|
| **`skip_if_active`** | Drop the new request entirely if a run is in-flight. | Idempotent "do this thing now" (e.g., fetch latest user state). In-flight run already covers the new request. |
| **`coalesce_if_active`** | Merge new context into the running run + emit audit row. | New request carries newer/additional context the running run should see (e.g., user triggered action twice, second has fresher timestamp). |
| **`always_enqueue`** | Queue every request independently. | Each request must execute independently, no merging semantics. |

## When to Use This Pattern

- **Wakeup queues, debounced background work.** "Re-run this analysis when state changes" — a flurry of state-change triggers should fire only once, but we need to know how many times we debounced.
- **Anywhere a flurry of triggers can fire close in time.** Only one execution is wanted, but the operator might later ask "how often did this happen?"
- **Systems where context accumulates.** The first request in a flurry may not have complete info; the second does. Coalescing captures the latest context.
- **High-variability load patterns.** During a traffic spike, coalescing keeps queue depth bounded while preserving observability.

## When NOT to Use

- **Strict request-per-response semantics.** HTTP endpoints where each request must produce exactly one response. Coalescing breaks this contract.
- **Queue items that aren't safely mergeable.** Monetary transactions, cryptographic signatures, or work items where combining requests is semantically invalid.
- **Systems with ordering guarantees.** If later work depends on earlier work's completion signal, coalescing may violate causality.

## Trap: Coalesce-at-Dequeue

The naive alternative — "let dupes queue up and just dedupe when the worker pulls" — has two critical problems:

1. **Queue depth grows with dup rate,** distorting metrics and delaying the actual execution of the first item. A burst of 100 duplicates creates 100 queue entries even though only 1 needs to execute.
2. **Worker has to know how to dedupe,** scattering coalesce logic across the codebase. The enqueue boundary is a single decision point; pushing it downstream creates multiple implementations.

**Push the decision to the enqueue boundary; workers stay dumb.**

## Observability Rules

- **Log the coalesce:** When writing the audit row, emit a debug log with: `coalescedId`, `mergedIntoId`, `contextSnapshot` (or hash if snapshot is large), `deltaInfo` (what changed between old and new context).
- **Dashboard by coalesce rate:** `SELECT agentId, hour, COUNT(*) FROM runs WHERE status='coalesced' GROUP BY agentId, hour` tells you which agents are receiving duplicate triggers and when.
- **Alert on runaway coalesce:** If coalesce rate is > 50% for an agent, something is generating spurious retries — investigate the trigger source.

## Related Patterns

- **[[one-reconciliation-pipeline-called-twice]]** — cleans up coalesced runs that lost their target (coalesced-into run failed; orphaned coalesce row must be handled)
- **[[conditional-update-for-atomic-queue-claim]]** — the primitive enqueue uses to detect "already running" and merge atomically (not yet in wiki; mentioned here for forward reference)

## Source Context

Identified during code dive into paperclip wakeup queue architecture ([project] session 2026-05-13). Examined `server/src/services/heartbeat.ts` lines 8541 and 8948-8980. The system manages a queue of async runs with deduplication; a common pattern is for multiple triggers (webhook, user action, scheduled timer) to request the same work within a short window. The system coalesces at enqueue time, merging context and emitting an audit row. Grounding: direct line-by-line trace of decision tree and database write.
