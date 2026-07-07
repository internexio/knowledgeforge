---
title: UTM 3-tier medium taxonomy for blog-driven conversion attribution
source_mode: builder
novelty_type: transferable_framework
grounding_score: 0.75
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-06
domain: patterns
topic: synthesis
tags: analytics, attribution, UTM, blog-conversion, content-marketing, funnel-measurement
related_entries: []
---

# UTM 3-tier medium taxonomy for blog-driven conversion attribution

## The gap

When a blog post carries multiple outbound-link types (product CTAs, cross-blog nav, pillar-page nav), a flat `utm_medium=blog` doesn't tell you which LINK TYPE converted. A weekly report like "blog drove 20 tool visits" collapses three distinct funnel behaviors into one number, and the underlying content-strategy levers are not separable.

## The taxonomy

Split `utm_medium` into three fixed values based on link intent:

| Link type | `utm_medium=` | Purpose |
|---|---|---|
| Tool/product CTA | `cta` | The conversion goal — end-of-post or inline "Try it" links |
| Pillar-page navigation | `pillar` | Links from a supporting post to the topic pillar page |
| Blog-to-blog nav | `cross-link` | Related/sibling posts within the same topic cluster |

All three share:

- `utm_source=blog` — so referral-source reports separate blog traffic from social/email/direct
- `utm_campaign=<post-slug>` — so per-post ROI is measurable

## Why the split matters

Without splitting, a "blog drove 20 tool visits this week" report can't distinguish:

- 20 visits from an inline CTA (users clicked the primary conversion goal directly)
- 20 visits from a pillar-page indirect path (users went blog → pillar → CTA)
- 20 visits from cross-blog navigation (users bounced through 2–3 related posts before landing on a CTA)

Each implies a different content strategy:

- **Direct CTA clicks** → standalone posts are converting; double down on similar post shapes.
- **Pillar-mediated clicks** → the topic hub is doing the work; invest in pillar-page depth.
- **Cross-link clicks** → cluster coverage is holding attention; invest in more sibling posts inside the cluster.

Different levers. A flat `utm_medium=blog` hides which lever is available to pull.

## Example URL construction

```
Base:        https://example.com/tools/ad-copy-analyzer/
CTA link:    https://example.com/tools/ad-copy-analyzer/?utm_source=blog&utm_medium=cta&utm_campaign=prompts-that-sound-like-you
Pillar link: https://example.com/ai-copywriter/?utm_source=blog&utm_medium=pillar&utm_campaign=prompts-that-sound-like-you
Cross-blog:  https://example.com/blog/ocean-subject-line-experiments/?utm_source=blog&utm_medium=cross-link&utm_campaign=prompts-that-sound-like-you
```

## Grounded example (client-project, 2026-07-06)

Applied to two Ghost blog drafts (Tue 7/7 "Prompts That Sound Like You" and Fri 7/10 "Promotion vs Prevention"). Prior baseline: ZERO blog→tool referrals in the last 14 days per GA4. Retrofit added UTMs to every outbound blog link before publish. Week 2 checkpoint (7/19) will be the first data point measuring whether the taxonomy resolves per-medium attribution correctly.

## Application procedure

1. Before publishing a blog post, list every outbound link.
2. Classify each as `cta`, `pillar`, or `cross-link` (or if none of the three fit, extend the taxonomy — document the extension for the next post).
3. Append `?utm_source=blog&utm_medium=<class>&utm_campaign=<post-slug>` to each href.
4. Publish.
5. In analytics reports, break down by `utm_medium` under `utm_source=blog` to see which link type is doing the conversion work.

## When it does NOT apply

- Posts with only ONE outbound link — no attribution ambiguity to resolve.
- Email campaigns (different `utm_source`), social atoms (different `utm_source`), paid ads (different `utm_source`, and often `utm_medium=cpc` or ad-network-specific).
- Static-site generators or CMS platforms that mangle query strings (rare, but check).

## Cross-references

- Related: general UTM discipline — always include `utm_source` and `utm_campaign` on cross-domain / cross-property links; medium taxonomy is where teams often skip discipline.

## Note on novelty

The UTM standard itself is not novel (Google Analytics has used it since 2007). The specific 3-tier medium articulation (`cta` / `pillar` / `cross-link`) as a durable taxonomy for content-marketing attribution is what this entry captures. Some marketing blogs recommend similar splits; this articulation frames the 3-tier as the minimum useful decomposition for blog-driven funnel measurement.
