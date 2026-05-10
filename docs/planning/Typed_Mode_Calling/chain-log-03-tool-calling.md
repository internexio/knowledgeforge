# Chain-Log 03 — Builder Phase

## Cascade Metadata

```yaml
cascade:
  stage: 2
  phase: Builder
  prior_phase: Strategist (chain-log-02-tool-calling.md)
  produces_for: chain-log-04-tool-calling.md (Critic phase) + Stage 3 Claude Code handoff
  cascade_id: tool-calling-architecture-audit
  track: C
  target_version: KF 7.1.0
  decision_type: evaluative_judgment
  date: 2026-05-08

builder_pre_authorship_verification:
  - Verified Module 04 v6.6.0 — no existing Handoff_Contract entity; "Handoff" appears in Usage Notes table only
  - Verified Module 05 — no existing variants[] field on Expert; no decision_type_exercised in output schema
  - Verified Module 07 — no existing variants[] field on Critic
  - Verified Module 16 v7.0.0 — metrics 1–9 present; no metric #10
  - Verified Module 19 — routing_index_schema v1.0 present; no routing_decision_log
  - All patches additive; no schema conflicts
```

## 1. Spec Patches

### Patch P1 (U1) — Module 04: trigger_disambiguator entity

**Location:** Module 04, new section after "Handoff Specification Template".

```yaml
# ─────────────────────────────────────────────────────────────────────
# Trigger Disambiguator Specification Template (NEW 7.1.0)
# ─────────────────────────────────────────────────────────────────────

trigger_disambiguator:
  # IDENTITY
  id: [unique-identifier]                  # e.g., "td-critic-variants"
  name: [human-readable name]
  version: [semantic version]

  # PURPOSE
  purpose: |
    Resolve cases where a trigger phrase activates multiple candidate modes or
    variants. Formalizes the variant-resolution and cross-mode-overlap predicates
    that previously lived as prose conventions.

  # SCOPE
  scope:
    trigger_phrase: [string]              # The ambiguous phrase
    candidate_modes:                       # Modes/variants that match this phrase
      - mode_id: [string]
        variant_id: [string | null]       # null if mode has no variants
        match_strength: [exact | partial | contextual]

  # PREDICATE
  predicate:
    type: output_type_difference | domain_specificity | chain_context | user_disambiguation
    rule: [string — explicit if/then logic]
    fallback: user_disambiguation         # If primary predicate inconclusive

  # PREDICATE TYPE DEFINITIONS
  predicate_type_definitions:
    output_type_difference:
      description: "Top-2 candidates produce different output types (artifact / recommendation / analysis / route)"
      action: "Activate Navigator (per orchestrator output-type predicate)"
      precedent: "Module 01 Navigator activation predicate (6.6.1)"

    domain_specificity:
      description: "Trigger phrase scoped by domain context — most domain-specific candidate wins"
      action: "Route to most-specific candidate"
      example: "'review API security' → Expert (security domain) not Critic (regular review)"

    chain_context:
      description: "Active chain pattern implies variant"
      action: "Route per chain pattern in Module 03"
      example: "Critic in auto-verify chain → adversarial variant"

    user_disambiguation:
      description: "No automatic resolution available"
      action: "Activate Navigator with one targeted question"
      precedent: "Module 01 ambiguity handling"

  # DESIGN DECISIONS
  design_decisions:
    - decision: "Predicate types are an enum, not a free-text field"
      decision_type: evaluative_judgment
      locked: true
      rationale: "Enum constrains future additions; new predicate types require explicit Module 04 update."

    - decision: "Fallback always defaults to user_disambiguation"
      decision_type: reckoning
      locked: true
      rationale: "Asking the user is always safe; never silent-fail to wrong route."

  # CAPABILITIES WHEN SUB-AGENT (per Module 20)
  capabilities_when_subagent:
    read: [trigger_phrase, candidate_modes, current_chain_context]
    write: [predicate result only]
    create: nothing
    modify: nothing
    escalate: when fallback fires
    restriction: "Read-only logic; emits routing decision, no side effects"

  # RISK TIER
  risk_tier:
    base_tier: LOW
    chain_escalation: false
    verification_required: false
```

**Test Criteria:**

```yaml
test_criteria_p1:
  deterministic_checks:
    - check_id: tdb_schema_validates
      assertion: "trigger_disambiguator instances validate against entity schema (jsonschema)"
      file_path: tests/spec/test_module_04_trigger_disambiguator.py
      assertion_summary: "Schema validation on all td-* entities in Module 04"

    - check_id: tdb_predicate_enum_complete
      assertion: "predicate.type is one of [output_type_difference, domain_specificity, chain_context, user_disambiguation]"
      file_path: tests/spec/test_module_04_trigger_disambiguator.py

    - check_id: tdb_no_variant_without_definition
      assertion: "Every variant_id in candidate_modes appears in target mode's variants[] field"
      file_path: tests/spec/test_module_04_cross_module_consistency.py

  existing_tests_must_pass:
    - tests/spec/test_module_04_template_validity.py (all existing template schemas)

  new_tests_required:
    - tests/spec/test_module_04_trigger_disambiguator.py
    - tests/spec/test_module_04_cross_module_consistency.py
```

**Migration:** Pure addition. Backward compatible. No deprecations.

---

### Patch P2 (U2) — Module 04: Handoff_Contract entity

**Location:** Module 04, new section replacing/extending the "Handoff Specification Template" section. Usage Notes table row "Handoff" renamed to "Handoff Contract".

