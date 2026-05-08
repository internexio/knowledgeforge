# Codemod-Driven Big-Bang Rename: Phase-0-Gated Migration Pattern

```yaml
metadata:
  source_mode: coordinator
  source_session: redacted
  created: "2026-05-05T00:00:00Z"
  date: "2026-05-05"
  confidence: 0.85
  grounding_score: 0.85
  grounding_source: "Empirical: cos-bfm migration applied to staging end-to-end. 13 tables + 39 indexes + 12 RLS policies + 1 view + 1 function renamed in single transaction; codemod applied across two repo worktrees; all 8/8 validation gates passed. Phase 0 inventory found 0 user-data rows + 0 API traffic in 14d, validating big-bang strategy choice."
  novelty_type: process_pattern
  staleness_risk: low
  importance: 3
  pinned: false
  accreted_in: "6.x"
  related:
    - wiki/migrations/big-bang-rename-supabase-fastapi-react.md  # Execution playbook (filed post-deploy 2026-05-08; gotchas + SQL patterns)
    - wiki/orchestration/spec-commit-before-impl-commit.md
    - modules/02_builder.md
    - modules/06_coordinator.md
```

---

## Pattern

When renaming a domain concept that touches schema, code, configuration, and routes simultaneously, the default instinct is **dual-naming with a deprecation window** — keep both names alive, route traffic to either, drift back when load is observed.

The dual-naming approach pays a permanent tax in:
- Doubled API surface (legacy + new endpoints both registered)
- Conditional logic at every read site (which name does this row use?)
- Half-finished states that ossify when the deprecation deadline passes without action

For a rename that is genuinely one-way and has either zero or trivial production traffic on the legacy surface, **codemod-driven big-bang** is the durable response: rewrite all references in a single transaction, deploy in lockstep, bake briefly, delete the old name from history.

The pattern is gated on a Phase 0 traffic check, not on subjective judgment of "how risky" the rename feels.

---

## Sequence

| Phase | Output | Gate to next phase |
|---|---|---|
| **0 — Inventory** | Migration inventory MD: legacy-name reference count, user-data row count, 14d API traffic on legacy routes, RLS policy enumeration, env-var enumeration | If user-data rows > 0 OR legacy API traffic > 0: STOP, switch to dual-naming. Otherwise proceed. |
| **1 — Codemod** | Single Python script with explicit `STRING_REPLACEMENTS`, `TABLE_RENAMES`, `INDEX_RENAMES`, `CONFIG_FIELD_RENAMES`, `PATH_REPLACEMENTS`, `PATH_RENAMES`, `HISTORICAL_DIR_MOVES`. `--dry-run` mode shows all touched files; `--apply` rewrites in place. Idempotent on re-run. | Dry-run output reviewed; no surprises. |
| **2 — Migration SQL** | Up + down migrations renaming tables, indexes, policies, views, functions in one transaction. Body recreations (views, functions) preserved verbatim with new identifiers. **No fragile DO blocks** scanning system catalogs with LIKE patterns — fixed lists only. | Tested up + down on staging clone if data exists; skipped if Phase 0 confirmed zero data. |
| **3 — Codemod apply** | Apply codemod across all repo worktrees (cos-platform + cos), commit. | Lint + typecheck + tests pass on renamed code. |
| **4 — Migration apply** | Apply migration to staging DB just-in-time before code deploy. | Validation queries: zero rows in `pg_class` matching `LIKE 'old_*'`; expected count matching new prefix. |
| **5 — Validation gates** | 8-point gate sheet: schema validation, OpenAPI surface check, frontend renders new routes, env-var read, e2e API hit returns expected payload, no `old_name` matches in deployed bundle, RLS still enforces on renamed tables, baseline metrics steady. | All 8 must pass. |
| **6 — Bake + delete window** | 24h post-deploy bake on staging. Rollback-ready window: down migration tested, codemod inverse documented. After bake, replicate to production. | No errors attributable to rename in 24h. |

---

## Why This Survives

- **Phase 0 traffic check makes the decision deterministic.** "Is this rename safe to big-bang?" becomes a measurement, not a judgment call. Zero traffic + zero rows = green-light. Anything else and the pattern bails out to dual-naming on its own.
- **Codemod is reviewable as data, not code.** The replacement tables (`STRING_REPLACEMENTS = {...}`) are diffable, auditable, and grep-checkable. Reviewers can verify completeness without reading executable logic.
- **Single-transaction migration removes the half-renamed state.** Either every table renamed or none — no scenario where reads succeed but writes fail because half the schema moved.
- **Lockstep deploy fits codemod + migration into one window.** Codemod commits the code that expects new names; migration applies the new names; both ship together. The commit history reads cleanly.

---

## Anti-Patterns

**"Add views as compatibility shims so old code keeps working."** This installs permanent state. The shim survives the rename and becomes a source of confusion for the next person reading the schema. Only acceptable if Phase 0 found > 0 production traffic — and then the right answer is dual-naming, not shims.

**Constraint-rename DO blocks scanning `pg_constraint` with `LIKE 'old_%'` patterns.** These are fragile across pg versions, opaque under transaction rollback, and mostly cosmetic (constraints reference tables by OID, not name). Drop them. Rename constraints explicitly if at all.

**Codemod-then-deploy without applying migration first.** If the deploy lands before the migration applies, every read against the (still-old-named) DB fails with `relation does not exist`. Mitigate by sequencing migration apply *before* code deploy, or by running both in a single deploy script. The 0-traffic Phase 0 finding is the safety net when this race is unavoidable.

---

## Reuse Heuristics

Reach for this pattern when **all four** hold:

1. The rename is final — no reason to keep the old name reachable
2. Phase 0 inventory shows zero or near-zero production traffic on legacy surface
3. The rename touches multiple layers (schema + code + config + routes) so dual-naming would multiply maintenance load
4. A rollback window exists (staging-first deploy, before production replication)

Skip this pattern when:

- External consumers (third-party API clients, partners) hit the legacy name — dual-naming is mandatory
- The rename is partial / experimental — keep both names and let usage decide
- You can't run a Phase 0 traffic check (instrumentation gap → either fix instrumentation first or default to dual-naming)

---

## Evidence

The cos-bfm DE→BC rename (May 2026) executed this pattern end-to-end:

- Phase 0: `migration_inventory_2026-05-05.md` documented 0 user-data rows, 0 API traffic on `/api/de/*` in 14d, RLS uses `auth.uid() OR get_session_id()` (not the renamed field)
- Codemod: `migrate_de_to_bc.py` (411 lines, 7 replacement tables) — applied in both `cos-platform/` and `cos/` worktrees
- Migration: `071_rename_decision_ensemble_to_buyers_committee.sql` renamed 13 tables, 39 indexes, 12 RLS policies, 1 view, 1 function in one transaction
- First Studio apply failed (42P01) — root cause was a constraint-rename DO block; removed it as cosmetic; second apply succeeded
- 8/8 validation gates passed including end-to-end auth'd API call returning 10 archetype records from the renamed table
- 24h bake initiated before production replication
