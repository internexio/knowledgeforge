---
title: Threading a new field through endpoints — enumerate ALL request/response models, not just the dominant one
source_mode: direct
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-28
tags: refactoring, regression-prevention, api-design, completeness-checks, sweep-changes, pydantic
related_entries:
  - diagnostics/2026-05-23_live-smoke-as-verification-gate-mocks-pass-prod-breaks.md
  - methodologies/2026-05-26_deterministic-scan-before-claiming-refactor-audit-beads.md
  - patterns/2026-05-16_discriminated-enum-extension-7-point-checklist.md
---

# Threading a New Field Through Endpoints: Enumerate ALL Request/Response Models, Not Just the Dominant One

## The Rule

When adding a new field/parameter "everywhere" across a set of API endpoints — request models, response models, handler signatures, service-layer calls — the failure mode is NOT getting the dominant/obvious model wrong. It's **MISSING a sibling model that participates in a subset of the endpoints**.

Before declaring a field-threading sweep complete, **enumerate every request model and every response model that feeds the affected endpoints**, and verify each one was updated. The dominant shared model is the one you'll remember; the one-off sibling used by a single endpoint is the one that ships a regression.

## Why The Sweep Pattern Is Dangerous

A sweep change feels mechanical and uniform, which lulls you into trusting a find-replace or a "I updated the model" mental checkmark. But endpoints rarely share ONE model uniformly:

- Most endpoints use a shared `AnalysisRequest`
- One endpoint uses a bespoke `PersuasionAnalysisRequest` (different fields, separate class)
- The handler code for ALL endpoints was updated to reference `request.temperature`
- → the bespoke model lacks `temperature` → AttributeError 500 on every call to that one endpoint

The handler-side change was uniform (good), but the model-side change was NOT applied to the sibling (bad). The asymmetry is the trap.

## The Completeness Procedure

1. **List the endpoints** affected by the field.
2. **For each endpoint, identify its request model AND its response model** (they're often not the shared default). `grep` the route signatures: `async def handler(request: SomeModel)` and `response_model=SomeModel`.
3. **Build the distinct set of models** across all endpoints.
4. **Apply the field to every model in that set** — not just the most common one.
5. **Grep for the field's usage** (`request.newfield`, `result["newfield"]`) and confirm every referencing site has a defining model.
6. **Write a test that exercises all model variants** — unit tests on the service layer won't catch request/response model boundaries if they only use the shared model.

## Pairs With Output-Side Stripping

The same incomplete-enumeration root cause bites on BOTH sides of the request/response boundary:

- **Input side:** a sibling REQUEST model missing the field → AttributeError 500
- **Output side:** a shared RESPONSE model missing the field → silent strip (see [FastAPI response_model field-stripping patterns](diagnostics/2026-05-23_live-smoke-as-verification-gate-mocks-pass-prod-breaks.md))

Audit both directions when threading a field.

## When It Does NOT Apply

- Single-endpoint changes (only one model involved — nothing to enumerate).
- Codebases with one universal request/response model and zero siblings.
- Changes that only touch the service layer and never cross the API model boundary (but these are rare in FastAPI/Pydantic stacks).
- Batch migrations using automated tooling (code-mods, type-aware linters) that enforce exhaustiveness.

## Concrete Grounding: A 3-Regression Cascade from One Sweep

**[project] 2026-05-27/28, the cos-bbf "add temperature everywhere" sweep:**

1. `temperature` added to the shared `AnalysisRequest` + all 8 analyzer `.analyze()` signatures + `_invoke_llm`. Looked complete; 1244 tests passed.

2. **cos-b3q (P0):** `/api/analyze/persuasion/{domain}` uses the bespoke `PersuasionAnalysisRequest`, which was NOT updated. The handler referenced `request.temperature` → AttributeError → 500 on every persuasion call in prod. A sibling request model was missed.

3. **cos-z93:** separately, the shared `AnalysisResponse` (output side) silently stripped analyzer-specific fields (`gap_analysis`, `key_issues`, `frame_analysis`) because the response model wasn't extended when the analyzers started returning them.

Both regressions trace to the same root: a sweep change that updated handlers/services uniformly but missed the per-endpoint model variations. An explicit "enumerate all models feeding these endpoints" step before marking the sweep done would have caught both. (The unit tests passed because they exercised the analyzer layer, not the full request→model→handler→response_model serialization path — a reminder that model-boundary regressions need request/response-level integration tests, not just service-layer tests.)

## When It Pays Off Most

- FastAPI/Pydantic applications with per-endpoint request/response models (common for domain-specific handlers or multi-tenant APIs)
- Refactor sweeps affecting 5+ endpoints simultaneously
- Codebases where service-layer tests dominate and request/response boundary tests are sparse
- Field additions affecting both input validation and output serialization

## Verification Checklist

Before marking a field-threading sweep complete:

- [ ] Listed all affected endpoints
- [ ] For each endpoint: identified request model, response model
- [ ] Built distinct set of all models (request + response, across all endpoints)
- [ ] Applied field to every request model in the set
- [ ] Applied field to every response model in the set
- [ ] Grepped for usage of the new field; confirmed all referencing sites have the model
- [ ] Wrote an integration test exercising all model variants (not just the shared one)
- [ ] Ran full test suite including request/response boundary tests

## Source Context

Discovered during [project] session 2026-05-27/28 while analyzing a field-threading regression cascade (cos-bbf feature + cos-b3q + cos-z93). A single sweep change to add `temperature` parameter resulted in three separate regressions: two from missing sibling request/response models, one from silent response-field stripping. The root cause was incomplete model enumeration before declaring the sweep done. The framework captures the completeness procedure and the grounding example to prevent future cascades.

