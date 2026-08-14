# KF-LOOP Instantiation Spec: KB Health / Accretion

```yaml
spec_metadata:
  loop_id: kf-loop-kb-health
  label: "KB health / accretion"
  spec_version: 1.1.0
  substrate_version: 1.1.0
  driver_bead: knowledgeforge-core-knw
  status: DEFINED (not built)
  date: 2026-08-13
  self_contained: true
  purpose: >
    Formalize the iterative audit-and-remediation loop that drives the KF knowledge base
    toward health. Each iteration remediates one failing entry in one failure_class.
    The loop exits per-class when that class reaches 90% linter pass rate (Wilson CI lower
    bound). The loop terminates for the session when all four classes have promoted.
```

---

## Purpose (P)

The KF knowledge base accretes entries over time (Module 21). Without a structured audit loop, entries silently become stale, contradict one another, lose grounding as external sources decay, or orphan references that no longer exist. The /kf-reflect command triggers a linter pass; this loop is the formalized backend that acts on what the linter finds.

**Who uses it and when:** The Critic (linter variant, Module 07) and Accretion (Module 21) modes, triggered by /kf-reflect at session start or on demand. The loop runs on both the cross-project wiki (~/.claude/wiki/) and the project-scoped wiki (~/Scripts/knowledgeforge/wiki/).

**Explicitly out of scope:**
- New entry creation (Module 21 handles that independently)
- Grounding score improvements for entries that already pass the linter
- Cross-session batch remediation of more than one entry per iteration
- Any loop instance other than kb-health (see Module 26 loop catalog for other instances)

---

## Design (D)

### I1 Satisfaction -- Evidence Stratification

**How:** The failure_axis_key is `failure_class`. Before any reasoning begins, the full evidence budget is spent on the single failure_class with the lowest linter pass rate in the current gate_window. Mixed-class evidence is NEVER passed to the reason stage.

**Pre-stratification validation (mandatory):** Before GROUP BY fires, verify that:
1. Every evidence row contains a `failure_class` field.
2. Every `failure_class` value is one of the four enumerated values (staleness | contradiction | grounding-decay | orphan). Free-text or unrecognized values HALT the loop iteration immediately with a configuration error.

This validation is the primary I1 protection for this loop. The four-class enumeration was chosen precisely because it is cleanly categorical -- the failure_case (missing or free-text axis key) cannot silently pass to reasoning.

### I2 Satisfaction -- Cross-Iteration Attempt Memory

**How:** Before the reason stage fires, the Module 19 attempt_ledger is loaded, filtered to loop_id = kf-loop-kb-health AND stratify_stratum = [current failure_class]. Prior hypothesis_summary entries with outcome_label IN (failed, partial) for this failure_class are injected as exclusion constraints.

The exclusion targets `hypothesis_summary` (the specific remediation action tried for a specific entry), NOT `root_cause_title` (the failure class). Example: the loop may return to the staleness class after a prior staleness remediation failed; it may NOT retry the same staleness remediation action on the same entry with the same approach.

**Canonicalization requirement:** To prevent two semantically identical hypotheses from defeating exclusion via different phrasing, the reason stage MUST express hypothesis_summary as a short predicate-form description (< 20 words, verb-object structure, entry path included). Example: "Updated staleness threshold for architecture domain entries from 180 to 90 days."

---

## Implementation (I)

### Gate Configuration

