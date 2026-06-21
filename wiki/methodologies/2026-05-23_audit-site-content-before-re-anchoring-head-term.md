---
title: Audit Existing Site Content Before Re-Anchoring to a Candidate Head Term
source_mode: builder
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: stable
importance: 5
pinned: false
created: 2026-05-23
domain: strategy
topic: trade-off-analysis
tags: quality-gate, adversarial, empirical, grounding
related_entries:
  - sem-tools/wiki/methodologies/2026-05-23_seo-repositioning-failing-rank-for-unranked-head-term.md
---

# Audit Existing Site Content Before Re-Anchoring to a Candidate Head Term

## The Failure This Prevents

You apply the trade-failing-rank repositioning pattern: a page ranks poorly for an established term, Keyword Planner research surfaces a related higher-volume LOW-comp head term, you re-anchor title/H1/meta to capture the new term. The pattern is sound.

The failure mode is choosing a candidate head term that is **already owned by another page on the same site**. The repositioning succeeds at swapping the anchor, but the new page now competes head-to-head with a sibling page Google already trusts on that term. Both pages split signal. Neither ranks well. The repositioning did not just fail to help — it actively created cannibalization where none existed.

## The Audit Step (One Command)

Before any title/H1/meta re-anchor commit, run a recursive grep for the candidate head term across the entire site tree:

```bash
grep -r -l -i "candidate head term" path/to/site/ --include="*.html"
```

For each matching file, inspect its `<title>`, `<h1>`, and `<meta name="description">`. If any other page leads with the same head term in those primary slots, abort the planned re-anchor and either:

1. Choose a differentiated head term (the page B re-anchor would then go to a smaller but uncontested keyword), or
2. 301-redirect one page to the other and consolidate, or
3. Differentiate by sub-intent so the two pages own different angles (riskier — Google often picks one anyway).

A passing audit is ALL OF: (a) no other page has the candidate head term in its title, (b) no other page has it in its H1, (c) any body-level occurrences on other pages are clearly secondary to those pages' own anchors.

## When This Audit Is Especially Important

- The site has > 50 indexed pages (large content surface = higher chance of collision)
- Multiple authors/agents have shipped pages over time (no single source of truth for what targets what)
- A `seo-keywords.md` or equivalent registry exists but may be out of date relative to actual page content
- The candidate head term is in the broad subject area the site already covers (rather than a brand-new topic)
- You are re-anchoring rather than greenfield-launching (re-anchoring is where you most often forget other pages may target the term)

## Why `seo-keywords.md` (or Equivalent Registries) Are Not Sufficient

Site keyword registries drift. A page may have been re-anchored without the registry being updated. A page may have been launched without ever being added to the registry. A page's actual on-page targeting may have evolved from what the registry records. The registry is a useful planning artifact but **NOT a substitute for grepping the live filesystem**.

Specifically: if you only check the registry and skip the file-tree grep, you can miss recently-shipped pages, ghost pages from earlier experiments, and any case where the registry was simply not updated after a content change.

## Concrete Case That Surfaced This Pattern (2026-05-23, COS / semalytics.com)

Session repositioned `cos/site/guides/personality-based-marketing-segmentation/` from "personality-based marketing segmentation" (10 vol) → "psychographic segmentation" (6,600 vol). Shipped, verified live. Two commits later, content audit during a Phase 3 expansion check revealed `cos/site/guides/psychographic-segmentation/` (a separate, well-developed page) already owned "psychographic segmentation" in its title + H1 + meta. Cannibalization created where none had previously existed.

Same-day corrective action: re-anchored Page B to "OCEAN marketing" (70 vol/mo, LOW comp, differentiated). 70 < 6,600 — the salvage anchor is much smaller than the dream anchor, but at least it doesn't compete with a sibling page. The original "psychographic segmentation" page now owns the head term cleanly.

Two same-day commits required where one well-audited commit would have done the job. Documented in cos beads as cos-7lw (initial re-anchor) → cos-6bq (corrective re-anchor) → seo-keywords.md anchor history.

## The Amendment to the Trade-Failing-Rank Pattern

The earlier pattern entry (`sem-tools/wiki/methodologies/2026-05-23_seo-repositioning-failing-rank-for-unranked-head-term.md`) lists four pre-conditions to confirm before applying the trade. This entry adds a FIFTH that should be checked BEFORE any of the others:

**0. Audit the entire site tree for existing pages that already target the candidate head term.** If any other page leads on that term in its primary slots (title/H1/meta description), do not apply the trade-failing-rank pattern with that term. Pick a differentiated candidate or pursue 301-consolidation.

Pre-conditions 1-4 (failing rank actually failing, new term genuinely unranked, thematic alignment, competition asymmetry) all assume the candidate is winnable. Pre-condition 0 establishes that the candidate is YOURS to win.

## When This Audit Is Not Strictly Necessary

- Greenfield page launch where the page is new and no other page exists yet for the subject area
- A site with a strict author / content registry process that mechanically enforces one-page-per-head-term (rare in practice)
- A site under 10 indexed pages (low enough collision risk that grep is overkill — but still cheap to run)

## Source Context

Amendment generated 2026-05-23 in the second `/kf-reflect` of the same cos-seo-pillar-repositioning session that filed the original trade-failing-rank methodology entry. The earlier entry described the pattern; this entry hardens it after a same-session failure mode demonstrated that the pattern's success is conditional on a pre-flight audit step the earlier entry did not explicitly require.
