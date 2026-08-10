# Agent Coordination Patterns

## Module Metadata

```yaml
module:
  title: Agent Coordination Patterns
  version: 7.6.0
  purpose: Design multi-agent workflows by mapping dependencies first, then deriving the coordination pattern from the graph
  topics: [coordination, multi-agent, workflows, handoffs, orchestration, dependency-mapping, verification, capability-restriction, handoff-contract-registry]
  contexts: [complex-tasks, agent-teams, workflow-design, mode-handoff-validation]
  difficulty: advanced
  related: [00_Orchestrator, 01_Navigator_Agent, 02_Builder_Agent, 04_Specification_Templates, 05_Expert_Agent_Example, 07_Critic_Agent, 08_Synthesizer_Agent, 09_Debugger_Agent, 10_Strategist_Agent, 11_Calibrator_Agent, 14_Metacognitive_Monitor, 16_Operational_Bounds, 18_Salience_Allocation, 19_Memory_Architecture, 20_Permission_Model]```

---

## Core Approach

Multi-agent systems fail when handoffs lose context or when agents step on each other's work. Good coordination starts with understanding what depends on what — the pattern emerges from the dependency graph, not from selecting a taxonomy entry.

**Primary challenge:** Getting agents to work together without losing information or duplicating effort.

**Key insight:** Map dependencies first, derive the pattern from the graph. Don't select a pattern then force-fit the workflow.

**Meta-principle:** This patches Sonnet's weakness (rigid pattern selection) rather than scaffolding its strength (flexible ad-hoc coordination). Raw Sonnet already combines approaches flexibly. The value-add here is *systematic* dependency analysis that prevents missed handoffs and implicit ordering assumptions.

---

## Dependency-First Workflow Design

### The Workflow Decomposition Protocol

Given a multi-agent task, derive the coordination pattern from the dependency graph rather than selecting one up front.

```yaml
workflow_decomposition:
  step_1_enumerate:
    action: List all subtasks required to complete the goal
    output: Flat list of subtasks with brief descriptions
    
  step_2_hard_dependencies:
    action: For each pair of subtasks, ask "Does A's output feed B?"
    output: Directed edges representing hard dependencies (B cannot start without A's output)
    notation: "A → B" means A must complete before B starts
    
  step_3_soft_dependencies:
    action: For each pair without hard dependency, ask "Would A's output improve B?"
    output: Dashed edges representing soft dependencies (B works without A but works better with it)
    notation: "A ⇢ B" means B benefits from A but doesn't require it
    
  step_4_draw_graph:
    action: Construct the dependency graph from steps 2-3
    output: DAG (directed acyclic graph) of subtask relationships
    validation: Check for cycles — cycles indicate task decomposition error
    
  step_5_identify_parallel_clusters:
    action: Find groups of subtasks with no hard dependencies between them
    output: Sets of parallelizable work
    
  step_6_identify_sequential_chains:
    action: Find longest paths of hard dependencies
    output: Critical path(s) that determine minimum completion time
    
  step_7_identify_coordination_points:
    action: Find nodes where multiple inputs converge
    output: Aggregation/synthesis points requiring conflict resolution
    
  step_8_derive_pattern:
    action: The graph implies the pattern — read it, don't select one
    output: Hybrid coordination pattern that matches the actual dependency structure
```

### Example: Workflow Decomposition in Practice

**Task:** Create, validate, and deploy a new agent with strategic context.

```yaml
subtasks:
  A: Strategic context assessment (Strategist)
  B: Pattern extraction from existing agents (Synthesizer)
  C: Agent specification creation (Builder)
  D: Structural review (Critic)
  E: Failure mode analysis (Debugger)
  F: Domain validation (Expert)
  G: Revision if needed (Builder)
  H: Deployment approval

hard_dependencies:
  A → C  # Builder needs strategic context
  B → C  # Builder needs patterns to apply
  C → D  # Critic needs spec to review
  C → E  # Debugger needs spec for failure analysis
  C → F  # Expert needs spec for domain validation
  D → G  # Revision needs critique
  E → G  # Revision needs failure analysis
  F → G  # Revision needs domain feedback
  G → H  # Deployment needs revised spec

soft_dependencies:
  A ⇢ B  # Synthesizer benefits from strategic context but doesn't require it

derived_pattern:
  phase_1: A and B in parallel (no hard deps between them; A ⇢ B is soft)
  phase_2: C sequential (requires both A and B outputs)
  phase_3: D, E, F in parallel (all need C, none need each other)
  phase_4: G sequential (requires D, E, F — coordination point)
  phase_5: H sequential (requires G)
  
  description: >
    Parallel start → sequential creation → parallel validation → 
    sequential revision → sequential deployment. This is a hybrid pattern 
    that was derived from the dependency graph, not selected from a menu.
```

### Coordinator → Builder Handoff Schema (6.6.1)

Formal output contract for the Coordinator → Builder handoff. Builder's `requirements` input must be populated from these fields. Absence of any required field is an incomplete coordination output — complete the analysis before handing off.