```yaml
# ─────────────────────────────────────────────────────────────────────
# Handoff Contract Specification Template (NEW 7.1.0)
# ─────────────────────────────────────────────────────────────────────
# Replaces informal "Handoff" usage. Formalizes mode-to-mode contract
# with required validation_checks for fast-fail at handoff boundary.
# ─────────────────────────────────────────────────────────────────────

handoff_contract:
  # IDENTITY
  id: [unique-identifier]                  # e.g., "hc-builder-to-critic-autoverify"
  name: [human-readable name]
  version: [semantic version]

  # CONTRACT PARTIES
  source_mode: [string]                    # e.g., "builder"
  source_variant: [string | null]          # required if source mode has variants[]
  target_mode: [string]                    # e.g., "critic"
  target_variant: [string | null]          # required if target mode has variants[]

  # CONTRACT TRIGGER
  trigger:
    type: automatic | chain_pattern | user_initiated
    condition: [string]                    # Plain-language activation rule
    chain_pattern_reference: [string]      # Module 03 chain pattern ID, if applicable

  # PAYLOAD SCHEMA
  payload_schema:
    fields:
      - name: [field_name]
        type: string | number | boolean | object | array
        required: true | false
        description: [string]
        validation: [optional rule, e.g., enum, pattern, min/max]
        grounding_score_minimum: [0.0–1.0]   # Optional, per Module 15

  # FALLBACK PATH
  fallback_path:
    type: escalate_to_user | retry_with_repair | abort_chain | route_to_navigator
    rationale: [string]
    user_message_template: [string]        # If type = escalate_to_user

  # VALIDATION CHECKS
  validation_checks:
    - check_id: [unique within contract]
      assertion: [string — what must be true]
      check_type: deterministic | llm_judgment   # ≥1 deterministic per contract REQUIRED
      failure_action: [references fallback_path type]
      failure_severity: Sev1 | Sev2 | Sev3

  # DESIGN DECISIONS
  design_decisions:
    - decision: "≥1 deterministic check required per contract"
      decision_type: reckoning
      locked: true
      rationale: "KF 7.0.0 'Deterministic first' meta-principle. Schema validation, field existence, type checks are deterministic."

    - decision: "fallback_path is mandatory, not optional"
      decision_type: evaluative_judgment
      locked: true
      rationale: "F2 root cause was silent degradation. Mandatory fallback path forces explicit handling."

  # CAPABILITIES WHEN SUB-AGENT
  capabilities_when_subagent:
    read: [payload from source_mode]
    write: [validation result + fallback trigger if needed]
    create: nothing
    modify: nothing
    escalate: per fallback_path
    restriction: "Pure validation; no payload mutation"

  # RISK TIER
  risk_tier:
    base_tier: LOW
    chain_escalation: false
    verification_required: false
```

**Module 04 Usage Notes table row update:**

```diff
- | Handoff | Designing transfer points between agents | Coordinator |
+ | Handoff Contract | Defining transfer points between modes/agents in chains, with payload schema and validation | Coordinator/Builder |
```

**Test Criteria:**

```yaml
test_criteria_p2:
  deterministic_checks:
    - check_id: hc_schema_validates
      assertion: "All handoff_contract instances validate against entity schema"
      file_path: tests/spec/test_module_04_handoff_contract.py

    - check_id: hc_at_least_one_deterministic_check
      assertion: "Each handoff_contract has ≥1 validation_checks entry with check_type: deterministic"
      file_path: tests/spec/test_module_04_handoff_contract.py

    - check_id: hc_fallback_path_required
      assertion: "Every handoff_contract has non-null fallback_path.type"
      file_path: tests/spec/test_module_04_handoff_contract.py

    - check_id: hc_variant_required_when_mode_has_variants
      assertion: "If source_mode or target_mode has variants[] field, source_variant or target_variant is non-null"
      file_path: tests/spec/test_module_04_cross_module_consistency.py

  existing_tests_must_pass:
    - tests/spec/test_module_04_template_validity.py

  new_tests_required:
    - tests/spec/test_module_04_handoff_contract.py
```

**Migration:** Renaming "Handoff" → "Handoff Contract" in Usage Notes is documentation-only. Existing prose references to "handoff" remain valid. No code change required.

---

### Patch P3 (U3) — Module 07: Critic variants[]

**Location:** Module 07 (Critic Agent), new section after agent identity, before existing trigger phrases section.

```yaml
# ─────────────────────────────────────────────────────────────────────
# Critic Variants (NEW 7.1.0)
# ─────────────────────────────────────────────────────────────────────
# Formalizes the 4 variants that previously shared the "Critic" mode label,
# distinguished only by trigger phrase. Resolves ERA F1.
# ─────────────────────────────────────────────────────────────────────

variants:
  - id: regular
    purpose: Review specifications, designs, or analyses for completeness, consistency, assumptions, edge cases
    trigger_phrases: [review, check, validate, find gaps, identify what's missing]
    output_format: findings_list
    output_template: Critique (Module 04)
    typical_chain_position: terminal | auto-verify
    decision_type_typical: evaluative_judgment
    risk_tier: MEDIUM

  - id: linter
    purpose: Health check the knowledge base for staleness, contradictions, redundancy, grounding decay, orphan references
    trigger_phrases: [health check, lint, validate the knowledge base]
    output_format: maintenance_backlog
    output_template: Critique (Module 04) extended with maintenance_priority field
    typical_chain_position: standalone
    decision_type_typical: evaluative_judgment
    risk_tier: MEDIUM

  - id: audit
    purpose: Inventory infrastructure state, analyze single points of failure, rate decomposition readiness
    trigger_phrases: [hosting audit, infrastructure inventory, decomposition readiness, single-point-of-failure analysis]
    output_format: hosting_audit_template_populated
    output_template: Hosting Audit (Module 04)
    typical_chain_position: chain_initial
    decision_type_typical: evaluative_judgment
    risk_tier: MEDIUM

  - id: adversarial
    purpose: Find the failure mode the producing agent missed; assume output has at least one significant flaw
    trigger_phrases: ["[automatic — fires on chain producing evaluative+ output]"]
    activation_predicate:
      type: chain_context
      rule: "Active chain pattern includes adversarial verification step (per Module 00 auto-verify gate)"
    output_format: severity_classified_findings
    output_template: Critique (Module 04) with framing override
    typical_chain_position: post_builder | post_strategist | post_expert (when decision_type_exercised >= evaluative)
    decision_type_typical: evaluative_judgment
    risk_tier: MEDIUM

# Existing Module 07 prose remains valid; variants[] adds formal taxonomy on top.
```

**Test Criteria:**

