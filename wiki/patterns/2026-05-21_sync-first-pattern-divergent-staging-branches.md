---
title: Sync-first pattern for divergent staging branches
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-21
tags: git-workflow, deploy-strategy, staging, ci-cd, branch-management
related_entries: ["infrastructure/2026-05-19_git-dash-c-cwd-stability-claude-code-bash.md", "infrastructure/2026-05-15_diverged-git-remotes-content-equivalence-realign.md"]
domain: patterns
topic: synthesis
---

# Sync-first pattern for divergent staging branches

## Pattern

When the staging branch (e.g., `test`) is N commits behind the production branch (e.g., `main`), and you're about to ship a new change through `staging → prod`, do not bundle the sync and the new change into a single push. Split into two commits/pushes:

1. **Sync push:** Merge `main` into `test`. Push `test`. Wait for staging deploy to complete. (No new feature code yet.)
2. **Feature push:** Add the new commit on top of synced `test`. Push `test`. Wait for staging deploy. Verify on staging sites.

Then merge `test → main` (typically a fast-forward) and push `main` to deploy to prod.

## When This Applies

- Staging branch is **significantly** behind prod (≥ 5 commits, or any divergence touching the same files as your new change)
- Staging environment is supposed to mirror production
- Your change interacts with files that have moved on `main` since the last sync
- You want to verify the new change on a staging state that actually matches what prod will look like post-merge

## When This Does NOT Apply

- Trunk-based teams where `main` *is* the only branch — no staging concept
- Staging branch is at-most 1–2 commits behind and the divergence doesn't touch your change's files
- Your change is purely additive (new migration, new file) and doesn't depend on recently-changed code paths
- You're explicitly testing "what happens when staging is behind prod" (rare)

## Why Bundled Sync + Feature is Dangerous

If you bundle the sync and feature in one push:

- **Staging deploys a Frankenstein** — staging now runs `prod-as-of-N-commits-ago + sync + feature` all at once
- **Verification is contaminated** — if staging breaks, you can't tell whether the sync caused it or your feature did
- **Rollback is messier** — reverting "the bad push" reverts both sync and feature, leaving staging behind again
- **CI is noisier** — one giant diff vs. two clean, attributable diffs

## Concrete Grounding (Tuan NW, 2026-05-21)

**Project:** Laravel multi-location restaurant app (lacabar.com, lacacafe.com, laca38th.com + tuannorthwest.com parent)

**State found:** `test` branch was 10 commits behind `main`. `main` had:
- SEO title/meta updates (P0 target)
- ClickAdTech tracking integration (4 commits)
- Layout fixes for tracking partial
- 410 responses for spam URLs
- Content fixes

**Risk if bundled:** Deploying P0 SEO changes to test sites without also having ClickAdTech work → false negative on JS errors / CSP violations from the tracking partial; H1 verification on a stale layout; potentially breaking change detection

**Mitigation applied:**
1. `git stash push -u` to preserve WIP
2. `git checkout test && git pull origin test --ff-only`
3. `git merge main -m "merge: sync test branch with main (pre-P0 SEO sync)"`
4. `git push origin test` (sync push — deploy ran, validated)
5. `git stash pop` to restore WIP
6. Stage only P0 files, commit, `git push origin test` (feature push — deploy ran, P0 verified on test sites)
7. `git checkout main && git merge test --ff-only && git push origin main` (prod deploy)

**Result:** Both pushes deployed cleanly. P0 changes verified on test sites against a production-equivalent baseline. Prod fast-forward was clean (no merge commit).

## Operational Checklist

```bash
# 1. Check divergence first
git log --oneline main..origin/test     # unique-to-test
git log --oneline origin/test..main     # unique-to-main

# 2. If main is meaningfully ahead, sync first
git stash push -u -m "wip-before-sync"
git checkout test
git pull origin test --ff-only
git merge main -m "merge: sync test branch with main"
git push origin test                    # sync push — deploy runs

# 3. Wait for staging deploy to complete and validate

# 4. Then add your feature
git stash pop                            # if you had WIP
# OR: re-apply your changes here
git add <only your files>
git commit -m "<feature commit>"
git push origin test                    # feature push — deploy runs

# 5. Wait for staging deploy, verify feature on test sites

# 6. Merge to main and deploy to prod
git checkout main
git merge test --ff-only
git push origin main
```

## Related Considerations

- If `git merge main` produces conflicts mid-sync, resolve them on `test` as part of the sync push — don't tangle conflict resolution with your new feature.
- The sync push will also include any other in-flight work that was on `main` but not `test` — confirm with the team before pushing if uncertain.
- After the sync push completes deploy, verify staging is healthy *before* adding your feature on top. A broken sync masks broken feature work.
- Use `git log --oneline -N` to see which commits are unique to which branch before deciding how far behind staging actually is.

## When This Applies (Variations)

**Multi-environment pipelines:** Any setup where you have dev → staging → prod branches and the sync gap is meaningful enough to interact with your change.

**Feature branches that depend on recent main work:** If your branch (or WIP) requires recent commits from `main` to compile/run, the two-phase pattern is essential. Phase 1 (sync) proves the merge is clean; Phase 2 (feature) proves your code works with the full main baseline.

**Risk-averse deployments:** High-traffic sites, production-critical services, or safety-sensitive changes benefit even when the gap is small. The marginal cost of two deploys is low; the debugging cost of a Frankenstein deploy is high.

## Source Context

This pattern emerged from live deployment work on Tuan NW Corp restaurant sites (2026-05-21) when a P0 SEO change needed to ship through a staging branch that was 10 commits behind production. The two-phase sync+feature approach allowed verification of both the sync baseline and the new feature independently, reducing risk of false negatives during staging validation. The pattern is reusable across any multi-environment git workflow where staging and production branches diverge.
