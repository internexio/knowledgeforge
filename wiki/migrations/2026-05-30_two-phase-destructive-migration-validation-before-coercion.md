---
title: Two-phase destructive-migration pattern — ship a read-only validation report before the irreversible coercion
source_mode: direct
novelty_type: transferable_framework
grounding_score: 0.8
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-30
tags: migrations, database, supabase, postgresql, risk-mitigation, deployment-safety
related_entries:
  - wiki/migrations/2026-05-24_safe-one-shot-backfill-script-dry-run-idempotent-no-improvement-skip.md
  - wiki/diagnostics/2026-05-25_http-adapter-silent-failure-integration-test-mandatory.md
  - wiki/methodologies/2026-05-27_supervise-first-real-data-run-autonomous-loops.md
domain: migrations
topic: error-classification
---

# Two-phase destructive-migration pattern — validation before coercion

When a database migration includes a destructive or irreversible step that could fail on dirty existing data (type coercion, FK repoint, NOT NULL addition with backfill, enum value change), split the rollout into two migrations:

## Phase 1 — Read-only validation report

A migration that runs entirely inside a `DO $$ ... $$` PL/pgSQL block and emits `RAISE NOTICE` messages reporting:

- A count of rows that would block the destructive change (e.g., rows whose `user_id` isn't a valid UUID; rows whose FK target doesn't exist in the new parent table).
- For each non-zero count, the exact SQL query a human can run to inspect the offending rows.
- A boundary message stating the explicit pass condition (typically "Phase 2 is safe to apply iff ALL counts are 0").

The phase-1 migration changes **zero state** — no DDL, no DML, no FK drops. Its `.down.sql` is a no-op `SELECT 1;`.

## Phase 2 — The actual destructive change

Lands only after the phase-1 report has been applied to staging (and/or prod) AND the counts come back clean (or the blocking rows have been manually resolved).

---

## When this applies

- Type coercion (`ALTER COLUMN ... TYPE UUID USING ...::UUID`).
- FK repoint (drop FK to A, re-add FK to B) when historical rows may reference A-only ids.
- Adding NOT NULL constraint to a backfilled column.
- Enum value renames where existing rows hold the old value.
- Any migration whose failure mode is "type/constraint violation on row N" partway through and would leave the schema in a half-migrated state.

## When this does NOT apply

- Pure additions (new column, new table, new index) — these don't risk data-shape failure.
- Migrations under transactional DDL where a rollback is cheap and complete.
- Schemas small enough that an exhaustive `SELECT` ahead-of-time isn't operationally different from a NOTICE-based report.

---

## Why it works

The classic failure mode for type-change migrations is:

> Passes locally, passes on staging with the staging dataset, fails on prod because of one stale row from 2022.

A read-only report:

1. **Runs cheaply** against any environment without changing state.
2. **Surfaces the exact failure-blocking rows** before you ship the destructive step.
3. **Lets the destructive migration be a clean win** (zero edge cases) rather than a 30%-fail risk.
4. **Embeds the diagnostic query inside the migration itself**, so the next engineer 6 months later doesn't have to rediscover it.

The pattern forces a decision point: phase-1 reports counts, human verifies they're acceptable (or resolves blocking rows manually), then phase-2 lands with confidence. Without the split, the destructive step hits the database blind.

---

## Concrete reference shape (PL/pgSQL, Postgres / Supabase)

```sql
-- Phase 1: Read-only validation (applies to any environment cost-free)
DO $$
DECLARE
    orphaned_count bigint;
    non_uuid_count bigint;
BEGIN
    -- Check 1: FK target integrity
    SELECT count(*) INTO orphaned_count
    FROM score_feedback
    WHERE user_id IS NOT NULL
      AND NOT EXISTS (
          SELECT 1 FROM profiles
           WHERE id = score_feedback.user_id
      );

    -- Check 2: Type conformance (if converting TEXT → UUID)
    SELECT count(*) INTO non_uuid_count
    FROM score_feedback
    WHERE user_id IS NOT NULL
      AND NOT (user_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$');

    RAISE NOTICE 'Phase 1 validation for score_feedback.user_id → UUID migration:';
    RAISE NOTICE '  Orphaned rows (FK target missing): %', orphaned_count;
    RAISE NOTICE '  Non-UUID values (type mismatch): %', non_uuid_count;
    RAISE NOTICE 'Phase 2 is safe to apply iff BOTH counts are 0.';
    RAISE NOTICE '';
    RAISE NOTICE 'Inspect orphaned rows: SELECT id, user_id FROM score_feedback WHERE user_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM profiles WHERE id = score_feedback.user_id);';
    RAISE NOTICE 'Inspect non-UUID rows: SELECT id, user_id FROM score_feedback WHERE user_id IS NOT NULL AND NOT (user_id ~ '\''^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'\'');';
END $$;

-- Down migration (no-op)
SELECT 1;
```

