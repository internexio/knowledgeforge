---
title: Beads ↔ disk reconciliation discipline
source_mode: strategist
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-23
domain: methodologies
topic: scope-management
tags: quality-gate, validation, empirical
related_entries:
  - architecture/2026-05-18_bead-as-context-anchor-deferred-runbooks.md
  - diagnostics/2026-05-23_beads-multi-database-working-directory-gotcha.md
  - migrations/2026-05-21_cross-db-bead-migration-external-ref-provenance.md
---

# Beads ↔ Disk Reconciliation Discipline

## When to Apply

At session start, or any time you are about to prioritize beads issues for work. Especially when the recent commit log shows aggressive progress but the corresponding epic/issue is still "open" — that gap is the signal.

## The Rule

Before treating an open beads issue as work-to-do, verify it against on-disk reality. Beads tracks intent optimistically; reality moves faster than the tracker.

### Concrete Reconciliation Steps

1. For each "open" P0/P1 issue, read its description's key deliverable (file path, command, test target).
2. Check the file/test exists at the named path with non-trivial content.
3. Check `git log --oneline` for commits whose message references the issue's deliverable.
4. If the deliverable exists AND has a recent commit, the issue is already done — close with `bd close <id> --reason="Verified complete on disk: <evidence>. Reconciled with on-disk reality."` rather than re-implementing.

## Why This Matters

Treating beads as ground truth leads to:

- **(a) Re-implementing already-done work** — the issue tracker is optimistic; the code moved faster than the tracker updated
- **(b) Cascading priority confusion** — when "blocked-by" relationships reference closed-in-reality issues, the strategist plan treats them as still-open, cascading false dependencies
- **(c) Wasted strategist analysis** — spending analysis budget on problems that are already solved

The asymmetry: **a 5-minute reconciliation pass prevents hours of duplicate or misprioritized work.**

## When This Does NOT Apply

- Single-developer beads DB in a fast-moving session where you wrote the work yourself — you already know the state
- Trivial issues (P3/P4 cleanup tasks) where reconciliation cost exceeds re-doing the trivial work
- Issues where the deliverable is inherently process-state (e.g., "review this PR") rather than disk-state; these need human verification, not git-log lookup

## Grounding From the Producing Session (2026-05-22)

Reconciliation pass during KF 7.0 validation session closed 6 stale-but-done issues that the strategist plan had treated as work-to-do:

- **kf-9fx** (module index) — file already at `hooks/kf_module_index.txt`
- **kf-oea** (kf-route.py hook script) — already 21 KB, fully working
- **kf-76j** (Ollama install) — superseded; the route hook now uses Gemini Flash Lite API instead
- **kf-e3o** (Phase 2 epic) — thin CLAUDE.md + 10 skills + 14 docs all committed
- **kf-8z4** (30-prompt test suite) — already at `knowledgeforge-core/tests/routing_test_suite.yaml` (31 cases)
- **kf-354** (cleanup of misplaced wiki file) — file already deleted

Each reconciliation took 1-2 minutes; the total strategist re-analysis prevented by not re-implementing these 6 would have consumed 30+ minutes.

## Bonus Pattern (Related)

When the issue's deliverable references a different repo than the one the issue lives in (e.g., tracking a bug in `[project]/iteration_loop/stages/calibrator_confidence.py` from inside `knowledgeforge-cc`'s beads DB), **refile in the correct repo** with a cross-reference and close the misfiled one. The right repo is the one whose CI/tests would catch the regression — usually the repo where the code lives.

## Source Context

Discovered during 2026-05-22 KF 7.0 validation session (kf-7-phase1-validation-2026-05-22) while strategizing the next sprint. Reconciliation against `git log --oneline` and filesystem checks revealed that 6 issues tracked as "open" had already shipped. The pattern generalized from this concrete finding: treat reconciliation as a discipline, not a one-off check.