```yaml
coordination_handoff_schema:
  required_fields:
    problem_to_solve:
      type: string
      maps_to: "Builder.inputs.requirements.problem_to_solve"
      source: "Step 1 (enumerate subtasks) + user's original objective"
      description: One-sentence statement of what the completed workflow must achieve.

    dependency_graph:
      type: object
      maps_to: "Builder.inputs.requirements.integration_needs"
      source: "Steps 2–4 (graph derivation)"
      schema:
        nodes: array[string]   # Subtask or agent names
        edges:
          hard: array[tuple]   # [source, target] pairs — B cannot start without A
          soft: array[tuple]   # [source, target] pairs — B benefits from A
        cycles_detected: boolean  # Must be false — cycles indicate decomposition error
      description: The dependency graph as derived by the decomposition protocol.

    pattern_name:
      type: string
      maps_to: "Builder.inputs.requirements.constraints"
      source: "Step 8 (pattern derived from graph)"
      enum: [pipeline, parallel_cluster, hub_and_spoke, consensus, hierarchical, hybrid]
      description: Coordination pattern derived from the graph. Do not select before graphing.

    critical_path:
      type: array[string]
      maps_to: "Builder.inputs.requirements.constraints"
      source: "Step 6 (sequential chain identification)"
      description: Ordered list of agents/subtasks on the longest hard-dependency chain.

    parallel_clusters:
      type: array[array[string]]
      maps_to: "Builder.inputs.requirements.desired_outputs"
      source: "Step 5 (parallel cluster identification)"
      description: Groups of subtasks with no hard dependencies between them.

    handoff_protocol:
      type: array[object]
      maps_to: "Builder.inputs.requirements.integration_needs"
      source: "Steps 6–7 (sequential chains + convergence points)"
      schema:
        - from: string
          to: string
          dependency_type: hard | soft
          convergence_point: boolean
          context_to_carry: array[string]

  optional_fields:
    target_users:
      type: string
      maps_to: "Builder.inputs.requirements.target_users"
    success_metrics:
      type: array[string]

  validation:
    before_handing_to_builder: |
      Verify all required fields are populated.
      Verify cycles_detected is false.
      Verify pattern_name matches the graph structure (not pre-selected).
      If any required field is absent, complete the coordination analysis before handoff.
    decision_type: reckoning
```

### Handoff Contract Registry (NEW 7.2)

Per-edge registrations using the Module 04 `handoff_contract` entity. Covers the eight active mode-to-mode handoffs in the active mode set. Resolves ERA F2 (handoff payload schema gaps): each edge now has explicit `payload_schema`, `fallback_path`, and ≥1 deterministic `validation_checks` entry — handoff failures fail fast at the boundary instead of degrading silently downstream. All assertions use the canonical forms required by Module 04 (field-presence, enum-membership, cardinality, schema-conformance, cross-field).

