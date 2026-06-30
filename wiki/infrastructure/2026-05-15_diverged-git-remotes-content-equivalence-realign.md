---
title: Realigning diverged git remotes via content-equivalence check + force-push
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-15
tags: infrastructure, git, multi-remote, force-push, history-realignment, content-equivalence
related_entries: []
domain: infrastructure
topic: ops
---

# Realigning diverged git remotes via content-equivalence check + force-push

## Pattern

When two git remotes (e.g., `origin` and `production` split across organizations) have walked along different commit histories but contain **identical code content**, every push between them requires cherry-picking onto a temp branch because non-fast-forward push fails.

The sustainable fix is a one-time realignment via force-push, but only safe if you can prove no content is lost. This entry provides the deterministic safety verification.

## Root Cause

Two remotes diverge when both are live upstream:

```
origin/master:      [a] → [b] → [c] → [d₁ (cos-obj3f)]
production/master:  [a] → [b] → [c] → [d₂ (cos-obj3f)]
```

Both `d₁` and `d₂` contain identical code (`cos-obj3f`), but different SHAs. Git's fast-forward mechanism sees different parents and rejects the push:

```bash
git push production origin/master:master
# error: failed to push some refs to 'production'
# hint: Updates were rejected because the tip of your current branch is behind its remote counterpart.
```

Recovery via cherry-pick solves the immediate problem but is unsustainable — every future push becomes a manual operation.

## The Deterministic Safety Check

Use `git cherry` to list commits on the target whose **patch content** (per the patch-id algorithm) is NOT present anywhere in the reference history:

```bash
git cherry <reference-remote>/<branch> <target-remote>/<branch>
```

**Output interpretation:**
- Zero output = all content on `<target>` exists in `<reference>`'s history. Realignment is safe.
- Non-empty output = those commits have unique content. Cherry-pick them onto `<reference>` BEFORE realigning, or they will be lost on force-push.

### Example

```bash
# Verify no unique content on production relative to origin
$ git cherry origin/master production/master
# (no output)

# Safe to realign
```

If the output shows commits like:
```
+ abc1234 some commit message
+ def5678 another commit message
```

Those commits exist only on production and must be preserved before realigning.

## Pre-Flight Checklist (Read-Only)

Run all of these before any destructive operation:

1. **Content preservation check**
   ```bash
   git cherry <reference> <target>
   ```
   Must return 0 commits (empty output).

2. **Branch protection status**
   ```bash
   gh api repos/<org>/<repo>/branches/<branch>/protection
   ```
   If 404 error: not protected, force-push will work without bypass.
   If 200: note the protection rules; may need temporary disable.

3. **Orphan branch scan**
   ```bash
   git ls-remote <target> 'refs/heads/*'
   ```
   Confirm no feature branches fork off the branch being rewritten. Orphans become harder to recover.

4. **Open PR audit**
   ```bash
   gh api repos/<org>/<repo>/pulls --jq '.[] | select(.base.ref == "<branch>") | .title'
   ```
   Empty result = no PR retargeting concerns. Non-empty = collaborators need to be notified.

5. **Create backup tag**
   ```bash
   git tag <branch>-pre-realign-YYYYMMDD <target>/<branch>
   git push <target> <tag>
   ```
   This is your rollback point. Test the tag fetch from `<target>` to confirm it persists.

## Execute with Safety Guard

Once pre-flight clears, force-push with `--force-with-lease` (not bare `--force`):

```bash
git push <target> <reference>/<branch>:<branch> \
  --force-with-lease=<branch>:<last-known-sha>
```

The `--force-with-lease=branch:sha` syntax aborts if the target branch moved since the last fetch — protects against concurrent updates by other engineers.

Example:

```bash
git push production origin/master:master \
  --force-with-lease=master:a51793415403009e70b41741f3fba556edd8cf83
```

## Expected Side Effects

1. **Deploy workflow fires** — target remote sees a "push to master" and triggers its `.github/workflows/*.yml` rules. Desired if you want the realigned code deployed; verify the workflow file includes `push.branches: [master]`.

2. **Container/image build with new SHA** — the old SHA's image remains intact in the registry; no cleanup needed.

3. **Local clones need reset** — other engineers who have clones of the target remote must run:
   ```bash
   git fetch && git reset --hard <target>/<branch>
   ```
   before the next pull. Notify them before executing the force-push.

## When This Applies

- Two git remotes (e.g., dev-org and prod-org split) where a branch has drifted via cherry-picks
- You have authorization to rewrite history on the target remote
- No active feature branches forking off the target's branch
- No open PRs against the target's branch
- No collaborator workflow keying off the existing target SHAs

## When This Does NOT Apply

- **Shared collaborator workflow** — multiple devs pull/push to the same remote. They will need to reset locally, which is disruptive. Use cherry-pick workflows instead.
- **Branch protection blocking force-push** — would need temporary disable + restore. Coordinate with team before attempting.
- **`git cherry` returns non-empty output** — there's unique content that would be lost. Cherry-pick it onto the reference first, commit, then realign.
- **High-stakes public branch** — main/master on a large team. Risk exceeds benefit unless absolutely necessary.

## Rollback If Needed

If the realignment introduces unexpected behavior, revert to the backup tag:

```bash
git push <target> +<branch>-pre-realign-YYYYMMDD:<branch>
```

The `+` prefix is explicit force-syntax. The tag's SHA overwrites the current branch HEAD.

## Concrete Evidence: COS Realignment (2026-05-15)

COS production split: `origin = internexio/cos.git`, `production = SEMalytics/cos.git`

Cherry-picks onto production created distinct SHAs (e.g., `a517934` on production vs `63b6f9b` on origin), but both commits carried the same `cos-o3f` content.

**Pre-flight verification:**
```bash
# Content check: zero commits unique to production
$ git cherry origin/master production/master
# (no output)

# Branch protection: not protected
$ gh api repos/SEMalytics/cos/branches/master/protection
# 404 Branch not protected

# Remote branches: only master
$ git ls-remote production 'refs/heads/*'
# [production master listed]

# Open PRs: none
$ gh api repos/SEMalytics/cos/pulls --jq '.[] | select(.base.ref == "master") | .title'
# (no output)

# Backup tag
$ git tag production-pre-realign-20260515 production/master
$ git push production production-pre-realign-20260515
```

**Execute:**
```bash
git push production origin/master:master --force-with-lease=master:a51793415403009e70b41741f3fba556edd8cf83
# Forced update a517934...52fc445
```

**Result:**
- Deploy workflow ran 11m35s, green
- semalytics.com/cos served new bundle
- Post-push: `git rev-parse origin/master == git rev-parse production/master == 52fc445`
- Future pushes became fast-forward in both directions
- Backup tag retained as rollback point

## Source Context

This diagnostic emerged from live COS production operations (2026-05-15) when `origin` and `production` remotes had walked along separate cherry-pick histories. The realignment enabled push workflows to return to fast-forward semantics and eliminated the need for temp-branch cherry-pick choreography on every deploy.