The `.down.sql` for phase 1 is `SELECT 1;` (read-only forward, nothing to revert).

---

## Phase 2 migration (applies only after phase 1 review)

```sql
-- Phase 2: Destructive coercion (applies only after phase-1 validation is clean)
BEGIN;

-- Drop old FK that referenced a different parent table (if applicable)
ALTER TABLE score_feedback DROP CONSTRAINT IF EXISTS score_feedback_user_id_fkey;

-- Coerce the column type
ALTER TABLE score_feedback
  ALTER COLUMN user_id TYPE uuid USING user_id::uuid;

-- Add NOT NULL if needed
ALTER TABLE score_feedback
  ALTER COLUMN user_id SET NOT NULL;

-- Re-add FK to correct parent
ALTER TABLE score_feedback
  ADD CONSTRAINT score_feedback_user_id_fkey FOREIGN KEY (user_id) REFERENCES profiles(id);

COMMIT;
```

---

## Grounding

Verified in [project] 2026-05-30, bead `cos-18v`:

- **Phase 1 decision:** "/bead-decisions" route voted "two-phase rollout — migration 104 validates, 105 coerces after manual review".
- **Phase 1 execution:** "/bead-build" deployed migration 104 (`104_validate_user_id_types.sql`) same evening.
- **Phase 1 validation report:** The migration emitted NOTICEs counting three classes of blocker:
  - `brand_guidelines.user_id` rows orphaned from `profiles(id)` (would fail FK repoint).
  - `score_feedback.user_id` values not matching the UUID regex (would fail TEXT→UUID coercion).
  - `analysis_feedback.user_id` values not matching the UUID regex.
- **Manual review gate:** Counts came back with 8 orphaned rows + 3 non-UUID rows across the two tables. Human inspection occurred before phase 2 landing.
- **Phase 2 bead:** Filing of bead `cos-alr` explicitly tracked phase 2 after the staging report review completed.

The pattern emerged from the bead's own **Risk section** ("Type-change on the feedback tables can fail if any existing rows have non-UUID values. Run a ... style check first") generalized into a reproducible migration shape.

---

## When to migrate from single-phase to two-phase

**Signal that two-phase is needed:**
- The destructive step has failure conditions you cannot guarantee are zero in production
- The dataset is large enough that manual inspection of blockers is tedious but affordable
- The cost of a failed migration (partial schema, manual recovery, rollback overhead) exceeds the cost of two deploys

**Don't migrate to two-phase for:**
- New tables / columns / indexes (no blockers to detect)
- Type changes where you've already fixed all known blockers (use a single phase with a pre-flight query confirmation)
- Dead-simple renames with no type coercion (expand-contract is simpler; see related)

---

## Anti-pattern to avoid

**Skipping the read-only phase and doing "validation on rollout":**

> Let's just apply the destructive migration. If it fails, we'll rollback and fix the blocking rows manually.

This trades:
- **Two deploys + one manual inspection** (two-phase pattern)

For:
- **One deploy + unplanned downtime to rollback + manual fix + re-deploy** (validation-on-failure)

The two-phase pattern is strictly better when downtime cost > deploy cost.

---

## Related patterns

- **Safe one-shot backfill script** — similar "dry-run first, then apply" discipline but for data transformation, not schema validation
- **Expand-contract column rename** — two-commit pattern for column renames, different failure mode (read-path breakage, not type failure)
- **Supervise the first real-data run before autonomous loops** — methodological reminder that destructive operations need human verification gates

---

## Source Context

Pattern derived from [project] session 2026-05-30 (`2026-05-30-[project]-bead-pipeline`). Bead `cos-18v` decided on two-phase user_id type migration for feedback tables after identifying potential blockers (orphaned FK rows, non-UUID text values). Phase 1 validation shipped the same day via `/bead-build`; phase 2 awaited manual review of the validation report. The pattern generalized from this single use case into a reusable framework for any destructive migration with identifiable blocker classes.
