---
title: Schema evolution via additive optional fields + tolerant reads
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.9
grounding_source: "Verified repeatedly in [project] iteration_loop across four independent format bumps (2026-05-24..05-29): pydantic schema versioning, heartbeat schema 1.0.0→1.1.0, tier3_demotion state file 1.0→1.1, pending-suggestions.jsonl kind-discriminator + optional fingerprint field. Referenced as a dependency by orchestration/2026-05-29_append-only-queue-fingerprint-dedup-reconcile-gc.md."
staleness_risk: stable
importance: 4
domain: migrations
topic: schema-evolution
tags: [schema-evolution, backward-compatibility, optional-fields, tolerant-reader, jsonl, state-files, zero-migration, versioning, additive-change]
related_entries:
  - orchestration/2026-05-29_append-only-queue-fingerprint-dedup-reconcile-gc.md
  - migrations/2026-05-20_idempotent-additive-column-sqlite-migrations.md
  - migrations/2026-05-21_expand-contract-column-rename-sqlite-commit-boundary.md
created: 2026-06-12
pinned: false
---

# Schema Evolution via Additive Optional Fields + Tolerant Reads

## The Pattern

When you need to evolve the format of a **self-describing record store** — a
JSONL queue, an append-only log, a JSON/TOML state file, a heartbeat envelope —
the cheapest safe migration is often **no migration at all**:

1. **Add every new field as `Optional[T] = None`** (or the language equivalent).
2. **Make the reader default missing fields to `None`** rather than requiring them.
3. **Bump a version constant for documentation**, but **do not gate reads on it**.

Existing writers keep emitting the old shape (still valid — the new fields are
optional). New writers populate the new fields. Old and new records coexist in
the same file or table indefinitely. No backfill script, no stop-the-world
rewrite, no dual-read/dual-write window.

This works precisely because the records are **self-describing** (each carries
its own fields) and the consumer is a **tolerant reader** — it reads what is
present and assumes a default for what is absent.

## Why It Is Safe

The invariant: *an old record is a new record with the optional fields unset.*
If that statement is true for your change, the change is purely additive and
needs no migration. If it is false — you renamed a field, changed a field's
type, made a previously-optional field required, or changed the meaning of an
existing value — then this pattern does **not** apply and you need a real
migration (expand-contract rename, two-phase coercion, etc.).

## The Companion: Kind-Discriminator Over Parallel Files

When the new shape is a genuinely new *record type* (not just new fields on an
existing type), add a new value to an existing `kind=`/`type=` discriminator
field rather than creating a parallel file. Consumers filter on the
discriminator; coexistence is free; cross-record ordering is preserved (useful
for replay); no new lock, no new directory, no new reader. The cost is a single
line in the schema doc explaining the new discriminator value.

## When It Applies

- **JSONL queues / append-only logs** with a re-running producer and a tolerant
  consumer. Adding a field (e.g. a dedup `fingerprint`) is additive; readers
  compute a fallback for rows that predate it.
- **JSON / TOML state files** read by a single owner. Pre-bump files read
  cleanly with the new optional fields defaulting to `None`.
- **Versioned envelopes** (heartbeats, telemetry) where the version is metadata,
  not a read gate.
- **Codegen-derived schemas** (TOML→pydantic, OpenAPI→client) where bumping the
  spec adds optional fields and regenerates — existing consumers that import the
  version constant (rather than hardcoding it) keep passing unchanged.

## When This Does NOT Apply

- **Field rename, type change, or semantic change** of an existing field — use
  expand-contract or a two-phase migration; additive optionality cannot express
  a rename safely.
- **Making a previously-optional field required** — old records lack it; the
  reader can no longer default. That is a contracting change, not an additive
  one.
- **Primary/relational data with referential constraints** — a SQLite/Postgres
  schema with FKs and NOT NULL columns needs a real (idempotent, additive-column)
  migration; see the SQLite additive-column entry. The *philosophy* transfers
  (additive + tolerant) but the mechanism differs.
- **Consumers that strictly validate against a fixed schema version** and reject
  unknown/extra fields. Make the reader tolerant first, or this pattern breaks
  on the first new field.

## Concrete Grounding

Verified four times in [project]'s iteration-loop during 2026-05-24..05-29,
each a format bump shipped with zero migration script:

- **tier3_demotion state file 1.0 → 1.1** — added `envelope`, `resume_token`,
  `state_schema_version` as optional; pre-P.3 state files read cleanly with
  `envelope=None, resume_token=None`.
- **heartbeat schema 1.0.0 → 1.1.0** — tests imported the `SCHEMA_VERSION`
  constant rather than hardcoding it, so the bump propagated and existing tests
  passed unchanged.
- **pending-suggestions.jsonl** — added `kind="pending_question"` alongside the
  existing `baked_proposal | watchdog_event | legacy_suggestion` discriminator
  values instead of creating a parallel `pending-questions.jsonl`; later added an
  optional `fingerprint` field for dedup, with the reader computing a fallback
  from the body for pre-fingerprint rows.
- **pydantic response schemas** — `model_json_schema()` output fed straight to
  `claude --json-schema`; optional `Field(default=None, ...)` produced the
  matching JSON-Schema keywords with no manual schema surgery.

## Cross-References

- [[append-only-queue-fingerprint-dedup-reconcile-gc]] — adds an optional
  `fingerprint` envelope field using exactly this pattern (tolerant read via
  `env.get("fingerprint") or _compute_from_body(...)`).
- [[idempotent-additive-column-sqlite-migrations]] — the relational-database
  analogue when the store is SQL with constraints rather than self-describing
  records.
- [[expand-contract-column-rename-sqlite-commit-boundary]] — the pattern to
  reach for when the change is a *rename* and additive optionality is not enough.
