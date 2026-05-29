---
title: Multi-dimensional UNIQUE + schema-defaults = silent dimension flattening
source_mode: debugger+builder
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-25
domain: debugging
topic: root-cause-analysis
tags: quality-gate, empirical, api
related_entries: []
---

# Multi-dimensional UNIQUE + schema-defaults = silent dimension flattening

## Problem

A common SQL schema pattern: define a `UNIQUE(a, b, c)` constraint on a table to express "rows are uniquely identified by the tuple (a, b, c)." Columns `b` and `c` get sensible defaults (`'United States'`, `'en'`, `0`, etc.) to make basic INSERTs easy.

The latent bug: when an INSERT statement OMITS columns `b` and `c` (relying on schema defaults), every such insert lands at the *default* values for those columns. If the caller's data actually varies across `b` and `c` — e.g., a keyword that should be tracked at multiple geographies — the data silently collapses to a single "default" row. The UNIQUE constraint correctly prevents true duplicates, but the underlying dimensionality is lost.

This bug is **invisible** until somebody actually populates the data along those omitted dimensions. The schema looks correct, the inserts succeed, the UNIQUE constraint enforces "uniqueness," and yet the table can never hold the multi-dimensional data the schema was designed for.

## When This Applies

- During code review of any INSERT statement against a table with a multi-column UNIQUE.
- When a feature adds a new dimension (e.g., per-location, per-device, per-language) to existing data and the storage layer "doesn't need changes."
- During schema audits — grep for INSERTs targeting tables whose UNIQUE has 3+ columns and verify all are written explicitly.
- When actual row dimensionality mysteriously remains flat despite the schema supporting a broader space.

## When This Does NOT Apply

- Tables with single-column UNIQUE (a primary key on `id` with no other UNIQUE) — no dimension to flatten.
- Tables where the "default" really is intended to be the only valid value for that column.
- Cases where the schema is correctly designed and all INSERT sites are known to supply all UNIQUE columns explicitly.

## Defensive Rule

**When a table has `UNIQUE(a, b, c, ...)`, every INSERT must explicitly write every column in that constraint.** Don't rely on schema defaults to fill in dimension columns. If callers don't always know `b` and `c`, design the function signature to require them; if they truly default in some contexts, set the defaults *in the caller* and pass them through explicitly so the INSERT statement remains complete.

A weaker but still useful version: when adding a column to an existing UNIQUE constraint via migration, audit every INSERT site against that table for explicitness on the new column.

## Grounding (sem-tools session 2026-05-25)

### Schema Definition

```sql
CREATE TABLE sem_keyword_metrics (
    keyword TEXT NOT NULL,
    location TEXT DEFAULT 'United States',
    language TEXT DEFAULT 'en',
    monthly_volume INTEGER,
    cpc REAL,
    competition TEXT,
    ...
    UNIQUE(keyword, location, language)
);
```

### Original Buggy INSERT

File: `KeywordIntel._store_metrics`

```python
INSERT INTO sem_keyword_metrics
   (keyword, monthly_volume, cpc, competition, competition_index, trend_data, refreshed_at)
   VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(keyword, location, language) DO UPDATE SET ...
```

The INSERT omits `location` and `language`. The UNIQUE constraint references them. Every row lands at `location='United States'`, `language='en'` (the defaults).

### Why the Bug Was Invisible

The bug was invisible for months. The schema *clearly* intended to support multi-location tracking — that's literally why the columns and the UNIQUE existed. But no caller was populating non-default values, so the inserts looked fine. The flatness was inferred from the schema not actually working that way — but no one looked.

### Bug Exposure

The bug was exposed only when ZIP-level keywords were added to `seo_keywords` (a sibling table) on 2026-05-24. The expectation was that `sem_keyword_metrics` would now hold per-ZIP volume rows. It did not — every refresh still wrote to the same `location='United States'` row, overwriting any prior values.

The mismatch between what the schema promised (per-location support) and what the data actually contained (all locations flattened to one default) became undeniable only when a downstream consumer tried to *use* that dimensionality.

### The Fix

```python
INSERT INTO sem_keyword_metrics
   (keyword, location, language,    -- explicit
    monthly_volume, cpc, competition, ...)
   VALUES (?, ?, ?, ?, ?, ?, ...)
```

And the caller now passes `location` and `language` through from the grouping in `refresh_metrics`.

## Detection Method

```sql
-- Inspect actual dimensionality
SELECT location, COUNT(*) FROM sem_keyword_metrics GROUP BY location;
-- If output is all one location despite the schema supporting many, suspect the bug.
```

Combine with a grep for INSERT statements against the suspect table and inspect column completeness.

## Anti-Patterns

- "I'll just rely on the schema defaults for `b` and `c` — they're stable values." (Until they aren't.)
- Defining a UNIQUE across columns the storage layer doesn't actively populate. The constraint is a *contract*; INSERTs are the *enforcement of the contract on the data side*.
- Treating the existence of a UNIQUE as evidence the table is being used multi-dimensionally. Inspect actual row contents (`SELECT DISTINCT location FROM table`) to verify dimensionality is real.
- Adding a new dimension to a table without auditing all existing INSERT sites to confirm they now pass the new dimension explicitly.

## Source Context

Discovered during debugging a data mismatch in sem-tools keyword intelligence pipeline (2026-05-25). `sem_keyword_metrics` table had a multi-column UNIQUE constraint supporting geography + language variations, but the primary insert path was omitting those columns, causing all keywords to collapse to the default location+language. The bug went undetected until a downstream query tried to use geography-level metrics.

This is a general pattern, not sem-tools-specific. It applies to any multi-dimensional data model where the storage layer uses UNIQUE constraints with defaults.
