---
title: Bead-left-open anti-pattern — verify implementation state before starting bead work
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: stable
importance: 4
pinned: false
created: 2026-08-16
domain: methodologies
topic: bead-triage-workflow
tags: accretion, quality-gate, temporal, bead-management, silent-completion, anti-rework
related_entries:
  - methodologies/2026-06-10_verify-premise-before-defensive-bead.md
  - methodologies/2026-06-09_read-bead-status-before-claiming-verify-explicit-deferral.md
  - methodologies/2026-05-26_deterministic-scan-before-claiming-refactor-audit-beads.md
  - orchestration/2026-05-30_bead-tracker-workflow-pipeline-triage-decisions-build-deploy.md
---

# Bead-Left-Open Anti-Pattern — Verify Implementation State Before Starting Bead Work

## Problem: Implementation-Complete Beads That Were Never Closed

When picking up an old bead and the description says "add X to module Y", the natural response is to start implementing. But when a bead was created months earlier and priority was recently escalated, the work may have already landed in commits months ago — the module versions bumped, the code artifact created and deployed, the compiled output updated — yet the bead was never closed.

Starting implementation without verifying current state wastes a session and risks introducing duplicate or conflicting changes.

## Verification Protocol (Before Writing Any Code for an Old Bead)

For each item in the bead's work scope, check whether it already exists. Run these checks in order:

### 1. Module Version Check
Does the module changelog mention this bead's driver or the feature described?

```bash
grep -n "M22\|core-acu\|wiki search\|Phase 2" modules/22_Knowledge_Accretion.md
```

The module version should reflect the bead's work. If the version is higher than it was when the bead was created, the feature may already be in.

### 2. Implementation Files Check
Does the target file/function already exist?

```bash
ls ~/.claude/hooks/kf_wiki_search.py           # direct file check
grep -n "def wiki_search\|class WikiSearcher" modules/*.md  # search across files
```

Look for the exact artifact described in the bead — function signature, file location, or class definition.

### 3. Compiled Output Check
Run the compiler with a diff flag to see if any changes are needed:

```bash
python3 compiler/kf-compile.py --diff --target claude-code
```

If the target is already current, zero changes will appear. No changes = work is already compiled.

### 4. Git Log Check
Scan for commits that mention the bead ID or the described feature:

```bash
git log --oneline | grep -i "core-acu\|Phase 2\|score fusion"
git log --all --grep="kf_wiki_search" --oneline
```

If commits landed weeks ago, the work is done. Cross-check commit dates against when the bead was created.

## Decision Point

If all scope items check out as already done:

- **Close the bead immediately** with a note explaining when and where the work landed
- **Do not re-implement** — rewriting code that's already shipping introduces conflicts and confusion
- **Document the closure** for future readers: "Implemented in commit X (2026-07-08), compiled to CC at Y (2026-07-09). Closing as completed."

If checks are inconclusive or suggest partial completion:

- **File a follow-up bead** to close out any gaps
- **Do not assume partial = start from scratch** — use the existing work as a base

## When It Applies

- Bead was created months ago and priority was recently escalated (likely signaling a stale backlog sweep)
- Bead description says "add X to Y" where X is a specific, concrete code artifact (function, file, module section)
- The module version in the spec is higher than when the bead was created
- No recent activity on the bead (closed_at or updated_at are ancient; no comments in the last 60 days)

## When It Does NOT Apply

- Bead was created in the current session or within the last 7 days (can't have been silently completed)
- Bead describes infrastructure/CI work with no code artifacts to check (no versioning signal)
- Bead is explicitly marked "not started" or "design only" in its notes (covered by separate rule: 2026-06-09 entry)
- Bead's scope is behavioral/testing (no compiled artifact to check)

## Anti-Pattern (What NOT to Do)

Do NOT:

- Run `bd update <id> --claim` and start writing code without first running the verification steps above
- Assume the bead is incomplete just because it's still open
- Begin a code diff without checking the git log first
- Implement a feature twice under different naming

The 5-minute verification cost avoids a wasted session, merge conflicts, and code-review friction.

## Observed Context

**core-acu (M22 Phase 2):** kf_wiki_search.py created 2026-07-08, kf-route.py extended, mempalace-wiki-mine.py updated. Module 22 bumped to v7.4.0 on 2026-07-09. All work visible in git log with dates and commit messages. Bead remained open until 2026-08-16 when this pattern was discovered.

**core-xaq (M07 comms variant):** Comms delegation added at M07 v7.4 (2026-07-04 era), with kf:if cos gating at v7.6.0. Git log shows commits from early July. Bead remained open until 2026-08-16.

In both cases, the work had shipped weeks earlier. Starting implementation would have meant:
1. Duplicating code changes already in production
2. Creating merge conflicts with the existing commits
3. Wasting 2-4 hours of session time on work already complete

The verification protocol caught this in under 5 minutes per bead.

## Related Behavioral Rules

This entry is part of a family of **verification-before-action** rules:

- **[[2026-06-10_verify-premise-before-defensive-bead]]** — verify the problem is real when CREATING defensive beads
- **[[2026-06-09_read-bead-status-before-claiming-verify-explicit-deferral]]** — check for deferred-status flags before CONSUMING shelved beads
- **[[2026-05-26_deterministic-scan-before-claiming-refactor-audit-beads]]** — verify the audit claim against code before filing refactor beads

This entry covers the **CONSUMING** phase when the work is already done but the bead wasn't closed — the complement to the "was this already done" check that applies at bead-creation time.

## Source Context

Session: knowledgeforge-ci-cleanup-2026-08-16. Two stale beads picked up during a backlog sweep yielded no work — the features had landed weeks earlier but the beads remained open. This pattern is reusable whenever a bead's age is greater than the staleness risk threshold for its domain.
