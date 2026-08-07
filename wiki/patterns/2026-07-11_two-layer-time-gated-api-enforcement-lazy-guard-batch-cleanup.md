---
title: Two-layer time-gated API enforcement — inline lazy guard + nightly cron batch cleanup
source_mode: builder
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-07-11
domain: patterns
topic: validation
tags: api, deployment, scheduling
related_entries: []
---

# Two-Layer Time-Gated API Enforcement

## Pattern: Two-Layer Time-Gated API Enforcement

### Problem

Time-limited API access (trials, subscriptions) requires enforcement at the API validation layer. A single enforcement point creates coverage gaps: a lazy check (fires only on API call) misses users who go dark after expiry; a batch job alone has up to 24h lag before blocking active abusers.

### Solution: Two complementary layers

**Layer 1 — Inline lazy guard (validate_api_key)**

Add a secondary DB lookup inside the key validation function when `key.tier == "trial"`. Check the user's `profiles.trial_end` against `now()`. If expired: deactivate the key in DB and return `None` (→ 401). This fires on the NEXT API call after expiry — zero lag for active users.

Fail-open design is critical: if the profile lookup fails (DB error, no profile row, null `trial_end`), log and allow the call rather than blocking legitimate users on a transient error.

```python
if record["tier"] == "trial":
    try:
        profile = client.table("profiles").select("trial_end").eq("id", record["user_id"]).single().execute()
        if profile.data and profile.data.get("trial_end"):
            trial_end = datetime.fromisoformat(profile.data["trial_end"])
            if trial_end.tzinfo is None:
                trial_end = trial_end.replace(tzinfo=timezone.utc)
            if now > trial_end:
                client.table("api_keys").update({"is_active": False, "revoked_at": now.isoformat()}).eq("id", record["id"]).execute()
                return None
        else:
            logger.warning("Trial key for user=%s has no profile — allowing call", record["user_id"])
    except Exception:
        logger.exception("Trial expiry check failed for user=%s — allowing call", record["user_id"])
```

**Layer 2 — Nightly cron batch cleanup**

A scheduled script (GitHub Actions cron or equivalent) queries all users where `tier='trial'` AND `trial_end < now()`. For each: revoke active API keys + downgrade profile tier to free. Runs in a low-traffic window (e.g. 03:00 UTC).

This handles silent users who never make another API call post-expiry — their keys would otherwise appear "active" in the developer dashboard indefinitely.

```python
# Pseudocode for nightly job
expired = client.table("profiles").select("id,email,trial_end").eq("tier", "trial").lt("trial_end", now_iso).execute()
for profile in expired.data:
    client.table("api_keys").update({"is_active": False, "revoked_at": now_iso}).eq("user_id", profile["id"]).eq("is_active", True).execute()
    client.table("profiles").update({"tier": "free"}).eq("id", profile["id"]).execute()
```

### Why both layers are needed

| Scenario | Layer 1 (inline) | Layer 2 (cron) |
|----------|-----------------|----------------|
| User calls API after day 7 | ✅ Blocks immediately | — |
| User goes dark after day 7 | — | ✅ Cleans up overnight |
| Dashboard shows stale active key | — | ✅ Revokes by morning |
| Profile tier stuck on 'trial' in UI | — | ✅ Downgrades to 'free' |

### When This Applies

- Any SaaS product with time-limited API access (trials, time-boxed subscriptions)
- API key-based auth where the key is separate from the account status
- Systems where MCP clients, CLI tools, or integrations hold long-lived keys that outlast account state

### When This Does NOT Apply

- OAuth token-based systems where token expiry is handled by the auth provider (the provider revokes the token; no secondary DB check needed)
- Systems where the session IS the key (JWT with embedded expiry claim — the expiry is enforced at decode time)
- Non-time-gated access tiers (permanent free/paid distinction — no expiry to check)

## Source Context

Implemented in `cos/backend/app/services/api_key_service.py` (commit 05c0c04, 2026-07-11). The inline guard adds one Supabase round-trip per trial key call — acceptable latency overhead for a low-volume tier. The cron runs on GitHub Actions against the production repo only (guarded by `if: github.repository == 'SEMalytics/cos'` on the scheduled trigger). 11 tests cover: active trial, expiry boundary, DB deactivation, fail-open edge cases, non-trial tier skip.
