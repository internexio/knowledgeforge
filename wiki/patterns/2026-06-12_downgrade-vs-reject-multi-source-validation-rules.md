---
title: Downgrade-vs-reject pattern for cross-cut validation rules
source_mode: critic
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-12
domain: patterns
topic: validation
tags: adversarial, quality-gate, metadata-filter, tier-0, empirical
related_entries: []
---

# Downgrade-vs-Reject Pattern for Cross-Cut Validation Rules

## Problem Shape

In schema validation pipelines with multi-source data (field X populated by either Source A or Source B), cross-cut rules that REJECT on incompatible combinations can silently hide useful data when the rejection path is the common case for one of the sources.

**Symptom:** A validation rule was written under the assumption that the field comes from Source A (where the rejected combination is rare); a downstream feature later adds Source B (where the rejected combination is the common case). The rule still fires; the feature's contribution is silently dropped; the feature appears to have no effect; debugging is hard because no error surfaces.

## Pattern

When a cross-cut validation rule encounters a combination that:
1. Is invalid for the ORIGINAL source path's invariants, AND
2. Is the COMMON case for a NEWER source path, AND
3. Has a valid downgrade path (a less-specific category that the data fits)

THEN: split the rule into two sub-rules based on source provenance.

- **Sub-rule 1 (downgrade):** If data is from the newer source AND in the rejected combination → downgrade to the safer category. Log the downgrade with a distinct reason code so it's auditable.
- **Sub-rule 2 (reject):** If data is from the original source (or has no provenance metadata) AND in the rejected combination → reject per original Phase 1 semantics.

This preserves the original rule's protective semantics while keeping the new source's contribution visible.

## Requires Source Provenance

The split rule needs to know which source produced each value. This typically means adding a small sidecar field (e.g., `path_globs_meta: [{glob: <string>, source: era|manual}, ...]`) alongside the main field. The sidecar stays optional — entries without it are treated as the original source for backwards compatibility.

## When This Applies

- A new feature adds a SECOND populating path for an existing field
- The original validation rule was correct for the first path but would reject the new path's common output
- There's a clean downgrade category — the data is valid in a less-specific bucket
- You can identify the source at validation time (provenance metadata exists)

## When This Does NOT Apply

- Both sources have the same invariants — there's no semantic reason to treat them differently; the original rule is just wrong and should change
- There's no safe downgrade — the rejected combination is invalid regardless of source (e.g., type errors); reject is the correct response
- Provenance is not knowable at validation time — the split rule has no discriminator to use

## Verified During

2026-06-12 KF session, bead 8gp adversarial-critic finding.

**Original M21 step_3c rule:** "If trigger == path_bound AND scope == global → reject candidate." Written under Phase 1 (y4b) when path_globs only came from explicit producer-mode authoring. Critic identified that 8gp's new ERA resolver commonly produces globs for architectural patterns — which are exactly the candidates that get classified as scope: global. Silent rejection would make the entire resolver invisible (the very thing it was built to prevent: <1% path_bound).

**Fix applied:** Split step_3c into TWO rules using a new `path_globs_meta` sidecar field that records source provenance per glob:
- ERA-source globs on global scope → DOWNGRADE trigger to task_bound, clear path_globs, log as `era_global_glob_downgrade`
- Manual-source globs on global scope → REJECT per Phase 1, log as `scope_glob_cross_cut`

**Effect:** The resolver's contribution stays visible (task_bound is the right semantic for cross-repo entity-anchored knowledge); manually-authored rule violations still surface as errors; the protective invariant is preserved per its original intent.

## Generalizability

Applies wherever:
- A schema/validation pipeline has multi-source field population
- One source's "rejection" is another source's "common case"
- A safer downgrade category exists

**Common appearances:**
- ETL pipelines with new data sources
- API versioning where v2 adds a new shape that v1 rules would reject
- User-input forms vs system-populated fields with shared schema

## Related Patterns

This pattern complements:
- **Sidecar manifests** for tracking tool-vs-user contributions (applies to metadata/config; this applies to data validation)
- **Discriminated unions** for source-specific handling (union shapes; this is about rule dispatch)
- **Gate-design quality patterns** (this is a specific gate-ordering decision)
