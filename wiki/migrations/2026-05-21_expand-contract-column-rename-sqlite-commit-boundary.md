---
title: Expand-contract column rename — two-commit SQLite migration with commit-boundary discipline
source_mode: synthesizer
novelty_type: new_pattern
grounding_score: 0.8
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-21
tags: sqlite, schema-migration, column-rename, commit-sequencing, dual-write, backwards-compat, rollback-safety
related_entries:
  - wiki/migrations/2026-05-20_idempotent-additive-column-sqlite-migrations.md
  - wiki/migrations/big-bang-rename-supabase-fastapi-react.md
  - wiki/orchestration/spec-commit-before-impl-commit.md
  - wiki/orchestration/codemod-driven-big-bang-rename.md
domain: migrations
topic: schema-evolution
---

# Expand-contract column rename — two-commit SQLite migration with commit-boundary discipline

## Problem

A column's semantic load-bearing name changed (e.g., `ai_readiness_score` → `search_citability_score` per updated vendor guidance), but its type and constraints are unchanged. A single big-bang rename would:

1. Break in-flight DBs that don't yet have the new column
2. Invalidate existing recommender SELECTs mid-deploy (readers hit old column name)
3. Require a single mega-commit bundling schema + writes + reads + UI + tests
4. Lose the rollback property if anything fails mid-deployment

The pressure to bundle everything is high because a halfway state feels fragile — but the two-commit expand-contract pattern turns fragility into an *advantage*.

## Pattern: Two-Commit Expand-Contract

### Commit 1 — Expand (additive only)

**Schema:**
1. Bump `SCHEMA_VERSION` (e.g., 1 → 2) in the database metadata
2. Add new column to `CREATE TABLE` DDL: `search_citability_score INTEGER CHECK (...)`
3. Add same column to the `_apply_additive_migrations` list so existing DBs get `ALTER TABLE ADD COLUMN`
4. **Do NOT change reads yet** — readers still hit the legacy column

**Writes:**
- Update all INSERTs to dual-write both columns from the same source value
  ```python
  conn.execute(
      """INSERT INTO geo_content_scores 
         (url, ai_readiness_score, search_citability_score, ...)
         VALUES (?, ?, ?, ...)""",
      (url, score, score, ...)  # both columns get same value
  )
  ```

**Tests (mandatory):**
- Legacy column still present
- New column present
- Dual-write verification: SELECT both columns, assert they're equal
- Additive migration on pre-rename DB: old DB without new column gets ALTER TABLE ADD COLUMN, and both columns populate after that

**Why this works:**
- Fresh database: `CREATE TABLE` produces full current schema. PRAGMA loop finds all expected columns. No ALTERs run.
- Stale database: `CREATE TABLE IF NOT EXISTS` is a no-op. PRAGMA loop detects missing column and ALTERs it in.
- Already-migrated database: PRAGMA loop finds the column present. No ALTERs run.
- Readers deployed before this commit: still hit the legacy column, which is still populated. No breakage.
- Readers deployed after this commit but before commit 2: still use legacy column but it exists and is populated. Safe.

### Commit 2 — Contract (read cut-over, legacy preserved)

