# Chain-Log 01 — ERA Phase

## Cascade Metadata

```yaml
cascade:
  stage: 2
  phase: ERA
  chain: "ERA → Strategist → Builder → Critic"
  cascade_id: tool-calling-architecture-audit
  track: C
  target_version: KF 7.1.0
  decision_type: evaluative_judgment
  expertise_level: advanced
  source_modes: [orchestrator, expert_era_variant]
  produces_for: chain-log-02-tool-calling.md (Strategist phase)
  date: 2026-05-08
```

## Scope (Locked)

**In-scope active modes (10):** Navigator (01), Builder (02), Coordinator-as-pattern (03 reference), Expert (05), Critic (07), Synthesizer (08), Debugger (09), Strategist (10), Calibrator (11), Orchestrator (00).

**In-scope infrastructure modules (5):** Module 04 (Specification Templates), Module 16 (Operational Bounds), Module 19 (Memory Architecture), Module 20 (Permission Model), Module 21 (Knowledge Accretion).

**Out-of-scope:** Cross-cutting modules 12–15, 17–18, 22–24 referenced only where they appear as handoff dependencies in the active-mode graph. Module 25 (ERA Agent) noted but not audited as entity (orphan reference risk handled in findings).

## 1. Entity Graph

### Mode Entities

```yaml
entities:
  - id: orchestrator
    name: KF Orchestrator
    module: 00 (this module)
    trigger_phrases: [all incoming requests]
    primary_output_type: route_decision
    decision_type_sensitivity: gating  # classifies all inbound; emits no content directly
    variants: none
    risk_tier_base: LOW (per Module 20)

  - id: navigator
    name: Navigator
    module: 01
    trigger_phrases: ["[automatic — fires on output-type predicate match]"]
    primary_output_type: route_decision
    decision_type_sensitivity: gating
    variants: none
    risk_tier_base: LOW
    activation_predicate:
      type: output_type_difference
      rule: "Top-2 candidate modes have different primary output types (artifact vs. recommendation vs. analysis vs. route)"

  - id: builder
    name: Builder
    module: 02
    trigger_phrases: [create, build, generate, write a specification, make]
    primary_output_type: artifact (specification)
    decision_type_sensitivity: evaluative+
    variants: none
    risk_tier_base: MEDIUM
    chain_escalation: true (HIGH when in 3+ mode chains)

  - id: expert
    name: Expert
    module: 05
    trigger_phrases: [domain-specific question, deep analysis, review, infrastructure architecture, model deployment, entity relationships]
    primary_output_type: analysis (with adversarial depth)
    decision_type_sensitivity: evaluative+
    variants:                              # FINDING F1 — currently informal
      - regular
      - infrastructure
      - ml_infrastructure
      - era
    risk_tier_base: MEDIUM

  - id: critic
    name: Critic
    module: 07
    trigger_phrases: [review, check, validate, find gaps, identify what's missing, health check, lint, hosting audit, decomposition readiness]
    primary_output_type: findings_list
    decision_type_sensitivity: evaluative
    variants:                              # FINDING F1 — currently informal
      - regular
      - linter (knowledge base health)
      - audit (infrastructure inventory)
      - adversarial (auto-verify in chains)
    risk_tier_base: MEDIUM

  - id: synthesizer
    name: Synthesizer
    module: 08
    trigger_phrases: [patterns, commonalities, what things have in common, frameworks from examples]
    primary_output_type: pattern + anti-pattern
    decision_type_sensitivity: evaluative
    variants: none
    risk_tier_base: MEDIUM

  - id: debugger
    name: Debugger
    module: 09
    trigger_phrases: [broken, not working, failing, diagnose, why is X happening]
    primary_output_type: root_cause
    decision_type_sensitivity: evaluative
    variants: none
    risk_tier_base: MEDIUM

  - id: strategist
    name: Strategist
    module: 10
    trigger_phrases: [priorities, trade-offs, "should I", what to do next, which option, moat, defensibility]
    primary_output_type: recommendation
    decision_type_sensitivity: evaluative+
    variants: none
    risk_tier_base: MEDIUM (HIGH for irreversible decisions)

  - id: calibrator
    name: Calibrator
    module: 11
    trigger_phrases: [setup, configuration, CLAUDE.md, .cursorrules, AI coder best practices]
    primary_output_type: configuration_artifact
    decision_type_sensitivity: evaluative
    variants: none
    risk_tier_base: MEDIUM
```

