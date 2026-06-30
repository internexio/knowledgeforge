---
title: Vendor-hostile migration triggers — when token revocation forecloses the pre-cancel capture step
source_mode: direct
source_session: redacted
novelty_type: refinement
grounding_score: 0.80
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-23
tags: methodology, migrations, diagnostics, grounding
related_entries:
  - wiki/methodologies/2026-05-21_saas-migration-pre-cancel-checklist-silent-failure-config-pointer-risk.md
  - wiki/diagnostics/2026-05-21_server-side-state-outlives-client-fixes-saas-wrappers.md
revises: null
domain: methodologies
topic: staged-rollout
---

# Vendor-hostile migration triggers — when token revocation forecloses the pre-cancel capture step

The pre-cancel migration checklist assumes a cooperative cancellation — you cancel on YOUR schedule, with API access intact until cutover. In hostile-vendor scenarios this assumption breaks and changes the priority order of migration steps.

## Hostile-vendor signals

- API tokens revoked without notice (HTTP 403 on previously working keys)
- Subscription artificially throttled before official cancellation date
- Account locked or downgraded after disputing charges
- Vendor unilaterally changes ToS in a way that retroactively invalidates current usage
- Forensic / disputed-payment scenarios where vendor cuts access first, negotiates second

## How this changes the standard migration checklist

The pre-cancel checklist normally sequences:
1. Final fresh-data capture from old vendor (uses old API while still authorized)
2. Config-pointer flip (route code to new vendor)
3. Validation that new vendor returns equivalent data
4. Actual cancellation

When the vendor is hostile, step 1 is **already foreclosed** at the moment you discover the hostility. The historical snapshot you have IS the final permanent capture — there is no fresh-capture path to execute. Three consequences:

- **Step 1 becomes "document, don't capture."** Mark the latest existing snapshot's date in your records; treat it as the final.
- **Step 2 (config flip) becomes more urgent, not less.** The silent-failure window is already open: every command that reads the now-dead config is failing silently or with WARNING-level errors that don't surface to monitoring.
- **Step 3 must rely on whatever you already have** for comparison. You cannot side-by-side the two vendors during cutover, because side A is dead.

## When this applies

- The vendor's revocation predates your planned cancellation timeline
- Symptoms: previously working API key returns 401/403, support tickets are non-responsive, or the dashboard shows reduced access
- The migration is being forced by hostility, not by your choice — even if cost was the *original* reason for moving

## When this does NOT apply

- Cooperative cancellation on your timeline (the standard checklist works)
- Quota exhaustion that resets (call it migration when the quota cycles, not now)
- Self-imposed cutoff (you turned off access, the vendor didn't)

## Diagnostic signature

```
HTTP/1.1 403 Forbidden
WARNING: sem.core.apis.<vendor> - request failed for '<query>': Client error '403 Forbidden'
```

If you see this pattern across ALL queries (not just rate-limited ones) and you have not exceeded a documented quota, treat the vendor as hostile. Skip "capture fresh data" and accelerate the config-pointer flip.

## Concrete grounding

In a recent session, Sprint 0a was scoped as "final SEMrush rank-check before cancellation" — the assumption was that the SEMrush API would still answer requests until subscription cancel date. Running it returned `HTTP/1.1 403 Forbidden` on every keyword (95 + 96 + 129 = 320 attempts), with no quota signal and no rate-limit hint. User confirmation: "DON'T USE SEMRush API... we have no tokens.. they confiscated them... part of the reason I am leaving."

The bead was closed moot — the 2026-04-27 snapshot (6,663 rows, source='semrush') became the permanent final. Sprint 0b (the config-pointer flip) was then executed immediately because the silent-failure window was already active and every cron run of `sem seo rank-check` was logging 403 warnings with 0 results landing.

## Related

- [[saas-migration-pre-cancel-checklist-silent-failure-config-pointer-risk]] — the canonical pre-cancel checklist this entry refines for the hostile-vendor case
- [[post-flip-structural-verification-routing-vs-downstream]] — how to verify the config-pointer flip itself succeeded once the priority order is reset

---

## Source Context

Refinement of the SaaS migration pre-cancel checklist (2026-05-21), triggered by SEMrush token confiscation event (2026-05-21). The standard checklist assumes vendor cooperation. This entry documents the hostile-vendor variant where API access is revoked unilaterally, foreclosing step 1 (final fresh capture) and accelerating step 2 (config-pointer flip). Grounding from production incident: 320 SEMrush API calls returned 403 Forbidden across three keyword sets; user confirmed token confiscation was vendor-initiated policy, not quota/rate-limit exhaustion. The 2026-04-27 snapshot became the permanent final state; config-pointer migration became a 24-hour critical priority instead of a pre-cancel planning task.
