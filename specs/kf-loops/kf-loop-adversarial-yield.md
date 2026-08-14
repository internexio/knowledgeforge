# KF-LOOP Instantiation Spec: Adversarial-Yield Tuning

## Spec Metadata

```yaml
loop_id: kf-loop-adversarial-yield
label: "Adversarial-yield tuning"
substrate_version: 1.1.0
driver_bead: knowledgeforge-core-hvj
status: DEFINED (not built)
spec_date: 2026-08-13
catalog_entry_ref: "Module 26 Loop Catalog, id: kf-loop-adversarial-yield"

metric: "Adversarial Critic Sev2+ yield -- count of Sev2+ findings per verification pass for a given producing_mode"
target_range: "20-80% per Module 07 adversarial variant spec"
failure_axis_key: producing_mode
```

---

## Purpose

This loop tunes the adversarial Critic's calibration per producing mode so that its Sev2+ yield remains in the healthy 20-80% range defined by Module 07. Yield outside that band is a miscalibration signal: below 20% the adversarial Critic is missing real flaws; above 80% it is generating noise.

Aggregate yield across all modes is meaningless for diagnosis. A 45% aggregate can hide a builder mode at 5% yield and a strategist mode at 85% yield. Per-mode stratification is the first invariant of this loop -- without it, calibration interventions applied to the aggregate apply to the wrong unit of analysis.

**Not in scope:**
- Changes to the adversarial Critic's domain coverage (which module specs it checks)
- Calibration of the linter or audit Critic variants (separate loops)
- Yield optimization for internal Critic passes within a single mode chain (in-session scope; use Module 14 Check 1 for those)

---

## I1 and I2 Satisfaction

### I1 -- Evidence Stratification

Satisfied by: stratify stage groups verification pass records by `producing_mode` and selects the mode with the lowest in-range rate in the gate window. The reason stage receives evidence only for that mode. No cross-mode evidence enters the reason stage on any iteration.

The in-range binary value (1 = yield in 20-80%, 0 = yield out of range) is computed per verification pass before stratification runs. The GROUP BY operates on these labeled records.

### I2 -- Cross-Iteration Attempt Memory

Satisfied by: Module 19 attempt_ledger partitioned by `loop_id = kf-loop-adversarial-yield`. Before the reason stage fires on any iteration, the recall stage loads all ledger entries for the current stratified mode with `outcome_label IN (failed, partial)` and injects `hypothesis_summary` values as an exclusion list. The Calibration Layer (Module 12) in the reason stage is explicitly prohibited from re-proposing any excluded hypothesis_summary.

---

## Stage Configuration

### cadence

```yaml
cadence_config:
  trigger: event-driven
  trigger_description: >
    Post-verify-stage in any chain that used the adversarial Critic with the
    stratified mode as the producing_mode. Each verification pass increments
    the evidence count for that mode. Gate evaluation fires when accumulated
    verification passes for a mode reach gate_window (15).
  frequency: not time-based
  manual_trigger: "/kf-reflect or operator command"
  note: >
    Cadence does not tick on a wall-clock schedule. It fires when evidence
    accumulates to gate_window for a given mode. Low-traffic modes accumulate
    slowly; high-traffic modes (builder, expert) accumulate faster. This is
    correct behavior -- calibration confidence should scale with evidence volume.
```

### gate

