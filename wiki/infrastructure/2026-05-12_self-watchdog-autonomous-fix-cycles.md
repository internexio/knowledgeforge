---
title: Self-watchdog — autonomous fix systems need external cycle-alive checks
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.80
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-12
domain: infrastructure
topic: ops
tags: scheduling, quality-gate
related_entries: []
---

# Self-watchdog — Autonomous Fix Systems Need External Cycle-Alive Checks

## The Pattern

An autonomous fix system that runs on a schedule (cron, systemd timer, launchd, k8s CronJob) can fail in two distinct ways:

1. **The cycle runs and emits bad signals** — caught by the cycle's own internal heartbeat, halt mechanism, and quality gates
2. **The cycle stops running entirely** — *not* caught by any internal signal, by definition. No cycle = no heartbeat = nothing to alarm on

The second failure mode is invisible to the system itself. You discover it when something downstream that depended on the cycle stops working, which can be days later.

The mitigation is a **separate, higher-frequency external watchdog** that reads the cycle's own state files (last-run timestamp, halt flag, latest heartbeat status) and alarms when:

- `last-run.json` is older than the cycle's expected cadence plus grace period (e.g., daily cycle → 25h max age)
- A halt flag is present (Sev1 / critical-failure state)
- The latest heartbeat status is anything other than "ok" or a documented benign skip status

The watchdog must be:
- **Separate process / separate cron entry** — co-located with the cycle defeats the purpose
- **Higher frequency** — at least daily, ideally hourly for daily cycles; the staleness window is the watchdog cadence plus cycle cadence
- **Read-only over the cycle's state** — no side effects, no recovery attempts; the watchdog's job is *detection*, not *repair*
- **Cheap and reliable** — must not fail in correlated ways with the cycle itself (don't share Python imports, don't share database connections, don't share locks)

## Concrete Implementation ([project] Dreaming)

The dreaming cycle runs daily at 06:00. The self-watchdog is a thin shell script that runs hourly at `0 * * * *` and shells out to a `dream.cli health` subcommand which:

1. Reads `~/.dream-state/last-run.json` and computes age in hours
2. Checks `~/.dream-state/halt.json` for presence
3. Reads the last line of `~/.dream-state/heartbeats.jsonl` and extracts the `status` field. Treats `locked_skip` and `paused_skip` as "ok" (intentional no-ops, not failures)
4. Returns a JSON snapshot and exits 0 if all checks pass, 1 if any fail

Shell wrapper writes one log line per invocation to `~/agent-workflow/dreaming-health.log`:
- `[ts] ok {snapshot}` on success
- `[ts] FAIL {snapshot}` on failure (grep-able)

The watchdog itself is dumb on purpose — it does not page, retry, or auto-recover. The single log line is enough to detect "cycle stopped" either via downstream log monitors or via the dreaming system's *next* cycle (which would itself surface the stale-log finding under Category C).

## When This Applies

- Any scheduled autonomous remediation cycle (daily/weekly substrate hygiene, nightly cleanup, periodic reconciliation)
- Any system whose own heartbeat mechanism is internal to the cycle itself (and therefore mute when the cycle doesn't run)
- Any pipeline where "silent failure to fire" is more dangerous than "noisy failure when fired"

## When This Does NOT Apply

- Always-on services with their own external monitoring (Kubernetes liveness probes, systemd watchdog, traditional monitoring stacks like Prometheus + Alertmanager) — the watchdog pattern is for systems too small or too local for that infrastructure
- Cycles where missing a run is harmless (best-effort cron jobs, cosmetic updates) — the cost of building the watchdog exceeds the cost of the failure
- Systems already wrapped in a higher-level orchestrator that already monitors execution (e.g., Airflow DAG with built-in failure alerting)

## Anti-Patterns

- **Co-located watchdog**: shell function inside the same cycle script. If the cycle doesn't run, neither does the watchdog
- **Same-language watchdog**: shares import surface with the cycle. A bad import in the cycle module breaks the watchdog too
- **Self-healing watchdog**: tries to restart the cycle. This couples detection to recovery; recovery failures now mask detection failures
- **No log discrimination**: writes the same line on success and failure, making post-hoc detection require parsing every line

## Source Context

Implemented during [project] Dreaming Tier 1 deployment, 2026-05-12. The dreaming cycle runs daily at 06:00 via cron. The user observed that without external verification, a silent stop-of-the-cycle would be invisible until downstream effects appeared. Implementation: new `scripts/[project]-dreaming-health.sh` + `dream.cli health` + hourly cron entry installed idempotently by `scripts/install-dreaming.sh`. Verified by running both the wrapper script directly and re-invoking the install script (second run reports "already present — skipping"). 296 unit tests pass including 7 new health-check tests covering: cold start, happy path, stale last-run, active halt, skip-status normalization, most-recent-heartbeat-wins, custom threshold override. PR #1 commit aeca186 in internexio/[project].
