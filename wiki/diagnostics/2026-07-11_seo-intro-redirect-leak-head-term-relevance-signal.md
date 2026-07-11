---
title: SEO Intro Redirect Leak — Page Intro That Sends "What Is" Intent Elsewhere Leaks Head-Term Relevance Signal
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.80
staleness_risk: stable
importance: 4
pinned: false
created: 2026-07-11
domain: diagnostics
topic: root-cause-analysis
tags: grounding, empirical, quality-gate, semantic-search
related_entries: []
---

# SEO Intro Redirect Leak

## Pattern

A page targeting a head-term keyword (e.g., "psychographic segmentation") that opens with a sentence like:

> "For the strategic case — what psychographic segmentation is and why it matters — see the [psychographic marketing guide]."

is actively telling Google that the definitive "what is" answer for that term lives on **another URL**. This is a relevance signal leak: the page is instructing crawlers to treat itself as a partial-intent page rather than the authoritative source for the head term.

## How It Was Observed

- `/guides/psychographic-segmentation/` dropped from ranking #76–83 → not in top 100 after a repositioning change (cos-7lw, May 2026)
- Page had strong process content (4-step workflow, detailed OCEAN signal mapping) but its own intro paragraph explicitly redirected "what is" intent to `/psychographic-marketing/`
- The FAQ section at the bottom correctly answered "What is psychographic segmentation?" — but the intro neutralized the signal by disclaiming it

## Root Cause

Content authors often partition pages by content type: "this page = how-to; that page = definition." This is logical for human navigation but damages SEO for head terms, which typically have mixed intent (both "what is" and "how to"). When a page explicitly disclaims the definitional intent in its most prominent position (the intro paragraph), Google reads that as a strong signal to weight the page away from definition queries.

The harm happens because:
1. Google sees the intro paragraph first (highest-weighted text zone)
2. The intro's explicit redirect sentence is a direct relevance-signal downgrade
3. The page's substantive process content is treated as secondary (lower in the page, after the disclaimer)
4. The linked page gains authority on the term while this page loses it

## When This Applies

- Pages with mixed-intent targets: the page's H1 claims the head term, but the intro apologizes for not being the "real" authoritative answer
- Pages with strong supporting content (process, framework, detailed guidance) whose intro undermines their own authority
- Multi-page canonical sibling structures where the role partition is implicit in content, not explicit in site architecture

## When This Does NOT Apply

- Pages with genuinely narrow intent (e.g., a changelog, a tool UI page, a data export page) — forcing a definition onto these creates noise
- Pages where the "what is" intent legitimately belongs to a different URL and there's no ranking ambition for the head term
- Pages that lead with the definition first, then reference related pages (the opposite structure does not leak signal)

## Fix

1. **Lead with a 2–3 sentence definition** in the intro — before describing what the guide covers. This satisfies the "what is" intent in the page's most-weighted content zone.
2. **Remove the explicit redirect sentence** that points "what is" content elsewhere. Internal links to related pages are fine; what's harmful is the framing "the definition is on another page."
3. **The definition does not need to be long** — the intro paragraph is enough. Full definitional depth can still live on the linked page; the head-term page just needs to not disclaim it.

## Grounding

- Directly observed: `/guides/psychographic-segmentation/` was re-indexed 2026-07-10 after the fix (definition-first intro replacing the redirect sentence) was deployed
- GSC impression data (no-slash variant DOWN, slash variant UP) was already showing consolidation — confirming Google was actively recrawling the page
- FAQPage JSON-LD schema was added in the same fix; both changes deployed together, so the individual contribution is not perfectly isolated

The grounding score reflects:
- High confidence in the mechanism (Google favors definition-first intros for head terms): empirical observation + alignment with known SEO principles
- Medium confidence in the causal isolation (schema + intro + other changes bundled): rank recovery happened post-fix, but multiple factors changed in parallel

## Source Context

Observed during content audit of semalytics.com/cos guides after a repositioning campaign (cos-7lw) that consolidated two separately-developed pages targeting the same term. The intro-redirect pattern was discovered as a diagnostic explanator for why the primary page dropped from ranking range.
