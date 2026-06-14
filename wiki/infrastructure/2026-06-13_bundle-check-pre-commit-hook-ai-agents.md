---
title: Bundle-check pre-commit hook — defense against AI agents doing broad git add
source_mode: direct
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-06-13
domain: infrastructure
topic: deployment
tags: deployment, quality-gate, hallucination-risk
related_entries: []
---

# Bundle-check pre-commit hook — defense against AI agents doing broad git add

## The Problem

AI coding agents (Claude Code, others) occasionally execute broad `git add` operations — `git add -A`, `git add .`, or `git commit -a` — even when project guardrails forbid it. When the working tree contains in-flight work from unrelated subsystems, the broad-add bundles them into a single commit, which:

- Breaks attribution (work from subsystem A and subsystem B appear under one commit)
- Pollutes the commit history (unrelated changes grouped together)
- Complicates blame/bisect workflows
- Violates subsystem-level commit discipline

This is especially problematic in multi-subsystem projects where focused commits per subsystem are a intentional structure.

## The Pattern

A lightweight pre-commit hook can prevent bundled commits by enforcing a two-condition gate:

**Block when (staged-file-count > threshold) AND (top-level-subsystem-count > 1)**

The dual condition avoids false positives:
- Many files in one subsystem → allowed (legitimate cross-cutting refactor within one area)
- Few files across subsystems → allowed (intentional small cross-subsystem change)
- Many files spread across subsystems → **blocked** (signature of unintended broad-add)

## Concrete Implementation

Hook installed at `scripts/git-hooks/pre-commit` in the [project] project (2026-06-13, commit db1daab):

```bash
#!/bin/bash
set -e

BUNDLE_THRESHOLD="${[project]_BUNDLE_THRESHOLD:-5}"
AUDIT_LOG="$HOME/agent-workflow/git-commit-audit.log"

STAGED=$(git diff --cached --name-only --diff-filter=ACMRTD 2>/dev/null || true)
if [ -n "$STAGED" ]; then
    COUNT=$(printf '%s\n' "$STAGED" | grep -c . || true)
    SUBSYSTEMS=$(printf '%s\n' "$STAGED" | awk -F'/' 'NF>0 {print $1}' | sort -u)
    SUB_COUNT=$(printf '%s\n' "$SUBSYSTEMS" | grep -c . || true)

    # Always audit (Layer B for free)
    {
        printf '%s\tcount=%d\tsubsystems=%d\toverride=%s\tbranch=%s\n' \
            "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$COUNT" "$SUB_COUNT" \
            "${[project]_ALLOW_BUNDLE:-0}" \
            "$(git rev-parse --abbrev-ref HEAD)"
    } >> "$AUDIT_LOG" 2>/dev/null || true

    # Block when both thresholds tripped, unless override
    if [ "${[project]_ALLOW_BUNDLE:-0}" != "1" ] \
       && [ "$COUNT" -gt "$BUNDLE_THRESHOLD" ] \
       && [ "$SUB_COUNT" -gt 1 ]; then
        cat >&2 <<EOF
[pre-commit] BLOCKED: bundle-check failed
  Staged files:     $COUNT  (threshold: $BUNDLE_THRESHOLD)
  Top-level dirs:   $SUB_COUNT
Recovery:
  1. Unstage unintended files:  git reset HEAD -- <path>
  2. Split into focused commits.
  3. If legitimate cross-subsystem: [project]_ALLOW_BUNDLE=1 git commit ...
EOF
        exit 1
    fi
fi
```

## Installation Pattern

A pre-commit hook only works if installed on every clone. Pair the hook with an idempotent installer that runs during routine background sync:

```bash
#!/bin/bash
# scripts/install-git-hooks.sh — idempotent

TARGET="scripts/git-hooks"
CURRENT="$(git config --local --get core.hooksPath 2>/dev/null || true)"
[ "$CURRENT" = "$TARGET" ] && exit 0

git config --local core.hooksPath "$TARGET"
chmod +x "$TARGET"/*
```

Call this installer from any periodic script the project already runs (e.g., beads-sync, build hooks, nightly jobs). The hook self-installs within one sync cycle of a pull.

## Layer B: Audit Log (Free)

