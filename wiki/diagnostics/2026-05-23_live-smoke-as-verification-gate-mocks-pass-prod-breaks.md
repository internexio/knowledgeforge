---
title: Live-smoke as the verification gate — mocks pass, prod still breaks
source_mode: debugger
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.92
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-23
domain: diagnostics
topic: hypothesis-testing
tags: [quality-gate, empirical, api, grounding, adversarial]
related_entries:
  - diagnostics/2026-05-18_http-status-signatures-deploy-verification-smoke-test.md
  - diagnostics/2026-05-18_vary-input-smoke-runs-llm-failure-modes.md
  - methodologies/2026-05-23_vendor-swap-semantics-recalibration-audit.md
---

# Live-smoke as the verification gate — mocks pass, prod still breaks

## Problem

Mock-based unit tests can pass 100% while production paths silently fail because:

- The test fixture schema drifts from the production migration (no CHECK constraints in tests, full CHECK constraints in prod)
- The mock contract assumes a vendor's response shape that differs from the live one
- The integration's runtime behavior depends on state (caches, rate limits, real corpus sizes) that mocks can't represent

A single live round-trip per integration — even one that produces a null/empty result — catches a class of bugs that no amount of mock coverage will surface.

## When to apply

- After shipping any feature that crosses a process boundary (HTTP API, DB write, filesystem mutation)
- After swapping vendors that nominally do "the same thing" — the new vendor's response shape, rate limits, error codes, and match semantics will differ
- Before declaring "tests pass, shipping" on integration-touching code
- One real call per integration is enough — burn $0.01–0.05 of API spend rather than ship a latent bug

## When NOT to apply

- Pure-internal refactors with no external surface (e.g., renaming a helper, restructuring imports)
- Code paths fully covered by existing live smoke tests (e.g., the second feature shipped against a vendor with proven live coverage)
- When the cost of a real call materially exceeds the cost of the bug it would surface (rare — most APIs are cheap enough)

## Grounding (sem-tools session 2026-05-23)

Two real bugs shipped past 100%-passing mocks during this session, both caught immediately on live smoke:

### Bug 1: CHECK constraint silently rejected F10.1 + F10.2 detector inserts

- Production DB schema: `severity TEXT CHECK (severity IN ('critical','high','medium','low'))` (sem/core/db.py:68 at v3)
- All 6 F10 spam-risk detectors emit `severity="warning"`
- Every recommender INSERT therefore raised `sqlite3.IntegrityError`
- 245+ mock tests passed because `tests/test_spam_risk_wiring.py` fixture defined `severity TEXT` with NO CHECK constraint — pure schema drift
- Caught by attempting to inject a synthetic row via the live recommender pipeline (C2 "eyeball the recommender's rendered output" task)
- Fix: v3→v4 migration expanding CHECK + test fixture mirrored to prod schema to prevent recurrence (commit 705812c)

### Bug 2: F9 threshold misbehaved against YouTube native search

- 248 tests passed for F9 after the Serper→YouTube Data API refactor (sem-tools-edr)
- Live smoke against 5 tracked brands × 2 topic types each produced counts that contradicted the design assumption (lacking restaurants showed HIGH presence on generic topics)
- Root cause: YouTube native search OR-matches across title + description + tags; mocks only stubbed the response shape, not the matching semantics
- Fix: post-filter to require brand-in-title; threshold itself was correct (commit c2970d8)

## Anti-patterns

- Skipping live smoke "because the mocks pass" — the failure modes mocks miss are exactly the ones that bite in prod
- Treating live smoke as "manual QA, do later" — the failures it catches are usually fast to fix in-context and expensive to debug after merge
- Burning the live-smoke budget on full multi-page audits when one quick round-trip per integration suffices
- Asserting "shipping" without having seen the integration round-trip in production at least once

## Lightweight implementation pattern

Keep a `scripts/smoke_<feature>.py` per integration that:

1. Loads real config from the project's `.env`
2. Makes ONE live call per code path the feature exercises
3. Prints the response shape + the detector/feature's output
4. Costs ≤ $0.05 to run

This file pays for itself on the first bug it catches. The F10.2c smoke in this project found two FPs across two sessions (Jaccard FP + verified the overlap-coefficient fix).

## Source Context

Discovered during sem-tools batch-and-vendor-eviction session (2026-05-23). Two real integration bugs (schema CHECK constraint silently failing on INSERT, and vendor-response-shape mismatch in YouTube API matching semantics) shipped past 100%-passing mock test suites. Both were caught within minutes of the first live smoke call. The pattern generalizes: mocks verify code paths and contracts you explicitly model; they cannot catch schema drift between fixture and production, or runtime behavior that depends on real vendor responses, rate limits, or corpus size. A single cheap live call per integration is the gate that mocks cannot be — it's empirical, adversarial, and grounding is 0.92 because it's directly observed in two independent bug classes within the same session.