```yaml
gate_config:
  class: Wilson-CI
  metric_source: >
    Per-failure_class linter pass rate. Count of entries in the current failure_class
    stratum that pass the Critic linter check, divided by total entries audited in
    that class within the gate_window. One ratio computed per failure_class.
  promote_threshold: 0.90
  gate_window: 20  # audit passes for the stratified failure_class
  n_trials_minimum: 5  # do not evaluate gate until at least 5 entries audited in class

  decision_rules:
    WAIT:
      condition: "ci_lower < 0.90"
      meaning: "This failure_class needs more remediation. Continue loop."
    PROMOTE:
      condition: "ci_lower >= 0.90"
      meaning: >
        This failure_class has converged. Loop does NOT terminate -- re-stratify to
        the next-most-failing class. Overall loop terminates only when all four
        classes have promoted in the same session.
    DIAGNOSE:
      condition: |
        ci_lower stable (delta < 0.01 over 3 evaluations)
        AND ci_upper < 0.90
        AND n_trials >= gate_window
      meaning: "Plateau within this failure_class. Escalate to monitor."

  gate_branching:
    WAIT: "Proceed: stratify -> recall -> reason -> verify -> act -> observe."
    PROMOTE: "Re-stratify to next-most-failing class. Do NOT fire reason through act on the promoted class again."
    DIAGNOSE: "Pass to monitor. Do NOT fire reason through act. Monitor determines escalation or pause."

  canary:
    protocol: >
      Before each gate evaluation period, run gate with fixed inputs (successes=0,
      n_trials=gate_window). Verify output == DIAGNOSE. If output != DIAGNOSE, gate
      is broken -- surface as configuration error. Absence of this canary check is a
      Critic linter HIGH finding.
```

### Stratify Configuration

```yaml
stratify_config:
  failure_axis_key: failure_class
  values_enumerated: [staleness, contradiction, grounding-decay, orphan]
  selection_rule: >
    Select the failure_class with the lowest linter pass rate in the gate_window
    (most problematic class first). Ties broken by alphabetical order to ensure
    determinism.
  algorithm: >
    GROUP BY failure_class, ORDER BY linter_pass_rate ASC, LIMIT 1.
    Output: evidence_set filtered to dominant (lowest-pass-rate) failure_class only.

  critical_constraint: >
    ONE failure_class per pass. Never mix classes in a single reason-stage invocation.
    This is the primary I1 protection for this loop. If evidence contains multiple
    classes, the stratify stage discards non-dominant class rows before passing to
    recall. The discarded rows are not lost -- they are the evidence budget for future
    iterations when their class becomes dominant.

  pre_stratification_validation:
    step_1: "Verify failure_class field is present in every evidence row."
    step_2: "Verify every failure_class value is in [staleness, contradiction, grounding-decay, orphan]."
    on_failure: >
      HALT loop iteration. Surface as configuration error with the failing row path.
      Do not proceed to recall. This is not a recoverable loop state.

  degenerate_case:
    condition: "All rows share the same failure_class value."
    action: >
      Pass full evidence_set as stratified_evidence. Log to attempt_ledger.stratify_note.
      This is valid -- if all failures are one class, that class is correctly the dominant stratum.
```

### Failure Class Definitions

These definitions are the Critic linter reference. Each check is per-entry.

```yaml
failure_class_definitions:

  staleness:
    definition: >
      Entry date is older than the domain_staleness_threshold for its wiki domain,
      per Module 17 (Temporal Knowledge) temporal decay rates. The threshold is
      domain-specific (e.g., integration entries may decay faster than methodology
      entries). Entry is flagged staleness even if the content is still factually
      accurate -- the age alone triggers review.
    check_type: date comparison (deterministic, LLM-free)
    linter_check: "entry.date < (today - domain_staleness_threshold[entry.domain])"

  contradiction:
    definition: >
      Entry makes a claim that contradicts another entry in the same topic cluster.
      Contradiction is detected by pairwise comparison across entries sharing the
      same wiki_domain AND wiki_topic.
    check_type: pairwise (requires topic-cluster scan, NOT per-entry in isolation)
    linter_check: "any(entry_A.claim conflicts_with entry_B.claim WHERE A.topic == B.topic)"
    implementation_note: >
      This check requires loading the full topic cluster for the entry under review.
      The reason stage (Critic linter variant) must receive the topic cluster, not just
      the single entry. See adversarial critic pass -- Probe 3 for the specific finding.

  grounding-decay:
    definition: >
      Entry's grounding_score (Module 15) has dropped below 0.6 since last audit.
      Grounding decay occurs when external citations have degraded (source moved,
      source changed its claim, or original claim superseded by later work).
    check_type: grounding score comparison (numeric threshold)
    linter_check: "entry.grounding_score < 0.6"
    resolution_note: >
      If the source is permanently gone and no equivalent source exists, the entry's
      action_type is archive (not remove -- the historical record of the claim has
      value). See adversarial critic pass -- Probe 4 for the specific finding.

  orphan:
    definition: >
      Entry references a module, bead, or external source that no longer exists.
      Specifically: a module number that has been removed, a bead ID that has been
      deleted from all known bead stores, or an external URL that returns 404/410.
    check_type: reference existence (deterministic, link-following)
    linter_check: "any(reference in entry does not resolve)"
```

