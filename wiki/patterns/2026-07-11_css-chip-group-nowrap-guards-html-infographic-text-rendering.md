---
title: CSS chip-group pairing and nowrap guards for HTML infographic text rendering
source_mode: builder
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.92
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-11
domain: patterns
topic: validation
tags: quality-gate, api
related_entries:
  - patterns/2026-06-29_headless-chrome-html-png-pipeline-text-heavy-social-infographics.md
---

# CSS Chip-Group Pairing and Nowrap Guards for HTML Infographic Text Rendering

## Problem

When rendering HTML infographic cards at fixed width (e.g. 1080px), two distinct text rendering failures appear:

1. **Chip triplets split across rows.** A row of role chips (e.g. [CFO] [Legal] [Security] [Procurement]) fills one row and the last chip wraps alone to the next row — visually orphaned and harder to read. The browser doesn't know which chips are semantically paired.

2. **Hyphenated compound words split at the hyphen.** CSS treats `-` as a valid line-break opportunity by default. Words like `prevention-oriented` render as `prevention-` on one line and `oriented` on the next. This looks like a typo and breaks readability. `hyphens: none` in the CSS reset suppresses *auto-hyphenation* (browser-inserted hyphens on long words) but does NOT prevent breaks at existing hyphens in the source text.

## Solutions

### Chip-group pairing

Nest chips that must stay together in a `.chip-group` container. The outer container wraps; the inner group never splits.

```css
.chips      { display: flex; flex-wrap: wrap; gap: 10px; }
.chip-group { display: flex; flex-wrap: nowrap; gap: 10px; }
```

```html
<div class="chips">
  <div class="chip-group">
    <span class="chip">CFO</span>
    <span class="chip">Legal</span>
  </div>
  <div class="chip-group">
    <span class="chip">Security</span>
    <span class="chip">Procurement</span>
  </div>
</div>
```

The outer `.chips` flex container wraps at group boundaries. Chips within a `.chip-group` are held together by `flex-wrap: nowrap`. If a group doesn't fit on the current row, the entire group wraps to the next row together.

### Nowrap guard for hyphenated words

Two-part fix: CSS reset + utility class.

```css
/* In global reset */
*, *::before, *::after { hyphens: none; }

/* Utility class */
.nowrap { white-space: nowrap; }
```

Then wrap any hyphenated compound word that should not line-break:

```html
<span class="nowrap">prevention-oriented</span>
```

`hyphens: none` kills auto-hyphenation (browser inserting hyphens on overflow). `.nowrap` prevents breaks at existing hyphen characters. Both are needed; neither alone is sufficient.

## When This Applies

- Any HTML infographic with chip/tag rows (role tags, category labels, feature tags)
- Any compound adjective that would look broken if split: prevention-oriented, promotion-focused, data-driven, etc.
- Apply `.nowrap` proactively to all hyphenated terms at authoring time, not reactively after seeing a break
- Fixed-width layouts at standard social media dimensions (1080px)

## When This Does NOT Apply

- Single chips that stand alone (no pairing logic needed)
- When you *want* chips to wrap individually (e.g. a long list where each chip is independent)
- Responsive layouts where breakpoint-driven reflow is preferred over layout constraints

## Grounding

Both patterns were discovered iteratively while building the PvP card series for SEMalytics (4 LinkedIn infographic cards rendered via headless Chrome). The chip-group fix was required on `tpl-comparison.html` when [CFO][Legal][Security] filled a row and [Procurement] orphaned alone. The nowrap fix was required on `tpl-stat-card.html` when "prevention-oriented" split across two lines. Both fixes verified with Chrome headless screenshots at 1080×1350 and 1080×1080 viewport dimensions. Patterns are now encoded in SKILL.md for the `leonardo-html-infographic` skill at `~/Scripts/leonardo-skills/`.

## Source Context

Discovered during SEMalytics GTM infographic card authoring (leonardo-html-infographic-skill-pvp-cards session). These patterns became concrete when the second and third card templates exhibited layout failures that straightforward flex sizing couldn't resolve. The patterns are now part of the skill's canonical template documentation, ready for reuse on future card batches.
