---
title: Verify FK target table on remote before writing migrations against renamed tables
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-16
domain: debugging
topic: error-classification
tags: empirical, quality-gate, grounding, deployment
related_entries:
  - wiki/migrations/big-bang-rename-supabase-fastapi-react.md
  - wiki/orchestration/codemod-driven-big-bang-rename.md
  - wiki/methodologies/2026-05-13_find-consumer-first-before-data-migration.md
---

# Verify FK target table on remote before writing migrations against renamed tables

## The trap

When writing a new migration that references an existing table via FK, the LOCAL filesystem's earlier migration files may show the table name as `de_personas` / `archetype_templates` / etc., but the REMOTE database may already carry a renamed version (`buyers_committee_personas`, `buyers_committee_archetype_templates`) from a later rename migration. Writing the new migration against the original name produces `ERROR: 42P01: relation "<name>" does not exist` at apply time. Cheap to fix mid-flight; expensive if it propagates to other developers' branches before the typo is caught.

## The deterministic check (before authoring any new migration with FK references)

```bash
# 1. List actual table names on the remote that match your domain prefix.
supabase db query --linked --output table \
  "SELECT table_name FROM information_schema.tables \
   WHERE table_schema='public' AND table_name LIKE '<domain-prefix>%' \
   ORDER BY table_name"
```

Match the FK target spelling in your `REFERENCES` clause to what the query returns, not to what's in the local-filesystem migration files. The filesystem files are authoritative ONLY if all of them have been applied via the CLI (which doesn't apply when migrations are paste-applied via Studio).

## Why filesystem-driven mental model fails

1. **Supabase Studio paste-and-run does NOT update `supabase_migrations.schema_migrations`** — separate gotcha. The schema_migrations table tracks only CLI-applied migrations; Studio paste-and-run leaves the table intact but applies the SQL directly to the DB. This creates a drift between "what CLI thinks has been applied" and "what's actually on the remote."

2. **CLI `supabase migration list --linked` shows only what's been CLI-applied** — manual rename migrations applied later via paste won't appear in the local-vs-remote diff. A migration list that shows "0071_rename_de_to_bc" as unapplied may be wrong if it was pasted last week.

3. **Searching backward through `migrations/*.sql` to find renames is error-prone** — a single ALTER TABLE RENAME in the middle of the migration sequence rewrites the working table name, and there may be multiple renames across different domain subsystems. Finding the authoritative current name by reading backward is tedious and fragile.

**The information_schema query is the single source of truth for the current remote state, independent of migration tracker state.**

## When this applies

- Project uses custom migration naming (`NNN_name.sql`) where the CLI's `db push` doesn't auto-sync
- Tables have been renamed in past migrations (e.g., domain rebranding: `de_*` → `buyers_committee_*`)
- New migration references existing tables via `REFERENCES <table>(id)` or other FK constraints
- You're unsure whether all rename migrations have been CLI-applied or some were pasted via Studio

## When this does NOT apply

- Brand-new schema with no rename history and no prior drift
- Migrations using `supabase db push` with timestamp-named files and tracked `schema_migrations` table — that workflow surfaces drift differently (though even there, a quick information_schema query costs nothing)
- Migration referencing only tables created in the same migration (those table names come from your code, not history)

## Concrete case: cos-3bu.7 (migration 100, 2026-05-16)

I wrote the migration with:
```sql
archetype_template_id UUID REFERENCES archetype_templates(id) ON DELETE SET NULL
```

The reasoning: migration 057_decision_ensemble.sql (which I'd just read) created `archetype_templates`. What I missed: migration 071_rename_decision_ensemble_to_buyers_committee.sql renamed it to `buyers_committee_archetype_templates`.

`supabase db query --linked -f /path/to/100_bc_library_personas.sql` returned:
```
unexpected status 400: {"message":"Failed to run sql query: ERROR:  42P01: relation \"archetype_templates\" does not exist\n"}
```

The verification query that should have come FIRST:
```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema='public' AND (table_name LIKE 'buyers_committee%' OR table_name LIKE 'archetype%')
ORDER BY table_name
```

Output showed the correct name (`buyers_committee_archetype_templates`). One-line fix to the migration FK clause, re-apply, done. Total slip: ~60 seconds. Could have been an hour if the failure had surfaced in a CI run instead of an interactive `db query` call.

## Habit to install

Before authoring a migration with `REFERENCES`, run the information_schema query against the deployment-of-record (linked remote) for any table whose name is older than the most recent rebrand/rename in the migration history. Three seconds of paranoia saves three minutes of debugging — and saves the embarrassment of a broken migration shipping to peers' local dev environments.

## Related patterns

- **Big-Bang Rename Playbook** (wiki/migrations/big-bang-rename-supabase-fastapi-react.md) — covers execution end-to-end; assumes you're renaming, not writing new FKs against already-renamed tables
- **Codemod-Driven Big-Bang Rename** (wiki/orchestration/codemod-driven-big-bang-rename.md) — decision framework for when big-bang is the right strategy; includes Phase 4 validation gates that would catch this error, but only if you get that far
- **Find-consumer-first before data migration** (wiki/methodologies/2026-05-13_find-consumer-first-before-data-migration.md) — methodological probe for data corpus freshness; this is about schema freshness instead

## Source context

Discovered during cos-3bu.7 work on 2026-05-16. Migration 100_bc_library_personas failed on first apply with 42P01 (relation does not exist) because the FK target table had been renamed in a prior migration. The information_schema query revealed the actual remote state instantly and provided a one-line fix. The pattern is narrower than the big-bang playbook but addresses a specific hazard when authoring migrations against a schema with rename history.
