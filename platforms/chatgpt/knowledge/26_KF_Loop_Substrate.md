# KF-LOOP Substrate

## Module Metadata

```yaml
module:
  title: KF-LOOP Substrate
  version: 1.2.0
  purpose: >
    Shared substrate for iterative self-improvement loops; formalizes evidence
    stratification (I1) and cross-iteration attempt memory (I2) so any KF loop
    has a convergence gradient and does not re-cover excluded ground
  topics: [iterative-convergence, loop-control, attempt-ledger, evidence-stratification, plateau-detection]
  contexts: [self-calibration, kb-health, pattern-extraction, grounding-loop, mode-selection-accuracy]
  difficulty: advanced
  related: [00_orchestrator, 03_coordination_patterns, 07_critic_agent, 14_metacognitive_monitor, 19_memory_architecture, 21_knowledge_accretion, 16_operational_bounds]
  added_in: "7.34"```

---

## The Problem This Patches

Iterative improvement loops in KF already exist at intra-session scope (Module 14 Check 1, Module 03 dual-fingerprint). The Clawber case study produced the empirical grounding event that exposed a gap: 23 consecutive loop failures from two root causes that no intra-session mechanism can prevent.

**I1 (signal):** A mixed evidence sample yields diagnosis on the statistical middle of a noisy distribution. In Clawber, the match API returned `opponent="unknown"` for historical matches. KF averaged three distinct opponents into one diagnosis and re-selected "ammo management" as the fix 17 of 21 iterations. The real failures were opponent-specific. The fix is not LLM judgment -- it is a deterministic `GROUP BY` on the dominant failure axis applied before any reasoning begins.

**I2 (memory):** Without a persisted, outcome-labeled, exclusion-constrained attempt ledger, an iterative loop has no exploration gradient. Each iteration started fresh in Clawber. The same hypothesis recurred with no record of its prior failure. The fix is a cross-iteration log that injects excluded hypothesis summaries into the reason stage context before the mode chain fires.

Both mechanisms exist in KF at intra-session scope. This module promotes them to iteration scope -- adding a persistence layer and a scope-aware detection window.

**Scope promotion, not reinvention.** Module 14 Check 1 hashes reasoning steps within a single session trace. Module 03 dual-fingerprint tracks dispatch state within one revision cycle. This module operates at the iteration level: each iteration is one full run of the loop cadence, potentially spanning a complete session. The two existing checks remain valid and complementary; this module extends their coverage upward one scope level.

---

## Two Invariants

Every KF-LOOP instance MUST satisfy both invariants. Satisfaction of one without the other is insufficient.

**I1 -- Evidence Stratification:** Before the reason stage fires, the full evidence budget for that iteration is spent on a single dominant failure axis value. Mixed-stratum evidence is never passed to the reason stage. The stratification operation is deterministic: `GROUP BY failure_axis_key`, `ORDER BY count DESC`, `LIMIT 1`.

**I2 -- Cross-Iteration Attempt Memory:** Before the reason stage fires, the attempt ledger for this loop is loaded and an exclusion constraint is injected into the reason stage context. The exclusion targets `hypothesis_summary` (the specific implementation tried), not `root_cause_title` (the general class). A loop may return to the same root cause class; it may not try the same specific hypothesis twice.

Both invariants are substrate-enforced (fixed stages in every loop instance). The instantiating loop designer does not implement them -- they configure the axis key and promote threshold, and the substrate applies the invariants.

---

## KF-LOOP Stage Abstraction

Eight stages. Stages marked `provided_by: substrate (fixed)` are invariant across all loop instances. Stages marked `provided_by: instantiating loop` require configuration per instance.

