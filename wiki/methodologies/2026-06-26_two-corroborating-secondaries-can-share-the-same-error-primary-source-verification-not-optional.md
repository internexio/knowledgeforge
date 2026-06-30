---
title: Two corroborating secondary sources can propagate the same error — primary-source verification is not optional for numeric claims
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: stable
importance: 5
pinned: false
created: 2026-06-26
date: '2026-06-26'
domain: methodologies
topic: validation
tags: grounding, quality-gate, adversarial, confidence, empirical
source_fingerprint: cos-grounding-hape-001-berger-milkman-2012-anxiety-figure-conflation
related_entries:
  - methodologies/2026-05-20_primary-source-vendor-guidance-reanchor.md
  - methodologies/2026-05-13_verify-audit-claims-before-designing-fix.md
  - methodologies/2026-05-27_read-ground-truth-not-surface-signals-universal-antipattern.md
  - methodologies/2026-05-21_critic-verification-pass-second-pass-validation.md
  - methodologies/external-source-to-kf-mapping.md
---

# Two Corroborating Secondary Sources Can Propagate the Same Error — Primary-Source Verification Is Not Optional for Numeric Claims

## The Diagnostic

Two independent secondary sources agreeing on a figure does **NOT** substitute for primary-source verification. When both secondaries paraphrase the same primary, they can share the same error — most commonly because they conflate adjacent reported statistics in the source (e.g., a logistic-regression coefficient with the derived probability change).

This is a failure mode of *evidential corroboration heuristics* (the rule "N independent sources agreeing raises confidence"). The heuristic assumes the sources are independent in their *derivation*, not just in their *publication*. When N summarizers all paraphrase the same upstream paper, an error in the first-summarizer's conflation propagates into all downstream summaries — and the downstream agreement looks like independent corroboration when it is actually a shared blind spot.

## Concrete Case Study — cos-grounding hape-001 / Berger & Milkman 2012

Two operator synthesis documents in `~/Research/Personal/Personal_Public/FIGP Reframing Demos/` independently cited *anxiety: +24% sharing odds* for Berger & Milkman's 2012 JMR paper:

- **Doc A line 9:** *"awe increases virality odds by 30%, anger by 34%, and anxiety by 24%, while sadness decreases it by 16%."*
- **Doc B lines 322–323 + line 77:** cited the same 24% figure independently.

The cos-grounding Phase 3 RE-RUN used this two-source corroboration to raise hape-001 from `figure_derivable @ evidential 0.4` to `figure_derivable @ evidential 0.6` (composite 0.40 → 0.60), but kept the verdict at `rebuild_needed` because the source paper body remained unverified.

When the F-AA agent manually browser-downloaded the SSRN preprint and `pdftotext` extracted the actual paper text, **Figure 2 showed anxiety = 21%, not 24%.** The 24% number both synthesis docs cited was the **Table 4 Model 4 coefficient (log-odds)**, not the probability-change displayed in Figure 2. Both syntheses conflated the coefficient with the probability change.

## Why Two Corroborating Secondaries Shared the Error

- When a primary reports both a coefficient AND a derived percentage (e.g., logistic regression with both log-odds and % change in fitted probability), secondary summarizers often grab whichever number they encounter first.
- If the first-grab convention is the coefficient table (which appears earlier in most papers than the visualization), multiple downstream summaries inherit the same conflation.
- The summaries look mutually corroborating because they cite the same number — but the number's *origin* in the source paper is shared.

## Impact on cos-grounding's Verdict Ladder

- Two-source corroboration pushed evidential from 0.4 → 0.6 (within `figure_derivable` cap).
- Only primary-source access (F-AA `pdftotext`) pushed it to `figure_verbatim` → evidential 0.8 → composite 0.80 → `grounded`.
- The discipline of refusing to declare `figure_verbatim` without source-body access is what caught this error. If the rubric had accepted two-secondary-corroboration as sufficient for `figure_verbatim`, the wrong number would have shipped.

## Operational Rule (for any agent grounding numeric claims)

1. **Coefficients and percentages are NOT interchangeable in logistic regression outcomes.** Treat them as distinct claims that need distinct verification.
2. **Multiple secondaries citing the same number is not evidence of correctness** — they can all be wrong in the same way, especially when paraphrasing a multi-statistic primary.
3. **Source-body verification is the only valid path to `figure_verbatim`.** Cap secondary-corroboration at `figure_derivable` regardless of how many secondaries agree.
4. **When the verdict ladder has a `figure_verbatim` rung, the rubric must require source-body access to climb to it** — no amount of secondary stacking substitutes.

## Cross-Reference

The `figure_verbatim` discipline is encoded in `cos-grounding/.claude/agents/evidence-grounder.md` and the Phase 3 rubric. This entry documents the underlying *reason* that discipline exists — the failure mode it prevents.

## Generalization Beyond cos-grounding

This pattern applies anywhere claims pass through summarization chains:

- **Literature reviews citing other literature reviews** (rather than the underlying empirical papers).
- **Press coverage of scientific findings** (where outlet B paraphrases outlet A who paraphrased the press release who paraphrased the paper).
- **Wiki entries citing other wiki entries** (in any wiki-of-wikis topology).
- **LLM training-data echoes** — when multiple training sources share an upstream paraphrase, the model's "confident" output reflects shared-error stacking, not independent corroboration.

In all of these, the rule is the same: count *derivation* independence, not *publication* independence. Two sources whose chain of derivation traces back to the same upstream paraphrase count as **one** source for grounding purposes.