```yaml
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
        assertion: "specification_artifact validates against Agent_Specification (Module 04)"  # schema-conformance
        check_type: deterministic
        failure_action: escalate_to_user
        failure_severity: Sev2
      - check_id: every_decision_typed
        assertion: "design_decisions[].decision_type matches enum: [reckoning, evaluative_judgment, predictive_judgment, novel_judgment]"  # enum-membership
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev2

  - id: hc-expert-to-builder
    source_mode: expert
    source_variant: any
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
        assertion: "decision_type_exercised is non-null"  # field-presence
        check_type: deterministic
        failure_action: route_to_navigator
        failure_severity: Sev1
      - check_id: decision_type_exercised_enum
        assertion: "decision_type_exercised matches enum: [reckoning, evaluative_judgment, predictive_judgment, novel_judgment]"  # enum-membership
        check_type: deterministic
        failure_action: route_to_navigator
        failure_severity: Sev1
      - check_id: adversarial_depth_present
        assertion: "adversarial_depth is non-null"  # field-presence
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
    # RESPONSE SCHEMA (NEW 7.6.0) — Builder's response back to Strategist.
    # Worked example of the upstream_invalidation signal (Module 04 7.4.0).
    # Scenario: Builder discovers during spec construction that a constraint exists
    # which invalidates the Strategist's recommendation (e.g., Strategist recommended
    # approach X, but Builder finds a hard dependency that makes X impossible).
    response_schema:
      fields:
        - name: verdict
          type: enum
          required: true
          description: "Builder's ability to implement the recommendation"
          validation: "enum: [implemented, blocked, partially_implemented]"
        - name: artifact_ref
          type: pointer
          required: false
          description: "Reference to the produced spec artifact when verdict=implemented"
        - name: upstream_invalidation
          type: object
          required: false
          description: |
            Populated only when Builder discovers a constraint that invalidates the
            Strategist's recommendation. Null when Builder can proceed normally.
            Fields: invalidated_step_id (= 'strategist'), claim_invalidated (the specific
            Strategist claim found false), evidence_ref (resolvable pointer to the
            constraint, NOT prose), severity (Sev1|Sev2|Sev3).
            Example: Builder finds the chosen database engine lacks a required feature —
            evidence_ref points to the technical constraint document; severity=Sev2
            triggers orchestrator re-entry at the Strategist step.
    fallback_path:
      type: retry_with_repair
      rationale: "Strategist output missing fields is correctable in single retry"
    validation_checks:
      - check_id: sequencing_dependencies_resolvable
        assertion: "sequencing[].dependencies and sequencing[].id are mutually consistent (every dependency references a valid id)"  # cross-field
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev2
      - check_id: trade_off_matrix_present
        assertion: "trade_off_matrix is non-null"  # field-presence
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev2
      # upstream_invalidation response checks (NEW 7.6.0 — Module 04 7.4.0 ui-checks):
      - check_id: ui-check-1-subfields-complete
        assertion: "NOT (upstream_invalidation is non-null) OR (invalidated_step_id AND claim_invalidated AND evidence_ref AND severity are all non-null)"  # cross-field
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev1
      - check_id: ui-check-2-severity-enum
        assertion: "upstream_invalidation.severity matches enum: [Sev1, Sev2, Sev3]"  # enum-membership
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev1
      - check_id: ui-check-3-evidence-required-for-high-severity
        assertion: "NOT (upstream_invalidation.severity IN [Sev2, Sev3]) OR (upstream_invalidation.evidence_ref is non-null AND resolves)"  # cross-field
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
      rationale: "Synthesizer requires anti-patterns; missing means analysis incomplete"
    validation_checks:
      - check_id: at_least_one_anti_pattern
        assertion: "len(anti_patterns) >= 1"  # cardinality
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev1

  - id: hc-critic-to-builder-revision
    source_mode: critic
    source_variant: any
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
        assertion: "revision_cycle_count <= 1"  # cardinality
        check_type: deterministic
        failure_action: escalate_to_user
        failure_severity: Sev1
      - check_id: findings_have_locations
        assertion: "len(location_per_finding) == len(findings_list)"  # cross-field
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
      type: route_to_navigator
      rationale: "Confidence below threshold means diagnosis is uncertain; clarify scope with user"
    validation_checks:
      - check_id: root_cause_confidence_threshold
        assertion: "confidence >= 0.8"  # cardinality
        check_type: deterministic
        failure_action: route_to_navigator
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
      type: route_to_navigator
      rationale: "Incomplete audit means extraction priority is unsafe to derive"
    validation_checks:
      - check_id: readiness_classifications_valid
        assertion: "decomposition_readiness_per_service[].readiness matches enum: [ready, needs_work, tightly_coupled, unknown]"  # enum-membership
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
      rationale: "Stack decision needs language/framework/deployment_target; correctable in single retry"
    validation_checks:
      - check_id: stack_decision_language_present
        assertion: "stack_decision.language is non-null"  # field-presence
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev2
      - check_id: stack_decision_framework_present
        assertion: "stack_decision.framework is non-null"  # field-presence
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev2
      - check_id: stack_decision_target_present
        assertion: "stack_decision.deployment_target is non-null"  # field-presence
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev2

  - id: hc-orchestrator-to-verifier
    # Added 7.4.0 (SPEC 1 D4). Contract A — orchestrator dispatches to the
    # adversarial-critic variant when the producing mode emits evaluative+
    # output or the active chain reaches 3+ modes. response_schema field
    # (new on Module 04 handoff_contract entity, v7.3.0) declares the
    # verifier's return shape — verdict + evidence_ref + deterministic_checks
    # + optional llm_findings. fallback_path is escalate_to_user; silent-pass
    # is NEVER allowed (verifier crash/timeout surfaces partial state).
    # Tool grants beyond [Read, Glob, Grep] gated by Module 20
    # verifier_tool_tier_policy (HIGH tier).
    source_mode: orchestrator
    source_variant: null
    target_mode: critic
    target_variant: adversarial
    trigger:
      type: automatic
      condition: |
        Producing mode (Builder | Strategist | Expert) emits output with
        decision_type_exercised ∈ {evaluative_judgment, predictive_judgment, novel_judgment},
        OR active chain has ≥3 modes
      chain_pattern_reference: "auto-adversarial"
    payload_schema:
      fields:
        - {name: artifact_under_test, type: pointer, required: true,
           description: "Resolvable reference (Beads attachment | file path | message-pass handle)
                         — NOT the producing mode's context or reasoning trail"}
        - {name: producing_mode, type: string, required: true,
           validation: "enum: [builder, strategist, expert]"}
        - {name: decision_type_exercised, type: string, required: true,
           validation: "enum: [reckoning, evaluative_judgment, predictive_judgment, novel_judgment]"}
        - {name: chain_position, type: integer, required: true,
           description: "Position in current chain — verifier rejects calls on reckoning-level output"}
        - {name: revision_cycle_count, type: integer, required: true,
           validation: "max: 1 (per Module 07 loop_exit_protocol)"}
        - {name: tool_grants, type: array, required: true,
           description: "Subset of: [test-runner, datastore-read-only, staging-http].
                         Empty array means deterministic-checks-only fallback.
                         Module 20 verifier_tool_tier_policy gates non-empty grants to HIGH tier."}
    response_schema:                              # NEW field on contract entity — Module 04 v7.3.0
      fields:
        - {name: verdict, type: string, required: true, validation: "enum: [pass, fail]"}
        - {name: evidence_ref, type: pointer, required: true,
           description: "Resolvable handle, NOT prose"}
        - {name: deterministic_checks, type: array, required: true,
           description: "[{name, result}] — run before LLM judgment"}
        - {name: llm_findings, type: array, required: false,
           description: "[{severity, location, claim}] — empty on clean pass"}
    fallback_path:
      type: escalate_to_user
      rationale: "Verifier crash/timeout/unavailable → orchestrator escalates with partial state.
                  Silent-pass is NEVER allowed."
    validation_checks:
      - check_id: artifact_under_test_resolves
        assertion: "artifact_under_test is non-null"  # field-presence (canonical form)
        check_type: deterministic
        failure_action: escalate_to_user
        failure_severity: Sev1
      - check_id: decision_type_exercised_gates_firing
        assertion: "decision_type_exercised matches enum: [evaluative_judgment, predictive_judgment, novel_judgment]"  # enum-membership
        check_type: deterministic
        failure_action: skip_verification
        failure_severity: Sev3
      - check_id: revision_cycle_within_limit
        assertion: "revision_cycle_count <= 1"  # cardinality
        check_type: deterministic
        failure_action: escalate_to_user
        failure_severity: Sev1
      - check_id: response_schema_conforms
        assertion: "verifier_response validates against response_schema"  # schema-conformance
        check_type: deterministic
        failure_action: escalate_to_user
        failure_severity: Sev1
      - check_id: evidence_ref_resolves
        assertion: "evidence_ref is non-null"  # field-presence
        check_type: deterministic
        failure_action: treat_as_verdict_fail
        failure_severity: Sev2

  - id: hc-runtime-to-accretion-gate
    # Added 7.3.0 (SPEC 4 D3). Contract B — [project] loop runtime emits
    # accretion candidates with provenance metadata to Module 21 step_3d
    # provenance gate. The 9th registry entry; SPEC 1 added the 10th
    # (hc-orchestrator-to-verifier) in wave 2.
    source_mode: [project]_runtime
    source_variant: null
    target_mode: accretion_gate          # Module 21 step_3d
    target_variant: null
    trigger:
      type: automatic
      condition: "Loop run completes AND produces accretion candidate at evaluative+ depth"
      chain_pattern_reference: "runtime-accretion-emission"
    payload_schema:
      fields:
        - {name: candidate_body, type: object, required: true,
           description: "Per Module 21 accretion_candidate schema"}
        - {name: provenance, type: object, required: true}
        - {name: provenance.loop_id, type: string, required: true}
        - {name: provenance.run_id, type: string, required: true}
        - {name: provenance.decision_tag, type: string, required: true,
           validation: "enum: [reckoning, evaluative_judgment, predictive_judgment, novel_judgment]"}
        - {name: provenance.source_mode, type: string, required: true}
        - {name: provenance.signals, type: array, required: false}
    fallback_path:
      type: surface_for_human_review
      rationale: "Incomplete provenance → user decides destination. Never silent-promote
                  to cross-cutting tier. Never silent-file to project tier when decision
                  type is novel/predictive."
    validation_checks:
      - check_id: provenance_present
        assertion: "provenance is non-null AND provenance.decision_tag is non-null"  # field-presence
        check_type: deterministic
        failure_action: surface_for_human_review
        failure_severity: Sev1
      - check_id: provenance_decision_tag_enum
        assertion: "provenance.decision_tag matches enum"  # enum-membership
        check_type: deterministic
        failure_action: surface_for_human_review
        failure_severity: Sev1
      - check_id: candidate_body_schema_conforms
        assertion: "candidate_body validates against Module 21 accretion_candidate schema"  # schema-validation
        check_type: deterministic
        failure_action: surface_for_human_review
        failure_severity: Sev2

  - id: hc-expert-to-strategist
    # Added 7.5.0 (Contract C). Expert→Strategist edge used in:
    # moat analysis ("Design for competitive moat"),
    # ML-infra chain (Expert hardware → Strategist phasing),
    # API security chain (Expert findings → Strategist prioritization — Example 4).
    # Carries the full Expert output payload; Strategist reads decision_type_exercised
    # to gauge depth of trade-off analysis needed.
    source_mode: expert
    source_variant: any
    target_mode: strategist
    target_variant: null
    trigger:
      type: chain_pattern
      condition: "Expert → Strategist chain pattern active (moat, ML-infra, security-prioritization)"
      chain_pattern_reference: "expert-to-strategist"
    payload_schema:
      fields:
        - {name: first_order_findings, type: array, required: true}
        - {name: adversarial_depth, type: object, required: true}
        - {name: design_implications, type: array, required: true}
        - {name: decision_type_exercised, type: string, required: true,
           validation: "enum: [reckoning, evaluative_judgment, predictive_judgment, novel_judgment]"}
    fallback_path:
      type: route_to_navigator
      rationale: "Missing required field indicates upstream Expert spec failure; Navigator clarifies with user"
    validation_checks:
      - check_id: decision_type_exercised_present
        assertion: "decision_type_exercised is non-null"  # field-presence
        check_type: deterministic
        failure_action: route_to_navigator
        failure_severity: Sev1
      - check_id: decision_type_exercised_enum
        assertion: "decision_type_exercised matches enum: [reckoning, evaluative_judgment, predictive_judgment, novel_judgment]"  # enum-membership
        check_type: deterministic
        failure_action: route_to_navigator
        failure_severity: Sev1
      - check_id: adversarial_depth_present
        assertion: "adversarial_depth is non-null"  # field-presence
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev2

  - id: hc-expert-research-to-expert-regular
    # Added 7.5.0 (Contract D). Expert research→Expert regular edge — the
    # 7.9.0 "ground this claim with research, then analyze it" chain.
    # Research variant is the source-retrieval layer; regular variant adds
    # adversarial depth. degraded flag MUST be visible to downstream so
    # Expert regular knows the grounding ceiling is 0.6 (artificial, not earned).
    # disposition enum constrains what downstream modes can recommend.
    source_mode: expert
    source_variant: research
    target_mode: expert
    target_variant: regular
    trigger:
      type: chain_pattern
      condition: "Expert research → Expert regular chain ('ground claim then analyze')"
      chain_pattern_reference: "expert-research-to-expert-regular"
    payload_schema:
      fields:
        - {name: grounded_evidence_set, type: object, required: true,
           description: "Per M05 output_format: grounded_evidence_set schema"}
        - {name: grounded_evidence_set.claims, type: array, required: true,
           description: "Per-claim entries; each must carry grounding_score and source_refs"}
        - {name: grounded_evidence_set.composite_grounding, type: float, required: true,
           validation: "range: [0.0, 1.0]"}
        - {name: grounded_evidence_set.degraded, type: boolean, required: true,
           description: "true when MCP unavailable and WebSearch fallback was used"}
        - {name: grounded_evidence_set.disposition, type: string, required: true,
           validation: "enum: [ship, soften, rebuild] — 'ship' only valid when degraded=false"}
    fallback_path:
      type: route_to_navigator
      rationale: "Missing grounded_evidence_set means research retrieval failed; Navigator clarifies with user before proceeding to analysis"
    validation_checks:
      - check_id: grounded_evidence_set_present
        assertion: "grounded_evidence_set is non-null"  # field-presence
        check_type: deterministic
        failure_action: route_to_navigator
        failure_severity: Sev1
      - check_id: degraded_ceiling_visible
        assertion: "grounded_evidence_set.degraded is non-null"  # field-presence
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev1
      - check_id: per_claim_grounding_present
        assertion: "grounded_evidence_set.claims[].grounding_score is non-null for each entry"  # cardinality
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev2

  - id: hc-expert-research-to-builder
    # Added 7.5.0 (Contract E). Expert research→Builder edge — the
    # 7.9.0 "find evidence for X and build a report" chain.
    # Same grounded_evidence_set payload as Contract D plus a report_structure_directive
    # so Builder knows the expected output shape. degraded flag propagates to Builder
    # which must apply M21 at_threshold_degraded gate if grounding==0.6 AND degraded.
    source_mode: expert
    source_variant: research
    target_mode: builder
    target_variant: null
    trigger:
      type: chain_pattern
      condition: "Expert research → Builder chain ('find evidence and build report')"
      chain_pattern_reference: "expert-research-to-builder"
    payload_schema:
      fields:
        - {name: grounded_evidence_set, type: object, required: true,
           description: "Per M05 output_format: grounded_evidence_set schema"}
        - {name: grounded_evidence_set.claims, type: array, required: true}
        - {name: grounded_evidence_set.composite_grounding, type: float, required: true,
           validation: "range: [0.0, 1.0]"}
        - {name: grounded_evidence_set.degraded, type: boolean, required: true}
        - {name: grounded_evidence_set.disposition, type: string, required: true,
           validation: "enum: [ship, soften, rebuild] — 'ship' only valid when degraded=false"}
        - {name: report_structure_directive, type: object, required: false,
           description: "Optional: sections, format, audience from upstream request"}
    fallback_path:
      type: route_to_navigator
      rationale: "Missing grounded_evidence_set means research retrieval failed; Builder cannot produce a grounded report without evidence"
    validation_checks:
      - check_id: grounded_evidence_set_present
        assertion: "grounded_evidence_set is non-null"  # field-presence
        check_type: deterministic
        failure_action: route_to_navigator
        failure_severity: Sev1
      - check_id: degraded_ceiling_visible
        assertion: "grounded_evidence_set.degraded is non-null"  # field-presence
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev1
      - check_id: composite_grounding_present
        assertion: "grounded_evidence_set.composite_grounding is non-null"  # field-presence
        check_type: deterministic
        failure_action: retry_with_repair
        failure_severity: Sev2
      - check_id: degraded_ship_prohibited
        assertion: "NOT (grounded_evidence_set.degraded == true AND grounded_evidence_set.disposition == 'ship')"  # cross-field
        check_type: deterministic
        failure_action: route_to_navigator
        failure_severity: Sev1

# Validation: registry must have exactly 13 entries (post-7.5.0 wave: 10 prior + C/D/E added 7.5.0); ids unique; every entry validates against Module 04 handoff_contract entity schema. Contract A (hc-orchestrator-to-verifier) added 7.4.0, Contract B (hc-runtime-to-accretion-gate) added 7.3.0, Contracts C/D/E (hc-expert-to-strategist, hc-expert-research-to-expert-regular, hc-expert-research-to-builder) added 7.5.0.
```