```yaml
kf_loop_stages:

  cadence:
    description: Scheduler entry point. Triggers each loop iteration.
    provided_by: instantiating loop
    example: "nightwatch cron, scheduled remote agent, manual trigger"
    note: >
      Not defined by substrate. Each loop supplies its own cadence.
      The substrate has no opinion on trigger timing.

  gate:
    description: Deterministic stop rule. Produces WAIT, PROMOTE, or DIAGNOSE.
    type: Wilson-CI class
    provided_by: substrate (fixed algorithm, configurable threshold)
    rule: "LLM-free. Arithmetic on metric values only. No LLM in the loop-control path."
    spec: see Gate Specification section
    branching:
      WAIT: "Proceed to stratify -> recall -> reason -> verify -> act -> observe."
      PROMOTE: "Exit loop. Do NOT fire stratify through act. Log PROMOTE to attempt_ledger observe and halt cadence."
      DIAGNOSE: "Pass to monitor. Do NOT fire stratify through act. Monitor determines escalation or pause."

  stratify:
    description: GROUP BY dominant_failure_axis; full evidence budget on dominant stratum only.
    provided_by: >
      Instantiating loop supplies the failure_axis_key.
      Substrate applies the GROUP BY operation.
    rule: "LLM-free. GROUP BY + ORDER BY count DESC + take-top on evidence rows."
    satisfies: I1 (evidence homogeneity)
    spec: see Stratify Specification section

  recall:
    description: Load cross-iteration attempt_ledger; inject exclusion constraint into reason stage context.
    provided_by: substrate (fixed)
    satisfies: I2 (cross-iteration memory)
    constraint: >
      Exclusion targets hypothesis_summary (specific implementation tried),
      NOT root_cause_title (general class). See Exclusion Constraint section.

  reason:
    description: Task-specific KF mode chain. Receives stratified evidence and exclusion constraint.
    provided_by: instantiating loop
    examples:
      - "[Debugger -> Strategist -> Builder]"
      - "[Expert -> Strategist]"
      - "[Critic (linter) -> Builder]"
    note: >
      KF mode chain selected by the loop designer.
      Substrate provides recall context before chain fires and verify after.

  verify:
    description: Adversarial Critic pass. Blocking.
    provided_by: substrate (fixed)
    protocol: "Module 07 adversarial variant; loop_exit_protocol max=1; circuit_breaker_exempt"
    canary: >
      Must include a seeded known-flaw artifact in canary position.
      Zero-finding pass without canary catch = Critic linter HIGH finding.
      Silence is not health; absence of the canary catch is a broken verify stage.

  act:
    description: One-variable change derived from the reason stage output.
    provided_by: substrate (fixed policy); instantiating loop defines the change variable
    rule: >
      Per Module 00 Surgical Changes always-on patch. One variable changed per iteration.
      No bundling. Bundled changes defeat the exploration gradient by making
      outcome attribution impossible.

  observe:
    description: Gate result -> append attempt_ledger entry -> cadence.
    provided_by: substrate (fixed)
    writes: >
      attempt_ledger entry with outcome_label derived from gate result.
      Entry written before cadence fires for next iteration.
    triggers: "cadence (next iteration) OR escalation (if DIAGNOSE)"
```

---

## Gate Specification

Wilson score confidence interval. Deterministic. No LLM in this stage.

```yaml
gate_specification:
  class: Wilson-CI
  rule: "Arithmetic only. No LLM judgment. Input: successes, n_trials. Output: {WAIT, PROMOTE, DIAGNOSE}."

  inputs:
    - name: successes
      type: integer
      description: Count of successful outcomes in gate_window
    - name: n_trials
      type: integer
      description: Total trials in gate_window
    - name: promote_threshold
      type: float
      description: "CI lower bound required to declare PROMOTE. Supplied by instantiating loop."
    - name: gate_window
      type: integer
      description: "Number of most-recent iterations to include. Supplied by instantiating loop."

  algorithm: |
    p_hat = successes / n_trials
    z = 1.96  # 95% confidence
    denominator = 1 + z^2 / n_trials
    center = (p_hat + z^2 / (2 * n_trials)) / denominator
    margin = (z * sqrt(p_hat * (1 - p_hat) / n_trials + z^2 / (4 * n_trials^2))) / denominator
    ci_lower = center - margin
    ci_upper = center + margin

  decision_rules:
    PROMOTE:
      condition: "ci_lower >= promote_threshold"
      meaning: "Performance has converged above target. Emit PROMOTE signal. Loop exits."
    WAIT:
      condition: "ci_lower < promote_threshold AND NOT diagnose_condition"
      meaning: "Within expected improvement band. Continue."
    DIAGNOSE:
      condition: |
        ci_lower stable (delta < 0.01 across last 3 gate evaluations)
        AND ci_upper < promote_threshold
        AND n_trials >= gate_window
      meaning: "No progress in gate_window iterations. Escalate to monitor."

  canary:
    description: >
      Seed a known-DIAGNOSE scenario before each gate evaluation period.
      Gate health is not verifiable by output alone -- the canary verifies the algorithm path.
    implementation: |
      Gate must be callable with fixed inputs (successes=0, n_trials=gate_window).
      Verify output == DIAGNOSE.
      If output != DIAGNOSE, gate is broken -- surface as configuration error.
      Absence of canary check is a Critic linter HIGH finding.
```

---

## Stratify Specification

