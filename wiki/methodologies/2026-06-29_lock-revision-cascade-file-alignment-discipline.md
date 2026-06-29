---
title: Lock-revision cascade — file alignment discipline when a positioning lock changes mid-cycle
source_mode: builder
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.75
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-06-29
domain: methodologies
topic: lock-revision-cascade
tags: kf-module-26, positioning-lock, file-cascade, coherence-discipline, rotation-required, project-state-files
related_entries:
  - methodologies/2026-05-20_propagation-gap-addenda-propose-downstream-changes-that-dont-execute.md
  - patterns/2026-06-26_skill-spec-vs-canonical-doc-staleness-silent-drift.md
  - patterns/2026-06-14_cross-module-summary-row-count-drift.md
---

# Lock-Revision Cascade — File Alignment Discipline

## The Pattern

When a positioning lock artifact (e.g., `wiki/positioning/CURRENT.md` under KF Module 26) revises mid-cycle, multiple downstream files carry the prior framing's vocabulary, targets, and decision triggers. **Skipping the cascade leaves the project incoherent**: CLAUDE.md says one thing, CURRENT_POSITION.md says another, the lock artifact says a third. The next session opens with conflicting context, and the operator's first hour is reconciliation instead of execution.

The discipline: when a lock revises, treat the revision as the *first* of a chain. The lock artifact change is necessary but not sufficient.

## The Cascade Chain

When a Module 26 positioning lock changes, these surfaces must update for project coherence:

1. **`wiki/goals/CURRENT_POSITION.md`** — cycle targets table (may carry RETIRED targets that no longer apply under new framing), "What this cycle is NOT testing" list (may need to retire stale lines or add new defer rules), decision triggers (any trigger referencing the prior framing or now-retired engagement must update).
2. **Project root `CLAUDE.md`** — "Current state" section and strategic guardrails. Stale notes like "premise update pending" should be removed once the update lands.
3. **`wiki/metrics/CURRENT_WEEK.md`** — cycle target retrofit + retrospective for the half-cycle prior to revision + concerning-indicators that now include lock-specific gates.
4. **`wiki/pipeline/INDEX.md`** — if any active pipeline or engagement carried the prior framing's value proposition (e.g., a "dog-food substrate" engagement classified under prior lock), the carry-over decisions section captures what changes.
5. **`wiki/daily_log/YYYY/MM/YYYY-MM-DD.md`** — captures the revision event itself + the structural reasoning (was it operator-correction-on-evidence vs coaching-pressure-derived).
6. **`rotation_required[]` section INSIDE the lock artifact** — lists product/marketing surfaces that contradict the new lock and must rotate to come into alignment. This is the structural discipline that prevents drift after revision.

## When This Applies

- Any KF Module 26 lock revision — customer-facing or investor-facing one-liner changes, distribution_channels block changes, proof_assets restrictions changes, allowed_phrases expansion.
- Analog systems: ICP pivots, pricing-model changes, category-redefinition decisions, any project-wide framework decision that propagates to multiple downstream files.
- Cascade triggers whenever the `customer_facing.one_liner` OR `customer_facing.full` text changes — those are the source surfaces that other files quote.

## When This Does NOT Apply

- Within-cycle micro-adjustments that don't change the lock's `customer_facing` / `investor_facing` surfaces. Phrasing tweaks, hashtag changes, channel additions, allowed_phrases cap increases without semantic shift.
- Hard-lock additions (killed positions) — these add restrictions but don't require downstream rewording.
- Telemetry updates — `wiki/positioning/.telemetry.yml` changes don't propagate.

## The `rotation_required[]` Discipline (the Underrated Half)

The cascade chain above is for SHARED project-state files. But the lock revision also implies changes to **product/marketing surfaces** that live in other repos (e.g., `[project]/` product code, live website copy, scheduled outreach templates). Without explicit tracking, these silently contradict the new lock and burn credibility on every click-through.

The `rotation_required[]` section IN the lock artifact lists every external surface that contradicts the new framing. Each entry: surface description, action required, bead ID, urgency (P1 / P2 / P3 / deferred), and what it blocks. P1 entries block downstream outbound — the cycle's execution-phase cannot legitimately ship while a P1 contradiction is live.

Example from source application (v1.0.5 generator-led pivot):

```yaml
rotation_required:
  - surface: "Ad Copy Analyzer + all 4 copy-scoring wedge tools"
    action: "Delete <h2>This is not an ad copy generator</h2> language"
    bead: cos-udhe
    urgency: P1
    blocking: "all v1.0.5-grounded broadcast surfaces"
```

The P1 entries become a known cycle-2 readiness gate. The metrics file's "what concerning looks like" section references them directly.

## Failure Mode if Cascade is Skipped

Files drift from each other within hours. The next session loads with stale CLAUDE.md "premise update pending" markers, CURRENT_POSITION.md cycle targets that reference retired engagements, and metrics targets that still measure the prior framing's KPIs. The operator opens the project and the first task is reconciliation — which is real cost that's avoidable.

Worst case: outbound ships under the new lock language while the live site / product surface still shows the old framing. Prospects click through and immediately see the contradiction. The lock revision was supposed to improve reply rate; instead it tanked credibility because the cascade was incomplete.

## Grounding

Observed and executed in source session — v1.0.5 had been ratified earlier on 2026-06-27 in client-project, and the cascade through CURRENT_POSITION.md targets + decision triggers + standing rule annotation, CLAUDE.md current-state, CURRENT_WEEK.md retrospective + new targets, pipeline INDEX.md closures + carry-over decisions, and daily log capture was the work of the 2026-06-29 session. 4 commits documenting the cascade are on `origin/main`: `154ec79`, `e4aff48`, `446dbad`, `34b3ebb`.

A specific failure mode from the same session: CLAUDE.md had been edited to mention v1.0.5 in some places but still carried a "cycle test premise update pending per v1.0.5 (currently still tests measurement-led hypothesis from v1.0.3)" parenthetical from a prior partial edit. That single stale phrase would have left a future session believing the cycle test was still v1.0.3-shaped. Caught and removed in commit `e4aff48`. Lesson: partial cascade is worse than no cascade — it creates false signals of completion.

## Discipline Check

After a lock revision, ask:

1. Have all files in the cascade chain been updated? (Run `grep -l "old-lock-vocabulary" .` to find missed surfaces.)
2. Is the `rotation_required[]` section populated with every product/marketing surface that contradicts the new lock?
3. Are the P1 entries tracked as beads in the destination repo?
4. Does the metrics file's "what concerning looks like" reference the rotation P1s as outbound-blocking gates?
5. Did the daily log capture the revision event with structural reasoning, not just a date+title?

If any answer is no, the cascade is incomplete.
