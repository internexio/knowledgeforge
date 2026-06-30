---
title: Bucket-binary audit UX silently substitutes agent URL-inference for operator per-page recall
source_mode: critic
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.8
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-25
domain: patterns
topic: audit-ux
tags: audit, ux, scope-discipline, attestation, schema-org, e-e-a-t
related_entries:
  - patterns/2026-06-20_operator-decision-driven-artifacts-four-surface-separation.md
  - methodologies/2026-06-19_operator-review-gate-in-semi-automated-workflows.md
  - methodologies/2026-05-27_read-ground-truth-not-surface-signals-universal-antipattern.md
  - methodologies/2026-05-21_critic-verification-pass-second-pass-validation.md
  - patterns/2026-05-22_spec-to-implementation-gap-distinct-review-pass.md
---

# Bucket-binary audit UX silently substitutes agent URL-inference for operator per-page recall

## The pattern

When a bead/spec calls for an **operator audit** — meaning the operator's private knowledge (which pages they wrote, which they reviewed, which they didn't touch) is the load-bearing differentiator — and the agent then presents the audit work as N bucket-level questions (each operator answer applies binary to ~20 pages), a silent substitution occurs:

| | |
|---|---|
| **Stated work** | operator-recall over individual pages |
| **Actual work** | agent URL-pattern inference + operator binary on clusters |

The bucket questions feel efficient ("we need 4 decisions instead of 74"), but the operator never reads page titles, never recalls writing any specific page — they answer based on the agent's bucket framing (URL prefix, top-level category) which has no relationship to actual authorship history. The agent then ships per-page schema attestations based on those bucket answers, effectively making URL-clustering an attestation proxy.

**Symptom in shipped artifact:** attestation pattern correlates with URL shape (e.g., all `/guides/*` pages claim the same author) rather than with actual content provenance (which crosses URL boundaries — some guides are operator-written, some are AI-drafted-and-edited, some are contributor-written).

## Why this matters for schema-org E-E-A-T specifically

- `Article.author = Person` makes a **verifiable claim** Google checks against backstop signals (LinkedIn cross-refs, podcast appearances, prior bylines). If the claim is bucket-uniform but the reality is mixed-provenance, the validation gap downgrades the entire site's E-E-A-T signal.
- **The risk is asymmetric:** under-attestation costs a marginal authority signal; over-attestation across content the operator didn't actually write causes a stronger negative signal (content-farm pattern). Bucket-binary biases toward over-attestation because it's easier for the operator to answer "yes, this whole bucket" than to think page-by-page.

## Fix pattern

When a bead says "operator audit," surface a **per-page UI**:

1. Markdown checklist of all candidate pages with:
   - URL
   - `<title>` tag content (so the operator recognizes the page)
   - Optional: last-modified date, brief description
   - `[ ]` checkbox the operator changes to `[x]`
2. **Default = no attestation** (the safe Stance-B-style default where the entity is `author = Organization` and per-page `editor = Person` additions are opt-in).
3. Operator marks the pages they recall actually authoring/editing.
4. Sweep script parses the checklist and applies attestation only to checked pages.

This puts the operator's private knowledge **into** the data flow instead of routing around it.

## When this applies

- Schema attestation work (`Article.author`, `Article.editor`, `reviewedBy`)
- Content-provenance claims at scale
- Any audit where a real-world fact varies per item and only the operator knows the per-item ground truth

## When this does NOT apply

- **Mechanical refactors with no attestation surface** (e.g., renaming a field across N files — bucket-level is correct because the change is structural, not factual).
- **Cases where the operator legitimately has cluster-level knowledge** (e.g., "I never edited any `/docs/api/` page" — bucket-level binary is fine because the operator's recall IS cluster-shaped).

## Diagnostic test

> Does the operator's private knowledge vary per-item or per-cluster?

If **per-item**, bucket-binary is wrong.

## Grounding

[project] 2026-06-25 cos-mk2l audit. I proposed 4 buckets (top-level: `marketing` / `guides` / `personality` / `docs-api`) × 3 schema options (Person / Organization / None). Operator invoked `/kf-5.1-backup review` → kf-critic surfaced 10 findings, of which the most load-bearing was **finding #3**: bucket-binary directly deviated from the bead description I'd written 24h earlier ("Operator audit: identify which pages David is genuinely the author of [per-page]"). Restart with a sitewide-stance prerequisite + per-page markdown checklist (74 pages, 19 sections) preserved the operator-recall data flow.

## Related entries

- `patterns/2026-06-20_operator-decision-driven-artifacts-four-surface-separation.md` — the four-surface mechanics for operator-decision artifacts; this entry diagnoses a UX-level failure mode that violates that pattern's "operator judgment is the load-bearing input" premise.
- `methodologies/2026-06-19_operator-review-gate-in-semi-automated-workflows.md` — operator review as a gate between auto-gen and publication; this entry is about the gate's *interrogation surface*, not just its presence.
- `methodologies/2026-05-27_read-ground-truth-not-surface-signals-universal-antipattern.md` — agent reading URL shape instead of authorship history is a domain-specific instance.
- `methodologies/2026-05-21_critic-verification-pass-second-pass-validation.md` — the kf-critic pass on the audit plan caught this before ship; reinforces critic-before-execute discipline for audit UX design.
- `patterns/2026-05-22_spec-to-implementation-gap-distinct-review-pass.md` — bead description ("per-page audit") vs implementation plan ("bucket questions") is exactly a spec-to-impl gap.
