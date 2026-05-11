---
title: Atomic-write stubs for pipelines that read-and-write the same file
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-11
domain: patterns
topic: validation
tags: quality-gate, filesystem, adversarial
related_entries: []
---

# Atomic-write stubs for pipelines that read-and-write the same file

When writing a test stub that fronts a shell command appearing on **both the read and write legs of the same pipeline** (e.g., `crontab -l | sed "..." | crontab -`), the naive form `cat > $STATE_FILE` race-truncates `$STATE_FILE` before the read leg has consumed it.

## The Problem

Bash spawns all three subprocesses concurrently. Shell redirection (`>`) opens the target file with `O_TRUNC` at fork time — not at first-write time. The read leg (`crontab -l` reading `$STATE_FILE`) and the write leg (`crontab -` truncating `$STATE_FILE` via `cat > $STATE_FILE`) race. The write leg often wins, leaving the read leg with an empty file and the final state empty.

### Wrong (race-prone)

```bash
#!/bin/bash
if [ "$1" = "-l" ]; then
    cat "$STATE"
elif [ "$1" = "-" ]; then
    cat > "$STATE"          # truncates $STATE immediately on fork — race
fi
```

### Right (atomic via tempfile)

```bash
#!/bin/bash
if [ "$1" = "-l" ]; then
    cat "$STATE"
elif [ "$1" = "-" ]; then
    TMP=$(mktemp)
    cat > "$TMP"            # writes go to a fresh tempfile
    mv "$TMP" "$STATE"      # atomic replace AFTER all stdin consumed
fi
```

The atomic form guarantees `$STATE` is not modified until the entire write payload is captured, which only happens after the upstream pipeline (including `crontab -l`) has finished reading.

## When This Applies

- Test stubs for `crontab(1)`, `sudo crontab` (per-user variants), `git config`, `sed -i` simulators, or any binary that appears on both sides of a transform pipeline.
- Any test fixture that mocks a "read-modify-write" tool used in `tool -l | filter | tool -` style.
- Production code paths that read-then-write the same file (the same `mktemp + mv` discipline applies).

## When This Does NOT Apply

- Stubs for tools that only appear on one side of a pipeline (the race needs both sides to share a file).
- Tools that already provide atomic-write semantics internally (e.g., `crontab(1)` on a real system uses an internal temp file; only the stub re-introduces the race).
- Single-process serial scripts where there's no concurrent fork.

## Source Context

Discovered during [project] Dreaming Tier 1 implementation — Phase I9 (install script tests). A `test_install.py` test stub for `crontab(1)` round-tripped through a state file. The install script ran `crontab -l 2>/dev/null | sed "..." | crontab -`. Every test that expected the rewrite to take effect failed with "rewrite did not produce [project]-dream.sh entry; restoring backup." Traced via `bash -x` to the race; fixed by switching the stub's write leg to `cat > $TMP && mv $TMP $STATE`. After the fix, all 12 install tests passed first try.
