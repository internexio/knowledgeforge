---
title: Explicit heartbeat file beats log-mtime as a liveness signal for processes that log only on errors
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.8
staleness_risk: stable
importance: 4
created: 2026-06-12
domain: infrastructure
topic: observability
tags: scheduling, temporal, quality-gate
related_entries:
  - infrastructure/2026-06-10_macos-tmp-cleaner-daemon-stdout-deletion.md
  - infrastructure/2026-05-15_silent-success-scripts-state-artifact-freshness.md
  - infrastructure/2026-05-14_idempotent-watchdog-producer-pattern.md
  - infrastructure/2026-05-12_self-watchdog-autonomous-fix-cycles.md
---

# Explicit Heartbeat File Beats Log-mtime as a Liveness Signal for Sparse-Logging Processes

## Problem

A long-running daemon's logger is configured to emit only on errors, warnings, or specific events (callback received, request completed, etc.). Healthy idle operation produces zero log writes for arbitrary stretches — minutes, hours, even days when the upstream is quiet. An external watchdog proxying liveness through the log file's mtime cannot distinguish healthy idle from a wedged poll loop. Either:

- **Threshold too low** → constant false-positive alarms / churn-kickstarts during normal quiet periods.
- **Threshold too high** → real wedges go undetected for hours.

## Rule

When the daemon's logger does not write per-iteration by design, do not use the log file as a heartbeat. Add an explicit heartbeat file that the main loop touches at the top of every iteration:

```python
HEARTBEAT = Path.home() / ".[project]" / "bridge-heartbeat"  # outside /tmp

def _heartbeat() -> None:
    try:
        HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
        HEARTBEAT.touch()
    except OSError as exc:
        logger.warning("heartbeat touch failed: %s", exc)

while not _shutdown:
    _heartbeat()         # BEFORE the work — a wedge inside the work
    try:                 #   path leaves the heartbeat stale
        do_one_iteration()
    except Exception as exc:
        logger.error("...")
        time.sleep(5)
```

Watchdog reads `stat -f %m $HEARTBEAT`. Threshold = a comfortable multiple of the natural iteration period.

## When This Applies

- Daemons whose primary work is a poll/long-poll loop and whose logger only fires on errors/events (Telegram getUpdates, MCP SSE, etc.).
- Any long-running process where "alive but quiet" is a normal state.
- Situations where the log file's mtime is an unreliable signal because the daemon deliberately logs infrequently.

## When This Does NOT Apply

- Daemons that already log per-iteration (e.g. request servers with INFO-level access logs). Their log mtime is a fine heartbeat.
- Short-lived scripts where launchd's KeepAlive + ExitStatus tracking is sufficient liveness on its own.
- Monitoring scenarios where the state artifact (not the log) already signals successful execution (see **silent-success-scripts** pattern).

## Design Constraints

- **Heartbeat file path must live outside `/tmp/`**. On macOS, `com.apple.tmp_cleaner` prunes /tmp files daily and the heartbeat becomes the next failure mode. Place under `~/.[project]/` or similar home-rooted location with documented retention. (See **macos-tmp-cleaner** for the underlying mechanism.)
- **The touch must be safe_emit-guarded**. A filesystem error must not crash the poll loop — the heartbeat is observability sidecar, not authoritative work. Log on failure, do not raise.
- **Touch BEFORE the iteration body**, not after. A wedge inside the body (long-poll hang, blocked syscall) leaves the heartbeat stale, which is exactly the signal the watchdog needs.
- **One initial touch in `main()` before the loop**, so the watchdog doesn't false-fire during a slow startup window where the file doesn't yet exist.

## Watchdog-Side Considerations

- Compare `stat -f %m $HEARTBEAT` to `date +%s`; treat age > N seconds as stale.
- Persistent-stale must retry (first-detection-only kickstarts leak: if the first kickstart fails to recover, the wedge stays). Rate-limit retries to avoid storming launchd — structure mirrors the **idempotent-watchdog-producer** pattern.

## Concrete Grounding ([project], 2026-06-12)

`scripts/orchestra-telegram-bridge.py` logs only on errors/callbacks. Bridge PID 92398 was alive 40+ hours with last log entry 2026-06-11T14:33Z — could not distinguish from log mtime whether it was wedged or just idle. Real pattern from historical log: 3-5 hour stretches of silence between error bursts even during fully healthy operation. `happy-healthcheck` Check 9's 5-minute threshold against log mtime had been firing whenever the bridge was simply idle.

Commit 82f3659 added `_heartbeat()` touching `~/.[project]/bridge-heartbeat` at the top of the poll loop; switched Check 9 to read the heartbeat instead. Verified: kickstart → heartbeat fresh within 1s → updates every ~30s (matching getUpdates long-poll timeout) → Check 9 reads "ok" against fresh heartbeat.

## Related Patterns

- **silent-success-scripts** — *what file to monitor* for freshness checks (answers the watchdog's question: "which artifact proves the cycle ran?"). This pattern answers the daemon's question: "how do I emit that signal?"
- **macos-tmp-cleaner** — why heartbeat path must be outside /tmp.
- **idempotent-watchdog-producer** — the watchdog-side rate-limiting and dedup structure that consumes the heartbeat signal.
- **self-watchdog** — broader pattern for detecting when a cycle stops running entirely.

## Source Context

[project] bridge liveness monitoring, 2026-06-12. The orchestra-telegram-bridge daemon's logger is configured to emit only on errors/updates, creating ambiguity between "idle but healthy" and "wedged". Log-file mtime monitoring produced false positives during normal quiet periods. The explicit heartbeat file disambiguates by updating on every poll iteration regardless of whether the iteration produced loggable events. Pattern generalizes to any long-running daemon whose logging is sparse by design.