```yaml
gate_config:
  class: Wilson-CI
  metric_source: >
    Per-mode adversarial yield rate. For the stratified mode: count verification
    passes in gate_window where Sev2+ findings >= 1 AND yield fraction is in
    [0.20, 0.80] (in-range = 1) vs. out of range (in-range = 0).
    Wilson-CI operates on this binary series (successes = in-range count, n_trials = gate_window).
  promote_threshold: 0.80
  gate_window: 15

  decision_rules:
    WAIT:
      condition: "ci_lower < 0.80 AND NOT diagnose_condition"
      meaning: "Mode is still being calibrated. Proceed to stratify -> recall -> reason -> verify -> act -> observe."
    PROMOTE:
      condition: "ci_lower >= 0.80"
      meaning: >
        Mode has converged to healthy yield in >= 80% of passes (lower CI bound).
        Exit loop for this mode. Log PROMOTE to attempt_ledger. Halt cadence for this mode.
        Do NOT fire stratify through act.
    DIAGNOSE:
      condition: |
        ci_lower stable (delta < 0.01 across last 3 gate evaluations)
        AND ci_upper < 0.80
        AND n_trials >= gate_window
      meaning: >
        Mode is stuck. No progress detected. Pass to monitor.
        Do NOT fire stratify through act.

  wilson_algorithm: |
    p_hat = successes / n_trials
    z = 1.96  # 95% confidence
    denominator = 1 + z^2 / n_trials
    center = (p_hat + z^2 / (2 * n_trials)) / denominator
    margin = (z * sqrt(p_hat * (1 - p_hat) / n_trials + z^2 / (4 * n_trials^2))) / denominator
    ci_lower = center - margin
    ci_upper = center + margin

  small_sample_behavior: >
    When n_trials < gate_window (evidence has not yet accumulated to window size),
    Wilson-CI still computes. At n_trials < 5, ci_lower is artificially wide and
    PROMOTE is nearly impossible. This is correct behavior -- do not promote on
    insufficient evidence. The gate emits WAIT until n_trials reaches gate_window.
    Log n_trials to ledger stratify_note when n_trials < gate_window at evaluation time.

  gate_canary:
    description: >
      Before each gate evaluation period, verify the gate algorithm path.
      Gate health is not verifiable by output alone.
    implementation: |
      Call gate with fixed inputs: successes=0, n_trials=15 (gate_window).
      Expected output: DIAGNOSE (0/15 = 0%, ci_upper well below 0.80, 3-eval delta = 0).
      If output != DIAGNOSE, gate is broken -- surface as configuration error. Halt.
      Absence of this canary check is a Critic linter HIGH finding.
```

### stratify

```yaml
stratify_config:
  failure_axis_key: producing_mode
  axis_values: [builder, expert, strategist, critic, synthesizer, debugger, coordinator, navigator]
  selection_rule: >
    Select the mode with the lowest in-range rate in gate_window (most out-of-range passes).
    This is the dominant failure stratum for this iteration.
  tie_break: >
    If two or more modes share the lowest in-range rate, select the mode with the highest
    absolute deviation from the 50% center of the target range (i.e., |yield_mean - 0.50|
    is largest). This is the worst-calibrated mode regardless of direction.

  pre_stratification_validation:
    required: true
    checks:
      - "producing_mode field is present in every evidence row"
      - "producing_mode values are members of the axis_values enum above (categorical, not free-text)"
    on_failure: >
      HALT loop iteration. Surface as configuration error. Do not proceed to reason stage.
      Log failure to attempt_ledger.stratify_note.

  algorithm: |
    groups = GROUP BY evidence_set[producing_mode]
    groups = SORT BY in_range_rate ASC  # lowest in-range rate first
    dominant_stratum = groups[0]
    stratified_evidence = evidence_set WHERE evidence_set[producing_mode] == dominant_stratum.key
```

### recall

```yaml
recall_config:
  source: "Module 19 attempt_ledger, partitioned by loop_id = kf-loop-adversarial-yield"
  filter: "stratify_stratum == [current stratified mode] AND outcome_label IN (failed, partial)"
  exclusion_target: hypothesis_summary
  exclusion_note: >
    The exclusion targets hypothesis_summary (the specific framing parameter changed and
    direction), NOT root_cause_title (over-yield | under-yield | oscillating). The reason
    stage may return to the same root cause class (e.g., "under-yield") with a different
    specific hypothesis (e.g., "reduce severity threshold by 1" after "reduce severity
    threshold by 2" has failed). It may not try the same specific adjustment twice.

  prompt_injection_format: |
    ATTEMPT LEDGER CONTEXT (cross-iteration memory):
    The following calibration adjustments have been tried for [mode] and have not resolved
    the yield deviation. Your proposed hypothesis MUST differ from each entry in
    hypothesis_summary. You MAY revisit the same root_cause_title (over-yield / under-yield /
    oscillating) if your specific calibration adjustment is genuinely different.

    Prior failed hypotheses for [mode]:
    - Iteration N: [root_cause_title] / [hypothesis_summary] -> [outcome_label]
    ...
```

