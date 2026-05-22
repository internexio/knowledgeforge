---
title: Cross-DB bead migration with external-ref provenance tracking
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.75
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-21
tags: orchestration, deployment, empirical
related_entries:
  - wiki/migrations/2026-05-21_idempotent-multi-target-issue-tracker-migration-state-file-dependencies.md
  - wiki/architecture/2026-05-18_bead-as-context-anchor-deferred-runbooks.md
---

# Cross-DB bead migration with external-ref provenance tracking

## Problem

A bead's natural home is a different project than the one it was created in:
- Mislabeled at creation (tagged for project A, should belong to project B)
- Project boundaries shifted (team reorg, repo split)
- Existing filters caught items that belong elsewhere

Each project has its own per-project bead database (`.beads/[project].db`). The source DB is the historical record; the target DB is the live workspace. Moving beads manually is error-prone; no built-in `bd migrate` command exists. A naive "create + close" loop loses the audit trail linking old ID to new ID.

## Pattern

**Three-step migration via JSON export + recreate + close:**

### Step 1: Export source beads as JSON

```bash
bd --db ../[source_project]/.beads/[source_project].db \
  list --label=[your-label] --json > /tmp/source.json
```

Use `--label` to filter: only export beads tagged with a label you control. This avoids exporting unrelated beads.

### Step 2: Recreate in target DB with external-ref + provenance note

In the target project's directory, for each source bead:

```bash
bd create \
  --title="$title" \
  --description="$description" \
  --type=$type \
  --priority=$priority \
  --external-ref="[source_project]:$source_id" \
  --notes="Migrated from [source_project] beads DB on $(date -I)" \
  --label="migrated-from-[source_project]"
```

**Key invariants:**
- `--external-ref="[source_project]:$source_id"` preserves the original ID for provenance lookup. Format: `[project]:[id]` for clarity.
- `--notes` carries the human-readable migration trail (source DB, date).
- `--label="migrated-from-[source_project]"` allows querying all migrated beads in bulk if needed.

### Step 3: Close source beads

In the source project:

```bash
bd --db ../.beads/[source_project].db close $source_id \
  --reason="Migrated to [target_project] as $new_id; see external-ref"
```

**Why closing matters:** Prevents the bead from appearing in `bd ready` on either side. Avoids duplicate-claim risk across projects.

## Why this is the right pattern

**One-way migration only.** Source DB is the historical record; target is the live workspace. No two-way sync complexity.

**External-ref is the audit trail.** Every migrated bead can be traced back to its origin: `bd show <new_id> | grep external-ref`. No manual cross-referencing needed. Future sessions can spot-check provenance.

**Uses only first-party bd commands.** No DB-file copy, no schema munging, no Dolt-specific operations. Survives bd version upgrades.

**Closing source prevents duplicate work.** Once a bead is closed, `bd ready` doesn't surface it. The human never accidentally claims the same work twice across projects.

## When to apply

- Beads mislabeled at creation and need reclassification
- Team reorg or repo split moved work to a new project's responsibility
- Consolidating multi-project tracking into per-project databases
- Ensuring each per-project bead DB is the source of truth for that project's work

## When NOT to apply

- Source DB is canonical and target is just a consumer → use `bd search` and external links instead
- You need bidirectional sync → beads has no such feature; don't fake it with this pattern
- Volume is very small (<3 beads) → manual re-creation is faster

## Operational notes

**Dry-run first.** Export to JSON, inspect manually, test the recreate + close cycle on 1–2 beads before automating the full batch.

**Label-based filtering in Step 1 avoids accidents.** Only export beads tagged with a label you control. This prevents exporting beads that shouldn't move.

**Closing source with reason is non-negotiable.** The reason field becomes the audit trail. Future sessions reading the source DB see "migrated to X" and know not to chase this up again.

**Script the full loop.** Three steps are simple enough to script once:

```bash
#!/bin/bash
SOURCE_PROJECT="[project]"
TARGET_PROJECT="sem-tools"
MIGRATION_LABEL="to-sem-tools"

# Export
bd --db ../$SOURCE_PROJECT/.beads/$SOURCE_PROJECT.db \
  list --label=$MIGRATION_LABEL --json > /tmp/export.json

# For each bead in /tmp/export.json:
# - cd $TARGET_PROJECT && bd create --external-ref="$SOURCE_PROJECT:$id" ...
# - bd --db .../$SOURCE_PROJECT close $id --reason="Migrated..."

# Alternative: use jq + xargs for batch processing if confident
```

## Reference implementation

The sem-tools project migrated 5 beads from [project]/.beads/[project].db on 2026-05-21 using this pattern. All 5 successfully created, source beads closed with migration reason, external-ref links verified with `bd show`.

## When this complements the other pattern

See also: **Idempotent multi-target issue-tracker migration with state file + dependency reconstruction** (Module 21, 2026-05-21). That pattern handles **complex many-to-many migrations with dependency reconstruction** across bucket boundaries. Use it when:
- Moving beads between 3+ targets
- Preserving cross-project dependencies is critical
- You need idempotency to recover from mid-run failures

This pattern is **lighter-weight and one-directional** — use it when:
- Moving beads one or two at a time to a single target
- Source DB is historical, target is live
- Simplicity matters more than crash-recovery

## Source context

Pattern derived from sem-tools beads project-separation task (2026-05-21). The knowledgeforge-cc project needed beads from [project] (a sibling project's Dolt-backed database) moved into its own per-project DB. The `external-ref` discipline ensures every migrated bead can be traced back to its origin for audit purposes. The pattern generalizes to any cross-DB bead transfer in multi-project setups using per-project beads databases.