Every commit attempt — passed, blocked, or overridden — appends a line to an audit log at `$HOME/agent-workflow/git-commit-audit.log`:

```
2026-06-13T21:30:15Z  count=7  subsystems=2  override=0  branch=master
2026-06-13T21:32:01Z  count=3  subsystems=1  override=0  branch=master
2026-06-13T21:35:42Z  count=12  subsystems=3  override=1  branch=feature-x
```

The audit log provides:
- **Defense:** visible history of what was blocked and when
- **Observability:** which commits were overridden (and by whom, if logs are tied to user context)
- **Calibration data:** count distribution over time to refine thresholds

## Override Mechanism

The hook must have an explicit, logged override for legitimate cross-subsystem commits (e.g., coordinated refactors affecting multiple subsystems):

```bash
[project]_ALLOW_BUNDLE=1 git commit ...
```

Without the override, users will eventually `git commit --no-verify` to bypass the hook entirely. The override preserves the audit trail and allows intentional bundled commits when justified.

## Delegation to Existing Hooks

If the project already has per-subsystem hooks (e.g., beads' `.beads/hooks/pre-commit` for db↔jsonl sync), use `exec` to delegate at the end:

```bash
# In scripts/git-hooks/pre-commit, at the end:
if [ -x "$REPO_ROOT/.beads/hooks/pre-commit" ]; then
    exec "$REPO_ROOT/.beads/hooks/pre-commit" "$@"
fi
exit 0
```

The `exec` replaces the current process — the existing hook's exit code becomes the final result, and both hooks' logic runs correctly.

## When This Applies

- Multi-subsystem repositories where the top level contains distinct directory structures (e.g., `iteration_loop/`, `scripts/`, `mayor/`)
- Projects where AI coding agents make commits
- Repos with frequent in-flight work from different subsystems that overlaps chronologically
- Any repo where commit attribution and subsystem-level history matter (beads/issue tracking, release notes, compliance audits)

## When This Does NOT Apply

- Single-purpose repos with no meaningful subsystem boundaries (all code in `src/lib/` or similar)
- Repos that genuinely execute many cross-subsystem commits (then raise the threshold, or recognize the pattern doesn't fit the project's structure)
- Commits via `--no-verify` (the hook is bypassed intentionally; this is the acknowledged escape hatch)

## Threshold Tuning

Default thresholds (`COUNT > 5`, `SUBSYSTEMS > 1`) are a starting point. Use the audit log to calibrate:

1. Run for ~1 week of normal development
2. Count blocks vs overrides
3. If blocks are mostly false positives, raise `BUNDLE_THRESHOLD`
4. If blocks never fire, lower the threshold or consider the pattern inapplicable

Example calibration sequence:
- Week 1: `COUNT > 5, SUB_COUNT > 1` → too aggressive (blocks legitimate 8-file refactor in 2 subsystems)
- Week 2: `COUNT > 10, SUB_COUNT > 1` → too permissive (lets through 12-file bundle)
- Week 3: `COUNT > 8, SUB_COUNT > 2` → sweet spot (blocks obvious bundles, allows intentional cross-subsystem)

## Related Entries

- **Dual opt-in pattern for elevated subprocess capability** (`infrastructure/2026-06-10_dual-opt-in-pattern-elevated-subprocess-capability.md`) — Similar two-condition gate for CI capability elevation
- **Idempotent watchdog producer pattern** (`infrastructure/2026-06-14_idempotent-watchdog-producer-pattern.md`) — Audit-log and self-healing patterns that pair with this hook
- **Commit-trailer fingerprinting** (sibling RCA finding from [project]-8vm7) — Identifies whether a problematic commit came from a Happy session vs manual CLI, narrowing RCA scope

## Source Context

Discovered during [project]-8vm7 RCA (2026-06-13) when a Claude Code session executed `git add -A` bundling 7 files across 2 unrelated subsystems (iteration_loop/ and scripts/). The unintended commit (f4dc47e) polluted the log and broke subsystem-level blame tracking. Post-incident, the hook was implemented and tested: staged 7 files across 2 subsystems, ran `git commit`, hook blocked with the expected error. No commit was created. This pattern is transferable to any multi-subsystem repo where commit discipline matters.