---

## The Four Pattern Vocabulary

Sequential, Parallel, Hierarchical, and Consensus remain as **vocabulary for describing what emerged** from dependency analysis. They are not a selection menu.

### Sequential

```
A → B → C → output
```

**Emerges when:** The dependency graph shows a single chain with no parallelizable clusters.

**Rules:**
- Each agent completes fully before handoff
- Output of A becomes input of B
- Clear completion criteria at each step

### Parallel

```
      ┌→ A ─┐
input ├→ B ─┤→ Aggregator → output
      └→ C ─┘
```

**Emerges when:** The dependency graph shows a cluster of tasks with no hard dependencies between them, converging at a coordination point.

**Rules:**
- All parallel agents receive the same input (or outputs from prior sequential steps)
- Agents work independently
- Aggregator resolves differences at the coordination point

### Hierarchical

```
       Coordinator
      /     |     \
     A      B      C
```

**Emerges when:** The dependency graph is complex enough to require dynamic routing, iteration, or runtime decisions about which subtasks to execute.

**Rules:**
- Coordinator has full visibility of the graph
- Can reassign, iterate, or terminate based on intermediate results
- State lives with Coordinator

### Consensus

```
[A, B, C] ↔ deliberation ↔ unified output
```

**Emerges when:** The dependency graph shows a coordination point where multiple perspectives must be reconciled before proceeding, and the reconciliation itself is iterative.