```yaml
stratify_specification:
  satisfies: I1 (evidence homogeneity)
  rule: "Deterministic. LLM-free. GROUP BY + ORDER BY count DESC + LIMIT 1."

  inputs:
    - name: evidence_set
      description: >
        Raw evidence rows for this gate_window. Examples: match logs, failure events,
        routing decisions. Rows must contain the failure_axis_key field.
    - name: failure_axis_key
      description: "Column/field name to GROUP BY. Supplied by instantiating loop."

  algorithm: |
    groups = GROUP BY evidence_set[failure_axis_key]
    groups = SORT BY COUNT DESC
    dominant_stratum = groups[0]  # top-1 by count
    output = evidence_set WHERE evidence_set[failure_axis_key] == dominant_stratum.key

  output:
    name: stratified_evidence
    description: >
      Subset of evidence_set containing only rows matching the dominant failure axis value.
      This is the only evidence passed to the reason stage.

  invariant: |
    The full evidence budget (token allocation) is spent on the dominant stratum only.
    Mixed-stratum evidence is NOT passed to the reason stage.
    This directly addresses I1: diagnosis is bounded by evidence about one axis at a time.
    The Clawber failure mode (opponent averaged across 3 types) is structurally impossible
    when this invariant holds.

  generalizability_note: |
    The failure_axis_key must be a cleanly categorical field in the evidence_set rows.
    If the axis values are continuous or not cleanly separable (e.g., ambiguous categories,
    missing values), stratification degenerates. Instantiating loops MUST verify their
    failure_axis_key is present and categorical before deploying. See Adversarial Critic
    Pass section for the specific probe against this assumption.

  degenerate_case:
    condition: "All rows share the same failure_axis_key value (no partition possible)"
    action: >
      Pass full evidence_set as stratified_evidence (stratum IS the set).
      Log to attempt_ledger.stratify_note. This is valid -- if all failures share one axis
      value, the stratum is correctly identified as the full set.

  failure_case:
    condition: "failure_axis_key not present in evidence_set rows"
    action: >
      HALT loop iteration. Surface as configuration error. Do not proceed to reason stage.
      A missing axis key is a setup failure, not a recoverable loop state.
```

---

## Attempt Ledger Schema

```yaml
attempt_ledger_schema:
  version: "1.0"
  satisfies: I2 (cross-iteration memory)

  ledger_entry:
    fields:
      - name: loop_id
        type: string
        required: true
        description: "Identifies which loop instance this entry belongs to. Partitions the ledger."
        example: "kf-loop-mode-calibration"

      - name: iteration_number
        type: integer
        required: true
        description: "Monotonically increasing within loop_id partition."

      - name: timestamp
        type: ISO8601
        required: true

      - name: stratify_axis
        type: string
        required: true
        description: "The failure_axis_key used for this iteration."

      - name: stratify_stratum
        type: string
        required: true
        description: "The dominant stratum value selected in this iteration."

      - name: root_cause_title
        type: string
        required: true
        description: "High-level root cause class identified by the reason stage."
        example: "routing-variant-confusion"

      - name: hypothesis_summary
        type: string
        required: true
        description: |
          Specific implementation hypothesis tried. This is the EXCLUSION TARGET
          for future iterations. Must be distinct enough to differentiate implementations
          within the same root_cause_title.
        example: "Tighten adversarial predicate to require chain_position >= 2"

      - name: action_taken
        type: string
        required: true
        description: "The one-variable change applied in the act stage."

      - name: outcome_label
        type: string
        required: true
        enum: [succeeded, failed, partial, inconclusive]
        description: "Gate result for this iteration."

      - name: metric_delta
        type: float
        required: false
        description: "Change in the loop's primary metric vs. prior iteration."

      - name: stratify_note
        type: string
        required: false
        description: "For degenerate_case or anomalies in stratification."

  exclusion_constraint:
    description: |
      Injected into the reason stage context before the mode chain fires.
      Targets hypothesis_summary, NOT root_cause_title.
    rationale: |
      A loop MUST be able to return to the same root cause class (correct diagnosis)
      while excluding the specific hypothesis that already failed. Excluding root_cause_title
      forces novelty-for-its-own-sake and can push the loop off a correct-but-repeated
      diagnosis when the real fix genuinely belongs to the same root cause class.
    prompt_injection: |
      ATTEMPT LEDGER CONTEXT (cross-iteration memory):
      The following hypotheses have been tried and failed. Your proposed hypothesis
      MUST differ from each entry in hypothesis_summary. You MAY revisit the same
      root_cause_title if your specific hypothesis is genuinely different.

      Prior failed hypotheses:
      [attempt_ledger WHERE loop_id == current_loop_id AND outcome_label IN (failed, partial)]
      - Iteration N: [root_cause_title] / [hypothesis_summary] -> [outcome_label]
      ...
```

