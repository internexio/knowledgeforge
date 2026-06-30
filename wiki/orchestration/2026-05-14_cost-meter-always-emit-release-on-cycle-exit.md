---
title: Cost meter must always emit release event on cycle exit, even on overrun
source_mode: builder
novelty_type: new_pattern
grounding_score: 0.92
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-14
tags: observability, cost-accounting, iteration-loop, watchdog-interaction, finally-block-discipline
related_entries: []
domain: orchestration
topic: queue-pattern
---

# Cost Meter Always Emit Release on Cycle Exit, Even on Overrun

## Pattern

When a worker uses the cost-meter reserve/spend/release primitive inside a cycle with a finally-block cleanup:

```python
state = cost_meter.snapshot(session_id)
release_usd = max(0.0, state.outstanding_usd)
cost_meter.release(session_id, release_usd)
if state.outstanding_usd < 0:
    overrun = -state.outstanding_usd
    print(
        f"cost-meter overrun by ${overrun:.4f} "
        f"(reserved=${state.reserved_usd:.2f} spent=${state.spent_usd:.4f}) — "
        f"raise reservation or trim per-stage caps if this recurs",
        file=sys.stderr,
    )
```

The invariant `reserved == spent + released` is allowed to break *visibly* when actual spend exceeds reservation. But **always emit the release event**, even if `outstanding_usd < 0`.

## Why This Is Critical

The iteration-loop spec (§11.4) designates reservation as a SOFT guardrail. `cost_meter._safe_spend()` does NOT block on overrun; only `--max-budget-usd` per call does.

Polecat-watchdog sweeps any session that hasn't emitted a close event within `MAX_CYCLE_DURATION_SEC` (30 min default). If a worker skips `release()` because `outstanding_usd` went negative, the session is treated as orphaned and silently swept — **losing audit fidelity completely**.

The naive optimization — "skip release when outstanding is negative since there's nothing to release" — is the exact bug. Silent orphan-sweep causes every overrun session to disappear from the audit trail.

## Implementation Rules

1. **Always call `cost_meter.release()`** in the finally block
2. **Use `max(0.0, outstanding_usd)`** as the release amount (never a negative release)
3. **Emit overrun warning to stderr** when `outstanding_usd < 0` for operator visibility
4. **Log the full state** (reserved, spent, actual release) so the overage is provable post-hoc

## When This Applies

- Any worker that reserves a cost budget and enters a cycle with finally-block cleanup
- Any multi-stage pipeline using cost-meter to cap per-stage spend
- Any context where a watchdog polls for cycle-alive signals (polecat or equivalent)

## When This Does NOT Apply

- One-shot cost-meter calls without a cycle loop (release naturally happens at return)
- Cost meters inside nested functions where cleanup is managed by the caller (delegate release upward)

## Validation

**2026-05-14 wiki-linter run (commit 6395e0f):**
- Reserved $15, spent $7.94, released $7.06 — invariant holds cleanly
- Prior runs at $5 reservation hit overrun ($9.02 spent) and validated the warning path
- Close event fired correctly in all cases; no orphan-sweep incidents

**Code reference:** `~/Scripts/[project]/scripts/wiki_linter.py` lines 163–186

## Source Context

Designed after multiple overrun incidents during iteration-loop v0 hardening in the [project] sprint. The pattern ensures observability is preserved during cost-overflow events, which are expected but should never be silent.
