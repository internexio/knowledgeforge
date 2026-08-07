---
title: API key tier config gap — missing tier in lookup dict causes silent fallthrough to wrong quota
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-11
domain: diagnostics
topic: api-design
tags: [api, error-handling, quality-gate, classification, adversarial]
related_entries: []
---

# API Key Tier Config Gap — Silent Fallthrough to Wrong Quota

## Problem

When a new billing tier is added to a SaaS API key system, it typically needs to be registered in TWO places:

1. **The database** — enum value, tier config table row, profile tier column
2. **The application code** — a config dict (e.g. `TIER_CONFIG`) that maps tier names to quotas, labels, prefixes

Missing from the code dict while present in the DB causes a silent fallthrough: `create_api_key()` receives the new tier name, fails the `if tier not in TIER_CONFIG` guard (if one exists), OR silently uses a default, resulting in the wrong quota being applied.

## Concrete Example (caught in [project], 2026-07-11)

Migration 037 added a `'trial'` value to the `user_tier` DB enum and a `tier_config` table row with `analyses_per_month: 50`. The application code `TIER_CONFIG` dict had only `free / developer / business / enterprise`. A trial user generating an API key would have gotten `free` tier (10 calls/month) instead of the intended 50.

**Fix:**

```python
TIER_CONFIG = {
    "free": {"monthly_quota": 10, "label": "Free"},
    "trial": {"monthly_quota": 50, "label": "Trial"},   # ← added
    "developer": {"monthly_quota": 500, "label": "Developer"},
    ...
}
TIER_PREFIXES = {
    "free": "free",
    "trial": "tri",   # ← added
    ...
}
```

## Detection

- A new tier works in the UI (DB-driven) but API key creation fails or gives wrong quota
- `ValueError: Invalid tier: 'trial'` if there's an explicit guard — silent wrong quota if not
- Users on the new tier report API rate limit errors sooner than expected
- Observing key-creation logic shows a default tier is applied instead of looking up the correct config entry

## Root Causes

1. **Sparse coordination:** DB migrations and code config dicts are separate artifacts that don't sync automatically
2. **Silent defaults:** Code that falls back to a default tier when lookup fails, without logging or raising an error
3. **Partial guard:** An `if tier in TIER_CONFIG` guard exists but was missed when the dict was extended
4. **No integration test:** Tier creation path is not tested end-to-end with a new tier value added to both DB and code

## Prevention Checklist When Adding a New API Key Tier

When you add a new tier to a DB enum and tier config table:

1. ✅ DB enum / tier table row
2. ✅ `TIER_CONFIG` dict (quota, label) — **if code uses a dict**
3. ✅ `TIER_PREFIXES` dict or equivalent prefix mapping
4. ✅ Any frontend tier display mapping or selection dropdown
5. ✅ Any rate-limit override logic that switches on tier name
6. ✅ End-to-end integration test that creates an API key for the new tier and verifies quota

## When This Applies

- API key systems with per-tier quotas stored in application code rather than fully DB-driven
- Any system where tier names are used as lookup keys in multiple independent config dicts
- Adding a new tier that was defined at the DB layer by a migration but code wasn't updated in the same PR
- Code paths that fall back silently to a default when a lookup fails

## When This Does NOT Apply

- Fully DB-driven tier systems where quota is read from the DB on every key lookup (no code-side config dict)
- Systems using exhaustive enum match checks that fail at compile/import time on unknown values
- Code that explicitly raises an error when a tier is not found (rather than falling back to a default)

## Related Anti-Patterns

This is a specialization of the broader **Configuration Skew** anti-pattern: when a system's state lives in multiple places (DB + code dict + frontend), updates to one place without the others create silent, hard-to-detect inconsistencies.

## Source Context

Caught during COS API key tier configuration audit ([project]-trial-mcp-enforcement session, 2026-07-11). Migration 037 added `'trial'` tier to the DB without corresponding updates to `TIER_CONFIG`. The oversight went undetected until users on trial tier exhausted their quota too quickly, triggering investigation of the key-creation logic.
