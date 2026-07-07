---
title: Ghost Admin API — feature_image_alt hard 191-char limit validated at post-create, not image-upload
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 1.0
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-06
domain: integration
topic: api-quirks
tags: [ghost, api, integration, gotcha, content-pipeline]
related_entries: []
---

# Ghost Admin API — feature_image_alt Hard 191-Char Limit

## What was learned

Ghost's Admin API validates `feature_image_alt` at **post-create time**, not at image-upload time. The upload endpoint (`/admin/images/upload/`) accepts images with any ref text and returns 200/201. The hard limit fires at `/admin/posts/` (POST) with a `422 ValidationError`:

```
"context": "Value in [post_revisions.feature_image_alt] exceeds maximum length of 191 characters. post_revisions.feature_image_alt"
```

By this point the image is already uploaded to Ghost's CDN and you can't atomically roll it back — you get a live orphaned image and no draft. You have to manually delete the uploaded image or re-stage the entire post.

## When This Applies

Any Ghost Admin API workflow that:
- Uploads a feature image and sets `feature_image_alt` in the same POST to `/admin/posts/`
- Uses programmatic draft creation (not the Ghost editor UI, which has client-side validation)

## When This Does NOT Apply

- Ghost editor UI (catches this before submission)
- Posts without `feature_image_alt` set
- Image uploads themselves (the `/admin/images/upload/` endpoint does not enforce this limit)

## Symptom

Upload succeeds (201 Created), post-create fails (422 Unprocessable Entity). Alt text may have been 200+ chars without being caught at upload time.

## Fix

Truncate alt text to ≤191 chars **before** the post create call, not after. The ghost-stage-draft.py script at `~/Scripts/client-project/scripts/ghost-stage-draft.py` already has this guard (line ~233):

```python
if alt and len(alt) > 191:
    print(f"  ⚠ alt text {len(alt)} chars > Ghost's 191-char limit — truncating to 188+...")
    alt = alt[:188].rstrip() + "..."
```

When writing custom staging scripts (bypassing ghost-stage-draft.py), this guard must be added manually.

## Grounding

Hit directly during internexio blog Post #2 staging (2026-07-07). Alt text was 213 chars. Image uploaded successfully (201), then the `/admin/posts/` call returned 422. Resolved by truncating to 161 chars and re-running.

## Related

- Ghost tag payload gotcha (send both `name` + `slug` to avoid lowercase duplicates) — separate entry in project MEMORY.md
- `feature_image` field requires the CDN URL returned by the image upload call — set both fields in the same post-create payload
- Ghost blog + Python-Markdown pipeline URL autolink (`pymdownx.magiclink`) — covers a different part of the content-to-post pipeline

## Source Context

Discovered during internexio blog post staging workflow (2026-07-06). The operator was using the Python Ghost Admin API client with truncation logic already in place, but custom scripts written without awareness of this limit will fail the same way.
