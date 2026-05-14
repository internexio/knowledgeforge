---
title: Fabricated-default fallback at call site hides upstream data quality bugs
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-13
domain: debugging
topic: error-classification
tags: [adversarial, quality-gate, empirical, stable]
related_entries: [diagnostics/2026-05-13_pricing-table-key-vs-default-value-collapse.md]
---

# Fabricated-default fallback at call site hides upstream data quality bugs

## The pattern

```python
# At a recording / persistence call site:
await db.create_message(
    ...,
    model=usage.get("model", "claude-sonnet-4-20250514"),
    # or:
    output_tokens=usage.get("output_tokens", 0),
)
```

When the optional field `model` (or any analytics/billing field) is missing
from `usage` because the producer forgot to populate it, the call site silently
substitutes a hardcoded "reasonable default" and records that as ground truth.

## Why this is harmful

The recorded value LOOKS correct downstream — dashboards, cost attribution,
audit logs all show the default value as if it had been measured. The
upstream omission becomes invisible:

- **Cost mis-attribution:** All "unknown model" requests get charged at the
  fabricated default's price, even if they actually used a cheaper/pricier
  model. Cost-by-model dashboards become wrong.
- **No signal to fix:** Because the recorded row is well-formed, no error
  log fires, no alert triggers. The producer-side bug can sit undetected
  for months.
- **Compounds over time:** Each new caller copies the same `get("x", DEFAULT)`
  idiom because it "works." The fabricated default becomes load-bearing.

## When it applies

Any optional field that is:
- recorded for downstream analytics, billing, or audit;
- expected to be populated by an upstream producer (API response, message
  envelope, telemetry payload);
- typed as `Optional[str]` / `str | null` in the data layer.

Especially common with: model IDs, request IDs, tier/plan labels, A/B variant
tags, feature flag values, region/zone codes.

## The fix

1. **At the call site:** drop the fabricated default — `usage.get("model")`,
   not `usage.get("model", DEFAULT)`. Let None propagate.
2. **At the consumer:** make the field truly optional in the persistence
   layer (`if model: data["model"] = model`). For cost/quality math that
   needs *some* value, fall back to a settings-sourced default INSIDE the
   consumer and log a WARNING noting the call-site omission. The warning is
   the signal upstream forgot to record the field.
3. **Record what was actually passed** — write `None` (or `model_used: null`)
   when nothing was passed, even though cost math falls back. This preserves
   the signal that the row is fallback-imputed, not measured.

## When NOT to apply

- **Truly defaulting fields**, where the consumer canonically owns the value
  (e.g. `analysis_depth: str = "full"` when no depth is part of the request
  contract).
- **Pricing-table lookups** where the literal string is a *key* in a
  dict, not a default value (different pattern — see related entry on
  pricing-table-key-vs-default).
- **Where signal-to-fix has another channel** (e.g. structured logging
  already records the producer-side omission separately).

## Grounding

Originally surfaced by the COS code audit (`CODE_REVIEW_2026-05-12.md`,
finding STR-H8). The exact call sites were `api/chat.py:1168, 1186, 1417, 1435`:

```python
model=usage.get("model", "claude-sonnet-4-20250514"),
```

repeated four times in two endpoints (KF chat + unified chat). Backed by the
audit's note: *"silently mis-attributes cost if upstream forgets to record
model."* Confirmed during the STR-H8 fix that the same model literal was
also hardcoded in 9 producer-side call sites (Anthropic API invocations) —
those producers were one Anthropic-SDK refactor away from forgetting to set
`model=` in their `messages.create` call, which would have made the fallback
silently take over.

Fix applied as commit `a4f88ba` 2026-05-13:
- 4 call sites: `usage.get("model", "claude-...")` → `usage.get("model")`
- `record_analysis(model: Optional[str] = None)` logs WARNING when None,
  uses settings default for cost math, writes `model_used = None` to DB.

## Related

- [[2026-05-13_pricing-table-key-vs-default-value-collapse.md]] — the dual-meaning
  string-literal trap encountered in the same refactor (do NOT collapse the
  pricing-table dict key into the new setting; they look identical but serve
  different roles).

## Source Context

Discovered during the COS STR-H8 anthropic-model-settings refactor session (2026-05-13).
Four call sites in `api/chat.py` were using `usage.get("model", DEFAULT_LITERAL)` to
record billing metrics, masking upstream failures to populate the model ID. A fifth related
pattern was identified where the same hardcoded literal was used as a fallback default
in multiple producer-side call sites, creating a cascade risk. Both issues were addressed:
call sites now let None propagate, consumer layer logs when it falls back, and the database
records the fallback-imputed state separately from measured values.
