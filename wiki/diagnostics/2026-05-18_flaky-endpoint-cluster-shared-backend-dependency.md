---
title: Flaky-endpoint cluster across same-parent subresources = shared backend dependency
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.8
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-18
tags: empirical, stable, grounding, error-classification, root-cause-analysis, dependency-failure
related_entries: []
---

# Flaky-endpoint cluster across same-parent subresources = shared backend dependency

## The heuristic

When ≥3 distinct subresource endpoints under the same parent (project,
account, organization, etc.) intermittently 500 within the same time
window, do NOT triage as 3 separate bugs. Almost certainly a single
shared backend dependency is failing under burst load.

Common shared dependencies that produce this signature:
- DB connection pool exhaustion (Supabase / pgbouncer / equivalent)
- A shared auth middleware that throws on cache miss
- A shared cache layer (Redis) timing out
- A shared service init that's slow on cold start
- An external API call (e.g. Stripe customer lookup) embedded in
  the auth path that itself flakes

## Diagnostic signature (positive evidence)

You'll see something like this in a single project's UI on initial
load or right after a heavy operation completes:

| Section                  | Sometimes works | Sometimes 500s |
|--------------------------|-----------------|----------------|
| Personas                 | ✓               | ✓              |
| Campaigns                | ✓               | ✓              |
| Recent Chats             | ✓               | ✓              |
| Weekly suggestions       | ✓               | ✓              |
| (the parent itself)      | ✓               | ✓ (sometimes)  |

Reload the page: a DIFFERENT subset fails this time. No correlation
between which subset fails. This is the key signal — uncorrelated
flake across endpoints that share nothing at the route level but
share something at the dependency level.

## Anti-pattern: triaging as N separate bugs

Filing one bug per failing endpoint costs N× the engineering effort and
produces N partial fixes (retries, defensive defaults, fallback UIs).
None of those fixes the root cause. Three months later the bugs reappear
in a slightly different combination because the shared dependency is
still broken.

The right move: file ONE parent bug with the dependency-suspected
hypothesis, then close the per-endpoint manifestations as "duplicate of
[parent] — related" to keep the trail. Investigation effort consolidates.

## How to confirm

1. Tail the backend logs during a window of 500s. Cluster by stack-trace
   suffix — if all the 500s point at the same library frame (pg pool
   acquire, jwt verify, redis get, etc.), that's your dependency.
2. Reproduce by deliberately running the heavy operation that precedes
   the flakes (in the COS case, finishing a 15s SEO audit was the
   reliable trigger). The flake should cluster right after that
   operation completes.
3. Compare to a working path: if some other endpoint (e.g. the /chat
   context rail in COS) reads the SAME data via a different path and
   never flakes, the dependency that's failing isn't the data store —
   it's something on the per-endpoint path.

## When this does NOT apply

- A single endpoint flaking by itself (different cause profile).
- Flakes correlated with a specific deploy or container restart (likely
  startup race or env-var issue, not dependency overload).
- Flakes only on writes, never reads (likely transactional / lock
  contention, not pool exhaustion).
- All failures returning the same error code at the same time (likely
  a service-down event, not a dependency flake).

## Real-world incident (grounding)

COS E2E run on 2026-05-17 caught this pattern:
- Project page Personas: 500 (intermittent)
- Project page Campaigns: 500 (intermittent)
- Project page Recent Chats: 500 (intermittent)
- Weekly Post Suggestions: 500 (intermittent)
- Project itself "Failed to load project.": 500 after audit
  completion (intermittent)

All five flaked uncorrelatedly across the same hour. Reloads fixed a
random subset. Same project. The COS chat context rail (a separate
endpoint reading the SAME project data) never flaked — proving the
data exists, the dependency on the per-endpoint path doesn't.

Filed as a single bead (cos-p9a) with four related-link beads for the
specific manifestations. Triage cost: 1 investigation instead of 4.

## Source Context

Discovered during E2E testing of COS via Chrome MCP (2026-05-17 session).
The pattern emerged across five distinct endpoints (Personas, Campaigns,
Recent Chats, Weekly Suggestions, and the parent Project itself) under
the same parent resource. All flaked intermittently within the same
time window, with uncorrelated failures across reloads. Contrast with
a working read path (chat context rail) that accesses identical data
but never flaked — establishing the data-store integrity and pointing
to a shared dependency on the per-endpoint path. Root cause was later
confirmed to be a shared resource constraint (connection pool or
similar) triggered by the heavy 15s SEO audit operation preceding
the flake cluster. Grounding reflects direct observation in production
E2E testing.
