---
title: Ghost active-theme verification before SSH theme edits
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-24
domain: infrastructure
topic: server-configuration
tags: [deployment, grounding, stable]
related_entries: ["integration/2026-07-14_ghost-casper-theme-hardcoded-tag-editorial-blocks-handlebars-match.md", "integration/2026-07-11_ghost-cross-post-workflow-multi-instance-staging-canonical-attribution.md", "integration/2026-07-06_ghost-admin-api-feature-image-alt-191-char-limit.md"]
---

# Ghost Active-Theme Verification Before SSH Theme Edits

## Problem

When editing Ghost theme files via SSH, changes may not render if you edit the wrong theme directory. Ghost supports multiple installed themes and tracks the active one in its SQLite database — not as a filesystem symlink or environment variable. This causes a silent failure mode: edits land on disk but don't appear on the live site because a different theme is active.

## Root Cause Observed

In this session: Ghost installation at `/var/www/ghost-internexio/` had three themes installed (`casper`, `digest`, `source`). The `digest` theme's `partials/content.hbs` was edited to add an author bio block. After Ghost restart, the bio didn't appear on the site.

Diagnosis: the active theme was `casper`, not `digest`. The edits were valid but applied to an inactive theme.

## Verification Command (Run BEFORE Editing Any Theme File)

```bash
sqlite3 /var/www/ghost-internexio/content/data/ghost.db \
  "SELECT value FROM settings WHERE key='active_theme';"
```

Returns the active theme name (e.g., `casper`). Edit files only under `/var/www/ghost-internexio/content/themes/<active_theme>/`.

## Confirming Changes Took Effect

After Ghost restart, use HTTP Content-Length as a lightweight proxy:

```bash
curl -sI https://example.com/blog/some-post/ | grep Content-Length
```

A changed `Content-Length` (vs pre-edit baseline) confirms the template was picked up. In this session: 26168 → 27132 bytes (+964 bytes ≈ size of author bio block) confirmed the fix was live before doing a full rendered fetch.

This avoids the cost of a full page fetch while still proving the template was reloaded. Compare before-edit and after-restart Content-Length; a mismatch signals template changes are active.

## Ghost Reload Without CLI (Root User Workaround)

`ghost restart` requires a non-root user. As root, send HUP to the Node process:

```bash
kill -HUP $(ps aux | grep 'node current/index' | grep -v grep | awk '{print $2}')
```

Ghost restarts with a new PID. Verify with `ps aux | grep 'node current'`. The log at `content/logs/https___<domain>_production.log` confirms startup.

## When This Applies

- Any Ghost self-hosted installation with multiple themes installed
- Any SSH-based Ghost theme editing workflow (no Ghost admin UI)
- Ghost versions 5.x and 6.x (SQLite schema confirmed in 6.52.1)
- Theme edits that don't appear on the live site after restart

## When This Does NOT Apply

- Ghost (Pro) — no SSH theme access
- Single-theme installations (only one theme in `themes/` directory) — still good practice to verify, but less likely to cause confusion
- Theme edits made through Ghost Admin UI (admin handles active-theme routing)

## Source Context

Verified in production Ghost 6.52.1 on Ubuntu (clickadtech server 143.244.188.165 / internexio.com) during fellows-surface-audit session 2026-07-24. Grounding: observed in a live deployment and confirmed via SQLite query and HTTP response headers before concluding the diagnosis.
