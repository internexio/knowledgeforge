---
title: Dormant-subsystem forensics — check the supervision layer before the subsystem code
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-29
tags: methodology, debugging, supervision, dormancy, launchd, watchdog, migration-orphans, forensics
related_entries:
  - methodologies/2026-05-29_deterministic-first-debugging.md
  - methodologies/2026-05-27_read-ground-truth-not-surface-signals-universal-antipattern.md
  - infrastructure/2026-05-14_idempotent-watchdog-producer-pattern.md
  - infrastructure/2026-05-12_self-watchdog-autonomous-fix-cycles.md
domain: methodologies
topic: verification
---

# Dormant-Subsystem Forensics — Check the Supervision Layer Before the Subsystem Code

## The Rule

When a service or background subsystem has gone silent — its database is frozen, its queue stopped advancing, its scheduled output isn't appearing — **diagnose the supervision layer first, the subsystem's own code second**.

Concretely, before reading the subsystem's source: identify what was supposed to keep it running. Check launchd plists / cron / parent-process trees / watchdog scripts / Happy or tmux sessions. Confirm whether that driver still exists, is still loaded, and is still pointing at the right entrypoint. Only after the supervision layer is ruled out should you open the subsystem's source files.

## Why It Matters

When a once-running subsystem stops, the prior probability that **its own code broke spontaneously** is low. The high-probability causes are:

1. The thing that drove it was deprecated / disabled / orphaned during a migration.
2. Its supervisor (launchd, cron, parent process, watchdog) was killed and never restored.
3. A dependency the supervisor relied on (PATH entries, env vars, a sourced rc file) changed.
4. *Its code broke spontaneously.* (Lowest probability.)

Engineers who skip #1–#3 and head straight to #4 spend hours reading code, building hypotheses about race conditions or undetected bugs, and producing a "maybe this could happen if…" diagnosis that doesn't actually match the timing of the outage. Meanwhile, the real answer ("we removed its watchdog plist in commit X") is one `launchctl list` away.

## The Pattern in Practice

When investigating a dormant subsystem, ground the investigation in *timing*. The subsystem's last known activity (DB mtime, last queue write, last log line) is the anchor. Ask:

1. **What was driving this just before that timestamp?** Identify the supervisor by name (specific plist, cron line, watchdog script, parent process, Happy session).
2. **Does the supervisor still exist + run?** `launchctl list | grep <label>`, `crontab -l`, `pgrep`, `ps` for the parent.
3. **If the supervisor died, when did it die?** Correlate with migrations / deprecations / commits around the subsystem's last-activity timestamp.
4. **If multiple subsystems went dormant in the same window**, suspect *one* migration that orphaned several — confirms supervision-layer cause, eliminates per-subsystem-internal hypotheses.
5. **Only then read the subsystem's code.** And read it specifically to validate that reviving the supervisor will resurrect the subsystem cleanly — schema drift, dependency upgrades, config-file format bumps in the dormancy window are real but secondary causes.

## When It Does NOT Apply

- The subsystem is **first-time install / greenfield** — there's no prior supervisor to investigate.
- The subsystem **crashes loudly with a traceback** every time you start it — that's a code/config bug, not orphaned supervision; read the traceback.
- The subsystem was **deliberately disabled** (documented, with a dated reason) — the "outage" is a feature.

## Failure Mode It Prevents

Spending a session reading 5,000 lines of subsystem source to "figure out why it broke" when the actual root cause is a launchd plist that points at a deprecated wrapper script and was unloaded six weeks ago in a per-repo-watchdog → orchestrator migration cleanup.

## Concrete Grounding (Source Session)

Two instances surfaced in a single 2026-05-29 [project] session, confirming the pattern is general rather than incidental:

### Instance 1: Orchestra (Revival via We2u)

Operator memory said "we did this before — orchestra-Telegram worked once and broke." Orchestra's `~/.orchestra/orchestra.db` last task was 2026-02-28 (~3 months stale). The instinct would be to read orchestra's source for "what broke." 

**Ground-truth check:** `claude-orchestra` ran as a Happy tmux session via the deprecated per-repo `~/Scripts/claude-orchestra-dev/scripts/happy-watchdog.sh` (managed by `com.happy.claude-orchestra.plist`). That plist is unloaded; the orchestrator (per [project] CLAUDE.md `## Happy Session Management`) actively kills old per-repo watchdogs; and `claude-orchestra` was never added to the new orchestrator's `SESSIONS` array (laptop branch: only `[project]` + `[project]`, no comment-marked pause).

**Root cause:** Orphaned in the watchdog→orchestrator migration.

Orchestra's own code had a separate schema-drift issue, but that was a downstream secondary cause that only mattered once supervision was restored.

### Instance 2: Lookout (O5lu, Deferred)

Same migration era — its `social_opportunities` table froze at 2026-02-25 (~93 days stale). The Reddit crawler (`lookout/crawlers/reddit_crawler.py`) existed but was **never scheduled** (no cron, no launchd, no process).

The bead's existing description captured the supervision-layer cause perfectly: "Reddit crawler exists but is not scheduled."

## Cross-References

- [[deterministic-first-debugging]] — pairs with this: "exhaust deterministic checks before invoking LLM judgment" includes "check the supervisor before reading the code."
- [[read-ground-truth-not-surface-signals-universal-antipattern]] — applies to the supervision layer too: read `launchctl list` and the actual plist contents, not assumptions about what should be running.
- [[idempotent-watchdog-producer-pattern]] — the pattern for *building* supervisors (watchdogs); this entry is for *diagnosing* when a supervisor was orphaned.
- [[self-watchdog-autonomous-fix-cycles]] — detecting when a cycle stops running (related but focuses on detection, not diagnosis of why it stopped).

## Source Context

Discovered during [project]-orchestra-revival session 2026-05-29 (we2u). Two unrelated dormancy events in the same migration window (watchdog→orchestrator, ~3 months prior) both traced to supervision-layer causes — one disabled plist, one unscheduled crawler. The pattern is general and appears in post-migration audits where supervisors are refactored but not fully re-wired. Grounding instances recur when service landscapes shift (Docker→systemd, per-repo watchdogs→centralized orchestrator, manual cron→scheduled task).
