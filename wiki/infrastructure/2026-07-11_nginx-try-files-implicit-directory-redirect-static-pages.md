---
title: nginx try_files implicit 301 for directory-style static pages — explicit location redirect not needed
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-11
domain: infrastructure
topic: server-configuration
tags: deployment, nginx, static-files, redirects
related_entries: []
---

# nginx try_files: implicit directory redirect for static pages

## Pattern

When serving static files with `try_files $uri $uri/ =404`, nginx automatically issues a 301 redirect from `/path` → `/path/` when `/path` is a directory (i.e., `$uri/` resolves to an existing directory with an `index.html`). This redirect happens **automatically inside nginx** — no explicit `location =` rule is required.

## When you DO need an explicit redirect

Explicit `location = /path { return 301 /new-path/; }` rules are required only when:
- The location is a **reverse-proxied upstream** (try_files never runs; the proxy_pass intercepts first and there's no filesystem to check against).
- The **page was renamed** (old slug → new slug, not just trailing-slash normalization).
- Serving `.html` extension variants where the target is a directory-style clean URL (e.g. `location = /disc-assessment.html { return 301 /disc-assessment/; }`).

## Anti-pattern (unnecessary rule)

```nginx
# ❌ REDUNDANT for directory-style static pages — try_files already handles this
location = /disc-assessment {
    return 301 /disc-assessment/;
}
```

## Correct approach

```nginx
# ✅ try_files $uri $uri/ =404 already issues the 301 for directory pages
location / {
    try_files $uri $uri/ =404;
}

# Only add explicit rules for the cases listed above:
location = /disc-assessment.html {
    return 301 https://$host/disc-assessment/;
}
```

## When it does NOT apply

- PHP/application servers where nginx proxies to an app (FastAPI, Node, etc.) — the app handles path routing, not the filesystem.
- Sites not using `try_files` (e.g., pure `proxy_pass` to an upstream).
- Windows IIS, Apache, Caddy — different mechanisms.

## Grounding

Verified 2026-07-10 on semalytics.com nginx config ([project] bead cos-7sh4). The `/tools/disc-assessment` → `/tools/disc-assessment/` redirect was already working via try_files. Only the `.html` variant redirect was missing and was the actual gap to fill. nginx version: 1.18.0 (Ubuntu 20.04, DigitalOcean Droplet).

## Source Context

Debugging a trailing-slash redirect issue on semalytics.com during COS feature work. Initially assumed an explicit redirect rule was missing; found that try_files was already handling the directory-style case correctly. The actual missing piece was the `.html` variant redirect, which cannot be handled by try_files alone and requires an explicit location rule.