### reason

```yaml
reason_chain: "[Critic (adversarial variant, Module 07)] -> [Calibration Layer (Module 12)]"

step_1:
  module: "Module 07 -- Critic Agent (adversarial variant)"
  configuration:
    circuit_breaker_exempt: true
    loop_exit_protocol_max: 1
  input: >
    Stratified sample of recent outputs from the stratified producing_mode. Sample
    must be bounded to the stratified mode's actual outputs in the gate_window.
  output: >
    List of Sev2+ findings with count. Yield rate for this sample:
    (Sev2+ finding count) / (total items checked).
  purpose: >
    Establish the current yield rate empirically before the Calibration Layer
    proposes an adjustment. The Calibration Layer must receive actual yield data,
    not a restatement of the metric.

step_2:
  module: "Module 12 -- Calibration Layer"
  input:
    - current yield rate (from Step 1)
    - target range: 20-80%
    - deviation direction: over-yield (yield > 80%) or under-yield (yield < 20%)
    - excluded hypothesis_summary list (from recall stage)
  output: >
    One calibration adjustment hypothesis. One variable only. Must specify:
    (a) the framing parameter to adjust, (b) the direction of adjustment, (c) the
    expected yield effect. Must not appear in the excluded hypothesis_summary list.
  direction_logic:
    over_yield: "Tighten adversarial framing (raise severity floor, reduce probe count, narrow check scope)"
    under_yield: "Loosen adversarial framing (lower severity floor, increase probe count, broaden check scope)"
    oscillating: "Stabilize one parameter before adjusting others; root cause is likely threshold instability"
```

### verify

```yaml
verify_config:
  protocol: "Module 07 adversarial variant; loop_exit_protocol max=1; circuit_breaker_exempt"
  sample: >
    Holdout sample from the stratified producing_mode -- distinct from the reason
    stage sample. The proposed calibration adjustment is applied to this holdout run.

  canary:
    required: true
    description: >
      Before the verify pass runs, inject one known Sev2 flaw into the holdout sample.
      The canary flaw is a specific seeded issue. The adversarial Critic must catch it.
    canary_failure_semantics: >
      If the verify pass returns zero findings AND the canary was not caught:
      HIGH finding -- the adversarial Critic is broken or the calibration adjustment
      over-tightened it to the point of blindness. This is NOT convergence.
      The loop has not improved; the tool has degraded. Escalate immediately.
      Do not continue cadence.
    zero_finding_valid_case: >
      A zero-finding pass is valid ONLY if the canary was explicitly caught and reported.
      "Zero findings + canary caught" means the adjusted adversarial Critic correctly
      found only the seeded flaw and no additional issues. This is a healthy result.
    canary_ledger_requirement: >
      Record canary_flaw_description in observe output (stratify_note field) so future
      iterations can vary the canary. Reusing the identical canary flaw across iterations
      risks the adversarial Critic pattern-matching the seeded flaw without genuine
      adversarial evaluation. Rotate canary design every 3 iterations.
```

### act

```yaml
act_config:
  variable_constraint: "ONE variable per iteration. No bundling."
  variable_scope: "The specific producing_mode identified in stratify. Do not adjust other modes."
  bundling_prohibition: >
    If multiple producing modes are simultaneously out of range, the loop handles one
    per iteration (stratify selects the worst). Adjusting multiple modes in one iteration
    defeats outcome attribution -- a compound change produces a compound yield shift with
    no way to isolate which adjustment caused which effect. The one-variable rule is
    not relaxable even when multiple modes are failing.

  candidate_parameters:
    - severity threshold delta (raise or lower the Sev2 floor for this mode)
    - probe count adjustment (more or fewer adversarial probe angles run)
    - framing instruction modification (reword the adversarial check instruction for this mode)
    - check_list addition or removal (add or remove a specific check type for this mode)
  selection_rule: >
    Select the candidate not excluded by hypothesis_summary from the recall stage.
    If all candidates have been tried for this mode (full exclusion), escalate to monitor
    without applying an act. Do not force a novel hypothesis when the exclusion list covers
    all candidate parameters -- that is a plateau, not a calibration problem.
```

