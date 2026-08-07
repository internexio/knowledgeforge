---
title: Ghost Casper theme tag editorial blocks via Handlebars match pattern
source_mode: debugger
novelty_type: new_pattern
grounding_score: 0.90
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-14
domain: integration
topic: external-tools
tags: [api, deployment, taxonomy]
related_entries: ["integration/2026-07-11_ghost-cross-post-workflow-multi-instance-staging-canonical-attribution.md", "integration/2026-07-06_ghost-admin-api-feature-image-alt-191-char-limit.md"]
---

# Ghost Casper Theme: Tag Editorial Blocks via Handlebars Match Pattern

## What Was Learned

Ghost's Casper theme `tag.hbs` supports hardcoded per-tag editorial content via Handlebars `{{#match slug "tag-slug"}}` conditional blocks. This is how editorial descriptions (beyond the database `description` field) are added to specific blog tag pages (e.g., `/blog/tag/ocean/`, `/blog/tag/psychographic-marketing/`).

The key discovery: these blocks are **NOT in Ghost's database, content API, settings, or the default theme template** — they live only in the theme file on the server.

## Template Location

```
/var/lib/ghost/content/themes/casper/tag.hbs
```

Inside a Docker container, this is accessible via volume mount or via `docker exec ghost-ghost-1 cat /var/lib/ghost/content/themes/casper/tag.hbs`.

## Pattern Structure

```handlebars
{{#tag}}
  {{#match slug "ocean"}}
    <section class="tag-editorial section-light">
      <div class="container">
        <div class="article-body">
          <p>Long-form editorial content for OCEAN tag.</p>
          <p>Related: <a href="/guides/some-guide/">Guide Title</a>.</p>
        </div>
      </div>
    </section>
  {{/match}}

  {{#match slug "psychographic-marketing"}}
    <section class="tag-editorial section-light">
      <div class="container">
        <div class="article-body">
          <p>Editorial for psychographic-marketing tag.</p>
        </div>
      </div>
    </section>
  {{/match}}
{{/tag}}
```

Each `{{#match slug "..."}}` block:
- Checks the tag's slug against a literal string
- Renders the enclosed HTML only if the slug matches
- Can include internal and external links (following normal `<a>` HTML rules)

## Why This Matters for SEO and Content Maintenance

- Editorial content on tag pages is **NOT** searchable in Ghost's admin UI or database
- It's **NOT** exposed via the Ghost Content API (`/ghost/api/v3/content/...`)
- It's **NOT** in tag `description`, `codeinjection_head`, or `codeinjection_foot` fields
- It's **NOT** in site-wide `settings.codeinjection_*` fields
- It **IS** in the compiled theme template on the server

This means SEO fixes — changing URLs in editorial links, fixing 301 redirects, updating internal link destinations — require **direct theme file edits**, not Ghost admin changes.

## Finding the Content

When a tag page shows editorial content that doesn't appear in Ghost admin:

```bash
# SSH to the server or use docker exec
docker exec ghost-ghost-1 grep -n 'match slug' /var/lib/ghost/content/themes/casper/tag.hbs
docker exec ghost-ghost-1 grep -rn 'tag-editorial' /var/lib/ghost/content/themes/casper/
```

Confirm the active theme:

```bash
docker exec ghost-ghost-1 mysql -u ghost -p$GHOST_DB_PASSWORD ghostdb -e \
  "SELECT value FROM settings WHERE key='active_theme';"
```

This tells you which theme file (`casper`, `london`, etc.) is actually serving the site. Multiple themes may be installed, but only one is active.

## How to Add or Modify Tag Editorial Blocks

1. SSH to the Ghost server
2. Edit the theme file (inside container or via volume mount):
   ```bash
   docker exec -it ghost-ghost-1 nano /var/lib/ghost/content/themes/casper/tag.hbs
   ```
   Or mount the theme and edit locally, then restart Ghost.

3. Add a new `{{#match slug "your-tag-slug"}}` block after existing ones
4. Restart Ghost to apply changes:
   ```bash
   cd /opt/ghost && docker compose restart ghost
   ```

Verify the change with `curl`:

```bash
curl https://semalytics.com/blog/tag/your-tag-slug/ | grep 'tag-editorial'
```

## Anti-Patterns

- **DO NOT add links that point to 301 redirects.** Crawlers detect and warn about "page links to redirect" — editorial links should point directly to final URLs.
- **DO NOT confuse this with the tag's Ghost `description` field.** The short plain-text description in Ghost admin is separate from these HTML editorial blocks.
- **DO NOT search the Ghost database for this content.** It won't be found — the database doesn't store theme template content.
- **DO NOT edit the theme from the Ghost admin UI.** Ghost's admin panel has no theme editor for deployed Casper instances (unless custom theme code editing is enabled, which is rare).

## When This Applies

- Ghost CMS with Casper theme installed
- Tag pages that display editorial sections beyond the short database description
- SEO fixes, link updates, or content changes to tag editorial blocks
- Multi-instance setups (semalytics.com and internexio.com can have different editorial blocks in their separate Casper theme files)

## When This Does NOT Apply

- Short tag `description` field (stored in Ghost database, editable in admin)
- Tag post lists or metadata (rendered from database)
- Custom themes other than Casper (may not support `{{#match slug}}` blocks)
- Ghost Pages (Pages use a different template: `page.hbs`, not `tag.hbs`)

## Source Context

Discovered during semalytics.com SEO remediation (Jul 2026). A crawl report flagged `/blog/tag/psychographic-marketing/` linking to a 301 redirect. The URL was not found in:
- Ghost database (checked `tags` table)
- Ghost Content API response
- Ghost settings codeinjection fields
- Default `theme/tag.hbs` patterns assumed from prior experience

Traced to `tag.hbs` line 163 via direct file grep (`docker exec grep -n 'match slug'`). Active theme confirmed as `casper` via database query. Fix required restarting Ghost after editing the theme file.