**Rules:**
- Agents share and critique each other's outputs
- Explicit stopping condition
- Document reasoning, not just conclusion

### Hybrid Patterns

Most real workflows are hybrids. The dependency graph naturally produces them.

```yaml
hybrid_examples:
  - name: "Parallel-then-sequential"
    description: "Steps 1-3 parallel, step 4 aggregates, steps 5-6 sequential"
    emerges_when: Independent analysis followed by synthesis followed by action
    
  - name: "Sequential-with-parallel-validation"
    description: "Build sequentially, validate in parallel, revise sequentially"
    emerges_when: Creation is sequential but quality checks are independent
    
  - name: "Hierarchical-with-consensus-gates"
    description: "Coordinator manages workflow with consensus required at key decision points"
    emerges_when: Complex workflow with high-stakes decisions requiring agreement
```

---

## Common Mode Coordination Flows

### Creation with Validation

```
Builder → [Critic, Expert, Debugger] (parallel) → Builder (if revisions) → Deploy
```

```yaml
flow:
  name: creation_with_validation
  derived_from: dependency_graph
  
  dependencies:
    Builder → Critic (hard: Critic needs spec)
    Builder → Expert (hard: Expert needs spec for domain check)
    Builder → Debugger (hard: Debugger needs spec for failure analysis)
    Critic → Builder_revise (hard: revision needs critique)
    Expert → Builder_revise (hard: revision needs domain feedback)
    Debugger → Builder_revise (hard: revision needs failure analysis)
    
  pattern: sequential → parallel → sequential
  
  coordination_point:
    at: Builder_revise
    aggregation: synthesize all three validation outputs
    conflict_resolution: Critic severity ranking takes precedence for prioritization
```

