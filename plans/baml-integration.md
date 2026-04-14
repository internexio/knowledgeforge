# BAML → KnowledgeForge Integration Plan

**Source:** BoundaryML/baml v0.220.0 | Rust compiler, multi-language clients
**Research date:** 2026-04-13 | **Plan version:** 1.0

---

## Strategic Value

BAML demonstrates that structured output reliability is a parsing problem, not a model problem. Schema-Aligned Parsing (SAP) achieves a 34-point accuracy improvement on Claude Haiku without changing the model or the prompt — purely through post-generation parsing strategy. This challenges KF's implicit assumption that output quality is primarily a function of prompt engineering.

The core insight for KF: when a mode produces structured output, the parsing/validation layer matters as much as the generation layer.

---

## Module Updates

### 1. Module 12 (Calibration Layer) — SAP-Inspired Structured Output Validation

**What changes:** Add a multi-strategy parsing cascade to the Calibration Layer for any KF mode that produces structured outputs (Builder specs, Critic gap lists, Strategist trade-off matrices).

**Why it works:** BAML's SAP cascade (strict JSON → markdown fence extraction → multi-JSON grep → fault-tolerant fix → raw string fallback) with scoring demonstrates that collecting *all* parse candidates and scoring them against the expected schema dramatically outperforms single-strategy parsing. The scoring system (lower = better: `ExtraKey` +1, `StrippedNonAlphaNumeric` +3, `DefaultFromNoValue` +100) provides a principled way to choose among ambiguous parses.

**Spec delta:**
```yaml
# Add to Calibration Layer → Output Validation
structured_output_cascade:
  trigger: Any mode producing YAML/JSON structured output
  strategy_order:
    1_strict: Direct parse (YAML/JSON) — accept if clean
    2_fence_extract: Find ```yaml/```json fences, try all closing positions
    3_multi_object: Scan for multiple structured objects in prose (handles CoT preamble)
    4_fault_tolerant: Character-level fixes (trailing commas, unquoted strings, unterminated collections)
    5_raw_fallback: Treat entire output as string, attempt schema coercion

  scoring:
    principle: "Lower score = closer to declared schema"
    penalties:
      extra_field: +1
      stripped_characters: +3
      single_to_array_coercion: +1
      default_from_no_value: +100  # fabricated field — flag to caller
    selection: Lowest-scoring candidate wins

  critical_flag:
    when: Winning candidate has any field with default_from_no_value penalty
    action: Surface to caller — this field was fabricated, not extracted
    kf_implication: >
      Grounding score for fabricated fields = 0.1 (pure LLM output).
      Do not propagate fabricated fields into downstream mode inputs
      without explicit caveat.
```

**Integration with Module 15 (Grounding Scores):** Fields parsed at cascade level 1-2 get grounding 0.8 (computed from grounded data). Level 3-4 get 0.6 (inference with partial verification). Level 5 gets 0.4. Fabricated fields (`DefaultFromNoValue`) get 0.1.

**Priority:** T2 — Adapt. Estimated effort: 4 hours (spec + prototype). Full BAML integration (compile step) deferred pending Claude Code workflow evaluation.

---

### 2. Module 02 (Builder) — `@alias` Debiasing for Enum/Option Fields

**What changes:** When Builder produces specifications with enumerated options (e.g., mode selection, severity levels, decision types), consider aliasing loaded terms to opaque symbols in prompts to reduce semantic anchoring.

**Why it works:** BAML's `@alias` renames schema fields to opaque symbols (`Refund` → `k1`, `CancelOrder` → `k2`) in prompts, backed by research (arxiv 2305.08298) showing this reduces LLM bias toward semantically-loaded terms. KF's decision classification uses terms like "reckoning" and "novel judgment" which carry strong semantic weight that could bias classification.

**Spec delta:**
```yaml
# Add to Builder → Prompt Engineering Practices
debiasing_aliases:
  trigger: >
    When a prompt presents enumerated options where the option names
    carry semantic weight that could bias selection
  technique:
    - Replace loaded terms with opaque aliases in the prompt
    - Map aliases back to original terms in post-processing
    - Preserve descriptions alongside aliases for clarity
  example:
    before: "Classify as: reckoning, evaluative, predictive, novel"
    after: "Classify as: k1, k2, k3, k4"
    mapping_provided_separately: true
  applicability:
    high_value: Decision classification, severity assessment, mode routing
    low_value: Free-form generation, creative output, reckoning answers
  caveat: >
    Only apply when measurement shows bias. Don't alias everything —
    semantic terms aid human readability of outputs.
```

