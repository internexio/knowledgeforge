---
title: parsed_at_least_one — Boolean flag for empty-list-safe streaming JSON decode loops
source_mode: debugger
novelty_type: new_pattern
grounding_score: 0.90
staleness_risk: stable
importance: 3
pinned: false
created: 2026-08-03
domain: debugging
topic: error-classification
tags: [error-classification, quality-gate, grounding]
related_entries: []
---

# parsed_at_least_one — Boolean flag for empty-list-safe streaming JSON decode loops

## Problem

When a JSON decoder loop uses `if not all_items:` to detect parse failure, it produces a false positive when the decoded JSON is an empty list (`[]`). The parse succeeded, but the empty list is falsy — so the error path fires anyway.

This bug surfaced in `[project]/iteration_loop/workers/project_reviewer.py` (bead [project]-xk03): Claude returned `[]` followed by prose commentary, which is valid output (no findings). The `if not all_items:` guard fired, logged a spurious JSON parse error, and returned `([], 0.0)` as if parsing had failed.

## Solution: `parsed_at_least_one` boolean

Track decode success with a separate boolean, independent of the decoded collection's content:

```python
decoder = json.JSONDecoder()
all_items: list[Any] = []
parsed_at_least_one = False  # track success separately from list length
remainder = output.strip()

while remainder:
    try:
        doc, idx = decoder.raw_decode(remainder)
    except json.JSONDecodeError as exc:
        if not parsed_at_least_one:
            # No successful decode yet — real parse failure
            print(f"JSON parse error: {exc}", file=sys.stderr)
            return [], 0.0
        # At least one JSON value decoded; non-JSON tail is model commentary
        break
    parsed_at_least_one = True
    if isinstance(doc, list):
        all_items.extend(doc)
    remainder = remainder[idx:].lstrip()
```

## When This Applies

- Any loop that progressively decodes multiple JSON values from a single string (e.g., `JSONDecoder.raw_decode` in a `while remainder:` loop)
- When the decoded collection can be legitimately empty (e.g., "no findings" = `[]`)
- When the string may contain non-JSON trailing content (model commentary, whitespace)

## When It Does NOT Apply

- Single-shot `json.loads()` calls (no loop, no trailing content)
- Schemas where an empty result is always a failure (use the list check directly)
- When you control the full output format and empty lists cannot be valid output

## Anti-Pattern

```python
# WRONG: fires on legitimate empty-list parse success
if not all_items:
    return [], 0.0
```

## Grounding

Verified 2026-08-02 in `[project]/iteration_loop/workers/project_reviewer.py` commit f487967 (bead [project]-xk03). The bug was triggered by `claude --print --json-schema` returning `[]` + prose when no findings were detected for a project — a common, valid output from LLM-powered workers.

## Source Context

Source session: [project]-session-2026-08-02-reflect. The bug was discovered during iteration-loop worker refinement when the project-review pass was returning false-positive parse errors on valid empty-findings output.