### Infrastructure Module Entities

```yaml
infrastructure_entities:
  - id: module_04
    name: Specification Templates
    role: schema_authority
    consumed_by: [builder, critic, synthesizer, debugger, strategist, calibrator, expert]
    provides: [Agent_Specification, Critique, Synthesis, Diagnosis, Strategic_Decision, Process_Specification, Message, Handoff, Context, Assessment, AI_Coder_Configuration, Infrastructure_Architecture, Hosting_Audit, ERA_Specification]

  - id: module_16
    name: Operational Bounds
    role: chronic_drift_monitor
    consumed_by: [orchestrator]
    metrics_count: 9
    provides: [context_utilization, error_rate, confidence_calibration, api_cost, cache_hit_rate, circuit_breaker_state, mode_transition_cost, consolidation_efficiency, token_cost_per_mode]

  - id: module_19
    name: Memory Architecture
    role: state_authority
    consumed_by: [all modes]
    tiers: [tier_0_persistent, tier_1_routing_index, tier_2_mode_state, tier_3_verbatim_history]
    schema_contract: routing_index_schema v1.0

  - id: module_20
    name: Permission Model
    role: capability_gate
    consumed_by: [orchestrator, all modes]
    tiers: [LOW, MEDIUM, HIGH]

  - id: module_21
    name: Knowledge Accretion
    role: persistence_decision
    consumed_by: [all modes producing evaluative+ output]
    novelty_threshold: calibrated
    reuse_threshold: calibrated
```

## 2. Edges (Relationships)

### Trigger Edges (orchestrator → mode)

```yaml
trigger_edges:
  - source: orchestrator
    target: navigator
    cardinality: 1:1 per turn (when output-type predicate fires)
    formality: formal (output_type_difference predicate documented in Module 00 static zone)

  - source: orchestrator
    target: [builder, expert, critic, synthesizer, debugger, strategist, calibrator, coordinator-pattern]
    cardinality: 1:1 per turn (mutually exclusive within turn)
    formality: prose convention (trigger phrases in static zone)
    GAP: No formal trigger_disambiguator entity for cross-mode trigger overlaps
```

### Handoff Edges (mode → mode within chains)

