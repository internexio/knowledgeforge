---
title: Disjoint-file-surface check via comm -12 as pre-parallelize gate for worktree feasibility
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 1.0
staleness_risk: stable
importance: 3
created: 2026-06-14
domain: methodologies
topic: gate-design
tags: [empirical, quality-gate]
related_entries:
  - orchestration/2026-06-12_parallel-spec-parallel-critic-pattern-independent-beads.md
pinned: false
---

# Disjoint-File-Surface Check as Pre-Parallelize Gate

## Problem Shape

Before parallelizing N implementations into separate git worktrees, the team needs a fast deterministic check for whether the parallel branches will conflict on merge. Eyeballing diffs is slow and miss-prone; running both branches and resolving conflicts at merge time is wasteful.

## Pattern

For two candidate branches `spec-A` and `spec-B`, both based on the same parent of `main`, run:

```bash
comm -12 <(git diff main...spec-A --name-only | sort) \
         <(git diff main...spec-B --name-only | sort)
```

- **Empty output** → zero file overlap → safe to land sequentially with no conflicts (the second merge fast-forwards or auto-merges cleanly).
- **Any output** → those files need either sequential implementation (one branch waits for the other to merge, then rebases) or a designed merge strategy (e.g., reserved sections, separate config files).

`git diff main...branch --name-only` produces files changed on the branch since it diverged from `main`. `comm -12` reports common lines between two sorted inputs — i.e., files touched by BOTH branches.

## When This Applies

- Two or more independently-developed branches based on the same parent
- Branches are short-lived (no overlapping rebase history)
- The branches' work is conceptually independent (the parallelism is a real optimization, not forced)

## When This Does NOT Apply

- Branches have already had `main` merged into them (their diff base is different — the comm result will under-report overlap)
- One branch was rebased on top of another mid-flight (diff is no longer against shared parent)
- The "files" are auto-generated (e.g., compile-output snapshots), where same-file overlap is expected and the right strategy is supersedence, not merge

## Grounding

KF-core loop-engineering integration (2026-06-13/14) used this check before parallelizing SPEC 4 + SPEC 5 in separate worktrees. The check returned empty — zero file overlap — and both branches landed sequentially via `git merge --no-ff` with no conflict-resolution work. The same check correctly flagged SPEC 1's later overlap with SPEC 5's earlier work on `kf-compile.py` (single-line argparse list), which the team then accepted as a trivial merge.

## Source Context

Codifies a one-liner pre-parallelize gate that replaces ad-hoc judgment about whether parallel work will conflict. The cost of running the check is ~100ms; the cost of mis-judging is a multi-hour conflict-resolution session.
