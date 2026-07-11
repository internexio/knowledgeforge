---
title: Chrome Extension Rendering Bug — Speculative API Shape vs Real Response Structure
source_mode: debugger → builder
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: stable
importance: 4
pinned: false
created: 2026-07-07
domain: debugging
topic: hypothesis-testing
tags: api, grounding, empirical
related_entries:
  - patterns/2026-06-10_mcp-tool-response-shape-live-verification-before-parsing.md
  - diagnostics/2026-05-25_http-adapter-silent-failure-integration-test-mandatory.md
  - diagnostics/2026-05-28_fastapi-shared-response-model-silently-strips-handler-fields.md
  - methodologies/2026-05-27_read-ground-truth-not-surface-signals-universal-antipattern.md
revises: null
superseded_by: null
---

# Chrome Extension Rendering Bug — Speculative API Shape vs Real Response Structure

## Problem

When building a Chrome extension that consumes an external API, rendering code is often written speculatively before the actual API response shape is verified. This creates a silent failure mode: the code runs without errors but produces a blank or zero-value UI because the assumed shape doesn't match reality.

### Concrete example (cos-browser-analyzer, bead e39)

The extension's `renderResults` function was written assuming the COS `/api/analyze/full` endpoint returned:
```json
{ "results": [{ "framework": "hape", "overall_score": 7.5, "dimensions": [...] }, ...] }
```

The actual API (FastAPI/Pydantic `FullAnalysisResponse`) returned:
```json
{
  "hape": { "framework": "hape", "overall_score": 7.5, "dimensions": [...], "recommendations": [...] },
  "big_five": { ... },
  "strategic_clarity": { ... },
  "framing_strategy": { ... },
  "combined_score": 7.5,
  "summary": "..."
}
```

The rendering code:
```js
// WRONG — data.results is always undefined
const scores = (data.results || []).map(f => f.overall_score);
(data.results || []).forEach(fw => list.appendChild(buildFrameworkBlock(fw)));
const allRecs = (data.results || []).flatMap(f => f.recommendations || []);
```

Result: no frameworks rendered, no bars filled, no recommendations shown. The overall score displayed as `0.0`. No JavaScript error — `[].map(...)` on an empty fallback array is valid.

## Why it silently succeeds

- `(data.results || [])` — the `|| []` fallback masks the undefined field
- Array methods on `[]` return `[]` without throwing
- The UI reaches the results state and shows headings and an empty score bar
- The user sees a "result" page with no content — looks like a loading or API failure, not a code bug

## Detection

The rendering function runs and `showState("results")` fires, but:
- Framework list is empty
- Score is `0.0` (or `NaN` depending on average logic)
- Recommendations section is hidden (no items)
- No console errors

When you see this pattern: **check the actual API response shape against what the renderer assumes before anything else.**

## Fix pattern

1. **Read the actual API schema** — Pydantic model, OpenAPI spec, or TypeScript interface. Don't infer from docs or variable names.
2. **Map named fields to an array** where needed:
```js
const FRAMEWORK_KEYS = ["hape", "big_five", "strategic_clarity", "framing_strategy"];
const frameworks = FRAMEWORK_KEYS.map(k => data[k]).filter(Boolean);
```
3. **Use pre-computed aggregate fields** (`combined_score`) instead of re-computing client-side averages that the API already provides.
4. **Log the raw response** during development: `console.log("API response:", JSON.stringify(result.data, null, 2))` before any rendering.

## When this applies

- Any extension/web client where the rendering code was written before the API was tested
- Typed backend APIs (Pydantic, Zod, TypeScript interfaces) where the actual serialization format differs from what was assumed
- APIs that return structured named fields (common in FastAPI `BaseModel`) instead of generic arrays

## When this does NOT apply

- When the frontend and backend were developed together against a shared contract (OpenAPI spec, codegen)
- When the API actually does return the assumed array format (verify before assuming it doesn't)

## Prevention

Before writing any rendering function that consumes an API:
1. Make one real API call (curl or test script) and log the raw response
2. Read the backend response model definition (`FullAnalysisResponse`, `BaseModel`, etc.)
3. Write the renderer against the real shape, not an assumed one

## Verified

Surfaced in cos-browser-analyzer bead e39 (2026-07-07). The `renderResults` function silently produced blank output on every real API call until the response shape was read from the COS backend Pydantic model (`FullAnalysisResponse` in `backend/app/api/analyze.py`).

## Source Context

Discovered during extension development session cos-browser-analyzer-extension-wiring. The extension consumes the COS `/api/analyze/full` endpoint. Rendering was initially written based on documented endpoint behavior assumptions. Live API invocation revealed the actual response structure was a keyed-object shape (framework names as keys) rather than the assumed array-of-objects format. The mismatch caused silent rendering failure: no console errors, but all framework widgets rendered empty. Grounding: direct observation in the codebase (extension + backend); 0.90 confidence reflects the concrete failure-to-fix link.