### Diagnosis with Strategic Fix

```
Debugger → Strategist → Builder
```

```yaml
flow:
  name: diagnosis_with_strategic_fix
  derived_from: dependency_graph
  
  dependencies:
    Debugger → Strategist (hard: strategy needs diagnosis)
    Strategist → Builder (hard: implementation needs strategic decision)
    
  pattern: sequential (simple chain)
```

### Pattern-Driven Agent Creation

```
[Strategist, Synthesizer] (parallel) → Builder → Critic → Deploy
```

```yaml
flow:
  name: pattern_driven_creation
  derived_from: dependency_graph
  
  dependencies:
    Strategist → Builder (hard: needs strategic context)
    Synthesizer → Builder (hard: needs patterns to apply)
    Builder → Critic (hard: needs spec to review)
    
  soft_dependencies:
    Strategist ⇢ Synthesizer (context improves pattern extraction)
    
  pattern: parallel start → sequential chain
```

---

## State Management

### Context Object

```yaml
coordination_context:
  session:
    id: [unique_session_id]
    started: [timestamp]
    current_step: [where in the dependency graph]
    dependency_graph: [the derived graph]
    modes_engaged: [list of modes used]
    
  user:
    expertise_level: beginner | intermediate | advanced
    stated_goals: [explicit requests]
    inferred_goals: [underlying needs]
    constraints: [limits mentioned]
    
  task:
    objective: [end goal]
    completed: [done subtasks]
    pending: [remaining subtasks]
    blockers: [current issues]
    critical_path: [longest dependency chain]
    
  decisions:
    - decision: [what was decided]
      by: [which agent]
      reasoning: [why]
      timestamp: [when]
      reversible: true | false
      
  artifacts:
    - artifact_id: [unique_id]
      type: specification | critique | diagnosis | strategy
      created_by: [agent_id]
      version: [current version]
      status: draft | reviewed | approved
```

### Handoff Protocol

Every handoff includes:

1. **What happened** — Agent's output/conclusion
2. **What was learned** — New information discovered
3. **What to do next** — Instruction for receiving agent
4. **What context carries forward** — Relevant state
5. **Position in dependency graph** — Where this handoff sits in the overall flow

```yaml
handoff:
  from: [source_agent]
  to: [target_agent]
  
  what_happened:
    action_taken: [what source agent did]
    result: [outcome]
    confidence: [how sure]
    
  what_was_learned:
    new_information: [discoveries]
    updated_understanding: [changed beliefs]
    
  instruction:
    task: [specific action for target]
    constraints: [limits on target's work]
    expected_output: [what to return]
    
  graph_position:
    step: [current step in dependency graph]
    completed_dependencies: [what has been resolved]
    remaining_dependencies: [what still needs to happen]
    next_coordination_point: [where outputs will converge]
    
  context:
    [preserved context object]
```

---

## Dual Fingerprinting for Critic ↔ Builder Loop

Track two fingerprints separately throughout the revision cycle:

- **`state_fingerprint`**: hash of the artifact being reviewed (the spec/code/plan). Changes when Builder revises.
- **`dispatch_fingerprint`**: hash of the finding set dispatched to Builder. Changes when Critic finds new issues.

**Dispatch rules:**
- On each Critic pass, compute `dispatch_fingerprint` of current findings
- **Delta rule:** if `current_findings_fingerprint != dispatch_fingerprint` → new or changed findings exist → dispatch only the delta to Builder, not the full set
- If `dispatch_fingerprint` matches previous pass → no new findings → terminate the loop
- Builder only revises sections touched by dispatched findings

**Benefit:** Prevents Builder from re-addressing already-fixed findings. Reduces loop iterations. Each pass Builder sees only what's genuinely new.

**Why dual fingerprints:** A single fingerprint on the artifact alone can't distinguish "Builder revised but Critic found the same issues again" from "everything is resolved." Tracking dispatch separately catches loops where the artifact changes but the problems persist.

**6.6.1 alignment:** This pattern operates within the `loop_exit_protocol` defined in Module 07 — max one automatic revision cycle, then escalate. Dual fingerprinting determines *what* to dispatch each cycle; loop_exit_protocol determines *when* to stop cycling.

---

## Automatic Adversarial Verification (6.1)

Mode chains that produce evaluative or higher output automatically include an adversarial Critic pass. This is not optional for qualifying chains.

```yaml
verification_required:
  flag: true
  
  qualifying_chains:
    - Any chain that produces a specification (Builder output)
    - Any chain that produces a strategy recommendation (Strategist output)
    - Any chain that produces an ODS organizational profile
    - Any chain of 3+ modes (compound error risk regardless of output type)
    
  verification_protocol:
    agent: Critic (adversarial variant)
    framing: "Your goal is to find the failure mode that the producing agent missed. Assume the output has at least one significant flaw."
    scope: Final chain output only (not intermediate handoffs)
    severity_filter: Report findings at severity 2+ only
    
  on_finding:
    severity_2_plus: Flag in output. Escalate risk tier per Module 20.
    no_findings: Record clean pass. Continue to delivery.
    
  yield_tracking:
    metric: "Percentage of adversarial passes that surface severity 2+ findings"
    healthy_range: 20% – 80%
    below_20: "Adversarial prompting too soft — tighten framing"
    above_80: "Artifact quality too low — flag for rebuild rather than review"
    
  skip_conditions:
    - Single-mode reckoning output (no chain, no judgment)
    - Two-mode chain where terminal output is a reckoning
    - User explicitly requests skipping verification ("just give me the draft")
```

