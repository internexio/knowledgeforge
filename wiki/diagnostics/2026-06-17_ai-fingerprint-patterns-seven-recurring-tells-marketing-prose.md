---
title: AI Fingerprint Patterns — 7 Recurring Tells in Marketing Prose
source_mode: cos-copy
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.75
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-06-17
domain: diagnostics
topic: content-quality
tags: ai-fingerprint, content-quality, cos-copy, prose-review, de-ai
related_entries:
  - diagnostics/2026-06-16_demonstration-gap-framework-explained-never-shown.md
  - diagnostics/2026-06-16_moat-left-offstage-evidence-grounded-brand-copy.md
---

# AI Fingerprint Patterns — 7 Recurring Tells in Marketing Prose

## Scope

Across three sequential cos-copy reviews of marketing-prose pillar pages on 2026-06-17 (the cos-oh8w GEO cluster: definitional pillar, tactical playbook, ranking-factors deep-dive), the same patterns appeared in every draft. Each was flagged HIGH or MEDIUM severity by the reviewer. Pre-empting these at draft time cuts cos-copy review iteration cycles roughly in half.

This is a **quick-reference enumeration of patterns to pre-empt at draft time** — not a replacement for the cos-copy `SKILL.md` review framework (which holds the authoritative review rules and severity framework). If `cos-copy/SKILL.md` grows an explicit "patterns to pre-empt" section in future, this entry should be deprecated.

## Sibling Diagnostics

- [[2026-06-16_demonstration-gap-framework-explained-never-shown]] — about leaving the **mechanism** offstage (framework described but not enacted).
- [[2026-06-16_moat-left-offstage-evidence-grounded-brand-copy]] — about leaving the **proof asset** offstage (credentials, dataset size, evidence base).

This diagnostic operates at a lower altitude than those two: it is about sentence-level AI fingerprint tells, not strategic under-claiming of authority. A piece can be free of all seven of these and still fail Demonstration Gap or Moat Left Offstage; conversely, a piece can hit all three of those moats correctly and still read as AI-generated because of the seven tells below.

## The 7 Recurring Patterns

### 1. Tricolon-then-punchline

Three parallel-structured sentences setting up a fourth-sentence payoff. Example:

> *"A page that wins retrieval but loses citation ranking doesn't show up. A page that wins both but has no extractable passage gets summarized away. A page that supplies the passage but isn't a recognizable source might be paraphrased without attribution. The pages that win all four are the ones that get cited by name."*

**Why it's a tell:** the parallel construction reads as deliberate persuasion architecture. Real practitioner prose mixes sentence types within a paragraph.

**Fix:** keep one contrast example + the punchline; cut two of the three setups.

### 2. "X is not Y, it's Z" formula

Inversion-then-correction. Example: *"Citable structure is a content discipline, not a markup hack."* / *"GEO is not SEO 2.0; it's a different optimization target."*

**Why it's a tell:** widely cited as the most over-used AI rhetorical pattern.

**Fix:** convert to a direct claim or drop entirely if the inversion adds nothing.

### 3. Unanchored "Most teams..." weasel

Generic claims about audience behavior without grounding. Example: *"Most teams already know GEO matters; they don't know what to fix first."* / *"Most teams find at least one fix worth shipping."*

**Why it's a tell:** assertion of authority without evidence. Real operator prose names specific examples or sources.

**Fix:** either source it ("Of the first 50 audits we ran, 47 surfaced a llms.txt issue") or drop the clause and let the actionable second half stand alone.

### 4. Header restatement in opening sentence

The first paragraph of a section begins by restating the H2 in different words. Example: H2 reads "GEO vs SEO — the practical difference"; the next paragraph opens *"Search engine optimization and generative engine optimization aren't competing disciplines."* Same content, twice.

**Why it's a tell:** AI models often re-establish topic for the model's own coherence; humans don't need to re-orient the reader who just read the header.

**Fix:** start the section with a sentence the header didn't already imply.

### 5. Marketing-deck phrases

Phrases that read like slide copy, not practitioner prose. Recurring offenders:

- "content posture" / "marketing posture"
- "in its own right" / "marketing outcome in its own right"
- "the strategic answer is to..." (hedge-as-bravery preamble before giving advice)
- "the bottom row is the strategic shift" (slide-deck framing of a comparison table)
- "citation candidacy" / "anchors the entity engines are scoring"

**Why it's a tell:** these compose well in PowerPoint headers but slow down on-page reading.

**Fix:** swap for the concrete mechanism (e.g., "treating citation-without-click as a win, not a failure mode").

### 6. Self-referential "This page does it" tic

The writer breaks the fourth wall to point at their own structure as a demonstration. Example: *"This page does it — every section opens with the action, then the rationale."*

**Why it's a tell:** once is a useful proof point; twice across a cluster becomes a fingerprint, because the meta-commentary is the same move done twice.

**Fix:** use at most once per cluster, and only when the demonstration is load-bearing (e.g., on a Quotability section that argues for the structure the page itself uses). For all other instances, the structure proves itself by existing.

### 7. Closing-sentence summary restatement

Section ends with a sentence that summarizes the section. Example: *"A page that looks anonymous gets paraphrased; a page that looks like a credible source gets cited by name."* (after a paragraph that already listed the credibility signals)

**Why it's a tell:** AI models close paragraphs by recapitulating the topic sentence. Human writers either let the last concrete claim stand or shift to a forward-pointing implication.

**Fix:** cut the summary closer. If a real punctuation is needed, swap to a directive ("Floor: byline, date, and at least one cited source") or to a stake ("Anonymous pages don't get cited by name — period.")

## How to Use This

**Pre-deploy audit, after drafting:**

- grep your draft for: `"Most teams"`, `"in its own right"`, `"content posture"`, `"the strategic answer"`, `"This page does it"`
- read paragraph-final sentences for restatement
- count tricolon parallel-structure paragraphs (3+ identical openers in sequence)
- cos-copy review will catch what self-audit missed — but pre-empting these typically reduces findings from 11-12 per page to 3-5

## Concrete Grounding (2026-06-17)

Patterns observed across three cos-copy reviews:

- **cos-rgvx review**: 12 findings, 4 HIGH (incl. all 7 patterns visible: tricolon, weasel, marketing-deck "content posture")
- **cos-sbf4 review**: 11 findings, 2 CRITICAL (incl. self-referential clone of cos-rgvx, tricolon in FAQ)
- **cos-r0fp review**: 12 findings, 3 HIGH (incl. cross-sibling clone, weight-note triple-stamp)

Live evidence pages:

- `semalytics.com/guides/what-is-generative-engine-optimization/`
- `semalytics.com/guides/how-to-rank-in-ai-overviews/`
- `semalytics.com/guides/ai-search-ranking-factors/`

## What This Is NOT

This is NOT a replacement for cos-copy `SKILL.md` (which holds the authoritative review rules and severity framework). This is a quick-reference enumeration of patterns to **pre-empt at draft time** so cos-copy reviews surface novel issues rather than repeating the same flags. If `cos-copy/SKILL.md` grows an explicit "patterns to pre-empt" section in future, this wiki entry should be deprecated.

## Staleness Note

LLM output patterns shift as models evolve. These are 2025-era patterns documented in mid-2026; expect drift over 12-24 months as models change defaults and as the patterns themselves become widely-known-and-deliberately-avoided. Revisit if cos-copy reviews start surfacing a different set of recurring tells.
