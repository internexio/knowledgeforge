---
title: Anthropic model-EOL incident response is a 3-phase fix, not a 1-line change
date: 2026-06-16
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.95
staleness_risk: slow_decay
importance: 5
tags: [anthropic, model-deprecation, incident-response, prod-debugging, llm, claude]
---

# Anthropic model-EOL incident response is a 3-phase fix, not a 1-line change

When a Claude model reaches end-of-life and starts returning `404 model_not_found`
in production, the obvious config-var migration is **only the first of three
required phases**. Newer model versions change output formatting and verbosity
in ways the old model's quirks-by-convention masked. Plan for hour-scale
debugging, not a minute-scale fix.

## The three phases

### Phase 1 — Model migration (~10 min)
- Single config-var change (e.g. `settings.anthropic_default_model` from
  `claude-sonnet-4-20250514` → `claude-sonnet-4-5`).
- Verify the new model resolves before shipping: send a trivial probe
  `messages.create(model=X, max_tokens=10, messages=[{"role":"user","content":"hi"}])`
  and confirm 200 (not 404). The Anthropic dashboard model list lags reality.
- Add pricing entry to whatever token-economics table tracks per-model costs.
  Keep the EOL'd model's entry for historical cost analyses.

**Trap:** Shipping this alone and assuming the bug is fixed. The endpoint
will return 200 (no more 404s) but the analysis will still be junk —
phases 2 and 3 are still required.

### Phase 2 — JSON parser hardening (~30 min)
Newer Claude models are more verbose and wrap output in markdown code fences
where older models returned raw JSON. Specific failures observed on
claude-sonnet-4-5 vs claude-sonnet-4-20250514:

- Output wrapped in `​```json\n{...}\n​```` rather than raw `{...}`.
  Any regex matching JSON via brace pairs (`\{[\s\S]*?\}`) is non-greedy
  on inner braces and matches the FIRST closing `}` on a nested-object
  response. Rewrite to match fence pairs: `​```(?:json)?\s*([\s\S]*?)​````.
- Response 2-3× longer than the old model's. Default `max_tokens=4096`
  truncates mid-stream — even with a correct regex, the truncated JSON
  fails to parse. Bump to `max_tokens=8192` (or per-analyzer override).
- Add a fallback for truncated responses (no closing fence): capture
  everything after the opening fence to end-of-text and try parsing what
  you got.

### Phase 3 — Prompt schema-locking (~30 min × N analyzers)
This is the part that surprises everyone. "Format response as structured
JSON" is too loose for newer models. claude-sonnet-4-5 chose:
- **list of objects with a `name` field** where the old model chose
  **dict keyed by snake_case dimension name**
- **nested object for the overall score** (`{weighted_score, calculation, interpretation}`)
  where the old model returned a scalar

Loose instructions let newer models pick whichever shape is most "natural"
to their training. Lock the shape with a literal JSON template:

```
OUTPUT FORMAT — return ONLY a single JSON object matching this exact schema.
No markdown, no prose, no code fences, no additional top-level keys:

{
  "framework_analysis": {
    "dimension_scores": {
      "dimension_a": {"score": 0, "explanation": "...", "improvement": "..."},
      "dimension_b": {"score": 0, "explanation": "...", "improvement": "..."}
    },
    "overall_score": 0.0,
    "recommendations": ["...", "...", "..."]
  }
}

Use these EXACT snake_case keys. Flat dict keyed by name (NOT an array).
Score must be a number 0-10. Overall must be a single number, NOT a nested object.
```

## Why this matters

The classic "swap the model name" hotfix is muscle memory from the SDK-stable
era. With Claude (and likely other frontier LLMs), model upgrades drift
output format. If your downstream parser was tightly coupled to the old
model's accidental conventions, you'll ship a green CI build that still
produces null/default scores for every user.

Smell test that proves you're in this trap, not the obvious one:
- Endpoint returns 200 (not 500 or 404)
- Logs show no exceptions
- But the response payload has `null` framework scores or scalar=0/default values
- Direct LLM probe shows the model IS reachable

## Verified grounding

COS free-tool repair 2026-06-15/16. `claude-sonnet-4-20250514` EOL'd on
2026-06-15. Four prod commits in sequence:
- `8fbf084` Phase 1 — model migration (returned 200 but null scores)
- `c769cbd` Phase 2 — fence-regex + max_tokens bump (still null because shape changed)
- `f63c563` Phase 3 — explicit JSON schemas in 4 analyzer prompts (verified working: HAPE 6.5/8 dims, BigFive 8.8/5 dims, StrategicClarity 6.0/5 dims, FramingStrategy 5.8/5 dims, all returning real non-default scores)

## Pre-flight checklist before next model EOL

- [ ] Inventory every prompt that uses LLM JSON output. Schema-lock NOW
      with explicit examples, before the next deprecation forces a scramble.
- [ ] Audit parser regexes: any `\{[\s\S]*?\}` non-greedy brace match is
      a latent bug.
- [ ] Set max_tokens explicitly per-analyzer with headroom (~2× expected
      response size).
- [ ] Keep at least 2 working model IDs in your config for fast rollback.

## Related

- [[fence-pair-json-regex-not-brace-pair]] — the specific regex fix from
  Phase 2 (sibling pattern, narrower scope)
- [[lock-llm-json-output-with-explicit-schema-example]] — the Phase 3
  pattern in isolation (sibling pattern, applies even without an EOL event)
