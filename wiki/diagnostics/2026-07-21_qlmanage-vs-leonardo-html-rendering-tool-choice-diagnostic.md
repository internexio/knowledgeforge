---
title: Use leonardo-html-infographic skill (Chrome headless) not qlmanage for HTML-to-PNG rendering
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-07-21
domain: diagnostics
topic: tool-evaluation
tags: infographic, html-rendering, chrome, leonardo, qlmanage, image-generation, tooling
related_entries:
  - patterns/2026-06-29_headless-chrome-html-png-pipeline-text-heavy-social-infographics.md
  - diagnostics/2026-07-11_chrome-headless-screenshot-full-page-height-min-height-gotcha.md
  - patterns/2026-07-11_css-chip-group-nowrap-guards-html-infographic-text-rendering.md
---

# Use leonardo-html-infographic Skill (Chrome Headless) Not qlmanage for HTML-to-PNG Rendering

## Rule

For HTML-to-PNG rendering of infographic cards, use the `leonardo-html-infographic` skill's screenshot script (Chrome headless) instead of qlmanage (macOS QuickLook).

## qlmanage Failure Mode

qlmanage has an effective viewport limit of approximately **1024px width**. HTML cards wider than ~1024px render with the right side truncated — content outside the viewport is clipped and does not appear in the output PNG. This affects any two-column infographic at standard social card widths (1200×628, 1080×1350, etc.).

Symptoms:
- Right column of a two-column layout is missing or partially cut off in the PNG output
- The PNG dimensions appear correct but content is clipped
- Adding viewport meta tags (`<meta name="viewport" content="width=1200">`) does not fix it

Attempted workarounds that did NOT fix qlmanage truncation:
- Reducing card width from 1200px to 1140px
- Adding viewport meta tag
- Rendering at 2× scale

## Chrome Headless (leonardo Skill) — The Correct Path

Script location: `~/.claude/skills/leonardo-html-infographic/scripts/screenshot.py`

Usage:
```bash
python3 ~/.claude/skills/leonardo-html-infographic/scripts/screenshot.py card.html \
  --width 1200 --height 628 \
  --output output.png
```

Requirements for the HTML file:
- Set `html, body { width: [W]px; height: [H]px; overflow: hidden; }` to match `--width`/`--height`
- Set `.card { width: [W]px; height: [H]px; }` to match
- Mismatch between HTML dimensions and `--width`/`--height` causes incorrect scaling

Chrome binary: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` (macOS default)

## Canvas Conventions (from leonardo Skill)

| Format | --width | --height |
|--------|---------|----------|
| Twitter/OG card | 1200 | 628 |
| LinkedIn feed (4:5) | 1080 | 1350 |
| Square | 1080 | 1080 |
| Stories | 1080 | 1920 |

## Fallback Hierarchy (If Chrome Headless Also Unavailable)

1. PIL/Pillow direct drawing (works but unicode arrows render as □ boxes in default PIL font)
2. puppeteer / playwright (not installed in this environment as of 2026-07-21)

## When This Applies

- HTML-to-image rendering for social media cards, quote cards, comparison grids, before/after infographics
- Any two-column or multi-column layout wider than ~1000px
- Workflows that require exact canvas dimensions and no truncation

## When This Does NOT Apply

- Photographic or naturalistic imagery (use diffusion models)
- Cases where qlmanage's limitations are acceptable (images narrower than 1024px)
- Workflows with no access to Chrome binary on target system

## Related Patterns

The broader context for this tool choice is documented in:
- `patterns/2026-06-29_headless-chrome-html-png-pipeline-text-heavy-social-infographics.md` — full pattern and design notes
- `diagnostics/2026-07-11_chrome-headless-screenshot-full-page-height-min-height-gotcha.md` — Chrome behavior quirk (full-page vs viewport capture)

## Source Context

Verified 2026-07-21 in semalytics-gtm content ops session. qlmanage truncated right column on a 1140×600 card. Chrome headless via leonardo skill rendered the same card at 1200×628 with full content. The infographic was published to semalytics.com social channels.
