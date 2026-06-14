---
title: tmux display-message #{pane_pid} race after new-session — single-sample checks false-positive
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-06-13
domain: diagnostics
topic: watchdog
tags: watchdog, empirical, stable, scheduling
related_entries: ["infrastructure/2026-05-16_pane-content-idle-patterns-mtime-liveness-signal.md", "infrastructure/2026-05-12_self-watchdog-autonomous-fix-cycles.md", "infrastructure/2026-06-12_explicit-heartbeat-file-liveness-signal-sparse-loggers.md"]
---

# tmux display-message #{pane_pid} Race After new-session — Single-Sample Checks False-Positive

## Finding

`tmux display-message -t <session> -p '#{pane_pid}'` can return an empty string in the immediate window after `tmux new-session -d`, even when the session is healthy and the pane process is running.

A watchdog that does:

```bash
tmux new-session -d ... && sleep 10 && PID=$(display-message -p '#{pane_pid}') && kill -0 "$PID"
```

will intermittently see `PID=""` and conclude the session failed — when in fact the session is fine and the pane process is running normally.

The race window is sub-second in most cases but extends when the system is under load (many sessions launched in stagger, fork+exec contention).

## Concrete Grounding

Observed in `scripts/happy-orchestrator.sh` of the [project] repo (2026-06-13, bead `[project]-7jy4`). The orchestrator launches sessions with a 15s stagger, then runs a post-launch stability check at +10s. The check was:

```bash
launch_session "$NAME" "$WORKDIR"
sleep 10
if $TMUX_BIN has-session -t "$NAME" 2>/dev/null; then
    PANE_PID=$($TMUX_BIN display-message -t "$NAME" -p '#{pane_pid}' 2>/dev/null || true)
    if [ -n "$PANE_PID" ] && kill -0 "$PANE_PID" 2>/dev/null; then
        log "$NAME: restart succeeded"
    else
        record_failure "$NAME"   # FALSE POSITIVE
    fi
fi
```

Production log evidence (2026-06-13 21:22-21:24 UTC):

```
21:22:18 [project]: launched and prompts accepted
21:22:29 [project]: failure #1 recorded            ← 11s later, false positive
21:23:47 [project]: attempting restart (attempt 2)
21:23:55 [project]: launched and prompts accepted
21:24:05 [project]: failure #2 recorded            ← 10s later, false positive
...
21:29:36 [project]: session stable, resetting backoff (was at attempt 2)
```

The session passed the 3-minute stability check (separate code path), proving it was healthy throughout — but the 10s post-launch check recorded two spurious failures that fed a global-cooldown counter.

## Fix Pattern

Replace the single check with a poll loop (every 2s up to 30s). Gate success on a stable signal pair:

```bash
LAUNCH_OK=false
POLL=0
while [ "$POLL" -lt 15 ]; do
    POLL=$((POLL + 1))
    sleep 2
    $TMUX_BIN has-session -t "$NAME" 2>/dev/null || continue
    PANE_PID=$($TMUX_BIN display-message -t "$NAME" -p '#{pane_pid}' 2>/dev/null || true)
    [ -n "$PANE_PID" ] && kill -0 "$PANE_PID" 2>/dev/null || continue
    # Gate on pane_current_command + last non-blank pane line so a
    # shell-only pane (target program exited) still records as failure:
    PANE_CMD=$($TMUX_BIN display-message -t "$NAME" -p '#{pane_current_command}' 2>/dev/null)
    LAST_LINE=$($TMUX_BIN capture-pane -t "$NAME" -p 2>/dev/null | grep -v '^$' | tail -1)
    case "$PANE_CMD" in
        zsh|-zsh|bash|-bash|sh|-sh|fish|-fish|dash)
            # PANE shows a shell prompt? Target program is dead — keep polling.
            if echo "$LAST_LINE" | grep -qE '^[A-Za-z0-9._-]+@[A-Za-z0-9._-]+ .+[%$#][[:space:]]*$'; then
                continue
            fi
            ;;
    esac
    LAUNCH_OK=true; break
done
```

First green poll exits early — healthy sessions feel fast. Truly-dead sessions wait the full 30s before `record_failure`. Both behaviors match the steady-state monitor's existing check semantics.

## When This Applies

- Any bash/sh watchdog that uses `tmux display-message ... #{pane_pid}` immediately after `tmux new-session -d`.
- Multi-session launchers (orchestrators, parallel test runners) where the stagger overlaps with the per-session post-launch check.
- High-load systems where fork+exec contention extends the race window.
- Post-session-creation stability checks where a single sample (wait N seconds then test once) is insufficient to wait out tmux's internal state settling.

## When This Does NOT Apply

- `tmux display-message` queries against a session that has existed for many seconds are reliable — the race is specifically post-new-session.
- Interactive use (attaching to sessions with `tmux attach`) — humans do the retry implicitly by reading the screen.
- Watchdogs that observe only at steady state (e.g., periodic health checks every N minutes) rarely hit the race because the new-session moment is rare.
- Sessions created with explicit initialization delays (e.g., `tmux new-session -d ... && sleep 30 && ...`) where the sleep is already >= 20 seconds.

## Why a Single sleep+check Isn't Enough

The instinct is "I waited 10 seconds, the session must be settled by now." But the race isn't about the pane process taking time to start — it's about tmux's internal state. `display-message` can read state before the `pane_pid` field is populated even though the pane is alive. The poll loop handles this without needing to know the tmux internals — it repeatedly tests until the signal stabilizes.

## Diagnostic Verification

To confirm whether a watchdog is hitting this race:

1. **Check if false positives cluster around new-session events:** grep the orchestrator logs for `failure recorded` immediately after launch attempts (within 5-15 seconds). Healthy sessions that later pass the longer stability check are a strong signal.
2. **Monkeypatch the launch to add logging:** insert `display-message` queries at 0s, +2s, +4s post-launch to see when `pane_pid` becomes non-empty.
3. **Correlate with system load:** the race extends when the box is busy. Run the same launcher under different loads (idle vs. concurrent builds) and measure failure rate delta.

## Related

- **Pane-content idle patterns** (2026-05-16) — complementary diagnostic for mtime-based liveness checks; addresses false positives from idle sessions, not race conditions.
- **Self-watchdog** (2026-05-12) — meta-pattern for watchdogs that monitor their own liveness.
- **Explicit heartbeat file** (2026-06-12) — alternative signal to replace both `display-message` polling and mtime-based schemes when applicable.

## Source Context

Discovered 2026-06-13 during [project] bead `[project]-7jy4` (fix to happy-orchestrator.sh post-launch stability checks). The orchestrator was recording two spurious session-launch failures in the same session's lifetime, both traced to `display-message` returning empty on the 10s post-launch check while the session was actually healthy. Prompted investigation of tmux's internal initialization timing and led to the polling pattern as a robust replacement for single-sample checks.
