---
title: Force-closing a bd epic with an intentionally-deferred child — when --force is acceptable and how to document it
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.7
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-05-30
tags: beads, bd-cli, dolt, workflow, epic-management, orchestration
domain: orchestration
topic: epic-closure-workflow
related_entries:
  - wiki/infrastructure/2026-05-27_bd-cli-dependency-wiring-inversion-two-pass-pattern.md
  - wiki/orchestration/2026-05-30_bead-tracker-workflow-pipeline-triage-decisions-build-deploy.md
  - wiki/architecture/2026-05-18_bead-as-context-anchor-deferred-runbooks.md
---

# Force-closing a bd epic with an intentionally-deferred child

`bd close <epic>` refuses to close an epic that has any open child issue, raising "cannot close epic <id>: N open child issue(s); close children first or use --force to override". This is the right default — it prevents accidental epic closure that buries unfinished work. But it also blocks the legitimate case where:

1. The epic's actual deliverable has shipped (verified end-to-end).
2. An open child issue represents work that was deliberately re-scoped / split out / deferred for separate tracking — not work-in-progress under the epic.

In that case, `bd close <epic> --force --reason="..."` is the correct action, provided the reason line explicitly explains why the child stays open.

## When the force-close is correct

All of these conditions must hold:

- The epic's primary deliverable is shipped and verified (commit hash + verification target named in the reason).
- The open child was filed as a deliberate carve-out — typically because the child became a different scope question (e.g. an API-surface promotion that needs separate triage), or because the user explicitly deferred it during a `/bead-decisions` or session-level decision.
- Closing the epic does not lose the child — the child remains open in bd and continues to surface in `bd ready` / `bd list --status=open` on its own merits.

## When the force-close is WRONG

- The open child is the unfinished half of the epic's deliverable (e.g. epic = "feature X frontend + backend", child = "backend half" still open). Close the child first.
- The open child is "we'll do it in next session" rather than a deliberate scope split. That's work-in-progress, not a deferral — leave the epic open.
- The open child blocks a downstream dependency (other beads have `bd dep add <other> <child>`). Force-closing the epic doesn't relieve the dependency, but it can give the false impression that the child is also out of scope.

## How to document the close reason

The close reason should be machine-greppable for the deliberate-deferral pattern and human-clear for future readers. Template:

```
Epic shipped: <primary deliverable shipped + verification target>. Open child <child-id> (<child title>) is intentionally DEFERRED per <session/decision reference> — tracked separately, not blocking this epic close.
```

Capitalized "DEFERRED" makes the intent grep-friendly. Naming the child id + title means future readers don't need to chase the bd graph to reconstruct why the close was forced.

## Grounding

Verified twice in the [project] session of 2026-05-30:

- **cos-3qz epic (Expert Council MVP)** — force-closed earlier in the session after user instruction "Close cos-3qz (MVP shipped)" because the prior triage had treated cos-3qz as "build Expert Council" but the EC was already fully built (203 tests + 14 routes shipped). Open child cos-fcm (a re-scoped piece) was tracked separately. Force-close succeeded with explicit reason.

- **cos-p45 epic (BC Phase 3a: JSON import)** — force-closed tonight after prod-verified ship of the JSON import. Open child cos-snc ("Promote buyers-committee to API surface") was DEFERRED per session decision earlier ("Approve: build /api/analyze/blindspot (cos-fcm) now; defer cos-snc"). Force-close succeeded with the reason capturing the deferral and naming the child id.

Both instances confirm the pattern: force-close is safe when the open child is a deliberate carve-out, not work-in-progress.

## Why bd defaults to blocking the close

The default behavior protects the common case where a parent-issue closes by mistake while children are still active. In a long-running pipeline (the `/bead-triage` → `/bead-decisions` → `/bead-build` cycle), it's easy to lose track of children mid-batch. The `--force` flag forces the operator to actively justify the override, which is the right tradeoff — the cost of a force-close-with-reason is low; the cost of silently losing track of a child is high.

## Related patterns

- **bd CLI dependency-wiring:** two-pass pattern for reliable batch bead creation with dependencies.
- **Bead-tracker workflow pipeline:** the orchestration framework that surfaces deferred beads via `/bead-decisions` and `/bead-build`.
- **Bead-as-context-anchor:** pattern for converting in-session deferrals into persistent beads with trigger conditions.

## When this applies

- Closing an epic after its primary deliverable ships but with re-scoped children remaining open
- Multi-phase work where a child issue becomes a different class of concern (API surface promotion, separate triage)
- End-of-session / end-of-day cleanup where deferral decisions have been explicitly made
- Batch-closing multiple related epics in a pipeline context (e.g. [project] `/bead-build` stage completing Phase 1 work)

## When this does NOT apply

- Closing an epic when its children represent genuinely unfinished work (the epic is incomplete)
- Single-child epics where closing the parent and leaving the child open creates confusion about scope
- Situations where the force-close would obscure a missing dependency (always verify `bd dep list` first)
- Exploratory / uncertain work — defer the close if unsure whether the child truly belongs separately

## Source Context

Verified during 2026-05-30 [project] bead-pipeline session. Two concrete force-closes (cos-3qz and cos-p45) with explicit deferral reasoning in the close reason. Pattern emerged as a distinction between "epic is complete, child is a carve-out" vs. "epic is incomplete, child is unfinished." The force-close with documented deferred reasoning became the practice for distinguishing these cases within the bead-tracker workflow pipeline.