---

## DECISION-1: Ledger Physical Location [RESOLVED -- Option (a) selected 2026-08-12]

Decision type: [evaluative]
Resolution: Option (a) -- Module 19 new log. Operator-selected 2026-08-12.
Module 19 bumped to 7.5.0. attempt_ledger schema added alongside routing_decision_log.
See Module 19 v7.5.0 changelog and Cross-Session Audit Logs section for implementation.

Three options were evaluated. Full analysis retained below for auditability.

### Option (a): New log in Module 19 (Memory Architecture)

Rationale: Module 19 already owns the `routing_decision_log` -- the only existing cross-session audit log in KF. The attempt_ledger follows the same shape (schema-versioned, keyed by context, retained permanently). Ownership is consistent: Module 19 manages all cross-session state.

Module 19 delta: Add `attempt_ledger` alongside `routing_decision_log` in the Routing Decision Log section (rename section to "Cross-Session Audit Logs"). Schema as defined above. Write trigger: observe stage. Read trigger: recall stage.

Reversibility: HIGH. Additive to M19. No existing M19 readers change. If a better location is found later, the schema migrates without breaking any consuming module.

Risk: Module 19 grows in scope. It began as memory management for routing accuracy; attempt_ledger is iteration-scoped, not routing-scoped. The conceptual boundary between "routing state" and "loop state" blurs.

Module 19 version bump required: 7.4.0 -> 7.5.0 (new schema, same tier model).

### Option (b): Cross-session promotion of Module 03 dual-fingerprint

Rationale: The dual-fingerprint in Module 03 already tracks dispatch state across Critic/Builder cycles. Promoting it to cross-iteration scope reuses the same mechanism.

Module 03 delta: Add an `iteration_fingerprint_log` alongside `dispatch_fingerprint`. Log entries carry the same fields as the attempt_ledger above.

Reversibility: LOW. The dual-fingerprint's current semantic contract is "what to dispatch in this revision cycle." Extending it to cross-iteration scope changes the contract for all current readers of Module 03 (Coordinator and every mode chain that uses the Builder/Critic loop). Rolling back would require coordinated update.

Risk: Semantic overload. `dispatch_fingerprint` answers "which findings delta to send Builder"; `attempt_ledger` answers "which hypotheses have been tried." These are distinct questions. Conflating them in one module obscures both.

Module 03 version bump required: 7.6.0 -> 8.0.0 (major -- interface change for existing readers).

### Option (c): New negative-results category in Module 21 (Knowledge Accretion)

Rationale: Module 21 already persists cross-session knowledge. A negative-results exemption lets the ledger live in the same store as positive accretions.

Module 21 delta: Add `negative_results` category exempt from novelty gate. Ledger entries file under this category.

Reversibility: MEDIUM. Additive to M21. But removing the novelty-gate exemption later breaks loops that depend on it. The exemption sets a precedent for further gate carve-outs.

Risk: The novelty gate is fundamentally incompatible with what the ledger stores. Negative results are valuable BECAUSE they are not novel -- the whole point is to record what was already tried. Carving an exemption introduces a logical inconsistency. Module 21 is for compiled knowledge; the attempt_ledger is operational iteration state, not a knowledge artifact.

Module 21 version bump required: 7.5.0 -> 7.6.0 (new category, gate exception).

### Author lean (non-binding)

Option (a). Rationale: Module 19 already proves the cross-session audit-log pattern (`routing_decision_log`); adding `attempt_ledger` is scope-consistent, reversibility is highest, and the conceptual boundary (Module 19 = cross-session state) is cleaner than overloading Module 03 or exempting Module 21's gate.

**HOLD OPEN. Do not implement any option until operator selects.**

---

## Monitor Specification