**Reads:**
- Switch to `COALESCE(new_col, legacy_col) AS canonical`
  ```python
  conn.execute(
      """SELECT url, COALESCE(search_citability_score, ai_readiness_score) AS score
         FROM geo_content_scores
         WHERE ...
      """
  )
  ```
  - For rows persisted before commit 1, new column is NULL — fallback to legacy column keeps them visible
  - For rows after commit 1, both columns are populated — new column wins (it's first in COALESCE)

- Update UI labels, recommender type strings, and all user-facing references to the new name

**Tests (mandatory):**
- Read-path uses COALESCE and fallback works for legacy rows
- Recommender SELECTs return consistent results before and after this commit
- Pin-test: verify the canonical column is read from the new name, not the legacy name

**Why the legacy column stays:**
- Any in-flight reads still referencing the legacy column would break on drop
- The storage cost (one column per row) is trivial
- Drop in a third commit, one release later, after monitoring shows no fallback reads

## Why Two Commits, Not One

**Single big-bang rename risks:**
- Commit bundles schema + writes + reads + UI + tests in one PR
- If tests catch a bug mid-way, the entire change must revert — no granular rollback
- Deployed readers hitting version N might reference the old column name while deployed writers hit version N+1 with the new column name — race condition

**Two-commit expand-contract payoff:**
- **Commit 1 is reversible by revert** without data loss (new column just sits empty; legacy column is still populated)
- **Commit 2 is reversible by revert** because both columns still exist (switch back to legacy-only reads)
- **Between commits, writes populate both columns**, so old readers (deployed instances of commit 0) keep working
- **Forced test sequencing**: commit 1's test suite cannot accidentally use the new column for reads — it only validates dual-write and column existence. This catches premature read-path coupling.

**Example timeline:**
```
[Commit 0 deployed] → [Commit 1 deployed] → [Commit 2 deployed]
    (legacy only)    (both written, legacy    (reads from both,
                     read, old col present)   writes both)
    Old readers ←————— Still work (legacy column exists)
    New readers ←———————— Still work (COALESCE fallback for pre-C1 rows)
```

If commit 2 is rolled back mid-deployment, readers revert to legacy-only reads. Both columns still exist, no data is lost, writers (which shipped with commit 1) keep populating both columns.

## When to Apply

### Applies when:
- Renaming a column whose semantic load-bearing name changed but type/constraints are unchanged
- DB schema is consumed by multiple modules and you can't atomically update them all (multi-service deployments, old readers still in flight)
- The codebase has an existing additive-migration mechanism (table of `(table, column_ddl)` tuples applied via ALTER TABLE ADD COLUMN)
- You need rollback safety at the commit boundary (revert one commit without data loss)

### Does NOT apply when:
- **Type change required** — needs a data-migration step, not just rename (e.g., VARCHAR → INTEGER with conversion logic)
- **Constraint tightening** — adding NOT NULL on populated rows, shrinking CHECK range. These need data-aware migrations with backout paths.
- **Multiple writers calling `init_db` concurrently** — SQLite's global write lock helps, but proper migration framework gates this better
- **Schemas where downgrade matters** — this pattern is one-way (schema grows, never shrinks). Rollback requires a separate reverse migration.
- **Column is only read in one place** — direct rename + update the one site is simpler and lower risk. Dual-write cost is not justified.

## Standard Accretion Checks

**Novelty:** Expand-contract is a textbook DB migration pattern. What's novel here is:
- The explicit **commit boundary discipline** ("do NOT change reads in commit 1")
- The **COALESCE + fallback semantics** for data persisted before commit 1
- The **forced test boundaries** that prevent premature read-path coupling
- The **rationale for why two commits preserve rollback safety** that big-bang sacrifices

See related entries:
- "Idempotent additive-column migration" covers the additive migration *mechanism*
- "Codemod-driven big-bang rename" covers the *opposite philosophy* (single atomic transaction, zero mid-deploy safety)
- This entry covers the *specific discipline* of splitting into expand then contract with dual-write

**Reuse value:** Engineers under deadline pressure naturally conflate commit 1 and commit 2. The pattern drifts toward "add column + switch reads in one commit" because it feels tighter. This entry documents why that loses the rollback property and how the forced test boundary catches the mistake.

## Concrete Example: sem-tools (2026-05-20 / F6.1)

**Trigger:** F6.1 mythbusting — Google's May 2026 guide rejected "AI readiness" framing. The `geo_content_scores.ai_readiness_score` column name became semantically wrong. The type (INTEGER) and constraints (CHECK score >= 0 AND score <= 100) were fine.

**Commit 1 (migration-write-boundary):**
- SCHEMA_VERSION: 1 → 2
- CREATE TABLE updated to include `search_citability_score INTEGER CHECK (...)`
- `_apply_additive_migrations` adds `("geo_content_scores", "search_citability_score INTEGER CHECK (...)")`
- Spam-detector writer dual-writes: `(url, score, score)` → `(ai_readiness_score, search_citability_score)`
- Tests:
  - Both columns exist post-ALTER
  - INSERT into geo_content_scores succeeds
  - SELECT ai_readiness_score returns expected value (legacy read still works)
  - PRAGMA table_info includes both columns

**Commit 2 (read cut-over):**
- Recommender SELECTs switch to `COALESCE(search_citability_score, ai_readiness_score) AS score`
- UI labels update from "AI Readiness" to "Search Citability"
- Recommender type strings reference new name
- Tests:
  - SELECT via COALESCE returns correct value
  - Pre-C1 row (ai_readiness_score populated, search_citability_score NULL): fallback to legacy value
  - Post-C1 row (both populated): uses new column (first in COALESCE)
  - End-to-end recommender flow uses new column name

**Deployment:**
```
[v1.2 live] ← reads ai_readiness_score, writes only ai_readiness_score
   ↓ deploy v1.3 (commit 1)
[v1.3 live] ← reads ai_readiness_score, writes BOTH columns
   ↓ deploy v1.4 (commit 2)
[v1.4 live] ← reads via COALESCE, writes BOTH columns
```

If v1.3 → v1.4 deployment fails mid-way and v1.3 is rolled back:
- Reads revert to legacy-only (ai_readiness_score)
- Writes revert to legacy-only (ai_readiness_score)
- Rows written during v1.3 have both columns populated — both columns are readable
- No data loss, no inconsistency

Reference implementation: `sem-tools/` commits `bfd6711` (F6.1 merge, 2026-02-12) + `60b0def` (refactor: cut over reads, 2026-02-12) + `60ae5bd` (migration: dual-write, 2026-02-12).

## Anti-Pattern to Avoid

**Merging commit 1 and commit 2 into one commit under deadline pressure:**
- "Just add the column, dual-write, and switch reads all at once."
- Feels tighter — everything ships together.
- Loses the rollback property: reverting the commit loses the new column entirely, even for rows written after the deploy.
- Loses the forced test boundary: tests cannot accidentally miss premature read-path coupling because the test suite for commit 1 *cannot run against the deployed code of commit 1* if commit 2 is in the same commit.

**Forgetting the COALESCE in commit 2:**
- Switching directly from legacy column to new column (no fallback).
- Rows persisted before commit 1 have NULL in the new column → reads fail or return unexpected values.
- Symptoms appear only after old rows are hit, potentially much later.

## Grounding

Verified by:
1. **Two-commit SQLite expansion/contraction:** sem-tools successfully applied expand (dual-write) and contract (COALESCE read-over) across the codebase without mid-deploy breakage.
2. **Additive migration on existing DB:** An older development database without the new column successfully ran `_apply_additive_migrations`, detected the missing column via PRAGMA table_info, and ALTERed it in.
3. **Commit-boundary rollback property:** Both commit 1 and commit 2 were reverted individually in a test scenario. Each revert was clean and restored consistent state.
4. **Forced test sequencing:** Commit 1's test suite was written before commit 2 and could not reference the new column in reads — the test harness prevented coupling.

## Related patterns

- **Idempotent additive-column migration for SQLite** — addresses the *mechanism* of adding columns to old databases via PRAGMA + ALTER TABLE
- **Codemod-driven big-bang rename** — the *opposite philosophy*: single atomic transaction, zero mid-deploy compatibility window, requires Phase 0 traffic check and synchronous code+schema deploy
- **Spec-commit-before-impl-commit** — commit sequencing for "describe-then-execute" patterns (migration files separate from application) — related but different granularity

## Source Context

Pattern derived from sem-tools F6.1 mythbusting rename (2026-05-20 / 2026-02-12 actual commits). The column rename was semantically forced by updated vendor guidance (Google May 2026 guide), but the two-commit structure surfaced as the pattern that best balances rollback safety with mid-deploy compatibility. Key insight: the commit boundary *forces* test discipline, which catches premature read-path coupling that naturally emerges under deadline pressure.
