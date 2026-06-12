---
title: Stale-base PR conflicts after batched core pushes — resolve via workflow_dispatch
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-06-12
domain: orchestration
topic: multi-stage-issue-workflow
tags: deployment, api, routing
related_entries: ["infrastructure/2026-05-25_ci-auth-failure-workflow-diagnosis-before-chasing-local-state.md", "compiler/multi-repo-artifact-placement.md"]
---

# Stale-Base PR Conflicts After Batched Core Pushes

## Diagnostic — Symptom and Signature

After a batched session of multiple pushes to a "source" repo (e.g., `knowledgeforge-core`) that triggers per-push PR-generating workflows on one or more "variant" repos (e.g., `knowledgeforge-cc`, `knowledgeforge-cp`):

- Variant repo accumulates N stacked PRs, each generated against the variant's main HEAD at the time the workflow fired
- If NONE of the prior PRs were merged before later pushes, all PRs are based off the same stale variant-main state
- Later, when ONE prior PR finally lands on variant main (e.g., a hotfix PR merges out-of-band), all the other still-open PRs become CONFLICTING
- GitHub UI shows `mergeStateStatus: DIRTY` and `mergeable: CONFLICTING`

### Root Cause

The compile/sync workflow creates branches off the variant repo's current main HEAD at trigger time. When source-side changes accumulate but variant-side merges happen out-of-order, the later PRs end up containing source-side deltas that already partially landed via the earlier merge — the SAME variant-side files have been modified two different ways:

1. Once by the merged PR's branch-modifications
2. Once by the open PR's branch-modifications

This is NOT a source-side conflict (the source commits are fine); it's a **variant-side branch-base mismatch**. All PRs thought they were branching off the same state, but one merge changed that state mid-batch.

## Fix — Fresh Compile via workflow_dispatch

**Steps:**

1. Close all stale variant-side PRs with `gh pr close <N> --delete-branch` and a comment noting they were stale-base.
   ```bash
   gh pr close 32 --delete-branch
   gh pr close 33 --delete-branch
   ```

2. Trigger a fresh compile via `gh workflow run <compile-workflow.yml>`.
   - Workflow checks out source@latest + variant@latest
   - Runs compiler against current state of both
   - Creates a new PR against current variant main — CLEAN base
   ```bash
   gh workflow run compile-cc.yml
   ```

3. Wait for completion (~15-30s for KF's compile workflows)

4. Merge the new PR once CI passes

This works because the workflow always uses HEAD-vs-HEAD, so the new PR's branch is automatically based off whatever variant main currently is.

## When This Applies

- Multi-push session in the source repo with NO intermediate variant merges **at the time pushes were batched**
- Variant has a PR-generating workflow (not a direct-push workflow)
- At least one variant-side merge happened mid-session, AFTER some PRs were already generated but BEFORE others

### Concrete Verification Checklist

- All stale PRs have `mergeStateStatus: DIRTY` or show file-content collisions
- The conflict is NOT in source files (source is clean); it's in compiled output
- Two PRs show conflicting edits to the SAME file (both think they're adding the same content)
- One PR merged between the generation of the stale PRs

## What Does NOT Work (And Why)

### Alternative 1: Rebase the stale PRs in place

Trying to rebase the stale PRs doesn't work well:
- Merge conflict resolution would be tedious (often 30+ files affected)
- The conflicts are non-semantic (just file content collisions from the same compile-output bytes)
- Rebasing buys nothing vs throwing away and regenerating

### Alternative 2: Merge the stacked PRs in order

This DOES work if none of them have a stale base — i.e., when no out-of-band variant merges happened. Useful pattern when applicable. But the stale-base case requires the workflow_dispatch fix.

## Process Implication for Future Sessions

The cleanest workflow is: **merge each variant PR as it's generated, before the next source push.** The cleanup-at-end pattern works when no intermediate merges happen but breaks otherwise.

For multi-hour batched sessions where intermediate merges may happen organically (e.g., a hotfix lands while you're still iterating on features), plan on the workflow_dispatch path being needed.

If you know a session will involve stacked source-side pushes without intermediate variant merges, you can batch-merge variant PRs at the end. But don't assume this will hold during long sessions.

## Verified During

2026-06-12 KF session, cleanup round 2. Five core pushes happened:
- `4533793` (3ym)
- `9d09b4d` (specs)
- `748f5ee` (8gp impl)
- `0fa5477` (8zt impl)

**cc (confluent):**
- 3ym-triggered PR #31 generated
- PR #31 merged mid-session → cc main moved
- Subsequent 8gp PR (#32) and 8zt PR (#33) were generated against pre-merge cc main
- Both #32 and #33 were CONFLICTING after the 3ym merge landed
- Closed both stale PRs + triggered `gh workflow run compile-cc.yml`
- Fresh PR #34 generated against current cc main
  - 35 additions / 35 deletions / 34 changed files
  - CLEAN, MERGEABLE, merged in one shot

**cp (clean):**
- All 3 cp PRs shared the same base (no out-of-band cp merge had happened)
- Confirming that the stale-base condition requires both:
  - Batched pushes creating multiple stacked PRs
  - An intermediate merge happening between PR generation times

## Source Context

Extracted from knowledgeforge-core 2026-06-12 session (cc-cp-pr-cleanup-stale-base). After Phase 1 and 2 core releases, two variants (cc and cp) had accumulated stacked PRs from the batched pushes. The cleanup round discovered stale-base conflicts on cc PRs post-merge, resolved via workflow_dispatch pattern. This is reusable for any multi-repo compile-sync workflow where variant-side merges can happen mid-batch.
