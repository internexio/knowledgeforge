---
title: CI branch-by-SHA collision — idempotent push pattern
source_mode: debugger
novelty_type: reusable_diagnostic + transferable_pattern
grounding_score: 0.85
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-08-16
domain: infrastructure
topic: ci-cd
tags: deployment, quality-gate, validation
related_entries: []
---

# CI branch-by-SHA collision — idempotent push pattern

## Problem

CI workflows that name feature branches by commit SHA (e.g. `compile/cc-{sha7}`) fail on re-runs with:

```
! [rejected] compile/cc-2583fd0 -> compile/cc-2583fd0 (fetch first)
```

Two scenarios trigger this collision:

1. **Re-running the workflow for the same commit** — manual dispatch, retry after transient failure
2. **Previous run merged the PR but left the remote branch** — GitHub "delete branch on merge" disabled, or merged via `gh pr merge` without `--delete-branch`

In both cases, the workflow attempts to push a branch that already exists on the remote, the push is rejected, and the CI pipeline fails.

## Fix Pattern

Before creating and pushing the branch, add two guards in sequence:

```bash
# Guard 1: Skip entirely if an open PR already exists for this SHA
EXISTING_PR=$(gh pr list \
  --repo owner/target-repo \
  --head "$BRANCH" \
  --json number --jq '.[0].number' 2>/dev/null)
if [ -n "$EXISTING_PR" ]; then
  echo "PR #${EXISTING_PR} already exists — skipping."
  exit 0
fi

# Guard 2: Delete the remote branch if it exists but has no open PR
# (handles merged-but-not-deleted case)
git push origin --delete "$BRANCH" 2>/dev/null || true
```

Then proceed with normal checkout → commit → push → `gh pr create`.

The first guard short-circuits the entire workflow when reusable work already exists (idempotent). The second guard clears stale branches that were merged but not cleaned up (makes push idempotent even after merge).

## When This Applies

- Any CI workflow that compiles/transforms one repo and opens PRs in another
- Branch name is derived from a deterministic value (commit SHA, version string, date)
- Multiple runs may target the same "slot" — manual retries, push-triggered + dispatch-triggered overlapping

## When This Does NOT Apply

- Branch names include a unique run ID (e.g. `compile/{sha}-r{run_number}`) — collisions are impossible
- Single-repo workflows where the branch is always rebased — different failure mode
- Workflows that rely on branch deletion being performed by GitHub's "delete branch on merge" setting — in that case, ensure the setting is enabled and don't assume it

## Source Context

Discovered while fixing knowledgeforge-core CI (sync-modules-cp.yml and compile-cc.yml workflows). Both workflows use `compile/{cc,cp}-{sha7}` branch naming. After a PAT rotation caused transition-window failures, subsequent re-runs collided with previously-merged branches that GitHub's auto-cleanup had not yet removed.

Fix committed at knowledgeforge-core:
- Commit 3550680 (CP workflow)
- Commit 1ac1003 (CC workflow)

Both workflows verified passing on re-run after fix (2026-08-16).

## Applicability Notes

This pattern generalizes beyond KnowledgeForge. Any multi-repo CI pipeline using deterministic branch naming should consider adding these guards. The cost is minimal (two lightweight git/gh calls), and the benefit is high—eliminating a class of CI-retry failures that are otherwise invisible until manual investigation.
