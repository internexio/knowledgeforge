---
title: Cross-module summary-row drift — referencing module's count claim desyncs when referenced module bumps entities
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic, transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-06-14
domain: patterns
topic: validation
tags: cross-reference-integrity, version-coordination, linter-pattern, summary-row-drift, kf-modules
related_entries:
  - patterns/2026-05-22_spec-to-implementation-gap-distinct-review-pass.md
  - patterns/2026-05-18_markdown-binary-artifact-drift-independent-editing.md
  - patterns/2026-05-12_vendoring-drift-detection.md
  - methodologies/2026-06-10_kf-semver-three-surfaces-module-system-binding.md
---

# Cross-module summary-row drift — referencing module's count claim desyncs when referenced module bumps entities

## The Problem

When a KF module is *referenced* from another module's Module Reference table or summary row, the row often encodes a numerical claim about the referenced module's contents — e.g., "Handoff Contract Registry — 8 contracts (7.2.0)". When the referenced module bumps to add entities (new contracts, new variants, new validation checks), the SOURCE module's own validation often catches the new count (e.g., M03's "exactly 10 entries" validation comment), but the REFERENCING row in the upstream summary does NOT auto-update.

Both modules pass isolated review. The drift is invisible until you cross-reference them.

## When this applies

- Any module that maintains a Module Reference table or count-claim summary row about another module
- When the referenced module has its own deterministic count assertion (validation comment, registry size declaration)
- When the referenced module bumps to add entities of the counted kind
- Specifically observed in KnowledgeForge: M00 Module Reference table, M00 module-grouping summaries, possibly other inter-module count references

## When this does NOT apply

- Modules with only narrative references ("see Module X") — no numerical claim to drift
- Single-source-of-truth fields with no duplication
- Changes that don't alter countable entity counts (text edits, rule clarifications)

## Concrete grounding

**Session: 2026-06-14, KF-core cp-reconciliation, audit item 3b.**

Defect surfaced: M00 (`modules/00_orchestrator.md` L610) said:

> "Handoff Contract Registry — 8 contracts (7.2.0)"

while M03's own validation comment (`modules/03_coordination_patterns.md` L602) asserted:

> "exactly 10 entries"

The drift was created when M03 added two new entries:

- Contract A: `hc-orchestrator-to-verifier`, 7.4.0/SPEC-1
- Contract B: `hc-runtime-to-accretion-gate`, 7.3.0/SPEC-4

Their respective changelog entries bumped M03 itself but did NOT update M00's summary row.

Detection mechanism in this session: an integrity audit pass cross-referenced the row text against M03's authoritative count. The defect was invisible to per-module review because each module's own asserts were internally consistent.

## Deterministic detection pattern

For an M07 linter variant or pre-commit check:

1. Parse referencing module for rows of shape `<entity-class> — N <units> (vX.Y.Z)` (e.g., `"Handoff Contract Registry — 8 contracts"`).
2. Identify the referenced module from the row's anchor (e.g., `03_Coordination_Patterns`).
3. Find that module's authoritative count assertion — typically:
   - a validation comment (`# Validation: registry must have exactly N entries`),
   - a registry list whose length is the count, or
   - a declared array length.
4. Flag any mismatch between the referencer's claim and the referenced module's authoritative count.

## Resolution pattern

When drift is detected:

- Patch-bump the referencing module (no behavior change, internal-consistency only).
- Update the row to match the referenced module's authoritative count, including the version stamp from the bump that added the new entities.
- Cite each added entity inline when possible, e.g.:

  > "10 contracts (7.4.0; +A 7.4.0, +B 7.3.0)"

  so future audits can trace which bumps introduced which entities.

## Why this matters as a class

- KF cross-references modules heavily (every module's `related:` field; M00's table; M06's quick reference).
- As the system evolves through compiler-emitted variants, summary rows act as load-bearing documentation — downstream readers consult them as primary sources.
- The cost of drift compounds: stale row → wrong reader mental model → wrong downstream artifact.

## Recommended follow-up

(Deferred — not scope of the producing session.)

- **M07 linter variant:** add a `check_class` for `cross_reference_count_drift`.
- **Pre-commit hook variant:** when a module changes its registry size, grep for referencers and flag any row that names the changed module.

## Relationship to neighboring entries

- **`patterns/2026-05-22_spec-to-implementation-gap-distinct-review-pass.md`** — same family (an artifact that passes self-review can still misrepresent another artifact). This entry specializes to the count-claim form of that gap, between two specs rather than between spec and code.
- **`patterns/2026-05-18_markdown-binary-artifact-drift-independent-editing.md`** — drift between markdown source and exported binary when both are edited independently. This entry covers drift between two source modules where one names a count of the other's entities.
- **`patterns/2026-05-12_vendoring-drift-detection.md`** — unreviewed divergence between vendored content and its source-of-truth. Similar shape; this entry is the inter-module-reference specialization.
- **`methodologies/2026-06-10_kf-semver-three-surfaces-module-system-binding.md`** — the multi-surface versioning context within which this drift class arises.
