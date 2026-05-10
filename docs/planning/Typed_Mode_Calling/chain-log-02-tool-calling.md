# Chain-Log 02 — Strategist Phase

## Cascade Metadata

```yaml
cascade:
  stage: 2
  phase: Strategist
  prior_phase: ERA (chain-log-01-tool-calling.md)
  produces_for: chain-log-03-tool-calling.md (Builder phase)
  cascade_id: tool-calling-architecture-audit
  track: C
  target_version: KF 7.1.0
  decision_type: evaluative_judgment
  date: 2026-05-08
```

## Carry-Forward from ERA

**Pre-flight gate:** PASS. Track C remains valid; F1 refines metric scope rather than invalidating it.

**Findings to remediate:**
- F1 (Sev 1) — mode-label collisions (Critic 4 variants, Expert 4 variants)
- F2 (Sev 2) — handoff contracts not formalized (8 edges)
- F3 (Sev 2) — `decision_type_exercised` not on Expert output schema
- F4 (Sev 2) — no routing-decision logging
- F5/F6 absorbed into F1/F2 remediation; F7 deferred to Stage 3 documentation pass

**Sequencing constraint:** F1 remediation must precede metric #10 specification. F4 remediation must precede metric #10 measurement.

## 1. Atomic Implementable Units

```yaml
atomic_units:
  - id: U1
    purpose: Define trigger_disambiguator entity in Module 04
    description: |
      Formal entity for resolving cases where a trigger phrase activates multiple
      candidate modes or variants. Predicates: output_type_difference (existing
      Navigator predicate), domain_specificity, chain_context, user_disambiguation.
    affected_modules:
      - Module 04 (new entity definition)
    reversibility: single_commit_revert
    dependencies: none
    decision_type: evaluative_judgment
    grounding: F1 + F6 (mode-label collisions + trigger phrase overlaps)

  - id: U2
    purpose: Define Handoff_Contract entity in Module 04
    description: |
      Formal entity with required fields: source_mode, source_variant, target_mode,
      target_variant, payload_schema, fallback_path, validation_checks (≥1 deterministic
      check). Resolves F2 root cause and F5 naming inconsistency.
    affected_modules:
      - Module 04 (new entity definition)
      - Module 04 Usage Notes table (rename "Handoff" → "Handoff Contract")
    reversibility: single_commit_revert
    dependencies: none
    decision_type: evaluative_judgment
    grounding: F2 + F5

  - id: U3
    purpose: Add variants[] field to Critic agent spec (Module 07)
    description: |
      Formalize the 4 Critic variants (regular, linter, audit, adversarial) with
      trigger_phrases, output_format, typical_chain_position per variant.
    affected_modules:
      - Module 07 (Critic agent spec)
    reversibility: single_commit_revert
    dependencies: U1 (variants reference trigger_disambiguator predicates)
    decision_type: evaluative_judgment
    grounding: F1

  - id: U4
    purpose: Add variants[] field + decision_type_exercised required output to Expert agent spec (Module 05)
    description: |
      Combined patch — both touch Module 05. Formalize 4 Expert variants (regular,
      infrastructure, ml_infrastructure, era). Add decision_type_exercised as required
      output field with enum [reckoning, evaluative_judgment, predictive_judgment,
      novel_judgment].
    affected_modules:
      - Module 05 (Expert agent spec)
    reversibility: single_commit_revert (multi-line edit, single semantic change)
    dependencies: U1 (variants reference trigger_disambiguator predicates)
    decision_type: evaluative_judgment
    grounding: F1 + F3

  - id: U5
    purpose: Add routing_decision_log hook to Module 19
    description: |
      New schema for logging every mode activation: timestamp, turn, request_text
      (truncated), candidate_modes, selected_mode, selected_variant, trigger_phrase_matched,
      predicate_used, re_routed flag, re_route_reason. Retention: rolling 1000 entries
      + permanent re-route archive. Schema_version 1.0.
    affected_modules:
      - Module 19 (new section: Routing Decision Log)
    reversibility: single_commit_revert
    dependencies: none (additive, parallel to routing_index_schema)
    decision_type: evaluative_judgment
    grounding: F4

  - id: U6
    purpose: Add metric #10 (mode_selection_accuracy) to Module 16
    description: |
      Metric specification with re-routing rate as primary measurement (deterministic,
      from U5 log) + adversarial sampling for periodic calibration. Variant-aware
      thresholds: 90% overall, 95% per-variant. Threshold breach actions specified.
    affected_modules:
      - Module 16 (new metric definition)
      - Module 16 Corrective Action Summary table (new row)
    reversibility: single_commit_revert
    dependencies: U1 (predicate types referenced in corrective actions), U5 (log is data source)
    decision_type: evaluative_judgment
    grounding: F1 + F4 + Track C deliverable requirement

  - id: U7
    purpose: Register handoff_contract_instance for each of 8 active handoff edges
    description: |
      Per-edge registration in Module 03 (Coordination Patterns) with payload_schema,
      fallback_path, validation_checks. 8 edges:
        - Builder → Critic (auto-verify)
        - Expert → Builder
        - Strategist → Builder
        - Synthesizer → Builder
        - Critic → Builder (revision)
        - Debugger → Strategist
        - Critic (audit) → Strategist
        - Strategist → Calibrator
    affected_modules:
      - Module 03 (Coordination Patterns) — new section: Handoff Contract Registry
    reversibility: single_commit_revert (entire registry in one commit)
    dependencies: U2 (entity definition), U3 (Critic variants), U4 (Expert variants)
    decision_type: evaluative_judgment
    grounding: F2

  - id: U8
    purpose: Orchestrator prompt update to write routing_decision_log entries
    description: |
      Implementation commit (impl_commit) corresponding to U5 spec. Adds explicit
      "after every mode activation, write a routing_decision_log entry with all required
      fields" behavior to Module 00 static zone.
    affected_modules:
      - Module 00 (orchestrator) — new behavior in Static Zone routing rules
    reversibility: single_commit_revert
    dependencies: U5 (log schema must exist)
    decision_type: reckoning (mechanical — write log per schema)
    grounding: U5 spec

  - id: U9
    purpose: Orchestrator prompt update to act on metric #10 thresholds
    description: |
      Implementation commit (impl_commit) corresponding to U6 spec. Adds metric #10
      threshold-breach actions to Module 00 (e.g., "if mode_selection_accuracy < 90%
      over rolling window, trigger Module 13 review").
    affected_modules:
      - Module 00 (orchestrator) — extend Operational Bounds awareness
    reversibility: single_commit_revert
    dependencies: U6 (metric must exist)
    decision_type: reckoning (mechanical — act per threshold)
    grounding: U6 spec
```

