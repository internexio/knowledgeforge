---
title: Headless Chrome HTML→PNG pipeline for text-heavy social infographics — diffusion-model bypass for structured layout
source_mode: builder
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-29
domain: patterns
topic: image-generation
tags: image-generation, social-assets, html-css, headless-chrome, infographics, diffusion-model-limits, brand-assets, content-workflow
related_entries:
  - patterns/2026-06-19_brand-asset-generation-4-layer-system.md
  - patterns/2026-05-30_chrome-mcp-verified-owner-api-alternative.md
---

# Headless Chrome HTML→PNG Pipeline for Text-Heavy Social Infographics

## The Pattern

When generating social media assets that are **text-heavy** (scorecards, quote cards, comparison infographics, list breakdowns, before/after grids), diffusion image models — Flux, Imagen, Nano Banana, SDXL — consistently produce garbled text at the densities these formats require. Even with strong prompts, the output is unusable for any asset where the text IS the value.

The fix: skip diffusion entirely. Author the asset as **pure HTML + CSS**, render it through **headless Chrome** at the target viewport, and screenshot to PNG. The result is reliable, reproducible, exact-typography output. The HTML file becomes a reusable template — swap the body content for the next post, re-render, ship.

## The Command

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless --disable-gpu --no-sandbox \
  --window-size=W,H --hide-scrollbars --virtual-time-budget=5000 \
  --screenshot=out.png \
  "file://absolute/path/to/template.html"
```

`--virtual-time-budget=5000` ensures Google Fonts have time to load before the snapshot. `--hide-scrollbars` prevents scrollbar artifacts at the viewport edge. The output PNG is exactly `W × H` pixels — no scaling, no DPI quirks.

## When This Applies

- Any social asset with structured text content where rendering fidelity matters more than stylistic variation per-render: scorecards, bad-vs-good comparisons, list infographics, quote cards, before/after pairs, dictionary-style breakdowns, blog-promo cards.
- Workflows that produce >3 social assets per week with consistent brand identity (the HTML template becomes a permanent reusable asset).
- Cases where the operator wants exact-typography control (font weight, letter-spacing, line-height) that diffusion models can't honor.
- Multi-aspect-ratio output (1080×1350 portrait + 1080×1080 square) from the same content — write two templates or use CSS media queries; render twice.

## When This Does NOT Apply

- Photographic or naturalistic imagery (use diffusion).
- Generative or abstract art where the visual itself is the value.
- Anything requiring stylistic variation per render — every HTML render is deterministic, by design.
- Cases where the operator needs interactive elements (use a static render path only — no JS-dependent visuals unless the JS completes inside `virtual-time-budget`).

## Design Notes from the Source Application

- **Fonts:** Google Fonts loaded inline via `<link rel="stylesheet">` is reliable inside `--virtual-time-budget`. Anton + Inter + JetBrains Mono covered: heavy display title, clean body, monospace accents. No external dependencies beyond the single fonts.googleapis.com call at render time.
- **Palette:** Navy `#1a2138` background + one accent color (red `#e84a3a` / green `#3ec97d` / orange `#ff8a3c`) reads well in social feeds. Cards on white background with light gray `#f4f4f4` for sub-rows.
- **Aspect ratios:** 1080×1350 for FB/IG/LinkedIn portrait; 1080×1080 for X/Bluesky/IG square. Separate HTML files with adjusted padding/sizing rather than CSS media queries kept each render predictable.
- **Square version trap:** When porting a portrait design to square, naive resize leaves whitespace at the bottom. Fix by scaling card padding + font sizes proportionally so content fills the canvas. Apply `justify-content: space-between` on the body flex column if cards still float to the top.
- **Text-fitting limit:** Longest example phrase determines max font size. Render at the proposed size, check for wrapping on the longest content, dial back if needed. Manual iteration is faster than algorithmic fit because the visual judgment is "does this still hit hard?" not just "does it wrap?".
- **Reusable templates:** Keep the body content in clearly-marked sections so future swaps are trivial. The structure (header → cards → footer) and CSS stay; only the inner text changes.

## Pipeline as a 3-Layer System

1. **Template (HTML/CSS)** — structure + brand identity. Stable across many posts.
2. **Content (per-post)** — the cliches, the principles, the quote, whatever the asset is showcasing. Swapped per render.
3. **Render (headless Chrome)** — deterministic. One command per output PNG.

This separation mirrors the brand-asset-generation 4-layer system (`patterns/2026-06-19_brand-asset-generation-4-layer-system.md`) but optimized for the text-heavy social subdomain where diffusion fails entirely.

## Grounding

Executed 8+ times in the source session producing 4 distinct templates × 2 aspect ratios = 8 PNGs. Operator inspected each render and approved. Templates committed to `client-project/wiki/templates/social/` (commit 5616b11) for reuse on future blog posts. File sizes 85–155 KB, render times ~1–2s per asset. Same Chrome binary path (`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`) works on macOS 14+; equivalent on Linux is `google-chrome --headless` if the binary is on PATH.

## Failure Modes Observed

- **First render with no `--virtual-time-budget`:** fonts had not loaded, text rendered in fallback system font. Always include the budget.
- **Scaling overshoot:** bumping all dimensions equally to fill square canvas caused footer credit line to clip at canvas edge. Solution: scale padding + content sizes but leave footer at original size, or use `justify-content: space-between` to push footer down.
- **Text wrap on edge cases:** "Loved your recent post about [X]." was the longest cliché tested at 42px; one more character would have wrapped. Test with the longest realistic content before locking sizes.