### observe

```yaml
observe_config:
  writes_to: "Module 19 attempt_ledger, loop_id = kf-loop-adversarial-yield"
  required_fields:
    - name: loop_id
      value: "kf-loop-adversarial-yield"
    - name: iteration_number
      type: integer
      note: "Monotonically increasing within this loop_id partition"
    - name: timestamp
      type: ISO8601
    - name: stratify_axis
      value: "producing_mode"
    - name: stratify_stratum
      type: string
      note: "The specific mode selected in this iteration (e.g., 'builder')"
    - name: root_cause_title
      type: string
      enum: [over-yield, under-yield, oscillating]
    - name: hypothesis_summary
      type: string
      note: >
        Specific framing parameter changed and direction. Canonicalize to
        short predicate-form (< 20 words, verb-object structure) to reduce
        collision probability with future ledger entries.
        Example: "raise severity floor by 1 for builder adversarial check"
    - name: action_taken
      type: string
      note: "Exact parameter modified in the act stage"
    - name: outcome_label
      type: string
      enum: [improved, failed, partial, canary_failure]
      note: >
        'canary_failure' is a distinct outcome_label, not a subtype of 'failed'.
        A canary_failure means the loop is broken. Escalate immediately. Do not
        continue cadence. The enum does not include 'succeeded' because PROMOTE
        exits the loop before observe writes a final iteration entry; if PROMOTE
        is reached, observe writes a PROMOTE record and cadence halts.
    - name: metric_delta
      type: float
      required: false
      note: "Yield rate delta for the stratified mode after act. Positive = moved toward range."
    - name: stratify_note
      type: string
      required: false
      note: >
        Record canary_flaw_description for this iteration. Also record small-sample
        warning when n_trials < gate_window at evaluation time.
```

### monitor

```yaml
monitor_config:
  plateau_window: 5
  similarity_threshold: 0.85
  similarity_metric: edit_distance on hypothesis_summary

  plateau_condition: |
    Last 5 entries in attempt_ledger for this loop_id AND this stratify_stratum
    ALL have outcome_label IN (failed, partial)
    AND pairwise similarity(hypothesis_summary) > 0.85 across plateau_window
    => plateau_detected

  action_on_plateau:
    escalation_required: true
    do_not_auto_continue: true
    message_format: |
      KF-LOOP PLATEAU ESCALATION
      Loop: kf-loop-adversarial-yield
      Mode: [stratify_stratum]
      Last [plateau_window] iterations share hypothesis_summary similarity > 0.85
      with no improved outcome.

      Attempt ledger excerpt:
      [last plateau_window entries for this mode]

      Options:
      (1) Inject new evidence -- widen gate_window or change the sample composition
      (2) Change the failure_axis_key to a different partition (e.g., sub-mode variant)
      (3) Pause loop -- the adversarial framing for this mode may require human redesign
      (4) Continue -- override plateau detection (requires explicit confirmation)

  canary:
    description: >
      Monitor must accept a synthetic ledger_excerpt input for validation.
      Monitor health is not verifiable by output alone.
    implementation: |
      Test 1 (plateau detection): Pass synthetic_plateau_excerpt (5 entries, all
      outcome_label=failed, hypothesis_summary pairwise similarity > 0.85).
      Expected output: plateau_detected = true.
      Test 2 (non-plateau): Pass non_plateau_excerpt (5 entries, mixed outcomes).
      Expected output: plateau_detected = false.
      If either test fails, monitor is broken -- surface as configuration error.
      Absence of this canary check is a Critic linter HIGH finding.
```

