---
title: 'Big-Bang Rename Playbook: Supabase + FastAPI + React Stack'
source_mode: synthesizer
source_session: redacted
created: '2026-05-08T20:00:00Z'
date: '2026-05-08'
confidence: 0.95
grounding_score: 0.95
grounding_source: 'Empirical execution of cos-bfm migration: 13 Postgres tables, 12
  RLS policies, 1 view, 1 function, ~50 backend files, ~30 frontend files. Single-transaction
  big-bang rename applied to shared Supabase project (enjuizlqazkuxpdwxhvk) covering
  both staging and production. Adversarial audit batch (cos-acr) ran post-deploy and
  surfaced two playbook gaps fixed inline (.15 idempotent rename + .16 IVFFLAT memory
  tuning).'
novelty_type: transferable_framework
staleness_risk: stable
importance: 4
pinned: false
accreted_in: '6.5'
related:
- wiki/orchestration/codemod-driven-big-bang-rename.md
- wiki/infrastructure/flat-namespace-prefix-convention.md
- wiki/architecture/scaffolding-vs-patching-pattern.md
domain: migrations
topic: schema-evolution
---

# Big-Bang Rename Playbook: Supabase + FastAPI + React Stack

## Companion entry

`wiki/orchestration/codemod-driven-big-bang-rename.md` (filed 2026-05-05) covers the **decision framework** — when big-bang is the right call vs dual-naming, the Phase 0 traffic-check gate, the 8-point validation sheet. Read that first if you're deciding *whether* to big-bang.

This entry covers **execution** — the gotchas, exact commands, and SQL patterns that surfaced when we actually applied a big-bang rename end-to-end through staging and production. Read this when you've already decided big-bang and are now writing the migration.

---

## When to use

You need to rename a subsystem across a Supabase + FastAPI + React stack — tables, RLS policies, views, functions, backend modules, frontend components, type names, constants, route prefixes — without breaking production users.

Big-bang means: one PR, one transaction, no dual-name compatibility shim period. The right choice when the subsystem is internal-only, has a small concurrent user surface, and your rollback budget is short (≤24h).

**Don't use big-bang when:** the surface is public-facing API (URL stability), there are external integrations referencing old names, or the team is large enough that a coordinated cutover is more costly than a transition period.

---

## Architecture

The rename touches three layers in this order:

```
1. Codemod    (backend + frontend code references new names)
       ↓ commits, doesn't deploy yet
2. Schema     (DB migration renames tables/policies/view/function)
       ↓ atomic single-transaction migration
3. Deploy     (CI builds image with new code; container hits new schema)
       ↓ 24h bake window
4. Wiki       (capture playbook while details are fresh)
```

The codemod **must** ship before the schema migration — if the schema renames first, backend code referencing the old names hits "table does not exist" errors. Backend code can reference new names against the old schema for arbitrarily long because the actual SQL doesn't run until a request hits it.

---

## Phase 1 — Codemod (backend + frontend)

**Pattern:**
- One PR, one logical change, all-or-nothing.
- Use search-replace tooling (ast-grep, sed with care, IDE refactor) for type/class renames.
- Search for **every** reference: code, tests, fixtures, docs, comments, log messages.
- Mechanical changes only. No semantic edits, no incidental cleanups, no "while I'm here" refactors.

**Validation gates (mandatory before merging):**
- Backend: `ruff check` + `pytest` (full suite, not just affected modules)
- Frontend: `eslint` + `tsc --noEmit` + `vitest run`
- CI on the branch must be green before merge.

**Anti-pattern observed:** "While I'm renaming, let me also fix this minor bug." Don't. The clean diff is the safety property — every line change is the same operation. Mixing in semantic edits hides bugs in mechanical noise.

---

## Phase 2 — Schema migration

### 2.1 Single transaction, atomic

```sql
BEGIN;
-- 1. Drop policies (recreated post-rename so the migration is audit-friendly)
-- 2. Drop view + function (rebuilt with new table refs)
-- 3. Rename tables (idempotent — see §2.3)
-- 4. Rename indexes (ALTER INDEX IF EXISTS — has IF EXISTS form)
-- 5. SKIP cosmetic constraint name renames (see §2.4)
-- 6. Recreate policies on renamed tables
-- 7. Recreate view + function with new table refs in body
COMMIT;
```

