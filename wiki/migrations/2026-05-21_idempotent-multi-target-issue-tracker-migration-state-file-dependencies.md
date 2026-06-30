---
title: Idempotent multi-target issue-tracker migration with state file + dependency reconstruction
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.75
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-21
tags: migrations, orchestration, infrastructure, idempotency, state-file, dependency-graph
related_entries:
  - wiki/migrations/2026-05-20_idempotent-additive-column-sqlite-migrations.md
  - wiki/migrations/big-bang-rename-supabase-fastapi-react.md
  - wiki/infrastructure/2026-05-14_idempotent-watchdog-producer-pattern.md
  - wiki/orchestration/2026-05-13_one-reconciliation-pipeline-called-twice.md
domain: migrations
topic: schema-evolution
---

# Idempotent multi-target issue-tracker migration with state file + dependency reconstruction

## Problem

A shared issue tracker accumulates issues belonging to N different projects under a single namespace, making it hard to triage per-project work, query "what's open for project X", or hand off to a project-local agent. The natural move is to split the shared tracker into project-local databases — but a naive "create new + close old" loop has three failure modes:

1. **Partial-run resumption** — if the migration is interrupted mid-stream (network blip, permission prompt, OOM), naively re-running creates duplicates.
2. **Lost dependencies** — issue A depends on issue B. If both migrate to the same target, the dependency must be reconstructed with the *new* IDs, not the old ones. If only A migrates and B stays behind, the dependency becomes cross-database and is silently dropped.
3. **Lost out-of-bucket context** — when A depends on something that stays in the source DB (because it belongs to a different project), the link is gone. The new A bead loses a load-bearing piece of context.

## Pattern

Implement migration as a Python script with three phases per target:

```python
state = load_state()                # /tmp/<job>-state.json

for target in targets:
    ensure_target_db_exists(target) # idempotent init (skip if exists)

    # PHASE 1 — create + tag
    for bead in manifest[target]:
        if bead.old_id in state.id_map:    # already migrated — skip
            continue
        new_id = create_in_target(bead)
        state.id_map[bead.old_id] = new_id
        save_state(state)                    # persist after EVERY step
        for label in bead.preserved_labels + ["to-review"]:
            tag(new_id, label)

    # PHASE 2 — reconstruct in-bucket dependencies
    in_bucket = {b.old_id for b in manifest[target]}
    for bead in manifest[target]:
        for dep in bead.deps:
            if dep in in_bucket:
                dep_add(state.id_map[bead.old_id], state.id_map[dep])
            else:
                # Cross-bucket / stays-in-source — preserve as a note,
                # don't silently drop
                add_note(state.id_map[bead.old_id],
                         f"Migration note: previously depended on {dep} (cross-DB)")

    # PHASE 3 — close source beads
    for bead in manifest[target]:
        if bead.old_id in state.closed:
            continue
        close_source(bead.old_id,
                     reason=f"Migrated to {target} as {state.id_map[bead.old_id]}")
        state.closed.append(bead.old_id)
        save_state(state)
```

## Key invariants

1. **Save state after every step**, not at end of phase. Interruptible at any point.
2. **Two-pass dependency reconstruction.** Create all new beads first to build the full `old_id → new_id` map, then reconstruct deps in a second pass. Otherwise you'll try to add a dep on something that hasn't been created yet.
3. **Three classes of dependency**, three different actions:
   - In-bucket → `dep_add(new_id, new_dep_id)`
   - Cross-bucket (to a bead in a different target) → cross-DB dep is impossible; preserve as note, surface to user for manual cross-reference
   - Stays-in-source (depends on a bead not migrating) → also preserve as note
4. **Tag every migrated bead with a review marker** (e.g. `to-review`) so the human can audit whether the work is genuinely still open or was completed elsewhere during the gap.
5. **Pre-dump the manifest to a separate file** before the migration starts. The migration reads from the manifest; the manifest is data; data is reviewable + rerunnable. Don't embed the issue list in the script body.
6. **Run smallest target first** as a dry-run-equivalent. Two beads exercise the same code paths as forty; only the cumulative blast radius differs. If something is wrong, you find out cheaply.

## When this applies

- Migrating issues between any two issue-tracker databases (beads, GitHub Issues, Jira, Linear, …)
- Splitting any structured store with cross-record references (knowledge bases, CMS content with internal links, RBAC policies referencing groups)
- Any "move N records from one place to another and preserve their relationships" job

## When this does NOT apply

- The records have no internal references — flatten to `xargs` or a one-liner
- The source tracker has a built-in `migrate` or `export+import` command — use that, don't reimplement
- Volume is small (< 5 records) and you can eyeball each one — manual is faster than scripting

## Reference implementation

`scripts/migrate-beads-to-projects.py` in `~/Scripts/[project]/` (commit 5ce8915) — concrete instance for [project] → [project]/knowledgeforge-cc/claude-orchestra-dev. State file at `/tmp/beads-migration-state.json`, manifest at `/tmp/migration-manifest.json`. Migrated 59 beads cleanly on first real run after one dry-run pass.

## Operational learning

The "smallest target first" rule paid off here: the orchestra bucket had only 2 beads, exercised create+tag+close paths fully, and proved the script before committing to the 40-bead COS migration. When the KF migration completed and 3 beads (puh, 5ae, m9o) showed as still-open in the source DB despite being marked closed in state, it was a small enough cohort to manually catch and recover. On a 40-bead migration that detection-and-recovery would have been much more painful.

## Source context

Pattern derived from [project] beads project-separation task (2026-05-20). [project] accumulated 59 beads across three logical projects ([project] core, COS, knowledgeforge). A shared beads database made per-project prioritization impossible. Splitting required moving records and preserving dependency chains that spanned multiple bucket boundaries. Initial attempt (batch close + manual re-open) lost cross-project dependencies; iteration led to the three-phase model with dependency reconstruction and state file idempotency.
