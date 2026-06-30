---
title: Spec-environment pattern mismatch — dual-pattern regex + authoritative downstream check
source_mode: direct
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-14
tags: spec, validation, regex, environment-mismatch, drift, beads
related_entries:
  - diagnostics/handoff-payload-schema-gap.md
  - orchestration/schema-first-elicitation-order.md
  - patterns/2026-05-13_conditional-update-for-atomic-queue-claim.md
domain: patterns
topic: validation
---

# Spec-Environment Pattern Mismatch — Dual-Pattern Regex + Authoritative Downstream Check

When a spec's regex pattern for an ID/identifier field doesn't match the actual runtime environment's shape, the temptation is either to (a) modify the spec to match reality or (b) hand-massage incoming values at every call site. Both create silent drift. There's a third path.

## The Pattern

1. **Relax the regex** to accept the spec's intended shape AND the actual environment's shape. Document both in a one-line comment.
2. **Treat the downstream existence check as authoritative.** The regex is a pre-filter for obviously malformed values; the real validation is "does this thing actually exist in the system."

## Concrete Instance from Iteration-Loop v0

The `baking_pipeline_contract.md` + `proposal_schema.toml` spec field:

```toml
[fields.source_beads_issue_id]
type = "string"
required = true
pattern = "^bd-\\d+$"
```

But [project]'s actual beads database uses slug-style IDs (`[project]-qh2`, `[project]-iats`). The spec was written speculatively before the beads database existed.

Three options considered:
- (a) Edit spec pattern → invalidates any other consumer's conformance proof + requires resync with spec author
- (b) Add a translator at every call site (`"bd-" + str(hash(slug))`) → silently rewrites authoritative data, double-translation hazards
- (c) **Dual-pattern + authoritative check** (chosen):

```toml
[fields.source_beads_issue_id]
type = "string"
required = true
# Accepts spec form `bd-1247` AND slug form `[project]-qh2` (the actual format
# in this project's beads database). Bd-existence check at the emit gate is
# authoritative — the regex is only a pre-filter for obviously malformed IDs.
pattern = "^(bd-\\d+|[a-z][a-z0-9]*(?:-[a-z0-9]+)+)$"
```

Authoritative check in `stages/input_validation.py::_bd_issue_exists`:

```python
completed = subprocess.run(["bd", "show", issue_id, "--json"], ...)
parsed = json.loads(completed.stdout)
# {"error": "..."} envelope → non-existent
# [{...}] array → exists
```

## Why This Beats the Alternatives

- **Spec readability preserved.** A future maintainer sees both intents — the original spec form and the local environment form. Comment explains why.
- **Single source of truth for existence.** The regex doesn't pretend to validate semantic existence; the subprocess does.
- **No double-translation.** Values flow through the pipeline as the environment emits them — no silent rewrites.
- **Migration-friendly.** When the environment changes its convention, you update the regex without touching call sites.

## When This Applies

- Multi-tenant tools where the same spec runs against environments with different naming conventions
- Specs written speculatively before the environment is fully built out
- Migration periods where both old + new formats coexist
- Vendor-prefixed IDs vs. namespace-prefixed IDs
- Cross-system integrations where upstream and downstream have independently evolved ID formats

## When This Does NOT Apply

- **Pattern mismatch is a hard correctness issue.** If the spec demands ASCII but the environment emits UTF-8, relaxing the regex creates a real downstream bug — fix the environment or fix the spec, don't paper over with regex relaxation.
- **The environment's format is a known prefix of the spec's format and a normalisation function is well-defined and reversible.** Then a normaliser at the boundary is cleaner.
- **The downstream check is also broken / unreliable.** If `bd show` can lie about existence, dual-pattern alone isn't enough.
- **The regex is the only line of defense against injection / parsing attacks.** A relaxed regex that passes unsafe input to the authoritative check is a security regression. Ensure the authoritative check sanitizes or rejects the input if necessary.

## Related Anti-Patterns This Avoids

- **"Edit the spec to match the environment"** — Invalidates other consumers' conformance proofs.
- **"Hand-massage at every call site"** — N call sites = N places bugs can hide.
- **"Strip the regex entirely"** — Loses pre-filter value, gives attackers / typos a free pass to subprocess invocation.
- **"Use normalisation functions silently"** — Rewrites authoritative data without visibility, causes confusion during migration.

## Source Context

Discovered in iteration-loop v0 ([project] sprint 2026-05-14) when reconciling `baking_pipeline_contract.md` (spec-side pattern `^bd-\\d+$`) with actual beads database ID format (slug-style `projectname-key`). The pattern emerged as a clean resolution that preserved spec authority, prevented silent data rewrites, and remained maintainable across future environment changes.
