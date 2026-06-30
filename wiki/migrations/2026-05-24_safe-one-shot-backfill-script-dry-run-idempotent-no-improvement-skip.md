---
title: Safe one-shot backfill script architecture — dry-run default + idempotent + skip-no-improvement
source_mode: builder
novelty_type: reusable_pattern
grounding_score: 0.80
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-24
tags: scripts, data-migration, backfill, dry-run, idempotency, python
related_entries:
  - wiki/migrations/2026-05-21_idempotent-multi-target-issue-tracker-migration-state-file-dependencies.md
  - wiki/migrations/2026-05-20_idempotent-additive-column-sqlite-migrations.md
  - wiki/infrastructure/2026-05-14_idempotent-watchdog-producer-pattern.md
  - wiki/methodologies/2026-05-13_find-consumer-first-before-data-migration.md
domain: migrations
topic: schema-evolution
---

# Safe one-shot backfill script architecture — dry-run default + idempotent + skip-no-improvement

## Pattern

For one-shot data backfills that update many rows in a production-shared database, the script must be safe to run repeatedly and impossible to apply accidentally. The pattern has four required properties:

### 1. Dry-run is the default

Running the script with no flags must NEVER modify data. `--apply` (or equivalent) is required to write. This makes accidental-Enter-after-paste safe and gives the operator confidence they can preview before committing.

```python
parser = argparse.ArgumentParser()
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()

if not args.apply:
    print("\nDry-run only. Re-run with --apply to write changes.")
    return 0
```

### 2. Print proposed changes before applying

A sample of the first N proposed changes goes to stdout regardless of mode. The user sees what would happen before committing to it, catching logic errors in the regeneration function early.

```python
print(f"Proposing {len(plan)} updates.")
print("\nSample (first 10):")
for row_id, old, new, preview in plan[:10]:
    print(f"  [{row_id[:8]}] {old!r} -> {new!r}  ({preview!r})")
```

### 3. Skip rows where the new value matches the old value

Trivially makes the script idempotent — re-running after an apply finds 0 updates instead of redoing work. Saves API calls, reduces churn in the audit log, and signals "all done" to the operator.

```python
def plan_updates(rows: list[dict]) -> list[tuple]:
    plan = []
    for row in rows:
        old = row.get(TARGET_COL) or ""
        new = regenerate(row)
        if new == old: 
            continue           # idempotency skip
        # ... rest of filtering
    return plan
```

### 4. Skip rows where the new value is no better than the old value

Domain-specific predicate (e.g., "the regenerated value falls into the same generic-label set"). Prevents the script from creating churn without improvement. The predicate is cheap and runs before the update plan is finalized.

```python
def plan_updates(rows: list[dict]) -> list[tuple]:
    plan = []
    for row in rows:
        old = row.get(TARGET_COL) or ""
        new = regenerate(row)
        if new == old: 
            continue           # idempotency
        if not is_improvement(new, old): 
            continue           # no-improvement skip
        plan.append((row["id"], old, new, preview(row)))
    return plan
```

## Concrete skeleton (Python + Supabase)

```python
def fetch_candidates(client, limit: int | None) -> list[dict]:
    """Page through candidate rows in batches; respect optional limit."""
    rows: list[dict] = []
    offset = 0
    while True:
        page_size = min(BATCH_SIZE, (limit - len(rows)) if limit else BATCH_SIZE)
        if page_size <= 0:
            break
        page = (
            client.table(TABLE)
              .select(SELECT_COLS)
              .in_(FILTER_COL, list(FILTER_VALUES))
              .order(ORDER_BY, desc=True)
              .range(offset, offset + page_size - 1)
              .execute().data or []
        )
        if not page: break
        rows.extend(page)
        if len(page) < page_size: break
        offset += page_size
        if limit and len(rows) >= limit: break
    return rows

def plan_updates(rows: list[dict]) -> list[tuple]:
    """Compute (id, old, new, preview) for rows that would be improved.
       Skip same-value (idempotency) and no-improvement cases."""
    plan = []
    for row in rows:
        old = row.get(TARGET_COL) or ""
        new = regenerate(row)
        if new == old: 
            continue           # idempotency
        if not is_improvement(new, old): 
            continue           # no-improvement skip
        plan.append((row["id"], old, new, preview(row)))
    return plan

def apply_updates(client, plan) -> int:
    updated = 0
    for row_id, _old, new, _preview in plan:
        result = client.table(TABLE).update({TARGET_COL: new}).eq("id", row_id).execute()
        if result.data: 
            updated += 1
    return updated

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    candidates = fetch_candidates(client, args.limit)
    print(f"Found {len(candidates)} candidate rows.")
    plan = plan_updates(candidates)
    print(f"Proposing {len(plan)} updates.")

    if not plan: 
        return 0
    
    print("\nSample (first 10):")
    for row_id, old, new, preview in plan[:10]:
        print(f"  [{row_id[:8]}] {old!r} -> {new!r}  ({preview!r})")

    if not args.apply:
        print("\nDry-run only. Re-run with --apply to write changes.")
        return 0

    print(f"\nApplying {len(plan)} updates...")
    print(f"Updated {apply_updates(client, plan)} rows.")
```

