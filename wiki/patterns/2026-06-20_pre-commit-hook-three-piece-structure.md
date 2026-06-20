---
title: Pre-commit hook three-piece structure — standalone checker + thin wrapper + manual installer
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.70
staleness_risk: stable
importance: 3
pinned: false
created: 2026-06-20
domain: patterns
topic: validation
tags: filesystem, deployment, empirical
related_entries:
  - infrastructure/2026-06-13_bundle-check-pre-commit-hook-ai-agents.md
  - infrastructure/2026-05-25_hook-installed-vs-source-drift-direct-edits.md
---

# Pre-commit hook three-piece structure

## The pattern
Project-level pre-commit lint checks benefit from a three-piece structure rather than a single monolithic hook script.

### Piece 1: Standalone checker script
Path convention: `scripts/check-<concern>.py`.
- Pure-stdlib (zero deps when the concern allows).
- Reads files passed as args; defaults to "all in-scope files" when no args.
- Exits 0 clean, 1 on issue.
- Has its own header docstring explaining the concern, exit codes, and standalone usage.
- Reusable from CI, manual invocation, IDE integration — anywhere that wants the check without git context.

### Piece 2: Thin shell wrapper at `scripts/git-hooks/<HOOK_NAME>`
- Inspects git state (`git diff --cached --name-only --diff-filter=ACM`) to find in-scope staged files.
- If no in-scope files staged → `exit 0` (no-op; zero overhead on unrelated commits).
- Otherwise → `exec python3 "$REPO_ROOT/scripts/check-<concern>.py" $staged`.
- Small enough (5–15 lines) to read at a glance.

### Piece 3: Manual installer at `scripts/install-git-hooks.sh`
- Copies every file in `scripts/git-hooks/` into `.git/hooks/` and `chmod +x`.
- Has `--force` flag to overwrite divergent existing hooks.
- Run once per fresh clone; not auto-run by git.

## Why three pieces (not one)

| Concern | Single monolithic hook | Three-piece |
|---|---|---|
| Reusable from CI / manual | NO — requires git context | YES — standalone script has no git deps |
| No-op overhead on unrelated commits | Often runs anyway | Wrapper short-circuits before invoking checker |
| Survives `git init --separate-git-dir` and unusual `.git` layouts | Tricky | Wrapper isolates git probe; checker doesn't care |
| Discoverable in `scripts/` | Hidden in `.git/hooks/` | Lives in tracked tree; `.git/hooks/` is just a deployment target |

## When this applies
- Project has lint-style validation that should also run in CI and on demand.
- Check has a clear "in-scope file pattern" (e.g. `modules/*.md`, `*.py`, etc.) that lets the wrapper short-circuit cheaply.
- Team has multiple devs / agents who clone fresh repos and need an explicit install step.

## When it does NOT apply
- Check is so tightly coupled to git state that standalone invocation makes no sense (e.g., "did you sign your commit?" — only meaningful at commit time).
- Single-purpose `commit-msg` linter where the message is the only input — no in-scope file pattern to short-circuit on.

## Concrete grounding
knowledgeforge-core commit `98c77d0` (closes bead `-3kk`):
- `scripts/check-identity-drift.py` — standalone, detects M00-style "You are the KnowledgeForge X.Y.Z" identity strings drifting from each module's own `version:` field.
- `scripts/git-hooks/pre-commit` — wrapper, no-op when no `modules/*.md` staged.
- `scripts/install-git-hooks.sh` — installer with `--force`.
- Verified end-to-end: clean state passes all 26 modules; two synthetic drift cases (identity-line and title-line) correctly block.