**Total atomic units: 9.** Within Track C ~10-task ceiling.

## 2. Sequencing Recommendation

```yaml
sequencing:
  serial_groups:
    group_1:  # Foundation — entities and infrastructure
      parallel:
        - U1 (trigger_disambiguator)
        - U2 (Handoff_Contract entity)
        - U5 (routing_decision_log hook)

    group_2:  # Mode-level patches (depend on group_1)
      parallel:
        - U3 (Critic variants — depends on U1)
        - U4 (Expert variants + decision_type_exercised — depends on U1)

    group_3:  # Registration (depends on group_2)
      serial:
        - U7 (per-mode handoff registrations — depends on U2, U3, U4)

    group_4:  # Metric specification (depends on U1 + U5)
      serial:
        - U6 (metric #10 — depends on U1, U5)

    group_5:  # Orchestrator implementation (depends on group_3 + group_4)
      parallel:
        - U8 (log-writing behavior — depends on U5)
        - U9 (metric-acting behavior — depends on U6)

  total_serial_groups: 5
  parallelizable_within_group: yes for groups 1, 2, 5
  estimated_PR_scope: 9 atomic commits (well within single-PR territory; ~ 200-line spec diff)

  sequencing_justification: |
    U1, U2, U5 are independent foundation work — entity definitions and a new schema.
    U3, U4 depend on U1 because variants reference disambiguator predicates.
    U7 depends on U2 (entity) and U3/U4 (variant identifiers used in source_variant/target_variant).
    U6 depends on U1 (predicates referenced in corrective actions) and U5 (log is data source).
    U8/U9 are orchestrator behavior changes that consume the new spec entities.

    Spec-commit-before-impl-commit protocol enforced: U1–U7 are spec_commits, U8–U9 are impl_commits.
```

