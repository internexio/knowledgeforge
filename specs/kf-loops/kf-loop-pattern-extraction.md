# KF-LOOP Instantiation Spec: Pattern Extraction

## Spec Metadata

```yaml
spec:
  loop_id: kf-loop-pattern-extraction
  label: "Pattern extraction"
  substrate_version: 1.1.0
  status: DEFINED (not built)
  driver_bead: knowledgeforge-core-7x5
  date: 2026-08-13
  source_fingerprint: "knowledgeforge-core-7x5 / kf-loop-pattern-extraction-spec"
  catalog_entry:
    metric: "Pattern distinctness score (negative: already-accreted overlap)"
    failure_axis_key: failure_signature
    reason_chain: "[Synthesizer (Module 08)] -> [Accretion (Module 21)]"
```

---

## Purpose

Extract reusable generalizable patterns from clustered failure data produced by other KF-LOOP
instances, accrete them to the wiki with source_fingerprint deduplication, and make them
retrievable by future loops via Module 24 (Tier 3) semantic search.

This loop is downstream of all other KF-LOOP instances. It consumes their attempt_ledger
failures as raw evidence, not its own.

**Not in scope:**
- Grounding of extracted patterns (that is Module 21's job after Accretion)
- Re-running failed modes directly (that is the loop that produced the failure data)
- Pattern retrieval or application (that is the consuming loop's responsibility)

---

## Invariant Satisfaction

Every KF-LOOP instance must satisfy I1 (evidence stratification) and I2 (cross-iteration
attempt memory). This section states how each is satisfied here.

**I1 -- Evidence Stratification (satisfied):**
Failures from other loops arrive as raw evidence rows keyed on free-text structural
descriptions. `failure_signature` is a DERIVED axis -- the Synthesizer derives it on
the first pass before GROUP BY fires. On subsequent iterations over the same cluster,
`failure_signature` is already present in evidence rows (written on first pass) and
stratification is deterministic. See Two-Pass Stratify section for the first-pass protocol.

**I2 -- Cross-Iteration Attempt Memory (satisfied):**
The attempt_ledger in Module 19 is the persistence layer. Filter: `loop_id =
kf-loop-pattern-extraction AND stratify_stratum = [current failure_signature]`. Prior
`hypothesis_summary` entries with `outcome_label IN (failed, partial)` for this
`failure_signature` are injected as exclusion constraints before the Synthesizer fires.
Additionally, existing wiki entries for this cluster are loaded via Module 24 semantic
search and injected to prevent re-accreting already-filed patterns.

---

## Stage Configuration

### Cadence

```yaml
cadence:
  trigger: >
    After any session that produces >= 5 new attempt_ledger entries with
    outcome_label IN (failed, partial) from OTHER loop instances
    (kf-loop-mode-calibration, kf-loop-adversarial-yield, kf-loop-kb-health, etc.).
    This loop does not consume its own failures as primary evidence.
  frequency: event-driven (evidence accumulation threshold), not time-based
  manual_trigger: /kf-reflect or explicit operator command
  minimum_evidence_check: >
    REQUIRED before loop fires. Count attempt_ledger entries with outcome_label
    IN (failed, partial) from other loop instances (excluding loop_id =
    kf-loop-pattern-extraction). If count < 5, log "insufficient evidence --
    loop deferred" and halt. Do not proceed to gate.
  multi_cluster_behavior: >
    After one failure_signature cluster saturates (gate returns PROMOTE for
    that cluster), re-stratify on remaining raw failures. Continue until all
    clusters saturate OR remaining failures fall below min_cluster_size (3 failures).
    Log overall extraction session summary when all clusters are exhausted.
  termination_condition: >
    All failure_signature clusters have promoted OR remaining raw failures
    are below min_cluster_size (3).
```

### Gate Configuration (Inverted Wilson-CI Semantics)

This gate uses Wilson-CI arithmetic with inverted semantic interpretation. Standard
Wilson-CI promotes when the success rate is HIGH (converged above target). This gate
promotes when the success rate is LOW -- low distinctness rate signals pattern space
saturation, which is the termination condition for this loop.

The arithmetic is identical to the substrate gate specification. The interpretation is
inverted. This section states both clearly to prevent implementer confusion.

```yaml
gate_config:
  type: Wilson-CI class (inverted semantics -- see inversion_note below)
  promote_threshold: 0.20
  gate_window: 10

  metric_source: >
    Binary per iteration, scoped to the current failure_signature cluster.
    1 = Synthesizer produced a pattern with distinctness_score > 0.6 against
        existing wiki entries AND Accretion filed it successfully.
    0 = No distinct pattern found (distinctness_score <= 0.6) OR pattern was
        already accreted (deduplication rejection from Module 21).

  decision_rules:
    WAIT:
      condition: "ci_lower >= 0.20"
      meaning: >
        At least 20% of recent iterations are still yielding distinct patterns.
        Pattern space remains productive. Continue extracting.

    PROMOTE:
      condition: "ci_lower < 0.20 AND NOT diagnose_condition"
      meaning: >
        Fewer than 20% of recent iterations yield distinct patterns.
        This failure_signature cluster is exhausted. PROMOTE signals termination
        for this cluster -- do NOT interpret as performance convergence.
        After PROMOTE: move to next failure_signature cluster via re-stratify, OR
        terminate if no remaining clusters exceed min_cluster_size.

    DIAGNOSE:
      condition: >
        ci_lower stable (delta < 0.01 over last 3 gate evaluations)
        AND ci_lower between 0.20 and 0.40
        AND n_trials >= gate_window
      meaning: >
        Marginal productivity -- below WAIT threshold but not yet saturated.
        This may indicate the evidence window is too narrow or the cluster
        needs re-stratification. Pass to monitor for escalation.

  inversion_note: >
    Standard Wilson-CI: PROMOTE when ci_lower >= promote_threshold (success rate high).
    This loop: PROMOTE when ci_lower < promote_threshold (success rate low = saturation).
    The arithmetic is unchanged. The termination semantics are inverted.
    An implementer applying the substrate gate algorithm verbatim MUST substitute
    this custom decision_rules block in place of the substrate defaults.

  zero_iteration_guard:
    condition: "n_trials == 0 before gate_window is reached"
    action: >
      Gate returns WAIT unconditionally when n_trials == 0 (no iterations completed).
      Wilson-CI arithmetic is undefined at n=0 (division by zero in p_hat calculation).
      Do not compute. Do not promote. Log "n_trials=0 -- gate returns WAIT" to observe.
      This guard prevents a fresh loop instance with no history from triggering PROMOTE
      on the first cadence tick.
    rationale: >
      With inverted semantics, a loop with zero iterations has a success rate of
      0/0 (undefined). Under the inverted rule, this could falsely signal saturation
      (0% distinctness). The guard prevents this. Minimum n_trials to fire Wilson-CI: 1.

  gate_canary:
    description: >
      Callable gate health check. Run before each gate_window evaluation period.
    inputs_for_canary: "successes=0, n_trials=10 (gate_window)"
    expected_output: PROMOTE (0% distinctness = saturated under inverted semantics)
    failure_condition: >
      If gate with successes=0, n_trials=10 does NOT return PROMOTE, gate is broken.
      Surface as configuration error. Halt loop.
    note: >
      This canary tests the inversion correctly: 0 successes / 10 trials -> ci_lower
      near 0 -> < 0.20 threshold -> PROMOTE. If standard semantics were applied
      erroneously (PROMOTE on high success), this canary would FAIL to trigger PROMOTE
      and the gate health check would catch the misconfiguration.
```

### Stratify Configuration (Two-Pass Mode)

`failure_signature` is a DERIVED field, not an observed field. Standard substrate
stratification assumes the failure_axis_key is already present in evidence rows.
This loop requires a two-pass protocol on first encounter with raw failure data.

```yaml
stratify_config:
  failure_axis_key: failure_signature
  definition: >
    failure_signature: a structural description of a recurring failure mode.
    Examples: "chain-skip-on-ambiguous-signal", "adversarial-yield-collapse-under-pressure",
    "recall-exclusion-not-injected-before-reason".
    It is DERIVED by the Synthesizer -- not observed directly from raw failure data.
    It describes the structural class of failure, not its surface symptoms.

  two_pass_protocol:
    trigger: "failure_signature field absent from evidence rows (first pass on raw failure data)"
    pass_1_derive:
      description: >
        Synthesizer receives raw failure evidence (attempt_ledger entries from other loops
        with outcome_label IN (failed, partial)). Synthesizer derives failure_signature
        labels by clustering failures on structural similarity (edit distance on
        outcome description and hypothesis_summary).
      output: >
        Each evidence row annotated with a derived failure_signature label.
        These labels are written back to the evidence set (not to attempt_ledger --
        they are working annotations for this stratification pass only).
    pass_2_stratify:
      description: >
        Standard substrate GROUP BY fires on the annotated evidence set.
        GROUP BY failure_signature, ORDER BY count DESC, LIMIT 1.
        Dominant cluster selected (highest count).
      output: stratified_evidence (rows matching dominant failure_signature)

    subsequent_iterations: >
      On second and later iterations for the same failure_signature cluster,
      failure_signature is already present in the evidence rows from the first pass.
      Two-pass mode does not re-fire. Standard stratification applies.

  stability_note: >
    failure_signature labels derived in pass_1 are WORKING ANNOTATIONS valid for
    the current extraction session only. They are NOT written to the attempt_ledger
    as the stratify_axis. The attempt_ledger records the failure_signature label
    selected after pass_2 (the dominant cluster label). This ensures consistency:
    the label in the ledger is the output of deterministic GROUP BY, not
    an intermediate annotation that might drift across sessions.
    If new raw failures are added in a later session, pass_1 re-derives labels
    for the new evidence only. Existing clusters (already in ledger) are not
    re-labeled -- their failure_signature is locked by the ledger entry.

  pre_stratification_validation:
    description: >
      Mandatory before GROUP BY fires (substrate Sev 2 requirement from Module 26
      Adversarial Critic Pass, Probe 1).
    checks:
      - field_presence: >
          Verify failure_signature is present and non-empty in every evidence row
          before GROUP BY. If any row is missing failure_signature after pass_1
          annotation, HALT. Surface as "malformed evidence row -- failure_signature
          derivation incomplete."
      - field_cardinality: >
          Verify number of distinct failure_signature values <= 20 (MAX_STRATA default).
          If > 20 distinct signatures, the first pass over-segmented -- surface as
          "cardinality exceeded; consider coarser clustering in pass_1."
      - minimum_cluster_size: >
          After GROUP BY, verify dominant cluster size >= min_cluster_size (3 failures).
          If not, HALT: "dominant cluster below min_cluster_size -- insufficient evidence
          for pattern extraction."
    action_on_failure: HALT loop iteration. Do not proceed to recall.

  selection: cluster with highest raw count (most recurring structural failure)
```

### Recall Configuration

```yaml
recall_config:
  source: Module 19 attempt_ledger
  filter:
    loop_id: kf-loop-pattern-extraction
    stratify_stratum: "[current failure_signature label]"

  exclusion_constraint:
    description: >
      Inject prior hypothesis_summary entries with outcome_label IN (failed, partial)
      for this failure_signature cluster. Prevents re-abstracting already-rejected patterns.
    prompt_injection: |
      ATTEMPT LEDGER CONTEXT (cross-iteration memory):
      The following pattern abstractions have been attempted for the failure_signature
      cluster "[current failure_signature]" and were rejected (already accreted or
      not sufficiently distinct). Your proposed pattern MUST differ from each entry below.
      You MAY revisit the same structural theme if your specific abstraction is genuinely
      different.

      Prior rejected pattern abstractions:
      [attempt_ledger WHERE loop_id = 'kf-loop-pattern-extraction'
       AND stratify_stratum = '[current failure_signature]'
       AND outcome_label IN (failed, partial)]
      - Iteration N: [hypothesis_summary] -> [outcome_label]
      ...

  existing_wiki_injection:
    description: >
      Also inject existing wiki entries for this failure_signature cluster to prevent
      re-accreting patterns already in the wiki. Uses Module 24 (Tier 3) semantic search.
    query: "[current failure_signature] pattern"
    scope: wiki/patterns/ (project and global)
    prompt_injection: |
      EXISTING WIKI PATTERNS (deduplication context):
      The following patterns are already accreted in the wiki for this failure signature
      area. Do not re-abstract any of these. Your candidate must be genuinely distinct.

      [Module 24 semantic search results for failure_signature]
```

### Reason Chain

**[Synthesizer (Module 08)] -> [Accretion (Module 21)]**

```yaml
reason_chain:

  step_1_synthesizer:
    module: "Module 08 (Synthesizer)"
    input: >
      stratified_evidence (dominant failure_signature cluster)
      + exclusion_constraint (prior rejected hypotheses)
      + existing_wiki_injection (deduplication context)
    task: >
      Apply pattern extraction to the stratified failure cluster.
      Identify common structural elements across failures.
      Derive one reusable abstract pattern -- not a diagnosis, but a generalizable
      rule or structural regularity that explains the failure class.
    required_output_fields:
      - pattern_name: >
          Short predicate-form title (< 20 words, verb-object structure).
          Example: "chain-skip-occurs-when-ambiguity-signal-precedes-mode-selection"
          This becomes hypothesis_summary in the ledger entry.
      - pattern_description: 2-4 sentence prose description of the pattern
      - applicability_boundaries: >
          List of conditions under which this pattern holds.
          Module 06.6.1 contract: REQUIRED. Must not be empty.
      - anti_patterns: >
          List of related patterns this should NOT be confused with.
          Module 06.6.1 contract: REQUIRED. Must not be empty.
      - distinctness_score: >
          Float 0.0-1.0. Synthesizer's assessment of overlap with existing wiki entries
          (loaded via recall). 1.0 = entirely novel. 0.0 = exact duplicate.
          Threshold: > 0.6 to proceed to Accretion.
      - failure_signature_cluster: the failure_signature label this pattern abstracts

    synthesizer_constraint: >
      Synthesizer MUST produce both anti_patterns[] and applicability_boundaries[] as
      non-empty lists. Verify stage will check these before Accretion fires. A pattern
      missing either field is incomplete -- do not pass it to verify.

  step_2_accretion_gate:
    condition: "distinctness_score > 0.6"
    if_true: pass candidate to Module 21 Accretion
    if_false: >
      Skip Accretion. Record outcome_label = partial in attempt_ledger.
      reason: "distinctness_score <= 0.6 -- not sufficiently distinct from existing patterns"
      Do not fire verify for a non-distinct candidate.

  step_3_accretion:
    module: "Module 21 (Knowledge Accretion)"
    fires_when: "distinctness_score > 0.6"
    task: >
      Apply Module 21 novelty gate + grounding gate (>= 0.6 for auto-file).
      If both gates pass: write wiki entry to appropriate wiki/patterns/ path.
      If novelty gate rejects: outcome_label = failed (Module 21 deduplication found overlap
      that Synthesizer distinctness check missed -- this is valid; record both checks).
    output:
      filed: wiki entry path (string)
      rejected: rejection reason (string)

  dual_gate_conflict_note: >
    The Synthesizer distinctness_score (> 0.6 threshold in step_2_accretion_gate) and
    the Module 21 novelty gate are two separate mechanisms. Either can reject a candidate:
    - Synthesizer check runs first (step 2). Rejection here skips Accretion entirely.
    - Module 21 novelty gate runs second (step 3). Rejection here records outcome_label = failed.
    These are not redundant: the Synthesizer check uses recall context (injected wiki entries
    and exclusion constraints) as its reference. Module 21 novelty gate queries its own
    full knowledge store independently. A candidate that passes Synthesizer's check (recall
    context was incomplete) may still be rejected by Module 21 (full store scan).
    When Module 21 rejects a candidate that Synthesizer approved (distinctness_score > 0.6),
    log a stratify_note: "M21 novelty gate rejected; Synthesizer distinctness check may have
    had incomplete recall context. Consider widening wiki injection query."
    This is expected behavior, not a contradiction. Two gates with different reference sets
    will occasionally disagree. The loop handles it via outcome_label = failed and I2 exclusion.
```

### Verify Configuration

```yaml
verify_config:
  module: "Module 07 (Critic Agent), adversarial variant"
  protocol: "loop_exit_protocol max=1; circuit_breaker_exempt: true"
  input: the candidate pattern spec produced by Synthesizer (step 1 output)
  circuit_breaker_exempt: true
  note: >
    Verify runs on the PATTERN SPEC, not on the raw failure evidence.
    The Critic evaluates the quality and validity of the abstracted pattern,
    not whether the underlying failures are correctly diagnosed.

  checks:
    - applicability_boundaries_present: >
        Synthesizer contract (Module 06.6.1). Verify that applicability_boundaries[]
        is non-empty. HALT on violation -- Accretion must not fire on an incomplete pattern.
    - anti_patterns_present: >
        Synthesizer contract (Module 06.6.1). Verify that anti_patterns[] is non-empty.
        HALT on violation.
    - distinctness_score_threshold: >
        Verify that distinctness_score > 0.6 before passing to Accretion.
        If Synthesizer reported > 0.6 but the Critic evaluation identifies substantial
        overlap with known patterns in its own context, surface as Sev 2 finding.

  canary:
    required: true
    description: >
      REQUIRED. Seed one deliberately non-distinct candidate pattern into the verify
      input in canary position before verify fires.
    canary_spec:
      distinctness_score: "< 0.3 (known overlap)"
      overlap_target: >
        A specific existing wiki entry that this canary pattern substantially duplicates.
        The canary pattern_description must clearly overlap with the target entry.
        The overlap target path is logged in the observe output (stratify_note field)
        for this iteration.
      expected_outcome: >
        Verify must return at least one finding (Sev 2+) identifying the overlap.
    failure_condition: >
      If verify returns zero findings on the canary candidate (Sev-2-or-higher finding
      about the known overlap NOT present in output), this is a HIGH finding --
      verify is broken. Halt loop. Do not proceed to Accretion.
      Canary silence = verify linter failure, not a healthy result.
    logging: >
      Log canary target entry path in attempt_ledger.stratify_note for every iteration,
      regardless of whether canary fires as the primary candidate or as a secondary check.
```

### Act Variable

```yaml
act_variable:
  description: >
    One variable changed per iteration. No bundling. Options are mutually exclusive per iteration.
  options:
    option_a_accretion:
      condition: "distinctness_score > 0.6 AND Module 21 novelty gate passes"
      action: "ONE wiki entry created at wiki/patterns/ path"
      scope: "The specific failure_signature cluster identified in stratify"
    option_b_refinement:
      condition: "distinctness_score <= 0.6 OR Module 21 novelty gate rejects"
      action: >
        ONE refinement to the abstraction boundary of the attempted pattern.
        Logged as a revised hypothesis_summary in observe. The refinement
        is the abstraction attempt itself -- the ledger entry IS the artifact.
  invariant: >
    One file write OR one ledger entry per iteration.
    Never both in the same iteration.
    This preserves the exploration gradient -- bundled changes make outcome attribution
    impossible.

  source_fingerprint_format: >
    Required for every accreted wiki entry (Module 21 requirement).
    Format: "kf-loop-pattern-extraction / iteration-{N} / {failure_signature}"
    Example: "kf-loop-pattern-extraction / iteration-3 / chain-skip-on-ambiguous-signal"
    This is unique per accreted entry: loop instance + monotonic iteration number +
    cluster label. Do not reuse source_fingerprints across entries.

  wiki_target_path:
    project_specific: "~/Scripts/knowledgeforge/wiki/patterns/"
    global: "~/.claude/wiki/patterns/"
    selection_rule: >
      Patterns about KnowledgeForge-internal failure modes -> project wiki.
      Patterns applicable across projects or session types -> global wiki.
      When uncertain, prefer project wiki and note in pattern_description that
      promotion to global wiki is a candidate after grounding rises.
```

### Observe Configuration

```yaml
observe_config:
  target: "Module 19 attempt_ledger"
  filter_write: "loop_id = kf-loop-pattern-extraction"

  fields:
    loop_id:
      value: "kf-loop-pattern-extraction"
      required: true
    iteration_number:
      type: integer
      required: true
      note: "Monotonically increasing within loop_id partition"
    timestamp:
      type: ISO8601
      required: true
    stratify_axis:
      value: "failure_signature"
      required: true
      note: "The failure_axis_key used for this iteration"
    stratify_stratum:
      type: string
      required: true
      note: "The specific failure_signature cluster label selected in this iteration"
      example: "chain-skip-on-ambiguous-signal"
    root_cause_title:
      type: string
      required: true
      note: "High-level structural failure class (broader than failure_signature)"
      example: "ambiguous-signal-handling-in-mode-dispatch"
    hypothesis_summary:
      type: string
      required: true
      format: "short predicate-form title of the abstracted pattern (< 20 words, verb-object structure)"
      example: "chain-skip-occurs-when-ambiguity-signal-precedes-mode-selection"
      note: >
        This is the EXCLUSION TARGET for future iterations. It must be specific
        enough to differentiate this abstraction attempt from others in the same
        failure_signature cluster.
    action_taken:
      type: string
      required: true
      values:
        accreted: "wiki path where entry was filed (e.g., wiki/patterns/chain-skip-ambiguity.md)"
        not_accreted: "refinement attempted -- [reason: not distinct / M21 rejection]"
    outcome_label:
      type: string
      required: true
      enum:
        accreted: >
          Distinct pattern (distinctness_score > 0.6) successfully filed to wiki.
          This is the success state for this loop. NOTE: this loop uses 'accreted'
          instead of the substrate default 'succeeded' to clarify the loop-specific
          success condition.
        failed: >
          Pattern was not distinct (distinctness_score <= 0.6) AND no successful
          refinement. OR Module 21 novelty gate rejected after Synthesizer approved.
        partial: >
          distinctness_score > 0.6 but Module 21 grounding gate did not reach auto-file
          threshold (< 0.6 grounding score). Pattern is plausible but not fully grounded.
          Not filed. Exclusion constraint applied for next iteration.
        canary_failure: >
          Verify stage did not catch the seeded canary overlap. Loop halted.
          Requires operator intervention before resuming.
    metric_delta:
      type: float
      required: false
      value: "distinctness_score of this iteration (not delta -- absolute score)"
      note: >
        Field is named metric_delta in the substrate schema. For this loop, populate
        with the absolute distinctness_score from the Synthesizer output. The gate
        computes its own binary success/failure; this field provides the continuous value
        for debugging and trend analysis.
    stratify_note:
      type: string
      required: false
      uses:
        - "canary target entry path for this iteration (always log)"
        - "degenerate_case note if full evidence set was passed as stratum"
        - "M21/Synthesizer gate disagreement note (see dual_gate_conflict_note)"
        - "re-stratification note when moving to next cluster after PROMOTE"
```

### Monitor Configuration

```yaml
monitor_config:
  plateau_window: 5
  similarity_threshold: 0.85
  similarity_metric: edit_distance on hypothesis_summary field

  plateau_condition: >
    Last 5 attempt_ledger entries for the same failure_signature cluster
    (same loop_id AND same stratify_stratum) ALL have outcome_label IN (failed, partial)
    AND pairwise similarity(hypothesis_summary) > 0.85 across the 5 entries
    => plateau_detected for this cluster

  plateau_meaning: >
    The failure_signature cluster has been abstracted as far as possible without
    new evidence. The loop is cycling over semantically similar abstraction attempts
    without producing distinct patterns. This is NOT the same as gate-level saturation
    (PROMOTE). Plateau means the Synthesizer is stuck, not that the cluster is exhausted.

  escalation_message_format: |
    KF-LOOP PLATEAU ESCALATION
    Loop: kf-loop-pattern-extraction
    Cluster: [failure_signature]
    Last [plateau_window] iterations share hypothesis_summary similarity > 0.85
    with outcome_label IN (failed, partial) -- no distinct pattern extracted.

    Attempt ledger excerpt (last 5 entries for this cluster):
    [ledger entries]

    Resolution options:
    (1) Widen evidence window -- include failures from more sessions or other loops
    (2) Split cluster -- failure_signature may conflate two distinct structural failure types
    (3) Mark cluster as exhausted -- move to next failure_signature cluster
    (4) Override -- continue extracting (requires explicit operator confirmation)

  do_not_auto_continue: true
  escalation_required: true

  canary:
    description: >
      Monitor must accept a synthetic ledger_excerpt for validation.
      Monitor health is not verifiable by output alone.
    validation:
      plateau_case: >
        Provide a synthetic_excerpt of 5 ledger entries for the same stratify_stratum,
        all with outcome_label IN (failed, partial) AND hypothesis_summary strings
        with edit distance < 0.15 (high similarity). Expected: plateau_detected = true.
      non_plateau_case: >
        Provide a synthetic_excerpt of 5 ledger entries with mixed outcome_labels
        (at least one 'accreted'). Expected: plateau_detected = false.
    failure_condition: >
      If monitor does not return plateau_detected = true on the plateau canary case,
      monitor is broken. Surface as HIGH finding.
```

---

## Adversarial Critic Pass (Inline)

This spec has at least one significant flaw -- find it. Sev 2+ only. Frame: assume a
competent implementer following this spec to the letter produces a broken loop.

---

**Probe 1 -- Gate zero-iteration false PROMOTE (Sev 2)**

The gate uses inverted Wilson-CI semantics: PROMOTE fires when ci_lower < 0.20.
With inverted semantics, a loop instance with NO prior history (n_trials = 0) has an
undefined success rate. The Wilson-CI arithmetic is undefined at n=0 (p_hat = 0/0).
An implementer who computes p_hat = 0/0 = 0 implicitly (treating undefined as zero)
produces ci_lower = 0, which is < 0.20, triggering PROMOTE immediately on the first
cadence tick of a fresh loop instance. The pattern extraction loop would terminate
before extracting any patterns.

**Risk (Sev 2):** Inverted semantics amplify the n=0 edge case. Standard Wilson-CI
with PROMOTE on HIGH success rate: n=0, p_hat=0, ci_lower=0, ci_lower < 0.85 -> WAIT.
This is harmless. Inverted semantics: n=0, p_hat=0, ci_lower=0, ci_lower < 0.20 -> PROMOTE.
This is catastrophic -- a never-run loop terminates immediately.

**Fix applied:** Added `zero_iteration_guard` to gate_config. Gate returns WAIT
unconditionally when n_trials == 0. Wilson-CI arithmetic does not run at n=0.
Minimum n_trials to fire Wilson-CI: 1. Guard is logged to observe on every n=0 hit.
The gate canary also validates this implicitly: the canary inputs successes=0, n_trials=10
(not n=0) -- implementers must ensure this guard fires before the canary test runs.

---

**Probe 2 -- failure_signature drift across sessions (Sev 3, advisory)**

The two-pass stratify derives failure_signature labels via Synthesizer clustering on
structural similarity. These labels are natural-language strings (e.g., "chain-skip-on-
ambiguous-signal"). Across sessions, a Synthesizer run on a DIFFERENT evidence batch
may derive a slightly different label for the same structural failure class:
"chain-skip-ambiguous-signal" vs. "chain-skip-on-ambiguous-signal". The attempt_ledger
partitions by stratify_stratum (exact string match). If labels drift, the exclusion
constraint for a cluster may not load correctly -- the ledger has entries under one label,
the current session uses a slightly different label, and I2 is silently broken.

**Risk (Sev 3, advisory):** Silent I2 failure. The loop appears to be running correctly
(exclusion constraint is injected) but the injected entries belong to a different cluster
label than the current one. The loop re-tries already-rejected hypotheses under a new label.
No hard error fires.

**Mitigation (not fixed -- advisory):** Consider canonicalizing failure_signature labels
to a controlled vocabulary (e.g., a `failure_signature_registry.yaml` in the wiki).
On first derivation, register the label. On subsequent passes, match against the registry
(fuzzy if necessary) and snap to the canonical form. This is not implemented in the
current spec -- it requires a separate registry artifact. Flag as a known limitation.
When this loop is built, consider whether the failure_signature registry warrants a
separate bead. For now: implementers should be aware that label drift is a risk and
should log both the derived label and the nearest registry match in stratify_note.

---

**Probe 3 -- Evidence source gap: other loops have no ledger entries yet (Sev 2)**

This loop is downstream of other KF-LOOP instances. Its raw evidence is attempt_ledger
entries from loops like kf-loop-mode-calibration, kf-loop-adversarial-yield, and
kf-loop-kb-health. The cadence states: trigger when >= 5 new failures from OTHER loop
instances accumulate.

If no other loops have been run (all are DEFINED, not built), this loop has NO input
evidence. The minimum_evidence_check prevents the loop from firing, but the spec as
originally stated did not articulate the minimum_evidence_check as a hard gate -- it
was implicit in the cadence trigger description.

**Risk (Sev 2):** Without an explicit halt mechanism for insufficient evidence, an
implementer following the cadence trigger may fire the loop on fewer than 5 failures
(or zero), reach stratify, find no evidence rows, and produce a null failure_case
(missing failure_axis_key) that surface as a configuration error rather than a
correctly-handled no-evidence state. The distinction matters: configuration error
halts with an alarming message; no-evidence state should halt with a clear "deferred --
insufficient evidence" message and retry on the next cadence tick.

**Fix applied:** Added explicit `minimum_evidence_check` to cadence configuration with
"loop deferred" logging semantics when count < 5. This is a distinct code path from the
stratify failure_case (missing key). The pre-stratification validation still fires as
a secondary check; the minimum_evidence_check is the primary guard that fires before
gate runs.

---

**Probe 4 -- Accretion novelty gate / distinctness_score conflict (Sev 3, advisory)**

The Synthesizer computes distinctness_score (> 0.6 threshold) and Module 21 runs its
own novelty gate independently. The spec acknowledges this in dual_gate_conflict_note.
A subtler risk: the Module 21 novelty gate uses its own reference set (full knowledge
store scan), while the Synthesizer distinctness check uses only the recall-injected
wiki entries (Module 24 semantic search, scoped to wiki/patterns/). If the Module 24
semantic search fails to surface a closely related pattern (query mismatch, index gap),
the Synthesizer may report distinctness_score = 0.75 (confident, not distinct) while
Module 21 finds the match and rejects. This is handled by outcome_label = failed and
the dual_gate_conflict_note. But the inverse is also possible: Module 24 surfaces a
pattern that the Synthesizer correctly determines is not substantively overlapping
(different applicability_boundaries), giving distinctness_score = 0.70, but Module 21's
keyword-based novelty gate flags it as a duplicate based on surface similarity.

**Risk (Sev 3, advisory):** Module 21 may reject a genuinely distinct pattern based on
surface-level similarity that the Synthesizer's richer semantic analysis correctly
distinguished. This is not a bug in the spec -- the dual-gate design is correct and the
outcome_label = failed path handles it. But it means the loop may plateau prematurely on
a cluster where valid novel patterns exist but Module 21's novelty gate is too strict.
This would manifest as monitor plateau escalation. Resolution option (1) in the
escalation message (widen evidence window) would not help; the real resolution is to
review the rejected pattern manually and override Module 21 if warranted.

**Mitigation (advisory):** When outcome_label = failed AND the dual_gate_conflict_note
is logged (M21 rejected after Synthesizer approved), surface the candidate pattern
to the operator for manual review before recording the exclusion constraint.
Not implemented -- the current spec applies the exclusion constraint automatically.
This is a known false-negative risk that escalation option (4) (override) partially covers.

---

## Deployment Notes

**Evidence source:** This loop consumes attempt_ledger entries from OTHER KF-LOOP instances
(kf-loop-mode-calibration, kf-loop-adversarial-yield, kf-loop-kb-health, etc.) with
outcome_label IN (failed, partial). It is structurally downstream of all other loops.
Deploy AFTER at least one other loop has accumulated >= 5 failures in the attempt_ledger.

**Relationship to the failed-hypothesis log:** The catalog ledger_note in Module 26 states:
"The failed-hypothesis log is the degenerate instance of this loop: it clusters by
'root cause already tried' and injects only the negative (exclusion constraint). This loop
promotes it: Synthesizer abstracts the positive (generalizable pattern), accretes it with
source_fingerprint dedup, and future loops retrieve it." In practice: this loop transforms
what Module 19 already records (failed hypotheses as exclusion constraints) into positive
wiki patterns retrievable by future reasoning chains.

**Claude Projects deployment:** Fully available. No external MCP dependencies.
Module 24 (Tier 3) semantic search degrades gracefully if the wiki index is small;
Synthesizer recall context will be less comprehensive but the distinctness check still runs.

**Wiki target paths:**
- KnowledgeForge-internal patterns: `~/Scripts/knowledgeforge/wiki/patterns/`
- Cross-project patterns: `~/.claude/wiki/patterns/`
- Selection: prefer project wiki; note promotion candidacy in pattern_description.

**source_fingerprint format:**
`"kf-loop-pattern-extraction / iteration-{N} / {failure_signature}"`
This satisfies the Module 21 source_fingerprint requirement. It is unique per entry
(monotonic iteration number within loop_id partition + cluster label). Do not hash or
abbreviate -- use the literal format above.

**Build order dependency:** This loop is DEFINED, not built. Build order relative to
other loops is at the implementer's discretion, but this loop cannot produce useful output
until at least one other loop has been built and has accumulated failure evidence.
Recommended: build after kf-loop-mode-calibration reaches at least 10 iterations.

**Gate inversion is the primary implementer risk.** Standard Wilson-CI substrate code
promotes on HIGH success. This loop promotes on LOW success. An implementer who copies
the substrate gate verbatim without substituting the decision_rules block will deploy a
loop that never terminates (WAIT forever when patterns are being found; PROMOTE never
fires because the loop keeps succeeding). The gate_canary (successes=0, n_trials=10 ->
PROMOTE) is the primary verification step. Run it before deploying.
```
