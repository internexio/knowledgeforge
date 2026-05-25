---
title: Beads multi-database working-directory gotcha — same project, two .beads/ databases
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-23
tags: beads, bd, workflow, infrastructure, gotcha, multi-project-layout
domain: infrastructure
topic: workflow-discipline
related_entries:
  - diagnostics/2026-05-18_bd-title-length-utf8-bytes-not-codepoints.md
  - infrastructure/2026-05-19_git-dash-c-cwd-stability-claude-code-bash.md
  - migrations/2026-05-21_cross-db-bead-migration-external-ref-provenance.md
---

# Beads Multi-Database Working-Directory Gotcha

## Symptom

`bd close <id>` returns `Error: resolving ID <id>: no issue found matching "<id>"` even though `bd ready` previously listed that exact ID, and the create command appeared to succeed.

## Root Cause

`bd` selects its database based on the nearest `.beads/` directory walking up from the current working directory. In multi-project layouts where a parent directory and a child subdirectory each have their own `.beads/` (e.g. `~/Scripts/[project]/.beads/` and `~/Scripts/[project]/cos/.beads/`), running `bd create` from one cwd and `bd close` from the other writes to and reads from two different databases. The IDs from one DB are invisible from the other.

## Reproduction (Verified 2026-05-23)

```bash
cd ~/Scripts/[project]
bd create --title="SEO Pillar 3..." ...       # creates cos-7zv in [project]/.beads/

cd ~/Scripts/[project]/cos                       # now in a different .beads/ root
bd close cos-7zv                                # → "no issue found matching cos-7zv"
bd list --status=open                          # shows DIFFERENT issues entirely (cos-9m3, cos-5il, ...)
```

The IDs in `[project]/.beads/` and `[project]/cos/.beads/` can collide by chance (both use the `cos-` prefix and similar slugs) which makes the bug harder to spot.

## Why This Doesn't Show Up Until You Hit It

`bd ready` and `bd list` always show "real" results from whatever DB they're invoked against. There's no error or warning that you're talking to a different DB than you were five minutes ago — the IDs just silently don't match. The mental model failure is treating `bd` like a globally-scoped tool when it's actually per-database, like git.

## When This Applies

- Any repository nested inside another tracked directory (a monorepo wrapper with project subdirs, e.g. [project]/ wrapping cos/, cos-platform/, comms/, etc.)
- Any session that `cd`s between project root and a subproject for git operations
- Any agent or hook that runs `bd` commands without setting cwd explicitly

## How To Avoid

1. **Pin the cwd before any `bd` invocation.** Either always run from the project root that owns the canonical `.beads/`, or always run from the subproject. Pick one and stick to it for the whole session.
2. **Verify on first `bd` call of the session** by running `bd list --status=open | head -3` and confirming the IDs look familiar. If you don't recognize anything, you may be in the wrong database.
3. **When `bd close` fails with "no issue found,"** the first hypothesis should be a database mismatch, not a typo or stale ID. Check with `find <project-root> -type d -name .beads` to see how many databases exist.

## How To Recover

Once you identify which DB the issue lives in:
```bash
cd <directory-containing-the-correct-.beads/parent>
bd close <id> --reason="..."
```

## Comparison to Similar Patterns

Comparable to running `git` commands from outside a repo, but worse — `git` errors loudly with "not a git repository," while `bd` happily operates on whatever DB it can find walking up the tree. The git equivalent, "git -C /abs/path for CWD-unstable Claude Code Bash harness" (2026-05-19), addresses the same defense principle: explicit path specification prevents silent database/repo mismatch.

## When This Does NOT Apply

- Single-project beads databases with no nesting (monorepos with a flat beads structure avoid this)
- Tools that enforce cwd before any `bd` call (CI pipelines with explicit directory guards)
- Manual issue creation via UI (no cwd ambiguity)

## Grounding Evidence

- **2026-05-23 [project] session:** Filed 4 SEO pillar issues from `[project]/` parent directory (cos-7zv, cos-7zw, cos-7zx, cos-7zy), then `cd`ed to `cos/` subdir for git ops
- Attempted `bd close cos-7zv` from subdir → "no issue found"
- Ran `find ~/Scripts/[project] -name .beads -type d` → revealed both `[project]/.beads/` and `[project]/cos/.beads/`
- Returned to `[project]/` parent and `bd close cos-7zv` succeeded
- Hypothesis verified: two separate `.beads/` databases in same project tree

## Source Context

Encountered live in 2026-05-23 [project] session (cos-seo-pillar-repositioning) while filing 4 SEO pillar issues from `[project]/`, then `cd`ing to `cos/` for git operations to commit the homepage SEO repositioning, then trying to close cos-7zv from the subdir. Close failed with "no issue found." Returning to `[project]/` cwd let the close succeed.
