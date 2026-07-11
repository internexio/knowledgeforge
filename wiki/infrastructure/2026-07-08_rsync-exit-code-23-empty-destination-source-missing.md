---
title: rsync exit code 23 with empty destination — source directory missing creates dir but transfers nothing
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.88
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-08
domain: infrastructure
topic: deployment
tags: rsync, ci-cd, debugging, gotcha, infrastructure
related_entries:
  - infrastructure/2026-05-20_static-site-rsync-excludes-leak-prevention.md
  - diagnostics/2026-05-18_http-status-signatures-deploy-verification-smoke-test.md
---

# rsync Exit Code 23: Empty Destination When Source Directory Missing

## What Happens

When rsync is invoked with a source path that doesn't exist, it exits with code 23 ("partial transfer due to error") but still creates the destination directory on the remote host. The destination exists but is empty. The source error is in the rsync sender output, making it easy to miss if you're only checking exit codes or the remote filesystem.

## Failure Signature

```
rsync: [sender] change_dir "/path/to/source" failed: No such file or directory (2)
sending incremental file list
created directory /path/to/destination
rsync error: some files/attrs were not transferred (see previous errors) (code 23) at main.c(1356) [sender=3.2.7]
sent 44 bytes  received 69 bytes  ...
total size is 0  speedup is 0.00
```

Key indicators:
- `change_dir "..." failed: No such file or directory` — source doesn't exist
- `created directory ...` — rsync still creates the destination
- `total size is 0` — nothing transferred despite apparent "success"
- Exit code 23, not 11 (which would indicate permission denied on destination)

## Why It's Confusing

1. rsync still exits with 23 (not the more obvious "connection failed" or "permission denied" codes), and the destination creation line makes it look like rsync at least partially worked.
2. With `continue-on-error: true` in GitHub Actions, the step shows ✓ (green) despite exit code 23.
3. Checking only the remote filesystem (`ls /path/to/destination`) shows the directory exists, making it look like deployment succeeded when nothing was actually copied.

## Root Cause Lookup

When you see rsync exit 23 with an empty destination:

1. Check the rsync sender output (earlier in the log) for `change_dir "..." failed`
2. Verify the source path actually exists: `ls -la <source-path>` on the runner
3. If in CI, check whether the checkout step that was supposed to create the source directory actually ran and succeeded (not masked by `continue-on-error`)

## rsync Exit Code Reference (Relevant Codes)

| Code | Meaning |
|------|---------|
| 0 | Success |
| 11 | Error in file I/O (often permissions on destination) |
| 23 | Partial transfer — some files/attrs not transferred (source missing, permissions, etc.) |
| 24 | Partial transfer — some files vanished during transfer |
| 35 | Timeout in data send/receive |

## When This Applies

- rsync targets a source path expected to exist
- Source directory is missing or doesn't contain the expected structure
- CI/CD workflow has `continue-on-error: true` or otherwise masks non-zero exit codes
- Remote filesystem checks (e.g., `ls /path/to/destination`) are the only verification step
- Deployment proceeds as though files were transferred when they were not

## When This Does NOT Apply

- rsync exits 11 (destination permissions issue — different cause)
- rsync exits 0 (genuine success)
- Source path exists but files inside it are missing (rsync would succeed with 0 bytes transferred, no error)
- Exit code is checked and deployment halts on non-zero (correct safeguard)

## Grounding

Directly observed in GitHub Actions CI runs 28907771276 and 28908485041 (SEMalytics/cos). In both runs, the `client-project/site/` source path was missing because `actions/checkout@v4` with a broken sparse-checkout pattern didn't create it. rsync created `/var/www/semalytics.com/ads/` on the production server but transferred 0 bytes. Confirmed via `ssh cos "ls -la /var/www/semalytics.com/ads/"` showing the directory existed but was empty.

## Source Context

Discovered during [project] CI debugging (2026-07-08, session [project]-ci-ads-deploy-2026-07-08). GitHub Actions workflow had `continue-on-error: true` on the rsync step, masking the exit code 23 as success. Post-deploy verification found the destination directory created but empty, while logs showed the typical "partial transfer" message.
