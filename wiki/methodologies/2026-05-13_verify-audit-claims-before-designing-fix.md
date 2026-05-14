---
title: Verify audit-doc structural claims against current code before designing the fix
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.80
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-13
tags: audit-workflow, refactoring, stale-documentation, scope-creep, prior-work-discovery
related_entries:
  - patterns/2026-05-11_audit-log-event-vocabulary-mismatch.md
  - orchestration/adversarial-filename-audit.md
---

# Verify Audit-Doc Structural Claims Against Current Code Before Designing the Fix

## The Diagnostic

Code-review / audit / "tech-debt manifest" documents go stale within weeks of being written. Unrelated PRs land between the audit and the implementation pass, and some of those PRs partially or fully resolve audit findings as a side-effect of other work. The audit doc never updates itself.

If you implement the prescribed fix without checking current state, you end up:
- Building structure for a problem that's already 80% smaller than documented
- Adding cleverness (loops, dataclasses, dispatchers) the residual problem doesn't justify
- Confusing future readers ("why is this abstraction here? the file it lives in is only 50 LOC")

## Concrete Grounding (COS STR-M1)

The COS 2026-05-12 code review flagged `buyers_committee/run_orchestrator.py::execute_run` as a "262-line linear T1→T5 pipeline with 18 inline cancellation checkpoints". The fix-as-written prescribed a `TurnSpec` loop "with one cancellation site".

Reading the current code first surfaced:
- `[project]-y4b` (filed ~2 weeks before the audit) extracted T5 (blindspot audit) into an explicit user-invoked endpoint `run_blindspot_audit`. The pipeline became T1→T4, not T1→T5.
- The cancellation checkpoints had been consolidated to turn boundaries (5 total, not 18). The "18 sub-turn checks" the audit cited belonged to a prior version that no longer existed.

The audit's structural prescription was sized for a problem that had been ~70% solved by an unrelated refactor. Implementing the literal sketch would have over-engineered the remaining cleanup.

The actual shipped fix: a single boilerplate helper + two small dataclasses (see entry on helper-extraction-vs-loop-refactor). Total `execute_run` body shrank by ~50 LOC; module net +50 LOC (helpers reusable for future turns).

## The Pre-Design Check

Before writing the refactor:

```bash
# 1. Read the cited file/function as it stands today
sed -n '<start>,<end>p' <file>

# 2. Count the structural claims (LOC, checkpoints, branches, duplicates)
grep -c '<pattern from audit>' <file>

# 3. If the count is materially lower than the audit cited:
#    - check git log for recent refactors of the cited region
git log --oneline -20 -- <file> | head -20
git log --diff-filter=M --grep '<keywords>' -- <file>

# 4. Then size the fix to the residual problem, not the documented one.
```

If the audit said "262 LOC, 18 checkpoints" and the current state is "150 LOC, 5 checkpoints", the residual problem may not be worth the prescribed abstraction. Note that in the commit body or PR description so reviewers don't expect the structural transformation the doc described.

## When This Applies

- Tech-debt manifests / code-review documents older than ~2 weeks
- Multi-week / multi-month implementation sequences against a fixed audit doc
- Hand-off briefs that cite specific line counts, checkpoint counts, or duplication counts
- Any artifact written by a different engineer / agent than the one implementing the fix

## When This Does NOT Apply

- Audit docs less than ~3 days old in a single-developer codebase (low drift risk)
- Findings about external surface (API contracts, schemas) that don't silently change
- Bug reports with concrete reproducers (the bug either reproduces or it doesn't; no need to verify the "structural" claim)

## The Deeper Lesson

Audit docs are snapshots, not contracts. Treat the structural claims ("N LOC", "M call sites", "K duplications") as approximate signals, not ground truth. The fix proposal is sized for the snapshot; the implementation must be sized for the present.

Cross-reference with the existing wiki entry on "audit-log-event-vocabulary-mismatch" — same class of drift, different artifact (event vocabulary instead of structural counts).

## Source Context

Discovered during COS 2026-05-12 code review cycle (session: cos-audit-2026-05-13-str-m1-stale-audit-claim). The STR-M1 turn-orchestrator audit prescribed a major refactor based on structural metrics (LOC, checkpoint count) that had been partially invalidated by an intervening refactor (`[project]-y4b`) extracting the final turn into a separate endpoint. The mismatch between audit snapshot and current state would have led to over-engineering if the fix had been implemented without re-reading the code first.

