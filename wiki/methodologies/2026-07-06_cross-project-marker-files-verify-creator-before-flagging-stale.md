---
title: Cross-project marker files — verify the creator lives elsewhere before flagging an empty repo-root file as stale
source_mode: critic
source_session: redacted
source_fingerprint: SR-sem-tools-20260704 / SURFACE_MAP.md line 149 / packet 2026-07-04_1720.md line 164 / corrective research artifact art_ed3e57f4
novelty_type: new_pattern
grounding_score: 0.80
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-06
domain: methodologies
topic: verification
tags: code-audit, state-report, defensive-bead, verify-premise, cross-project, marker-files, false-positive
related_entries:
  - methodologies/2026-06-10_verify-premise-before-defensive-bead.md
  - methodologies/2026-06-18_cross-scope-search-blindness-operator-insistence-as-broaden-signal.md
  - methodologies/2026-05-26_deterministic-scan-before-claiming-refactor-audit-beads.md
  - methodologies/2026-05-27_read-ground-truth-not-surface-signals-universal-antipattern.md
---

# Cross-Project Marker Files — Verify the Creator Lives Elsewhere Before Flagging an Empty Repo-Root File as Stale

## The Pattern

Some tools deliberately create empty (or near-empty) files at the root of *other* projects as signaling markers — the file's **presence** (not its content) is what matters. The creator lives in a sibling project. Grepping only within the repo where the file appears returns zero references; from inside that repo the marker looks like stale garbage. Flagging it "KILL / purpose unclear" without a cross-project search will send a false-positive recommendation upstream — into a STATE_REPORT, SURFACE_MAP entry, code-audit finding, or "chore: delete stale file" PR.

## Concrete Case (Grounding, 2026-07-04)

`.gastown-ignore` (0 bytes, untracked) appeared at the root of `sem-tools`. Nothing in sem-tools referenced it. A STATE_REPORT (`SR-sem-tools-20260704`) was filed with the Stale-table verdict:

> `KILL — empty file at repo root, purpose unclear`

cos-manager (L2) ingested that verdict into `state/SURFACE_MAP.md` line 149 and packet `2026-07-04_1720.md` line 164. A parallel STATE_REPORT from a sibling repo (`semalytics-gtm`) also listed the file as untracked, showing the marker appears system-wide — a signal that should have been caught before recommending removal.

Cross-project grep after the fact revealed the creator: `~/Scripts/[project]/scripts/happy-enable.sh` lines 89–99. The script writes `.gastown-ignore` (empty) into any repo where Happy is enabled, to *prevent* GasTown from wedging Happy's first-boot session in that repo. Deleting the marker re-enables the wedge.

A corrective research artifact (`art_ed3e57f4`) had to be pushed to `cos-advisor` to walk back the SURFACE_MAP verdict. Real recovery cost, from a false positive that a one-command sweep would have prevented.

## The Rule (Deterministic-First)

For any empty or near-empty file at repo root whose purpose is NOT obvious from the repo itself:

```bash
grep -rn "<filename>" ~/Scripts/ --include="*.sh" --include="*.py" \
  --include="*.md" --include="*.yaml" --include="*.yml" --include="*.json"
```

Run this BEFORE:
- recommending removal
- filing a KILL verdict in a STATE_REPORT
- opening a "chore: delete stale file" PR
- listing the file in a Stale table with a purge recommendation

## When This Applies

- STATE_REPORT / SURFACE_MAP / code-audit contexts (any output that flows upstream to a coordinator that trusts the finding)
- Any empty or near-empty untracked file that surfaces in `git status`
- Files with unusual extensions or names that don't match any in-repo convention
- Files that a sibling repo's STATE_REPORT ALSO lists — a strong signal the creator is cross-cutting

## When This Does NOT Apply

- Files clearly authored by a known in-repo tool (build outputs, cache directories, IDE state) — those have obvious creators
- Files inside `.gitignore`d directories that `git status` wouldn't show anyway
- One-off developer scratch files in a lone-developer repo (no cross-project surface exists)

## Sibling Markers with the Same "Purpose Lives Elsewhere" Property (Verified 2026-07-04)

- `.kf/` — KnowledgeForge local runtime state (created by KF harness in the enclosing project)
- `scripts/happy-watchdog.sh` — Happy machine-specific infrastructure, often gitignored in some repos and tracked in others
- `.claude/worktrees/` — Claude Code Agent-tool worktree runtime (agents create these; they're not project artifacts)

## Underlying Meta-Rule

This entry extends `verify-premise-before-defensive-bead` (in `~/.claude/rules/`) with a specific case pattern. That rule says "read the FULL relevant function before filing a defensive bead." This entry says the equivalent for a *file*: "check the FULL relevant repo tree — including sibling projects — before recommending removal." Same shape: don't file a defensive/corrective recommendation until you've searched the whole surface the artifact could be created by.

## Why This Matters Beyond One False Positive

Coordinator systems (cos-manager L2, KF's routing layer, similar multi-repo orchestrators) explicitly trust incoming STATE_REPORTs and don't re-verify the findings — that's the whole design of L2/L3 delegation. A false-positive KILL in a STATE_REPORT can propagate into a downstream automated cleanup, a real deletion, or a mis-scoped bead. The recovery mechanism (corrective research artifact) works, but it's a papercut every time.

## Composes With

- **[[2026-06-10_verify-premise-before-defensive-bead]]** — parent rule; same shape applied to code/function scope rather than file/repo scope.
- **[[2026-06-18_cross-scope-search-blindness-operator-insistence-as-broaden-signal]]** — sibling pattern for search-scope failures; both address confident-but-wrong negatives produced by too-narrow scope.
- **[[2026-05-26_deterministic-scan-before-claiming-refactor-audit-beads]]** — same "verify before you claim" family; that entry covers refactor/audit beads.
- **[[2026-05-27_read-ground-truth-not-surface-signals-universal-antipattern]]** — the universal shape: an empty file's meaning is not on its filesystem surface; ground truth lives in the creator elsewhere.
