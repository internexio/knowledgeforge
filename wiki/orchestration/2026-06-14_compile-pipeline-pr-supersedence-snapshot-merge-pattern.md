---
title: Compile-pipeline PR supersedence — close intermediates, regenerate latest at current upstream HEAD
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: slow_decay
importance: 3
created: 2026-06-14
domain: orchestration
topic: recovery
tags: [deployment, empirical]
related_entries:
  - orchestration/2026-06-12_stale-base-pr-conflicts-batched-pushes-workflow-dispatch.md
pinned: false
---

# Compile-Pipeline PR Supersedence: Close Intermediates, Regenerate Latest

## Problem Shape

A compile-pipeline (GH Actions workflow that watches an upstream repo and creates a PR per upstream commit) accumulates multiple open PRs when several upstream commits land before the team merges. Each PR is a full snapshot of the derived artifact at a specific upstream SHA. Merging the OLDEST first creates conflicts on the rest — even though those rest are STRICT SUPERSETS in content (later snapshot contains everything earlier snapshots had, plus more).

The naive resolution (manually resolve each conflict by taking the PR's version) is wasted work: the later PR's content is the correct end-state for ALL of them.

## Pattern

1. **Merge the oldest open PR.** It lands cleanly because it's the only one with no overlapping main.
2. **Trigger a regeneration of the compile workflow at current upstream HEAD.** Most pipelines have `workflow_dispatch:` enabled — `gh workflow run <workflow-name>.yml` from the upstream repo. The regenerated PR represents "compile output at the latest upstream SHA" and is conflict-free against current main.
3. **Close intermediate PRs with `gh pr close <N> --comment "Superseded by #<latest> ..."`.** Document the supersedence chain in the comment so the audit trail is intact.
4. **Merge the new regenerated PR.** End state matches "what the team would have if they'd merged each PR in order, manually resolving each conflict."

## When This Applies

- Compile-pipeline auto-generates one PR per upstream commit (the workflow file watches `push` on `main`)
- Two or more such PRs are open simultaneously
- Each PR's content is a FULL SNAPSHOT of the derived artifact at the named upstream SHA (so later snapshots contain earlier snapshots' content)
- The workflow has `workflow_dispatch:` enabled for manual triggering at current HEAD

## When This Does NOT Apply

- PRs that are INCREMENTAL deltas (each PR is a delta on the prior, so conflicts are real)
- PRs that have substantive review comments or in-progress changes (you'd lose those)
- The compile-pipeline supports `workflow_dispatch` but cannot point at a specific SHA (rare; usually trivially supported)

## Grounding

KF-core 2026-06-14: three open PRs (#35, #36, #37) corresponding to three core SHAs (897d725, b83979d, 20b76a1). Merged #35 (cleanly) → triggered `gh workflow run compile-cc.yml` → new PR #38 generated at core@3800c77 → closed #36 and #37 as superseded → merged #38. End state: cc was in lock-step with core at the latest SHA. Total active time: ~3 minutes. Manual conflict resolution would have been ~30 minutes per PR.

## Source Context

The pattern only works because snapshot PRs are content-supersetting. The common alternative (sequentially merging with `git merge -X theirs` per file) requires a checkout / push cycle and isn't supported by `gh pr merge`. The supersedence approach uses only stock GH UI flows and leaves a clean audit trail.