```yaml
handoff_edges:
  - id: hf-builder-critic-autoverify
    source_mode: builder
    target_mode: critic
    target_variant: adversarial
    cardinality: 1:1 per chain step that produces evaluative+ output
    payload: specification_artifact + design_decisions + decision_types
    formality: prose convention (Module 00 "Automatic Adversarial Verification")
    GAP: No formal payload_schema, no fallback_path, no validation_checks

  - id: hf-expert-builder
    source_mode: expert
    source_variant: any
    target_mode: builder
    cardinality: 1:1 per chain
    payload: analysis + adversarial_depth + decision_type_exercised
    formality: prose convention (Module 05) + 6.6.1 changelog only for decision_type_exercised
    GAP: decision_type_exercised is read by orchestrator auto-verify gate but not formally required on Expert output schema

  - id: hf-strategist-builder
    source_mode: strategist
    target_mode: builder
    cardinality: 1:1 per chain
    payload: recommendation + sequencing + reversibility
    formality: prose convention
    GAP: No formal payload_schema

  - id: hf-synthesizer-builder
    source_mode: synthesizer
    target_mode: builder
    cardinality: 1:1 per chain
    payload: pattern + anti_pattern + applicability_boundaries
    formality: prose convention
    GAP: No formal payload_schema

  - id: hf-critic-builder-revision
    source_mode: critic
    source_variant: adversarial OR regular
    target_mode: builder
    cardinality: 1:1 per revision cycle (max=1 per loop_exit_protocol)
    payload: findings_list (Sev 1/2/3 classified)
    formality: Module 07 loop_exit_protocol; payload structure prose convention
    GAP: No formal feedback schema; Builder interprets findings ad hoc

  - id: hf-debugger-strategist
    source_mode: debugger
    target_mode: strategist
    cardinality: 1:1 per chain
    payload: root_cause + diagnostic_path
    formality: prose convention

  - id: hf-critic-audit-strategist
    source_mode: critic
    source_variant: audit
    target_mode: strategist
    cardinality: 1:1 per infrastructure cascade
    payload: hosting_audit_template_populated + decomposition_readiness
    formality: Module 04 (Hosting Audit template) + prose convention for handoff

  - id: hf-strategist-calibrator
    source_mode: strategist
    target_mode: calibrator
    cardinality: 1:1 per "decide stack then setup" chain
    payload: stack_decision
    formality: prose convention
```

### Activation Predicate Edges

```yaml
activation_predicates:
  - predicate: output_type_difference
    activates: navigator
    formal: yes (Module 00 static zone)

  - predicate: trigger_phrase_match
    activates: [builder, expert, critic, synthesizer, debugger, strategist, calibrator]
    formal: prose convention only
    GAP: F1 — multiple trigger phrases activate same mode label across variants

  - predicate: chain_position_implies_variant
    activates: critic_adversarial (post-Builder/Strategist), expert_era (in ERA chain)
    formal: chain pattern in Module 03 prose; no formal predicate entity

  - predicate: decision_type_exercised >= evaluative
    activates: critic_adversarial (auto-verify gate per 6.6.1)
    formal: 6.6.1 changelog only; not in any schema
```

### Infrastructure Activation Edges

```yaml
infrastructure_activations:
  - source: any_evaluative_plus_output
    target: module_12_calibration_layer
    cardinality: 1:1
    formal: Module 00 prose

  - source: claims_built_on_uncertain_premises
    target: module_15_grounding_scores
    cardinality: 1:1
    formal: Module 00 prose

  - source: extended_reasoning (>5 steps)
    target: module_14_metacognitive_monitor
    cardinality: 1:1
    formal: automatic (Module 14)

  - source: any_mode_completion
    target: module_19_routing_index_update
    cardinality: 1:1
    formal: Module 19 routing_index_schema v1.0
    GAP: No routing-decision logging (only state index, not decision audit trail)

  - source: any_evaluative_plus_output
    target: module_21_accretion_check
    cardinality: 1:1
    formal: Module 21 calibration thresholds (6.6.1)

  - source: any_action
    target: module_20_risk_tier_classification
    cardinality: 1:1
    formal: Module 20 tier model
```

## 3. Coupling Analysis

### Implicit Contracts (couplings present in practice but not formalized)

