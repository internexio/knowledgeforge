---
title: Default policy diverges by path — smart-default tri-state parameters for composite endpoints
source_mode: builder
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-18
domain: patterns
topic: validation
tags: api, latency, empirical, quality-gate
related_entries: [patterns/2026-05-18_composite-vs-atomic-mcp-tool-design.md]
---

# Default Policy Diverges by Path — Smart-Default Tri-State Parameters for Composite Endpoints

## Pattern

When a composite endpoint has paths with very different cost profiles (e.g. "generate from scratch" vs "refine my existing draft"), don't pick a single global default for the expensive sub-step. Instead make it a tri-state parameter (`None | True | False`) where `None` derives the effective default from another request field. This optimizes the common case while keeping explicit override on the table.

## Implementation Shape (Python / FastAPI / Pydantic v2)

```python
class CompositeRequest(BaseModel):
    draft: str | None = Field(default=None, ...)
    include_scoring: bool | None = Field(
        default=None,
        description=(
            "Run expensive scoring on the result. "
            "If None (default): derive from draft — score only if user provided one. "
            "Set explicitly to override either way."
        ),
    )

# In the endpoint:
if request.include_scoring is None:
    scoring_included = (request.draft is not None and request.draft.strip())
else:
    scoring_included = request.include_scoring
```

## Response Surfaces the Effective Decision

```python
class CompositeResponse(BaseModel):
    scoring_included: bool  # Always present — makes the policy decision visible
    persuasion: PersuasionResult | None = None  # None when scoring_included=False
    platform: PlatformResult | None = None
    rewrites: list[Rewrite] = []  # empty when scoring skipped
    one_thing: str  # always populated — explains how to opt in if skipped
```

## Three Forces

1. **Latency.** The expensive sub-step is the dominant cost. Skipping it on the common path is the only way to hit reasonable defaults.
2. **Honesty.** The response must surface whether the expensive step ran, not pretend it always does. Callers need to know what they got. The `scoring_included` field is non-optional in the response — even when false.
3. **Override-ability.** Power users and tests need explicit on/off. Don't take the override away by making the param `bool` with a fixed default — the tri-state preserves explicit choice.

## When This Applies

- Composite endpoints with measurably-different cost paths (e.g. ≥3× ratio)
- Caller types include both "fast common path" users AND "thorough audit" users
- The cost driver is a real LLM call / network round-trip / heavy compute (not just a few CPU ms)

## When This Does NOT Apply

- The expensive step's output IS the response — can't skip it
- Path costs are similar (no win from skipping)
- The two paths have different success criteria entirely (then they should be different endpoints)

## Grounding from Session

`POST /analyze/optimize-email` (COS backend) — composite endpoint orchestrating audience profile + draft generation + persuasion + platform scoring.

Before this pattern:
- Always ran scoring (PersuasionAnalyzer + PlatformAnalyzer in parallel via asyncio.gather)
- Measured: 47s total on test env
- ~35s of that was scoring on freshly-generated output

After this pattern:
- `include_scoring=None` (default) → scoring runs ONLY if `draft` was supplied
- Generate path (no draft): scoring skipped by default
- Refine path (draft supplied): scoring runs by default
- Override: pass `include_scoring=True/False` explicitly

Measured outcome on test env, same prospect payload:
- Generate path: 47s → **5.5s (88% reduction)**
- Refine path: ~40s (unchanged when scoring desired)
- Generate-with-explicit-opt-in: 42s (within expected envelope)
- Production smoke same-day verified 5.97s on prod (matched test envelope).

Tests cover all 4 states: generate-default-skip, generate-opt-in, refine-default-on, refine-opt-off.

## Counterexample / Failure Mode to Watch

- The tri-state hides intent — if the default switches behavior based on another field, document it loudly. The Pydantic Field description IS the documentation surface; agents and humans both read it.
- Test all four cells (default×supplied, default×missing, explicit-on, explicit-off). Two-cell coverage is insufficient.
- Don't extend this to >2 paths. If you find yourself adding `include_scoring`, `include_subject`, `include_rewrites` — that's a new request object, not more tri-state knobs.

## Cross-References

- **Composite vs atomic MCP tool design** — composites need fast-path defaults to be usable; atomic chains naturally bypass this question because the caller controls which atoms to invoke.
- **FastAPI StreamingResponse pre-flight gates** — different design pattern (gates run synchronously), but shares the "expensive path" concern; here we optimize away the expense entirely for some callers rather than pre-flight-gating it.

## Source Context

Built `optimize_email_for_prospect` MCP tool and backend endpoint during **cos-mcp-clarify-integration-phase2-3-prod-push** session. Initial `POST /analyze/optimize-email` always ran persuasion + platform scoring in parallel. Measured 47s on test env with fresh-generated output; profiling showed ~35s was scoring overhead that wasn't needed for the generate-and-return path. Introduced tri-state `include_scoring` parameter: None (default) derives from draft presence, True/False overridable. Result: generate path dropped to 5.5s, refine path stayed ~40s when scoring desired. Smoke test on prod verified same day. Pattern generalizes to any composite endpoint where sub-steps have 3+x cost variance and caller demand is heterogeneous.