```yaml
test_criteria_p3:
  deterministic_checks:
    - check_id: critic_variants_count
      assertion: "Module 07 critic.variants[] has exactly 4 entries: regular, linter, audit, adversarial"
      file_path: tests/spec/test_module_07_variants.py

    - check_id: critic_variants_unique_ids
      assertion: "All variant.id values unique"
      file_path: tests/spec/test_module_07_variants.py

    - check_id: critic_variants_trigger_phrases_non_empty
      assertion: "Every variant has non-empty trigger_phrases array"
      file_path: tests/spec/test_module_07_variants.py

    - check_id: critic_variant_in_disambiguator
      assertion: "Trigger phrases that overlap across variants are registered in trigger_disambiguator entity (Module 04)"
      file_path: tests/spec/test_module_04_cross_module_consistency.py

  existing_tests_must_pass:
    - tests/spec/test_module_07_critic_agent.py (Module 07 existing schema)

  new_tests_required:
    - tests/spec/test_module_07_variants.py
```

**Migration:** Backward compatible. Module 07 existing prose continues to apply. Existing references to "Critic" remain valid; variants[] disambiguates where prose was ambiguous.

---

### Patch P4 (U4) — Module 05: Expert variants[] + decision_type_exercised

**Location:** Module 05 (Expert Agent), two extensions:
- New variants[] section
- New required field on outputs[] schema

```yaml
# ─────────────────────────────────────────────────────────────────────
# Expert Variants (NEW 7.1.0)
# ─────────────────────────────────────────────────────────────────────

variants:
  - id: regular
    purpose: Domain-specific deep analysis with adversarial depth (compound failures, blast radius, assumption inversions, design implications)
    trigger_phrases: [domain-specific question requiring deep analysis, expert review, deep dive]
    output_format: analysis_with_adversarial_depth
    output_template: agent output (Module 04)
    typical_chain_position: chain_initial | standalone
    decision_type_typical: evaluative_judgment | predictive_judgment
    risk_tier: MEDIUM

  - id: infrastructure
    purpose: Infrastructure architecture domain — service topology, deployment phases, hardware bottlenecks
    trigger_phrases: [design infrastructure, plan service topology, map deployment phases, architect internal networking]
    output_format: infrastructure_architecture_inputs
    output_template: Infrastructure Architecture (Module 04) inputs
    typical_chain_position: pre_builder (Expert → Builder)
    decision_type_typical: evaluative_judgment
    risk_tier: MEDIUM

  - id: ml_infrastructure
    purpose: Self-hosted model deployment, GPU sizing, inference serving strategy, model-to-hardware mapping
    trigger_phrases: [self-hosted model deployment, GPU sizing, inference serving, model-to-hardware mapping]
    output_format: model_hardware_analysis
    output_template: agent output (Module 04)
    typical_chain_position: pre_strategist (Expert → Strategist → Builder)
    decision_type_typical: evaluative_judgment
    risk_tier: MEDIUM

  - id: era
    purpose: Entity Relationship Analysis — entity graph, cardinality, coupling analysis, hidden contracts
    trigger_phrases: [map entity relationships, analyze data model structure, audit module dependencies, model coordination contracts, map what entities a system produces and consumes]
    output_format: era_analysis_inputs
    output_template: ERA Specification (Module 04) inputs
    typical_chain_position: pre_builder (Expert ERA → Builder)
    decision_type_typical: evaluative_judgment
    risk_tier: MEDIUM
```

```yaml
# ─────────────────────────────────────────────────────────────────────
# Expert output schema extension (NEW 7.1.0)
# ─────────────────────────────────────────────────────────────────────

# Patch to existing outputs[] section:
outputs:
  - name: analysis
    type: response | artifact
    format: markdown
    structure:
      first_order_findings: array
      adversarial_depth: object
      design_implications: array
      decision_type_exercised:                  # NEW 7.1.0 — required field
        type: string
        enum: [reckoning, evaluative_judgment, predictive_judgment, novel_judgment]
        required: true
        purpose: |
          Gate signal for orchestrator auto-verification. Expert outputs at
          evaluative_judgment or higher trigger Critic adversarial pass per
          Module 00 auto-verify gate (formalized from 6.6.1 changelog reference).
        backward_compat:
          rule: |
            Existing Expert outputs without this field default to
            evaluative_judgment (conservative — triggers auto-verify).
          deprecation_timeline: KF 7.2.0 — field becomes hard-required, no default
```

**Test Criteria:**

```yaml
test_criteria_p4:
  deterministic_checks:
    - check_id: expert_variants_count
      assertion: "Module 05 expert.variants[] has exactly 4 entries: regular, infrastructure, ml_infrastructure, era"
      file_path: tests/spec/test_module_05_variants.py

    - check_id: expert_decision_type_exercised_in_output
      assertion: "Module 05 expert.outputs[].structure includes decision_type_exercised as required field with enum constraint"
      file_path: tests/spec/test_module_05_output_schema.py

    - check_id: expert_decision_type_enum_matches_module_13
      assertion: "decision_type_exercised enum values match Module 13 decision_type values"
      file_path: tests/spec/test_module_05_cross_module_consistency.py

    - check_id: expert_output_consumed_by_autoverify
      assertion: "Module 00 auto-verify gate references decision_type_exercised explicitly (not via default)"
      file_path: tests/spec/test_module_00_orchestrator_consistency.py

  existing_tests_must_pass:
    - tests/spec/test_module_05_expert_agent.py (existing schema)

  new_tests_required:
    - tests/spec/test_module_05_variants.py
    - tests/spec/test_module_05_output_schema.py
```

**Migration:**
- Variants[] addition is pure addition; backward compatible.
- decision_type_exercised: backward-compat rule defaults to evaluative_judgment if missing. **Behavior change:** existing Expert outputs without the field will now reliably trigger auto-verify (conservative). Hard requirement deferred to KF 7.2.0 for one minor cycle of grace period.

---

### Patch P5 (U5) — Module 19: routing_decision_log hook

**Location:** Module 19 (Memory Architecture), new section after "Tier 1: Routing Index".