```yaml
monitor_specification:
  description: >
    Cross-iteration plateau check. Extends Module 14 Check 1 to iteration scope.
    Module 14 Check 1 hashes reasoning steps within a single session trace (hash_window=10).
    KF-LOOP monitor checks iteration-level convergence across multiple full sessions.
  scope: KF-LOOP contexts only (not in-session reasoning)

  plateau_detection:
    window: plateau_window  # Supplied by instantiating loop; default: 5
    similarity_metric: edit_distance  # On hypothesis_summary field
    similarity_threshold: 0.85

    condition: |
      Last plateau_window entries in attempt_ledger (same loop_id)
      ALL have outcome_label IN (failed, partial)
      AND pairwise similarity(hypothesis_summary) > similarity_threshold across window
      => plateau_detected

    action_on_plateau:
      escalation_required: true
      do_not_auto_continue: true
      message_format: |
        KF-LOOP PLATEAU ESCALATION
        Loop: [loop_id]
        Last [plateau_window] iterations share hypothesis_summary similarity > [threshold]
        with no successful outcome.

        Attempt ledger excerpt:
        [last plateau_window entries]

        Options:
        (1) Inject new evidence -- change the stratify axis or widen gate_window
        (2) Change the failure_axis_key to a different partition
        (3) Pause loop -- the root cause may require human insight
        (4) Continue -- override plateau detection (requires explicit confirmation)

  canary:
    description: >
      Seed a known-plateau scenario in the ledger before monitor fires.
      Monitor health is not verifiable by output alone.
    implementation: |
      Monitor must accept a synthetic ledger_excerpt input.
      Verify: synthetic_plateau_excerpt -> plateau_detected = true.
      Verify: non-plateau_excerpt -> plateau_detected = false.
      Absence of this canary check is a Critic linter HIGH finding.

  module_14_extension:
    cross_ref: "Module 14 Check 1 (circular_reasoning, hash_window=10)"
    distinction: |
      Module 14 Check 1 hashes reasoning STEPS within a single session trace.
      KF-LOOP monitor checks ITERATIONS -- each is one full run of the loop cadence,
      potentially spanning a complete session.
      The two checks are complementary: Check 1 catches intra-session loops;
      monitor catches inter-session plateaus.
    note: >
      Module 14 gains an iteration_scope block in v6.7.0 to formally reference
      this extension. See Touched Modules section.
```

---

## Loop Catalog

Five loops defined; five built (all instantiation specs complete as of v1.2.0).

```yaml
loop_catalog:

  - id: kf-loop-mode-calibration
    label: "Mode-selection self-calibration"
    status: REFERENCE INSTANCE (built)
    metric: "Module 16 metric #10 -- mode_selection_accuracy"
    failure_axis_key: routing_variant
    stratify_description: "Select the variant with lowest accuracy (adversarial | linter | audit | standard | navigator | etc.)"
    reason_chain: "[Decision Classification (Module 13)] -> [Navigator trigger_disambiguator (Module 04)]"
    ledger_note: >
      routing_decision_log (Module 19) already exists as the cross-session audit log.
      re_route_reason serves as hypothesis_summary. re_routed=true entries are the
      ledger entries. Adoption adds loop_id and outcome_label as optional fields
      to calibration-iteration entries (non-breaking).
    note: "Proof-of-concept. This loop already satisfies both invariants. See Reference Instance section."

  - id: kf-loop-adversarial-yield
    label: "Adversarial-yield tuning"
    status: BUILT (spec: specs/kf-loops/kf-loop-adversarial-yield.md)
    metric: "Adversarial Critic Sev2+ yield (target: 20-80% per Module 07)"
    failure_axis_key: producing_mode
    stratify_description: "Per-mode yield; aggregate yield is meaningless for diagnosis"
    reason_chain: "[Critic (adversarial)] -> [Calibration (Module 12)]"
    canary_requirement: >
      Seed a known flaw in every verify pass. Zero-finding pass that misses the canary
      means the loop is broken, not converged.
    driver_bead: knowledgeforge-core-hvj

  - id: kf-loop-kb-health
    label: "KB health / accretion"
    status: BUILT (spec: specs/kf-loops/kf-loop-kb-health.md)
    metric: "Ratio of entries passing Critic linter per failure_class"
    failure_axis_key: failure_class
    stratify_description: "One failure_class per pass: staleness | contradiction | grounding-decay | orphan"
    reason_chain: "[Critic (linter)] -> [Accretion (Module 21)] -> [Temporal (Module 17)]"
    note: >
      Stratify constraint is critical: one failure_class per pass.
      Running on mixed-class evidence re-introduces I1 failure.
    driver_bead: knowledgeforge-core-knw

  - id: kf-loop-pattern-extraction
    label: "Pattern extraction"
    status: BUILT (spec: specs/kf-loops/kf-loop-pattern-extraction.md)
    metric: "Pattern distinctness score (negative: already-accreted overlap)"
    failure_axis_key: failure_signature
    stratify_description: "Cluster failures by structural signature before abstracting"
    reason_chain: "[Synthesizer (Module 08)] -> [Accretion (Module 21)]"
    ledger_note: |
      The failed-hypothesis log is the degenerate instance of this loop: it clusters
      by "root cause already tried" and injects only the negative (exclusion constraint).
      This loop promotes it: Synthesizer abstracts the positive (generalizable pattern),
      accretes it with source_fingerprint dedup, and future loops retrieve it.
    driver_bead: knowledgeforge-core-7x5

  - id: kf-loop-cos-grounding
    label: "COS grounding / claim-fidelity"
    status: BUILT (spec: specs/kf-loops/kf-loop-cos-grounding.md)
    metric: "Claim grounding score (Module 15)"
    failure_axis_key: claim_type
    stratify_description: "Partition by claim_type (numeric | mechanism | comparative) AND source_corpus"
    reason_chain: "[Expert (research variant, Module 05)] -> [Grounding (Module 15)] -> [Builder rebuild]"
    constraint: |
      Claude Projects deployment: degraded mode (no Asta/Alia MCP, grounding capped 0.6).
      Full fidelity requires Claude Code environment with Asta connected.
      Per Module 05 research variant degraded_mode: ship disposition unavailable at degraded.
    ledger_note: >
      On re-ground: exclude already-failed sources. Claims that rebuild twice escalate.
      Exclusion target: hypothesis_summary = specific source combination tried.
    driver_bead: knowledgeforge-core-r7y
```

