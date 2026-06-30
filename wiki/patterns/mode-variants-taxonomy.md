---
title: Mode-Label-with-Variants Taxonomy
source_mode: expert_era
source_session: redacted
created: '2026-05-10T00:00:00Z'
date: '2026-05-10'
confidence: 0.85
grounding_score: 0.85
grounding_source: 'Stage 2 ERA finding F1 (chain-log-01-tool-calling §F1). Mechanically
  derived from

  enumerating Critic and Expert trigger-phrase tables and observing 4 distinct

  output formats per mode label, distinguished only by trigger phrase + chain

  context. Variant-level disaggregation makes mode-selection accuracy meaningful.

  '
source_fingerprint: tool-calling-audit-track-c-era-f1
novelty_type: new_pattern
staleness_risk: low
importance: 4
pinned: true
accreted_in: 7.2.0
related:
- modules/05_expert_agent.md
- modules/07_critic_agent.md
- modules/04_specification_templates.md
- modules/16_operational_bounds.md
- wiki/diagnostics/handoff-payload-schema-gap.md
- wiki/methodologies/external-source-to-kf-mapping.md
domain: patterns
topic: classification
---

# Mode-Label-with-Variants Taxonomy

## Pattern

When a single mode label spans multiple distinct output formats — distinguished in practice by trigger phrases or chain position rather than by formal taxonomy — that label is hiding 2+ modes. **Treat them as variants of a base mode, not as a single mode.** Formalize each variant with its own trigger_phrases, output_format, output_template, typical_chain_position, decision_type_typical, and risk_tier.

The diagnostic signal is simple: if you can't write a single output template that captures all "expected" outputs for the label, you have variants.

---

## Why It Matters

A mode label without variants conflates routing accuracy. Aggregate "Critic accuracy" or "Expert accuracy" is meaningless when the same label spans:

- `Critic`: regular review, knowledge-base linter, infrastructure audit, adversarial chain auto-verify
- `Expert`: regular domain analysis, infrastructure architecture, ML infrastructure (GPU/serving), entity relationship analysis

A re-routing event from `critic.regular` → `critic.audit` is a routing failure that's invisible at the mode-label level. Variant-aware metrics surface it.

---

## When to Apply

Apply this taxonomy when:

1. A mode label has 2+ trigger phrase clusters that produce different output templates.
2. Aggregate accuracy metrics for the label are flat or improving while user-facing routing complaints persist.
3. A new domain is being added that "fits inside" an existing mode but produces a structurally different output (e.g., adding ERA inside Expert).

Do **not** apply when:

- Variation is purely stylistic (same output template, different prose tone).
- The "variant" is actually a subroutine of one mode (e.g., compound-failure check inside Expert.regular is a step, not a variant).

---

## Mechanics

```yaml
variants:
  - id: [variant_id]              # snake_case, unique within mode
    purpose: [one-sentence what this variant does that base does not]
    trigger_phrases: [list]
    output_format: [identifier referenced in payload_schema of any handoff]
    output_template: [Module 04 template name]
    typical_chain_position: [position string]
    decision_type_typical: [reckoning | evaluative_judgment | predictive_judgment | novel_judgment]
    activation_predicate:           # Optional — required for variants without explicit trigger phrases
      type: chain_context | output_type_difference | domain_specificity | user_disambiguation
      rule: [if/then logic]
    risk_tier: LOW | MEDIUM | HIGH
```

Trigger overlap between variants is then resolved by the `trigger_disambiguator` entity (Module 04), not by ad-hoc prose.

---

## Generalization

This pattern transfers beyond KF modes. It applies to any system where:

- A "type" or "kind" field has accumulated subtypes via informal extension.
- Aggregate metrics by type are diverging from actual user experience.
- New extensions are difficult to add without breaking existing consumers.

Examples in adjacent domains:

- [project] event taxonomy (`nw.*` events with informal sub-types).
- Cross-portfolio: any handler-by-string-key pattern where the strings are accumulating qualifiers.

---

## Reversibility

The variant taxonomy is descriptive, not constraining. Existing prose conventions remain valid; the formal `variants[]` field adds a layer that downstream modules (orchestrator, metric #10, trigger_disambiguator) can consume. Reverting the taxonomy means deleting the `variants[]` field — no behavioral change for modes that don't read it.