---

## Attempt Ledger Schema Extension

This loop uses the Module 19 attempt_ledger schema (v1.0) with two extensions:

1. **outcome_label enum addition:** `canary_failure` is added alongside the base schema's `[succeeded, failed, partial, inconclusive]`. The canary_failure label has distinct semantics (loop broken, not merely unsuccessful) and must not be conflated with `failed`.

2. **stratify_note dual use:** The base schema defines stratify_note as optional, for degenerate_case or anomalies. This loop additionally uses it for `canary_flaw_description`. The field remains a single string; concatenate both values with a delimiter if both conditions apply in one iteration.

---

## Deployment Notes

### Self-Monitoring Relationship

This loop monitors the adversarial Critic that it uses in both the reason chain (Step 1: current yield measurement) and the verify stage. This is intentional. The adversarial Critic is the primary diagnostic tool for yield assessment -- the only alternative would be a separate yield-measurement tool that does not exist in the substrate.

The canary requirement at the verify stage exists specifically to prevent this self-referential relationship from becoming a failure mode. A miscalibrated adversarial Critic that has been overtightened (under-yield direction gone too far) could theoretically produce zero findings in both the reason stage and the verify stage, causing the loop to record a false PROMOTE. The canary blocks this path: a zero-finding pass is only valid if the canary flaw was caught. An overtightened Critic that misses even a seeded known flaw triggers a canary_failure escalation before the false PROMOTE can be written.

Implication for canary design: the canary flaw must be representative of Sev2 severity at the mode's normal operating point, not an obvious maximum-severity issue. A canary that any framing variant would catch regardless of calibration provides no protection.

### Claude Projects Deployment

Fully available. All stages use standard KF mode chain. No external MCP dependencies. No degraded-mode constraints apply.

### Module 07 Dependency

The yield target range (20-80%) is sourced from Module 07's adversarial variant spec. If Module 07 changes the target range, the following must be updated before the next gate evaluation:
- `gate_config.metric_source` in-range definition (the [0.20, 0.80] bounds)
- `reason_chain.step_2.input` target range
- The gate canary inputs (successes=0, n_trials=15 should still produce DIAGNOSE at any reasonable target range)

Do not silently inherit a Module 07 range change without updating gate_config -- the gate's WAIT/PROMOTE boundary would be decoupled from the Module 07 definition.

### PROMOTE Semantics Per Mode

PROMOTE exits the loop for the stratified mode, not for all modes. A mode reaching ci_lower >= 0.80 is removed from the stratification pool. If other modes remain out-of-range, the loop continues for those modes (they are selected on the next cadence tick). The loop as a whole is complete when all modes have either PROMOTEd or been explicitly paused via monitor escalation.

---

## Adversarial Critic Pass (Inline)

This spec has at least one significant flaw -- find it. Sev 2+ only.

### Probe 1 -- Canary Design and False-Positive Convergence

**Concern:** Can a miscalibrated adversarial Critic escape detection? Specifically: if calibration adjustments progressively overtighten the Critic's framing to the point of near-blindness, does the canary reliably catch this before a false PROMOTE?

**Analysis:**

The canary requires catching a known Sev2 flaw in every verify pass. An overtightened Critic that misses the canary triggers `canary_failure` (not PROMOTE). This path is correctly blocked.

**Sev 2 finding identified:** The canary rotation rule (rotate every 3 iterations) is stated as a requirement but has no enforcement mechanism in the observe stage. A fixed canary flaw reused across many iterations creates an adversarial Critic that has been, in effect, trained to find that specific flaw pattern while remaining miscalibrated for novel flaws. The canary then validates flaw-pattern recognition, not adversarial sensitivity.

Additionally, the canary flaw selection criteria state it should be "representative of Sev2 severity at the mode's normal operating point" but give no guidance on who selects the canary per iteration or how to verify representativeness. An operator who consistently seeds easy-to-find canary flaws (e.g., an obvious logical contradiction rather than a subtle over-claim) will systematically pass canary checks on an undertightened Critic while the real yield problem persists.