```yaml
implicit_contracts:
  - id: ic-1
    description: "Expert output contains decision_type_exercised field consumed by orchestrator auto-verify gate"
    source: expert
    target: orchestrator (auto-verify gate)
    location_documented: Module 00 changelog 6.6.1
    location_formalized: NONE
    risk: Expert variant or future mode change could omit field; gate silently degrades to evaluative_judgment default

  - id: ic-2
    description: "Builder output structure assumed by Critic (adversarial) for finding location specificity"
    source: builder
    target: critic_adversarial
    location_documented: Module 02 prose + Module 07 prose
    location_formalized: NONE
    risk: Schema drift between Builder output structure and Critic expectations surfaces as runtime "vague finding location" rather than fast-fail

  - id: ic-3
    description: "Critic findings format consumed by Builder for revision cycle"
    source: critic
    target: builder (revision)
    location_documented: Module 07 loop_exit_protocol
    location_formalized: NONE
    risk: Builder may misinterpret severity levels or location specifications in revision

  - id: ic-4
    description: "Decision Ensemble three-provider isolation contract (Anthropic persona, OpenAI judge, Google blindspot)"
    source: orchestrator
    target: provider_routing
    location_documented: User memory / KF 7.0.0 design notes
    location_formalized: NONE in module specs
    risk: Out of scope for this cascade; flag for future work

  - id: ic-5
    description: "Variant disambiguation within Critic (regular/linter/audit/adversarial) and Expert (regular/infrastructure/ml_infrastructure/era)"
    source: orchestrator
    target: critic OR expert
    location_documented: Module 00 trigger phrases (prose)
    location_formalized: NONE — variants share single mode label
    risk: F1 directly — metric #10 cannot disaggregate variant accuracy without formal taxonomy
```

### Trigger Phrase Overlaps

```yaml
trigger_overlaps:
  - phrase: "review"
    candidates:
      - {mode: critic, variant: regular}
      - {mode: expert, variant: any (when domain follows)}
    disambiguation: domain specificity (currently prose convention only)
    risk: Low in practice (domain context usually clear) but no formal predicate

  - phrase: "audit"
    candidates:
      - {mode: critic, variant: linter (knowledge base)}
      - {mode: critic, variant: audit (infrastructure)}
    disambiguation: object of audit (knowledge base vs. hosting)
    risk: Medium — same mode label, different output formats

  - phrase: "validate"
    candidates:
      - {mode: critic, variant: regular}
      - {mode: critic, variant: linter}
      - {mode: calibrator (config validation)}
    disambiguation: domain context (spec vs. KB vs. config)
    risk: Medium

  - phrase: "build"
    candidates:
      - {mode: builder}
      - {mode: calibrator (when "build config")}
    disambiguation: object specificity
    risk: Low (Calibrator typically triggered by AI-coder-tool keywords)

  - phrase: "design"
    candidates:
      - {mode: builder}
      - {mode: expert, variant: infrastructure (when "design infrastructure")}
      - {mode: strategist (when "design strategy")}
    disambiguation: chain context
    risk: Medium
```

### Handoff Payload Schema Gaps

| Edge | Source Output | Target Input Expectation | Schema Match? |
|------|---------------|--------------------------|---------------|
| Builder → Critic (auto-verify) | specification_artifact | structured spec with design_decisions | implicit, prose only |
| Expert → Builder | analysis + adversarial_depth + decision_type_exercised | first-order findings + design implications | implicit; decision_type_exercised gate dependency |
| Strategist → Builder | recommendation + sequencing | actionable directives | implicit |
| Synthesizer → Builder | pattern + anti_pattern | reusable building block | implicit |
| Critic → Builder (revision) | findings_list (Sev classified) | location + fix per finding | implicit |
| Debugger → Strategist | root_cause + diagnostic_path | actionable fix-or-rebuild input | implicit |
| Critic (audit) → Strategist | hosting_audit_template | extraction priority input | partial (template formal, handoff not) |
| Strategist → Calibrator | stack_decision | configuration scope input | implicit |

**Eight handoff edges. Zero formal payload_schema. Zero formal fallback_path. Zero formal validation_checks.**

### Mode-Label Collisions

```yaml
mode_label_collisions:
  - mode_label: critic
    variant_count: 4
    variants:
      - regular: trigger "review/check/validate/find gaps"; output findings_list
      - linter: trigger "health check/lint knowledge base"; output maintenance_backlog
      - audit: trigger "hosting audit/decomposition readiness"; output hosting_audit_populated
      - adversarial: trigger automatic (chain auto-verify); output severity_classified_findings
    distinguished_by: trigger phrase + chain context only
    formal_taxonomy: NONE
    impact: Aggregate "Critic mode usage" metrics meaningless; F1 root cause

  - mode_label: expert
    variant_count: 4
    variants:
      - regular: domain-specific deep analysis (any domain)
      - infrastructure: infrastructure architecture domain
      - ml_infrastructure: GPU sizing / inference serving
      - era: entity relationship analysis
    distinguished_by: trigger phrase + chain context only
    formal_taxonomy: NONE
    impact: Same as Critic; doubled by Expert's broader trigger surface
```