### Recall Configuration

```yaml
recall_config:
  source: "Module 19 attempt_ledger"
  filter:
    loop_id: "kf-loop-kb-health"
    stratify_stratum: "[current failure_class]"
  exclusion_constraint:
    target: "hypothesis_summary"
    outcome_labels_excluded: [failed, partial]
    injection_format: |
      ATTEMPT LEDGER CONTEXT (cross-iteration memory):
      Prior failed remediation approaches for [failure_class] entries. Your proposed
      hypothesis MUST differ from each entry in hypothesis_summary. You MAY revisit
      the same failure_class if your specific hypothesis is genuinely different.

      Prior failed hypotheses for [failure_class]:
      [attempt_ledger WHERE loop_id == "kf-loop-kb-health"
        AND stratify_stratum == current_failure_class
        AND outcome_label IN (failed, partial)]
      - Iteration N: [root_cause_title] / [hypothesis_summary] -> [outcome_label]

  hypothesis_summary_scope: >
    hypothesis_summary targets specific remediation approach tried for a specific entry,
    NOT the general failure class. Example: "Updated staleness threshold for
    architecture domain entries from 180 to 90 days." The failure class (staleness) is
    root_cause_title; the specific edit is hypothesis_summary.
```

### Reason Chain

```yaml
reason_chain: "[Critic (linter variant, Module 07)] -> [Accretion (Module 21)] -> [Temporal (Module 17)]"

reason_chain_detail:

  step_1:
    mode: "Critic (linter variant, Module 07)"
    input: >
      Stratified evidence (entries in the dominant failure_class only).
      For contradiction class: full topic cluster for each entry under review.
      Exclusion constraint from recall stage.
    output: >
      List of failing entry paths with failure_class label and specific failure detail.
      For staleness: entry path + days_since_update + domain_staleness_threshold.
      For contradiction: entry path + conflicting_entry_path + conflicting_claim.
      For grounding-decay: entry path + current_grounding_score + degraded_sources.
      For orphan: entry path + broken_reference_path.
    note: >
      Critic linter variant does NOT produce a remediation -- it produces a diagnosis.
      The remediation decision is Step 2.

  step_2:
    mode: "Accretion (Module 21)"
    input: "Step 1 diagnosis. Exclusion constraint (prior hypothesis_summary failures)."
    output: >
      One remediation hypothesis. Action type MUST be one of:
        (a) update -- entry is still relevant, data is stale; rewrite the stale content.
        (b) archive -- entry is superseded; move to wiki/archive/.
        (c) remove -- entry is an orphan with no resolvable reference; delete.
        (d) reclassify -- entry is misclassified; change domain/topic.
      Accretion applies novelty + grounding gates to updated entries per Module 21 rules.
      One entry, one hypothesis, one action type.

  step_3:
    mode: "Temporal (Module 17)"
    input: "Staleness-class failures from Step 1. Domain of the failing entry."
    output: >
      Domain-specific decay rate and staleness score for any staleness-class failures.
      Used as input to the remediation plan: is this entry merely old or has its
      domain's decay rate changed since last audit?
    applicability: >
      Step 3 fires ONLY when stratified failure_class == staleness.
      For contradiction | grounding-decay | orphan: Step 3 is skipped.
      Gate branching for step_3: WAIT and DIAGNOSE fire step_3 only when failure_class is staleness.

  output_contract: >
    Reason chain output is ONE remediation hypothesis: a specific proposed action
    for ONE entry. The hypothesis_summary must be a predicate-form description
    (< 20 words, verb-object, entry path included) for I2 canonicalization.
```

