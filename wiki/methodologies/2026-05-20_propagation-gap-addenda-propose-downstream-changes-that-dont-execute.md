---
title: Propagation-gap pattern — addenda propose downstream changes that don't get executed
source_mode: critic
novelty_type: reusable_diagnostic
grounding_score: 0.8
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-20
domain: methodologies
topic: propagation-discipline
tags: methodology, propagation-discipline, multi-file-engineering, critic-patterns, recurrent-anti-pattern, quality-gate
related_entries:
  - patterns/2026-05-18_markdown-binary-artifact-drift-independent-editing.md
  - infrastructure/2026-05-12_vendoring-drift-detection.md
  - methodologies/2026-05-13_verify-audit-claims-before-designing-fix.md
---

# Propagation-gap pattern — addenda propose downstream changes that don't get executed

## The Pattern

When a research or analysis artifact proposes a change to a downstream build artifact (e.g., "add these 4 keywords to build_sheet.csv"), the proposal is recorded in the artifact but the execution often does not follow. Future readers of the proposing artifact assume the downstream is current. The build state silently drifts from the documented state.

**Cognitive mechanism:** Proposing the change in the artifact *feels like* "doing" the change. The cognitive close happens at the proposal step, not the execution step. The downstream file (CSV, config, code) is not in the same edit session as the artifact. Switching context to the downstream file is a separate action that's easy to defer and easy to forget.

## Recurrent Confirmation

Flagged in two separate adversarial-critic passes on the same project (5SB Paid Ads) within 30 days:

1. **First pass (critic-1):** A research artifact recorded a keyword research finding but the change wasn't pushed to the build sheet. The findings were accurate; the propagation was incomplete.

2. **Second pass (critic-2):** An addendum proposed adding 4 keywords. Only 1 made it to the build sheet, and that one was already there pre-addendum. Effectively 0-of-4 new keywords propagated.

Both occurrences were in multi-file engineering workflows where research → planning → execution span separate directories and file types.

## When This Applies

- Any analysis artifact that recommends changes to other artifacts (build sheets, configs, code, schemas)
- Any time the proposing artifact and the target artifact are in different files
- Especially in multi-file engineering work spanning research → planning → execution → ops layers
- When the proposing artifact is read-only or lower-frequency compared to the target

## When This Does NOT Apply

- Purely descriptive analysis with no downstream changes proposed
- Single-file changes where the artifact IS the target file (propagation is trivially closed by saving)
- Systems where analysis and build artifacts are generated together (e.g., CI pipelines that rebuild from a single source)

## The Fix — Propagation Checklist as a Load-Bearing Artifact Mechanic

Any addendum or research artifact that proposes a downstream file change MUST include a propagation checklist. The checklist is the source of truth for "was this propagated?"

### Template

```
## Propagation checklist for this change

- [ ] `path/to/file1.csv` — add row X, Y, Z
- [ ] `path/to/file2.md` — update count from N to N+3
- [ ] `path/to/file3.md` — flag in decision log
```

### Discipline Rule

The closing decision-log entry for the change is not written until all checklist items are `[x]`. The checkbox state is the source of truth for "did this change actually propagate?"

This prevents the false-close problem: the analyst writes the research artifact (cognitive close ✓), but the build artifact hasn't been touched yet. The checklist forces a second, explicit, file-by-file close.

### Optional Automation (Low Investment, High Catch Rate)

1. **Linter for un-propagated items:** Parse each research artifact's checklist. Grep the target files for the proposed content. Flag items that didn't make it. Run before closing the decision log.

2. **Diff-against-target for quantitative changes:** For proposals like "add 4 keywords," count keywords in the target file before and after. Report propagation rate.

## Root Cause

**False locality:** Editors interact with multiple files that *appear* independent because they're separate objects on disk. Without an explicit propagation checkpoint, there's no enforcement mechanism. The project has implicitly adopted a "optimistic" stance: "the analyst will propagate it." This almost always fails under time pressure.

## Operational Checklist

Before closing a research/analysis artifact that proposes downstream changes:

- [ ] Are there downstream changes proposed?
  - If NO: skip the rest of this checklist.
  - If YES: continue.

- [ ] Does the artifact include a propagation checklist with `[ ]` or `[x]` items?
  - If NO: add one before marking the artifact complete.
  - If YES: continue.

- [ ] Are all checklist items marked `[x]`?
  - If NO: complete the propagations before closing, or defer to a follow-up bead.
  - If YES: proceed to close.

- [ ] If this artifact is part of a decision log, has the decision-log entry been written?
  - If NO: write it now (after propagations are done).
  - If YES: verify the decision-log entry links to or references this artifact + its propagation checklist.

## Adjacent Pattern — Load-Bearing Assumption

A related pattern from the same critic-pass series: architectural assumptions that didn't survive verification (e.g., a platform deprecation oversight in the same project). Both propagation-gap and load-bearing-assumption share a structure:

- **Claim made in artifact** → **Reality diverges** → **Drift goes uncaught until adversarial review**

The fixes differ:
- **Propagation gap** → Process discipline (propagation checklist)
- **Load-bearing assumption** → Verification discipline (re-check platform mechanics at implementation time, don't trust analyst notes from earlier in the session)

## Source Context

Observed during 5sb-paid-ads-ch1-propagation-gap-2026-05-20 (critic pass #2). A research artifact proposed adding 4 keywords to the build sheet after analyzing gaps in the current keyword portfolio. The artifact was well-grounded (grounding 0.8), but the execution propagation was incomplete. Follow-up critic review surfaced that only 1 of the 4 keywords had made it to the build sheet, and that one pre-existed.

This recurrence (second flag within 30 days on the same project) elevated it from "local mistake" to "systemic process gap." The fix is cheap (a 3-line checklist) and the cost of the bug is high (production build drift that goes undetected until the next adversarial review).

The pattern is stable, process-driven, and transferable to any multi-file engineering work where analysis artifacts feed build/execution artifacts.
