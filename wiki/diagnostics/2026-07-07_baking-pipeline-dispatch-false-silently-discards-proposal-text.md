---
title: baking_pipeline dispatch=False silently discards full proposal text
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-07
domain: diagnostics
topic: dispatch-routing-data-loss
tags: iteration-loop, baking-pipeline, dry-run, data-loss, silent-failure
related_entries:
  - diagnostics/2026-06-13_green-daemon-zero-output-status-field-silently-excludes-work.md
  - orchestration/2026-05-30_dry-run-first-validation-mutation-bearing-orchestration-skills.md
  - infrastructure/2026-05-15_silent-success-scripts-state-artifact-freshness.md
---

# baking_pipeline dispatch=False silently discards full proposal text

## Pattern: Silent Data Loss During Dry-Run Mode

### What happens

In `iteration_loop/baking_pipeline.py`, `bake_and_route()` accepts a `dispatch: bool` parameter. When `dispatch=False` (controlled by the `dispatch` field in `workers.toml` per worker stanza), the function hits an early-return branch at the "Dispatch" stage:

```python
if not dispatch:
    _log_routing_decision(
        raw=raw, stage="dispatch", outcome="emitted",
        ...
        trigger="dispatch_disabled",
    )
    return PipelineResult(stage="dispatch", outcome="emitted", ...)
```

This returns BEFORE calling `orchestra.enqueue_proposal()`. As a result:
- The routing log gets a 20-character truncated headline snippet only
- The full proposal (headline, body/rationale, source signals, first_reversible_step, worker_action spec) exists only in the in-process `PipelineResult` object
- When the scheduler process exits, the full text is permanently lost
- The worker metrics correctly count "emitted: N" (counting PipelineResult outcomes), so the scheduler summary appears successful
- The morning brief shows "N findings" in worker health but "no active baked proposals" in the Orchestra queue section — because nothing was enqueued
- The pending-suggestions.jsonl file has no corresponding baked_proposal entries

### Diagnostic signature

**Check these signals to identify the pattern:**

1. Routing log has `"trigger":"dispatch_disabled"` entries with 20-char `request_text` (truncated)
2. Scheduler JSON shows `emitted: N` for the worker but `spent_usd: $X` (cost was real; computation happened)
3. Morning brief worker health row says "N findings" but baked proposals section is empty
4. `pending-suggestions.jsonl` has no `kind="baked_proposal"` entries from that session
5. `~/.[project]/logs/dispatch-dry-run.jsonl` (post-fix) has full proposal JSONL records if present

### Root cause

The `dispatch=False` mode was designed as a "dry-run before going live" gate (per `workers.toml` comments: "flip dispatch=false or enabled=false to silence the worker"). But the intent of dry-run (read the output, evaluate quality) is broken because the output is never persisted anywhere. Proposals are computed at full cost but discarded at the routing boundary, leaving zero audit trail.

### Fix applied (2026-07-07, [project] commit e18ea3e)

Added `_write_dry_run_log(raw, proposal, decision.surface)` call in the early-return block. Appends a full JSONL record to `~/.[project]/logs/dispatch-dry-run.jsonl` before returning. Record includes:
- `headline`
- `body` (full rationale)
- `spec` (worker action spec)
- `confidence`
- `grounding_score`
- `reversibility`
- `action_tier`
- `estimated_effort`
- `first_reversible_step`
- `decision_type`
- `route_would_be` (where it would have gone if dispatch=True)
- `worker_session_id`
- `ts` (ISO 8601 timestamp)

Uses `os.O_WRONLY|os.O_CREAT|os.O_APPEND` (no fcntl lock) — same pattern as `orchestra.py` queue writes. Swallows all errors so a log write failure never crashes the pipeline.

### When this applies

- Any iteration-loop worker with `dispatch = false` in `workers.toml`
- Any generative worker (calls `claude --print`) where you want to inspect output quality before enabling live routing
- Debugging a worker that reports "N findings" but morning brief shows "no proposals" despite healthy worker state
- Post-fix: check `~/.[project]/logs/dispatch-dry-run.jsonl` after nightly run to review dry-run output

### When it does NOT apply

- `dispatch = true`: proposals go to `pending-suggestions.jsonl` via `orchestra.enqueue_proposal()` — fully persisted
- Deterministic workers (wiki-linter, [project]-code-audit): these don't use `dispatch=False` in production; findings always go to the queue
- When the absence of proposals IS the intended behavior (testing a disabled worker intentionally)

### Grounding

Directly verified in session 2026-07-07 ([project]-overnight-review):
- Read `baking_pipeline.py` lines 511–526 confirming the early-return path
- Confirmed `pending-suggestions.jsonl` had no baked_proposal entries for the session
- Routing log showed two `dispatch_disabled` entries with 20-char truncated text
- Morning brief confirmed "no active baked proposals" despite "2 findings" in worker health
- Cost meter showed $0.6928 spent (proposals were computed, just not stored)
- Fix committed as e18ea3e, 906 tests pass
- `dispatch-dry-run.jsonl` now captures full proposal text on every dry-run cycle

### Data Loss Cost

For each dry-run session:
- **Computation cost:** $0–$2 per nightly run (depends on worker complexity + finding count)
- **Audit trail cost:** Zero — no way to recover what was computed without re-running
- **Quality-review cost:** Zero opportunity to inspect proposals before enabling dispatch=true
- **Iteration cost:** If a worker needs tuning before going live, you have to rely on partial routing-log snippets and worker-health counts

### Prevention

1. Always enable `dispatch=true` for workers intended to generate proposals
2. If tuning a worker, use a separate `dispatch=false` stanza in `workers.toml` during development
3. After tuning is complete, switch `dispatch=true` before merging to main
4. Monitor `dispatch-dry-run.jsonl` size and entry count to catch workers stuck in dry-run mode

### Source Context

Discovered during [project] overnight review 2026-07-07. A test worker had `dispatch=false` in the staging workers.toml to prevent proposals leaking before go-live. The worker ran nightly, computed 2 findings ($0.69 cost), but the findings were lost when dispatch returned early. Morning brief showed the findings in worker health but not in the proposal queue. The routing log had the dispatch_disabled trigger but only truncated headlines. Root cause: the early-return path hit before `orchestra.enqueue_proposal()`, so the full proposal never persisted anywhere. The fix appends dry-run proposals to a separate JSONL for audit and quality review.
