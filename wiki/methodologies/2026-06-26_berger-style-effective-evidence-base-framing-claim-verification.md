---
title: Berger-style "effective evidence base" framing for claim verification
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-26
domain: methodologies
topic: measurement-methodology
tags: grounding, adversarial, quality-gate, empirical
related_entries:
  - methodologies/2026-05-13_verify-audit-claims-before-designing-fix.md
  - methodologies/2026-05-29_deterministic-first-debugging.md
  - methodologies/2026-06-25_invoke-kf-critic-before-sweep-minting-operator-attestation-claims.md
  - diagnostics/2026-06-16_moat-left-offstage-evidence-grounded-brand-copy.md
  - rules/verify-premise-before-defensive-bead.md
---

# Berger-style "effective evidence base" framing for claim verification

## The framework

When marketing or product copy cites "grounded in N peer-reviewed papers" (or any aggregate-count framing of an evidence base), the figure often includes papers REFERENCED BY the meta-analyses in the corpus, not just the directly-cataloged papers. This is the **Berger-style effective evidence base** framing:

```
effective_evidence_base = direct_corpus + unique(papers_referenced_by_meta_analyses) - overlap
```

The naming comes from Jonah Berger-style behavioral-marketing books that routinely cite "thousands of studies" while the bibliography is in the low hundreds — the "thousands" count includes the studies the cited meta-analyses themselves aggregated.

## When this matters

- Initial verification of an "N papers" claim against a smaller direct corpus may incorrectly conclude the claim is overstated, when in fact it is conservative under the effective framing.
- This is the failure mode the cos-grounding Phase 3 first-run hit: rejected an "860+" site claim as unsupported because the direct corpus was only 327 papers. F-II/F-JJ later proved the effective evidence base was 6,804 — making "860+" a ~8x undercount.

## When it does NOT apply

- Claims about *directly conducted analysis* ("we analyzed 10,000 messages") — those need direct-corpus backing, not meta-referenced inclusion.
- Per-paper specific-figure claims (a 30% lift figure attributed to one paper) — those still need source-body verification regardless of the corpus framing.

## How to compute it (Asta MCP)

1. Identify Tier-1 papers (meta-analyses) in the direct corpus: grep `evidence_tier: meta-analysis` across paper YAMLs.
2. For each meta-analysis, fetch references: `get_paper(s2_id, fields=references)`. Note: chunk batches to ≤10 with `--max-time 90` because large reference lists cause batch timeouts and NoneType errors.
3. Aggregate all referenced paperIds, dedupe across meta-analyses + against direct corpus.
4. Effective base = direct + unique-new-from-meta-references.

## Concrete grounding from the session that produced this entry

- Direct corpus: 327 papers
- 92 of 100 meta-analyses successfully processed (F-II initial 50 + F-JJ recovery 42)
- 6,477 unique meta-referenced paperIds (15 overlap with direct corpus, 6,477 new)
- Effective evidence base: 6,804 papers
- Ratio vs original site claim: 7.91× (i.e., site "860+" represented ~12.5% of provable evidence base)
- Audit trail: `~/Scripts/cos-grounding/findings/FII_CHECKPOINT-2026-06-26.md` and `FJJ_CHECKPOINT-2026-06-26.md`

## Caveat (academic-strict reading)

Some reviewers argue that citing a meta-analysis counts as relying on the meta-analysis's *conclusions*, not on each of the 8–10 underlying studies it aggregated. Under that strict reading, "effective evidence base" overstates direct evidential reach. The framing is a marketing-honest framing, not an academic-rigor framing — disclose the construction method when using the figure in formal contexts (academic submissions, regulatory filings, peer review).

## The deeper lesson

When a claim's denominator looks "too high" relative to a direct corpus, the first hypothesis to test is NOT "the claim is overstated" but "the claim uses a different counting framework than I assumed." Verifying claim semantics before verifying claim magnitude prevents the false-negative that the cos-grounding Phase 3 first-run produced. Pair this with the general "verify-premise-before-defensive-bead" rule — both are instances of the same anti-pattern: filing a defect against a claim whose construction method you haven't yet enumerated.
</content>
</invoke>