---
title: Lock LLM JSON output with an explicit schema example in the prompt
date: 2026-06-16
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.95
staleness_risk: stable
importance: 5
tags: [prompt-engineering, llm, json, schema, anthropic, claude]
---

# Lock LLM JSON output with an explicit schema example in the prompt

"Format your response as structured JSON" is too loose for frontier LLMs.
Different model versions of the same family will pick different shapes for
the "structured JSON" — and your downstream parser only knows one shape.

## The failure mode

Old model (claude-sonnet-4-20250514) — inferred this shape:
```json
{
  "psychological_systems_scores": {
    "identity_recognition": {"score": 8, "explanation": "..."},
    "social_connection":    {"score": 6, "explanation": "..."}
  },
  "overall_score": 7.2
}
```

New model (claude-sonnet-4-5) given the SAME prompt — picked this shape:
```json
{
  "hape_analysis": {
    "psychological_systems": [
      {"name": "Identity Recognition", "score": 8, "explanation": "..."},
      {"name": "Social Connection",    "score": 6, "explanation": "..."}
    ],
    "overall_hape_score": {
      "weighted_score": 7.2,
      "calculation": "...",
      "interpretation": "..."
    }
  }
}
```

Three drift dimensions in one model upgrade:
1. **Extra wrapper key** (`hape_analysis` at top level)
2. **List of objects** with `name` field instead of dict keyed by snake_case
3. **Overall score as nested object** instead of scalar

Each is reasonable on its own. None matches what the parser expected.
Parser falls back to defaults silently; user sees junk output.

## The fix

Include a literal JSON template in the prompt with explicit keys and types.
Specify what NOT to do (array vs dict, scalar vs nested, key naming).

```
OUTPUT FORMAT — return ONLY a single JSON object matching this exact schema.
No markdown, no prose, no code fences, no additional top-level keys:

{
  "framework_analysis": {
    "dimension_scores": {
      "dimension_a": {"score": 0, "explanation": "...", "improvement": "..."},
      "dimension_b": {"score": 0, "explanation": "...", "improvement": "..."},
      "dimension_c": {"score": 0, "explanation": "...", "improvement": "..."}
    },
    "overall_score": 0.0,
    "recommendations": ["...", "...", "..."]
  }
}

Use these EXACT snake_case dimension keys. Flat dict keyed by name
(NOT an array of objects with a "name" field). Score is a number 0-10.
Overall is a single number, NOT a nested object.
```

Three properties of an effective schema-lock:
1. **Concrete keys** — name every expected key with type-correct placeholder
   (`0` for int, `0.0` for float, `"..."` for string, `[...]` for array).
2. **Anti-pattern callouts** — explicitly forbid the shapes you've seen
   newer models pick ("NOT an array", "NOT a nested object").
3. **No-fences instruction** — tell the model not to wrap output in
   `​```json ... ​```` fences (even if your parser can handle them, raw
   JSON saves tokens and parsing complexity).

## When to use this pattern

- ANY LLM call where downstream code parses the response as structured data
- Especially when the prompt is reused across model versions
- Especially when output shape drift would manifest as silent defaults
  rather than loud errors

## When this might NOT be enough

- Very long schemas (10+ nested levels) — models still drift on edge keys.
  Add structured output mode (Anthropic's tool-use forcing, OpenAI's
  `response_format: json_schema`) instead.
- Free-text quality is critical (the schema-lock pushes the model toward
  filling slots rather than reasoning). Counter with explicit
  "fill explanation with 2-3 substantive sentences" in the schema.

## Verified grounding

Applied to 4 COS analyzers (HAPE, BigFive, StrategicClarity, FramingStrategy)
during the 2026-06-15/16 free-tool repair. Before schema-lock: all dimensions
defaulted to 7.0 / null. After: real differentiated scores observed
(8/3/7/4/9 spread across HAPE dimensions on a single test input). Verified
via direct call against claude-sonnet-4-5 in the cos-prod container.

## Related

- [[anthropic-model-eol-incident-response-three-phase-fix]] — the umbrella
  context that surfaced this pattern (Phase 3 of the 3-phase response)
- [[fence-pair-json-regex-not-brace-pair]] — sibling parser fix (Phase 2);
  this prompt fix sidesteps fence handling entirely if model follows the
  "no fences" instruction