## 4. Adversarial Findings Checklist

### Hidden Couplings

- **Auto-verify gate ↔ Expert output:** orchestrator gates on `decision_type_exercised` field. Expert spec doesn't formally require it. (ic-1)
- **Module 21 accretion check ↔ Builder output:** Module 21 reads accretion candidate metadata from Builder/Expert/Synthesizer outputs. Module 04 templates don't enforce the metadata structure on output schemas (it's documented as "field added" in 6.2 but not as required field per output type).
- **Decision Ensemble cross-provider isolation ↔ orchestrator:** three-provider isolation is a design constraint without spec representation. (ic-4)

### Cardinality Violations

- **Auto-verify trigger:** orchestrator spec implies 1:1 chain output → Critic (adversarial). In multi-mode chains (Expert → Strategist → Builder), each evaluative+ producer could trigger Critic. Spec is ambiguous on whether one consolidated Critic pass or N passes. **Current behavior unclear.**
- **Module 04 → Builder in cascades:** 1:1 by template selected. But infrastructure cascades produce N module specs from one Critic-audit handoff. Builder spec doesn't formally describe per-cascade artifact multiplication.

### Schema Drift

- **Module 04 Usage Notes table** lists template "Handoff" (singular) — implies entity exists. **No `Handoff_Contract` or `Handoff` entity definition in Module 04.** Naming inconsistency.
- **6.6.1 changelog references** `decision_type_exercised`, `loop_exit_protocol`, `routing_index_schema` v1.0 — schema_version exists in Module 19, but `decision_type_exercised` and `loop_exit_protocol` are referenced in changelog without corresponding schema entries in Module 05 or Module 07 outputs.
- **Module 06 (Quick Reference)** must be inspected for variant taxonomy alignment if variants are formalized in Module 05/07. Drift risk from this cascade.

### Implicit Contracts Not Represented as Formal Entities

- All eight handoff edges (see table above)
- Variant disambiguation predicate (per mode_label_collisions)
- Auto-verify activation predicate (decision_type_exercised >= evaluative)
- Cross-provider isolation contract (Decision Ensemble)

### Orphan References

- **Module 25 (ERA Agent):** orchestrator module reference table lists as "optional — only created if Module 05 ERA section exceeds ~200 lines." Status as file uncertain. Expert ERA variant references it via "Reference: 05_Expert_Agent_Example.md (ERA domain adaptation), 04_Specification_Templates.md (ERA Specification Template)" — Module 25 not actually referenced in trigger flow. Low risk; documentation cleanup item.
- **Module 03 (Coordination Patterns):** referenced by orchestrator as "Coordinator mode" trigger but Module 03 is patterns reference, not an active mode. Naming inconsistency (Coordinator-as-pattern vs. Coordinator-as-mode). Low risk; Module 03 is consulted, not activated as a mode.

## 5. Findings Classification

