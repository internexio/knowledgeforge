---
title: Silent-success scripts — monitor by state artifact, not log file
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-15
domain: infrastructure
topic: ops
tags: observability, monitoring, cron, logging-patterns, freshness-checks, anti-patterns
related_entries:
  - infrastructure/2026-05-14_idempotent-watchdog-producer-pattern.md
  - infrastructure/2026-05-12_self-watchdog-autonomous-fix-cycles.md
  - diagnostics/2026-05-13_content-diff-mtime-inversion-idle-systems.md
  - methodologies/2026-05-14_healthy-system-gate-trap-empirical-thresholds.md
---

# Silent-Success Scripts — Monitor by State Artifact, Not Log File

## The Anti-Pattern

Cron-driven scripts that log only on errors leave their log file's mtime stuck at the last error. Health-check monitors that stat the log file then conclude "the job hasn't run in 87 days" — even though the job is running perfectly every 15 minutes.

You can't fix this in the script (logging every success line clutters disks and hides real errors). You fix it in the monitor: stat the artifact the script actually updates on every successful run.

## Concrete Trigger ([project], 2026-05-15)

The [project] morning brief flagged three "stale cron" warnings:

- `health.log` — stale **87 days** (since the cron's `mkdir: command not found` error was fixed). Actual `health-report.json` was updating every 15 minutes.
- `dream.log` — stale **60 hours**. Actual `~/.dream-state/last-run.json` was updating every day at 06:00 with the latest cycle ID and findings count.
- `karma-scan.log` — full of "Failed HTTP 200" lines that were actually soft-skip success responses being misclassified by the client (a separate but related issue).

All three scripts were healthy. All three monitors were lying.

## The Rule

For every cron job you monitor:

1. Find the artifact the job updates **on success**, not on failure.
2. Stat that artifact's mtime for freshness checks, not the log file.
3. Log files remain useful for the *content* of recent errors — keep that role separate from the freshness check.

In code:

```python
# Each entry: (display_name, freshness_artifact, max_age_hours).
# Bare names resolve relative to WORKFLOW_DIR; ~ / / are expanded directly.
EXPECTED_CRON_JOBS = [
    ("scan-and-route", "scan-and-route.log", 36),        # script logs on every run
    ("dream",          "~/.dream-state/last-run.json", 36),  # silent on success
    ("health-check",   "health-report.json", 1),         # silent on success
]
```

## What to Look For in a Script to Know Which File to Stat

- **Logs every run** → stat the log file.
- **Logs only on error** → find the state file. Common patterns:
  - `*-report.json` written at end of each cycle
  - `~/.<tool>-state/` directory with `last-run.json` / `heartbeats.jsonl`
  - SQLite DB updated with a `last_run_at` row
  - Output directory (`reports/YYYY-MM-DD/`) with date-stamped subdirs

## When This Applies

- Cron-driven tasks that fail silently (no stderr, no log file update on success)
- Monitoring systems that need to distinguish "working but idle" from "broken"
- Health checks that cannot rely on log file mtime
- Long-running scheduled tasks where the log file sees updates only on error

## When This Does NOT Apply

- The script may legitimately not run for long stretches (e.g., on-demand utilities) — staleness has no meaning.
- The "state artifact" is itself written by an upstream system that may be lagging (false freshness signal). Walk the chain.
- The job's purpose IS the log file — e.g., audit-trail collectors where missing-log IS the failure mode. Stat the log there.

## Related Patterns

This diagnostic pairs with the **idempotent watchdog producer pattern** (what to emit when) and **self-watchdog** (detecting if the cycle stops running entirely). It answers a complementary question: assuming the cycle is running silently, which file proves it's actually doing its job?

The **content-diff mtime inversion** entry describes the inverse trap: why mtime can be stale even when a producer is running constantly. This entry flips the perspective: mtime is correct for state files *precisely* because they track actual work completion, not log file updates.

The **healthy-system gate trap** documents why thresholds designed on "noisy systems" fail in working ones. This pattern is part of the same diagnostic family: empirical signals (like file mtime) need clear semantics about what they actually measure.

## Grounding

Observed three independent cases in one session on the same machine, all fixed by the same remediation:

1. `[project]-health.sh` writes `health-report.json` on every 15-min run; cron was healthy for ~3 months while `health.log` showed "stale 87d" (fixed in commit `c43c664`).
2. `[project]-dream.sh` runs `python3 -m dream.cli cycle`; the cycle writes to `~/.dream-state/last-run.json` and `heartbeats.jsonl` but is silent on the wrapper's stderr-redirected `dream.log` (fixed in `816b7fc`).
3. `karma-scan.sh` confusion was not the same anti-pattern but rooted in the same instinct: "the log says errors → therefore broken" — when actually the log was reporting soft-skips that the client misclassified (fixed in `66d9baa`).

Both #1 and #2 ship the same fix in `scripts/nw-morning.py`'s `EXPECTED_CRON_JOBS` table — switching from log-file path to state-file path. The pattern generalises to any cron-monitored system.

## Source Context

[project] morning brief, 2026-05-15. Health check monitors (`nw-morning.py`) were falsely alerting on three healthy cron jobs. Root cause: monitors were statting log files instead of the state artifacts that jobs update on every successful run. The diagnostic rule (stat the state file, not the log) is reusable across any cron job where "silent success" is the normal case. Related to broader observability patterns in [project]: self-watchdog (what to do if the cycle stops), idempotent watchdog producer (what to emit when failures happen), and healthy-system gates (empirical thresholds need safety valves for working systems).
