---
title: Blog hero image pre-generation library pattern — generate all variants upfront, select retroactively
source_mode: synthesizer
novelty_type: reusable_pattern
grounding_score: 0.82
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-11
domain: patterns
topic: synthesis
tags: api, throughput, deployment, latency
related_entries: []
---

# Blog Hero Image Pre-Generation Library Pattern

## What It Is

When building a blog with AI-generated hero images, generate ALL theme × post combinations upfront rather than generating one image per post at publishing time. Selection happens retroactively based on thematic fit.

## Concrete Implementation (Grounded in KPT Session, 2026-07-10/11)

- **10 blog posts × 8 visual themes = 80 images** generated in approximately 3 batch runs
- **Themes:** switchboard, terminal blocks, rope knots, card catalog, sorting, optics, yellow pages, lock & key
- **All images stored in `/blog/images/`** with naming convention: `{post-slug}-{theme}-v1.jpg`
- **Theme selection done after the full library exists**, not before generation

## Why This Works

1. **Avoids decision bottlenecks** — you don't need to know which theme fits which post before generating. Creative direction and production are decoupled.
2. **Enables comparison** — seeing all 8 variants for a post (or the same theme across all posts) produces better thematic choices than evaluating one image in isolation.
3. **Batch generation is faster** — running 30 or 80 images in one script session is more efficient than generating 1 image per publish cycle.
4. **Future posts are already served** — when post #5 publishes, its image already exists in the library from the initial generation run.

## When to Apply

- Blog with a defined post roadmap (titles/topics known ahead of time)
- Using a batch-capable image generation API (Flux via fal-client, Imagen, DALL-E)
- Publishing cadence faster than image-generation turnaround allows per-post generation
- Want visual consistency across posts (same physical theme DNA applied uniformly)

## When NOT to Apply

- Posts are highly news-driven (topic unknown until day of publish)
- Images require post-specific content (e.g., screenshots, diagrams, data viz)
- Budget per image is high (you can't afford N×M generation cost upfront)

## Naming Convention That Makes This Work

`{post-slug}-{theme}-v1.jpg`

- Post slug matches the URL path (easy to find the right image at publish time)
- Theme in the name allows filtering: `ls *-switchboard-v1.jpg` gives you the full switchboard set
- Version suffix (v1) allows regeneration without breaking existing references

## Generation Script Pattern (Python + fal-client)

```python
SLUGS = ["exact-match-vs-phrase-match", "negative-keyword-audit", ...]
THEMES = {
    "switchboard": "telephone operator switchboard, bakelite panels, ...",
    "knots": "natural hemp rope knots, dark surface, ...",
}
for theme_name, prompt in THEMES.items():
    for slug in SLUGS:
        filename = f"{slug}-{theme_name}-v1.jpg"
        # generate and save
```

## When This Applies

- Blog roadmap is locked (post titles/topics known before generation)
- Image generation APIs support batch requests or parallel calls
- Team can afford the upfront N × M image cost in a single batch
- Visual coherence across posts is a priority

## When This Does NOT Apply

- Posts are published ad-hoc or news-driven (topics unknown until publishing day)
- Images must be post-specific (screenshots, diagrams, real photographs)
- Cost constraints require per-post generation only (budget won't cover N × M upfront)

## Composes With

- **Brand asset generation 4-layer system** (`patterns/2026-06-19_brand-asset-generation-4-layer-system.md`): The pre-generation library pattern is the workflow optimization; the 4-layer system is the quality-enforcement architecture. Use together when consistency across the full image set is critical.
- **Variant axes as temperature substitute** (`patterns/2026-06-26_variant-axes-as-temperature-substitute-content-generation.md`): If each theme represents a distinct "angle" or "personality," the multi-theme library is a concrete application of the variant-axes pattern.

## Why This Is Reusable

- The pattern is independent of image generation tool (applies to Flux, Imagen, Midjourney, DALL-E, etc.)
- The workflow optimization (batch-then-select vs generate-on-demand) is applicable to any multi-variant asset scenario (social media templates, ad creatives, illustration sets)
- The naming convention is portable and extends easily if themes or posts grow

## Anti-Pattern This Prevents

- **Per-publish generation cycles** — waiting for image generation at publish time blocks the post; if generation fails, the post must be delayed
- **Retroactive theme regret** — after selecting a theme, realizing another theme fit better, but having to regenerate
- **Single-theme monotony** — using the same visual theme across all posts because generation is expensive per-post

## Source Context

Grounded in the kpt-blog-image-theme-selection session (2026-07-10/11). Pattern emerged as a workflow organizing principle: batch API calls are cheaper per-image and faster overall than sequential per-post generation. Selection after generation decouples creative from production decisions, reducing coordination overhead.