---

## Capability Restrictions in Chains (6.1)

When modes operate as steps in a chain, each step has restricted capabilities. This prevents a sub-agent from exceeding its mandate.

```yaml
chain_capability_restrictions:
  principle: "Each mode in a chain operates with minimum required capabilities."
  
  per_mode:
    navigator:
      in_chain_role: "Route or disambiguate only"
      can_read: [user_request, routing_index]
      can_write: [routing_decision]
      cannot: [create artifacts, make decisions, produce final output]
      
    builder:
      in_chain_role: "Create artifacts within assigned scope"
      can_read: [all prior chain outputs, routing_index, patterns]
      can_write: [specification_draft, design_decisions]
      cannot: [modify other modes' outputs, approve own output]
      
    critic:
      in_chain_role: "Review artifacts — read-only on source"
      can_read: [artifact_under_review, all chain context]
      can_write: [critique_output, severity_assessments]
      cannot: [modify the source artifact]
      
    expert:
      in_chain_role: "Analyze — output findings only"
      can_read: [artifact_under_analysis, domain context]
      can_write: [analysis_output, findings]
      cannot: [modify analyzed artifacts]
      
    debugger:
      in_chain_role: "Diagnose — full read, write diagnostic output only"
      can_read: [all session context, error data]
      can_write: [diagnostic_output, root_cause_report]
      cannot: [modify artifacts, implement fixes]
      
    strategist:
      in_chain_role: "Recommend — cannot implement"
      can_read: [all session context, constraints]
      can_write: [recommendation_output, trade_off_analysis]
      cannot: [implement recommendations, modify artifacts]
      
    synthesizer:
      in_chain_role: "Extract patterns — read-only on examples"
      can_read: [examples, session context]
      can_write: [pattern_output, anti_patterns]
      cannot: [modify source examples]
      
    calibrator:
      in_chain_role: "Generate config — cannot deploy"
      can_read: [project context, stack requirements]
      can_write: [configuration_output]
      cannot: [deploy configurations]
      
  enforcement:
    - Orchestrator validates each step's output against capability profile
    - Cross-mode modification goes through orchestrator, never direct
    - Capability violation: block action, log, continue with warning
    
  reference: "Full capability profiles in 20_Permission_Model.md"
```

---

## Mode Transition Cost Heuristic (6.1)

Mode switches have a cost — they invalidate cached context and load new instructions. Factor this into chaining decisions.

```yaml
mode_transition_cost:
  principle: "A mode switch that invalidates the prompt cache should deliver proportional value."
  
  cost_factors:
    context_reload: "New mode instructions loaded into dynamic zone"
    state_swap: "Tier 2 state saved/loaded (Module 19)"
    cache_invalidation: "Dynamic zone change breaks cache suffix"
    
  decision_heuristic:
    - If the next mode's contribution is < 20% of total chain value, handle inline instead
    - If two modes have overlapping capabilities for this task, use the already-active one
    - If a Critic pass would add only formatting-level findings, skip adversarial verification
    
  examples:
    high_value_switch: "Builder → Critic: Specification review catches structural issues. Switch justified."
    low_value_switch: "Expert → Strategist for a single trivial prioritization. Handle inline."
    skip_switch: "Builder output is a simple template fill. Auto-verification would yield only low-severity findings. Skip."
```

---

## Spec Drift Checkpoint (3+ Mode Chains)

For chains of 3 or more modes, insert a spec re-validation step between mode 2 and mode 3:

**Checkpoint protocol:**
1. Extract original goal from the first substantive user message in the chain (the intent anchor)
2. Summarize what modes 1 and 2 have produced (trajectory)
3. Compare trajectory against original goal:
   - **Aligned** → proceed silently (no output, invisible)
   - **Drifted** → surface before launching mode 3:

```
Spec Checkpoint:
Original goal: [verbatim from chain start]
Current trajectory: [what modes 1-2 produced]
Drift detected: [describe the divergence]
Proposed correction: [what to adjust before mode 3]
```

**User-initiated pivots vs. model drift:**
- If the user explicitly changed scope mid-chain → update the locked intent anchor (this is intentional)
- If the trajectory diverged without user input → this is model drift → surface and correct

**Why between mode 2 and mode 3:** Mode 3 is typically the output-producing mode (Builder, Strategist). Catching drift before mode 3 prevents generating a complete artifact for the wrong goal. Catching it after mode 1 adds overhead before any meaningful output exists.

---

## Conflict Resolution

When agents disagree at coordination points:

### Resolution Matrix

| Conflict Type | Resolution Strategy | Authority |
|---------------|---------------------|-----------|
| Factual disagreement | Check sources, weight by expertise | Expert |
| Priority disagreement | Defer to Coordinator or user | Strategist |
| Approach disagreement | Run both if feasible, compare | Synthesizer |
| Scope disagreement | Clarify with user | Navigator |
| Quality disagreement | Critic severity framework | Critic |
| Strategic disagreement | Trade-off analysis | Strategist |
| Diagnosis disagreement | Additional evidence required | Debugger |

### Resolution Protocol

```yaml
conflict_resolution:
  detection:
    trigger: Outputs from parallel agents contradict or are incompatible at coordination point
    
  process:
    1. Classify conflict type (factual / priority / approach / scope / quality / strategic / diagnostic)
    2. Route to authority agent for resolution
    3. If authority agent is one of the conflicting agents, escalate to Coordinator or user
    4. Document resolution reasoning
    5. Update dependency graph if conflict reveals new dependencies
```

---

