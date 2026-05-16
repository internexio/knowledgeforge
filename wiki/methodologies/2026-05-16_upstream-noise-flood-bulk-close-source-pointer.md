---
title: Surviving an upstream-noise flood in the issue tracker — close-with-source-pointer, accept recurring waves
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-16
tags: methodologies, project-management, issue-tracking, beads, upstream-dependencies
related_entries:
  - methodologies/2026-05-15_pre-emptive-scope-sweep-downstream-verdict.md
  - infrastructure/2026-05-15_silent-success-scripts-state-artifact-freshness.md
  - infrastructure/2026-05-14_idempotent-watchdog-producer-pattern.md
---

# Surviving an upstream-noise flood in the issue tracker — close-with-source-pointer, accept recurring waves

## The Pattern

When an external automated system floods the issue tracker with low-signal entries — site monitors, security scanners, dependency-bot pings, AI-generated suggestion firehoses — the temptation is to **triage each one** for genuine actionability. That impulse loses to the math: a system emitting N noise items per hour will outpace any human triage rate, and "what if this one is real" anxiety makes every closure feel costly.

The pattern that scales is:

1. **Identify the source.** One grep across the tracker for the recurring title pattern; one read of the issue body to find the routing tag (e.g., "Source: site-monitor"); locate the upstream file. If it's outside your repo's scope, name that explicitly.

2. **Bulk-close with a wontfix that points at the source.** Don't triage individually. The close reason becomes the trail of breadcrumbs to the actual fix:
   - WHO generated this (filename + line number of the routing logic)
   - WHY it's not actionable in *this* scope (wrong URL / different repo / monitoring config bug)
   - WHAT the upstream fix would be (one-line change in the source file)
   - WHERE to do it (which separate session / which repo)

3. **Accept the recurrence.** New duplicates will keep arriving on the same cron cadence until upstream is fixed. **The mass-close does not stop the firehose.** Closing today's wave is hygiene — it gets the tracker out of "P0-overflow" state — but it does not solve the underlying problem. Plan a separate session for the upstream fix; don't conflate "tracker is clean" with "problem is solved."

4. **Don't pick at false positives.** Some of the noise items may *coincidentally* be useful suggestions (e.g., "Add Schema.org markup" is reasonable advice even if pointed at the wrong URL). Resist the urge to convert them to real beads in the same close pass — that's how scope creep enters. Instead: if any noise item *would* be useful when retargeted, file a SEPARATE bead with explicit content + acceptance criteria, *after* the bulk-close lands. Keep the noise-close stream clean.

## When This Applies

- A recurring automated source is producing identical-shaped issues at >5/hour.
- The upstream source is outside the current session's authorization scope (different repo, different on-call, different account).
- The signal-to-noise ratio is low enough that individual triage isn't economical.

## When This Does NOT Apply

- The "noise" might include real outages mixed in with false positives — never bulk-close monitoring alerts on a system that's actually in distress without verifying. Check the underlying-system health independently first.
- The source is fixable in this session — fix it instead of clearing downstream noise.

## Concrete Grounding: COS / [project], 2026-05-16

The COS `.beads/` tracker accumulated **189 noise issues** in a single morning from a misconfigured [project] site-monitor at `~/Scripts/[project]/scripts/gastown-router.py` line 34 — the routing map had `"cos.semalytics.com": "cos"`, but that hostname has a broken SSL cert and is not the prod URL (real URL: `semalytics.com/cos`). The monitor was pinging a dead endpoint and generating both "Fix website availability" (63 P0) and SEO/UX-suggestion (126 P1) beads against it.

Per CLAUDE.md's [project]-only rule, fixing [project] was out of scope for the cos session. The close pattern applied:
- Bulk-close all 189 with `bd close <id> --reason "<wontfix + source pointer>"` via a `while read; do ... done < /tmp/noise.txt` loop.
- Reason text included: file path of upstream source, line number of the wrong-URL mapping, broken-cert context, and "this and N sibling noise beads from the same monitor run" for traceability.
- Verified prod URL was healthy independently (deploy run 25951873287 green; semalytics.com/cos HTTP 200).
- Mid-session: a second wave of 50 P1 SEO noise arrived during the close pass; closed those too as wave #2. Documented in CLOSE_REASON that "new duplicates will keep arriving until [project] monitor is fixed in a separate non-cos session."

The cleared-tracker state lasted only until the [project] cron's next firing (~1 hour). Closing the noise three times in one day was the right call — each close cleared the P0/P1 ready-queue so real work surfaced — but it did not solve the underlying problem, which remains scheduled for a non-cos session.

## Anti-Pattern to Avoid

The **"I should investigate each one in case it's real"** reflex. With identical-shaped automated entries, the marginal value of investigating bead #87 of 189 is approximately zero. Sampling 1–2 from the batch is enough to confirm the noise pattern.

## Process Integration

**Automation opportunity:** If noise entries follow a stable schema, write a one-off script that:
1. Greps the tracker for the source pattern
2. Reads one sample entry to extract issue_ids
3. Generates a batch close command with a templated reason text

Example for [project] URLs:
```bash
bd search "gastown-router" --status open \
  | grep -oE '\[cos-[0-9]+\]' \
  | while read id; do
      bd close "$id" --reason "wontfix: upstream noise from ~/Scripts/[project]/scripts/gastown-router.py:34 (routing map has wrong hostname). See non-cos session."
    done
```

The loop takes seconds vs. minutes of one-by-one UI clicks. Saves the cost of the second and third waves.

## Related Patterns

- **[[pre-emptive-scope-sweep-downstream-verdict]]** — similar "batch classification before execution" thinking; applies to task interdependencies rather than noise sources
- **[[idempotent-watchdog-producer-pattern]]** — upstream pattern for reliable producer circuits that minimize false positives to begin with (preventive vs. reactive)
- **[[silent-success-scripts-state-artifact-freshness]]** — detecting liveness of monitoring systems via artifacts rather than log inspection (useful for verifying "did the monitor actually run today?")

## Source Context

Discovered 2026-05-16 during COS [project] site-monitor noise flood. Direct application: 189 P0/P1 noise beads from misconfigured gastown-router.py; closed in three bulk passes (waves #1, #2, #3 spanning the morning). Pattern immediately transferable to any tracker receiving sustained low-signal bursts from external automated systems.
