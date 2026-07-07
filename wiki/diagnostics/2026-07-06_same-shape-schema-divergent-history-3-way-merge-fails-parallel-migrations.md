---
title: Same-shape schema, divergent history — 3-way merges fail when parallel migrations converge on identical current schema
source_mode: debugger
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-07-06
domain: diagnostics
topic: version-control-schema-evolution
tags: dolt, database-migration, version-control, schema-evolution, merge-conflict, cross-machine-sync, diagnostic-pattern
related_entries:
  - diagnostics/2026-07-04_bd-schema-migrations-version-fence-migrate-dirty-config-refusal.md
  - infrastructure/2026-05-15_diverged-git-remotes-content-equivalence-realign.md
  - methodologies/2026-06-25_bd-cross-store-sweep-nested-stores-dolt-state-diagnostic.md
  - diagnostics/2026-05-23_beads-multi-database-working-directory-gotcha.md
  - migrations/2026-05-21_cross-db-bead-migration-external-ref-provenance.md
---

# Same-shape schema, divergent history — 3-way merges fail when parallel migrations converge on identical current schema

## Pattern (the diagnostic frame)

A versioned-data system (dolt, Liquibase-with-git, Flyway-with-git, or any similar VCS-schema tool) can refuse to 3-way merge two branches even when their *current* schemas are byte-identical, if both sides reached that schema through *parallel independent migration commits*. The 3-way merge algorithm inspects the schema at the merge-base — which pre-dates both migrations — and compares primary keys / column shapes to each side. When the merge-base has a DIFFERENT primary key than either side (even though both sides now match each other), the merge fails.

## Concrete signature (dolt-specific, but the pattern generalizes)

```
Error: merge origin/main: Error 1105: error: cannot merge because
table <name> has different primary keys in its common ancestor
```

Verification commands (dolt) that confirm the pattern:

```bash
dolt diff --schema main remotes/origin/main -- <table>
# → EMPTY OUTPUT (schemas are identical NOW)

dolt diff --schema <merge-base-hash> main -- <table>
# → shows the local-side migration diff

dolt diff --schema <merge-base-hash> remotes/origin/main -- <table>
# → shows the remote-side migration diff (often IDENTICAL to local's diff — same migration, done twice)

dolt log --oneline main..remotes/origin/main | grep "schema:"
dolt log --oneline remotes/origin/main..main | grep "schema:"
# → both sides carry their own "schema: apply migrations" commit
```

## Root cause (when this actually fires)

Both machines running the same versioned-data tool independently auto-migrated the schema after a binary/tool upgrade. Each machine's migration ran locally and produced its own commit. The migrations converge on identical current shapes but the commit *paths* diverged. This is common in tool-managed schema evolution (dolt / bd, Rails migrations run in local envs, Alembic offline runs) where each environment applies migrations autonomously.

## When this applies

- Cross-machine sync of a versioned-data store where migrations are tool-triggered per-environment (not centrally applied)
- Long-running branches in a schema-migration setup
- Any dolt sync that fails with "different primary keys in common ancestor" while `dolt diff --schema HEAD remote/main` shows empty

## When this does NOT apply

- Genuinely conflicting schemas (both sides evolved DIFFERENT PKs) — that's a real conflict, not this pattern
- Data-only merge conflicts (row-level PK collisions) — different error class
- Single-machine dolt / VCS-DB usage without cross-machine sync

## Why the standard fixes don't work

- `dolt merge --squash`: still does the 3-way merge internally; hits the same check.
- `dolt merge --no-ff`: same.
- `dolt cherry-pick` of the local-only commits onto origin: works in principle but rejects the schema-migration commits since remote already has them at same current shape.
- `bd compact` / `bd flatten`: only rewrites local history; doesn't change what the shared merge-base is on the remote's side.
- Reset one side to the other: destroys real work.

## Safe recovery paths (ordered by data-preservation guarantee)

1. **Do nothing — accept broken sync.** Both machines operate on local store. Cross-machine visibility degrades. Not blocking as long as neither machine depends on the other's writes propagating.

2. **Manual data-level merge (data-preserving, high-effort):**
   - Snapshot laptop's affected tables to TSV.
   - Do the same on the remote side (or fetch origin/main into a scratch clone).
   - Compute laptop-only rows via row-ID diff.
   - Reset laptop to remotes/origin/main.
   - INSERT ... ON DUPLICATE KEY UPDATE the laptop-only rows.
   - Verify row counts + spot-check known-good rows.
   - Push.

3. **Force-push one side wins (destroys other side's unpushed commits).** Only safe when one side genuinely doesn't need the other's work.

**Prerequisite for any fix:** align the schema-migration-triggering tool version across ALL machines first. Otherwise the fix drifts again on the next parallel auto-migration.

## Grounding — actual case that produced this entry (2026-07-04, sem-tools repo)

sem-tools uses `bd` (beads) with an embedded dolt backend. Laptop and Mac Mini both auto-migrated the `dependencies` table's PK from compound `(issue_id, depends_on_id)` to surrogate `id UUID` after a bd binary upgrade. `bd dolt pull` failed with the signature above. Schemas confirmed byte-identical between local `main` and `remotes/origin/main`. Divergence stats: 228 local-only commits, 38 remote-only. Merge-base: pre-migration commit `saaes2bvdjfid7dvmpuhl6dv7ve3b70s`. User (advanced ops operator with real data-loss risk from options 2/3) chose "do nothing" and filed a tracker bead (sem-tools-4j7) with the full option matrix for deliberate later reconciliation.

## Sibling patterns to consider

- Rails migrations run in staging + production out of order can produce the same shape but different `schema_migrations` table history — Rails handles this via version tracking, but the same "identical shape, divergent history" pattern applies.
- Terraform state files diverged across two automation runners — different problem class but same "converged state, divergent history" frame.
- `infrastructure/2026-05-15_diverged-git-remotes-content-equivalence-realign.md` — related pattern for plain git remotes where the CONTENT is identical but SHAs differ; safe realignment via `git cherry` verification + force-push. That pattern's safety check does not transfer directly to dolt schema-migration divergence because the 3-way merge algorithm inspects the merge-base schema, not commit-content parity.
