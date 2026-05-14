---
title: Idempotent watchdog producer pattern — detector + check_and_alert + dated state file + CLI + cron block
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.90
staleness_risk: stable
importance: 4
domain: infrastructure
topic: ops
tags: scheduling, observability, quality-gate, empirical
related_entries: [infrastructure/2026-05-12_self-watchdog-autonomous-fix-cycles.md, diagnostics/2026-05-13_bd-search-idempotency-grep-trap.md]
created: 2026-05-14
---

# Idempotent Watchdog Producer Pattern

When building watchdog-style producers that emit alerts/events from periodic scans (cron / launchd / k8s cronjob), use this 4-piece template. Six concrete instances shipped in iteration-loop v0 (2026-05-14) — every Path B watchdog producer in the spec uses this shape.

## The Four Pieces

**1. Pure detector function** — returns structured findings, no side effects.
```python
def find_violations(...) -> list[Finding]:
    # walk state, evaluate rules, return findings list. NEVER writes anywhere.
```
Easy to unit-test in isolation: monkeypatch the source directory + assert the returned list shape. No subprocess mocks, no fakefs gymnastics.

**2. check_and_alert orchestrator** — wraps emit + dispatch behind opt-in flags.
```python
def check_and_alert(*, emit_event=False, send_telegram=False) -> Result:
    findings = find_violations(...)
    for f in findings:
        if _was_alerted_today(f.key): continue
        if emit_event:    orchestra.enqueue_event(_build_event(f))
        if send_telegram: telegram_stub.send_watchdog_alarm(...)
        _mark_alerted_today(f.key)
    return Result(findings=findings, events_emitted=..., telegram_emitted=...)
```
Default flags off so unit tests + dry-runs don't pollute disk; production callers (the cron block) enable both.

**3. Per-finding-per-day idempotency state file**
```
<state_dir>/<finding_key>.txt    # contents: today's ISO date, one line
```
- Read = check if contents match today (skip alert if so)
- Write = mark alerted today (set contents to today's date)
- Day rolls = file content stale → re-alert eligibility renewed
- Operator force-renotify = `rm <state_dir>/<finding_key>.txt`

Six instances chose six distinct state dirs (`~/.[project]/budget_breach_state`, `~/.[project]/stranded_state/`, `~/.[project]/invariant_state/`, `~/.[project]/silence_state`, `~/.[project]/cycle_warn_state/`, …). Separate dirs make cleanup + audit obvious.

**4. Thin CLI wrapper** — argparse + JSON stdout + exit 0/2 convention.
```python
exit_code = 2 if (result.events_emitted or result.telegram_emitted) else 0
```
The exit-2 convention lets the cron block grep without parsing JSON. Bash idiom:
```bash
if cli_json=$(python3 "$CLI" --flags 2>>"$LOG"); then
    summary=$(echo "$cli_json" | python3 -c '...one-line parse to summary...')
    log "block: $summary"
else
    rc=$?
    [ "$rc" = "2" ] && log "block: alert fired this tick" || log "⚠ CLI exited $rc"
fi
```

## Concrete Instances (Iteration-Loop v0)

All in `~/Scripts/[project]/iteration_loop/`:

| Module | Detection Target | Spec § |
|----|---|---|
| budget_check.py | sum_spend_today > cap → budget_breach | §4.1 HIGH |
| sweep.py | orphan reservation → orphaned_reservation_swept | §4.1 LOW |
| session_health.py | open reservation + stale heartbeat → stranded_work | §4.1 MEDIUM |
| heartbeat_audit.py | assert_invariants violation → cost_invariant_violation | §4.1 HIGH |
| morning_silence.py | N consecutive empty Orchestra days → consecutive_empty_mornings | §4.1 MEDIUM |
| cycle_duration.py | heartbeat cycle_duration_sec > 0.75 × MAX → cycle_duration_warn | §4.1 LOW |

Each spent ~80-150 lines + ~8-10 tests. Same pattern, six fillings of the form.

## When This Applies

- Periodic scans (every N minutes / hours / days)
- Per-finding alerts that would storm if un-deduped
- Idempotent events (re-emitting is wasteful but not destructive)

## When This Does NOT Apply

- One-shot detectors with no schedule → no idempotency needed
- Real-time / streaming detectors → use offset / watermark dedup, not dated state files
- Multi-day rollups → state granularity is week-of-year or month, not date

## Failure Mode If You Skip Idempotency

Alert storms. Every 30-min cron tick re-emits the same alert. 48 alerts/day for an unresolved issue. Operators stop reading alerts. Real alarms get missed.

## Anti-Pattern: In-Memory Dedup

Tempting: a `seen_today` set in the daemon. Two problems:
- Cron jobs are short-lived → no in-memory state survives ticks
- Long-lived daemons accumulate seen_today across days → never re-alert after a day boundary

The dated file is the simplest persistence that handles both.

## Source Context

Direct pattern extraction from iteration-loop v0 watchdog suite (2026-05-14). Six independent watchdog producers across cost management, task health, and invariant auditing all independently converged on the same four-piece structure. Grounding: implemented and unit-tested in `~/Scripts/[project]/iteration_loop/` with ~300 total tests. Staleness risk is stable because the pattern addresses inherent properties of cron-based detection (restart per tick, per-finding idempotency window, CLI integration) that are unlikely to change. Distinct from "Self-watchdog" pattern (which addresses detecting when a cycle stops running entirely); this pattern addresses detecting violations *within* running cycles.
