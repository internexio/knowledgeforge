---
title: Ghost Admin API key discovery via SQLite when credentials are unknown
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-27
domain: diagnostics
topic: server-configuration
tags: [api, deployment, empirical]
related_entries: ["integration/2026-07-14_ghost-admin-api-base-path-follows-install-subpath.md", "integration/2026-07-27_ghost-canonical-cross-post-workflow-substack-republish.md"]
---

# Ghost Admin API Key Discovery via SQLite

## Problem

You need to call the Ghost Admin API for a self-hosted Ghost instance but the Admin API key is not in any env file, .env, or known config. The Ghost admin UI may be inaccessible or you want a programmatic path.

## When This Applies

- Self-hosted Ghost (not Ghost Pro)
- You have SSH/root access to the server
- The Ghost SQLite database is at `/var/www/ghost-<name>/content/data/ghost.db`
- You need the key without going through the Ghost admin UI

## When It Does NOT Apply

- Ghost Pro (managed hosting) — no direct DB access
- PostgreSQL-backed Ghost installs (query syntax differs; table structure same)

## Discovery Steps

**Step 1: Find integrations by name**

```bash
sqlite3 /var/www/ghost-<name>/content/data/ghost.db \
  "SELECT id, name FROM integrations LIMIT 20;"
```

Note the `id` of the integration you want.

**Step 2: Get the API key for that integration**

```bash
sqlite3 /var/www/ghost-<name>/content/data/ghost.db \
  "SELECT id, secret FROM api_keys WHERE integration_id='<integration_id>';"
```

Two rows are returned per integration: one Content API key (short secret, ~26 chars) and one Admin API key (long secret, 64 hex chars).

Admin API key format for use:

```
{api_keys.id}:{api_keys.secret}
```

**Step 3: Get author IDs if needed**

```bash
sqlite3 /var/www/ghost-<name>/content/data/ghost.db \
  "SELECT id, name, email FROM users WHERE id NOT LIKE '%00000000%' LIMIT 10;"
```

**Step 4: Get existing tag slugs**

```bash
sqlite3 /var/www/ghost-<name>/content/data/ghost.db \
  "SELECT id, slug FROM tags ORDER BY slug LIMIT 50;"
```

## Schema Gotcha

The `api_keys` table in Ghost 6.x does NOT have a `name` column. Columns are: `id`, `type`, `secret`, `integration_id`, `user_id`, `last_seen_at`, `last_seen_version`, `created_at`, `updated_at`. Always look up integration names via the `integrations` table.

`SELECT id, name, secret FROM api_keys` will fail with "no such column: name" — the correct query is `SELECT id, secret FROM api_keys WHERE integration_id='...'`.

## Distinguishing Key Types

| | Content API key | Admin API key |
|---|---|---|
| `type` | `content` | `admin` |
| `secret` length | ~26 chars | 64 hex chars |
| Usage | Read-only | Full write access |

## Grounding

Verified on Ghost 6.52.1 (internexio.com/blog, 2026-07-27, SQLite backend). The column schema error (`name` column doesn't exist) was hit and corrected in-session. Existing wiki entry `2026-07-14_ghost-admin-api-base-path` covers API routing/URL patterns — this entry covers credential discovery, which is a distinct problem.

## When This Applies (Credential Recovery)

This pattern applies when:
- API keys are not stored in environment files or secrets management
- The instance is self-hosted with direct filesystem/database access
- You need programmatic credential recovery without accessing the Ghost UI

## When This Does NOT Apply

- Keys are managed by a secrets system (Vault, AWS Secrets Manager, etc.)
- The admin UI is accessible and you can generate a new key there (preferred)
- Ghost Pro managed hosting (no direct DB access)

## Source Context

Discovered during semalytics-gtm Internexio cross-post session (2026-07-27) when the Ghost Admin API key for internexio.com/blog was needed to stage republished posts but was not in any .env file. Direct SQLite query provided the path to discovery. Verified end-to-end against Ghost 6.52.1.