### Verify Configuration

```yaml
verify_config:
  protocol: "Module 07 adversarial variant, loop_exit_protocol max=1, circuit_breaker_exempt"
  action: >
    Re-run Critic linter on the target entry after proposed remediation. Verify entry
    now passes linter for the targeted failure_class.

  canary:
    required: true
    protocol: >
      REQUIRED before every verify pass. Seed one deliberately broken entry into the
      audit set. The canary entry must have a known failure_class matching the current
      stratified class. If verify returns zero failures AND the canary was not caught,
      this is a HIGH finding -- verify is broken.
    canary_namespace: "wiki/canary/kb-health-canary.md"
    canary_constraint: >
      The canary entry MUST NOT be written to the production wiki. Use only the
      reserved canary namespace path. The canary path is excluded from normal linter
      passes -- it is injected only into verify-stage audit sets.
    canary_log: >
      Log canary_entry_path and canary_failure_class in the observe entry
      (stratify_note field).

  zero_finding_rule: >
    A verify pass that returns zero findings is only valid if the canary was caught.
    Zero findings without canary catch = broken verify stage. Surface as HIGH finding.
    Do not record outcome_label = improved without confirmed canary catch.
```

### Act Variable

```yaml
act_config:
  act_variable: >
    One entry remediated. Action types: update (rewrite stale content), archive
    (move to wiki/archive/), remove (delete orphan), reclassify (change domain/topic).
  scope: "The specific failing entry identified in the reason stage."

  one_variable_rule: >
    Per Module 00 Surgical Changes patch: one variable per iteration. One entry,
    one action. Do not remediate multiple entries in a single iteration even if
    multiple failures are identified. The unexplored entries remain in the evidence
    set for the next iteration.

  no_bundling: >
    Bundled changes defeat the exploration gradient by making outcome attribution
    impossible. If three entries share the same failure and the fix is applied to
    all three at once, there is no way to isolate which entry's fix caused a pass
    or fail in the next gate evaluation.

  action_details:
    update: "Rewrite the stale or contradicted content in place. Preserve source_fingerprint history."
    archive: "Move entry to wiki/archive/ subdirectory. Update any cross-references."
    remove: "Delete orphan entry. Log removed path in attempt_ledger action_taken."
    reclassify: "Change wiki_domain and/or wiki_topic fields to correct taxonomy values (Module 23)."
```

### Observe Configuration