## When this applies

- Schema or value backfills against tables with thousands–millions of rows
- Any time the same script may run more than once (idempotency requirement)
- Production-shared databases where applying is reversible only with another backfill
- Cases where the new value is computed from the old row state, not from a fixed map
- Unattended / cron-scheduled backfills that must not fail silently or corrupt data on re-run

## When this does NOT apply

- One-row updates (just run the SQL)
- Append-only inserts (idempotency unnecessary or domain-specific via unique constraint)
- Time-sensitive cutover migrations (use a real migration tool with up/down)
- High-throughput streaming updates (different architecture entirely)
- Fixed-map rewrites where you're replacing every value uniformly (simpler than conditional re-generation)

## Operational benefits from the source session

**Dry-run safety caught two bugs before apply:**
1. **Pipeline-prefix artifact leaking into outputs** — regeneration logic included `[User's request: ...]` prefix that should have been stripped. Visible in the sample, fixed pre-apply.
2. **URL extractor returning trailing content** — the regenerated URL extractor captured everything after `https://` including trailing noise. Dry-run sample showed URLs like `https://example.com/path?utm_source=...extra-junk`. Fixed pre-apply.

**`--limit` flag:**
Spot-checking before full unfiltered run. With `--limit 10`, the operator exercises the same code paths but on a small cohort, catches edge cases, and gains confidence before the full run.

**Post-apply re-run idempotency:**
After applying 97 updates, re-running the script with no arguments returned "354 candidates → 0 proposed updates", confirming that idempotency skip prevented churn. The operator can be confident the job is truly done.

## Grounding

Verified by:
1. **Dry-run preview caught real bugs:** Two pre-apply bugs (artifact leaking, URL extraction) were visible in the sample output and were fixed before `--apply` was invoked.
2. **No-improvement skip prevented redundant updates:** Post-apply re-run on the 354-row candidate set resulted in 0 proposed updates (all rows matched old == new after the apply).
3. **Operator confidence in apply step:** The dry-run sample made the 97-row decision to apply unambiguous — the preview showed exactly what would change.
4. **Script reusability:** The same script architecture was used for multiple backfills in the session without modification; only the `regenerate()` and `is_improvement()` domain-specific functions changed per use case.

## Source Context

Pattern derived from [project] session 2026-05-23, backfill_analysis_titles.py (backend/scripts/backfill_analysis_titles.py). The script regenerated analysis metadata based on updated business logic, with the explicit requirement that the dry-run be legible and safe. The pattern emerged from two failed early attempts: (1) apply-by-default with a `--dry-run` flag (felt backwards and unsafe) and (2) skip-on-same-value without the no-improvement predicate (allowed churn). Final form: dry-run default + sample preview + idempotency + no-improvement skip delivered 97 successful, auditable updates with zero data corruption risk.

Reference implementation: `[project]/backend/scripts/backfill_analysis_titles.py` (commit ada7c2f, 2026-05-23).

## Anti-patterns to avoid

**Apply-by-default with `--dry-run` flag:**
```python
# DON'T do this:
if args.dry_run:
    print("DRY RUN: ...")
    # no changes
else:
    # apply changes
```

This is backwards. Operators expect the default behavior (no flags) to be safe. Flipping that expectation invites accidents.

**Skip-on-same-value without `is_improvement()` check:**
```python
# DON'T do this:
if new == old: 
    continue  # idempotency only
plan.append((row["id"], old, new, preview(row)))
```

Without the no-improvement check, the script can still create churn: rows that already have good values get re-flagged for update if the regeneration logic produces a different (but equally bad) output. The no-improvement predicate prevents this.

**Forgetting the sample print:**
```python
# DON'T do this:
plan = plan_updates(candidates)
if not args.apply:
    return 0  # silent dry-run
# apply when --apply is set
```

Silent dry-runs hide logic errors. The operator cannot audit what would change without actually reading the code. Always print a sample.

**Unlimited `--limit`:**
Not actually an anti-pattern, but combining `--limit 1000` with `--apply` can create very large transactions on shared databases. Consider batching:
```python
for batch in chunks(plan, BATCH_SIZE):
    apply_updates(client, batch)
    time.sleep(1)  # give the DB time to recover
```

## Related patterns

- **Idempotent multi-target issue-tracker migration** — similar philosophy (state file, skip-on-already-done) but for tracker records with dependencies
- **Idempotent watchdog producer pattern** — timestamps + state file to prevent redundant alarms (similar idempotency layer, different domain)
- **Find consumer first before data migrations** — methodological reminder to understand how the data is used before changing it (applies upstream of this pattern)
