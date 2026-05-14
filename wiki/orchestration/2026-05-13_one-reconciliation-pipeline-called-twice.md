---
title: One reconciliation pipeline, called twice (startup + periodic)
source_mode: code-dive
source_session: redacted
novelty_type: technique-original
grounding_score: 1.0
grounding_source: "Direct code trace: paperclip server/src/index.ts:670-790. Six reconciliation steps identified and ordered. Pipeline invoked identically from both startup handler and periodic timer."
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-13
domain: orchestration
topic: recovery
tags: reconciliation, recovery, idempotency, liveness, orchestration, startup
related_entries: [infrastructure/2026-05-12_self-watchdog-autonomous-fix-cycles.md, patterns/2026-05-12_dogfood-apply-undo-end-to-end-testing.md]
---

# One Reconciliation Pipeline, Called Twice

## Pattern

A single, idempotent recovery pipeline that runs both at process startup (to clean up after the last process death) and on a periodic timer (to clean up stranded work that accumulates during normal operation). Same function, same order of operations, called from two places.

## Code Reference

```
server/src/index.ts:670-790

Same six-step pipeline invoked identically from:
- startup handler (on app boot)
- periodic timer (hourly or daily)

The six steps:

1. heartbeat.reapOrphanedRuns()             // mark runs whose owner is gone
2. promoteDueScheduledRetries()             // move retry-scheduled → queued
3. resumeQueuedRuns()                       // wake up dispatchers
   + reconcileStrandedAssignedIssues()      // assigned-but-no-run cleanup
4. reconcileIssueGraphLiveness()            // unblock/escalate stale issues
5. scanSilentActiveRuns()                   // detect silent-but-active workers
6. reconcileProductivityReviews()           // bookkeeping rollups
```

Each step satisfies three invariants:

- **Idempotent** — running it twice in a row is a no-op the second time.
- **Composable** — order matters but each step makes the world more consistent.
- **Quiet by default** — logs only when something *changes*. A reconciliation tick that finds nothing wrong produces zero output.

## Why This Is the Right Shape

Most systems write *startup recovery* and *periodic liveness* as separate code paths. That creates three problems:

1. **Startup logic drifts away from the periodic logic** over time as each evolves independently.
2. **Bugs only reproduce on cold-start or only mid-flight.** The other path masks them, making root cause hard to find.
3. **"Is something stuck?" answers are operationally distinct** depending on when you ask (startup vs periodic).

One pipeline kills all three birds:

- Cold-start is just the case where lots of work is stranded; periodic is the case where a little is. Same code handles both.
- Bugs that reproduce on startup will reproduce in the periodic cycle too (they'll show up when the timer fires).
- The answer to "what's stuck?" is consistent whether you ask at boot or during operation.

## Implementation Rules

1. **Every step must be safe to call mid-flight.** No assumption that the process just started; no assumption that no other workers are running. Each step queries the actual current state and acts only on findings.

2. **Step ordering encodes dependency.** Reap orphans *before* queuing retries *before* promoting queued runs — each step makes the next step safer or more meaningful.

3. **One audit row per state transition, not per tick.** A reconciliation that touches 0 runs writes 0 rows. A reconciliation that touches 5 runs writes 5 rows. Helps post-hoc forensics: you can grep the audit log and see exactly when each run was transitioned and why.

4. **Crash counter / staleness windows reset on healthy ticks.** Otherwise a transient outage (brief database unavailability, brief network hiccup) leaves the system in permanently-flapping recovery state even after the outage passes.

## When to Use

- Any long-running process that owns mutable state and can crash. Process death leaves work dangling; reconciliation cleans it up.
- Any system where work can become "stranded" — owner gone, expected next-step never happened, deadline missed, transaction rolled back but side effects weren't.
- Systems with both heartbeat-style execution and ad-hoc bursts, where the scheduler may be overloaded and miss a deadline.
- Recovery must be idempotent because the same logic runs both at startup (when lots is broken) and at periodic (when usually nothing is broken). Idempotency means periodic runs are cheap.

## When This Does NOT Apply

- Pure request/response services with no persistent claim semantics. The service doesn't own mutable state, so there's nothing to reconcile on startup.
- Systems with strong external schedulers (Kubernetes controller pattern, Airflow, etc.) that already handle the reconciliation loop for you. Delegating reconciliation to an external orchestrator is often the right call.
- Stateless workers in a load-balanced pool where the pool orchestrator (load balancer, k8s, etc.) already detects dead workers and redistributes work. You don't need both.

## Trap: Two Paths Mask Bugs

Periodic-only systems (reconciliation only on timer) mask startup-recovery bugs. When a worker crashes and restarts, startup recovery runs — if it's broken, you might not see the bug until the process crashes again and restarts. The bug hides in low-frequency scenarios.

Startup-only systems (reconciliation only on boot, nowhere else) mask mid-flight stranding bugs. Work can become stranded during normal operation if a deadline is missed or a worker dies. The periodic reconciliation is what catches those. Without it, stranded work accumulates silently.

**The split into two paths is common because each individual path is simpler.** But the combination is fragile and creates blind spots.

## Related Patterns

- **[[conditional-update-for-atomic-queue-claim]]** — the primitive each reconciliation step uses to safely transition state
- **[[log-only-when-something-changed]]** — the silent-tick discipline this pattern depends on
- **[[self-watchdog]]** — external monitoring that the reconciliation pipeline itself is running correctly (this pattern reconciles work; self-watchdog reconciles the reconciler)

## Source Context

Identified during code dive into paperclip server architecture, 2026-05-13. The system owns a queue of runs, an issue graph with state machines, and productivity metrics. Workers claim runs, execute them, and report completion. If a worker crashes, its run is orphaned; if a deadline passes with no completion, an issue stalls. The reconciliation pipeline catches both cases identically, running once at startup and once per hour. Same code path, same six steps, same idempotency contract. Grounding: direct file read and step trace of `server/src/index.ts` lines 670–790.