---

## Reference Instance: Mode-Selection Self-Calibration

This loop already satisfies both invariants in-repo. Adoption is recognition, not invention.

```yaml
reference_instance:
  loop_id: kf-loop-mode-calibration
  label: "Mode-selection self-calibration"
  proof_point: >
    Metric #10 (mode_selection_accuracy) is tracked per routing_variant in Module 16.
    routing_decision_log (Module 19) is the cross-session audit record.
    Both invariants are already structurally present.

  I1_satisfied:
    how: |
      Metric #10 is tracked per routing_variant (adversarial, linter, audit, navigator, etc.).
      Aggregate accuracy across all variants is meaningless for diagnosis -- a 70% aggregate
      hides 40% adversarial accuracy. Stratify axis = routing_variant.
    evidence: "Module 16 metric #10 schema; per-variant accuracy already separable."

  I2_satisfied:
    how: |
      routing_decision_log (Module 19, re_route_reason retained permanently) is the
      cross-session attempt record. re_route_reason captures what disambiguation failed.
      re_routed=true entries are the ledger entries for this loop.
    evidence: "Module 19 v7.4.0 routing_decision_log schema, re_route_reason field."

  gate_config:
    promote_threshold: 0.85
    gate_window: 20
    metric_source: "Module 16 metric #10, per routing_variant"

  stratify_config:
    failure_axis_key: routing_variant
    description: >
      Select the variant with lowest accuracy in the gate_window.
      Run reason stage on routing decisions for that variant only.

  reason_chain: "Decision Classification (Module 13) -> Navigator trigger_disambiguator (Module 04)"

  act_variable: >
    One predicate in trigger_disambiguator (Module 04). One variable per iteration.

  adopt_existing_ledger:
    description: |
      routing_decision_log IS the attempt_ledger for this loop instance.
      No new schema required at this time. re_route_reason serves as hypothesis_summary.
      Loop adoption adds loop_id and outcome_label as optional fields to routing_decision_log
      entries written during calibration iterations (non-breaking; optional fields).
```

---

## Touched vs. Referenced Modules

### Touched (version bumps required)

| Module | Current | Target | Change |
|--------|---------|--------|--------|
| Module 14 (Metacognitive Monitor) | 6.6.0 | 6.7.0 | Add iteration_scope block to circular_reasoning Check 1 -- documents the scope distinction between intra-session hash_window and cross-iteration monitor |
| Module 26 (this file) | -- | 1.0.0 | New |
| kf.yaml | 7.33.0 | 7.34.0 | New module added; M14 minor bump |

CONDITIONAL on DECISION-1 selection:
- Option (a): Module 19: 7.4.0 -> 7.5.0 (add attempt_ledger schema; rename cross-session audit logs section)
- Option (b): Module 03: 7.6.0 -> 8.0.0 (major -- interface change for existing readers)
- Option (c): Module 21: 7.5.0 -> 7.6.0 (new category, novelty-gate exception)

### Referenced-only (no version bump)

