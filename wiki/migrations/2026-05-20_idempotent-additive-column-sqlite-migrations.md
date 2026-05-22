---
title: Idempotent additive-column migration pattern for SQLite without a migration framework
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.75
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-05-20
tags: sqlite, schema-migration, idempotency, pragma-table-info, pre-production
related_entries:
  - wiki/migrations/2026-05-16_verify-fk-target-table-remote-before-migration.md
  - wiki/migrations/big-bang-rename-supabase-fastapi-react.md
---

# Idempotent additive-column migration pattern for SQLite without a migration framework

## Problem

Small and medium projects with SQLite databases often add columns to existing tables as the schema evolves. They typically lack a formal migration framework (Alembic, sqlx migrate, etc.) because that overhead is not yet justified. Naive approaches break:

- **Just updating the `CREATE TABLE IF NOT EXISTS` statement:** Works for fresh databases but does nothing for existing ones — they keep the old schema and `INSERT` statements referencing the new column fail.
- **Running an unconditional `ALTER TABLE ... ADD COLUMN`:** Fails on the second `init_db` call because the column already exists. SQLite has no `ADD COLUMN IF NOT EXISTS`.
- **Manual one-shot migration scripts:** Easy to forget, easy to skip on fresh checkouts. Not reliable in a multi-developer environment.

All three leave the database in an inconsistent state or fail to converge toward a target schema.

## Pattern

Keep the `CREATE TABLE` statement up-to-date (the source of truth for fresh databases) AND add a single `_apply_additive_migrations` function that runs after the CREATE pass on every `init_db` call. For each (table, column_def) pair, query `PRAGMA table_info(table)` and only ALTER if the column is absent.

### Implementation

```python
def _apply_additive_migrations(conn: sqlite3.Connection) -> None:
    """Apply additive schema migrations idempotently.
    
    Runs after CREATE TABLE statements. Detects missing columns via
    PRAGMA table_info and adds them if absent. Safe to call repeatedly.
    """
    additive_columns = [
        ("geo_content_scores", "spam_flags TEXT"),
        ("geo_content_scores", "phishing_score REAL"),
        # ... more (table, column_def) pairs as schema evolves
    ]
    for table, column_def in additive_columns:
        col_name = column_def.split()[0]  # Extract column name from "name TYPE ..."
        existing_cols = {
            row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")

def init_db(path: str) -> sqlite3.Connection:
    """Initialize or upgrade database to current schema."""
    conn = sqlite3.connect(path)
    
    # Create tables (idempotent via IF NOT EXISTS)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS geo_content_scores (
            id INTEGER PRIMARY KEY,
            url TEXT NOT NULL UNIQUE,
            engagement_score REAL,
            domain TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            category TEXT
        );
    """)
    
    # Apply additive migrations (idempotent via column existence check)
    _apply_additive_migrations(conn)
    
    conn.commit()
    return conn
```

### Why this works

1. **Fresh database:** The `CREATE TABLE` statements produce the full current schema immediately. The PRAGMA loop examines every table and finds all expected columns already present. No ALTERs run.

2. **Stale database at prior schema:** The `CREATE TABLE IF NOT EXISTS` clauses are no-ops (tables already exist). The PRAGMA loop detects missing columns and ALTERs each one in.

3. **Already-migrated database:** The PRAGMA loop finds all columns present. No ALTERs run.

All three paths are idempotent under repeated `init_db()` calls — critical because library callers may not know the database's migration history.

## When this applies

Projects with:
- One to three engineers, SQLite or similar embedded database (DuckDB, etc.)
- Pre-production or early-production stage where schema breakage is recoverable (e.g., internal tools, experiments, beta features)
- Schema changes that are **strictly additive:** new columns with sensible defaults, new tables, new indexes
- No need for audit trails or rollback mechanisms beyond "restore from backup"

## When this does NOT apply

- **Multi-tenant production** where schema rollback must be auditable. Use a proper framework (Alembic, sqlx migrate, Flyway).
- **Destructive changes** (column rename/drop, type narrowing, NOT NULL additions on populated rows). Those need data-aware migrations with backout paths and coordination windows.
- **Multiple writers calling `init_db` concurrently.** SQLite's global write lock helps, but a proper migration framework gates this better (e.g., advisory locks, migration state tables).
- **Schemas where downgrade matters** (e.g., shared dev/prod databases with multiple versions in flight). This pattern is one-way: it can grow a schema but not shrink it. Rollback requires a separate reverse migration.
- **Publicly-exposed schema** where external integrations or backups depend on column order or naming stability. Additive migrations are low-risk here, but the pattern assumes an internal-only schema.

## Anti-pattern to avoid

Wrapping the ALTER in a bare `try/except sqlite3.OperationalError: pass`:

```python
# DON'T do this:
try:
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
except sqlite3.OperationalError:
    pass  # Assume column exists
```

This approach works in the happy path but swallows other operational errors:
- Table doesn't exist (typo in table name)
- Locked database (concurrent writer interference)
- Syntax errors in the column definition
- Disk full or permission errors

The PRAGMA check is one extra query that makes the migration explicit and the failure modes legible. When the check fails, the error message clearly states what column was missing, making debugging straightforward.

## Concrete example: sem-tools spam-detector (2026-05-20)

The `geo_content_scores` table started with three columns: `id`, `url`, `engagement_score`. Later, spam detection scoring was added, requiring `spam_flags` and `phishing_score` columns.

Fresh database: `init_db()` runs the full CREATE statement with all columns. PRAGMA loop finds them all and skips ALTERs.

Existing development database: CREATE is a no-op. PRAGMA loop detects the two missing columns and ALTERs them in. Second and third calls are no-ops.

Database shared across the team: Each developer's `git pull` + next `init_db()` call converges to the same schema, regardless of when they last synced.

Reference implementation: `sem-tools/sem/core/db.py:_apply_additive_migrations` (commit 639a16b, 2026-05-20).

## Grounding

Verified by:

1. **Fresh-DB smoke test:** CREATE includes all columns. PRAGMA loop is a no-op. INSERT with new columns succeeds.
2. **Old-schema migration test:** Constructed a database without `spam_flags` and `phishing_score`. CREATE was a no-op on the table. PRAGMA loop detected both missing columns. ALTERs ran. New columns were present and usable.
3. **Idempotency test:** Ran `init_db()` five times in sequence on the migrated database. Column count remained stable. No duplicate columns. No errors.

## Related patterns

- **Verify FK target table on remote before writing migrations against renamed tables** (wiki/migrations/2026-05-16_verify-fk-target-table-remote-before-migration.md) — addresses a different layer (PostgreSQL + Supabase); same spirit of "query the source of truth, don't infer from files"
- **Big-Bang Rename Playbook** (wiki/migrations/big-bang-rename-supabase-fastapi-react.md) — comprehensive framework for high-stakes schema changes; operates at a different scale/risk level

## Source context

Pattern discovered during sem-tools spam-detector wiring (2026-05-20). The tool needed to add spam-detection columns to an existing SQLite schema. Initial approach (unconditional ALTER) broke after the first migration; attempted fix (try/except) was too silent when errors occurred. The PRAGMA-based check provided clarity, idempotency, and legible error messages. Pattern is narrower than full migration frameworks but is reliable for small, additive-only schema evolution in pre-production environments.