**Priority:** T3 — Reference. Worth testing empirically against KF's decision classification; not immediately actionable without measurement.

---

### 3. Module 07 (Critic) — Union Disambiguation with Scoring

**What changes:** When Critic encounters ambiguous findings that could be classified under multiple severity levels or finding types, apply BAML-style scoring rather than forced single classification.

**Why it works:** BAML's `Value::AnyOf(candidates, original_string)` pattern — collect all valid interpretations, score each against the schema, surface the best — is directly applicable to Critic's severity classification when a finding sits at a boundary (e.g., is this Sev 1 or Sev 2?).

**Spec delta:**
```yaml
# Add to Critic → Severity Classification
boundary_scoring:
  trigger: Finding's characteristics match multiple severity levels
  protocol:
    - Score finding against each candidate severity level
    - Report winning severity with margin to next candidate
    - If margin < 0.2: report as "Sev X (borderline Y)" with rationale for X over Y
  benefit: >
    Makes Critic's reasoning transparent at severity boundaries.
    Reduces false confidence on edge cases.
```

**Priority:** T2 — Adapt. Estimated effort: 2 hours (spec change + Critic prompt update).

---

### 4. Module 16 (Operational Bounds) — Declarative Resilience Patterns

**What changes:** Document BAML's retry/fallback/round-robin resilience patterns as reference architecture for any KF mode that makes external calls.

**Why it works:** BAML declares retry policies, fallback chains, and round-robin rotation in the schema file next to the function definition. KF's circuit breakers are reactive (detect failure after the fact). Adding declarative resilience would be proactive (specify retry/fallback behavior before the call).

**Spec delta:**
```yaml
# Add to Operational Bounds → Resilience Patterns (reference)
declarative_resilience:
  retry:
    pattern: exponential_backoff
    params: [max_retries, delay_ms, multiplier, max_delay_ms]
    kf_usage: Any mode making external tool calls (web_search, file ops)
  fallback:
    pattern: ordered_provider_list
    kf_usage: Model selection (primary → fallback), tool selection (primary → alternative)
  round_robin:
    pattern: rotate_across_equivalent_providers
    kf_usage: Load distribution across equivalent tools or model endpoints
  note: >
    Reference pattern. Not immediately implementable in Claude Code
    without hook-level retry logic. Document for future autonomous deployment.
```

**Priority:** T3 — Reference. Document now, implement when KF moves to autonomous deployment.

---

## Patterns Noted but Not Adopted

| Pattern | Reason for deferral |
|---------|-------------------|
| Typed streaming with `@stream.done` field annotations | KF treats responses as complete artifacts. Relevant only for progressive disclosure in future real-time UI |
| Inline test blocks in schema files | Good DX pattern but KF's test infrastructure is behavioral evals, not schema unit tests |
| `completion_state` on every parsed value | Token-level partial JSON tracking. Relevant only for streaming structured outputs |
| 80% fewer tokens than JSON Schema | KF uses YAML, which is already compact. Marginal benefit |
| DSL compilation step (.baml → client code) | Adds build complexity to Claude Code workflow. Evaluate if SAP benefits justify the toolchain cost |

---

## Key Risk

**SAP can be wrong silently.** The `DefaultFromNoValue` penalty (score=100) fabricates missing fields without surfacing to the caller unless metadata is read. If KF adopts SAP-inspired parsing, the fabrication flag MUST propagate to Grounding Scores. A fabricated field with 0.8 grounding would be a dangerous silent failure.

---

## Implementation Sequence

```
1. Structured output cascade spec (Module 12)   ← spec first, validate concept
2. Grounding score integration for parse levels  ← prevents silent fabrication
3. Boundary scoring for Critic severity (Module 07)  ← quick spec change
4. @alias debiasing research (Module 02)         ← empirical test needed first
5. Declarative resilience documentation (Module 16)  ← reference only
```

---

## Version Target

Module 12 cascade + Module 07 boundary scoring warrant inclusion in **KF 6.7.0**. The `@alias` debiasing is a research item for 6.8+.
