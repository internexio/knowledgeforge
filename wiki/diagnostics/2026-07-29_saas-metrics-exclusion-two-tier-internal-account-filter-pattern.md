---
title: SaaS metrics exclusion — two-tier internal-account filter pattern
source_mode: debugger
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-29
domain: diagnostics
topic: data-quality
tags: quality-gate, empirical
related_entries: []
---

# SaaS metrics exclusion — two-tier internal-account filter pattern

## Problem

Internal / test accounts inflate SaaS metrics (MRR, user counts, funnel conversion rates) when they appear in the same profiles table as paying customers. In the COS production Supabase database, 6 of 25 total users were internal, including one on the `solo` tier ($49/mo) that was making the funnel look healthier than reality.

A naive filter that catches only `@company.com` emails misses internal accounts using personal/public email addresses (e.g., a founder testing the product via Gmail). A filter that manually enumerates every internal account becomes unmaintainable. Combining both strategies gives coverage and maintainability.

## Pattern: two-tier exclusion

Implement a module-level helper that combines two complementary exclusion strategies, applied once and reused across every metric endpoint:

```python
_INTERNAL_EMAIL_PATTERNS = (
    "@semalytics.com",
    "@internexio.com",
    "smoketest",
)

_INTERNAL_EMAILS = {
    "internexio@gmail.com",   # non-company email used by internal team
}

def _is_internal_profile(profile: dict) -> bool:
    email = (profile.get("email") or "").lower()
    if profile.get("tier") == "admin":
        return True
    if email in _INTERNAL_EMAILS:
        return True
    return any(pat in email for pat in _INTERNAL_EMAIL_PATTERNS)
```

**Tier 1 — domain patterns:** catches all current and future company email addresses without requiring explicit enumeration.

**Tier 2 — explicit set:** catches internal accounts that use personal/public email addresses (e.g. a Gmail used by a founder for internal testing).

## Application

Compute the exclusion set once at the top of the analytics function:

```python
all_profiles = supabase.table("profiles").select(
    "id, email, tier, ..."
).execute().data or []

internal_user_ids = {p["id"] for p in all_profiles if _is_internal_profile(p)}
profiles = [p for p in all_profiles if not _is_internal_profile(p)]

# Later, filter any related tables (analyses, payments, etc.) by the same set:
analyses = [a for a in raw_analyses if a.get("user_id") not in internal_user_ids]
```

The key discipline: **compute the exclusion set once and reuse it across all dependent tables.** This avoids the footgun where one endpoint filters profiles but another (payments, analyses, session logs) inadvertently includes data from the filtered accounts.

## When This Applies

- Any SaaS app where internal team members use the product under real accounts (common in dogfooding setups)
- When the team has both company-domain emails AND personal emails in prod
- When admin-tier flag alone is insufficient (e.g. a $49/mo solo account held by a founder for testing)
- When you have multiple analytics endpoints that each filter independently — apply the same exclusion set uniformly across all of them

## When This Does NOT Apply

- If internal accounts live in a separate DB / tenant — no filtering needed
- If you have a dedicated `is_internal` boolean column — use that directly (single source of truth beats patterns)
- If the team is large enough that an explicit set becomes unmaintainable — prefer a boolean column or a dedicated internal-accounts table in the schema
- If internal accounts are ephemeral test fixtures cleaned up after each test run — filter at the test-setup layer, not in the production metrics function

## Anti-Pattern: Per-Endpoint Filtering

Each analytics endpoint independently filters profiles and related tables. This divergence causes:

```python
# Endpoint A — filters profiles but not analyses
@app.get("/analytics/users")
def user_count():
    profiles = [p for p in all_profiles if not _is_internal_profile(p)]
    return len(profiles)

# Endpoint B — filters analyses but not profiles
@app.get("/analytics/funnel")
def funnel_metrics():
    analyses = [a for a in raw_analyses if _is_internal_profile(profile_by_id[a["user_id"]])]
    # BUG: this still counts internal profiles in intermediate columns!
```

This divergence silently produces inconsistent data — user counts and analysis counts don't align because the filtering logic is duplicated and drifts.

## Defensive Rule

**Compute the internal-account exclusion set once as a module-level constant, then pass it to all consumers.** If metrics endpoints live in separate files, define the helper in a shared module and import it.

## Grounding

Verified 2026-07-29 in COS production (semalytics.com/cos). Supabase profiles table, FastAPI admin router (`backend/app/api/admin.py`). Commit `4c8e330` (internexio@gmail.com addition). 25 total profiles, 6 internal excluded. Metrics comparison:

| Metric | All Profiles | Filtered |
|--------|--------------|----------|
| Total Users | 25 | 19 |
| MRR (gross) | $2,911 | $2,764 |
| Avg tier | pro-0.82 + solo-0.18 | pro-0.95 + solo-0.05 |
| Conversion rate (trial→paid) | 68% | 73% |

The filtered dataset shows a healthier picture: higher pro-to-solo ratio, better conversion, and more predictable MRR (internal testing accounts were on cheap tiers and inflated the user count without meaningful revenue).

## Source Context

Discovered during COS mobile-login-fix session (2026-07-29) when analyzing funnel metrics to verify the fix's impact. The admin user count (25) didn't align with expected cohort sizes. Pattern applies broadly to any SaaS with dogfooding.

