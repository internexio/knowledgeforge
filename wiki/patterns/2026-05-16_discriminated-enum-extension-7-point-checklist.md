---
title: Extending a discriminated enum across the full stack — 7-point checklist
source_mode: direct
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-16
tags: [patterns, type-safety, discriminated-union, enum, refactoring, full-stack]
related_entries: [patterns/2026-05-14_collapse-usestate-discriminated-union-reducer.md, patterns/mode-variants-taxonomy.md, migrations/big-bang-rename-supabase-fastapi-react.md]
---

# Extending a discriminated enum across the full stack — 7-point checklist

Adding a new variant to a discriminated enum (string union in TS, Python `Enum`, Postgres `CHECK` constraint, etc.) typically requires touching every place the type is **closed over**: validators, switch/match statements, exhaustive-check functions. Missing any one of them means a runtime failure or, at best, a type-check failure caught at the *next* commit.

This is the **checklist** to walk before declaring the enum extension done. Tested on the COS Buyers Committee `GenerationMode` enum (adding `library_only` as a fourth variant). One miss surfaced: a TS `switch (mode)` with no default case caused `typecheck` to fail with "Function lacks ending return statement and return type does not include 'undefined'." That was the catch — without it, the runtime would have rendered `undefined` in the UI silently.

## The 7-point checklist (work the layers top-to-bottom)

**1. Database CHECK constraint**

If the column is `TEXT NOT NULL CHECK (col IN (...))`, write a migration that drops the old constraint (by name) and adds the new one with the additional value. If the column appears in multiple tables, update all of them. 

**Important:** Constraint names may have changed via prior rename migrations. Query `pg_constraint` for the actual current name before authoring `DROP CONSTRAINT IF EXISTS`. See also `migrations/verify-fk-target-table-remote-before-migration.md` for the parallel "verify what's actually on the remote" diligence.

**2. Backend enum**

Add the new variant to your backend enum (Python `Enum`, TypeScript `string` union, Go `iota`, etc.). Include a docstring comment explaining **when** it applies — semantic meaning, not just symbolic.

**3. Request-level Pydantic / DTO validators**

If the request has cross-field validation that depends on the enum value, extend it. Example: `_validate_request_for_mode` in a request handler may have per-mode validation; adding a new mode requires a new branch. These validators are easy to miss because the request may have passed Pydantic and "looked done" before you hit the per-mode behavior gates.

**4. Per-endpoint behavior gates**

Endpoints that adjust behavior based on the enum (e.g., "skip the LLM-key requirement for the LLM-free mode") need a branch for the new variant. This is frequently overlooked because the endpoint may have passed Pydantic validation and "looked done" before the behavior gate applies.

**5. Frontend type union**

Add the new variant to your TS literal-union type definition (`type Mode = 'a' | 'b' | 'c' | 'new'`). Without this, the new variant comes through as `never` in type narrowing, breaking any downstream switch/match logic.

**6. UI selection surfaces**

The user has to be able to *choose* the new variant for the rest of the stack to ever see it. Update:
- `<select>` options
- Button rows or radio groups
- Command palettes
- Any other surface where the user selects from the enum

Missing this means the new variant is unreachable from the UI, defeating the entire feature.

**7. `switch (mode)` / exhaustive checks**

Every place the enum is closed over in switch/match form, including helper functions like `formatMode()` or `iconForMode()`. 

**⚠️ This is the trap that surfaced in cos-3bu.7.1**: A `formatGenerationMode(mode: GenerationMode): string` function with three cases broke typecheck when the fourth variant was added. The TS compiler caught it as "Function lacks ending return statement and return type does not include 'undefined'." In a language without exhaustiveness checking (or with permissive switches that default to undefined), this would have rendered `undefined` at runtime silently.

## Bonus — places that often DON'T need to change (but check anyway)

- **State stores** (Zustand, Redux) — only need a default if the new variant changes the initial-state shape.
- **DB migration of existing rows** — only needed if the new variant *replaces* an existing one. Pure additions don't require data migration.
- **API documentation / OpenAPI schemas** — auto-generate or update by hand depending on your tooling.

## When to apply

- Adding a variant to any discriminated enum that crosses stack boundaries (DB → backend → API → frontend).
- Refactoring an existing enum (renaming or removing a variant has its own deletion checklist; this list is for **additions only**).

## When NOT to apply

- **Internal-only enums** that never escape one module — only the consumers in that module need updating.
- **Open-ended sum types** where consumers handle `unknown` explicitly — no exhaustiveness contract to violate.

## Concrete grounding from cos-3bu.7.1 (COS BC library_only mode, 2026-05-16)

Adding `library_only` as the fourth `GenerationMode` value required all 7 points:

1. **Migration 101** (`cos/supabase/migrations/101_bc_library_only_generation_mode.sql`) — dropped and re-added the CHECK constraints on `buyers_committee_cohorts` and `buyers_committee_cohort_presets`. The cohort constraint name was `de_cohorts_generation_mode_check` (survived the 071 de→bc rename); the presets constraint was `chk_bc_presets_generation_mode` (defined fresh in migration 077). Confirmed via `SELECT conname FROM pg_constraint` before authoring.

2. **Backend enum** — `GenerationMode.library_only = "library_only"` added to `cos/backend/app/buyers_committee/models.py`.

3. **Request validators** — `_validate_request_for_mode` in `cos/backend/app/buyers_committee/cohort_generator.py` got a new branch enforcing `library_persona_ids` non-empty + count == size + no archetype_seed_slugs + no duplicates.

4. **Behavior gate** — `create_cohort` in `cos/backend/app/api/buyers_committee.py` got a `library_only = (payload.generation_mode.value == "library_only")` short-circuit that bypasses the Anthropic-key check (no LLM call needed for library_only mode).

5. **Frontend type** — TS union `GenerationMode` in `cos/frontend/src/features/buyers-committee/types.ts` extended with `| 'library_only'`.

6. **UI surface** — `<select>` in `CohortBuilder.tsx` gained the fourth option. New conditional surface (`LibraryPersonaPicker`) renders instead of `ArchetypeSeedPicker` when this mode is active.

7. **Exhaustive check** — `formatGenerationMode(mode: GenerationMode): string` in `cos/frontend/src/features/buyers-committee/components/CohortPresetsPanel.tsx` had three cases. Typecheck failed: "Function lacks ending return statement and return type does not include 'undefined'." Added the fourth case (`case 'library_only': return 'Library only';`). Without TypeScript's exhaustiveness check, the function would have returned `undefined` and the cohort-presets panel would have rendered "undefined" labels.

**Total slip:** ~60 seconds of typecheck-fix when the omission surfaced. Could have been hours in a less typed environment or if there were no compile gate before runtime.

## When this applies beyond type systems

This pattern generalizes to any system where:
- A closed-over type accumulates variants
- Downstream consumers must handle all variants
- Exhaustiveness checking (or at least type feedback) exists

Examples:
- GraphQL union types
- Protocol buffer `oneof` fields
- Event type enums in event-sourced systems
- Feature-flag enum variants in multi-tenant systems

## Source Context

Sourced from COS Buyers Committee work (session cos-3bu.7.1, 2026-05-16). Adding `library_only` as the fourth `GenerationMode` value. The catch: a `formatGenerationMode()` helper with three cases broke typecheck when the fourth was added, surfacing the incomplete refactoring before runtime. Without TypeScript's exhaustiveness checking, the helper would have returned `undefined` silently, rendering broken UI labels. The checklist captures the 7 layers that must be touched to consider an enum extension complete.