```yaml
# ─────────────────────────────────────────────────────────────────────
# Routing Decision Log (NEW 7.1.0)
# ─────────────────────────────────────────────────────────────────────
# Audit trail of routing decisions, separate from routing_index (state).
# Data source for Module 16 metric #10 (mode_selection_accuracy).
# ─────────────────────────────────────────────────────────────────────

routing_decision_log:
  schema_version: "1.0"

  trigger: "On every mode activation by orchestrator (including variant selection)"

  log_entry:
    fields:
      - name: timestamp
        type: ISO8601
        required: true

      - name: turn_number
        type: integer
        required: true

      - name: request_text
        type: string
        required: true
        max_length: 200                    # Truncate; operational data, not user data

      - name: candidate_modes
        type: array<{mode_id: string, variant_id: string | null, confidence: float}>
        required: true
        min_length: 1

      - name: selected_mode
        type: string
        required: true

      - name: selected_variant
        type: string | null
        required: true                     # null if mode has no variants

      - name: trigger_phrase_matched
        type: string
        required: true

      - name: predicate_used
        type: string | null                # references trigger_disambiguator.predicate.type
        required: false

      - name: re_routed
        type: boolean
        required: true
        default: false

      - name: re_route_reason
        type: string | null
        required: false                    # required when re_routed = true
        validation:
          rule: "If re_routed is true, re_route_reason must be non-null"

  retention:
    rolling_window:
      size: 1000 entries
      eviction: oldest first

    permanent_archive:
      condition: "re_routed = true"
      destination: "wiki/operations/routing-log/{YYYY-MM}.md"
      rationale: "Re-routing events are training data for trigger_disambiguator refinement"

  aggregation_persistence:                 # ADDED post-Critic Phase 1 revision
    purpose: |
      Beyond the rolling 1000-entry log, persist aggregate metric values for
      historical calibration. Module 16 metric #10 reads aggregates here when
      raw log entries have rolled out of the window.
    location: tier_2_metric_aggregates
    schema:
      window_id: ISO8601 (week start)
      total_routing_events: integer
      re_routed_events: integer
      per_mode_accuracy: object<mode_id, float>
      per_variant_accuracy: object<{mode_id, variant_id}, float>
    retention: permanent (until manual archive)

  privacy:
    request_text:
      retention: 200 chars truncated
      pii_filtering: not applied — operational scope
      access: orchestrator + linter (Critic linter variant) only

  drift_detection:
    schema_version_check:
      rule: |
        When a module reads routing_decision_log entries with schema_version != 1.0,
        flag SCHEMA_DRIFT in Tier 2 state and surface at session end. Continue with
        best-effort field mapping.

  consumed_by:
    - Module 16 metric #10 (mode_selection_accuracy) — primary measurement
    - Critic linter variant — re-routing pattern analysis during health checks
    - Orchestrator — session-end metric calculation
```

**Test Criteria:**

```yaml
test_criteria_p5:
  deterministic_checks:
    - check_id: rdl_schema_validates
      assertion: "routing_decision_log entries validate against schema_version 1.0"
      file_path: tests/spec/test_module_19_routing_decision_log.py

    - check_id: rdl_re_routed_reason_required_when_true
      assertion: "Every entry with re_routed: true has non-null re_route_reason"
      file_path: tests/spec/test_module_19_routing_decision_log.py

    - check_id: rdl_request_text_truncated
      assertion: "request_text is ≤200 characters"
      file_path: tests/spec/test_module_19_routing_decision_log.py

    - check_id: rdl_entry_per_mode_activation
      assertion: "For test session with N mode activations, log contains exactly N entries"
      file_path: tests/integration/test_orchestrator_logging_behavior.py

    - check_id: rdl_aggregation_persistence_present
      assertion: "tier_2_metric_aggregates schema is defined and routing_decision_log references it"
      file_path: tests/spec/test_module_19_routing_decision_log.py

  existing_tests_must_pass:
    - tests/spec/test_module_19_routing_index.py (existing routing_index_schema v1.0)

  new_tests_required:
    - tests/spec/test_module_19_routing_decision_log.py
    - tests/integration/test_orchestrator_logging_behavior.py
```

**Migration:** Pure addition. Coexists with routing_index_schema v1.0 (different concerns: state vs. audit trail). No deprecations.

---

### Patch P6 (U6) — Module 16: metric #10 (mode_selection_accuracy)

**Location:** Module 16, new section after "9. Token Cost Per Mode (6.4)" and before "Corrective Action Summary".

```yaml
# ─────────────────────────────────────────────────────────────────────
# 10. Mode Selection Accuracy (7.1.0)
# ─────────────────────────────────────────────────────────────────────

mode_selection_accuracy:
  measurement:
    primary:
      type: deterministic
      formula: "1 - (re_routed_events / total_routing_events)"
      window: rolling 100 routing events
      data_source: Module 19 routing_decision_log

    calibration:
      type: adversarial_sampling
      frequency: weekly
      sample_size: 20
      method: |
        Critic adversarial variant reviews sampled routing decisions against original
        request. "Wrong mode for this task" or "wrong variant for this task" findings
        at Sev 2+ count as routing failures.

    historical_data_source:
      type: aggregate
      location: Module 19 tier_2_metric_aggregates  # Per P5 aggregation_persistence
      use: "When raw log has rolled past window, calibration uses aggregate"

  tracking:
    per_mode: [navigator, builder, expert, critic, synthesizer, debugger, strategist, calibrator, orchestrator]
    per_variant: [critic.regular, critic.linter, critic.audit, critic.adversarial, expert.regular, expert.infrastructure, expert.ml_infrastructure, expert.era]
    rolling_average_window: 100 routing events
    aggregate_window: weekly (per Module 19 tier_2_metric_aggregates)

  healthy_range:
    overall: ">= 90%"
    per_variant: ">= 95%"
    calibration_drift: "Adversarial sample failure rate within 5pp of (1 - primary)"

  below_90_overall:
    diagnosis: Routing logic misclassifying requests; orchestrator prompt may be drifting
    severity: notification
    corrective_action:
      - Trigger Module 13 (Decision Classification) review
      - Audit recent re_routed events for shared failure pattern
      - Consider trigger_disambiguator schema update (Module 04)

  below_80_overall:
    diagnosis: Severe routing failure
    severity: escalation
    corrective_action:
      - ESCALATE
      - Halt new chain starts until calibration check completes
      - Surface specific re_routed events for human review

  below_95_per_variant:
    diagnosis: Variant disambiguation failing within mode label
    severity: notification
    corrective_action:
      - Audit variant-level trigger phrases for overlap
      - Consider tightening domain_specificity predicate in Module 04 trigger_disambiguator

  below_85_per_variant:
    diagnosis: Variant taxonomy degraded
    severity: escalation
    corrective_action:
      - Trigger Module 04 trigger_disambiguator review
      - Halt chains using affected variant until taxonomy resolved

  calibration_drift:
    rule: "If adversarial-sample failure rate exceeds (1 - primary_measurement) by > 5pp, primary is under-counting"
    severity: notification
    corrective_action:
      - Re-baseline primary measurement
      - Trigger orchestrator prompt revision

  rationale: |
    F1 from Stage 2 ERA — mode-label collisions (Critic 4 variants, Expert 4 variants)
    make aggregate "mode selection" metrics misleading. Variant-level disaggregation
    is mandatory. Re-routing rate is the deterministic proxy; adversarial sampling is
    the calibration check. F4 — routing_decision_log is the data source for primary
    measurement.

  check_frequency:
    primary: every_chain_completion
    calibration: weekly
    aggregation: weekly (writes to tier_2_metric_aggregates)

  data_source:
    primary: Module 19 routing_decision_log (live entries)
    historical: Module 19 tier_2_metric_aggregates (post-window)
```

