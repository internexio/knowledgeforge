---
title: Hedging-language loss during migration from draft to outbound surfaces — a recurring numeric-claim failure mode
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-27
date: '2026-06-27'
domain: methodologies
topic: content-migration
tags: content-migration, numeric-claim, hedging-language, epistemic-degradation, grounding, citation-audit, knowledge-aggregation, marketing-copy
related_entries:
  - methodologies/2026-06-26_two-corroborating-secondaries-can-share-the-same-error-primary-source-verification-not-optional.md
  - methodologies/2026-06-26_berger-style-effective-evidence-base-framing-claim-verification.md
  - methodologies/2026-05-20_primary-source-vendor-guidance-reanchor.md
  - methodologies/2026-05-27_read-ground-truth-not-surface-signals-universal-antipattern.md
  - diagnostics/2026-06-16_moat-left-offstage-evidence-grounded-brand-copy.md
  - diagnostics/2026-06-17_ai-fingerprint-patterns-seven-recurring-tells-marketing-prose.md
---

# Hedging-language loss during migration from draft to outbound surfaces

## The pattern

When a specific numeric claim originates in a draft or research artifact (where the author is thinking carefully and hedges the figure with a qualifier — "midpoint of a 25-35% band", "in our sample of N=...", "this study estimates..."), and that content is later MIGRATED to a higher-confidence surface (outbound email, marketing copy, public web page, schema.org JSON-LD), the hedging language tends to be DROPPED because it reads as weak. The figure survives; the epistemic status it had does not.

## Two independent confirmations from the same session (2026-06-27)

**Confirmation 1 — cos-grounding site-citation audit (`findings/site-citation-audit-2026-06-27.md`):**
- Noar et al. 2007 paper body reports r=.074 ≈ d=0.15 as the meta-analytic mean effect size. The site copy claims "d=0.48" (a different sub-aggregate, presented as if it were the headline number). Hedging-of-the-aggregate was lost in migration.
- Loewenstein 1994 is a theoretical review with no experiments. The site copy attributes "23-47% engagement lift" to it. The hedging that the original paper does NOT report this figure was lost — the figure appears to be from downstream replication studies but is attributed to the theoretical source.
- Brehm 1966 is a theoretical monograph with no experimental conversion-rate data. The site copy claims "40% reduction" via Brehm. The hedging that Brehm 1966 doesn't measure this was lost in migration.

**Confirmation 2 — client-project gtm-6ed audit (`~/Scripts/client-project/wiki/reference/stat-grounding/2026-06-27_32-percent-audience-reach.md`):**
- The "32% of B2B messaging reaches its intended audience" figure originated in a Feb 2026 COS blog draft (`[project]/cos/docs/blog/drafts/cluster-c/C1-32-percent-problem.md`) with EXPLICIT hedging: "the effective coverage tends to land between 25% and 35%... that's where the 32% comes from. Not a precise universal constant, but a consistent pattern."
- That hedging caveat appears verbatim in the source draft on line 23.
- When the figure migrated to outbound templates, the Substack T5 title, the Huffman DM, and the 14-Day Plan, the hedging language was dropped. The bare "32%" appeared as if it were a measured external statistic for months.

## When the pattern applies

Any time content migrates from a context where the author was thinking carefully (research notes, drafts, internal docs, source-paper bodies, methodology sections) to a context where the author is performing confidence (outbound copy, marketing surfaces, public web, schema.org descriptions, press releases, sales decks).

Specific high-risk transitions:
- Source paper body → website citation
- Internal blog draft → published blog post
- Research note → cold-email template
- Founder pitch deck early version → final pitch deck (specific numbers from "directionally true" framing get committed-to)
- Long internal Slack thread → short external Slack DM
- PhD thesis methodology → consumer-facing claim about the technology

## Diagnostic signal