**Fix applied:**

Added explicit canary governance requirements to verify_config:
- canary_ledger_requirement already records canary_flaw_description in stratify_note (preserving history)
- Added rotation rule: the 3-iteration rotation applies automatically; the iteration N+3 canary MUST differ from iteration N's canary_flaw_description (checked against ledger before seeding)
- Added representativeness constraint: the canary flaw must be drawn from the same failure taxonomy as real Sev2 findings observed in prior iterations for this mode, not invented independently. If no prior real findings exist (first gate window), use the module spec's own illustrative Sev2 examples as canary source.

These additions are incorporated in the verify_config canary block above.

**Residual risk (Sev 3, advisory):** A fully converged adversarial Critic (genuinely calibrated) would also catch all canary flaws. There is no way to distinguish "Critic is correctly calibrated and catches canary" from "Critic is pattern-matching canary without genuine adversarial evaluation" purely from the canary result. The canary verifies the Critic is not blind; it does not verify the Critic is genuinely adversarial. This is a fundamental limitation of single-artifact canary design. Noted without fix -- a multi-artifact canary (varied flaw types, drawn from different check_list categories) reduces but does not eliminate this risk and is left to the implementer's discretion.

---

### Probe 2 -- Wilson-CI on In-Range Binary Series

**Concern:** Is the Wilson-CI gate correctly applied to an in-range binary series? Are small sample sizes handled?

**Analysis:**

The gate operates on a binary outcome (1 = yield in-range, 0 = yield out-of-range) per verification pass. Wilson-CI is designed for binary proportion estimation. The application is formally correct.

Small sample behavior: at n_trials < 5, ci_lower is artificially wide and PROMOTE is structurally inaccessible. The spec documents this in `small_sample_behavior` and correctly says this is the desired behavior. WAIT is the safe default when evidence is thin.

**Sev 2 finding identified:** The gate window is per-mode (15 verification passes for the stratified mode), but modes accumulate evidence at very different rates. A rarely-invoked mode (e.g., coordinator) may spend many calendar sessions with n_trials = 2-4, where Wilson-CI is so wide that DIAGNOSE is also structurally inaccessible (ci_lower and ci_upper are too wide to trigger the stable-delta condition). The loop emits WAIT indefinitely for low-traffic modes regardless of their actual calibration state.

This is not just a slow convergence issue. The DIAGNOSE condition requires n_trials >= gate_window. A mode that never reaches 15 verification passes never receives a DIAGNOSE signal and therefore never escalates to monitor, even if it is permanently miscalibrated.

**Fix applied:**

Added to gate_config:
- `small_sample_behavior` block already logs n_trials to stratify_note when n_trials < gate_window
- Added: if a mode has accumulated fewer than gate_window passes after 90 days of wall-clock time, surface a LOW advisory to the operator ("Mode [X] has not accumulated sufficient verification passes for gate evaluation. Consider auditing whether this mode is being invoked in production."). This is not a loop error -- the loop state is valid -- but the advisory prevents permanent silent stagnation.

The 90-day threshold is advisory; implementers may adjust based on deployment cadence. This addition does not affect the gate algorithm's deterministic output -- it is an out-of-band advisory only.

---

### Probe 3 -- Reason Chain Feedback Loop: Calibration Degrading the Adversarial Critic

**Concern:** Does the reason chain create a feedback loop that could degrade the adversarial Critic through its own calibration adjustments?

**Analysis:**

The reason chain's Step 1 uses the adversarial Critic (Module 07) to measure yield on a sample of the stratified mode's outputs. Step 2 (Calibration Layer, Module 12) then produces a framing adjustment targeting the deviation direction. The act stage applies this adjustment.

The self-referential concern is: the loop is using the adversarial Critic to diagnose the adversarial Critic's miscalibration, then applying a calibration change, then in the next iteration using the (now-adjusted) adversarial Critic to measure whether the adjustment worked. If the Calibration Layer produces a systematically biased adjustment direction (e.g., always loosens framing when the real problem is instability), successive iterations compound the error.

