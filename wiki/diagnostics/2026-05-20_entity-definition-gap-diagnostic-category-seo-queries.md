---
title: Entity-definition gap diagnostic for category SEO queries
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-20
domain: seo-strategy
topic: serp-ranking-diagnosis
tags: seo, gsc, ai-overviews, category-queries, entity-definition
related_entries:
  - methodologies/2026-05-20_primary-source-vendor-guidance-reanchor.md
  - methodologies/2026-05-19_seo-keyword-volume-cpc-tradeoff.md
---

# Entity-Definition Gap Diagnostic for Category SEO Queries

## Diagnostic Signature

When a single page ranks **page 1 for `[term] comparison` queries** but **page 3 or deeper for bare `[term]` / `[term]s` queries**, the root cause is almost always: the page jumps directly to comparison framing without first **defining the entity** at the semantic level. AI Overviews, featured snippets, and category-search ranking algorithms preferentially surface pages that lead with an explicit entity definition.

## Real-World Signature (from 2026-05-20 session)

GSC 90-day data for `/guides/content-analytics-tools/`:

| Query | Position | Impressions | Clicks |
|---|---|---|---|
| `content analytics tools comparison` | 7.8 | 11 | 0 |
| `content analytics tool` | 28.8 | 16 | 0 |
| `content analytics tools` | 25.6 | 7 | 0 |
| `content analytics platform` | 25.0 | 1 | 0 |

The 20-position spread between modifier-bearing queries ("comparison") and bare-entity queries is the signature.

## Diagnostic Interpretation

- **Strong "comparison" position** → the page has competitor names, contrast structures, decision tables — Google parses it correctly as a comparison asset.
- **Weak bare-tool position** → the page never tells Google what category of thing it's about at the entity level. The H2s may mention the term but as descriptive labels, not definitions.

The ranking delta points to a gap in foundational semantic structure, not missing comparison content.

## The Fix (Additive, Low-Risk)

Three edits that lift category-query ranking without disturbing comparison-query ranking:

### 1. Entity-Definition Lead Sentence
Place in the page-header/lede paragraph — explicit `"A [term] is software that measures X — and Y."` as the opening statement. Everything else follows. This is the semantic anchor Google needs to position the page for bare-entity queries.

### 2. Semantic-Sibling Sentence
In body H2 #1, pre-emptively name the variants Google is also surfacing (`platform`, `software`, `system`). Prevents query-cluster fragmentation and signals you own the full semantic family.

### 3. New FAQ + Matching FAQPage JSON-LD
Create `"What is a [term]?"` Q&A. Schema markup is the dominant featured-snippet signal for category definition queries.

## What NOT to do

- **Do not change** the title tag
- **Do not change** the H1
- **Do not change** the meta description
- **Do not restructure** existing H2s

These surfaces protect the existing "comparison" ranking. The diagnostic-and-fix is **entirely additive**.

## Validation Pattern

Run COS `analyze_full` on the additions (excerpt path, ~2–3K chars). Expected signals:
- **Curiosity:** 8–9 (new definitional content should intrigue)
- **Coherence:** 8–9 (definitions are tight structures)
- **Big Five:** Stable (additions should preserve voice)

**Strategic Clarity** may dip in the excerpt due to CTA absence in the slice; this is a slicing artifact, not a signal about the full page.

## Expected Lift and Timeline

- **Position improvement:** pos 25–28 → pos 15–20 over 4–6 weeks as Google re-crawls and resurfaces the entity definition
- **Comparison query:** stays stable or improves
- **Click lift:** contingent on CTR improvements to the snippet; position alone is not sufficient

## When This Diagnostic Applies

- Pages where you have a clear position gap between modifier + bare queries
- Category or product-type pages (tools, platforms, frameworks)
- Pages already ranking on page 1 for narrow modifiers (the foothold exists; the gap is in semantic breadth)
- Situations where you're competing in a growing category (AI Overviews, emerging problem classes)

## When This Diagnostic Does NOT Apply

- **Pages already at pos 1–5 for both bare and modifier queries** — position improvements have diminishing CTR returns; focus on snippet optimization and SERP feature positioning instead
- **Bare-term query is the high-volume driver, comparison is the long-tail** — inverse problem. Diagnose with the same position-gap data shape, but apply a different fix (add comparison content instead of definition content)
- **Bare-term queries are zero-intent** (people searching just the word, not the problem) — no entity definition will help; these are usually brand/navigation queries the domain has zero chance to rank for
- **The page is page 3+ on both** — not a gap problem; this is an authority/relevance problem. Add backlinks or deepen content before tweaking copy

## Related Session Artifacts

- Commit `a80e10b` — site(content-analytics-tools): add entity definition + 6th FAQ to lift bare-tool queries
- GSC query script at `/tmp/gsc-query.py` (service account at `~/Scripts/sem-tools/gsc-credentials.json`)

## Source Context

Diagnostic derived from 2026-05-20 content-analytics-tools SEO optimization session. The pattern surfaced when analyzing GSC 90-day query performance and noticed the 20-position gap between comparison and bare-entity queries on the same page. Root-cause analysis (reading competitor pages, Google's entity-definition signals, and featured-snippet structure) pinpointed the missing semantic anchor. Fix applied and validated with COS analyze_full. Reuse value: applicable to any category-comparison page where bare-entity queries underperform; common in product categories, tool taxonomies, and emerging-problem spaces.
