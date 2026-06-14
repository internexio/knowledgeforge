---
title: macOS tmp_cleaner silently deletes /tmp files held open by long-running daemons — keep StandardOutPath outside /tmp
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-10
tags: scheduling, observability, filesystem, quality-gate, stable
related_entries:
  - infrastructure/2026-06-10_launchd-subprocess-shell-alias-resolution-gotcha.md
  - infrastructure/2026-05-14_idempotent-watchdog-producer-pattern.md
  - infrastructure/2026-05-15_silent-success-scripts-state-artifact-freshness.md
---

# macOS tmp_cleaner Silently Deletes Daemon Stdout Files

## Pattern

macOS ships a system-level cleaner at `/System/Library/LaunchDaemons/com.apple.tmp_cleaner.plist` that runs `/usr/libexec/tmp_cleaner` daily at 00:00 (`StartCalendarInterval.Hour=0`, `LowPriorityIO=true`, `Nice=1`). It deletes files in `/tmp` whose access time exceeds a threshold (typically 3 days). A long-running daemon whose `StandardOutPath` / `StandardErrorPath` lives in `/tmp/` is vulnerable:

- The daemon writes to the file periodically, but **writes don't reliably update atime** in macOS's default mount options (especially noatime/nodiratime variants used on APFS).
- When tmp_cleaner runs, it unlinks the file out from under the daemon.
- The daemon's fd1/fd2 are now held against a *deleted inode* — visible in `lsof -p <pid>` as `REG ... <inode> /private/tmp/<name>.stdout` where the path no longer exists on the filesystem.
- Python (and most other languages) keep writing to the deleted-inode fd. The bytes vanish. The daemon does not get an EBADF or EPIPE.
- In some configurations the daemon then *also* stops making progress on other channels (asyncio loops, callback polls, etc.) — the actual failure mode that gets noticed.

## Concrete grounding

Verified 2026-06-09 → 2026-06-10 against the [project] `orchestra-telegram-bridge` daemon (PID 2527, started Jun 4):

- 2026-06-09 12:15:30Z: bridge stopped logging entirely (last entry to its `.log` file at this time).
- 2026-06-09 19:18Z (~7 hours later): `lsof -p 2527` showed `Python 2527 dp 1u REG 1,16 0 129308431 /private/tmp/[project]-orchestra-telegram-bridge.stdout` — size 0, inode 129308431 was DELETED (file no longer at that path).
- The bridge process was still alive, claiming to be a daemon, but polling Telegram had stopped.
- `launchctl kickstart -k` restarted the daemon; new fd1/fd2 on fresh inodes worked correctly.

We initially blamed our own `scripts/nw-maintenance.sh` (runs at 05:00 via launchd) but verified it never touches `/tmp/` — the culprit was the system tmp_cleaner.

## Fix

Never use `/tmp/` for `StandardOutPath` or `StandardErrorPath` on a daemon that needs to live for more than ~3 days. Use a user-owned directory like `~/.[project]/logs/` (or whatever the app's convention is). Tmp_cleaner never touches `~/`.

```xml
<!-- BAD -->
<key>StandardOutPath</key>
<string>/tmp/myapp.stdout</string>

<!-- GOOD -->
<key>StandardOutPath</key>
<string>/Users/foo/.myapp/logs/myapp.stdout</string>
```

Add a daemon health check that detects this class of failure even after migration:

- For daemons that write to a separate `.log` file, monitor that file's mtime (proxy heartbeat).
- For daemons that write a dedicated heartbeat file, monitor that file's mtime directly.
- Threshold 5 min during business hours; auto-kickstart on staleness is safe because daemons should be respawn-tolerant by `KeepAlive`.

Reference: [project] `scripts/happy-healthcheck.sh` Check 9 (added same day): `gt escalate -s HIGH` + `launchctl kickstart -k` on bridge log mtime >5 min stale.

## When This Applies

Any macOS LaunchAgent or LaunchDaemon that:

- Lives for more than ~3 days continuously.
- Has StandardOutPath / StandardErrorPath set.
- Writes to those paths only intermittently (so atime doesn't get refreshed reliably).

Especially likely to bite:

- Polling daemons that mostly log to a separate file (not stdout).
- Background workers whose normal operation is quiet.
- Any daemon installed during a "just put it in /tmp for now" early development phase that then ships to production.

## When This Does NOT Apply

- Short-lived processes (timer-triggered jobs that exit between fires).
- Daemons that log every poll cycle to stdout/stderr (atime refresh keeps tmp_cleaner from pruning).
- Linux systems (atime semantics + cleanup policies are different; `tmpfiles.d` behaves differently and is configurable).

## Diagnostic Signal

A daemon that's `launchctl list`-visible with a valid PID but no recent log entries, AND `lsof -p <pid>` shows fd1 or fd2 pointing at a REG inode in `/private/tmp/` that does not exist on disk. The classic "held-deleted-inode" signature.

Detection one-liner:

```bash
lsof -p $(launchctl list <label> | awk -F'= ' '/PID/{gsub(";",""); print $2}') \
  | awk '$4 ~ /^[12]/' | grep "/tmp"
```

If the result shows a path that no longer exists on the filesystem (e.g., `REG 1,16 0 129308431 /private/tmp/name.stdout` where `ls /private/tmp/name.stdout` returns "no such file"), the file has been deleted while the daemon holds the fd open.

## Source Context

[project] `fys7` bridge silent-wedge investigation (2026-06-10). The orchestra-telegram-bridge daemon stopped writing logs silently overnight. Diagnosis took ~7 hours because the process was still running and heartbeat signals (via Telegram API polling) were intermittent; the obvious check (process existence) passed.