```yaml
observe_config:
  destination: "Module 19 attempt_ledger"
  trigger: "Write before cadence fires for next iteration."

  ledger_entry_fields:
    loop_id:
      value: "kf-loop-kb-health"
      required: true
    iteration_number:
      type: integer
      description: "Monotonically increasing within loop_id partition."
      required: true
    timestamp:
      type: ISO8601
      required: true
    stratify_axis:
      value: "failure_class"
      required: true
    stratify_stratum:
      type: string
      description: "The specific failure_class processed in this iteration."
      example: "staleness"
      required: true
    root_cause_title:
      type: string
      description: "The failure_class processed (same as stratify_stratum for this loop)."
      example: "staleness"
      required: true
    hypothesis_summary:
      type: string
      description: >
        Specific remediation action: what entry, what change. Predicate form, < 20 words.
        This is the I2 exclusion target.
      example: "Archived architecture-domain entry /wiki/integration/2024-01-15_llm-api-patterns.md as superseded."
      required: true
    action_taken:
      type: string
      description: "Exact edit applied, file moved, or file deleted."
      required: true
    outcome_label:
      type: string
      enum: [improved, failed, partial, canary_failure]
      description: >
        improved: entry now passes linter AND canary was caught.
        failed: entry still fails linter after remediation.
        partial: entry now passes for targeted failure_class but a new failure_class detected.
        canary_failure: verify returned zero findings without catching canary. ESCALATE.
      required: true
    metric_delta:
      type: float
      description: "Linter pass rate delta for this failure_class vs. prior iteration."
      required: false
    stratify_note:
      type: string
      description: "canary_entry_path, canary_failure_class, and any stratification anomalies."
      required: false
    wiki_target:
      type: string
      description: "Which wiki was audited: cross-project (~/.claude/wiki/) or project-scoped (~/Scripts/knowledgeforge/wiki/)."
      required: true

  canary_failure_escalation: >
    outcome_label = canary_failure is a distinct escalation path. Do NOT continue
    cadence after a canary_failure entry. Surface immediately with the canary_entry_path
    and canary_failure_class from stratify_note. The verify stage is broken and must
    be repaired before the loop resumes.
```

### Monitor Configuration

```yaml
monitor_config:
  plateau_window: 5
  similarity_threshold: 0.85
  similarity_metric: edit_distance
  similarity_target: hypothesis_summary

  plateau_condition: |
    Last 5 entries in attempt_ledger WHERE loop_id == "kf-loop-kb-health"
    AND stratify_stratum == [current failure_class]
    ALL have outcome_label IN (failed, partial)
    AND pairwise edit_distance(hypothesis_summary) > 0.85 across window
    => plateau_detected

  plateau_meaning: >
    A plateau within one failure_class indicates a systemic root cause that per-entry
    remediation cannot fix. Examples: a staleness threshold that is too aggressive for
    the domain, a taxonomy entry that creates contradictions by design, or a grounding
    decay pattern caused by a source domain going offline (not an individual entry issue).

  escalation_message_format: |
    KF-LOOP PLATEAU ESCALATION
    Loop: kf-loop-kb-health
    Class: [failure_class]
    Last [plateau_window] iterations share hypothesis_summary similarity > 0.85
    with no successful outcome.

    Attempt ledger excerpt:
    [last 5 entries for this failure_class]

    Options:
    (1) Inject new evidence -- change gate_window or widen the audit scope for this class.
    (2) Change the failure_class threshold -- e.g., adjust domain_staleness_threshold via Module 17.
    (3) Pause loop -- the class may require human insight into systemic root cause.
    (4) Continue -- override plateau detection (requires explicit confirmation).

  do_not_auto_continue: true

  canary:
    description: >
      Monitor must accept a synthetic ledger_excerpt for validation before deployment.
      Verify: synthetic_plateau_excerpt (5 failed entries, similarity > 0.85) -> plateau_detected = true.
      Verify: non_plateau_excerpt (mixed outcomes or low similarity) -> plateau_detected = false.
      Absence of this canary check is a Critic linter HIGH finding.
```

### Cadence Configuration

```yaml
cadence_config:
  trigger: >
    /kf-reflect command. The health check instruction invokes the Critic linter variant,
    which routes to this loop for any identified failure_class.
  frequency:
    recommended_session_start: true
    recommended_weekly_full_audit: true

  per_class_completion: >
    When one failure_class promotes (ci_lower >= 0.90), the loop re-stratifies to the
    next-most-failing class within the same session. No new trigger is required.

  all_class_completion: >
    Loop terminates for the session when all four failure_classes have promoted.
    Record overall KB health score in the session reflect report.
    KB health score = sum(1 for each class where ci_lower >= 0.90) / 4.
    A score of 1.0 is the KB-wide health certificate for the session.

  session_health_certificate: >
    The all-class promote condition (all four classes >= 0.90 Wilson CI lower bound)
    is surfaced as a boolean (kb_health_certified: true/false) in the /kf-reflect
    Accretion Status section.

  iteration_scope: >
    One iteration = one full run of the loop cadence for one failure_class entry.
    Potentially spans a complete session for complex remediations.
```

