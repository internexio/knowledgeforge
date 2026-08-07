---
title: WebFetch returns typographically transformed content — not safe for verbatim jobs
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.70
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-27
domain: integration
topic: external-tools
tags: [empirical, grounding]
related_entries: ["integration/2026-07-27_ghost-canonical-cross-post-workflow-substack-republish.md"]
---

# WebFetch Typographic Transformation Caveat

## Problem

The WebFetch tool fetches a URL, converts HTML to markdown, and runs an AI model over the result. During this pipeline, typographic characters can be altered or normalized. In at least one confirmed case, the Substack CDN (or the WebFetch processing layer) returned content where em dashes (`—`) were present in the output, but the actual live page used period-separated sentences with no em dashes.

The operator corrected the output mid-session and provided the accurate verbatim text. The discrepancy was discovered only because the operator had the live page available for comparison.

## When This Matters

- Any task where the fetched content must be reproduced verbatim (republishing, cross-posting, legal/compliance copy)
- Tasks where punctuation style carries meaning (em dashes vs. periods changes sentence rhythm and voice)
- Tasks where the output is compared against the live page by the operator or a reader

## When It Does NOT Matter

- Summarization or extraction tasks where exact punctuation is irrelevant
- Research and synthesis tasks using WebFetch as a signal source, not a transcription source

## Root Cause (Uncertain)

The transformation could originate from:
1. The HTML-to-markdown conversion layer in WebFetch
2. The AI model summarizing or rewording during extraction
3. Substack's CDN serving cached/formatted variants with different typography
4. The AI prompt instructing "verbatim" may not be honored at the character level

The exact cause was not isolated in this session. The effect is confirmed.

## Mitigation

For verbatim content jobs:

1. **Treat WebFetch output as a first draft, not a source of record**
2. **Have the operator verify against the live page**, or provide the accurate text directly
3. **If the operator provides a correction, accept it without debate** — they have ground truth
4. **When constructing HTML for republishing, flag any em dashes for operator review** before publishing

## Specifics for Cross-Posting Workflows

When republishing a Substack post to Ghost:

- After fetching via WebFetch, manually spot-check the live Substack post for em dashes, curly quotes, and sentence structure
- If the fetched output differs from the live page, use the live page as authoritative
- Ghost `feature_image_alt` text should be verified separately (191-char hard limit; see companion integration entry on this constraint)
- The canonical URL step (pointing back to Substack) remains correct regardless of typography discrepancies in the body

## Grounding

Confirmed on 2026-07-27 during cross-posting of "The Scores Improved. The Results Got Worse." (dpsea.substack.com → internexio.com/blog). WebFetch returned content with em dashes throughout; the live Substack post used period/comma constructions instead. Operator provided the accurate text and the Ghost post was updated accordingly. One full republish cycle was wasted due to this discrepancy.

Likely other Substack posts and external platforms may exhibit the same pattern, but only this one instance has been verified.

## When This Applies

- Cross-posting workflows (Substack → Ghost, Medium → custom blog, etc.)
- Content republishing for SEO canonicalization
- Verbatim transcription tasks where typography is a content signal
- Legal, compliance, or brand-voice documents where punctuation carries meaning

## When This Does NOT Apply

- Summarization tasks where the fetched content is rewritten anyway
- Analysis or extraction tasks that don't require verbatim reproduction
- Single-source research where the fetched content is treated as a signal, not a transcript

## Source Context

This diagnostic is a follow-up to the companion entry on Ghost canonical cross-post workflows. The cross-post entry references this caveat in passing; this entry expands the caveat into a standalone diagnostic for reuse across any verbatim content job, not just cross-posting.
