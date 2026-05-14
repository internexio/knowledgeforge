---
title: Pricing-table key vs default value — don't collapse identical literals when extracting settings
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.75
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-13
domain: diagnostics
topic: refactoring
tags: [debugging, anti-pattern, configuration, empirical, literal-extraction, find-replace-trap]
related_entries: []
---

# Pricing-table key vs default value — don't collapse identical literals when extracting settings

## The trap

When extracting a hardcoded string literal into a settings variable, you may find the *same literal* appearing in two roles within one module — and they have opposite semantics:

```python
# Role 1: DATA (lookup key — must stay literal)
ANTHROPIC_PRICING = {
    "claude-sonnet-4-20250514": {
        "input_per_1m": Decimal("3.00"),
        ...
    },
    "claude-haiku-4-5-20251001": {...},
}

# Role 2: DEFAULT VALUE (config — should be hoisted to settings)
DEFAULT_MODEL = "claude-sonnet-4-20250514"
```

The naive sweep ("replace every occurrence of the literal with `settings.anthropic_default_model`") would replace the dict key too, silently breaking the pricing lookup:

```python
# WRONG — replaced both occurrences:
ANTHROPIC_PRICING = {
    settings.anthropic_default_model: {  # ← now a runtime-only key
        ...
    },
}
```

This still type-checks, may even pass tests if the default happens to match what the test data uses, but:
- Other models' prices can no longer be looked up by their literal ID (they're not in the dict because the key is now dynamic).
- If the setting is later changed, the pricing table follows it catastrophically — `ANTHROPIC_PRICING["claude-sonnet-5"]` would now hold the prices for the OLD sonnet-4 model.

## The rule

Before doing a global find/replace on a string literal:

1. **Audit each occurrence's role:** Is this literal *data* (a dict key, enum value, lookup tag) or *configuration* (a default that controls behavior)?
2. **Replace only the configuration roles.** Dict keys, schema fields, match-statement labels, lookup tags stay literal.
3. **Leave a comment at the data sites** explaining why they didn't get the sweep: *"This literal is a dict key (data), not a default. Do not collapse to settings.X."*

## When it applies

Any string-literal extraction refactor where the literal also appears as:
- Dict keys in pricing / capability / rate-limit tables
- Switch/match case labels
- Schema field names
- Lookup tags in registries
- Enum values
- Test fixture identifiers (these may also need to stay literal so tests remain decoupled from config)

## Grounding

Surfaced during the COS STR-H8 refactor (commit `a4f88ba`, 2026-05-13). The literal `"claude-sonnet-4-20250514"` appeared 19 times across the backend. 17 were configuration roles (call-site `model=` arguments, module-level `DEFAULT_MODEL` constants). Two were data:

- `app/services/token_economics.py:11` — `ANTHROPIC_PRICING` dict key
- `app/tests/test_chat_kf.py:21` — test fixture data

Both required leaving the literal in place. The `token_economics.py` case got an explicit comment: *"Keys are model IDs; the table is data, not a default. Do not collapse to settings.anthropic_default_model."*

If the trap had been missed, `ANTHROPIC_PRICING.get(model)` lookups for any non-default model would have returned None, falling back to default pricing — silently wrong cost math, no error log.

## Related

- The parent finding from the same refactor: fabricated-default-fallback-at-call-site (four sibling call sites had a different but related anti-pattern where config defaults were added at call sites instead of module level).

## When This Does NOT Apply

- Single-occurrence literals that appear only in configuration contexts
- Enum values where the enum itself is not used as a lookup key in another structure
- Refactors where you've already verified the literal doesn't appear in data structures

## Source Context

Discovered during the COS STR-H8 anthropic-model-settings refactor session (2026-05-13). A global find-and-replace sweep for `"claude-sonnet-4-20250514"` would have accidentally collapsed the `ANTHROPIC_PRICING` dict key from a literal to a dynamic reference, breaking non-default-model lookups. The literal audit caught both the dict-key and test-fixture roles, preserving them while extracting the 17 configuration roles correctly.
