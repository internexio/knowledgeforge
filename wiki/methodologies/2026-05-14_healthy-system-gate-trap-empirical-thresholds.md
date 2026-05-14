---
title: Healthy-system gate trap — failure-mode thresholds never trip in working systems
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.80
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-14
domain: methodologies
topic: gate-design, staged-rollout
tags: methodologies, diagnostics, gate-design, empirical, threshold-tuning, escalation-design
related_entries:
  - infrastructure/2026-05-13_deployment-gap-audit-shadow-mode-patterns.md
  - methodologies/2026-05-13_find-consumer-first-before-data-migration.md
  - orchestration/spec-commit-before-impl-commit.md
---

# Healthy-System Gate Trap — Failure-Mode Thresholds Never Trip in Working Systems

## The Diagnostic

When a feature's "ready to ship Phase B" gate is conditioned on accumulating
failure-mode signals (e.g., ≥N `would_escalate` events, ≥M crash recoveries,
≥K timeout incidents), the gate may never clear in a healthy system. The
empirical-soak design assumes the data will arrive; if the system is working
correctly, the data is exactly what doesn't accumulate. The gate becomes a
permanent block on a feature that may not need to ship at all.

## Concrete Grounding ([project] u9z, 2026-05-13 → 2026-05-14)

`[project]-u9z` (Pattern 3: replace forever-backoff with one-retry-then-escalate)
shipped Phase A on 2026-05-13: shadow logging via `SHADOW_ESCALATION=1`, writes to
`/tmp/[project]-shadow-escalations.jsonl` on any orchestrator failure at
attempt ≥ 8.

**Phase B unblock gate:** ≥5 `would_escalate` events observed in the shadow log
before flipping live escalation.

**Soak check** ~5h after deploy (2026-05-13 22:00 → 2026-05-14):
- `/tmp/[project]-shadow-escalations.jsonl` did NOT EXIST. Not empty — absent.
- `record_failure()` had not been called once.
- `/tmp/happy-backoff-state/` directory empty (no session in failure mode).
- Orchestrator (PID 87269) running cleanly since restart.

**Implication:** The orchestrator's auth + session lifecycle was completely healthy
since the Phase A deploy. Zero events → 0 / 5 toward the gate.

**Extrapolation:** At typical orchestrator-failure rates (none observed in
the prior 7 days either), reaching 5 `would_escalate` events would require a
genuine outage event lasting hours, or a regression. Neither is desirable just
to unblock a feature.

## The Trap Mechanism

The gate was designed in a vacuum:

1. **Pattern 3 critic-pass** rejected calendar-based gating ("ship after N days")
   because it provided no empirical evidence the escalation path works.
2. **Empirical-signal gating** was substituted ("ship after N events") as the
   rigour-preserving alternative.
3. **The vacuum** did not account for what a *healthy* system produces — namely,
   no events.

Both gating choices have failure modes:

- **Calendar gate:** Ships untested code on a date even if the code is wrong.
- **Pure empirical gate:** Never ships even if the code is right; or worse,
  incentivises waiting for or producing the failures the code is meant to fix.

## The Fix (Applied)

Two complementary moves:

1. **Lower the threshold** to the minimum that still validates the path
   (u9z: 5 → 3). The threshold size assumed a noisy system; in a quieter
   system, fewer events are sufficient to verify the path.
2. **Add an explicit healthy-system clause** to the bead notes: "if soak runs
   N+ days without M events, that is itself signal — the escalation path may
   not be needed in its current shape, and the work may re-scope or defer."
   This converts the silence into actionable signal rather than indefinite block.

## When This Applies

- Phase B / staged-rollout gates that fire on failure-mode data
- Shadow-mode features waiting on production signal to flip live
- Empirical-soak gates designed by critics rejecting calendar gates
- Watchdog / escalation features (by definition, soak-data is failure-data)
- Cost-meter / quota-breach / circuit-breaker flip gates
- Backoff / retry path validation gates
- Any pattern designed to activate only when some system is *broken*

## When This Does NOT Apply

- Gates conditioned on *successful* signal (e.g., ≥N healthy heartbeats, ≥M
  passing dry-runs). These accumulate in working systems by design.
- Synthetic-injection-allowed environments (staging, fuzz tests). If the
  team can deliberately produce failures for the test, threshold can be
  arbitrary.
- Tier 4 / kill-switch / kill-criterion gates (intentional non-firing).
- Features designed to activate in degraded states (by design, activation is rare).

## The Deeper Lesson

A failure-mode threshold without a "what if it never arrives?" clause is a
permanent commit to feature limbo. Empirical gates need a re-scoping
trapdoor: **"if N didn't arrive in M time, here's how we decide whether to
ship anyway, lower the threshold, or remove the feature."**

Calendar gate + empirical gate are both incomplete. The right shape is
**empirical gate with calendar trapdoor**: "ship when N events OR M days
elapse AND active re-evaluation triggers."

## Antipattern: Threshold Set for Hypothetical Noise

Thresholds are often designed by imagining "a noisy system":
- "If the system has lots of transient timeouts, we want ≥5 before shipping."
- "If retries fail often, we'll need ≥10 escalation events."

But if the system is *actually* healthy, that hypothetical noise doesn't materialize. The threshold becomes a permanent block disguised as empirical rigour.

**Check the assumption:** Before committing to an N-event threshold, verify that N events will actually arrive in the target environment within some reasonable time horizon (e.g., 1 week). If not, lower N or add a calendar trapdoor.

## Related Concepts

- **Spec-commit-before-impl-commit** (timing pattern — same design-in-vacuum domain)
- **Forward-compat-vs-premature-optimization** (sibling principle — threshold designed for hypothetical noise that didn't materialize)

## Source Context

Discovered during iteration-loop v0 Phase 1 wrap-up + paperclip soak status
check on 2026-05-14. The user requested a Pattern 2/3/5 soak summary; the
empty `/tmp/[project]-shadow-escalations.jsonl` revealed the gate was
structurally unlikely to clear. Fix applied to [project]-u9z bead within
the same turn: threshold lowered 5 → 3, healthy-system clause added to bead notes.

The pattern surfaced during validation of shadow-mode deployment (related entry:
deployment-gap audit checklist). Once verified that the shadow logging was
running and producing zero events after healthy-system soak, the gate design
became the next diagnostic target.
