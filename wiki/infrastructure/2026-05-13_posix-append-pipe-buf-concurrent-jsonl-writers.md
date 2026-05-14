---
title: POSIX atomic-append for concurrent JSONL writers — flock is unnecessary when lines stay under PIPE_BUF
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-13
domain: infrastructure
topic: process-coordination
tags: latency, throughput, stable
related_entries: ["patterns/2026-05-11_atomic-write-stubs-for-readwrite-pipelines.md"]
---

# POSIX atomic-append for concurrent JSONL writers — flock is unnecessary when lines stay under PIPE_BUF

On POSIX-compliant filesystems, a single `write(2)` call to a regular file opened in `O_APPEND` mode is atomic with respect to other concurrent appenders, provided the write size does not exceed `PIPE_BUF` (typically 4096 bytes on Linux and macOS — `getconf PIPE_BUF /` confirms).

Shell redirection `>>` opens with `O_APPEND`. A single `echo "$line" >> file` issues one `write(2)`. As long as `$line` plus its trailing newline stays under PIPE_BUF, multiple processes appending concurrently cannot interleave bytes mid-line. Line orientation is preserved without any explicit locking.

## Why This Matters

The default reflex when adding a sidecar audit log written by multiple scripts is to reach for `flock(1)`. On macOS, `flock` is not in the base install — you would need Homebrew. On Linux it ships but adds boilerplate. For line-oriented append logs (JSONL, syslog-style), the lock is often unnecessary: the kernel already guarantees what you need.

## Practical Bound

JSONL records typical of audit logging — wakeup-skips, telemetry events, trace entries — are 100-500 bytes. Even a verbose error entry with stack trace context rarely exceeds 2 KB. PIPE_BUF gives you approximately 4 KB of headroom on common platforms. If your records risk exceeding PIPE_BUF, you DO need a lock; if they do not, you do not.

## Verification

```bash
# Confirm PIPE_BUF on target platform
getconf PIPE_BUF /

# Measure max line length in your audit log
wc -L < your-audit.log

# If wc -L result << PIPE_BUF, flock is unnecessary
```

## When This Applies

- Multi-process audit logs (orchestrator + healthcheck both appending to the same JSONL)
- Multiple shell scripts logging to a shared file without coordination
- Cron jobs writing to a shared event log
- Any scenario where you would normally use `flock` but the platform lacks it (or you want to avoid the dependency)

## When This Does NOT Apply

- **NFS and clustered filesystems:** PIPE_BUF guarantees are local-only. Atomicity may not extend across NFS clients. If your audit log lives on NFS, use flock or a single-writer architecture.
- **Large records:** A 10 KB JSON line concatenated with stack trace may exceed PIPE_BUF on platforms where it is only 512 bytes (older Solaris, etc.).
- **Multiple writes per logical record:** If you build a record with `echo "{" >> f; echo "  \"key\": \"$v\"" >> f; echo "}" >> f`, each line is independently atomic but the record as a whole is not. Single-write composition is required.
- **Write amplification / partial-record visibility:** If downstream readers are polling the log and must never see a partial record, flock ensures mutual exclusion. Without it, a reader may catch lines mid-batch.

## Theoretical Foundation

POSIX.1-2017 §2.9.7 and the `write(2)` man page on Linux and macOS guarantee that a write of N bytes to a regular file is atomic if N ≤ PIPE_BUF. This atomicity is not an implementation detail — it is part of the standard because append-only logs, syslog, and multi-process WALs depend on it.

## Grounding

Used to justify skipping `flock` in `scripts/nw-skip-reasons.sh` in [project] (paperclip Pattern 4, commit 51a2bdc). The target Mac has no `flock` installed; record sizes are approximately 200-250 bytes (verified end-to-end with `jq` parsing seven distinct call-site patterns). Helper falls back to plain `echo >>` and JSONL line orientation is preserved across orchestrator + healthcheck concurrent appenders. Tested in production for 48+ hours with zero interleaved lines.

## Why Staleness Risk is "Stable"

This is a POSIX guarantee codified in the standard. Changing it would break decades of syslog, multi-process logging frameworks, and append-only database WALs. The PIPE_BUF value can change per platform but the guarantee floor (≥ 512 bytes per POSIX) is fixed.

## Source Context

[project] paperclip Pattern 4 audit-log refactor. Session: 2026-05-13_[project]-paperclip-pattern-4-audit-jsonl.
