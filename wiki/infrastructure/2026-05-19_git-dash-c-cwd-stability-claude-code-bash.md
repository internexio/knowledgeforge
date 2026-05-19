---
title: "git -C /abs/path for CWD-unstable Claude Code Bash harness"
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-19
tags: infrastructure, git, claude-code, bash-harness, cwd-stability, defensive-coding
related_entries: ["infrastructure/2026-05-13_launchd-cwd-trap-relative-tool-lookups.md"]
---

# git -C /abs/path for CWD-Unstable Claude Code Bash Harness

## The Problem

The Claude Code Bash tool does not reliably preserve working directory between invocations. A sequence like:

```bash
cd /path/to/repo && git push origin master
```

does not guarantee that the next Bash call runs from `/path/to/repo`. The harness frequently lands in a parent directory—often `~/Scripts/[project]` instead of `~/Scripts/[project]/cos`—causing subsequent git operations to fail or succeed **against the wrong repository**.

## Symptom Cascade

### Immediate Failure (Easier to Catch)

```bash
$ git push origin master
fatal: 'origin' does not appear to be a git repository
fatal: Could not read from remote repository.
```

This occurs because `git` walked up from CWD to find the first `.git/`, which was `~/Scripts/.git` (a parent directory that may be git-initialized but has no `origin` remote), not the intended `~/Scripts/[project]/cos/.git`.

### Silent Failure (Worse)

When the parent directory is a valid git repo with an `origin` remote (or is a monorepo wrapper), the operation succeeds **silently against the wrong tree**. You commit, push, or reset changes that were meant for one project to another project entirely — without any warning.

Example: attempting to push to `[project]/cos` but the bash harness lands in `~/Scripts`, which is itself a git-initialized directory containing dozens of project repos. The push succeeds against `~/Scripts`, corrupting the parent-level history.

## Root Cause

The Claude Code Bash execution model does not carry CWD state between tool invocations in a way that multi-step git workflows rely on. Each bash call is independent; a `cd` in one call does not affect the starting directory of the next call. Combined with a shallow check for git repos (git walks up from CWD), this creates a footgun.

## Defense: Always Use `git -C <absolute-path>`

The `-C <path>` flag forces git to operate as if invoked from that directory, bypassing any CWD drift:

```bash
git -C ~/Scripts/[project]/cos status
git -C ~/Scripts/[project]/cos add file.html
git -C ~/Scripts/[project]/cos commit -m "Update content"
git -C ~/Scripts/[project]/cos push origin master
```

No `cd` required. No CWD state carried between calls. No ambiguity about which `.git` git will find.

## Verification Idiom (Pre-Flight Audit)

Before staging anything, verify that git is operating on the intended repository:

```bash
git -C ~/Scripts/[project]/cos rev-parse --show-toplevel
# Expected output: ~/Scripts/[project]/cos

# If output differs, abort — you would have committed to the wrong repo.
```

This is a read-only check that is always safe to run. Make it a habit before any destructive operation.

## Coverage

Apply `-C` to all destructive git operations:
- `add`
- `commit`
- `push`
- `reset`
- `clean`
- `checkout`
- `rm`

Read-only operations (`status`, `log`, `diff`, `rev-parse`) still benefit from `-C` because their output will describe the correct repository, making debugging easier and avoiding the silent-failure trap.

## When This Applies

- Multi-step git workflows in Claude Code where you script a sequence of commits/pushes
- Working in a monorepo or nested-repo structure (e.g., `~/Scripts/` contains dozens of project repos, many of which are themselves git repositories)
- Any destructive git operation where you cannot afford to corrupt the wrong repository's history
- Defensive coding posture: always use `-C` in scripts, even when you "know" the CWD is stable

## When This Does NOT Apply

- Single, one-off `git` commands run interactively in a properly-positioned terminal (though `-C` doesn't hurt)
- Contexts where absolute paths are not available (rare for Claude Code; `~/Scripts/...` paths are always deterministic)

## Related Diagnostics

**CLAUDE.md guidance:** The global instruction set mentions `git rev-parse --git-dir` as an audit pattern. That is the underlying defense mechanism. The `-C` flag is the **proactive pattern**; `rev-parse` is the **reactive audit** after failure.

**launchd CWD trap (2026-05-13):** A related but distinct issue where launchd sets CWD=/; this entry addresses the Claude Code harness equivalent (CWD drift between invocations, not a fixed bad value).

## Concrete Example: COS Workflow

Typical sequence in [project]:

```bash
# Session 1: Check status
git -C ~/Scripts/[project]/cos status

# Session 2: Make changes and stage (separate bash invocation)
git -C ~/Scripts/[project]/cos add cos/backend/app.py

# Session 3: Commit (separate bash invocation)
git -C ~/Scripts/[project]/cos commit -m "Fix auth flow"

# Session 4: Verify target (safety check)
git -C ~/Scripts/[project]/cos rev-parse --show-toplevel
# Output: ~/Scripts/[project]/cos ✓

# Session 5: Push
git -C ~/Scripts/[project]/cos push origin master
```

Each bash call is independent; `-C` ensures all four operations target the same `.git` directory, even if the harness lands in different starting directories.

## Reuse Context

This applies to **every multi-repo working tree**. The `~/Scripts/` directory contains dozens of project repos; `knowledgeforge-core`, `[project]`, `riptide`, `reddit-scan`, and others all coexist under a parent that is itself sometimes git-tracked. The `-C` pattern is one of the highest-frequency Claude Code defensive patterns.

## Source Context

Emerged from live observation of CWD drift in Claude Code bash execution model during multi-step git workflows. The pattern was formalized as a knowledge entry to prevent silent repository corruption in future work.
