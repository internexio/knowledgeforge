---
title: Validate new mutation-bearing orchestration skills with --dry-run on real-but-small data
source_mode: kf-builder + kf-critic
novelty_type: reusable_diagnostic
grounding_score: 0.75
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-30
tags: validation, dry-run, orchestration, skill-development, mutation-safety, methodology
related_entries:
  - wiki/orchestration/2026-05-29_append-only-queue-fingerprint-dedup-reconcile-gc.md
  - wiki/migrations/2026-05-24_safe-one-shot-backfill-script-dry-run-idempotent-no-improvement-skip.md
  - wiki/patterns/2026-05-12_dogfood-apply-undo-end-to-end-testing.md
  - wiki/methodologies/2026-05-27_supervise-first-real-data-run-autonomous-loops.md
---

# Validate new mutation-bearing orchestration skills with --dry-run on real-but-small data

## The Pattern

When building a new Claude Code skill / orchestration / agent-pipeline that mutates state (bead-tracker, git repo, file system, third-party API), implement a `--dry-run` mode FIRST and validate by running it against a real but small production dataset. Mutations are skipped; classifications, decisions, or actions are reported as "would do X." The output validates both correctness (did it classify right?) and design completeness (did it miss a field/case/dependency?).

## Why "real but small" beats fixtures

- **Fixtures lie.** Real data has weirdness fixtures don't capture: the symlinked `.beads`, the cross-repo path topology, the bead-with-no-description, the dep that nobody filed.
- **Production-shaped > production-sized.** Three real beads exercised more of the pipeline's branches than a synthetic 30-bead fixture would have. The orchestrator gets the path-resolution, the agent's classification quality, the dependency surfacing — all in one pass.
- **Reversible.** `--dry-run` makes the mutation-bearing parts of the design impossible to "accidentally" exercise. You can re-run as many times as you want.

## The Concrete Win in This Session

Built a 4-stage bead-workflow pipeline (4 skills, ~200 LOC of SKILL.md specs). Ran `/bead-triage --dry-run cos-12g cos-372 cos-sxk` as the first validation.

The dry-run's agent surfaced a real workflow gap: cos-372 depends on cos-12g (the shared module must land first), but v1 of the pipeline had no structured way to track or enforce this. The agent noted it in prose; v1 design would have silently lost the information.

### v2 Enhancement Applied Immediately

- `triage-prompt.md` → added `**Depends on:**` field to NEEDS-SPEC + READY-TO-BUILD output blocks
- `bead-triage` SKILL → step 7 now runs `bd dep add <bead> <dep>` for surfaced deps
- `bead-decisions` SKILL → preserves the field in worksheet → queue handoff
- `bead-build` SKILL → pre-flight checks dep satisfaction; skips blocked beads with annotation
- `bead-pipeline` README → documents v2 with the surfaced example

**Total cost of fixing the gap pre-mutation:** ~15 min. **Total cost if the gap had been found after a real run:** hours (cos-372 built before cos-12g, then rework on the not-yet-extracted shared module).

## When to Apply

ANY new skill that:
- Closes, updates, or creates issue-tracker items
- Pushes commits, opens PRs, or modifies branches
- Runs DB queries that aren't read-only
- Calls external APIs that cost money or have rate limits
- Coordinates multiple agents whose work is hard to roll back

**Decision rule:** If your skill EVER includes the phrase `if not dry_run:` in its instructions, the dry-run must be exercised on real data before anything else touches it.

## When NOT to Apply

- Skills that are purely read-only (querying, search, analysis) — no `--dry-run` needed because there's nothing to mutate
- One-off scripts that will only ever run once on a known input
- Skills where the dry-run is harder to build than the real thing (rare, but exists)

## Grounding

**Session:** 2026-05-30 [project] bead pipeline v1 → v2 enhancement

**Validation:**
- **Skill:** `/bead-triage` (Phase 1 of a 4-stage pipeline)
- **Real data:** 3 beads filed earlier in the same session (cos-12g, cos-372, cos-sxk)
- **Dry-run output:** 1 NEEDS-SPEC + 2 READY-TO-BUILD classifications, with file:line evidence + draft proposal text
- **Surfaced gap:** implicit dep (cos-372 → cos-12g) noted in agent prose but unstructured in v1
- **v2 fix:** 5 SKILL.md/template edits applied immediately, `bd dep add cos-372 cos-12g` recorded the real dep, pipeline strictly more useful post-fix

## When This Applies

Applies in two tiers:

### Tier 1: New skill on an existing pipeline
You've shipped a 4-stage bead pipeline (A → B → C → D). You're adding a new skill that mutates artifacts in stage B. Run the new skill's dry-run against 2–3 real beads that are actually queued for B. If dry-run surface a design gap (missing field, unhandled case, missing dependency), fix it before real mode activates.

### Tier 2: New pipeline on a new problem domain
You're building a 4-stage orchestration for a problem you haven't solved before. The first validation of the entire pipeline (stage 1 through stage 4) should be a dry-run against real-but-small data. This catches inter-stage contract mismatches (output of stage A doesn't match input schema of stage B), missing handoff fields, and blocking dependencies.

## When This Does NOT Apply

- Read-only analysis pipelines (no mutations, so dry-run adds no value)
- Pipelines that have already shipped and been in production for weeks (use the "supervise-first-real-data-run" pattern instead)
- Systems where a staging environment is available and cheaper than risk analysis (dry-run is about risk, not cost)

## Anti-Patterns to Avoid

**Running dry-run on synthetic data only:**
Misses real-shape edge cases (the symlinked `.beads`, the cross-repo topology, the bead-with-no-description). Synthetic data validates the happy path. Real data validates the pipeline's resistance to chaos.

**Skipping dry-run because "I'll just be careful":**
Every real failure this author has watched started with this thought. Dry-run is not about being careful; it's about shipping correctly the first time.

**Running dry-run on data that's been pre-shaped to match the skill's expectations:**
Defeats the purpose. Pick whatever's been sitting in the backlog — the weird data is what you need.

**Treating dry-run output as success-only:**
The real value is when it surfaces a gap you didn't design for. A dry-run that finds no issues is less valuable than one that says "you forgot to handle the case where the bead has no description."

## Source Context

Derived from [project] session 2026-05-30, bead pipeline v1 → v2 enhancement. A 4-stage orchestration for bead triage, decision, build, and handoff was designed and 3 skills were coded (~200 LOC of SKILL.md specs). Before running any real mutations, the `/bead-triage --dry-run` command was invoked on 3 real beads (cos-12g, cos-372, cos-sxk) that had been filed earlier in the same session. The dry-run surfaced a critical design gap: cos-372 depends on cos-12g, but v1 had no way to represent or enforce this dependency. The dependency was noted in the agent's prose output but was unstructured. v2 added a `**Depends on:**` field to all output blocks, and step 7 of the triage skill now records these deps via `bd dep add`. This change made the entire pipeline more robust. The gap would have been discovered post-mutation (during the first real run on a larger backlog) if the dry-run hadn't been run first.

## See Also

- **Safe one-shot backfill script** — similar philosophy (dry-run default + idempotent + skip-no-improvement) but for data migration scripts
- **Dogfood the safety machinery** — testing strategy for autonomous systems; complements dry-run as a second layer of validation
- **Supervise first real-data run** — what to do when the dry-run passed but you're now running on the full production dataset
- **Append-only queue with re-running producer** — orchestration pattern for handling real data as it flows through multi-stage pipelines