```yaml
findings:
  - id: F1
    severity: 1  # Sev 1 — blocking for Track C
    category: mode_label_collision
    location:
      - Module 00 (orchestrator) trigger sections
      - Module 05 (Expert) variants prose
      - Module 07 (Critic) variants prose
    evidence:
      - "Critic" label has 4 variants distinguished only by trigger phrase
      - "Expert" label has 4 variants distinguished only by trigger phrase + chain context
      - No formal taxonomy enforces variant identity
    impact: |
      Mode-selection accuracy metric (Track C deliverable) cannot be grounded without
      variant-level disaggregation. Aggregate "Critic accuracy" or "Expert accuracy"
      conflates 4 distinct output types per mode. This is the determining factor for
      Track C metric specification.
    proposed_remediation_scope:
      - Formalize variants[] field on Critic and Expert agent specs
      - Define trigger_disambiguator entity in Module 04 to formalize variant resolution
      - Make metric #10 (mode_selection_accuracy) variant-aware

  - id: F2
    severity: 2  # Sev 2 — significant
    category: handoff_payload_schema_gaps
    location:
      - Module 04 (no Handoff_Contract entity)
      - All 8 handoff edges (no formal payload_schema)
    evidence:
      - Schema mismatches surface as runtime escalation rather than fast-fail at boundary
      - No fallback_path defined per edge
      - No validation_checks defined per edge
    impact: |
      Handoff failures degrade silently into "Critic finds vague locations" or
      "Builder misinterprets feedback." No deterministic check at handoff boundary.
      Article principle 2 (tool definitions as contracts) is the most direct
      defensibility gap for KF orchestration vs. frontier-native orchestration.
    proposed_remediation_scope:
      - Define Handoff_Contract entity in Module 04
      - Register handoff_contract_instance for each of 8 active handoff edges
      - Add validation_checks with at least one deterministic check per edge

  - id: F3
    severity: 2
    category: implicit_contract_not_formalized
    location: Module 05 (Expert agent spec), Module 00 (auto-verify gate)
    evidence:
      - 6.6.1 changelog references decision_type_exercised as gating signal
      - Expert output schema does not formally include decision_type_exercised as required field
    impact: |
      Auto-verify gate silently defaults if Expert output omits the field. Variant
      changes or future mode additions could break the gate without spec violation.
    proposed_remediation_scope:
      - Add decision_type_exercised as required field on Expert output schema in Module 05
      - Specify enum values matching Module 13 (reckoning, evaluative_judgment, predictive_judgment, novel_judgment)

  - id: F4
    severity: 2
    category: missing_logging_for_metric_grounding
    location: Module 19 (routing index covers state, not decision audit trail)
    evidence:
      - routing_index tracks current state but not historical routing decisions
      - No log of which trigger phrase matched which mode/variant
      - No log of re-routing events
    impact: |
      Metric #10 (mode_selection_accuracy) measurement protocol depends on routing-
      decision audit trail. Without it, metric is unmeasurable. F4 directly enables F1
      remediation; sequencing constraint for Strategist phase.
    proposed_remediation_scope:
      - Add routing_decision_log hook to Module 19 with schema and retention policy
      - Schema_version 1.0 for new log; coexists with routing_index_schema v1.0

  - id: F5
    severity: 3
    category: schema_drift_naming_inconsistency
    location: Module 04 Usage Notes table
    evidence:
      - Usage Notes lists "Handoff" template
      - No Handoff entity definition in Module 04
    impact: Documentation inconsistency; resolves automatically via F2 remediation (Handoff_Contract entity)
    proposed_remediation_scope: Absorbed into F2

  - id: F6
    severity: 3
    category: trigger_phrase_overlap_undocumented
    location: Module 00 (orchestrator) trigger sections
    evidence:
      - "review", "audit", "validate", "design" each activate multiple modes/variants
      - Disambiguation is prose convention, not formal predicate
    impact: Edge case routing failures; resolves automatically via F1 remediation (trigger_disambiguator)
    proposed_remediation_scope: Absorbed into F1

  - id: F7
    severity: 3
    category: orphan_reference
    location: Module 00 module reference table
    evidence:
      - Module 25 (ERA Agent) listed as "optional"
      - Status as file uncertain
      - Module 03 referenced as "Coordinator mode" in some places, "Coordination Patterns" in others
    impact: Documentation cleanup; Stage 3 awareness item, not blocking
    proposed_remediation_scope: Resolve in Stage 3 handoff; orchestrator prose pass
```

## 6. Pre-flight Escalation Gate Check