**Module 16 Corrective Action Summary table additions:**

```diff
+ | Mode selection accuracy < 90% (overall) | Trigger Module 13 review, audit re_routed events, consider trigger_disambiguator update |
+ | Mode selection accuracy < 80% (overall) | ESCALATE, halt new chain starts |
+ | Variant accuracy < 95% (per-variant) | Audit variant trigger phrase overlap, tighten domain_specificity predicate |
+ | Variant accuracy < 85% (per-variant) | Trigger trigger_disambiguator review, halt affected variant |
+ | Calibration drift > 5pp | Re-baseline primary, trigger orchestrator prompt revision |
```

**Test Criteria:**

```yaml
test_criteria_p6:
  deterministic_checks:
    - check_id: msa_metric_schema_validates
      assertion: "Module 16 metric #10 validates against metric definition schema"
      file_path: tests/spec/test_module_16_metric_10.py

    - check_id: msa_thresholds_monotonic
      assertion: "Threshold actions are monotonic: 80 < 90, 85 < 95"
      file_path: tests/spec/test_module_16_metric_10.py

    - check_id: msa_data_source_exists
      assertion: "Referenced Module 19 routing_decision_log and tier_2_metric_aggregates are defined"
      file_path: tests/spec/test_module_16_cross_module_consistency.py

    - check_id: msa_corrective_action_table_extended
      assertion: "Module 16 Corrective Action Summary table contains 5 new rows for metric #10"
      file_path: tests/spec/test_module_16_metric_10.py

  existing_tests_must_pass:
    - tests/spec/test_module_16_metrics.py (metrics 1–9 schemas)

  new_tests_required:
    - tests/spec/test_module_16_metric_10.py
```

**Migration:** Pure addition. Backward compatible.

---

### Patch P7 (U7) — Module 03: handoff contract registry

**Location:** Module 03 (Coordination Patterns), new section "Handoff Contract Registry" listing all 8 active handoff edges.