## 3. Mode-Selection Accuracy Metric (Module 16 #10)

### Definition

**Correct mode selection** = orchestrator routes a request to the (mode, variant) pair such that the resulting output meets the request's stated intent without requiring re-routing.

**Re-routing event** = either (a) Navigator activates after initial routing failed, (b) user explicitly redirects ("no, I meant Strategist not Builder"), or (c) Critic adversarial pass surfaces "wrong mode for this task" finding at Sev 2+.

**Variant-level correctness** is mandatory. Aggregate "Critic accuracy" without variant disaggregation is meaningless per F1.

### Measurement Protocol

```yaml
measurement_protocol:
  primary_measurement:
    type: deterministic
    formula: "1 - (re_routed_events / total_routing_events)"
    window: rolling 100 routing events
    data_source: Module 19 routing_decision_log
    rationale: |
      Re-routing rate is the most direct deterministic proxy. Available from log
      data without LLM judgment. Aligns with KF 7.0.0 "Deterministic first" principle.

  calibration_measurement:
    type: adversarial_sampling
    frequency: weekly
    sample_size: 20 randomly selected routing decisions
    method: |
      Sampled decisions reviewed by Critic adversarial variant against original
      request. Findings of "wrong mode for this task" or "wrong variant for this task"
      classified at Sev 2+ count as routing failures undetected by re-routing rate.
    rationale: |
      Some routing failures don't trigger re-routing — request gets answered by wrong
      mode and user accepts the lower-quality output. Adversarial sample catches these.
      Weekly cadence keeps cost bounded.

  calibration_adjustment:
    rule: |
      If adversarial-sample failure rate exceeds (1 - primary_measurement) by more
      than 5 percentage points, primary metric is under-counting. Trigger orchestrator
      prompt revision and re-baseline.
```

### Thresholds and Corrective Actions

```yaml
thresholds:
  overall_accuracy:
    healthy_range: ">= 90%"

    below_90:
      action: |
        - Trigger Module 13 (Decision Classification) review
        - Audit recent re_routed events for shared failure pattern
        - Consider trigger_disambiguator schema update (Module 04)
      severity: notification (chronic drift)

    below_80:
      action: |
        - ESCALATE
        - Halt new chain starts until calibration check completes
        - Surface specific re_routed events for human review
      severity: escalation

  per_variant_accuracy:
    healthy_range: ">= 95% per variant"

    below_95:
      action: |
        - Variant disambiguation is failing within mode label
        - Audit variant-level trigger phrases for overlap
        - Consider tightening domain_specificity predicate in trigger_disambiguator
      severity: notification

    below_85:
      action: |
        - Variant taxonomy is degraded
        - Trigger Module 04 trigger_disambiguator review
      severity: escalation

  calibration_drift:
    rule: "If calibration_adjustment fires (adversarial-sample failure > primary by >5pp), re-baseline within one week"
    severity: notification
```

### Storage Location

Module 16 metric #10 specification (full schema). Module 16 Corrective Action Summary table extended with two rows: "Mode selection accuracy < 90%" and "Variant accuracy < 95%."

### Grounding to ERA Findings

