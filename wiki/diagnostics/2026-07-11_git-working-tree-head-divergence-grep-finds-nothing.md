---
title: Git working-tree/HEAD divergence — grep finds nothing but user reports issue exists
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.75
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-11
domain: diagnostics
topic: root-cause-analysis
tags: metadata-filter, filesystem, empirical, grounding
related_entries: []
---

# Git Working-Tree/HEAD Divergence — Grep Finds Nothing But User Reports Issue Exists

## Symptom

`grep -rn "term" file` returns empty (or zero results), but the user insists the content is still present in the codebase.

## Root Cause

The working tree has already been fixed (or the file hasn't been committed), while git HEAD still contains the old content — or vice versa. The user is seeing the HEAD version (e.g., in a browser on GitHub, or from memory), while grep reads the working tree. These can diverge silently after uncommitted edits.

## Diagnostic Steps

1. Run `git show HEAD:path/to/file | grep "term"` to check what HEAD contains, independent of working tree.
2. Run `git diff -- path/to/file` to see the full delta between working tree and HEAD.
3. If HEAD has the content and working tree does not: working tree has the fix; it just hasn't been committed yet. Stage and commit.
4. If working tree has the content and HEAD does not: the fix was reverted or never applied to the branch. Re-apply the change.
5. Also check `git stash list` and `git log --oneline -10` to rule out stashed or recently reverted commits.

## Concrete Grounding

Occurred in knowledgeforge-cc `docs/add-ons.md` during the cos-skills investigation (2026-07-11). `grep -rn "cos-skills" docs/add-ons.md` returned empty. User reported the reference still existed. Running `git show HEAD:docs/add-ons.md | grep cos-skills` found the reference in HEAD. `git diff -- docs/add-ons.md` confirmed the working tree had the correct fix already applied but uncommitted. Fix: stage and commit the existing working-tree change (`git add docs/add-ons.md && git commit`).

## When This Applies

- User reports content "still there" but grep returns zero results
- After a multi-session workflow where a prior session may have edited a file without committing
- When investigating a reported bug that "grep says doesn't exist" in files the user actively edits between sessions

## When This Does NOT Apply

- Fresh repos with no uncommitted changes (working tree = HEAD by definition)
- Binary or auto-generated files where grep is inherently unreliable
- When the user is certain the change has never been made (no prior session edits)

## Source Context

knowledgeforge-cc vscode-phase2-phase3-cos-skills-fix session, 2026-07-11. User reported missing cos-skills reference in docs/add-ons.md while grep found nothing; actual root cause was HEAD vs working-tree divergence with uncommitted fix in place.