---

## Inline Adversarial Critic Pass

This spec has at least one significant flaw -- find it. Sev 2+ only. Advisory Sev 3 noted without fix.

---

**Probe 1 -- Per-class PROMOTE sequencing: can the loop terminate prematurely?**

The gate_config states: "Overall loop terminates only when all four classes have promoted in the same session." But the PROMOTE branching rule says "re-stratify to the next-most-failing class." If the next-most-failing class has fewer than n_trials_minimum (5) entries audited in the current session, the gate cannot produce a valid Wilson-CI result.

**Risk (Sev 2):** A class with zero prior audit entries in this session has no gate evaluation basis. If the loop re-stratifies to a class with n=0, the gate cannot fire WAIT or PROMOTE -- it either crashes or (worse) silently treats n=0 as WAIT and begins remediation against an unaudited baseline. This is a premature-termination risk in the opposite direction: the loop could declare a class healthy (by never auditing it and therefore never recording failures) if the gate logic does not enforce n_trials_minimum before evaluating.

**Fix applied:** Added `n_trials_minimum: 5` to gate_config. The gate produces no output (loop audits entries without gate evaluation) until n_trials >= 5 for the current class. Before n_trials_minimum is reached, the loop operates in "populate mode" -- run linter, record observe entries, accumulate gate_window data. Gate decisions (WAIT/PROMOTE/DIAGNOSE) are only valid after n_trials_minimum is satisfied. This prevents a zero-evidence class from producing a spurious PROMOTE.

---

**Probe 2 -- Canary namespace: is wiki/canary/ excluded from normal linter passes?**

The spec declares the canary entry is at wiki/canary/kb-health-canary.md and states it "MUST NOT be written to the production wiki." However, the linter that runs in the reason stage (Critic linter variant, Step 1) is invoked on the full evidence set. If the canary path is within the wiki directory tree that the linter scans, the canary entry will be audited as a real entry in normal linter passes and will appear as a genuine failure (it is deliberately broken).

**Risk (Sev 2):** The canary entry, if audited in normal passes, contaminates the linter pass rate metric. It is a known-broken entry that should fail; if it counts toward the failure rate of its failure_class, the loop will perpetually try to remediate it and never converge. The canary must be structurally unreachable by the normal linter scan.

**Fix applied:** Added an explicit exclusion rule in canary_constraint: "The canary path is excluded from normal linter passes -- it is injected only into verify-stage audit sets." The linter must treat wiki/canary/ as a reserved namespace excluded from the evidence set. The implementation bead for this loop MUST add wiki/canary/ to the linter's exclude_paths configuration. This is a required deployment step, not optional.

---

**Probe 3 -- Contradiction check: per-entry linter is insufficient for cross-entry detection.**

The Critic linter variant is invoked per-entry in the reason stage (Step 1). For staleness, grounding-decay, and orphan classes, per-entry checking is sufficient -- the failure condition is detectable from the entry alone. But contradiction is fundamentally a pairwise property: entry A contradicts entry B, which means neither A nor B can be checked in isolation.

**Risk (Sev 2):** If the reason stage receives only the failing entry (standard per-entry linter input), it cannot detect contradictions. The linter would need to compare the entry against every other entry in the same topic cluster. If only the single entry is passed, the linter has no basis for finding contradictions, and the contradiction class will never produce failures -- the metric will show 100% pass rate (vacuously, because contradictions are undetectable with the given input). This would produce a false PROMOTE for the contradiction class.

