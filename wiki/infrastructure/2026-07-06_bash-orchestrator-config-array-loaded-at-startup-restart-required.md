---
title: Bash long-running orchestrator config arrays loaded at startup — restart required to add new sessions
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.80
staleness_risk: slow_decay
importance: 3
created: 2026-07-06
domain: infrastructure
topic: ops
tags: [deployment, empirical, stable]
related_entries: ["infrastructure/2026-06-10_launchd-subprocess-shell-alias-resolution-gotcha.md", "infrastructure/2026-05-14_idempotent-watchdog-producer-pattern.md"]
---

# Bash Long-Running Orchestrator Config Arrays Loaded at Startup

## Pattern

When a bash script runs as a long-lived daemon or orchestrator process (managed by launchd, systemd, or cron), configuration arrays defined at the top of the script are evaluated **once at process startup**. The running process maintains its own in-memory copy — it does NOT re-source the script file or re-evaluate the array on each iteration.

This is standard bash behavior, not a bug. But it creates a hidden trap: hand-editing the script to add new items to a config array will have NO EFFECT on the already-running process.

## Concrete Grounding

Verified 2026-07-06 during [project] happy-orchestrator session management.

**Setup:** `happy-orchestrator.sh` defines a SESSIONS array at the top:
```bash
SESSIONS=(
    "cos-manager"
    "lookout-scanner"
    "kf-debug"
)
```

The orchestrator runs as a launchd daemon (PID 1840, started 2026-07-03). The monitor loop iterates over `${SESSIONS[@]}` on each tick:
```bash
while true; do
    for session in "${SESSIONS[@]}"; do
        # launch, monitor, backoff logic
    done
    sleep "$MONITOR_INTERVAL"
done
```

**Scenario:** On 2026-07-06, `cos-manager` was added to the SESSIONS array in the script (line 70). The already-running orchestrator (PID 1840) had no knowledge of the new entry.

**Symptoms:**
- `tmux list-sessions` showed no `cos-manager` session
- Orchestrator log (`tail ~/agent-workflow/happy-orchestrator.log`) had zero mentions of cos-manager since 2026-07-03 startup
- No backoff state existed for cos-manager (`ls /tmp/happy-backoff-state/` showed nothing for that name)
- No pause flag existed (`~/.config/happy/paused-cos-manager` absent)

**Why:** The running orchestrator process had its own in-memory SESSIONS array captured from the 2026-07-03 startup. Editing the script file changed the disk state but not the running process's memory.

**Resolution:** Restarted the orchestrator via launchctl:
```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.happy.orchestrator.plist
# Wait 2-3 seconds for graceful shutdown
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.happy.orchestrator.plist
```

The new orchestrator process (PID 23962, restarted 18:27:45) re-read the script, evaluated the updated SESSIONS array, and launched `cos-manager` at 18:29:08 — first log entry "cos-manager: launched and prompts accepted".

Existing tmux sessions (`lookout-scanner`, etc.) survived the orchestrator restart because they are independent tmux processes, not children of the orchestrator.

## Diagnostic signals before restart

Before concluding a session is "missing" from orchestrator management:

1. **Check if orchestrator is still running:**
   ```bash
   cat /tmp/happy-orchestrator.lock  # get the PID
   ps -p $(cat /tmp/happy-orchestrator.lock) > /dev/null  # verify it's alive
   ```

2. **Scan orchestrator logs for the session name:**
   ```bash
   tail -100 ~/agent-workflow/happy-orchestrator.log | grep "<session_name>"
   ```
   If the session name never appears since orchestrator startup, the in-memory SESSIONS array doesn't include it in the running instance.

3. **Confirm it's not a pause state issue:**
   ```bash
   ls -la ~/.config/happy/paused-<name>  # if this doesn't exist AND step 2 showed no log entry, it's an in-memory gap
   ```

4. **Double-check the script's SESSIONS array:**
   ```bash
   grep -A 30 'SESSIONS=' ~/Scripts/[project]/scripts/happy-orchestrator.sh
   ```
   Verify the session name is there on disk.

## When this applies

- Adding a new orchestrated session to a running daemon's config array
- Any hand-edit to a config array in a long-running bash process
- Deploying config changes that are read once at startup, not on each iteration
- Verifying that a manual edit to a script file has taken effect in a running process

## When this does NOT apply

- Pause flag toggling (`/happy-enable`, `/happy-disable`) — those work via filesystem flags read on each monitor tick, not the SESSIONS array
- Backoff state changes — also per-filesystem, persist and refresh without restart
- Sessions already in the SESSIONS array when the orchestrator started — the monitor loop handles those fine (restart, backoff logic, pause/enable transitions)
- Edits to functions or logic blocks — those are re-sourced if the script explicitly re-sources itself mid-run, but config arrays don't get re-evaluated unless the whole script does

## Related patterns

- **Config-at-startup latching:** Any long-running process that reads and caches config in memory exhibits this pattern. Even if the cache is explicitly refreshed (e.g., re-sourcing the script), hand-edits to a script don't affect running instances unless the process calls that refresh logic.
- **Launchd daemon lifecycle:** See infrastructure/2026-06-10_launchd-subprocess-shell-alias-resolution-gotcha.md for other launchd-spawned process gotchas.
- **Idempotent watchdog pattern:** See infrastructure/2026-05-14_idempotent-watchdog-producer-pattern.md for daemon supervision best practices that avoid this trap via config files + reload signals.

## Source Context

[project] cos-manager startup integration, 2026-07-06. Adding cos-manager to the happy-orchestrator SESSIONS array in the script had no effect on the running orchestrator (started 2026-07-03) because bash arrays are evaluated once at script execution time, not re-read on each iteration. The fix was a launchctl restart to spawn a new orchestrator process that re-evaluates the updated SESSIONS array from disk.
