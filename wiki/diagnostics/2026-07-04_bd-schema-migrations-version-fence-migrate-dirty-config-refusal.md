---
title: bd schema_migrations version fence + bd migrate dirty-config refusal
source_mode: debugger
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-04
domain: diagnostics
topic: bd-cli
tags: bd, dolt, schema-migration, diagnostics, operational
related_entries:
  - infrastructure/2026-05-27_bd-cli-dependency-wiring-inversion-two-pass-pattern.md
  - methodologies/2026-06-25_bd-cross-store-sweep-nested-stores-dolt-state-diagnostic.md
  - diagnostics/2026-05-23_beads-multi-database-working-directory-gotcha.md
  - diagnostics/2026-05-18_bd-title-length-utf8-bytes-not-codepoints.md
---

# bd schema_migrations Version Fence + bd migrate Dirty-Config Refusal

## When you see this

You (or a triage tool) run `bd list` (or any bd query) against a bd store on the shared dolt server and get:

```
Error: failed to open database: schema skew check: Error 1146 (HY000): table not found: schema_migrations
```

You suspect the store is broken. **It usually isn't** — the store is fine, bd just refuses to open it because its schema is behind bd's own version fence.

## Why this happens

bd uses a `schema_migrations` table in each database as its version marker. Stores initialized before this tracking table was added (schema_version ≤ 11 in the version I encountered) have all the "normal" tables (issues, events, dependencies, etc.) but not `schema_migrations`. Current bd refuses to open them defensively — the schema skew check fires before any query runs.

## What `bd migrate` does — and doesn't

Instinct: `bd migrate` on the legacy store should apply the pending migrations. But bd will refuse:

```
Error: failed to open database: failed to initialize schema: schema migration: pending schema migrations alter pre-existing dirty tables: config
```

The pre-existing `config` table (bd tuning params: `auto_compact_enabled`, `compact_batch_size`, etc.) is at the v11 shape; current migrations would collide. bd will not migrate over dirty pre-existing tables — it refuses rather than risk data loss.

## Diagnostic steps (in this order)

1. Confirm the store is actually reachable:
   `dolt sql -q "SHOW TABLES"` from the DB directory (in the dolt data dir, not the .beads dir). If tables list, the DB is fine — the problem is bd's schema fence.
2. Check `custom_types`, `config`, and `issues` row counts. **If issues=events=wisps=comments=labels=dependencies=0, the store is zero-data** — just a scaffold that was never used. Don't invest in migration.
3. Only if row counts are non-zero: `bd migrate --dry-run --inspect` to see exactly which tables would collide.

## Recovery options (from lightest to heaviest)

- **Suppress** — legacy zero-data store: add it to your triage tool's known-error suppression list, link a bead explaining. See `patterns/` — Triage-tool SUPPRESSED_STORE_LABELS pattern (if it exists in this wiki).
- **Archive** — no real data: remove the DB from the shared server + rm the `.beads` skeleton. Custom-type registry (if any) can be re-declared.
- **Export/reimport** — real data present: `bd export --format=jsonl > /tmp/legacy.jsonl`, drop the collision tables (config), `bd migrate`, `bd import /tmp/legacy.jsonl`, verify counts match. Preserves history but touches shared infra — get operator sign-off.

## What NOT to do

- **Don't `rm -rf` the .beads dir on gut instinct.** In this session's diagnosis, one "broken" store had 168 real historical issues in it (pre-dolt SQLite backend, different problem). Investigate before deleting.
- **Don't restart the shared dolt server.** The server is healthy; only bd's client-side schema fence is failing. Server restart doesn't help and could disturb other consumers.

## Grounding

Diagnosed 2026-07-04 against `~/gt/town/.beads` on [project] laptop. Shared dolt server pid 1817 healthy on port 3307; town DB had 24 tables including config (11 rows) and custom_types (11 rows: gt entity types agent/role/rig/convoy/slot/queue/event/message/molecule/gate/merge-request) but 0 rows in issues/events/wisps/interactions/comments/labels/dependencies. Six dolt commits since 2026-03-03, last was `[claude_setup]` — never re-used. `bd migrate --dry-run` reproduced the "dirty config table" refusal. Tracked in [project]-8n5w (closed) and [project]-yj6g (open, archive-vs-migrate decision).