- Module 00: deterministic-first meta-principle; Surgical Changes always-on patch (one variable per act stage)
- Module 03: dual-fingerprint (cited as intra-cycle analog to I2)
- Module 04: trigger_disambiguator (instantiation target for reference instance reason chain)
- Module 05: research variant / degraded_mode (COS grounding loop constraint; grounding capped at 0.6)
- Module 07: loop_exit_protocol; adversarial variant; circuit_breaker_exempt (verify stage protocol)
- Module 08: Synthesizer (pattern extraction loop reason chain)
- Module 12: Calibration Layer (adversarial-yield loop reason chain)
- Module 13: Decision Classification (reference instance reason chain)
- Module 15: Grounding Scores (gate metric for COS grounding loop)
- Module 16: metric #10 mode_selection_accuracy (reference instance gate metric; per-variant tracking)
- Module 17: Temporal Knowledge (KB-health loop reason chain)
- Module 21: Knowledge Accretion (pattern extraction loop; DECISION-1 option c)
- Module 24: Verbatim History Mining (Tier 3 search for evidence retrieval in reason stage)
- Module 25: ERA (entity-scoped filters are Tier 3 retrieval signals, not stratification inputs)

---

## Adversarial Critic Pass (Inline)

This spec has at least one significant flaw -- find it. Sev 2+ only.

**Probe 1 -- Does stratification generalize beyond Clawber?**

In Clawber, `opponent_id` is a clean categorical field with discrete values. The GROUP BY operation is unambiguous. For mode-calibration and KB-health loops, the failure_axis_key must also be cleanly categorical:

- `routing_variant` (mode-calibration): the Module 16 per-variant tracking schema confirms this field exists and is enumerated. Pass.
- `failure_class` (KB-health): staleness | contradiction | grounding-decay | orphan. These are defined categories, not free-text. Pass.
- `producing_mode` (adversarial-yield): enumerated mode identifiers. Pass.

**Risk identified (Sev 2):** The spec provides no enforcement mechanism to verify that the instantiating loop's `failure_axis_key` is present and categorical in the evidence_set before stratification runs. The failure_case block says "HALT loop iteration -- surface as configuration error" but this is documentation, not a runtime check. Without a deterministic pre-stratification validation step, a misconfigured loop silently passes all evidence to the reason stage (I1 violated) or crashes on missing keys with an uninformative error. Mitigation: add a mandatory pre-stratification validation step to the substrate that checks (a) field presence in every evidence row and (b) field cardinality <= configurable MAX_STRATA (default 20) before GROUP BY fires. Flag this as a DEFINED omission -- the substrate spec here states the contract; the implementation bead must include the validation.

**Probe 2 -- Does the exclusion constraint force novelty-for-its-own-sake?**

The exclusion targets `hypothesis_summary`, not `root_cause_title`. This is the correct design. A loop can return to the same root cause class with a different specific hypothesis. Example: if "routing-variant-confusion" is the correct root cause class but two specific predicate tightening attempts have failed, the loop correctly excludes those two specific hypotheses while being free to try a third predicate approach in the same class. The rationale in the Exclusion Constraint section is accurate.

**Risk identified (Sev 3):** `hypothesis_summary` is a free-text string field with no uniqueness enforcement. Two iterations may record semantically identical hypotheses under slightly different phrasing, defeating the exclusion. The exclusion_constraint prompt injection uses string equality, not semantic similarity. Mitigation: instruct the reason stage to canonicalize hypothesis_summary to a short predicate-form description (< 20 words, verb-object structure) before filing the ledger entry. This reduces collision probability without requiring embedding-based deduplication. Flag as advisory -- the current design is functional; the canonicalization instruction reduces failure rate.

**Sev 2 finding accepted.** Pre-stratification validation is a mandatory implementation bead requirement for any loop instance that deploys this substrate.

**Probe 3 (external adversarial pass) -- Gate short-circuit behavior unspecified:**

The stage abstraction originally listed all 8 stages in sequence without specifying that stratify through act are skipped when gate returns PROMOTE or DIAGNOSE. An implementer reading the CC Doc flow diagram (`cadence -> gate -> stratify -> ...`) could conclude all stages run on every cadence tick -- firing the reason chain even after a PROMOTE decision.

**Risk (Sev 2):** A loop that runs the reason chain after PROMOTE would apply an additional one-variable change to an already-converged system, potentially de-converging it. Location: gate stage in Stage Abstraction section; CC Doc flow.

**Fix applied:** Added explicit `branching` field to the gate stage specifying which downstream stages fire for each gate output (WAIT: proceed; PROMOTE: exit; DIAGNOSE: monitor). Both the stage abstraction and CC Doc flow now carry the branching semantics.

