---
title: Content-diff mtime preservation inverts liveness signal on idle-but-healthy systems
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.75
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-13
domain: infrastructure
topic: watchdog, liveness, ops
tags: patterns, diagnostics, empirical, stable
related_entries:
  - infrastructure/2026-05-12_self-watchdog-autonomous-fix-cycles.md
  - infrastructure/2026-05-13_deployment-gap-audit-shadow-mode-patterns.md
---

# Content-Diff mtime Preservation Inverts Liveness Signal on Idle-but-Healthy Systems

## The Pattern

A common atomic-write idiom for dedup / change-detection:

```bash
capture > "$tmp"
if [ ! -f "$dest" ] || ! cmp -s "$tmp" "$dest"; then
    mv -f "$tmp" "$dest"
else
    rm -f "$tmp"
fi
```

This is correct for **dedup and content-change tracking** — `$dest`'s mtime indicates *when content last meaningfully changed*, not when the producer last ran. A downstream consumer inspecting `stat -f %m $dest` answers: "when did the underlying state last become different?"

**But** this assumption only holds if "no content change" reliably means "no underlying activity." For systems with a stable idle state, that equivalence fails.

## The Trap

A "silent-run watchdog" pattern fires on idle-but-healthy systems if it equates `mtime stale` with `process not doing anything`:

- **Producer:** Snapshots terminal pane content periodically, content-diffs, only moves to dest on change.
- **Consumer:** Checks dest mtime, alerts if older than threshold (e.g., 90 min).
- **Idle subject:** A terminal showing a fixed prompt (`❯ ` waiting for user input). Process is healthy and responsive; pane content is unchanging *by design*.

Result: the watchdog fires on every healthy session the user steps away from for > threshold. The producer is doing exactly what it should (mtime stable = content stable); the consumer's interpretation is wrong (mtime stable ≠ subject hung).

## Root Cause: Semantic Divergence

Producer and consumer have **inconsistent definitions of "fresh":**

- **Producer's semantic:** "fresh content" — the file reflects the latest *meaningful* state; mtime tracks when that state became different
- **Consumer's semantic:** "fresh activity" — something important is happening; mtime proves the producer ran recently

For idle-capable subjects, these semantics diverge. The producer can be running every cycle (e.g., polling pane content every 30s) without changing the file. The consumer sees "old mtime" and concludes "producer stopped" — false premise.

## When This Applies

Any time you find:
- Code using file mtime as a "did something happen recently?" signal
- **AND** the producer uses content-diff conditional writes (move-only-on-change idiom)
- **AND** the subject has a meaningful idle state (a prompt waiting for input, a build completed and waiting for next trigger, a service in standby)

Specifically suspect:
- Snapshot/cache files with dedup logic
- "Has the build changed?" detection
- Status files written by deduplicating scripts
- Terminal pane tailer files
- Session heartbeat files that only update on content change

## When This Does NOT Apply

- Producer overwrites the file unconditionally on every run (mtime always tracks producer activity)
- Subject has no meaningful idle state (e.g., a build process that's either working or finished; a streaming log that should produce continuous output)
- Consumer is already content-aware (parses the file to detect idle state, doesn't rely on pure mtime check)

## Fixes (with trade-offs)

### Fix 1: Make producer mtime track activity, not content

Always `touch` the destination on every successful capture, even when no content change:

```bash
capture > "$tmp"
if [ ! -f "$dest" ] || ! cmp -s "$tmp" "$dest"; then
    mv -f "$tmp" "$dest"
else
    rm -f "$tmp"
fi
touch "$dest"  # Always update mtime on successful capture
```

**Trade-off:** Loses the "file mtime means content changed" semantic. Any other consumer that relied on the original behavior breaks.

### Fix 2: Make consumer content-aware

Instead of pure mtime check, inspect the captured content:

```bash
if [ $(find "$dest" -mmin +90) ]; then
    # Check if the tail-file shows known idle states
    if tail -1 "$dest" | grep -q "^❯ "; then
        # Idle prompt — not a failure
        return 0
    fi
    # Otherwise, alert
fi
```

**Trade-off:** Detector complexity; must hardcode idle state patterns. Preserves producer purity; all existing consumers still work.

### Fix 3: Use a different liveness signal entirely

Abandon mtime for liveness. Use process tree health, CPU/IO sampling, or application-specific heartbeat files. Heavier; usually overkill if Fix 1 or Fix 2 suffice.

### Fix 4: Pair the alert with content evidence

Fire the alert but include the last 5 lines of the snapshot file in the report. The recipient can immediately distinguish "session at idle prompt" from "session mid-execution with no progress" without a separate investigation.

## Grounding & Real-World Impact

**Discovered 2026-05-13** in [project]. `scripts/happy-pane-tailer.sh:42-47` uses the content-diff-mv idiom with explicit comment: `"mv only when content differs — preserves mtime on truly idle sessions."` The downstream `happy-healthcheck.sh` Phase B watchdog interprets mtime age via `WATCHDOG_SUSPICIOUS_SECS=5400` (90 min) → bead creation.

**Real firing:** First production fire created bead `[project]-1m7` for a tmux session whose pane showed a healthy `❯ ` prompt and whose underlying `happy --yolo` process:
- Was running cleanly for 1 day 6 hours
- Had PID 1170 (zsh) with child process PID 1614 (happy)
- Had no backoff state file
- Had no error log entries
- Was fully responsive when the user returned to the terminal

The session was idle, not hung. The watchdog as designed will fire on *every* Happy session any time the user steps away for > 90 minutes, producing structural noise rather than signal.

**Status:** Currently unfixed in [project] as of 2026-05-13. The user deferred the fix decision to a later turn. The root cause was surfaced during the deployment-gap audit (see related entry). This entry documents the class-of-bug pattern with a production example; it is not a prescription for the user's specific case.

## Source Context

Discovered during 2026-05-13 paperclip pattern 2 deployment audit (`2026-05-13_paperclip-pattern-2-deployment-audit` session). Uncovering this pattern required first auditing the deployment-gap checklist (related entry) to answer "why isn't the watchdog firing correctly?" The watchdog *was* firing correctly — the issue is that mtime as a liveness signal is fundamentally inverted for idle subjects under the content-diff-dedup design.