```yaml
# ─────────────────────────────────────────────────────────────────────
# Handoff Contract Registry (NEW 7.1.0)
# ─────────────────────────────────────────────────────────────────────
# Per-edge registrations using Module 04 handoff_contract entity.
# ─────────────────────────────────────────────────────────────────────

handoff_contract_registry:

  - id: hc-builder-to-critic-autoverify
    source_mode: builder
    source_variant: null
    target_mode: critic
    target_variant: adversarial
    trigger:
      type: automatic
      condition: "Builder produces specification with decision_type evaluative_judgment or higher"
      chain_pattern_reference: "auto-verify"
    payload_schema:
      fields:
        - {name: specification_artifact, type: object, required: true, description: "Full Builder spec output"}
        - {name: design_decisions, type: array, required: true, description: "Each with decision_type tag"}
        - {name: grounding_scores, type: array, required: false, description: "Per Module 15"}
        - {name: accretion_candidate, type: object, required: false, description: "Per Module 21 if applicable"}
    fallback_path:
      type: escalate_to_user
      rationale: "Auto-verify is high-stakes; user awareness preferred over silent abort"
    validation_checks:
      - check_id: payload_schema_conforms
        assertion: "Payload validates against Module 04 Agent Specification schema"
        check_type: deterministic
        failure_action: escalate_to_user
        failure_severity: Sev2
      - check_id: every_decision_typed
        assertion: "Every entry in design_decisions[] has non-null decision_type"
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev2

  - id: hc-expert-to-builder
    source_mode: expert
    source_variant: any  # All Expert variants share this contract
    target_mode: builder
    target_variant: null
    trigger:
      type: chain_pattern
      condition: "Expert → Builder chain pattern active"
      chain_pattern_reference: "expert-to-builder"
    payload_schema:
      fields:
        - {name: first_order_findings, type: array, required: true}
        - {name: adversarial_depth, type: object, required: true}
        - {name: design_implications, type: array, required: true}
        - {name: decision_type_exercised, type: string, required: true, validation: "enum: [reckoning, evaluative_judgment, predictive_judgment, novel_judgment]"}
    fallback_path:
      type: route_to_navigator
      rationale: "Missing required field indicates upstream Expert spec failure; Navigator clarifies with user"
    validation_checks:
      - check_id: decision_type_exercised_present
        assertion: "decision_type_exercised field is non-null and matches enum"
        check_type: deterministic
        failure_action: route_to_navigator
        failure_severity: Sev1
      - check_id: adversarial_depth_present
        assertion: "adversarial_depth object contains at least one of: compound_failures, blast_radius, assumption_inversions, design_implications"
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev2

  - id: hc-strategist-to-builder
    source_mode: strategist
    source_variant: null
    target_mode: builder
    target_variant: null
    trigger:
      type: chain_pattern
      condition: "Strategist → Builder chain pattern active"
      chain_pattern_reference: "strategist-to-builder"
    payload_schema:
      fields:
        - {name: recommendation, type: object, required: true}
        - {name: sequencing, type: array, required: true}
        - {name: reversibility_per_unit, type: array, required: true}
        - {name: trade_off_matrix, type: object, required: true}
    fallback_path:
      type: retry_with_repair
      rationale: "Strategist output missing fields is correctable in single retry"
    validation_checks:
      - check_id: sequencing_dependencies_resolvable
        assertion: "Every sequencing[].dependencies entry references a valid sequencing[].id"
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev2

  - id: hc-synthesizer-to-builder
    source_mode: synthesizer
    source_variant: null
    target_mode: builder
    target_variant: null
    trigger:
      type: chain_pattern
      condition: "Synthesizer → Builder chain pattern active"
      chain_pattern_reference: "synthesizer-to-builder"
    payload_schema:
      fields:
        - {name: pattern, type: object, required: true}
        - {name: anti_patterns, type: array, required: true, validation: "min_length: 1"}
        - {name: applicability_boundaries, type: object, required: true}
    fallback_path:
      type: retry_with_repair
    validation_checks:
      - check_id: at_least_one_anti_pattern
        assertion: "anti_patterns array length >= 1 (per Synthesizer spec)"
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev1

  - id: hc-critic-to-builder-revision
    source_mode: critic
    source_variant: any  # adversarial OR regular
    target_mode: builder
    target_variant: null
    trigger:
      type: chain_pattern
      condition: "Critic finds Sev 2+ in Builder output; loop_exit_protocol max=1"
      chain_pattern_reference: "critic-builder-revision"
    payload_schema:
      fields:
        - {name: findings_list, type: array, required: true}
        - {name: severity_per_finding, type: array, required: true}
        - {name: location_per_finding, type: array, required: true, description: "specific location reference"}
        - {name: proposed_fix_per_finding, type: array, required: true}
        - {name: revision_cycle_count, type: integer, required: true, validation: "max: 1"}
    fallback_path:
      type: escalate_to_user
      rationale: "Per loop_exit_protocol — if revision_cycle_count > 1, escalate with options"
    validation_checks:
      - check_id: revision_cycle_within_limit
        assertion: "revision_cycle_count <= 1"
        check_type: deterministic
        failure_action: escalate_to_user
        failure_severity: Sev1
      - check_id: findings_have_locations
        assertion: "Every finding has non-empty location reference"
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev2

  - id: hc-debugger-to-strategist
    source_mode: debugger
    source_variant: null
    target_mode: strategist
    target_variant: null
    trigger:
      type: chain_pattern
      condition: "Debugger → Strategist chain pattern active"
      chain_pattern_reference: "debugger-to-strategist"
    payload_schema:
      fields:
        - {name: root_cause, type: object, required: true}
        - {name: confidence, type: float, required: true, validation: "range: [0.0, 1.0], minimum: 0.8"}
        - {name: diagnostic_path, type: array, required: true}
    fallback_path:
      type: retry_with_repair
    validation_checks:
      - check_id: root_cause_confidence_threshold
        assertion: "confidence >= 0.8 (per Debugger spec)"
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev2

  - id: hc-critic-audit-to-strategist
    source_mode: critic
    source_variant: audit
    target_mode: strategist
    target_variant: null
    trigger:
      type: chain_pattern
      condition: "Critic audit → Strategist chain pattern (infrastructure cascade)"
      chain_pattern_reference: "audit-to-extraction-priority"
    payload_schema:
      fields:
        - {name: hosting_inventory, type: object, required: true}
        - {name: spof_analysis, type: array, required: true}
        - {name: decomposition_readiness_per_service, type: array, required: true}
    fallback_path:
      type: retry_with_repair
    validation_checks:
      - check_id: readiness_classifications_valid
        assertion: "decomposition_readiness_per_service[].readiness in [ready, needs_work, tightly_coupled, unknown]"
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev2

  - id: hc-strategist-to-calibrator
    source_mode: strategist
    source_variant: null
    target_mode: calibrator
    target_variant: null
    trigger:
      type: chain_pattern
      condition: "Strategist → Calibrator chain pattern (decide-stack-then-setup)"
      chain_pattern_reference: "stack-decision-to-config"
    payload_schema:
      fields:
        - {name: stack_decision, type: object, required: true}
        - {name: complexity_assessment, type: object, required: true}
        - {name: compliance_requirements, type: array, required: false}
    fallback_path:
      type: retry_with_repair
    validation_checks:
      - check_id: stack_decision_complete
        assertion: "stack_decision contains language, framework, deployment_target fields"
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev2
```

**Test Criteria:**

```yaml
test_criteria_p7:
  deterministic_checks:
    - check_id: registry_count
      assertion: "handoff_contract_registry has exactly 8 entries"
      file_path: tests/spec/test_module_03_handoff_registry.py

    - check_id: registry_unique_ids
      assertion: "All registry entry ids are unique"
      file_path: tests/spec/test_module_03_handoff_registry.py

    - check_id: every_registry_entry_validates
      assertion: "Every registry entry validates against Module 04 handoff_contract entity schema"
      file_path: tests/spec/test_module_03_handoff_registry.py

    - check_id: registry_covers_all_active_handoffs
      assertion: "Every Mode → Mode chain pattern in Module 03 has corresponding handoff_contract_registry entry"
      file_path: tests/spec/test_module_03_handoff_completeness.py

  existing_tests_must_pass:
    - tests/spec/test_module_03_coordination_patterns.py

  new_tests_required:
    - tests/spec/test_module_03_handoff_registry.py
    - tests/spec/test_module_03_handoff_completeness.py
```

**Migration:** Pure addition. Module 03 prose remains valid. Existing chain pattern references continue to work; registry adds formal validation layer.

---

### Patch P8 (U8) — Module 00: orchestrator log-writing behavior (impl_commit)

**Location:** Module 00 Static Zone, "Routing Index Integration" section, after the existing "After every mode completion or decision, update the routing index" line.

```diff
  After every mode completion or decision, update the routing index.

+ After every mode activation (entry into a mode, including variant selection),
+ write a routing_decision_log entry per Module 19 routing_decision_log schema
+ v1.0. Required fields: timestamp, turn_number, request_text (truncated to
+ 200 chars), candidate_modes, selected_mode, selected_variant,
+ trigger_phrase_matched, predicate_used (if applicable), re_routed flag,
+ re_route_reason (if re_routed = true).
+
+ Re-routing events (Navigator activation after initial routing, user explicit
+ redirect, or Critic adversarial finding "wrong mode for this task" at Sev 2+)
+ MUST set re_routed: true and provide re_route_reason. These entries archive
+ permanently per Module 19 retention policy.

  Before acting on any indexed information from prior turns, apply the
  skeptical verification rule...
```

**Test Criteria:**