**Probe 4 (external adversarial pass) -- ACCRETION_CANDIDATE missing taxonomy fields:**

The accretion_candidate block contained no domain/topic/tags fields. Module 23 requires taxonomy classification for any wiki entry to be filed. The knowledge-librarian agent rejects entries without valid domain/topic/tags. Without classification, the candidate cannot enter the accretion pipeline.

**Risk (Sev 2):** The pattern "scope promotion of intra-session convergence to iteration scope" is genuinely novel and would be lost at session end without taxonomy fields. Location: Accretion Candidate Flag section.

**Fix applied:** Added wiki_domain=orchestration, wiki_topic=recovery, wiki_tags per Module 23 approved vocabulary. Added taxonomy_note flagging that 'recovery' is the closest approximation and recommending a Vocabulary Extension Protocol request for 'iterative-convergence' when grounding rises above 0.85.

---

## Accretion Candidate Flag

```yaml
accretion_candidate:
  pattern: >
    Intra-session convergence mechanisms promoted to iteration scope by adding
    a persistence layer (attempt_ledger) and a scope-aware detection window
    (iteration-level plateau detection vs. session-level hash window).
  novelty_type: new_pattern
  grounding: 0.7
  grounding_note: >
    Clawber n=1 (empirical grounding event). routing_decision_log analogy
    corroborates -- Module 19 already proves the cross-session audit-log pattern
    at 7.4.0. Confidence 0.7 reflects single-case empirical basis plus one
    structural analog. Would rise to 0.85+ on second loop instance deployment.
  source_fingerprint: "knowledgeforge-core-31l / Clawber case study"
  decision_tag: novel
  source_module: 26
  # Taxonomy classification for wiki filing (Module 23 compliance):
  wiki_domain: orchestration
  wiki_topic: recovery  # closest approved topic -- convergence is a form of recovery
  wiki_tags: [routing, chain, accretion]
  taxonomy_note: >
    No approved topic in the orchestration domain precisely names iterative convergence.
    'recovery' is the closest approved topic. When a second loop instance deploys and
    grounding rises above 0.85, consider a Vocabulary Extension Protocol request for
    'iterative-convergence' topic under orchestration domain.
```

---

## Integration Points

### Module 14 (Metacognitive Monitor)
Module 14 Check 1 (circular_reasoning, hash_window=10) operates within a single session trace. KF-LOOP monitor operates at iteration scope (one full loop cadence = one iteration). The two checks are complementary -- Check 1 catches intra-session loops; this module catches inter-session plateaus. Module 14 v6.7.0 adds an `iteration_scope` block to Check 1 to document this distinction formally.

### Module 03 (Coordination Patterns)
The dual-fingerprint in Module 03 tracks dispatch state within one revision cycle (intra-cycle; Builder/Critic handoff). The attempt_ledger in this module tracks hypotheses across full iterations (inter-cycle; across complete loop cadences). Module 03 is cited as the intra-cycle analog, not modified.

### Module 19 (Memory Architecture)
Option (a) of DECISION-1 places the attempt_ledger in Module 19 alongside the existing `routing_decision_log`. The reference instance (mode-calibration) already uses `routing_decision_log` as its de facto ledger. Module 19 v7.5.0 formalizes this if Option (a) is selected.

### Module 16 (Operational Bounds)
Metric #10 (mode_selection_accuracy) is the gate metric for the reference instance. The per-variant tracking schema in Module 16 provides the stratify axis values for kf-loop-mode-calibration. No Module 16 changes are required; it is consumed as-is.

### Module 07 (Critic Agent)
The verify stage uses Module 07 adversarial variant with `loop_exit_protocol max=1` and `circuit_breaker_exempt`. This prevents the verify stage from being skipped when the loop is under pressure to converge.

---

## Related Modules

- `00_orchestrator.md` -- deterministic-first meta-principle; Surgical Changes patch
- `03_coordination_patterns.md` -- dual-fingerprint (intra-cycle analog)
- `07_critic_agent.md` -- adversarial variant used in verify stage
- `14_metacognitive_monitor.md` -- Check 1 extended to iteration scope in v6.7.0
- `16_operational_bounds.md` -- metric #10 (gate metric for reference instance)
- `19_memory_architecture.md` -- cross-session audit log; DECISION-1 Option (a) target
- `21_knowledge_accretion.md` -- DECISION-1 Option (c) target; pattern extraction loop

---
