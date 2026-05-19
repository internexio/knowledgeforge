---
title: Happy CLI file-watcher binds to ghost session_id that Claude never creates
source_mode: kf-debugger
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-05-18
domain: diagnostics
topic: root-cause-analysis
tags: api, filesystem, temporal, empirical, stable
related_entries:
  - infrastructure/2026-05-14_claude-cli-bare-disables-oauth-keychain-auth.md
  - infrastructure/2026-05-14_self-identity-minting-cli-flag-cron-workers.md
---

# Happy CLI File-Watcher Binds to Ghost Session_id That Claude Never Creates

## What

Happy CLI v0.13.0 launchers mint a fresh UUID at startup and bind their file-watcher to `<claude_project_dir>/<that_uuid>.jsonl`. The actual Claude process generates its own session_id (or inherits one via `--resume`), so it writes to a *different* file. Happy's watcher never observes Claude's stream-completion events; the user-visible symptom is periodic "Process exited unexpectedly" messages with output that appears truncated, recoverable only by typing anything to re-engage the queue. Affects every Happy session on the host, not just specific projects.

## Detection (Verified Empirically 2026-05-18)

```bash
LATEST=$(ls -t ~/.happy/logs/*pid*.log | head -1)
grep -c 'FILE_WATCHER.*ENOENT.*restarting' "$LATEST"   # >100 = bug active
grep 'FILE_WATCHER.*ENOENT' "$LATEST" | tail -1 | grep -oE "watch '[^']+'"   # the ghost path
ls -la "<ghost_path>"   # confirm: No such file or directory
```

## Workaround (Verified on 2 Sessions; ENOENT Loop Stops Within 1s)

```bash
HAPPY_PID=<pid_from_happy_log_filename>
LOG=$(ls -t ~/.happy/logs/*pid-${HAPPY_PID}*.log | head -1)
GHOST=$(grep 'FILE_WATCHER.*ENOENT' "$LOG" | tail -1 | grep -oE "watch '[^']+'" | sed "s/watch '//;s/'//")
PROJECT_DIR=$(dirname "$GHOST")
REAL=$(ls -t "$PROJECT_DIR"/*.jsonl 2>/dev/null | head -1)
ln -s "$REAL" "$GHOST"
```

## When This Applies

- You see repeated "Process exited unexpectedly" messages in Happy sessions
- Happy log files (in `~/.happy/logs/`) show 100+ `FILE_WATCHER.*ENOENT` retries
- The ghost path (the file Happy is watching) does not exist, but a similar `.jsonl` file nearby does
- Every Happy session on the same machine exhibits the symptom, not just specific projects

## When This Does NOT Apply

- Native Claude Code without Happy wrapper (the bug is in Happy's launcher, not Claude itself)
- Fresh sessions where Claude hasn't yet written its first transcript event — `ls -t *.jsonl | head -1` will grab a stale file. Wait for at least one Claude response before applying the symlink.
- Sessions where the Happy file-watcher target happens to coincide with Claude's session_id (rare; would require deliberate seeding)

## Grounding Evidence from Session

- **[project] session pid-58646:** 179,107 ENOENT retries over 18+ hours, ghost `804ba8fb-4b61-4e45-91a5-20fd503ba454.jsonl` did not exist; real Claude wrote to `92127a13-d8fd-40d6-8f22-21e41e3f2742.jsonl`. After `ln -s`: 0 new ENOENT entries in 8s window, last retry timestamp froze.
- **[project] session pid-72506:** 7,641 retries over 2 hours, ghost `4a5736d0-...`, real `5d73ebd8-...`. After `ln -s`: ENOENT delta = 0 over 8s; last retry timestamp froze.
- **Auto-restart of [project] (old session died, new launcher pid-72506 spawned)** reproduced the bug with a *fresh* ghost UUID — confirms the mismatch is generated at every launcher startup, not inherited from a stale state file.

## Distinct from Related Bugs

- NOT the older "npm install Claude causes Process exited unexpectedly" Mac Mini bug (fixed by switching to native installer; current laptop runs native installer 2.1.143 and still hits this).
- NOT MCP process leakage (process boundaries are clean; MCP children auto-cleanup correctly).

## Real Fix Path (Upstream)

Happy's file-watcher should either:
1. Wait for Claude's first `.jsonl` write before binding, or
2. Re-resolve target after N consecutive ENOENT retries

Workaround is per-session and needs re-application after each Happy restart.

## Source Context

Extracted from [project] debugging session 2026-05-18 (kf-debugger mode). Full diagnostic trace in beads issue `[project]-wzrj`. Verified across two distinct Happy sessions ([project], [project]) with independent UUID mismatches, confirming the bug is systematic in Happy's launcher protocol, not session-specific corruption. This diagnostic has high reusability for any developer running Happy CLI on the same machine; the workaround is safe, immediate, and requires no upstream fixes.

**Taxonomy note:** This entry's preferred tags would be `claude-cli, session-management, file-watcher, workaround` — these are not currently in Module 23's approved vocabulary. Recommend extending the taxonomy with these four terms; they have clear reuse value across Claude tooling and file-system monitoring patterns. Remapped to approved terms (`api, filesystem, temporal, empirical, stable`) for filing compatibility.