```yaml
test_criteria_p8:
  deterministic_checks:
    - check_id: orchestrator_emits_log_entry
      assertion: "For test session with N mode activations, routing_decision_log contains N entries"
      file_path: tests/integration/test_orchestrator_logging_behavior.py
      depends_on: P5 (log schema)

    - check_id: orchestrator_re_route_reason_present
      assertion: "Every entry with re_routed: true has re_route_reason set"
      file_path: tests/integration/test_orchestrator_logging_behavior.py

    - check_id: orchestrator_static_zone_text_match
      assertion: "Module 00 Static Zone contains routing_decision_log behavior block"
      file_path: tests/spec/test_module_00_static_zone.py

  existing_tests_must_pass:
    - tests/spec/test_module_00_orchestrator.py

  new_tests_required: (covered by P5 integration test)
```

**Migration:** Behavior change — orchestrator now writes log entries. Backward compatible: prior sessions don't have log entries; metric #10 only computes against entries that exist (denominator handles N=0 case as "no data" rather than divide-by-zero).

---

### Patch P9 (U9) — Module 00: metric #10 awareness (impl_commit)

**Location:** Module 00 Static Zone, new behavior block after "Routing Index Integration", before "Infrastructure Module Activation".

```diff
+ ### Metric #10 Awareness (Mode Selection Accuracy)
+
+ Module 16 metric #10 (mode_selection_accuracy) tracks routing correctness
+ from routing_decision_log data. At every chain completion, evaluate the
+ rolling 100-event window:
+
+ - If overall accuracy < 90%: trigger Module 13 (Decision Classification)
+   review at session end
+ - If overall accuracy < 80%: ESCALATE — halt new chain starts until
+   calibration check completes
+ - If any per-variant accuracy < 95%: notify and audit variant trigger
+   phrase overlap
+ - If any per-variant accuracy < 85%: trigger Module 04 trigger_disambiguator
+   review, halt affected variant
+
+ Threshold checks are deterministic (per Module 16 metric #10 spec). Do not
+ re-evaluate per-turn — chain completion is the natural check point.
```

**Test Criteria:**

```yaml
test_criteria_p9:
  deterministic_checks:
    - check_id: orchestrator_metric_check_at_chain_completion
      assertion: "After chain completion, orchestrator evaluates mode_selection_accuracy thresholds"
      file_path: tests/integration/test_orchestrator_metric_10_behavior.py

    - check_id: orchestrator_threshold_actions_match_module_16
      assertion: "Threshold actions in Module 00 match Module 16 metric #10 corrective_action specifications"
      file_path: tests/spec/test_module_00_module_16_consistency.py

  existing_tests_must_pass:
    - tests/spec/test_module_00_orchestrator.py
    - tests/spec/test_module_16_metrics.py

  new_tests_required:
    - tests/integration/test_orchestrator_metric_10_behavior.py
    - tests/spec/test_module_00_module_16_consistency.py
```

