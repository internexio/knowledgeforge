---
title: Dolt embedded-mode DDL for locked server databases (MySQL 9.x client workaround)
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-06
domain: infrastructure
topic: ops
tags: deployment, filesystem, empirical, stable
related_entries:
  - diagnostics/2026-07-04_bd-schema-migrations-version-fence-migrate-dirty-config-refusal.md
  - infrastructure/2026-05-27_bd-cli-dependency-wiring-inversion-two-pass-pattern.md
---

# Dolt Embedded-Mode DDL for Locked Server Databases (MySQL 9.x Client Workaround)

## Problem

When running schema mutations against a Dolt SQL server database and the MySQL client is unavailable (MySQL 9.x on macOS Homebrew removed the `mysql_native_password.so` plugin — `dlopen` fails with "no such file"), you cannot connect via `mysql -h 127.0.0.1 -P <port>`. Similarly, `dolt sql-client` was removed in older Dolt versions (not present in Dolt 2.1.9).

## Workaround: Dolt Embedded Mode

`cd` into the Dolt database directory (the directory that contains `.dolt/`) and use `dolt sql -q "..."` directly. This runs the query against the local working set via the embedded Dolt engine, bypassing the server entirely.

```bash
# Given a server at 3307 serving ~/gt/.dolt-data/town:
cd ~/gt/.dolt-data/town
dolt sql -q "SHOW TABLES;"           # works even while server is running
dolt sql -q "DROP TABLE config;"     # executes on the working set
dolt status                          # shows "deleted: config" (unstaged)
```

**Critical caveat: DDL goes to the working set, not committed HEAD.** The Dolt server on 3307 serves the committed HEAD. Until you commit and restart the server, the server still sees the old schema.

```bash
# Commit the change so the server picks it up on restart
dolt add config
dolt commit -m "drop config table to unblock bd migrate"

# Restart the server to serve the new HEAD
gt dolt stop
gt dolt start
```

After restart, any tool connecting via the MySQL protocol to 3307 will see the new committed schema.

## When This Applies

- MySQL client incompatibility (MySQL 9.x removed `mysql_native_password.so`)
- `dolt sql-client` not available (Dolt < 2.2.x)
- Need to run DDL against a Dolt server database
- The database directory is locally accessible (same machine as the server)

## When This Does NOT Apply

- Remote Dolt server (database directory is not locally accessible)
- When data must be written without a server restart (transactions in flight)
- Server uses WAL or locking that prevents concurrent embedded access (in practice Dolt 2.x allows embedded read/write of the working set alongside a running server — they use different layers; the embedded write does not conflict with server in-flight transactions, only with the committed HEAD served)

## Source Context

Verified 2026-07-06 during [project]-yj6g migration:
- `mysql -h 127.0.0.1 -P 3307 -u root` → `ERROR 2059: mysql_native_password cannot be loaded` (macOS Homebrew MySQL 9.2.0)
- `dolt sql -q "DROP TABLE config;"` from `~/gt/.dolt-data/town/` → exit 0, SHOW TABLES confirmed table absent
- `dolt add config && dolt commit -m "drop config table..."` → Dolt commit hash issued
- After `gt dolt stop && gt dolt start` → `bd -C ~/gt/town migrate` ran 5 schema migrations (wisp_*, repo_mtimes, local_metadata, nonlocal table commits visible in dolt log)
- `bd -C ~/gt/town list` → exit 0 (previously failing with "table not found: schema_migrations")
