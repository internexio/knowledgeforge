---
title: Pane-content idle patterns make mtime an unreliable liveness signal
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-16
domain: infrastructure
topic: watchdog, liveness, observability
tags: diagnostics, watchdog, liveness, false-positive, observability, empirical
related_entries:
  - infrastructure/2026-05-13_content-diff-mtime-inversion-idle-systems.md
  - infrastructure/2026-05-14_idempotent-watchdog-producer-pattern.md
  - infrastructure/2026-05-12_self-watchdog-autonomous-fix-cycles.md
---

# Pane-Content Idle Patterns vs mtime-Based Liveness Watchdogs

## The Trap

A common watchdog pattern: a pane-tailer captures terminal session snapshots periodically, writes them to a file, and only updates the file when the content changes. A separate watchdog checks the file's mtime — "if mtime is older than threshold X, the session is stuck."

This works for HUNG processes. It silently produces false positives for **legitimately idle sessions whose pane content stops changing on purpose**.

The trap: pane content can stop changing for several non-broken reasons:
1. The agent is sitting at an idle prompt waiting for user input.
2. The agent is in a remote/proxy mode where the pane is just a status display decoupled from agent activity (the agent runs out-of-band and the pane only updates on activity bursts).
3. The agent has been backgrounded by the user but the session is still healthy.

mtime alone cannot distinguish "hung" from "idle but fine." Watchdogs that escalate by silence duration alone (e.g., 90 min → suspicious, 6h → critical) produce false-positive bug reports on long-idle healthy sessions.

## The Fix: Content-Aware Suppression

Before filing a bead/alert for a silent pane, grep the snapshot for known **idle-pattern fingerprints**:

```bash
if grep -qE "bypass permissions|Press space to switch to local mode" "$tail_file"; then
    log "$session silent ${age}s ($tier) — idle/remote-mode pane, no-op."
    continue
fi
```

Apply at ALL severity tiers, not just the early one. A session at the idle Happy welcome screen for 6 hours is not a bug — it is an abandoned session. If the user wants to clean it up, that is housekeeping, not a P1.

## Concrete Fingerprints (Claude Code / Happy CLI, 2026-05)

- `bypass permissions on (shift+tab to cycle)` → Local Mode at idle Happy prompt waiting for input
- `Press space to switch to local mode • Ctrl-C to exit` → Remote Mode footer. In Remote Mode the agent runs out-of-band; pane mtime is decoupled from agent activity.

Other systems will have their own fingerprints — REPL banners, "press q to quit" footers, idle TUI screens. Identify them empirically: when a false-positive bead fires, look at the pane snapshot and find the constant footer or banner that signals "this is an idle UI, not a hung process."

## When This Applies

- Any tmux/screen pane-tailing watchdog.
- Any "is this session alive" check that uses file mtime as a proxy.
- Any system where the watched process can legitimately go silent for hours (interactive shells, debugger sessions, monitoring dashboards).

## When This Does NOT Apply

- True liveness checks via process-level signals (`kill -0 pid`, heartbeat counters, periodic application-level pings). Those measure actual process health, not pane activity.
- Batch-processing jobs that should produce continuous output — silence there IS a real signal.

## Trap Within the Trap

Tightening the threshold ("OK, then suspicious-tier suppresses idle, but critical-tier must still alert at 6h") just defers the false positive. Empirically, abandoned-but-fine Claude Code sessions can stay silent indefinitely. The right move is suppression at all tiers when an idle fingerprint matches, and a separate "housekeeping" workflow if you want to actually clean up old sessions.

## Source Context

Identified during [project] silent-session watchdog investigation, 2026-05-16. Four false-positive beads (2 P1 critical, 2 P2 suspicious) had been filed against legitimately idle / Remote Mode sessions. Code fix in `scripts/happy-healthcheck.sh` (commit c7a1ee7) extended content-aware suppression to all tiers and added the Remote Mode fingerprint. All 4 false-positive beads were closed.

This entry documents the practical fix pattern and complements the root-cause analysis in the 2026-05-13 "Content-diff mtime preservation inverts liveness signal" entry, which explains why mtime is an unreliable signal for idle-capable subjects. Together they form the diagnosis (mtime semantic divergence) + remedy (content-aware suppression) pairing.

## Related

- Content-diff mtime preservation inverts liveness signal (root cause diagnosis — 2026-05-13)
- Idempotent watchdog producer pattern (structural pattern for cron-based detectors — 2026-05-14)
- Self-watchdog — autonomous fix systems need external cycle-alive checks (detection of cycle-level silence — 2026-05-12)