**Migration:** Behavior change. Backward compatible (no metric #10 enforcement before patch).

---

## 2. Pre-Drafted Changelog Entries (KF 7.1.0)

```yaml
changelog:
  7.1.0:
    date: 2026-MM-DD                      # Set at merge
    cascade_reference: |
      Stage 2 cascade — tool-calling architecture audit, Track C.
      See chain-log-01 through chain-log-04 in cascade artifacts.
      Source article: "The Roadmap to Mastering Tool Calling in AI Agents"
      (7-step practitioner guide), mapped to KF modes-as-tools and
      orchestrator-as-model. Defensibility audit driver.
    changes:
      - Module 04: added Handoff_Contract entity with required fields
        (source_mode, source_variant, target_mode, target_variant,
        payload_schema, fallback_path, validation_checks). Resolves ERA F2
        and F5. Reversibility — single-commit revert.
      - Module 04: added trigger_disambiguator entity formalizing variant-
        resolution and cross-mode-overlap predicates (output_type_difference,
        domain_specificity, chain_context, user_disambiguation). Resolves
        F1 root cause and F6.
      - Module 05: Expert agent — variants[] field added (regular,
        infrastructure, ml_infrastructure, era). decision_type_exercised
        formalized as required output field with enum constraint
        (was 6.6.1 auto-verify gate signal, now schema-enforced).
        Backward-compat default until KF 7.2.0.
      - Module 07: Critic agent — variants[] field added (regular, linter,
        audit, adversarial). Trigger phrases and output formats per variant.
      - Module 16: added metric #10 (mode_selection_accuracy). Re-routing
        rate as primary measurement (deterministic, from routing_decision_log).
        Adversarial sampling for weekly calibration. Variant-aware thresholds:
        90% overall, 95% per-variant. ERA F1 + F4.
      - Module 19: added routing_decision_log hook (schema_version 1.0).
        Audit trail of routing decisions, separate from routing_index (state).
        Retention — rolling 1000 entries + permanent re-route archive +
        weekly aggregate persistence.
      - Module 03: added Handoff Contract Registry — 8 active handoff edges
        registered as handoff_contract_instance entries (Builder→Critic
        auto-verify, Expert→Builder, Strategist→Builder, Synthesizer→Builder,
        Critic→Builder revision, Debugger→Strategist, Critic-audit→Strategist,
        Strategist→Calibrator).
      - Module 00 (orchestrator): static zone updated to write
        routing_decision_log entries on every mode activation; metric #10
        threshold awareness at chain completion.
```

## 3. Stage 3 Handoff Block

```yaml
stage_3_handoff:
  target: knowledgeforge-core Claude Code session
  protocol: spec-commit-before-impl-commit
  branch_naming: feat/tool-calling-audit-c

  pre_flight_blockers:
    - none for Track C scope (typed error signals deferred to separate cascade per Stage 1)
    - confirm wiki/ taxonomy accommodates accretion candidates surfaced this audit (3 candidates: ac-era-1, ac-era-2, ac-era-3 — see chain-log-04)
    - confirm KF 7.0.0 main branch is the integration target
    - F7 orphan reference (Module 25 ERA Agent status, Module 03 naming inconsistency) — Stage 3 documentation pass, non-blocking

  atomic_tasks:
    - id: T01
      type: spec_commit
      description: "Module 04 — add trigger_disambiguator entity (P1 / U1)"
      affected_files: [04_Specification_Templates.md]
      patch_reference: chain-log-03 §1 Patch P1
      test_protocol:
        failing_test_first: "tests/spec/test_module_04_trigger_disambiguator.py — file does not exist; run shows 'no such file'"
        patch: P1
        passing_test_after: "test_module_04_trigger_disambiguator.py — all 3 deterministic checks pass"
      rollback: single-commit revert

    - id: T02
      type: spec_commit
      description: "Module 04 — add Handoff_Contract entity, rename Usage Notes (P2 / U2)"
      affected_files: [04_Specification_Templates.md]
      patch_reference: chain-log-03 §1 Patch P2
      test_protocol:
        failing_test_first: "tests/spec/test_module_04_handoff_contract.py — file does not exist"
        patch: P2
        passing_test_after: "all 4 deterministic checks pass"
      rollback: single-commit revert

    - id: T03
      type: spec_commit
      description: "Module 07 — add Critic variants[] (P3 / U3)"
      affected_files: [07_Critic_Agent.md]
      depends_on: T01
      patch_reference: chain-log-03 §1 Patch P3
      test_protocol:
        failing_test_first: "tests/spec/test_module_07_variants.py — file does not exist"
        patch: P3
        passing_test_after: "all 4 deterministic checks pass"
      rollback: single-commit revert

    - id: T04
      type: spec_commit
      description: "Module 05 — add Expert variants[] + decision_type_exercised (P4 / U4)"
      affected_files: [05_Expert_Agent_Example.md]
      depends_on: T01
      patch_reference: chain-log-03 §1 Patch P4
      test_protocol:
        failing_test_first: "tests/spec/test_module_05_variants.py and test_module_05_output_schema.py do not exist"
        patch: P4
        passing_test_after: "all 4 deterministic checks pass"
      rollback: single-commit revert (multi-line edit, single semantic change)

    - id: T05
      type: spec_commit
      description: "Module 19 — add routing_decision_log hook (P5 / U5)"
      affected_files: [19_Memory_Architecture.md]
      patch_reference: chain-log-03 §1 Patch P5
      test_protocol:
        failing_test_first: "tests/spec/test_module_19_routing_decision_log.py does not exist; existing test_module_19_routing_index.py still passes"
        patch: P5
        passing_test_after: "all 5 deterministic checks pass; existing test_module_19_routing_index.py still passes"
      rollback: single-commit revert

    - id: T06
      type: spec_commit
      description: "Module 16 — add metric #10 (mode_selection_accuracy) (P6 / U6)"
      affected_files: [16_Operational_Bounds.md]
      depends_on: [T01, T05]
      patch_reference: chain-log-03 §1 Patch P6
      test_protocol:
        failing_test_first: "tests/spec/test_module_16_metric_10.py does not exist"
        patch: P6
        passing_test_after: "all 4 deterministic checks pass; existing test_module_16_metrics.py still passes (metrics 1–9)"
      rollback: single-commit revert

    - id: T07
      type: spec_commit
      description: "Module 03 — add Handoff Contract Registry (P7 / U7)"
      affected_files: [03_Coordination_Patterns.md]
      depends_on: [T02, T03, T04]
      patch_reference: chain-log-03 §1 Patch P7
      test_protocol:
        failing_test_first: "tests/spec/test_module_03_handoff_registry.py and test_module_03_handoff_completeness.py do not exist"
        patch: P7
        passing_test_after: "all 4 deterministic checks pass for 8 registered edges"
      rollback: single-commit revert

    - id: T08
      type: impl_commit
      description: "Module 00 — orchestrator writes routing_decision_log entries on every mode activation (P8 / U8)"
      affected_files: [00_Agent_Instructions.md]
      depends_on: T05
      patch_reference: chain-log-03 §1 Patch P8
      test_protocol:
        failing_test_first: "tests/integration/test_orchestrator_logging_behavior.py — log entries absent for test session"
        patch: P8 (Module 00 static zone update)
        passing_test_after: "log contains entry per mode activation; re_routed entries have re_route_reason"
      rollback: single-commit revert

    - id: T09
      type: impl_commit
      description: "Module 00 — orchestrator evaluates metric #10 thresholds at chain completion (P9 / U9)"
      affected_files: [00_Agent_Instructions.md]
      depends_on: T06
      patch_reference: chain-log-03 §1 Patch P9
      test_protocol:
        failing_test_first: "tests/integration/test_orchestrator_metric_10_behavior.py — no threshold evaluation occurs"
        patch: P9 (Module 00 static zone update)
        passing_test_after: "threshold evaluation fires at chain completion; corrective actions match Module 16 spec"
      rollback: single-commit revert

  atomic_task_count: 9
  ceiling: 10
  status: WITHIN_CEILING

  test_artifacts:
    existing_must_pass:
      - tests/spec/test_module_00_orchestrator.py
      - tests/spec/test_module_03_coordination_patterns.py
      - tests/spec/test_module_04_template_validity.py
      - tests/spec/test_module_05_expert_agent.py
      - tests/spec/test_module_07_critic_agent.py
      - tests/spec/test_module_16_metrics.py
      - tests/spec/test_module_19_routing_index.py

    new_required:
      - tests/spec/test_module_04_trigger_disambiguator.py
      - tests/spec/test_module_04_handoff_contract.py
      - tests/spec/test_module_04_cross_module_consistency.py
      - tests/spec/test_module_05_variants.py
      - tests/spec/test_module_05_output_schema.py
      - tests/spec/test_module_05_cross_module_consistency.py
      - tests/spec/test_module_07_variants.py
      - tests/spec/test_module_16_metric_10.py
      - tests/spec/test_module_16_cross_module_consistency.py
      - tests/spec/test_module_19_routing_decision_log.py
      - tests/spec/test_module_03_handoff_registry.py
      - tests/spec/test_module_03_handoff_completeness.py
      - tests/spec/test_module_00_static_zone.py
      - tests/spec/test_module_00_module_16_consistency.py
      - tests/integration/test_orchestrator_logging_behavior.py
      - tests/integration/test_orchestrator_metric_10_behavior.py

  spec_diff_estimate: ~250 lines additive across 6 module files
  pr_scope_estimate: 9 commits, single PR

  completion_signal: |
    PR ready with chain-log-04-tool-calling.md attached and all Critic
    Sev 1/2 findings resolved (loop_exit_protocol max=1 applied).
```

---

**Builder phase complete. Handoff to Critic phase (chain-log-04).**
