---
title: Ghost cross-post workflow — multi-instance staging with attribution and canonical URL
source_mode: builder
novelty_type: reusable_pattern
grounding_score: 0.85
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-11
domain: integration
topic: multi-instance-content-deployment
tags: [ghost-api, cross-posting, canonical-url, seo-attribution, utm-tracking]
related_entries: ["integration/2026-07-06_ghost-admin-api-feature-image-alt-191-char-limit.md", "patterns/2026-07-06_utm-three-tier-medium-taxonomy-blog-conversion-attribution.md"]
---

# Ghost Cross-Post Workflow (Multi-Instance)

When republishing a blog post from one Ghost CMS instance to another (e.g., semalytics.com/blog → internexio.com/blog), follow this exact sequence to preserve SEO attribution and maintain UTM tracking integrity.

## When This Applies

- Source and destination are different Ghost instances (may be different versions: Ghost 5.x mobiledoc vs Ghost 6.x lexical)
- Destination is a secondary/cross-posting property
- You want the source to remain the canonical URL for SEO

## When This Does NOT Apply

- Single Ghost instance (use scheduling instead)
- Destination is the original/primary source
- Ghost Pages (not Posts) — Pages use a different API endpoint

## Verified Pattern (2026-07-11, semalytics.com → internexio.com)

### Step 1 — Prepare Content

Read the source markdown draft. Strip:
- YAML frontmatter
- H1 title (Ghost title field handles this)
- Image concept block (`**Concept:**` section at bottom — image generation metadata)
- Ghost-specific HTML comments

Keep: article body, references section (render as `<hr>` + paragraphs).

### Step 2 — Prepend Attribution Paragraph

Insert as the FIRST paragraph of the HTML body (before the main article content):

```html
<p><em>Originally published on <a href="https://SOURCE_DOMAIN/blog/SLUG/">SOURCE_DOMAIN/blog</a>.</em></p>
```

### Step 3 — Update CTA UTM Parameters

Replace bare CTA links (e.g., `semalytics.com/cos`) with UTM-tagged versions:

```
utm_source=DESTINATION_SOURCE_SLUG
utm_medium=blog
utm_campaign=CAMPAIGN_SLUG
utm_content=POST_SLUG
```

**Reference:** See `patterns/2026-07-06_utm-three-tier-medium-taxonomy-blog-conversion-attribution.md` for the full taxonomy.

### Step 4 — Upload Hero Image Separately

Ghost API requires a separate image upload before creating the post:

```
POST https://DESTINATION/ghost/api/admin/images/upload/
Authorization: Ghost JWT
Content-Type: multipart/form-data
Field name: file
```

Response JSON contains `url` field — use this as `feature_image` in the post payload.

**Caveat:** `feature_image_alt` is validated at post-create time (max 191 chars), not at upload. See `integration/2026-07-06_ghost-admin-api-feature-image-alt-191-char-limit.md` for details.

### Step 5 — Create Post via Ghost Admin API

For Ghost 6.x (lexical), use `?source=html` to let Ghost convert HTML to lexical:

```
POST https://DESTINATION/ghost/api/admin/posts/?source=html
```

Payload:

```json
{
  "posts": [{
    "title": "...",
    "slug": "POST_SLUG",
    "status": "scheduled",
    "published_at": "2026-MM-DDTHH:MM:SS.000Z",
    "canonical_url": "https://SOURCE_DOMAIN/blog/SLUG/",
    "feature_image": "URL_FROM_STEP_4",
    "feature_image_alt": "...",
    "html": "ATTRIBUTION_PARAGRAPH + ARTICLE_HTML"
  }]
}
```

**Key fields:**

- `canonical_url`: Points to the source post. Tells search engines which is the original. **Do NOT omit** — without it, the cross-post competes with the source for rankings.
- `status: scheduled` with `published_at`: Set to at least 3 days after the source publishes (gives source time to get indexed first).
- `?source=html`: Required for Ghost 6.x. Ghost 5.x uses mobiledoc body format instead.

### Step 6 — JWT Authentication Pattern

Both Ghost 5.x and 6.x use the same JWT auth:

```python
import jwt, time
key_id, secret = GHOST_ADMIN_KEY.split(':')
payload = {'iat': int(time.time()), 'exp': int(time.time())+300, 'aud': '/admin/'}
token = jwt.encode(payload, bytes.fromhex(secret), algorithm='HS256', headers={'kid': key_id})
```

The JWT expires in 300 seconds — keep API calls within this window.

## Scheduling Lag Convention

- Cross-post goes live 3–7 days after source publishes
- Ensures source gets crawled and indexed as canonical first
- Example: semalytics.com publishes Sun Jul 12 → internexio.com scheduled Fri Jul 18 (6-day lag)

## Anti-Patterns

- Do NOT set the same slug on both instances — Ghost may conflict on sitemap
- Do NOT omit `canonical_url` — without it, both posts compete in search
- Do NOT update UTM source to a generic value — use the destination-specific slug from the attribution model
- Do NOT upload the image via URL reference — Ghost requires a multipart upload to its own CDN; external image URLs are not accepted as `feature_image` directly
- Do NOT mix Ghost 5.x and 6.x HTML/Lexical formats without testing — 5.x expects mobiledoc, 6.x with `?source=html` converts to lexical

## Source Context

Developed during semalytics-gtm content production workflow (2026-07-11) when cross-posting internexio.com blog content strategy required republishing to semalytics.com/blog while maintaining SEO hygiene and conversion attribution tracking. Verified with Ghost 6.52 on internexio.com and semalytics.com staging instances.
