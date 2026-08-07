---
title: GasTown scheduled formulas must self-GC their own step wisps to prevent accumulation
source_mode: debugger
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-07-11
domain: orchestration
topic: recovery
tags: scheduling, quality-gate, deployment
related_entries: [orchestration/2026-05-14_cost-meter-always-emit-release-on-cycle-exit.md, infrastructure/2026-05-14_idempotent-watchdog-producer-pattern.md]
---

# GasTown Scheduled Formulas Must Self-GC Their Own Step Wisps to Prevent Accumulation

## Problem

GasTown mol (molecule) formulas create step wisps to track execution progress through each formula's steps. The `gt reaper` tooling only closes wisps past `max_age` (default 24h). If a scheduled formula runs more frequently than max_age (e.g., hourly), each run creates N new step wisps that are too fresh for the reaper to touch. Without self-cleanup, these accumulate rapidly.

Observed 2026-07-06 (bead hq-uvyh): `mol-dog-reaper` runs hourly with 5 steps (scan, reap, purge, auto-close, report). Each run creates ~5 step wisps per database. Open wisp count jumped from 770 to 1610 in 24h despite a full reaper run on 2026-07-04. Root cause identified by dog-alpha: mol-dog-reaper doesn't clean up its own step wisps. Fixed by adding `self-gc` as step 0 (formula v2→v3).

## The Pattern: Swim-Lane Self-GC

Every scheduled formula that runs more frequently than `max_age` should include a self-gc step at the start of each cycle:

```toml
[[steps]]
id = "self-gc"
title = "Clean up own wisps from previous cycles"
description = """
GC your own wisps from previous runs before starting new work.

```bash
bd mol wisp gc --closed --force
bd mol wisp gc --age 1h --force
```

SWIM LANE RULE: Only GC wisps YOU created. Do NOT touch wisps from other
agents/formulas. Closing foreign wisps kills active polecat work molecules.
"""
```

Then make your first real step depend on `self-gc`:

```toml
[[steps]]
id = "scan"
needs = ["self-gc"]
```

## Precedent

`mol-witness-patrol` step 0 has used this pattern since its initial design:

```bash
bd mol wisp gc --closed --force   # close own closed wisps from prior cycles
bd mol wisp gc --age 1h --force   # close own abandoned wisps
```

## When This Applies

- Any GasTown formula dispatched on a schedule faster than `max_age` (24h default)
- Formulas run by infrastructure Daemons (wisp_reaper, patrol scheduler, etc.)
- Any formula that creates ≥3 step wisps per run

## When This Does NOT Apply

- One-shot formulas (polecat work molecules — they run once and the polecat session ends)
- Formulas with inter-run intervals >> 24h (wisp reaper will naturally handle them)
- Formulas that already close their own wisps via squash on completion

## Verification

After adding self-gc, check that the open wisp count stabilizes rather than growing linearly:

```bash
gt reaper scan --db=<name> --port=3307 --json | jq .open_wisps
```

Run across two consecutive reaper cycles and confirm the count is not growing.

## Source Context

Debugged during [project] Happy orchestrator TOML migration (2026-07-11, session [project]-happy-orchestrator-toml-migration). The mol-dog-reaper hourly cycle accumulated step wisps because the formula ran faster than the reaper's 24h max_age. Each of 5 steps in the cycle creates a wisp; at 24 hourly runs before the reaper fires, that's 120 wisps/day from a single formula. With Dolt's multiple databases multiplying the wisp count, the 770→1610 jump over 24h was geometrically plausible. The fix is the swim-lane self-gc step — close only wisps the formula itself created (scoped by the formula's own mol ID), never touching step wisps from other formulas' runs. Precedent established in mol-witness-patrol; dog-alpha applied the same pattern to mol-dog-reaper v3.
