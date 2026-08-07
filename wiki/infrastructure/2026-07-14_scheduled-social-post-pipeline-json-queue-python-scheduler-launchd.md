---
title: Scheduled social post pipeline — JSON queue + Python scheduler + launchd
source_mode: builder
novelty_type: reusable_pattern
grounding_score: 0.88
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-14
domain: infrastructure
topic: ops
tags: scheduling, deployment
related_entries: []
---

# Scheduled Social Post Pipeline — JSON Queue + Python Scheduler + launchd

## Pattern: Scheduled Social Post Pipeline

### What it is
A lightweight system for firing social posts (X + BlueSky) at random times within a defined morning window (5am–6am local time), with URL validation to handle blog-promo posts that depend on a live blog URL.

### Components
1. **Queue file** (`data/social-queue.json`) — flat list of posts with fields:
   - `id`, `date` (YYYY-MM-DD), `channel`, `type` (blog_promo | insight_atom | question | cross_promo)
   - `x_text`, `bsky_text` — platform-specific copy (X ≤280 chars, BlueSky ≤300)
   - `url_check` (optional, for blog_promo) — URL that must return HTTP 200 before firing
   - `status` (pending | fired | skipped), `fired_at` (ISO timestamp on completion)

2. **Scheduler script** (`scripts/social-scheduler.py`) — reads queue, fires today's pending posts:
   - Called at 5:00am by launchd
   - Validates URL for `blog_promo` type posts — skips if URL not live
   - Calculates random inter-post gaps that sum to the remaining window time
   - Falls back to 15s gaps if called after the window (catch-up mode)
   - Marks each post `fired` with timestamp after success
   - Writes temp JSON manifests per-post, calls `post-social.py --manifest <file>`
   - Caps at 5 posts per day (configurable `MAX_POSTS_PER_DAY`)

3. **LaunchD plist** (`~/Library/LaunchAgents/com.semalytics.social-scheduler.plist`) — fires scheduler at 5:00am local time daily. `RunAtLoad: false`. Logs to `data/social-scheduler-launchd.log`.

### Key design decisions
- **URL validation gate**: blog_promo posts are skipped if the target URL is not returning 200 at fire time. This prevents firing promo posts for blogs not yet published. Insight atoms and questions fire unconditionally.
- **Random spacing**: gaps are computed by `random.sample(range(1, remaining_secs), n-1)` then sorted as breakpoints. This distributes posts unpredictably within the window, not uniformly.
- **Catch-up mode**: if the script runs after the window end (past 6am), it fires with 15s gaps. This lets manual/catch-up runs complete quickly without requiring a separate invocation path.
- **Status persistence**: `status: fired` + `fired_at` timestamp written back to the queue file after each successful post. Failed posts remain `pending` and will not be re-attempted by the scheduler (manual re-trigger required).

### When This Applies
- Multi-channel social posting (X + BlueSky at minimum) from a content calendar
- Posts need to land before a business-day start (e.g., 9am EST) for maximum reach
- Some posts (blog promos) depend on a live URL that may not be published until early morning
- Content is authored weekly in batch; posting is automated daily

### When This Does NOT Apply
- High-frequency posting (>10 posts/day) — the random-gap approach doesn't scale to tight time windows with many posts
- LinkedIn/Facebook — these platforms require manual paste (ToS + engagement quality concerns); do not extend this system to them
- Posts that need real-time trigger (e.g., fire when a Ghost post goes live) — the URL check is a poll at 5am, not a true event trigger

### Gotchas
- `post-social.py` requires `--manifest` flag (not positional argument)
- launchd plist fires at local time — if machine is in DST, "5am PST" becomes "5am PDT" automatically. This is correct behavior.
- Queue file must be writable by the launchd agent's user. Check permissions if status updates fail silently.
- Blog_promo posts with a `url_check` that permanently fails (404, bad slug) stay `pending` indefinitely — no auto-expire.

### Implementation location
- Queue: `~/Scripts/semalytics-gtm/data/social-queue.json`
- Scheduler: `~/Scripts/semalytics-gtm/scripts/social-scheduler.py`
- Plist: `~/Library/LaunchAgents/com.semalytics.social-scheduler.plist`
- Downstream poster: `~/Scripts/semalytics-gtm/scripts/post-social.py` (pre-existing)

## Source Context

Pattern developed in semalytics-gtm GTM operations, 2026-07-13. The system automates daily social-post scheduling for multi-channel campaigns where timing is strategic (early-morning reach) and content depends on other systems (blog publications). Built to avoid manual posting overhead while honoring platform-specific constraints (X char limits, BlueSky URL handling).