**Finding (Sev 3, advisory):** The reason chain has no check for oscillation between over-tighten and over-loosen adjustments. The root_cause_title enum includes `oscillating`, and the step_2 direction_logic specifies "stabilize one parameter before adjusting others" for oscillating cases. However, oscillation detection depends on the Calibration Layer correctly diagnosing oscillation from the yield rate sequence, which is itself an LLM judgment. There is no deterministic oscillation check analogous to the Wilson-CI gate.

The monitor's plateau detection (similarity_threshold=0.85 on hypothesis_summary) partially covers this: alternating "tighten severity threshold" and "loosen severity threshold" would have low hypothesis_summary similarity (< 0.85) and would NOT trigger plateau detection. A persistent oscillation pattern would accumulate as mixed `improved/failed` outcome_labels rather than `failed/partial`, and might never trigger either plateau detection or DIAGNOSE (because the in-range rate oscillates around the promote_threshold).

**No Sev 2 finding.** The oscillation risk is real but does not constitute a spec flaw -- the canary requirement and the one-variable act constraint bound the degradation. An oscillating loop with canary checks in place cannot certify a broken Critic as converged. The monitor's plateau detection covers the degenerate case (hypothesis oscillation). Noted as advisory; no fix required.

---

### Probe 4 -- One-Variable Constraint When Multiple Modes Are Out of Range

**Concern:** Is the one-variable-per-act constraint enforced when multiple modes are simultaneously out of range?

**Analysis:**

When multiple producing modes have out-of-range yield simultaneously, the stratify stage selects one (lowest in-range rate, tie-broken by highest deviation from 50% center). The act stage adjusts one variable for that one mode. This is structurally enforced by the stratify stage's LIMIT 1 semantics -- only one mode's evidence enters the reason stage on any iteration.

However, the spec as written does not explicitly prohibit an implementer from applying calibration adjustments to non-stratified modes "while they are at it" -- the bundling prohibition in act_config says "do not adjust other modes" but this relies on the implementer reading and following the constraint, not on a technical enforcement mechanism.

**Sev 2 finding identified:** The act_config bundling prohibition is stated as a prose rule with no observable enforcement hook. An implementer running this loop in a semi-automated context could apply the reason chain's output (framing adjustment for mode A) and simultaneously apply a "common sense" adjustment to mode B based on its observed yield problem. This would defeat outcome attribution across both modes on the same iteration.

**Fix applied:**

Added to act_config:
- `bundling_prohibition` block explicitly names the multi-mode simultaneous failure scenario and states the loop handles one mode per iteration by design (stratify selects worst)
- Added: observe stage required fields include `stratify_stratum` (the specific mode adjusted). Any post-iteration audit that shows metric_delta movement in a mode other than the logged stratify_stratum is evidence of bundling. The ledger serves as the enforcement audit trail.
- The prohibition is preserved as prose -- no technical enforcement beyond ledger-based audit. The Sev 2 finding is the absence of this explicit audit guidance, which is now present.

---

### Summary: Sev 2 Findings and Fixes

| Finding | Severity | Fixed in spec |
|---------|----------|---------------|
| Canary rotation has no enforcement mechanism; fixed canary enables pattern-matching not adversarial sensitivity | Sev 2 | Yes -- canary rotation sourced from prior real findings; rotation check against ledger before seeding |
| Low-traffic modes may never reach gate_window, making DIAGNOSE structurally inaccessible | Sev 2 | Yes -- 90-day advisory added; does not affect gate algorithm |
| Bundling prohibition has no audit mechanism when multiple modes fail simultaneously | Sev 2 | Yes -- ledger audit trail clarified; stratify_stratum required field enables post-iteration audit |
| Oscillation detection depends on Calibration Layer LLM judgment, no deterministic check | Sev 3 | No -- advisory only; canary + one-variable act bound the degradation |
| Canary representativeness depends on operator judgment; easy canaries pass without genuine adversarial sensitivity | Sev 3 | No -- advisory; multi-artifact canary noted as implementer option |
