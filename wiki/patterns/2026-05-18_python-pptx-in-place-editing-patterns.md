---
title: python-pptx in-place editing patterns for cleaning shipped decks
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-05-18
tags: patterns, infrastructure, python, pptx, content-pipelines, tooling
related_entries: []
---

# python-pptx in-place editing patterns for cleaning shipped decks

When you need to apply targeted edits to a .pptx file without redesigning it from scratch (e.g., strip named references, swap a row in a competition table, replace a slide section), python-pptx supports five core operations that together cover ~80% of editorial cleanup work. Use these in preference to wholesale slide regeneration when the deck has visual design you want to preserve.

## Pattern 1: Inspect shape geometry before editing

Always dump the shape index, position, size, and text first. The same slide will have many text boxes and rectangles; mistakes come from editing the wrong one. Example output format:

```
[idx] L={inches} T={inches} W={inches} H={inches} | {first 80 chars of text}
```

Repeat for every slide you plan to touch. Without this map, edit instructions are guesses.

## Pattern 2: Edit text in place, preserving formatting

The naive approach (`shape.text_frame.text = "new text"`) wipes formatting. Instead, work at the run level:

```python
def replace_text_preserving_format(shape, new_text):
    tf = shape.text_frame
    first_para = tf.paragraphs[0]
    if not first_para.runs:
        first_para.add_run()
    first_run = first_para.runs[0]
    # Remove all but first run in first paragraph
    for run in first_para.runs[1:]:
        run._r.getparent().remove(run._r)
    # Remove all other paragraphs
    for para in tf.paragraphs[1:]:
        para._p.getparent().remove(para._p)
    first_run.text = new_text
```

This keeps the font, size, color, and weight of the first run. Lossy for multi-run formatting (e.g., a sentence with a bold word in the middle), but acceptable for most text-block edits.

## Pattern 3: Delete a shape

python-pptx has no first-class `delete()` method on shapes. Manipulate the XML directly:

```python
shape_element = shape._element
shape_element.getparent().remove(shape_element)
```

When deleting multiple shapes from a single slide, collect them first and delete in REVERSE index order — deleting earlier indices invalidates the later ones.

## Pattern 4: Resize/reposition

Set `.top`, `.left`, `.width`, `.height` directly with `Inches(N)` or `Emu(N)` units. Example to match the height of one rectangle to another:

```python
target_h = source_rect.height  # EMU value
other_rect.height = target_h
```

EMU = English Metric Units; 914400 EMU = 1 inch. Use `Emu(value).inches` to read.

## Pattern 5: Add new shapes by deep-copying existing ones

The cleanest way to add a new text box with formatting matching the deck's existing style:

```python
from copy import deepcopy
src_el = existing_shape._element
new_el = deepcopy(src_el)
src_el.getparent().append(new_el)
# Then find new shape in slide.shapes by identity (sh._element is new_el)
# Reposition + replace text
```

This inherits font, color, and box styling without manually specifying them.

## When This Applies

- Shipping deck has visual design you want to preserve
- Edits are localized (text swaps, deleting a section, repositioning a box)
- You have a working python3 with `python-pptx` installed
- Backup made before destructive operations

## When This Does NOT Apply

- Wholesale slide regeneration (use Marp, Pandoc, or build from markdown)
- Heavy formatting changes (font swaps across all slides, theme overhaul)
- Tables with complex cell-level styling (python-pptx table support is limited)
- Charts that need data updates (use the underlying chart_data API, not raw text edits)

## Operational Gotchas

- PowerPoint on macOS doesn't always hard-lock the file, but it can overwrite your changes on its next save. Close the app before running edits.
- Always back up the .pptx before destructive operations. `cp` to a timestamped backup is sufficient; the file is self-contained.
- The `-Repaired.pptx` filename pattern appears when PowerPoint detects a corruption it auto-fixed. Investigate before assuming the file is healthy.

## Source Context

Pitched a deck cleanup session on 2026-05-18 with a 12-slide pitch deck requiring text replacements, shape deletions, and repositioning. Used all five patterns: text replacement on 11 slides, shape deletion (4 shapes on slide 10, 14 shapes on slide 11), resize to match sibling shape (slide 10 OPEN co-founder box), deep-copy-based shape addition (slide 11 24-MONTH VISION block). Two backups taken before destructive ops, both survived. Verification was a re-read pass with a regex scan for known offending substrings; passed 11/11 checks.
