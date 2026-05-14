---
title: Deployment-gap audit checklist for shadow-mode patterns
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-13
domain: infrastructure
topic: deployment
tags: quality-gate, scheduling, empirical, stable
related_entries:
  - infrastructure/2026-05-12_self-watchdog-autonomous-fix-cycles.md
  - infrastructure/2026-05-11_python-package-cli-under-cron.md
---

# Deployment-Gap Audit Checklist for Shadow-Mode Patterns

## The Problem

A pattern can appear fully deployed — code merged, on disk, even with docs claiming it's live — while being silently inert at runtime due to an **activation gap**. The gap is invisible until you explicitly verify that the deployed code actually executes.

In a ~25-minute audit of three sibling shadow-mode patterns in the [project] project, three distinct gap classes surfaced:

1. **Missing scheduler / consumer.** A producer was running (pane-tailer writing snapshot files every 30s via launchd), but the consumer that should read those snapshots had no launchd plist on the machine. The downstream watchdog code was committed but never executed. Project docs (CLAUDE.md) claimed "runs every 5 minutes via launchd" — but no such plist existed. The doc and the runtime had diverged silently.

2. **Stale running process.** A long-running bash script (orchestrator, PID 959, started Tue May 12 11:20:53) predated both pattern commits (May 13 16:44 and 16:47). The on-disk script had the new instrumentation (source-with-fallback, conditional-logging branches), but the live process held its originally-loaded copy in memory. Bash sources scripts at startup; once running, edits don't propagate. Result: two patterns' instrumentation was silent for ~1 day despite "being deployed."

3. **Swallowed errors hiding configuration mismatch.** Once the consumer was scheduled, the first execution failed. The error path used `>/dev/null 2>&1`, hiding the actual cause. After patching to capture combined output, the error surfaced: launchd processes run with CWD=`/`, so a tool relying on CWD-relative database lookup (`bd`) couldn't find its data. Fix was a one-line env var in the plist.

## When This Applies

Any pattern that involves:
- A scheduler-triggered consumer (cron, launchd, systemd-timer, APScheduler)
- Code that gets added to an existing long-running process
- Shadow-mode / silent-mode features that produce no output when nothing notable happens
- Any pattern that claims to be "deployed" via merged commits but has not yet been validated end-to-end

## Audit Checklist

Run these in order on every shadow-mode pattern deployment, **before relying on its output:**

### 1. Is the consumer scheduled?

```bash
launchctl list | grep <label>                    # macOS
systemctl status <unit>                          # linux
crontab -l | grep <pattern>                      # cron
```

Match the expected scheduling source. CLAUDE.md claims are not evidence — check the actual scheduler. If the pattern is supposed to run and the schedule does not exist, deployment is incomplete.

### 2. Is the producer process running fresh enough?

```bash
ps -p <pid> -o lstart,command
git log -1 --format=%ci -- <script>
```

The process start time must be **later than** the commit time of any code it's expected to honor.

**For long-running bash scripts:** Edits don't reload — restart required. If the script has been running since before your commit, the old in-memory version is executing, not the new on-disk version.

### 3. Are error paths visible?

```bash
grep -E '>/dev/null 2>&1|>&/dev/null' <script>
```

Particularly on conditional blocks: `if cmd >/dev/null 2>&1; then log "OK"; else log "FAILED"; fi` — the failure branch has zero diagnostic surface. Capture combined output into a variable for the failure path even if you discard it on success.

### 4. Does the runtime environment match the interactive environment you tested in?

Specifically for scheduled jobs:
- **CWD differs:** launchd: `/`; cron: `$HOME`; interactive: wherever you cd'd
- **Environment variables:** launchd and systemd run with minimal env; cron inherits some shell vars but not all
- **PATH:** May be stripped or reordered

Any tool with CWD-relative state lookup needs an explicit env var (e.g., `BEADS_DIR`, `GIT_DIR`, `PYTHONPATH`). Check the scheduler config (plist, systemd unit, crontab line) for explicit env var declarations.

### 5. Does the first real-world invocation produce the expected log line?

Shadow-mode patterns by design log only on triggers. A silent log file after deployment is ambiguous: did nothing trigger, or is the pattern broken?

Force a trigger if possible:
```bash
launchctl kickstart -k gui/$(id -u)/<label>     # macOS
systemctl start <unit>                           # linux
```

Wait ~10s (pattern cadence + margin) and check the log tail. If no new log entry appears, the pattern either never ran or failed silently.

## Verification Template

Each checklist item maps to a single shell command. For any shadow pattern, a deployment verification script looks like:

```bash
#!/bin/bash
LABEL="com.example.my-pattern"
PIDFILE="/var/run/my-orchestrator.pid"
SCRIPT="/opt/my-project/orchestrator.sh"
LOGFILE="/var/log/my-pattern.log"

echo "[1] scheduler:"
launchctl list | grep "$LABEL" || echo "MISSING"

echo "[2] producer freshness:"
if [ -f "$PIDFILE" ]; then
  ps -p "$(cat "$PIDFILE")" -o lstart
  echo "Script last commit:"
  git log -1 --format="%ci" -- "$SCRIPT"
fi

echo "[3] error visibility:"
grep -c '>/dev/null 2>&1' "$SCRIPT" || echo "OK (no redirections)"

echo "[4] runtime env:"
launchctl print "gui/$(id -u)/$LABEL" 2>/dev/null | grep -A 20 "environment"

echo "[5] forced trigger:"
launchctl kickstart -k "gui/$(id -u)/$LABEL" 2>/dev/null
sleep 8
tail -3 "$LOGFILE" || echo "No log file yet"
```

## When This Does NOT Apply

- Synchronous foreground tools (no scheduler, no long-running process)
- Already-validated patterns running for ≥ 1 week with observed triggers in the log
- Patterns that produce output every run (no shadow / silent mode — output alone proves execution)
- Patterns deployed via container/function-as-a-service (cloud runtime handles lifecycle; different audit approach)

## Related Patterns

- **Self-watchdog pattern:** Once a shadow-mode pattern is verified deployed, use an *external* watchdog (separate cron/launchd entry) to detect if the pattern stops running. This entry audits *initial* deployment; self-watchdog covers *ongoing* monitoring.
- **Python package CLIs under cron:** A specific instance of the runtime-environment gap — relative imports fail in cron when invoked as a script instead of a module.

## Source Context

Discovered 2026-05-13 during soak-data audit of paperclip patterns 2, 3, 4 in the [project] project. All three patterns had been "deployed" via merged commits with passing tests and SPEC docs claiming live. The audit found:
- Pattern 2: pane-tailer running, healthcheck consumer absent (no plist on machine despite CLAUDE.md claim)
- Patterns 3 + 4: orchestrator PID 959 from May 12 predated commits from May 13 (in-memory script stale)
- Pattern 2 sub-bug: error path swallowed launchd CWD mismatch via `>/dev/null 2>&1` redirect

Related discovery: [[bd-search-idempotency-grep-trap]] — surfaced in the same paperclip work-stream; same class of "diagnostic path swallows the real error."