**Fix applied:** Added to the failure_class_definitions/contradiction block and reason_chain/step_1: "For contradiction class: full topic cluster for each entry under review." The reason stage must receive the topic cluster, not just the single entry. Implementation bead requirement: when stratify_stratum == contradiction, the evidence set construction must load all entries sharing wiki_domain AND wiki_topic with the candidate entry, not just the candidate entry itself. This changes the evidence input shape for the contradiction class only.

---

**Probe 4 -- Grounding-decay with permanently unavailable source: loop termination risk.**

The grounding-decay failure_class is defined as entries whose grounding_score has dropped below 0.6. The remediation options are update, archive, remove, or reclassify. For grounding-decay, the typical path is update (find a replacement source and re-ground the entry). But what happens when the source is permanently gone and no equivalent source exists? The spec says the action_type is archive, but does the loop handle this correctly in the gate?

**Risk (Sev 3 -- advisory):** If an entry is archived (moved to wiki/archive/), it should no longer appear in the linter evidence set. If the archival action is correctly applied and the archived entry is excluded from future linter passes, the gate metric improves. But if the archive operation fails silently (file moved but linter still scans wiki/archive/ paths), the entry will appear again in the next iteration with the same grounding-decay failure, and the loop will attempt to remediate it again. This is a loop cycle, not a termination.

**Advisory note:** The implementation bead MUST confirm that wiki/archive/ is excluded from the linter's evidence set construction (same exclude_paths configuration as wiki/canary/). No fix applied here -- this is an implementation requirement, not a spec design flaw. The spec correctly states the action_type is archive; the gap is in the deployment notes, which now include this requirement explicitly.

---

## Deployment Notes

**Entry point:** This loop is the formalized backend for the /kf-reflect KB linter command. The @critic (linter variant) routing in Module 00 Orchestrator is the entry point. This loop spec defines what happens after routing -- the linter identifies failure_class instances, and this loop takes over.

**Wiki targets:** The linter runs on both wikis. Specify which wiki in the observe entry (wiki_target field).
- Cross-project: ~/.claude/wiki/
- Project-scoped: ~/Scripts/knowledgeforge/wiki/

**Required exclude_paths configuration (implementation bead requirement):**
- wiki/canary/ -- reserved canary namespace, never audited in normal linter passes
- wiki/archive/ -- archived entries excluded from active linter evidence set

**Canary namespace setup (one-time):** Create a reserved canary entry at wiki/canary/kb-health-canary.md. The canary entry must have a known failure_class label in its metadata and a deliberate failure appropriate to that class. Rotate the canary class periodically so all four failure_classes are covered across multiple sessions.

**Claude Projects deployment:** This loop is fully available. No external MCP dependencies. All four failure_class checks are achievable within context window constraints. The exception is the grounding-decay URL resolution check (orphan URLs returning 404/410) -- in Claude Projects without web access, this check degrades to detecting broken internal module references only. Note this in the observe entry when running in degraded mode.

**All-class termination condition:** When all four failure_classes have promoted (ci_lower >= 0.90) in the same session, surface the KB health certificate as a boolean in the /kf-reflect Accretion Status section:

```yaml
kb_health:
  certified: true | false
  classes_promoted: [staleness, contradiction, grounding-decay, orphan]  # only those that promoted
  session_score: 0.75  # example: 3/4 classes promoted
  certificate_date: 2026-08-13
```

**Connection to Module 21 Accretion:** The Accretion mode (Step 2 of reason chain) applies Module 21 novelty + grounding gates to any entry that is updated (not archived or removed). An updated entry must pass Module 21's gate before being written back. This prevents the loop from writing back an updated entry that itself fails accretion standards -- which would create a new grounding-decay failure in the next audit.

**Attempt ledger location:** Module 19 attempt_ledger (Decision-1 resolved: Option (a) selected 2026-08-12). The ledger is keyed by loop_id = kf-loop-kb-health and partitioned by stratify_stratum (failure_class) within that loop_id.
