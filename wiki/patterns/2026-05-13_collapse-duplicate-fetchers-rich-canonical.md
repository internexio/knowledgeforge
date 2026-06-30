---
title: Collapse near-duplicate fetchers by making the rich shape canonical
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.8
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-13
domain: patterns
topic: synthesis
tags: [refactoring, duplication, fetch-pattern, single-source-of-truth, projection]
related_entries: [patterns/2026-05-13_phased-god-module-split-facade-first.md]
---

# Pattern: Collapse near-duplicate fetchers via rich-shape canonical + discard-projection wrapper

## The smell

A module has two fetcher functions that differ only in return shape:

```python
def fetch_thing_simple(...) -> str:        # 100 LOC
    # fetch from DB
    # render block
    return rendered_string

def fetch_thing_with_breakdown(...) -> dict:  # 150 LOC
    # fetch from DB (same logic)
    # render block (same logic)
    # also track per-section char counts + labels
    return {"rendered": rendered_string, "sources": [...], ...}
```

The simple one is a string-returning subset of the rich one. Every time
you add a new section (a new file type, a new reference subblock), you
have to edit BOTH. They drift.

## The fix

1. Make the rich-shape function the canonical implementation. It does the
   work and builds the full breakdown.
2. Make the simple-shape function a thin wrapper that calls the canonical
   one and discards the extra fields:

```python
def fetch_thing_simple(...) -> str | None:
    breakdown = await fetch_thing_with_breakdown(...)
    return breakdown["rendered"] if breakdown else None
```

That's the entire refactor. One source of truth, zero drift surface.

## Why this works

The rich shape strictly dominates the simple shape — every byte the
simple shape produces is already inside the rich shape's `rendered`
field. The cost of building the per-source breakdown is small (it's a
parallel list of `{label, char_count}` dicts built alongside the
rendered parts), and most callers that pay for it actually want it.

The few callers that don't want it pay a tiny dict-construction tax in
exchange for never having to coordinate two parallel implementations.

## When to apply

- Two (or more) fetchers in the same module with byte-identical fetch
  logic and shape divergence only at the return statement.
- Adding a new field to the underlying data WOULD require touching both
  fetchers.
- The richer shape is a strict superset (or near-superset) of the
  thinner shape.

## When NOT to apply

- **Cost asymmetry**: if the richer shape requires meaningfully more DB
  work or compute, callers of the thinner shape would pay for work they
  don't use. Either keep both, or parameterize what to compute.
- **Different fetch logic**: if the two fetchers actually query different
  tables or use different filters, the duplication is about reads, not
  shape — refactor the read instead.
- **Stable rich shape contract**: if the rich shape is a public API that
  external clients depend on, you can't expand it freely. Use a private
  internal function and keep two public surfaces.

## Discovery heuristic

If the audit complaint about a module mentions "X (100 LOC) and Y (150
LOC) will drift", and X's output is recoverable as `Y(...)[some_field]`,
this pattern applies.

## Grounding

Implemented in [project] as the STR-M2 refactor of
`backend/app/services/project_context.py` (1140 LOC monolith) into
`backend/app/services/project_context/`. The old file had two parallel
sync fetchers — `_fetch_and_format` (~100 LOC, returned string) and
`_fetch_with_breakdown` (~150 LOC, returned dict). They duplicated the
entire fetch + type-dispatch + reference/campaign/files append logic.

After the refactor, `fetcher.py` has one sync path `_fetch_to_breakdown`
that always builds the breakdown. `get_project_context` is now:

```python
async def get_project_context(...) -> Optional[str]:
    breakdown = await get_project_context_breakdown(...)
    return breakdown["rendered"] if breakdown else None
```

CODE_REVIEW_2026-05-12 audit (STR-M2) called this out as guaranteed
drift; the refactor eliminated ~100 LOC of duplicated fetch logic.
Commit `f961fb2` on master. All 998 backend tests pass; 3 existing
breakdown tests passed unmodified after the refactor (test patches
needed a one-line repoint — see the separate sibling wiki entry on
module→package patch-target shifts).

## Source Context

Validated during the COS STR-M2 refactor session breaking down the monolithic
`project_context.py` service into a package structure. The pattern surfaced
as an audit finding and was applied to eliminate parallel fetch/render logic
across two return-shape variants, reducing duplicated code by ~100 LOC and
establishing a single source of truth for the underlying fetch logic.