### 2.2 Idempotent ALTER TABLE RENAME (cos-acr.15)

**Trap:** `ALTER TABLE ... RENAME` has no `IF EXISTS` variant. If the migration tracker records "succeeded" before COMMIT ack lands (network blip), a re-run aborts on the first rename whose source no longer exists.

**Fix:** wrap each rename in a DO block that checks information_schema first:

```sql
DO $$
DECLARE
    rename_pair RECORD;
BEGIN
    FOR rename_pair IN
        SELECT * FROM (VALUES
            ('old_table_a', 'new_table_a'),
            ('old_table_b', 'new_table_b')
            -- ...
        ) AS t(src, dst)
    LOOP
        IF EXISTS (
            SELECT 1 FROM information_schema.tables
             WHERE table_schema = 'public' AND table_name = rename_pair.src
        ) THEN
            EXECUTE format('ALTER TABLE %I RENAME TO %I', rename_pair.src, rename_pair.dst);
        ELSIF NOT EXISTS (
            SELECT 1 FROM information_schema.tables
             WHERE table_schema = 'public' AND table_name = rename_pair.dst
        ) THEN
            -- Neither source nor destination exists — flag loudly.
            RAISE EXCEPTION 'rename: neither % nor % exists', rename_pair.src, rename_pair.dst;
        END IF;
        -- else: dst already exists, src already gone — re-run no-op.
    END LOOP;
END $$;
```

Apply the same pattern to the down migration.

### 2.3 Constraint name renames — SKIP

Auto-generated FK/PK/check/unique constraints retain their old prefix after `ALTER TABLE RENAME`. `de_cohorts_pkey` survives the table rename to `buyers_committee_cohorts`.

**Tempting:** rename them in a DO block scanning `pg_constraint`.

**Don't.** A DO block dynamically generating ALTER TABLE statements for constraints caused a transaction-rollback bug in the Supabase Studio SQL editor (the inner-statement error didn't surface; the outer transaction silently aborted). Skipping this section keeps the migration atomic and visibly-correct.

If naming-consistency becomes important later, file a separate cleanup migration. For all functional purposes the old names work fine — `pg_constraint.conrelid` is OID-based and follows the table.

### 2.4 Pre-conditions inventory

Before applying, snapshot current state. Examples:

```sql
SELECT table_name, (SELECT count(*) FROM information_schema.columns
                    WHERE table_name = t.table_name) AS col_count
  FROM information_schema.tables t
 WHERE table_schema = 'public' AND table_name LIKE 'old_prefix\_%';

SELECT count(*) FROM old_prefix_central_table;  -- preserve row counts for post-check
```

Post-migration, run the same queries against the new prefix. Counts must match exactly. Any divergence is a flag.

---

## Phase 3 — Migration application

### 3.1 Three methods, ranked

| Method | When to use | Tracker behavior |
|---|---|---|
| **Supabase Management API** | One-shot apply, ad-hoc fixes, tracker-drift recovery | Bypasses tracker entirely |
| **Supabase Studio paste-and-run** | Manual review feel, no CLI link required | Does NOT update `supabase_migrations.schema_migrations` |
| **Supabase CLI (`supabase db push`)** | Full-history project, no prior drift | Updates the tracker; will fail if local migration set diverges from remote |

**Trap (cos-bfm.7 reality):** mixing Studio paste with CLI tracking guarantees drift. Once any migration has been pasted, **stop using the CLI for that project** — or you'll need to manually mark migrations as applied and risk skipping ones that aren't.

### 3.2 Management API — fastest, most reliable

```bash
curl -sS -X POST \
  "https://api.supabase.com/v1/projects/${SUPABASE_PROJECT_REF}/database/query" \
  -H "Authorization: Bearer ${SUPABASE_MANAGEMENT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg q "$(cat migration.sql)" '{query: $q}')"
```

Returns JSON results. Errors come back as `{"message": "Failed to run sql query: ..."}`. Each call runs in an implicit transaction.

