---
title: DriveFS write safety via SIGALRM (companion to read-safety pattern)
type: transferable_framework
date: 2026-06-25
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 3
tags: [drivefs, gdrive, timeout-guard, sigalrm, macos, write-safety]
domain: patterns
topic: retrieval
---

# DriveFS write safety via SIGALRM (companion to read-safety pattern)

The companion to the existing GDrive READ-safety pattern documented in the operator's global CLAUDE.md (`gdrive-read.sh` timeout-guarded helper for reads, `signal.SIGALRM` pattern in `nw-morning.py` `_with_timeout`). This entry covers the WRITE side, which has different failure modes but the same safety primitive.

## Core pattern

Wrap any write to a DriveFS path (`~/Library/CloudStorage/GoogleDrive-...`) with `signal.SIGALRM` to prevent indefinite hang when DriveFS sync is stalled. Standard `cp` command has no native timeout on macOS (the `timeout` GNU coreutils command is not installed by default).

## Python implementation

```python
import os, signal, shutil
from pathlib import Path

def alarm_handler(signum, frame):
    raise TimeoutError("Drive operation timed out — DriveFS may be stalled")

signal.signal(signal.SIGALRM, alarm_handler)
signal.alarm(15)  # 15-second deadline
try:
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
finally:
    signal.alarm(0)  # always clear the alarm
```

## Timeout choice

- 10–15 s is a reasonable upper bound for a write to DriveFS
- Small files (< 1 MB) usually write in <1 s; the timeout exists to bound the BAD case, not the typical case
- Don't set <5 s — DriveFS write latency varies, false positives waste a retry

## Failure modes this guards against

- DriveFS sync stalled, write blocks indefinitely
- DriveFS in "no_user" / "Core is not running" state (per global CLAUDE.md note about 4-account limit)
- Write to a parent dir that's actually stale-orphaned after DriveFS reconnect (operator's global CLAUDE.md documents this — after disconnect/reconnect, Drive remounts under a NEW timestamped dir, orphaning the old path)

## When to apply

- Any write to `$GDRIVE_OUTPUT` or any DriveFS mount path
- Inside Python or Python-via-bash invocations
- Critical writes where hanging is worse than failing-loud

## When NOT to apply

- Writes to local non-DriveFS paths — alarm overhead is unnecessary
- Inside an async event loop — SIGALRM only works on main thread

## Concrete grounding (2026-06-25)

- Operator: "Copy the file to the shared drive"
- Source: `wiki/reference/2026-07-28_seattle-tech-week.md` (19,607 bytes)
- Destination: `$GDRIVE_OUTPUT/research/2026-07-28_seattle-tech-week.md`
- Implementation: Python heredoc, SIGALRM with 15 s timeout, `shutil.copy2`
- Actual write time: <1 s (alarm never fired)
- Worked cleanly; the timeout-guard was the right precaution even though unnecessary in this run

## Related

- Global CLAUDE.md "## Cross-Machine Shared Context (Google Drive)" — read-safety patterns + DriveFS stall symptoms + reconnect-orphan-dir gotcha
- `[project]/scripts/gdrive-read.sh` — read companion (timeout-guarded shell)
- `[project]/scripts/nw-morning.py` `_with_timeout()` — Python signal.SIGALRM read-side pattern
- macOS `timeout` command absence — separate pattern worth its own CLAUDE.md note: `timeout 10s cp ...` returns "command not found: timeout" on stock macOS; install GNU coreutils via `brew install coreutils` (provides `gtimeout`), or use Python SIGALRM as documented here
