---
title: Reactive cache-refresh-and-retry on known stale-validator failure
source_mode: direct
novelty_type: new_pattern
grounding_score: 0.80
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-15
tags: quality-gate, empirical, adversarial, stable, latency
related_entries: [diagnostics/2026-05-15_bd-validator-cache-requires-unset-reset-refresh.md]
domain: patterns
topic: error-recovery
---

# Reactive Cache-Refresh-and-Retry on Known Stale-Validator Failure

## Pattern

When a downstream service has a known cache-staleness failure mode with a cheap refresh mechanism, the cleanest fix is to **catch the failure signature in the caller's error branch, run the refresh, and retry once** — instead of three worse alternatives:

| Alternative | Why worse |
|---|---|
| Defensively refresh before every call | Slow on the happy path (which is 99%+ of calls); turns a recovery primitive into an everyday tax |
| Restart the cache-holding process | Heavy, observable, may have its own failure modes; loses unrelated in-memory state |
| Leave it failing | Silent daily failures that pollute downstream surfaces (logs, briefs, dashboards) for days before noticed |

## When It Applies

- The downstream service has a documented stale-cache failure mode (or one observed empirically with a reproducible refresh)
- The refresh is cheap (sub-second, no observable side effects beyond cache invalidation)
- The failure signature is distinctive enough to match in caller-side error handling (substring on a specific error message, or specific exit-status pattern)
- The happy path is the overwhelming majority — adding the retry doesn't slow normal operation

## When It Does NOT Apply

- The failure has multiple unrelated causes that share the same surface signature (retry would mask real bugs)
- The refresh has side effects beyond cache invalidation (changes config the system depends on, triggers reconnects, etc.)
- The retry budget is unbounded — only retry ONCE; if a refresh+retry still fails, raise the original error
- The cache is owned by code you control and can fix at the cache layer instead

## Concrete Form

```python
def create_thing(name, deps):
    cmd = ["downstream-cli", "create", name, *deps]
    success, output = run_cmd(cmd, cwd=DOMAIN_DIR)

    # On known stale-cache signature — refresh and retry once.
    if not success and "invalid issue type" in output:
        log("WARN: validator rejected — refreshing cache and retrying")
        _refresh_validator_cache()
        success, output = run_cmd(cmd, cwd=DOMAIN_DIR)

    if not success:
        log(f"ERROR creating thing: {output}")
        return None
    return parse_id(output)


def _refresh_validator_cache():
    """Write the same config value back to invalidate downstream cache."""
    ok, current = run_cmd(["downstream-cli", "config", "get", "types.custom"], cwd=DOMAIN_DIR)
    if ok and current.strip():
        run_cmd(["downstream-cli", "config", "set", "types.custom", current.strip()], cwd=DOMAIN_DIR)
```

Key design choices:
- Refresh helper reads the **current** value before writing back (don't hard-code; let config be the source of truth)
- Substring match on the error message is intentionally loose — broader signatures catch sibling staleness cases without code change
- Single retry (no loop) — if refresh+retry still fails, escalate to the operator instead of spinning

## Anti-Pattern: Hide the Cause

Don't silently retry without logging. The `WARN: validator rejected ...` line preserves the signal that the cache went stale, which is operationally useful (you can correlate frequency with restarts, time-of-day, load, etc.). Reactive retries that hide their work make the cache failure invisible until it stops auto-recovering.

## Anti-Pattern: Pre-emptive Refresh

A pre-emptive refresh-on-every-call appears safer but doesn't actually fix the bug — it just papers over it on the caller side while leaving the cache layer broken. Other callers (CLI users, other scripts) still hit the failure. A reactive retry contains the workaround at the failing surface AND keeps pressure on the underlying cache bug to get fixed.

## Grounding

Direct empirical evidence from [project] session 2026-05-15:
- `gt convoy create` failing daily at 13:01 UTC for 3+ days with `validation failed for issue hq-cv-XXXX: invalid issue type: convoy`
- `bd config get types.custom` in `~/gt/.beads` confirms `convoy` IS in the allowed-types list
- Manual `bd config set types.custom <same value>` refreshes the cache and the next `gt convoy create` succeeds
- Pre-fix workaround was the user running the refresh manually; post-fix the create_convoy() function catches the signature and retries automatically
- Refresh helper smoke-tested directly against ~/gt before commit (8fb2e14)

## Related Entries

- `diagnostics/2026-05-15_bd-validator-cache-requires-unset-reset-refresh.md` — the specific stale bd validator cache diagnostic; this pattern describes the general recovery shape

## When This Applies

- Cached validation gates that can go stale between invocations
- Configuration caches that require a write-to-invalidate cycle
- Async index caches where refresh is cheaper than invalidation signals

## When This Does NOT Apply

- Caches with complex invalidation semantics (eventual-consistency, distributed coordination)
- Downstream services where the refresh has side effects (config changes, state mutation)
- Failure modes that mask underlying correctness bugs (use a reactive retry only for known, bounded stale-cache issues, not unknown failures)

## Source Context

Direct evidence from [project] convoy-validator troubleshooting session (2026-05-15). The reactive refresh+retry pattern emerged as the cleanest solution to a recurring stale-cache validation failure in the GasTown bd CLI, where the config layer was correct but the validator cache required a refresh cycle.
