---
title: Chrome headless --screenshot captures full page height, not viewport — min-height causes non-deterministic PNG dimensions
source_mode: critic
novelty_type: reusable_diagnostic
grounding_score: 0.75
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-11
domain: diagnostics
topic: hypothesis-testing
tags: api, quality-gate, empirical, testing
related_entries:
  - patterns/2026-06-29_headless-chrome-html-png-pipeline-text-heavy-social-infographics.md
  - patterns/2026-06-19_brand-asset-generation-4-layer-system.md
---

# Chrome Headless `--screenshot` Captures Full Page Height, Not Viewport

## The Problem

Chrome headless in `--headless=new` mode with `--screenshot=output.png` captures the **full scrollable page height**, not the viewport height set by `--window-size`. This means:

```bash
chrome --headless=new --screenshot=out.png --window-size=1080,1350 card.html
```

If `card.html` has `min-height: 1350px` and content that overflows to 1600px, the output PNG will be **1600px tall**, not 1350px. The `--window-size` height only sets the viewport; it does not clip the screenshot.

## Where This Surfaces

HTML-to-image pipelines where:
- A target canvas dimension is specified (e.g., "feed card = 1080×1350px")
- The HTML scaffold uses `min-height` to ensure the card fills the canvas
- Content varies in length (e.g., user-provided copy, number of rows in a grid)
- The pipeline assumes `--window-size` controls output dimensions

Concrete context: the `leonardo-html-infographic` skill uses this exact pattern in its `screenshot.py` script and its 5 HTML templates all use `min-height` on `body` and `.card`. A role-grid card with 8 items vs 4 items would produce different PNG heights from the same `--window-size` invocation.

## The Correct Fix

Use **fixed height with overflow clipping** instead of `min-height`:

```css
/* WRONG — allows PNG height to vary with content */
body {
  width: 1080px;
  min-height: 1350px;
  overflow: hidden;
}

/* CORRECT — deterministic PNG dimensions */
body {
  width: 1080px;
  height: 1350px;        /* exact, not minimum */
  overflow: hidden;      /* clips content that exceeds canvas */
}
```

The `overflow: hidden` on a **fixed** height body tells the browser not to expand the document height beyond the specified value. Chrome's full-page capture then equals the viewport size, producing a PNG with exact target dimensions.

## Trade-off: Clipping vs. Flexibility

Fixed-height clipping means overflow content is silently cropped. For infographic workflows this is the desired behavior (content must be designed to fit the canvas). For workflows where content length is variable and must not be clipped, capture the full-page height and resize/crop as a post-processing step.

## Width vs. Height Behavior

`--window-size=W,H` correctly controls PNG **width** in both modes — content does not typically overflow horizontally when `overflow: hidden` is set. **The issue is height-only**: vertical content growth causes `--screenshot` to expand the capture.

## Grounding

Derived from code analysis of `leonardo-html-infographic/scripts/screenshot.py` and its 5 HTML templates during a critic review. The `min-height` issue identified as a Sev 1 finding. Chrome headless full-page capture behavior is well-documented and consistent across Chrome versions (grounding score 0.75 — analysis-based, not directly tested in this session; behavior is stable and widely reported in Chrome DevTools documentation and Stack Overflow).

## Related

- Chrome issue: Full-page capture is the default mode for `--screenshot`; to capture only the viewport, use DevTools Protocol `Page.captureScreenshot` with `clip` params rather than the CLI `--screenshot` flag.
- Similar issue documented in the existing `patterns/2026-06-29_headless-chrome-html-png-pipeline-text-heavy-social-infographics.md` entry, which provides the broader pattern context.

## When This Applies

Any HTML-to-image pipeline using headless Chrome with:
- Fixed target canvas dimensions
- Dynamic or user-provided content
- Requirement for consistent PNG output size across renders

## When This Does NOT Apply

- Workflows where full-page capture is desired (e.g., capturing long documents)
- Cases where post-render image resizing is acceptable
- Non-Chrome rendering engines (use engine-specific documentation)

## Source Context

Discovered during code review of `leonardo-skills` commit session (2026-07-11). The critic role identified this pattern in `leonardo-html-infographic/scripts/screenshot.py` and its associated HTML templates.