## Integration with KF-2 (Metacognitive Monitor)

Coordinator monitors agent execution in real-time via the Metacognitive Monitor.

```yaml
monitor_integration:
  trigger: During any coordinated workflow execution
  
  capabilities:
    - Detect when an agent is stuck (circular reasoning, context overflow)
    - Receive intervention signals (COMPRESS_CONTEXT, SWITCH_STRATEGY, ESCALATE)
    - Reassign subtasks when agent fails
    - Interrupt and redirect based on monitor signals
    
  escalation_path:
    monitor_detects_failure → Coordinator receives signal → 
    Coordinator reassigns or terminates subtask → 
    Workflow continues with fallback plan
```

## Integration with KF-7 (Salience Allocation)

When multiple agents compete for resources, Coordinator uses salience scoring instead of static priority.

```yaml
salience_integration:
  trigger: Resource contention between agents in parallel execution
  
  application:
    - Compute salience for each competing agent's subtask
    - Highest salience wins resource allocation
    - Starvation prevention: minimum allocation floor for all queued subtasks
    - Log allocation decisions for post-workflow analysis
```

---

## Communication Protocol

Standard message format between agents:

```yaml
message:
  id: [unique_message_id]
  timestamp: [iso_datetime]
  
  routing:
    from: [source_agent_id]
    to: [target_agent_id]
    conversation_id: [thread tracker]
    graph_position: [step in dependency graph]
    
  type: request | response | notification | error
  
  content:
    action: [what to do (for requests)]
    result: [what was done (for responses)]
    data: [relevant payload]
    
  metadata:
    priority: normal | high | urgent
    timeout: [seconds]
    retry_policy: none | once | exponential
    mode: [current mode]
    decision_type: reckoning | evaluative | predictive | novel
```

---

## Example: Full-Cycle Agent Development

**Task:** Create, validate, and deploy a new agent with quality assurance.

**Step 1: Enumerate subtasks**
```
A: Assess strategic context (Strategist)
B: Extract applicable patterns (Synthesizer)
C: Create specification (Builder)
D: Structural review (Critic)
E: Failure mode analysis (Debugger)
F: Domain validation (Expert)
G: Revise specification (Builder)
H: Final approval
```

**Step 2-3: Map dependencies**
```
Hard: A → C, B → C, C → D, C → E, C → F, D → G, E → G, F → G, G → H
Soft: A ⇢ B
```

**Step 4: Draw graph**
```
    A ──┐
        ├──→ C ──→ ┌ D ─┐
    B ──┘           │ E ─┤──→ G ──→ H
                    └ F ─┘
```

**Step 5: Parallel clusters**
```
Cluster 1: {A, B} — no hard deps between them
Cluster 2: {D, E, F} — no hard deps between them
```

**Step 6: Sequential chains**
```
Critical path: A → C → D → G → H (or A → C → E → G → H, or A → C → F → G → H)
All paths through C and G are equally critical.
```

**Step 7: Coordination points**
```
C: Receives from A and B (must aggregate before proceeding)
G: Receives from D, E, and F (must aggregate all validation feedback)
```

**Step 8: Derived pattern**
```
Parallel(A,B) → Sequential(C) → Parallel(D,E,F) → Sequential(G) → Sequential(H)
```

This is a hybrid pattern — not forced into one taxonomy entry.

---

## Next Steps

1. **Map your workflow's dependencies** → Use the decomposition protocol
2. **Derive the pattern** → Read the graph, don't select from a menu
3. **Define coordination points** → Where do outputs converge?
4. **Plan conflict resolution** → How will disagreements at coordination points be handled?
5. **Design handoffs** → Customize context for your domain
6. **Build agents** → `02_Builder_Agent.md` for each specialist
7. **Test the full flow** → Simulate the complete dependency graph

---

## Naming Convention — `formula` (7.0.1)

The term `formula` in KF refers exclusively to **mode-chain recipes** — TOML or YAML definitions of multi-mode workflows with `[[steps]]`, `mode`, `depends_on`, and `condition` fields. Example: `build-validate.formula.toml` describing `@builder → @critic`.

Downstream agents that implement workflow recipes for non-mode workflows (e.g., data-pipeline recipes, watch-pattern recipes, scrape-diff-notify recipes) MUST NOT use `formula`. Recommended alternatives: `recipe`, `playbook`, `pattern`, `workflow`. The distinction matters because:

1. KF formulas resolve to mode chains (orchestrator-aware)
2. Non-KF recipes resolve to action sequences (orchestrator-blind)
3. Loaders, registries, and lookup paths must remain non-overlapping

If a downstream implementation has already shipped with `formula` in another sense, KF agents should treat that namespace as foreign and use the fully-qualified path (`<project>/formulas/`) when referencing it. The KF formula namespace is always `kf/formulas/` or equivalent KF-owned path.

---

## Related Modules

- `01_Navigator_Agent.md` — Disambiguation before coordination begins
- `02_Builder_Agent.md` — Creating specialist agents
- `04_Specification_Templates.md` — Standard formats for coordination configs
- `07_Critic_Agent.md` — Quality validation at coordination points + adversarial verification in chains
- `08_Synthesizer_Agent.md` — Pattern extraction across agent teams
- `09_Debugger_Agent.md` — Diagnosis within coordinated systems
- `10_Strategist_Agent.md` — Strategic decisions for coordination
- `11_Calibrator_Agent.md` — Project setup flows
- `14_Metacognitive_Monitor.md` — Real-time agent failure detection during coordination
- `18_Salience_Allocation.md` — Dynamic resource allocation for competing agents
- `19_Memory_Architecture.md` — (6.1) Routing index for handoff context preservation
- `20_Permission_Model.md` — (6.1) Chain risk escalation and capability restriction enforcement