- **F1 (mode-label collisions):** directly addressed by per-variant disaggregation
- **F4 (no routing-decision logging):** addressed by U5 (log) being the data source
- **F2 (handoff contracts):** indirectly addressed — handoff failures produce re-routing events, captured in metric

## 4. Out-of-Scope Items (Rejected with Rationale)

```yaml
rejected_items:
  - item: typed_error_signals_per_mode
    rationale: |
      Per Stage 1 pressure-test resolution. Trigger condition is at handoff payload
      validation (F2 remediation introduces validation_checks per edge). Once handoff
      contracts are formalized, typed errors become natural extension. Separate cascade
      after this ships.
    deferred_to: separate cascade post-7.1.0

  - item: chain_step_parallelization
    rationale: |
      Per Stage 1 pressure-test resolution. Adversarial Critic + accretion check could
      run in parallel after Builder output. Marginal latency benefit (< 30s typical)
      vs complexity cost (parallel error handling, race conditions on routing_index
      writes). Skip.
    deferred_to: not planned

  - item: prompt_injection_defense_between_handoffs
    rationale: |
      Per Stage 1 pressure-test resolution. Trigger condition (first KF chain consuming
      external untrusted MemoryRouter content) not yet present. F2 remediation provides
      handoff payload validation infrastructure that prompt-injection defense will
      build on. Defer until trigger fires.
    deferred_to: when MemoryRouter routes external content into KF chains

  - item: module_25_era_agent_creation
    rationale: |
      F7 orphan reference. Module 25 listed as "optional — only if Module 05 ERA section
      exceeds ~200 lines." Decision deferred — current ERA section length not measured
      in this cascade. Stage 3 documentation pass.
    deferred_to: Stage 3 handoff documentation pass

  - item: module_03_naming_resolution
    rationale: |
      F7 orphan reference. "Coordinator" used inconsistently as mode name vs. patterns
      reference. Stage 3 documentation pass.
    deferred_to: Stage 3 handoff documentation pass
```

## 5. Decision Lock — Track C Selection Validation

```yaml
track_c_validation_post_era:
  validation_question: "After ERA findings, does Track C still produce highest-defensibility artifact?"

  evidence:
    - F1 surfaces a structural taxonomy problem invisible in Track A (metric only) — defensibility gain
    - F2 surfaces handoff contract gap invisible in Track A — defensibility gain
    - Track B (audit only) would leave F1/F2 open — embarrasses KF at audit time
    - Track C remediates both with single-commit-reversible patches and grounded metric — ships fixes + measurement

  conclusion: Track C confirmed. No track switch.

  defensibility_thesis: |
    Article principle 2 (tool definitions as contracts) is the single most direct
    architectural gap between KF orchestration and frontier-native orchestration
    capabilities. Frontier providers have native function-calling with formal schemas;
    KF mode handoffs have prose conventions. F2 remediation closes this gap with
    KF-native semantics (decision types, reversibility, auto-verify gates) that
    frontier-native orchestration does not provide. Demonstrates neuro-symbolic depth
    under self-reflection.
```

## 6. Output to Builder Phase

**Mandatory carry-forward:**
- 9 atomic units with full specification (above)
- Sequencing groups with dependency graph
- Metric #10 full specification (above) — Builder writes the YAML
- Out-of-scope items with rationale

**Builder must:**
- Verify each unit's affected modules against current Module 04, 16, 19, 20, 21 schemas before authoring patches (per constraint in Stage 2 prompt)
- Produce canonical KF YAML per Module 04 conventions
- Include ≥1 deterministic test per patch
- Include migration notes per affected module
- Pre-draft KF 7.1.0 changelog entries
- Produce Stage 3 handoff block (per schema in Stage 2 prompt)

**Decision type exercised by Strategist:** evaluative_judgment.
**Auto-verify gate:** triggers Critic adversarial pass at chain-log-04. Confirmed.

---

**Strategist phase complete. Handoff to Builder phase (chain-log-03).**