**Question:** Do these findings invalidate the Track C decomposition?

**Track C requires:**
1. Audit produces evidence-based architectural insight ✓ (this ERA)
2. Grounded metric specification (mode-selection accuracy) — requires F1 remediation to be meaningful
3. Shipped patches addressing F1 + F2 + supporting infrastructure

**Assessment:**

F1 does not invalidate Track C; it **refines** the metric specification. The metric must be variant-aware. This is a scoping refinement, not a Track C failure. Sequencing is unchanged: F1 remediation (variant taxonomy + disambiguator) precedes metric #10 specification.

F4 introduces a new Strategist-phase patch (routing-decision logging hook) not anticipated in Stage 1 pressure-test. Estimated additional patch surface: 1 atomic unit. Track C atomic-task ceiling is ~10. Stage 1 pressure-test estimated 4–6 patches. New estimate: 6–9 patches. Within ceiling.

**Decision:** Proceed to Strategist phase. No escalation to David. Pre-flight gate passes.

## 7. Adversarial Yield (Self-Check)

```yaml
adversarial_yield:
  findings_total: 7
  sev_1_count: 1
  sev_2_count: 3
  sev_3_count: 3
  sev_2_plus_yield: 4 / 7 = 57%
  yield_threshold_per_module_00: 20%
  yield_status: WELL_ABOVE_THRESHOLD
  rationale: |
    F1, F2, F3, F4 are independent failure modes affecting orchestrator integrity.
    F5, F6, F7 are minor cleanup absorbed into Sev 1/2 remediation.
    Yield is high because article-principle audit surfaces well-documented gap class
    (handoff contracts in tool-calling protocols).
```

## 8. Accretion Candidates Surfaced

```yaml
accretion_candidates_phase_1:
  - id: ac-era-1
    novelty_type: new_pattern
    content: "Mode-label-with-variants taxonomy as architectural pattern"
    grounding_score: 0.85
    importance_inferred: 4 (new_pattern + Expert source + ERA finding)
    knowledge_target: wiki/architecture/mode-variant-taxonomy.md
    deferred_to: chain-log-04 accretion check (post-Critic verification)

  - id: ac-era-2
    novelty_type: reusable_diagnostic
    content: "Handoff payload schema gap as systematic ERA finding category"
    grounding_score: 0.8
    importance_inferred: 3
    knowledge_target: wiki/era/handoff-contract-gaps.md
    deferred_to: chain-log-04 accretion check

  - id: ac-era-3
    novelty_type: transferable_framework
    content: "Article-to-KF principle mapping methodology — practitioner-guide to architecture-spec translation pattern"
    grounding_score: 0.75
    importance_inferred: 4 (transferable_framework)
    knowledge_target: wiki/methodology/practitioner-guide-translation.md
    deferred_to: chain-log-04 accretion check
```

## 9. Output to Strategist Phase

**Mandatory carry-forward:**
- All 7 findings with severity classification
- F1 + F4 sequencing constraint (F1 remediation enables variant-aware metric; F4 enables metric measurement)
- Patch surface estimate: 6–9 atomic units (within Track C ceiling)
- Pre-flight gate: PASS

**Open items for Strategist:**
- Define "correct mode selection" with variant awareness (grounded in F1 evidence)
- Specify measurement protocol (re-routing rate as primary, adversarial sampling for calibration)
- Specify threshold actions (per-mode and per-variant thresholds)
- Sequence patches: F1 (disambiguator + variants) → F2 (Handoff_Contract entity) → F2 (per-mode registrations) → F3 (Expert decision_type_exercised) → F4 (routing-decision log hook) → metric #10 spec

**Decision type exercised by ERA:** evaluative_judgment.
**Auto-verify gate (per Module 00):** This output triggers Critic adversarial pass at chain-log-04. Confirmed.

---

**ERA phase complete. Handoff to Strategist phase (chain-log-02).**
