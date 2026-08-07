---
title: Ghost canonical cross-post workflow (Substack → Ghost republish)
source_mode: builder
novelty_type: reusable_pattern
grounding_score: 0.75
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-27
domain: integration
topic: external-tools
tags: [api, deployment]
related_entries: ["integration/2026-07-11_ghost-cross-post-workflow-multi-instance-staging-canonical-attribution.md", "integration/2026-07-06_ghost-admin-api-feature-image-alt-191-char-limit.md"]
---

# Ghost Canonical Cross-Post Workflow (Substack → Ghost Republish)

## What This Is

A repeatable workflow for republishing a Substack post verbatim to a Ghost blog with the canonical URL pointing back to the Substack original. Prevents duplicate content penalties while making the content discoverable on both properties.

## When This Applies

- You have a Substack post that should also live on a Ghost blog (internexio.com/blog, or similar)
- You want SEO canonical authority to stay on the Substack URL
- The content must be verbatim (no rewriting, same links, same images)

## When It Does NOT Apply

- If you want the Ghost post to rank independently (use canonical pointing to Ghost URL instead)
- If the content needs significant adaptation for the new audience (that's a rewrite, not a republish)

## Step-by-Step Pattern

**1. Fetch the live Substack post**

Use WebFetch with a prompt requesting verbatim content including all links, formatting, and image URLs. Treat the output as a starting point — verify em dashes, curly quotes, and punctuation against the actual page if verbatim fidelity matters (WebFetch can transform typography; see companion entry on WebFetch em-dash caveat).

**2. Download the cover image**

```bash
curl -L "<substackcdn_url>" -o /tmp/cover.jpg --silent --show-error
```

Do NOT hotlink Substack CDN URLs in Ghost — re-upload to Ghost's own CDN.

**3. Build the HTML body**

Convert markdown/fetched content to clean HTML. Preserve:
- All hyperlinks (anchor text + URLs)
- Blockquotes (`<blockquote><p>...</p></blockquote>`)
- Bold/italic emphasis (`<strong>`, `<em>`)
- Section headers (`<h2>`)
- Horizontal rules (`<hr>`)
- Closing italic note if present
- Bullet lists (`<ul><li>...</li></ul>`)

Use HTML entities for typographic quotes (`&#8220;` / `&#8221;`, `&#8216;` / `&#8217;`) rather than straight quotes when the source uses curly quotes.

**4. Ghost Admin API: JWT auth**

Key format: `{key_id}:{secret_hex}` (split on first colon).

```python
import jwt, time
key_id, secret_hex = api_key.split(":", 1)
secret_bytes = bytes.fromhex(secret_hex)
payload = {"iat": int(time.time()), "exp": int(time.time()) + 300, "aud": "/admin/"}
header = {"alg": "HS256", "kid": key_id}
token = jwt.encode(payload, secret_bytes, algorithm="HS256", headers=header)
```

Or use the manual HMAC approach (no PyJWT dependency): see ghost-stage-draft.py in semalytics-gtm/scripts/ for reference implementation.

**5. Upload image**

```
POST /ghost/api/admin/images/upload/
multipart: file=<binary>, purpose=image
Returns: {"images": [{"url": "https://..."}]}
```

**6. Create the post (source=html)**

```
POST /ghost/api/admin/posts/?source=html
Content-Type: application/json
Body: {"posts": [{
  "title": "...",
  "slug": "...",
  "html": "<full html body>",
  "status": "published",
  "custom_excerpt": "subtitle text",
  "canonical_url": "https://dpsea.substack.com/p/...",
  "authors": [{"id": "<author_id>"}],
  "tags": [{"slug": "tag-slug", "name": "Tag Name"}],
  "feature_image": "<uploaded image url>",
  "feature_image_alt": "..."  # max 191 chars — Ghost hard limit
}]}
```

**7. Verify canonical on the live page**

```python
import re, requests
html = requests.get(post_url).text
m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', html)
canonical = m.group(1) if m else None
assert canonical == substack_url
```

**8. Update feature image separately if needed**

If you need to swap the feature image post-creation:

```
GET /ghost/api/admin/posts/{id}/ → extract updated_at
PUT /ghost/api/admin/posts/{id}/
Body: {"posts": [{"feature_image": url, "feature_image_alt": alt, "updated_at": updated_at}]}
```

The `updated_at` field is required for PUT — Ghost rejects without it.

## Feature Image Alt Text

Ghost enforces a **191-character hard limit** on `feature_image_alt` at the revision level (not just post creation). A 422 error on PUT with `post_revisions.feature_image_alt` in context means the alt text is too long even if it was accepted at post creation.

## Gotchas

- `source=html` query param on the POST URL is required for Ghost to accept the `html` field
- Tags are matched by slug; sending both `slug` and `name` prevents Ghost from creating duplicate lowercase tags
- Author must be sent as `{"id": "..."}` — name-only matching is unreliable
- Ghost 6.x still accepts the `v5.0` Accept-Version header

## When This Applies (SEO Canonical)

This pattern is essential when:
- Source platform (Substack) has higher domain authority than destination (Ghost blog)
- Duplicate content penalty risk is material (both URLs are public and linkable)
- Goal is to drive discovery on the secondary property without splitting ranking signals

## When This Does NOT Apply

- Destination Ghost blog is higher-authority than source (reverse the canonical)
- Content is subscription-only on source (don't republish publicly)
- Cross-posting is truly syndication (both versions should rank independently — omit canonical)

## Source Context

Verified against Ghost 6.52.1 on internexio.com/blog (2026-07-27). Used to publish "The Scores Improved. The Results Got Worse." cross-post from dpsea.substack.com. All steps verified end-to-end including canonical tag confirmation on live page.
