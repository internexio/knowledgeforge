---
title: Ghost author page og:image requires cover_image field, not profile_image
source_mode: debugger→builder
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-14
domain: integration
topic: api-quirks
tags: [ghost-cms, og-tags, seo, gotcha]
related_entries: ["integration/2026-07-06_ghost-admin-api-feature-image-alt-191-char-limit.md", "integration/2026-07-11_ghost-cross-post-workflow-multi-instance-staging-canonical-attribution.md"]
---

# Ghost Author Page og:image: cover_image Required, Not profile_image

## What Was Learned

Ghost CMS does NOT generate `og:image` meta tags on author pages from the `profile_image` field of the `users` table. Setting `profile_image` adds the visible avatar (`<img class="author-profile-pic">`) but does NOT produce `<meta property="og:image">`.

To get `og:image` on Ghost author pages, you must set the `cover_image` field on the `users` table row. Ghost reads `cover_image` specifically for og:image generation on author page templates.

## How To Fix

```sql
UPDATE users
SET cover_image = 'https://yourdomain.com/images/author-photo.png'
WHERE slug = 'author-slug';
```

After updating, restart Ghost to clear its rendering cache:

```bash
cd /opt/ghost && docker compose restart ghost
```

## Verification

```bash
curl -s https://yourdomain.com/blog/author/slug/ | grep 'og:image'
```

Expected: `<meta property="og:image" content="https://...">` with the cover_image URL.

## When profile_image IS Used

- Visible avatar on author page (`<img class="author-profile-pic">`)
- Author cards on blog post pages
- Ghost admin UI avatar

## When It Does NOT Apply

- Ghost Pages and Posts: those use the post's `feature_image` for og:image
- Tag pages: use `feature_image` on the tag record
- This is specifically about the author page template (`author.hbs`)

## Source Context

Discovered during semalytics.com SEO remediation (Jul 2026). Crawl tool flagged author page at `/blog/author/david/` as having incomplete OG tags (missing `og:image`). Setting `profile_image` did not fix it. Setting `cover_image` to the same URL produced the `og:image` tag after Ghost restart. Verified on Ghost 6.44 running in Docker.
