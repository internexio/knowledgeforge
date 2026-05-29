---
title: FastAPI shared response_model silently strips handler-specific fields
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-28
domain: diagnostics
topic: api-design
tags: fastapi, pydantic, api-design, serialization, debugging, web-frameworks
related_entries:
  - patterns/2026-05-12_fastapi-streaming-preflight-gates.md
  - architecture/2026-05-14_domain-exceptions-exclude-http-metadata.md
revises: null
superseded_by: null
---

# FastAPI Shared response_model Silently Strips Handler-Specific Fields

## The Gotcha

When multiple FastAPI route handlers share a single `response_model` Pydantic class, but individual handlers return dicts containing MORE fields than the shared model declares, FastAPI/Pydantic **silently drops the undeclared fields during response serialization**. No error, no warning, no log line — the field simply vanishes from the HTTP response while remaining present in the handler's return value.

This is by design: `response_model` acts as an output filter/validator. Pydantic v2 only serializes fields declared on the model. Extra keys in the source dict are discarded.

## How It Manifests

A field is present in:
- The function's `return {...}` dict (visible in source)
- The analyzer/service layer that produced it (visible in source)

…but ABSENT from the actual JSON the client receives. A developer reading the source concludes "the code returns it" and wastes time hunting for a deploy lag, a caching layer, or an environment difference — when the real cause is the response_model schema.

## Diagnostic

When a field is in the handler's return dict but missing from the HTTP response:

1. Find the route decorator: `@router.post(..., response_model=SomeModel)`
2. Check whether `SomeModel` declares that field
3. If not — that's the silent strip. The fix is to add the field to the model (typically `field: T | None = None` for backward compatibility).

## When This Bites Hardest

- **Shared response models across heterogeneous handlers.** If `AnalysisResponse` is the response_model for 4 endpoints but only 1 of them returns `gap_analysis`, that field is stripped from that 1 endpoint's responses. The other 3 are unaffected because they never produced it.
- **Refactors that add fields to the service layer** without touching the API schema. The new data reaches the handler but dies at serialization.

## The Fix Pattern

Add the field as Optional with a None default:

```python
class AnalysisResponse(BaseModel):
    framework: str
    overall_score: float
    # ... universal fields ...
    gap_analysis: dict | None = None      # only big_five populates this
    key_issues: list | None = None        # only strategic_clarity
    frame_analysis: dict | None = None     # only sovereign_mind
```

Optional + None default is backward compatible: handlers that don't populate the field leave it None; clients that don't read it are unaffected.

## When It Does NOT Apply

- Handlers with their own dedicated response_model (no sharing) — the model already matches the return shape.
- Endpoints returning the model instance directly (`return SomeModel(**data)`) rather than a dict — though the same filtering still applies, the mismatch is usually caught at construction.
- `response_model=None` or no response_model — FastAPI returns the dict as-is, no filtering.

## Concrete Grounding

[project] 2026-05-28: `/api/analyze/big-five` was missing `gap_analysis` from its response, blocking a downstream OCEAN_projection scoring step. The `big_five` analyzer's `analyze()` returned a dict WITH `gap_analysis` (confirmed in both local and prod source via `docker exec grep`). Root cause: the shared `AnalysisResponse` model (used by big_five, strategic_clarity, framing_strategy, and hape) declared only 5 universal fields. The same silent strip also affected `key_issues` (strategic_clarity) and `frame_analysis` (sovereign_mind) — none had surfaced yet because those consumers hadn't been exercised. Fixed by adding all three as `T | None = None`. The user initially suspected "deploy lag" precisely because the source clearly returned the field — the classic symptom of this gotcha.

## Related Patterns

This is distinct from but complements the general "domain exceptions should not carry HTTP metadata" pattern (2026-05-14) — that pattern is about intentional decoupling, while this gotcha is about **unintentional silencing** due to schema mismatch. Also related to "fastapi-streaming-preflight-gates" (2026-05-12) — both are about FastAPI's implicit filtering behavior that can hide bugs if not caught at design time.

## Source Context

Discovered during cos-variance-beads session 2026-05-28. The `/api/analyze/big-five` endpoint returns `gap_analysis` from the analyzer service layer, but the shared `AnalysisResponse` model didn't declare it. The field was silently stripped from the HTTP response. Grounding score 0.9 reflects the direct observation of the bug in production, confirmation of the root cause via source inspection, and verification that the same pattern silently affected two other fields in the same shared model.
