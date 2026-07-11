---
title: HTML + Chrome headless as the preferred replacement for SVG in mobile-first infographics
source_mode: builder
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.95
staleness_risk: stable
importance: 4
pinned: false
created: 2026-07-10
domain: patterns
topic: image-generation
tags: html, css, infographic, mobile-legibility, architecture, svg, screenshot
related_entries:
  - patterns/2026-06-19_brand-asset-generation-4-layer-system.md
  - patterns/2026-05-30_chrome-mcp-verified-owner-api-alternative.md
revises:
  - patterns/2026-06-29_headless-chrome-html-png-pipeline-text-heavy-social-infographics.md
---

# HTML + Chrome Headless as the Preferred Replacement for SVG in Mobile-First Infographics

## Decision

When producing mobile-first infographic cards (LinkedIn, Instagram, feed posts), prefer HTML+CSS rendered via Chrome headless screenshot over hand-authored SVG.

## Why SVG Breaks Down for Text-Heavy Infographics

SVG text requires hand-computing every line break via `<tspan dy="...">` offsets. There is no native text wrapping — the author must know in advance how many characters fit per line at a given font size and viewBox scale. This makes iterating on copy fragile: changing one word can misalign every line below it. Multi-column layouts, chip rows, and body paragraphs all require manual re-layout on every content edit.

## Why HTML+CSS Works Better

CSS handles text wrapping natively. `flexbox` with `flex-wrap: wrap` reflows chips automatically. `line-height`, `font-size`, and `padding` are intuitive. Multi-column layouts are a two-line CSS rule. The author writes content; the browser handles geometry.

## The Pipeline

1. Author card as HTML file (1080px fixed-width `<body>`)
2. Screenshot via Chrome headless:
   ```bash
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
     --headless=new --disable-gpu --no-sandbox \
     --hide-scrollbars --virtual-time-budget=5000 \
     --screenshot=out.png \
     --window-size=1080,1350 \
     "file:///path/to/card.html"
   ```
3. Output is a pixel-perfect 1080×1350 PNG — identical to what you'd get from Figma or SVG at the same dimensions

## Scale Factor Math (Same as SVG Lint)

S = canvas_width / render_width (e.g., 1080 / 360 = 3 for LinkedIn mobile)

rendered_px = css_px / S

Examples at S=3:
- Body floor 16px rendered → 48px CSS
- Caption floor 12px → 36px CSS
- Footnote floor 11px → 33px CSS

## When This Applies

- Social assets with structured text content where rendering fidelity matters more than stylistic variation: scorecards, before/after comparisons, list infographics, quote cards, personality trait cards, multi-column breakdowns
- Workflows that produce >3 social assets per week with consistent brand identity (the HTML template becomes a permanent reusable asset)
- Cases where the operator wants exact-typography control (font weight, letter-spacing, line-height) that diffusion models can't honor
- Multi-aspect-ratio output (1080×1350 portrait + 1080×1080 square) from the same content — write two templates or use CSS media queries; render twice

## When This Does NOT Apply

- Photographic or naturalistic imagery (use diffusion)
- Generative or abstract art where the visual itself is the value
- Animated content (CSS animations in Chrome headless are inconsistent)
- When the output needs to be an actual SVG file (e.g., for web embedding)
- Cases where the operator needs interactive elements (headless render completes; no JS-dependent visuals unless JS finishes inside `--virtual-time-budget`)

## Design Notes from Production

- **Fonts:** Google Fonts loaded inline via `<link rel="stylesheet">` is reliable inside `--virtual-time-budget`. Anton + Inter + JetBrains Mono covered: heavy display title, clean body, monospace accents
- **Palette:** Navy `#1a2138` background + one accent color (red `#e84a3a` / green `#3ec97d` / orange `#ff8a3c`) reads well in social feeds. Cards on white background with light gray `#f4f4f4` for sub-rows
- **Aspect ratios:** 1080×1350 for FB/IG/LinkedIn portrait; 1080×1080 for X/Bluesky/IG square. Separate HTML files with adjusted padding/sizing rather than CSS media queries kept each render predictable
- **Square version trap:** When porting a portrait design to square, naive resize leaves whitespace at the bottom. Fix by scaling card padding + font sizes proportionally so content fills the canvas. Apply `justify-content: space-between` on the body flex column if cards still float to the top
- **Text-fitting limit:** Longest example phrase determines max font size. Render at the proposed size, check for wrapping on the longest content, dial back if needed. Manual iteration is faster than algorithmic fit because the visual judgment is "does this still hit hard?" not just "does it wrap?"
- **Reusable templates:** Keep the body content in clearly-marked sections so future swaps are trivial. The structure (header → cards → footer) and CSS stay; only the inner text changes

## Grounding

Validated by building a complete production pipeline: 5 HTML templates + 4 live infographic cards (Promotion vs Prevention series for SEMalytics). All cards rendered correctly at 1080×1350 at S=3 (scale factor 3x). The SVG variants of the same cards required significantly more authoring effort for identical visual result. Screenshots archived at `~/Scripts/semalytics-gtm/wiki/drafts/2026-07-01_bvt-card*.html` (source templates). Render times ~1–2 seconds per asset. File sizes 85–155 KB.

## Source Context

Originated in the leonardo-html-infographic-skill development for SEMalytics GTM campaign, 2026-07-10. Supersedes earlier 2026-06-29 entry with higher grounding validation (0.95 vs 0.85) from additional production runs and PvP card series completion.
