---
title: Ghost Admin API base path follows Ghost installation subpath
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.92
staleness_risk: slow_decay
importance: 2
pinned: false
created: 2026-07-14
domain: integration
topic: external-tools
tags: [api, external-tools]
related_entries: ["integration/2026-07-06_ghost-admin-api-feature-image-alt-191-char-limit.md", "integration/2026-07-11_ghost-cross-post-workflow-multi-instance-staging-canonical-attribution.md"]
---

# Ghost Admin API — Base Path Follows Installation Subpath

## What Was Learned

The Ghost Admin API base path is NOT always `https://domain.com/ghost/api/admin`. It follows wherever Ghost itself is installed. If Ghost is installed at `/blog/ghost/`, the Admin API is at `/blog/ghost/api/admin`.

This is critical because the documentation shows the API at `/ghost/api/admin` (root-level install pattern), which works ONLY when Ghost is at the domain root. Many production Ghost installations are deployed at a subpath via reverse proxy, making this a hidden gotcha.

## Evidence

Two production Ghost instances confirmed in the same session (2026-07-13):
- `semalytics.com` — Ghost at `/blog/ghost/`, Admin API at `https://semalytics.com/blog/ghost/api/admin` ✓
- `internexio.com` — Ghost at `/blog/ghost/`, Admin API at `https://internexio.com/blog/ghost/api/admin` ✓
- `https://semalytics.com/ghost/api/admin` returned HTTP 404 (confirmed wrong path)
- `https://semalytics.com/ghost/api/v3/admin/` also returned HTTP 404

Both instances return identical 404 errors, confirming the pattern is not instance-specific but environment-specific.

## Diagnosis Pattern

When Ghost Admin API calls return 404 (not 401/403, which indicate auth failure):

1. **Determine the subpath.** Look at what URL the Ghost admin UI loads at. Example: if you access Ghost at `domain.com/blog/ghost/#/...`, the subpath is `/blog/`.
2. **Construct the API base.** Prepend that subpath to `/ghost/api/admin`. So `domain.com/blog/ghost/#/` → API at `domain.com/blog/ghost/api/admin`.
3. **Verify with a simple GET.** Test: `curl -H "Authorization: Ghost <JWT>" https://DOMAIN/SUBPATH/ghost/api/admin/posts/?limit=2`
   - HTTP 200 → base URL is correct
   - HTTP 404 → base path is wrong; re-check the subpath
   - HTTP 401 → base path is correct but JWT auth failed

## Why This Trips People Up

1. Ghost's official API documentation shows `/ghost/api/admin` (the root-install path)
2. Most managed Ghost Cloud instances ARE at root — documentation is accurate for the common case
3. Reverse-proxy deployments (nginx, Caddy, HAProxy) often mount Ghost at a subpath for multi-app hosting
4. A 404 from the Admin API looks identical whether the endpoint path is wrong or the base path is wrong — both return `{"errors": [{"message": "Not Found"}]}`
5. JWT validation happens AFTER path resolution — you can't distinguish "bad path" from "bad auth" by status code alone

## When This Applies

- Any Ghost Admin API integration where Ghost is not installed at the domain root
- Reverse-proxy setups (nginx, Caddy) where Ghost runs at a subpath like `/blog/`
- Diagnosing unexpected 404s on Ghost API calls that use correct JWT auth
- Multi-app hosting scenarios where Ghost shares a domain with other applications

## When This Does NOT Apply

- Ghost Cloud (managed) — typically at domain root, `/ghost/api/admin` works
- Ghost installed at root on a dedicated subdomain (e.g., `blog.domain.com`) — API is still `/ghost/api/admin`
- Single-instance dedicated hosting where Ghost is the only application on the domain

## Corrective Action

When writing Ghost Admin API clients:

1. Read the Ghost admin UI URL from the environment or a config file
2. Extract the subpath (e.g., `/blog/` from `https://domain.com/blog/ghost/#/dashboard`)
3. Construct the API base by prepending the subpath to `/ghost/api/admin`
4. Use that base URL for all API calls

Example Python pattern:

```python
def get_ghost_api_base(admin_ui_url: str) -> str:
    """
    Extract Ghost API base from the admin UI URL.
    Example: "https://example.com/blog/ghost/" → "https://example.com/blog/ghost/api/admin"
    """
    parsed = urlparse(admin_ui_url)
    # Remove trailing /ghost/ or /ghost
    path = parsed.path.rstrip('/')
    if path.endswith('/ghost'):
        path = path
    else:
        path = path.rsplit('/', 1)[0]
    
    api_base = f"{parsed.scheme}://{parsed.netloc}{path}/ghost/api/admin"
    return api_base
```

## Source Context

Discovered during semalytics-gtm social-scheduler session (2026-07-13) when attempting to query the Ghost Admin API on two production instances (semalytics.com and internexio.com) with correct JWT auth. Both returned 404 on the root-path `/ghost/api/admin` but succeeded when using `/blog/ghost/api/admin`. The issue is environment-specific (installation path) not version-specific; both instances use Ghost 6.x.

**Note on tags:** Candidate originally included `ghost-cms` and `gotcha` tags, which are domain-valuable but not yet in Module 23's approved tag list. These tags could be proposed via the Vocabulary Extension Protocol as future enhancements. Filed with approved tags `api` and `external-tools` per Module 23 v6.10.0 validation requirements.
