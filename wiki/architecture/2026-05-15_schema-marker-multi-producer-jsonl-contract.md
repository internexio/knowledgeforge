---
title: Multi-producer JSONL queue — schema marker is the contract, not the filename
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.80
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-15
domain: architecture
topic: data-plane-contracts
tags: architecture, queues, jsonl, schema-evolution, multi-producer, contract-design
related_entries: ["infrastructure/2026-05-13_posix-append-pipe-buf-concurrent-jsonl-writers.md", "orchestration/2026-05-13_coalesce-at-enqueue-every-coalesce-gets-a-row.md"]
---

# Multi-producer JSONL queue — schema marker is the contract, not the filename

## Pattern

When two or more producers append to a shared append-only JSONL file, they share the **filename**, but their **contract** is the schema marker (a field like `kind` or `schema_version`). Each reader filters by the markers it understands and ignores the rest.

The mistake is to treat unrecognized rows as "contamination" and try to coerce all writers into a single schema. That breaks every time a third producer shows up.

## Concrete example ([project], 2026-05-15)

`~/agent-workflow/pending-suggestions.jsonl` is appended by two systems:

- **site-monitor** writes legacy rows with `site`, `spec`, `rationale`, `scan_type`, `priority`, `confidence`
- **iteration_loop** writes envelope rows with `kind` (`baked_proposal` / `watchdog_event`), `enqueued_at`, `ttl_seconds`, `demote_reason`, `proposal` (nested), `schema_version`

Two consumers read the same file:

- **gastown-router** reads legacy rows, creates beads + slings work
- **iteration_loop.morning_briefing** reads envelope rows, ranks proposals by score formula

### Initial failure

gastown-router was reporting envelopes as "title required" failures (671/672 in a single day). The rows were not in its schema; the naive fix was to move envelopes out of the file or force a unified schema. But that would require iteration_loop to migrate already-enqueued entries, and adding a third producer in the future would repeat the problem.

### The fix

The router simply skips rows where `kind` is present, since those aren't its rows. iteration_loop's docstring documents the multi-producer design explicitly:

```python
if not spec:
    if "kind" in suggestion:
        return None  # envelope — not this reader's row
    log("SKIP: legacy row missing required spec")
    return None
```

Both readers now coexist peacefully on a single file.

## Core principle: Marker-based filtering

The schema marker is **not a nice-to-have categorization** — it is the **contract boundary**. A reader that sees a marker it doesn't understand should:

1. **Check if the marker is recognized** — `"kind" in row` or similar guard
2. **If not recognized, skip silently** — other readers may understand it
3. **If recognized, validate the shape** — enforce schema for rows this reader owns

This decouples producer evolution from reader evolution. Producers can add new marker values without coordinating with readers; readers can reject malformed rows that claim to be in a schema the reader owns.

## When to apply

- Multiple independent writers, append-only, eventual consistency tolerable
- Schema can evolve per-producer without breaking other readers
- Consumers can be added/removed independently
- File-based queueing (JSONL, CSV, etc.) where you want to avoid a real queue system
- Cron-scheduled systems where implicit coordination overhead is acceptable

## When NOT to apply

- **Strong-consistency requirements** → use a real queue (Kafka, SQS, etc.)
- **Bidirectional state** (queue items get mutated by consumers) → JSONL append-only breaks down; use a database
- **Schema-marker collisions** across producers (e.g. two producers both use `type` for different things) → namespace the markers (`kind=foo.proposal` vs `kind=bar.proposal`)
- **Synchronous request-response** → producers expect acknowledgment before continuing; file-based queues add latency
- **No downstream reader** for a marker → dead-letter rows accumulate indefinitely

## Drainage strategies

Two viable models:

### 1. TTL-based (iteration_loop's choice)

Each envelope carries `enqueued_at` + `ttl_seconds`. Readers filter expired entries at read time. The file grows; periodic compaction trims expired rows.

**Pros:** Readers own their own retention logic; no external janitor needed.  
**Cons:** File grows unbounded until compaction; disk usage creeps over time.

### 2. Per-reader cursor

Each consumer tracks a high-water mark (last-processed offset or timestamp). Cheap but requires consumers to be reliable (lost cursor → re-process all).

**Pros:** Automatic cleanup; minimal disk overhead.  
**Cons:** Requires stateful tracking per consumer; lost state means re-processing.

### 3. Single-writer rewrite (gastown-router's current hybrid)

After processing, rewrite the file with only unprocessed rows. Cheap, simple, but **brittle**: two writers racing the rewrite can corrupt the file.

```bash
# Rewrite after processing
jq 'select(.kind != null or .status != "success")' "$file" > "$file.tmp"
mv "$file.tmp" "$file"
```

This works only when cron cadence is slow and single-writer invariant is enforced by scheduling, not by code.

## Related anti-patterns

- **"We need to add a new field to all rows"** → Only if **all readers** actually need it. New readers can safely ignore unknown fields.
- **"Let's split the file by producer"** → Loses the at-most-one-place-to-look property and adds coordination cost. Only do this if schema collisions are unavoidable (i.e., you can't add a namespace marker).
- **"Let's enforce a strict schema on the file"** → Enforces single-producer/schema assumption; breaks when the second producer joins.

## Observability

When multiple producers coexist, track:

- **Rows per marker** — `jq -s 'group_by(.kind // "legacy") | map({key: .[0].kind // "legacy", count: length})'`
- **Processing latency by reader** — each reader should log `received_at` and `processed_at` to measure queue depth
- **Reader-specific skip rates** — if gastown-router is skipping 10% of the file (envelopes), that's healthy; if it's skipping 50% of expected legacy rows, something's wrong

## Grounding

Empirically observed and documented in `iteration_loop/orchestra.py` docstring:

> The target file is shared with the pre-iteration-loop site-monitor flow which wrote bare entries lacking the `kind` field. Per §7.1 final paragraph, the read side treats missing-kind as `legacy_suggestion`, so appending new envelopes here is safe — no migration needed before v0 ships.

**Fix shipped 2026-05-15** in commit `b9cac43`: gastown-router now silently skips rows with `kind` field present.

**Code paths:**
- `iteration_loop/orchestra.py:morning_briefing.load_active_entries()` — returns three buckets: `(proposals, events, legacy)` — all from one file, all coexisting
- `scripts/gastown-router.py` — filters legacy rows, skips envelopes

**Production data:** 671 false failures on 2026-05-14 (before fix) → 0 failures on 2026-05-15 (after fix). No envelope rows were lost; they were correctly routed to iteration_loop.

## Why Staleness Risk is "Stable"

This is a **design principle**, not an implementation detail. The pattern works regardless of tool versions, languages, or queue technologies. The only staleness vector is if the semantics of "marker-based filtering" changes (highly unlikely).

## Source Context

Discovered during [project] morning-loop foundation work (2026-05-15). The site-monitor → iteration_loop → gastown-router pipeline was failing on envelope rows because gastown-router was trying to enforce a schema that envelopes never claimed to implement. The multi-producer design was implicit in the code but not documented. Surfacing it as a pattern prevents future bug-fest when a third producer joins.
