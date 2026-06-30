---
title: Handoff Payload Schema Gap (ERA Diagnostic Category)
source_mode: expert_era
source_session: redacted
created: '2026-05-10T00:00:00Z'
date: '2026-05-10'
confidence: 0.8
grounding_score: 0.8
grounding_source: 'Stage 2 ERA finding F2 (chain-log-01-tool-calling §F2). 8 active
  mode-to-mode

  handoff edges audited; 0 had formal payload_schema, 0 had formal fallback_path,

  0 had formal validation_checks. All eight surfaced the same gap class.

  Resolution patches (Module 04 Handoff_Contract entity, Module 03 registry)

  closed the gap without breaking changes.

  '
source_fingerprint: tool-calling-audit-track-c-era-f2
novelty_type: reusable_diagnostic
staleness_risk: low
importance: 3
pinned: false
accreted_in: 7.2.0
related:
- modules/04_specification_templates.md
- modules/03_coordination_patterns.md
- wiki/patterns/mode-variants-taxonomy.md
- wiki/methodologies/external-source-to-kf-mapping.md
domain: diagnostics
topic: data-integrity
---

# Handoff Payload Schema Gap (ERA Diagnostic Category)

## Diagnostic

When auditing a multi-mode chain, check every mode → mode edge against this checklist:

1. **Payload schema** — Is the source mode's output structure formally specified, with required fields and types?
2. **Fallback path** — If validation fails, what happens? (escalate / retry / abort / route_to_navigator)
3. **Deterministic validation_checks** — Is there at least one boundary check that doesn't require LLM judgment?

If any of the three is missing, mark the edge as a **handoff payload schema gap**.

---

## Why It Matters

Schema gaps don't fail loudly. They degrade silently into one of:

- "Critic finds vague locations" (because Builder spec didn't enforce location specificity).
- "Builder misinterprets feedback" (because Critic findings format wasn't enforced).
- "Auto-verify gate skipped" (because Expert output omitted `decision_type_exercised` and gate defaulted to safe-but-uninformative).

The cost is paid in re-work and silent quality drift. Fast-fail at the boundary surfaces the gap immediately and forces upstream fix.

---

## Resolution Pattern

Three commits, in order:

1. **Entity definition** — Define `Handoff_Contract` (or equivalent) at the spec template level. Required fields: source/target identifiers, payload_schema, fallback_path, validation_checks (≥1 deterministic).
2. **Per-edge registration** — For each active handoff in the system, register a `handoff_contract_instance` with concrete payload_schema, fallback_path, and validation_checks.
3. **Assertion canonical-form constraint** — Constrain validation_checks[].assertion to a small enum of canonical forms (field-presence, enum-membership, cardinality, schema-conformance, cross-field). Prevents prose assertions from silently degrading fast-fail.

Each commit is reversible independently. The entity definition can ship without instances; instances can be added one edge at a time.

---

## Detection Signals

You're likely to find this gap when:

- A chain "works most of the time" but fails in ways that are hard to attribute to a specific mode.
- "Re-work" rate is high after specific handoffs (Builder revising after Critic, etc.).
- New modes added recently consume outputs from existing modes via informal conventions.
- Auto-verify or quality gates fire inconsistently for "the same kind of input."

---

## Generalization

The gap class generalizes beyond KF:

- **VisionForge L01–L13 module boundaries** — same structural concern (boundary contracts between specification layers).
- **COS Decision Ensemble cross-provider handoffs** — analogous boundary contract (Anthropic persona → OpenAI judge → Google blindspot).
- **Any multi-stage pipeline** where stages produce structured outputs consumed by other stages.

---

## ERA Workflow Application

When running ERA on a multi-mode chain:

1. Enumerate all source → target edges in the active mode set.
2. For each edge, list the documented payload structure.
3. Tag each edge with one of: `formal_schema`, `prose_convention`, `implicit`.
4. Edges tagged `prose_convention` or `implicit` are handoff payload schema gaps.
5. Surface count + total as a single ERA finding (not per-edge findings — they share root cause).

This compresses what could be 8 separate Sev 2 findings into 1 with a clear remediation pattern.
