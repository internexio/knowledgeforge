---
title: File-based timer-poll pattern for deferred async acknowledgement
source_mode: builder
novelty_type: transferable_framework
grounding_score: 0.9
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-14
domain: infrastructure
topic: ops
tags: observability, quality-gate, stable, empirical, infrastructure
related_entries:
  - patterns/2026-05-14_file-based-stub-deferred-dispatch-surfaces.md
  - infrastructure/2026-05-13_posix-append-pipe-buf-concurrent-jsonl-writers.md
  - infrastructure/2026-05-14_idempotent-watchdog-producer-pattern.md
---

# File-Based Timer-Poll Pattern for Deferred Async Acknowledgement

## Problem

You need a system that emits an alert (or dispatches an action) and then takes
a follow-up action if the recipient doesn't acknowledge within a timeout window.
The natural shape — "real bot/webhook + callback handler" — requires
infrastructure you don't have yet, or that's deferred to a later phase.

Concrete example from [project]: spec §3.4 says Tier 3 proposals sent to
Telegram start a 60-min approval timer; on timeout, demote to Orchestra with
`demote_reason="tier3_timeout"`. But the real Telegram bot is deferred (spec
Q-R1) — for v0, the "dispatch" surface is a file in
`~/.[project]/telegram-outbox/` written by a stub.

Without callbacks, how do you know when the timer fires? And how does an
acknowledgement cancel it?

## Pattern

Decouple the timer from the dispatch surface. Persist emit-state to a file
when the alert is dispatched. Run a polling worker on the same cadence as
your existing watchdog/cron; on each tick, scan the state dir for entries
older than the window that aren't yet acked or demoted, and take the
expiry action idempotently.

```python
# iteration_loop/tier3_demotion.py
def record_tier3_emit(proposal, *, now=None) -> Path:
    state = {
        "tier3_emit_ts_utc": (now or _utc_now()).isoformat(timespec="seconds"),
        "proposal": proposal.model_dump(mode="json"),
        "demoted": False,
        "demoted_at_utc": None,
    }
    path = TIER3_TIMER_DIR / _state_filename(proposal)
    path.write_text(json.dumps(state, separators=(",", ":")), encoding="utf-8")
    return path

def find_pending_demotions(*, now=None, window_seconds=3600):
    # Scan dir; return entries where age > window AND demoted is false.
    ...

def demote_to_orchestra(pending, *, now=None) -> bool:
    orchestra.enqueue_proposal(pending.proposal, demote_reason="tier3_timeout", ...)
    # Mark state file demoted=true so reruns are idempotent.
    state = json.loads(pending.state_path.read_text(...))
    state["demoted"] = True
    pending.state_path.write_text(json.dumps(state, ...))
    return True
```

The polling worker is invoked from the existing watchdog cron block. No new
scheduler, no daemon, no event loop — it composes with infrastructure you
already have.

## Ack Semantics Under This Pattern

The state file's existence IS the timer; modifying or deleting it IS the ack.
Three operations cover the surface:

| Action | Mechanism | Who does it |
|--------|-----------|-------------|
| Emit (start timer) | Write `{emit_ts, payload, demoted: false}` | Producer (e.g., pipeline orchestrator) |
| Ack (cancel timer) | Delete the file | Recipient (v0: manual; later: bot callback) |
| Expire (fire timer) | Mark `demoted: true` + take action | Polling worker |

When the real callback infrastructure lands (real Telegram bot, real webhook
receiver), the bot's Approve/Refine/Reject handler deletes the state file. No
code change required in the polling worker or the timer-recording function.

## Idempotency Mechanics

The polling worker can run as often as you like — every minute, every five,
every fifteen — without double-firing. Two guards:

1. `demoted: true` in the state file means "already handled" — find_pending
   skips it.
2. State filename is stable per (session_id, headline_hash) — re-emitting the
   same alert overwrites the same file rather than creating duplicates.

Re-emitting an alert effectively restarts the timer, which is the right
semantic: "user re-triggered this; give them another window."

## When This Applies

- Async dispatch with timeout semantics where the callback infrastructure is
  deferred or unreliable.
- Systems where the expiry action is idempotent (enqueue to a queue with a
  unique key, mark a state, send a downstream alarm).
- Low-frequency timers where polling-cost is negligible (minutes/hours, not
  milliseconds).
- Cases where you want a clean swap-path to real callbacks later — the
  recording function persists state; the eventual callback just deletes it.

## When This Does NOT Apply

- High-frequency or real-time timeouts (sub-second) — polling overhead and
  state-file I/O cost dominate.
- Non-idempotent expiry actions (e.g., "send one email") — duplicate fires
  during polling-window edge cases would double-act. Make the expiry
  idempotent first (e.g., via a dedup column at the consumer).
- High-concurrency emits to the same key — state-file overwrite races could
  lose data. Add file-locking (fcntl.LOCK_EX) or use a single-writer
  abstraction.
- Cases where you genuinely need precise timing (millisecond accuracy or
  scheduled-to-the-second) — polling is granular to the cron cadence.

## Concrete Grounding

- Shipped: [project] commit 9f94e83 (2026-05-14), `iteration_loop/tier3_demotion.py`
  with record/find/demote/process functions, CLI script
  `scripts/iteration_loop_demote_tier3.py`, wired into
  `scripts/polecat-watchdog.sh` (runs each tick), 8 new tests covering
  emit-records-state, idempotent-re-emit, missing-dir-empty,
  under-window-not-pending, aged-is-pending, demote-marks-state,
  process-is-idempotent, e2e-through-baking-pipeline. 233 total tests passing.
- Pipeline wiring: `baking_pipeline.bake_and_route` calls
  `tier3_demotion.record_tier3_emit(proposal)` after the Tier 3 Telegram
  send. The polling worker is invoked from
  `scripts/polecat-watchdog.sh` each tick.
- Storage: `~/.[project]/tier3_timers/` for state files.
- Bead: [project]-kmu2 (closed with shipping reference).

## Why Staleness Risk is "Stable"

File I/O semantics (atomic write, stable naming, readable state format) are
stable across platforms and OS versions. The pattern's correctness depends
only on these guarantees, not on any time-dependent infrastructure that might
drift (database versions, daemon lifetimes, scheduler changes). The only
mutable component is the worker cadence (cron tick frequency), which is
operator-configurable and does not affect the pattern's correctness — just
the expiry window granularity.

## Source Context

Discovered during [project] iteration-loop v0 Phase 1 implementation
(2026-05-14), session `[project]-iteration-loop-v0-tier3-demotion-2026-05-14`.
The Tier 3 proposal routing (spec §3.4) required a 60-minute approval timeout
before auto-demotion to Orchestra. Callback infrastructure (real Telegram bot)
was deferred. Rather than block on callbacks or build a custom scheduler, the
pattern emerged from composing file-based state (sibling entry: file-based stub)
with idempotent polling (sibling entry: idempotent watchdog producer). The
pattern is a timeout-aware generalization of the broader async-acknowledgement
problem in systems with deferred callback infrastructure.
