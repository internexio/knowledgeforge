---
title: Launchd cron-style vs persistent-daemon misread — PID `-` is not "down"
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 4
pinned: false
created: 2026-07-05
tags: quality-gate, empirical, stable
related_entries: []
domain: diagnostics
topic: system-integration
---

# Launchd cron-style vs persistent-daemon misread — PID `-` is not "down"

## The trap

`launchctl list | grep <name>` shows a leading dash where the PID column would be:

```
-	0	com.[project].orchestra-autopoll
```

Natural reading: "the daemon is down." Kickstart it.

That reading is wrong when the plist is **cron-style** — `StartInterval` (or `StartCalendarInterval`) + `RunAtLoad`, no `KeepAlive`. Such a job runs briefly (often <5s), exits cleanly, then launchd waits for the next interval and fires it again. In between, `launchctl list` shows PID `-` and `state = not running`. That is the **designed** steady state, not an outage.

## Verify before restarting

Before concluding "daemon down," check the plist for the pattern:

```bash
grep -A1 -E 'StartInterval|KeepAlive|StartCalendar|RunAtLoad' \
    ~/Library/LaunchAgents/<name>.plist
```

- `KeepAlive = true` + no `StartInterval` → persistent daemon; `PID = -` IS a problem.
- `StartInterval = <seconds>` + `RunAtLoad = true` + no `KeepAlive` → cron-style; `PID = -` between fires is normal.

Real failure signals for a cron-style plist:

- `runs` count not incrementing across successive `launchctl print` calls
- `last exit code != 0`
- `.stderr` growing with tracebacks (`~/.[project]/logs/<name>.stderr` on this fleet)
- App-level `.log` gaps that exceed `StartInterval` × 1.5

## Recovery

If the diagnosis is "cron-style, not currently in its run window," no action is needed — the next interval-tick will fire it. `launchctl kickstart -k gui/$UID/<name>` forces an immediate on-demand run, which is safe but usually unnecessary.

## When This Applies

- Any macOS `LaunchAgent` / `LaunchDaemon` with `StartInterval`
- Any triage or watchdog that treats `PID = -` as "process crashed"
- Any operator-facing report that says "daemon down" without also checking the plist type

## When This Does NOT Apply

- Persistent daemons declared with `KeepAlive = true`. There `PID = -` combined with `last exit code != 0` and no immediate relaunch IS a failure.
- Cron-style jobs that ARE within their expected run window but show no activity — that's a stall, not a "designed steady state."

## Source Context

[project] session 2026-07-04: `orchestra-autopoll` misdiagnosed as down after a `dz6m` timeout-bump ship. `launchctl list` showed PID `-`; assumed the daemon had exited and needed a kickstart. Kickstart succeeded but was cosmetic — the plist header explicitly says "Not KeepAlive — this is a one-shot cron-style poll, not a daemon." `runs = 101, last exit code = 0` confirmed 15-min cadence had been running fine. False alarm cost: one kickstart + operator attention. The user's follow-up ("investigate why it was down") caught the misread.