A figure on a high-confidence surface that:
1. Looks authoritative (specific, named source, paired with a "research shows X" framing)
2. Cannot be located verbatim in the named source body when audited
3. Traces back to an internal draft where it appears with hedging ("around", "roughly", "midpoint of a band", "in our analysis")

The hedge being present in the source draft + absent in the migrated surface is the smoking-gun pattern.

## Why it happens (the failure mode)

Three forces:

1. **Confidence performance** — outbound copy and public surfaces reward specificity; hedging reads as weak; copywriters strip it.
2. **Multi-surface drift** — the same figure appears in multiple downstream surfaces over time; each migration strips a little more hedging; by the time it reaches the most public surface (homepage, schema.org meta-description), the hedging is gone.
3. **Loss of authorial context** — the person migrating the content is often NOT the person who originally hedged it. They see "32%" in a draft and assume it's a measured fact, not a derived heuristic.

## Preventive pattern

When migrating numeric claims across surfaces:

1. **Carry the hedging language forward.** If the source says "around 32%", the migrated version says "around 32%" (not "32%"). Hedge propagation is a deliberate authorial choice, not a copywriting failure.

2. **Tag the epistemic status at the source.** Use a convention like `~32%` (derived heuristic), `32% [N=...]` (empirically measured with sample size), or `"around a third"` (explicitly qualitative). Make the form of the figure carry the certainty signal.

3. **Audit numeric claims on high-confidence surfaces against their named sources** — verbatim. If the figure does not appear verbatim in the source body, flag the migration as broken and either rework the claim or replace the source.

4. **For derivative figures (no external source — internal derivation):** use honest-attribution framing rather than dropping the number. Examples from gtm-6ed Path B: "in our analysis" / "by the math" / "a derived midpoint of..." preserve the bite of specificity while signaling the figure's epistemic status. This is the alternative to either keeping the bare figure (overclaim) or stripping it entirely (loses the hook).

## When the pattern does NOT apply

- The source IS the authoritative document and the figure IS a measured fact (e.g., a properly-conducted survey with N=10,000 reports "32% of respondents..."). The figure is then a citable fact that can survive migration without hedging.
- The hedge in the source was a stylistic choice (the author's personal hedging tic) and not an epistemic statement. (Distinguish: "we found 32%" with a hedging "I think" tic vs "we found a midpoint of a 25-35% band" where the hedge IS the epistemic statement.)
- The migration is purely between artifacts of the same confidence level (one internal doc to another). The forces that strip hedging activate at the outbound/public boundary.

## How to use this in future audits

When auditing a public-facing numeric claim:

1. Find the FIRST appearance of the figure in the content trail (search internal drafts, source papers, research notes).
2. Read the original hedging language around the figure.
3. Compare it to the current public version.
4. If hedging is missing — flag the claim. Either restore the hedging, replace the figure with a properly-cited alternative, or rework as honest-attribution.

This audit pattern surfaced 4 unsourceable figures in one session (3 on the cos-grounding site, 1 in client-project outbound) — high signal-to-noise.

## Concrete grounding from the session

The session that produced this candidate ran two independent citation audits using two different teams of agents (cos-grounding's site-citation-audit agent + client-project's 3-track stat-grounding agent). Both surfaced the same failure mode — bare numeric claims on outbound surfaces that traced back to drafts with explicit hedging. The pattern is documented in:

- `~/Scripts/cos-grounding/findings/site-citation-audit-2026-06-27.md` — 20 citations audited, 5 figures softened (Noar d=0.48, Loewenstein 23-47%, Brehm 40%, Cialdini 200+, Kahneman r=0.581 attribution-chain)
- `~/Scripts/client-project/wiki/reference/stat-grounding/2026-06-27_32-percent-audience-reach.md` — the 32% derivation chain, Track 3 specifically documents the hedging-loss
- `~/Scripts/cos-grounding/findings/gtm-6ed-path-b-rollout-2026-06-27.md` — the resolution applying honest-attribution to a derivative figure (the preventive pattern in §4 above)