The token is in `~/Scripts/[project]/cos/backend/.env` as `SUPABASE_MANAGEMENT_TOKEN`. Project ref as `SUPABASE_PROJECT_REF`.

### 3.3 IVFFLAT index gotcha (cos-acr.16)

Supabase default `maintenance_work_mem` is **32MB**. IVFFLAT index builds with `lists ≥ 50` over modest row counts can need 60MB+. Symptom:

```
ERROR:  54000: memory required is 60 MB, maintenance_work_mem is 32 MB
```

**Fix in the same query:**
```sql
SET LOCAL maintenance_work_mem = '128MB';
DROP INDEX IF EXISTS my_ivfflat_index;
CREATE INDEX my_ivfflat_index ON ... USING ivfflat (...) WITH (lists = 50);
```

**Always include `SET LOCAL` in the migration file itself.** Otherwise the migration succeeds in your dev environment (where you ran `SET` manually) but fails on the next applier.

### 3.4 Shared Supabase caveat

Pre-revenue projects sometimes share one Supabase project for prod + staging (cost optimization). When this is the case:
- "Applied to staging" = "Applied to prod"
- Pre-flight checks count for both
- Document the trigger to split (typically: paying clients arrive)

Make the shared-vs-split state explicit in project memory; otherwise team members assume they're separate and run "staging-only" experiments that hit prod.

---

## Phase 4 — Deploy + bake

### 4.1 Sequence

1. CI on the branch passes (lint + test + build + integration).
2. Merge to `master`. Origin CI re-runs and deploys to staging.
3. Run staging smoke: backend container healthy, no new ERROR signatures in 10m log window, key API endpoints return 200, target feature page renders.
4. Apply schema migration to shared Supabase (or staging-only if separate).
5. `git push production master` → triggers production CI + deploy.
6. **Hold a 24h post-deploy bake window.** Watch logs for new ERROR signatures. Hard rollback deadline = deploy time + 24h.
7. Beyond 24h, the rename is "set." Down-migration becomes purely a recovery tool, not a planned-rollback path.

### 4.2 Bake-window monitoring

Things that look normal but aren't:
- A new ERROR signature you didn't see pre-deploy → investigate before it normalizes
- API latency p99 quietly climbs (event-loop blocking, connection-pool starvation)
- Health checks flap (tells you cold-starts now exceed the timeout — see cos-acr.19)

Things that ARE normal:
- One ERROR per partial-run path that triggers a designed retry (cos-acr.10 PartialRunBanner pattern)
- Brief log volume spike right after deploy (warmup)

---

## Phase 5 — Wiki accretion (this document)

Capture immediately after deploy succeeds — within 24-48h. The reasoning context for each design choice degrades fast: by week 2, "why did we pick big-bang?" has soft edges; by week 4, the gnarly details (Management API tracker drift, IVFFLAT memory tuning) require archaeology to recover.

Format: one wiki entry per playbook, ~300 lines, structured by Phase. Cross-link to bead IDs that surfaced gaps so future readers can pull the original thread if needed.

---

## Anti-patterns (observed in cos-bfm execution)

1. **Renaming auto-generated constraints in the same transaction** — caused silent transaction rollback. Skip them.
2. **Assuming Supabase CLI tracker reflects reality after Studio paste** — it doesn't. Pick one method per project.
3. **Forgetting `SET LOCAL maintenance_work_mem` in IVFFLAT migrations** — works in your env, breaks on the next applier.
4. **Not documenting the shared-Supabase status** — staging-experiments hit prod; pre-flights confused; team mental models drift.
5. **Mixing rename with semantic edits in one PR** — defeats the safety property of "every line change is the same operation."

---

## Reusable artifacts

- **Idempotent rename DO block template** (§2.2)
- **Pre-flight inventory query template** (§2.4)
- **Management API curl template** (§3.2)
- **IVFFLAT memory-tuning preamble** (§3.3)
- **Bake-window monitoring checklist** (§4.2)

---

## Origin

`cos-bfm.6` (rename migration) + `cos-bfm.7` (production replication runbook) + `cos-acr.15` (idempotent rename gap) + `cos-acr.16` (IVFFLAT memory gap). Captured per `cos-bfm.15` after successful deploy + 24h bake window passed (2026-05-08).
