---
title: Happy file-watcher ghost session_id — detection + absolute-path symlink fix
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-05-21
domain: diagnostics
topic: root-cause-analysis
tags: filesystem, temporal, diagnostics, symlink, happy-cli, tooling, node-fs-watch
related_entries:
  - diagnostics/2026-05-18_happy-cli-filewatcher-ghost-session-mismatch.md
revises:
  - diagnostics/2026-05-18_happy-cli-filewatcher-ghost-session-mismatch.md
superseded_by: null
---

# Happy File-Watcher Ghost Session_id — Detection + Absolute-Path Symlink Fix

## Problem

Happy CLI launchers mint a `session_id` UUID at tmux session creation and bind their file-watcher to `<claude_project_dir>/<that_uuid>.jsonl`. The inner Claude process often mints its own session_id (or uses `--resume <other_id>`), so the file-watcher loops forever on `ENOENT: no such file or directory ... restarting watcher in a second` at 1Hz. Symptom is silent UI breakage — output truncates mid-response and the next prompt surfaces "Process exited unexpectedly". On long-running sessions the loop accumulates 100K+ retries before being noticed.

Reproduced this session on 4 different sessions concurrently: sem-tools, 5sb-paid-ads, tuannw, semalytics-gtm.

## Detection Heuristic — Don't Use Cumulative Count

The naive check is:
```bash
for log in ~/.happy/logs/*pid*.log; do
  count=$(grep -c 'FILE_WATCHER.*ENOENT.*restarting' "$log")
  [ "$count" -gt 100 ] && echo "STUCK: $log ($count)"
done
```

This produces **false positives**. A session that was stuck for 18 hours and then resolved (via symlink fix or restart) still shows 100K+ cumulative ENOENT entries in its log forever. The log is append-only.

The correct heuristic combines two signals:

1. **Log mtime gate** — file written within the last ~30 seconds → loop is currently active
2. **Tail ENOENT count** — `tail -100 "$log" | grep -c ENOENT.*restarting` ≥ threshold (≥10 works) → currently looping, not just a brief blip

A log that hasn't been touched in 30+ seconds is inert regardless of its historical content. Use mtime first as a cheap reject filter, then check the tail.

## Fix — Symlink With ABSOLUTE Path

The Happy-side workaround is to symlink the ghost UUID jsonl to the real session's jsonl:

```bash
ln -sfn "$REAL_ABSOLUTE_PATH" "$GHOST_ABSOLUTE_PATH"
```

**The symlink target must be an absolute path.** A relative form (`ln -s real-uuid.jsonl ghost-uuid.jsonl` in the same dir) appears to succeed — `os.readlink()` returns the relative target, `os.path.exists()` returns True — but the node `fs.watch` in Happy's file-watcher continues to throw ENOENT. The loop never stops.

Why: `node`'s `fs.watch` and the `ln -s` resolver use different working-directory anchors at watch time vs. creation time. The kernel-level inotify equivalent on macOS may also handle the symlink chain differently when given a relative target.

This was verified concretely 2026-05-20 on the sem-tools session: an `ln -sfn d867fc00-....jsonl e65e3bda-....jsonl` (basename relative) left the watcher still looping at 18:04. After replacing with `ln -sfn ~/.claude/projects/-Users-dp-Scripts-sem-tools/d867fc00-....jsonl ~/.claude/projects/-Users-dp-Scripts-sem-tools/e65e3bda-....jsonl` (absolute), the loop stopped within 1 second.

## Cross-Directory Variant (Slug Mismatch)

A second variant: the Happy launcher computes the claude project_dir slug differently than the inner Claude does. Verified case: `~/.claude/projects/-Users-dp-Scripts-client-project/` (underscore — Happy's ghost dir, doesn't exist) vs `-Users-dp-Scripts-semalytics-gtm/` (hyphen — Claude's real dir, has the jsonl). The fix is to `mkdir -p` the ghost dir and then symlink across:

```bash
mkdir -p ~/.claude/projects/-Users-dp-Scripts-client-project
ln -sfn ~/.claude/projects/-Users-dp-Scripts-semalytics-gtm/<real>.jsonl \
        ~/.claude/projects/-Users-dp-Scripts-client-project/<ghost>.jsonl
```

When auto-detecting the slug variant, try `${slug//_/-}` and `${slug//-/_}` as fallbacks before declaring the case manual-triage.

## When This Applies

- You see `FILE_WATCHER Watch error: ENOENT ... restarting watcher in a second` in `~/.happy/logs/*.log`
- The UI of any Happy session has been silently breaking ("Process exited unexpectedly", output truncates mid-response)
- Periodically (every new Happy session is a fresh draw at this bug)

## When This Does NOT Apply

- The watcher error refers to a path that genuinely doesn't exist anywhere (no real jsonl in the project dir at all) — that's a different bug, possibly a process that died before writing its first event
- The session is in idle Remote Mode showing "Press space to switch to local mode" — that's the documented idle pattern, not a stuck watcher
- Cumulative ENOENT count is high but mtime is stale — false positive, ignore

## Reference Implementation

`scripts/check-happy-watchers.sh` in `~/Scripts/[project]/` (commit 5ce8915) — implements the mtime+tail detection heuristic, the absolute-path symlink fix, and the slug-variant cross-dir handler. Wired into `happy-healthcheck.sh` Check 6 so launchd applies fixes unattended every 5 min.

## Revision Notes

This entry **supersedes** the 2026-05-18 diagnostic (`happy-cli-filewatcher-ghost-session-mismatch.md`). The earlier entry identified the problem correctly but:
- Did not articulate why relative symlinks fail (appears to work but doesn't)
- Did not provide the critical mtime+tail detection heuristic (cumulative log count produces false positives)
- Did not cover the cross-directory slug-mismatch variant
- Did not provide the reference implementation integrated into launchd watchdog

Both entries should be indexed; cite this one as the authoritative detection + fix procedure.

## Source Context

Extracted from [project] debugging session 2026-05-20 (bead [project]-wzrj). Full diagnostic trace and reference implementation verified across 4 concurrent Happy sessions. The absolute-path symlink requirement was discovered by direct empirical test: relative symlink appeared to resolve correctly but left the node `fs.watch` looping indefinitely; absolute symlink stopped the loop in 1 second. This diagnostic has high reusability for any developer running Happy CLI on the same machine; the fixes are safe, immediate, and require no upstream Happy changes (though upstream should adopt detection + auto-fix).
