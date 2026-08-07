---
title: Ghost casper theme omits author bio from post pages — fix pattern
source_mode: debugger
novelty_type: new_pattern
grounding_score: 0.80
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-25
domain: infrastructure
topic: server-configuration
tags: [deployment, stable]
related_entries: ["infrastructure/2026-07-24_ghost-active-theme-verification-before-ssh-edits.md", "integration/2026-07-14_ghost-casper-theme-hardcoded-tag-editorial-blocks-handlebars-match.md", "integration/2026-07-11_ghost-cross-post-workflow-multi-instance-staging-canonical-attribution.md"]
---

# Ghost Casper Theme: Author Bio Omitted from Post Pages — Fix Pattern

## Problem

Ghost stores an author bio in the `users` table of its SQLite database, but the default casper theme's `post.hbs` does NOT include a `{{#primary_author}}` block in the post body. The bio exists in the database but is never rendered on individual post pages — only the author name and avatar appear in the byline at the top.

## Root Cause

The casper theme template (`post.hbs`) closes the main content section (`</section>` after `{{content}}`) without including an author bio block. This is by design — casper is a minimal default theme. Custom theme variants (digest, source) also lack this block by default.

The template has no conditional placeholder for author bios; they must be added manually.

## Diagnosis

Verify the bio exists in the database:

```bash
sqlite3 /var/www/ghost-internexio/content/data/ghost.db \
  "SELECT name, bio FROM users;"
```

Returns bio text confirming it's set in the database.

Then check post.hbs for a `{{#primary_author}}` block — it will not be present in the default template:

```bash
grep -n "primary_author" /var/www/ghost-internexio/content/themes/casper/post.hbs
# Returns no output
```

## Fix: Add Author Bio Card to casper/post.hbs

Insert the following block in `casper/post.hbs` between the `</section>` that closes `.gh-content` and the `{{#if comments}}` block:

```handlebars
{{#primary_author}}
    {{#if bio}}
    <aside class="gh-post-author gh-canvas" style="padding:3.2rem 0;border-top:1px solid var(--color-border,#e1e4e8);display:flex;align-items:flex-start;gap:1.6rem">
        {{#if profile_image}}<img src="{{img_url profile_image size='xs'}}" alt="{{name}}" style="width:52px;height:52px;border-radius:50%;flex-shrink:0;object-fit:cover">{{/if}}
        <div>
            <p style="margin:0 0 .4rem;font-size:1.4rem;font-weight:600;color:var(--ghost-accent-color,#5b7a99)">About the author</p>
            <h4 style="margin:0 0 .6rem;font-size:1.6rem">{{name}}</h4>
            <p style="margin:0;font-size:1.5rem;line-height:1.6;color:var(--color-midgrey,#738a94)">{{bio}}</p>
        </div>
    </aside>
    {{/if}}
{{/primary_author}}
```

### Why Inline Styles

Inline styles are used to avoid modifying the compiled `assets/built/screen.css`, which would require a theme rebuild pipeline. The block conditionally renders only when a bio is set, so posts with no bio are unaffected.

### Insertion Target (Exact Location)

```
<section class="gh-content gh-canvas">
    {{content}}
</section>

← INSERT AUTHOR BLOCK HERE →

{{#if comments}}
    <section class="article-comments gh-canvas">
```

## Backup Before Editing

Always create a backup:

```bash
cp /var/www/ghost-internexio/content/themes/casper/post.hbs \
   /var/www/ghost-internexio/content/themes/casper/post.hbs.bak-$(date +%Y%m%d)
```

## Verification After Ghost Reload

Use the active-theme verification pattern before editing (see related entry). After restarting Ghost, verify the template took effect:

```bash
# Reload Ghost (as root, use HUP signal)
kill -HUP $(ps aux | grep 'node current/index' | grep -v grep | awk '{print $2}')
sleep 8

# Lightweight verification via Content-Length delta
curl -sI https://example.com/blog/some-post/ | grep Content-Length
# Compare to pre-edit baseline; template uptake causes byte count increase

# Explicit verification of bio text
curl -s https://example.com/blog/some-post/ | grep 'About the author'
```

A successful `Content-Length` increase (~900-1000 bytes for a typical bio block) confirms the template was picked up before doing a full page fetch.

## Scope

- Confirmed in casper (default Ghost theme, versions 5.x / 6.x)
- The digest theme also lacks this block by default
- `{{#primary_author}}` is available inside the `{{#post}}` context in any Ghost post template
- Apply the same pattern to any Ghost theme missing author bio in post pages
- Requires SSH access (Ghost self-hosted, not Ghost Pro)

## When This Applies

- Ghost self-hosted installations with Casper or similar minimal themes
- Post pages where author bio should be visible but is missing
- Author records that have a `bio` field set in Ghost admin
- Themes where author info is intentionally limited to the post byline only (minimal themes)

## When This Does NOT Apply

- Ghost (Pro) — no SSH theme access
- Custom Ghost themes that already render author bio on post pages
- Themes where author bio is intentionally scoped to author archive pages only
- Themes that display bios only on tag pages (digest theme does this)

## Source Context

Applied in production Ghost 6.52.1 on internexio.com/blog (clickadtech server 143.244.188.165) during fellows-surface-audit session 2026-07-24. Grounding: author bio verified rendering live via curl HTML extraction; `Content-Length` delta (+964 bytes) confirmed template uptake. Bio text confirmed present via `curl ... | grep 'About the author'` immediately after Ghost reload. Session: fellows-surface-audit-2026-07-24.
