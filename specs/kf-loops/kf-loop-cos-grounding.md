# KF-LOOP Instantiation Spec: COS Grounding / Claim-Fidelity

```yaml
spec_metadata:
  loop_id: kf-loop-cos-grounding
  label: "COS grounding / claim-fidelity"
  substrate_version: 1.1.0
  driver_bead: knowledgeforge-core-r7y
  status: DEFINED (not built)
  date: 2026-08-13
  module_ref: 26_kf_loop_substrate.md
  catalog_entry_ref: "Loop catalog -- kf-loop-cos-grounding"
```

---

## Purpose

One sentence: iteratively improve the grounding score of COS claims by stratifying on claim type and source corpus, excluding already-failed source combinations, and rebuilding one claim per iteration until each (claim_type, source_corpus) stratum meets its grounding target.

**Who uses it:** COS content production and review workflows. Runs after any session that generates Module 15 grounding score evaluations below the grounding target.

**What is NOT in scope:**
- Grounding claims that require original human research (route to cos-grounding repo)
- Validating COS claims for business accuracy (not grounding -- a separate review concern)
- Grounding content outside the COS domain
- Replacing the cos-grounding repo as the canonical grounding hub (this loop is a consumer of that hub, not a replacement)

---

## How This Spec Satisfies the Two Invariants

**I1 -- Evidence Stratification:**
Before the reason stage fires, the evidence set (failing claims from the current gate_window) is stratified by a two-axis key: (claim_type, source_corpus). The dominant stratum is the (claim_type, source_corpus) pair with the highest count of failing claims in the gate_window. The reason stage receives only claims from that dominant stratum -- mixed-stratum evidence is never passed through. Gate arithmetic is also per-stratum: Wilson-CI operates on the binary success series for the current (claim_type, source_corpus) pair only. Aggregate grounding across all claim types is meaningless for diagnosis.

**I2 -- Cross-Iteration Attempt Memory:**
Before the reason stage fires, the Module 19 attempt_ledger is loaded and filtered to loop_id=kf-loop-cos-grounding AND stratify_stratum=[current (claim_type, source_corpus) pair]. Failed and partial entries are injected as an exclusion constraint. The exclusion targets hypothesis_summary (the specific source combination tried), NOT root_cause_title (the general grounding failure pattern). The reason stage may return to the same root cause class; it may not re-attempt the same source combination.

---

## Stage Configuration

### Cadence

```yaml
cadence:
  trigger: >
    Event-driven. Fires after any COS content creation or review session that
    produces Module 15 grounding score evaluations below grounding_target.
  batch_mode: RECOMMENDED
    description: >
      Collect all failing claims across the session before running the loop.
      Do NOT run claim-by-claim in real time. Batch processing allows stratification
      to identify the dominant (claim_type, source_corpus) stratum across the full
      session's failing claims rather than reacting to individual claims in sequence.
  source_of_claims:
    - cos-grounding repo claim briefs (~/Scripts/cos-grounding/claims/)
    - COS content review outputs with Module 15 grounding scores below grounding_target
  per_stratum_completion: >
    When one (claim_type, source_corpus) stratum emits PROMOTE, loop continues on
    the next-most-failing stratum. Loop terminates when all strata have either
    promoted or been fully escalated.
```

### Gate

```yaml
gate_config:
  class: Wilson-CI
  rule: "Arithmetic only. No LLM judgment. Input: binary pass/fail series per stratum. Output: {WAIT, PROMOTE, DIAGNOSE}."

  metric_source: >
    Per-claim binary: 1 if claim grounding_score (Module 15) >= grounding_target for
    the active_mode, 0 if below. Wilson-CI operates on this binary series for the
    current (claim_type, source_corpus) stratum only.

  grounding_target:
    full_mode: 0.85   # Claude Code environment with Asta MCP connected
    degraded_mode: 0.60  # Claude Projects -- no Asta/Alia MCP

  promote_threshold: 0.90
    meaning: >
      ci_lower >= 0.90 means 90% of gate_window claims in this stratum reliably
      meet the grounding_target. The loop exits for this stratum. Note: this is
      90% of claims meeting the grounding_target bar, not the grounding_score itself
      reaching 0.90. The two are distinct. In degraded mode, a claim passes the
      binary if it scores >= 0.60; PROMOTE fires when 90% of the gate_window pass
      that bar. The loop can promote in both modes.

  gate_window:
    default: 20
    small_stratum_floor: >
      REQUIRED adaptation (see Adversarial Critic findings, Probe 1):
      With 15 possible strata (3 claim_types x 5 source_corpora), many strata will
      have fewer than 20 claims in any gate_window. Wilson-CI on fewer than 8 samples
      produces confidence intervals too wide to be actionable.

      Adaptive gate_window rule:
        if n_claims_in_stratum < 8:
          gate_output: WAIT (unconditional -- do not run Wilson-CI)
          note: "Insufficient sample for Wilson-CI. Accumulate more claims in this stratum."
        elif n_claims_in_stratum < 20:
          gate_window: n_claims_in_stratum  # use all available claims; note reduced window
          log: "Reduced gate_window to [n] for stratum [claim_type, source_corpus]."
        else:
          gate_window: 20  # standard

  active_mode: full | degraded  # set at session start based on environment detection

  decision_rules:
    WAIT:
      condition: "ci_lower < 0.90 AND NOT DIAGNOSE condition"
      action: "Proceed to stratify -> recall -> reason -> verify -> act -> observe."
    PROMOTE:
      condition: "ci_lower >= 0.90"
      action: >
        Exit loop for this stratum. Log PROMOTE entry to attempt_ledger. Do NOT fire
        stratify through act. Begin cadence for next-most-failing stratum if any remain.
    DIAGNOSE:
      condition: >
        ci_lower stable (delta < 0.01 across last 3 gate evaluations)
        AND ci_upper < 0.90
        AND n_trials >= gate_window (or adaptive floor)
      action: "Pass to monitor. Do NOT fire stratify through act."

  canary:
    description: >
      Gate must be callable with fixed inputs (successes=0, n_trials=gate_window).
      Required output: DIAGNOSE. If output != DIAGNOSE, gate implementation is broken.
      Absence of this canary check is a Critic linter HIGH finding.
    implementation: >
      Before each gate evaluation period, call gate(successes=0, n_trials=gate_window).
      Verify output == DIAGNOSE. Log result.
```

### Stratify

```yaml
stratify_config:
  failure_axis_key: claim_type + source_corpus  # two-axis stratification
  primary_axis: claim_type     # numeric | mechanism | comparative
  secondary_axis: source_corpus  # first-party-research | peer-reviewed | industry-report | web-accessible | no-source

  algorithm: |
    strata = GROUP BY (claim_type, source_corpus)
    strata = SORT BY COUNT(failing_claims) DESC
    dominant_stratum = strata[0]  # highest count of failing claims
    stratified_evidence = failing_claims WHERE (claim_type, source_corpus) == dominant_stratum

  output:
    name: stratified_evidence
    description: >
      Subset of failing claims from the dominant (claim_type, source_corpus) pair.
      Only these claims are passed to the reason stage.
    example_dominant_stratum: "(numeric, industry-report) -- most common low-grounding combination"

  pre_stratification_validation:
    required: true
    description: >
      Verify ALL of the following before GROUP BY fires. HALT on any failure.
    checks:
      - "claim_type field present in every evidence row"
      - "source_corpus field present in every evidence row"
      - "claim_type value in [numeric, mechanism, comparative] for every row"
      - "source_corpus value in [first-party-research, peer-reviewed, industry-report, web-accessible, no-source] for every row"
    on_failure: >
      HALT loop iteration. Surface as configuration error with field name and
      offending row index. Do not proceed to reason stage. Free-text or
      missing axis values make stratification undefined.

  claim_type_definitions:
    numeric: >
      Statistical or quantitative claims. Examples: "32% audience reach",
      "2.3x conversion lift", "top 3 in category by volume". Requires numeric
      evidence that supports the stated figure or range.
    mechanism: >
      Claims about causal or process relationships. Examples: "N-type personalities
      process information via ELM peripheral route", "cognitive load reduces message
      retention". Requires mechanistic or experimental evidence.
    comparative: >
      Claims asserting relative performance. Examples: "more effective than X",
      "highest-ranked in category", "outperforms alternatives". Requires comparative
      evidence; a single non-comparative benchmark is insufficient.

  source_corpus_definitions:
    first-party-research: Internal COS or SEMalytics research and data
    peer-reviewed: Academic journals, conference proceedings with peer review
    industry-report: Industry analyst reports, market research firms, trade publications
    web-accessible: Public web sources not in the above categories (news, blogs, organization sites)
    no-source: Claim has no source attached

  degenerate_case:
    condition: "All failing claims share the same (claim_type, source_corpus) value"
    action: >
      Pass full failing claims set as stratified_evidence. This is valid -- the
      stratum is the full set. Log to attempt_ledger.stratify_note.
```

### Recall

```yaml
recall_config:
  source: "Module 19 attempt_ledger"
  filter:
    loop_id: kf-loop-cos-grounding
    stratify_stratum: "[current (claim_type, source_corpus) pair]"
  load: "All entries with outcome_label IN (failed, partial) for this stratum"

  exclusion_constraint:
    target: hypothesis_summary (specific source combination tried)
    NOT_target: root_cause_title (general grounding failure pattern)
    rationale: >
      The loop may return to the same root cause class (e.g., "numeric source
      insufficient") with a different source combination. It may not re-attempt
      the same source combination that already failed.
    prompt_injection_format: |
      ATTEMPT LEDGER CONTEXT (cross-iteration memory):
      Previously tried source combinations for [claim_type] claims in [source_corpus] corpus
      that did not reach grounding_target. Do NOT re-attempt these source combinations:

      - Iteration [N]: [root_cause_title] / [hypothesis_summary] -> [outcome_label]
      ...

      You MAY address the same root cause class if your specific source combination
      is genuinely different from all entries above.

  hypothesis_summary_examples:
    description: >
      hypothesis_summary targets the SPECIFIC source combination tried, in short
      predicate form (< 20 words, verb-object structure). Not the general claim class.
    examples:
      - "APA 2021 meta-analysis + Nielsen 2019 industry report for numeric reach claims"
      - "WebSearch-retrieved Statista 2023 + eMarketer 2022 for B2B audience numeric"
      - "HBR 2020 article + Google Think 2021 for comparative effectiveness claims"

  supplementary_load:
    cos_grounding_handoffs:
      path: "~/Scripts/cos-grounding/findings/composed/"
      description: >
        Pre-verified citation files from the canonical cos-grounding hub. Load
        before the reason stage fires. These are human-verified source combinations
        for claims that previously went through full cos-grounding workflow. Prefer
        these over in-loop research -- they carry higher grounding confidence.
      action: >
        If a pre-verified handoff packet exists for the current claim or claim class,
        inject it into the reason stage context before firing Expert research variant.
        The reason stage should attempt to use pre-verified sources before conducting
        new research.
```

### Reason Chain

```yaml
reason_chain: "[Expert (research variant, Module 05)] -> [Grounding (Module 15)] -> [Builder rebuild]"
```

**Step 1: Expert (research variant, Module 05)**

Receives: the dominant-stratum claim(s) + claim_type + source_corpus + exclusion constraint from recall + any pre-verified cos-grounding handoff packets.

Task: search for alternative source combinations that could ground the claim above grounding_target. Propose one specific source combination as the hypothesis for this iteration.

Environment behavior:
- Full mode (Asta MCP available): query Allen AI Semantic Scholar corpus, peer-reviewed sources, plus web-accessible sources. Asta should be probed with a known-good DOI before beginning. If Asta probe fails within 5 seconds, enter degraded_mode immediately and log.
- Degraded mode (Claude Projects, no Asta): use WebSearch for source retrieval only. Cap composite grounding score output at 0.60. Emit degraded=true in grounded_evidence_set output. OMIT ship disposition entirely -- emit only soften or rebuild dispositions. Log: "[kf-research] DEGRADED mode: Asta MCP unavailable. WebSearch fallback active. grounding_cap=0.6 ship_disposition=blocked"

Degraded mode and the reason chain: degraded mode still produces rebuild hypotheses (soften and rebuild dispositions remain valid outputs). The reason chain can complete in degraded mode -- the Expert output feeds Step 2 with a proposed source combination, regardless of mode. The constraint is that degraded outputs never reach ship disposition, so all rebuilt claims in degraded mode carry rebuild/soften framing. Full-mode verification of any degraded-mode rebuild is deferred until a Claude Code session is available.

**Step 2: Grounding (Module 15)**

Receives: the candidate source combination from Step 1.

Task: rescore the target claim against the proposed source combination. Output: grounding_score for this source combination, recommended source set, disposition (ship/soften/rebuild -- noting that degraded mode blocks ship).

**Step 3: Builder rebuild**

Receives: Module 15 grounding output + highest-scoring source combination.

Task: rebuild the claim text and citation block using the recommended source set. One claim rebuilt per iteration. Output is a revised claim + citation block.

**Claim escalation check (before firing reason chain):**
- Query attempt_ledger for this specific claim (not just the stratum): count prior entries where outcome_label IN (failed, partial)
- If count >= 2: skip reason chain. Mark this claim as escalated. File to cos-grounding repo (bead in ~/Scripts/cos-grounding/). Do not attempt a third rebuild in-loop.
- If count < 2: proceed with reason chain.

### Verify

```yaml
verify_config:
  protocol: "Module 07 adversarial variant; loop_exit_protocol max=1; circuit_breaker_exempt=true"

  checks:
    - "Rebuilt claim grounding_score (Module 15) >= grounding_target for active_mode"
    - "Rebuilt claim text accurately represents the source (no overclaiming)"
    - "hypothesis_summary for this iteration is distinct from all prior failed entries (exclusion constraint respected)"

  canary:
    required: true
    description: >
      Inject one known-ungrounded claim into the verify set before each verify pass.
      The canary claim has no source attached (source_corpus=no-source) and an expected
      grounding_score=0. If verify returns a passing score for the canary claim, this
      is a HIGH finding -- Module 15 grounding scoring is broken, not the claim.
    canary_claim_template: >
      "[Canary] COS audiences achieve [metric] [timeframe]." Source: none.
      Expected grounding_score: 0. Expected verify result: FAIL.
    on_canary_miss: >
      Do NOT record a passing outcome_label for this iteration. Surface as HIGH finding.
      Log: "VERIFY CANARY MISS: Module 15 scored a known-ungrounded claim as passing.
      Grounding module scoring is unreliable. Pause loop and surface for human review."
    log_target: observe entry, stratify_note field
```

### Act

```yaml
act_config:
  variable: "One claim rebuilt with one alternative source combination"
  scope: "The specific claim identified in the dominant stratum's reason stage"
  constraint: "One claim per iteration. No bundling."
  rationale: >
    Bundling multiple claim rebuilds defeats the exploration gradient -- if iteration N
    rebuilds three claims and the gate improves, there is no attribution for which
    rebuild caused the improvement. The next iteration cannot distinguish productive
    from unproductive rebuilds.

  action_types:
    source_swap: >
      Replace existing source with a higher-grounding alternative. Use when the claim
      scope is correct but the evidence source is weak (e.g., trade publication ->
      peer-reviewed study).
    source_add: >
      Add a corroborating source to an existing partial-grounding claim. Use when
      the claim has some source support but falls below grounding_target.
    claim_rewrite: >
      Narrow the claim scope to match what the available evidence can actually support.
      Use when no source can support the claim as stated but a scoped version (smaller
      number, hedged mechanism, narrower comparative) is groundable. The rebuilt claim
      must remain commercially accurate.
    claim_archive: >
      Mark the claim as unable to ground with available sources. Escalate to cos-grounding
      repo. See review gate requirement in Adversarial Critic findings (Probe 3).
      REQUIRED: do not execute claim_archive without human-review confirmation.
      The archive action removes a claim from active COS outputs -- this is a content
      production decision, not a loop-internal state change.

  claim_archive_review_gate:
    trigger: "reason stage proposes action_type=claim_archive"
    required_action: >
      PAUSE loop. Surface to operator with the following information:
        - claim text
        - all source combinations tried (from attempt_ledger for this claim)
        - grounding scores achieved across attempts
        - proposed archive rationale
      Require explicit human confirmation before executing archive.
      On confirmation: proceed to act (archive) and observe (outcome_label=escalated).
      On rejection: treat as failed iteration; operator may suggest alternative source.
    rationale: >
      Claim archiving removes content from COS production outputs. This is a content
      decision with business impact -- not an internal loop state change. A loop should
      not autonomously remove COS claims without human review. Identified as Sev 2
      finding in Adversarial Critic pass.
```

### Observe

```yaml
observe_config:
  destination: "Module 19 attempt_ledger"
  write_trigger: "After act stage completes, before cadence fires for next iteration"

  ledger_entry_fields:
    loop_id:
      value: "kf-loop-cos-grounding"
      required: true
    iteration_number:
      type: integer
      required: true
      description: "Monotonically increasing within loop_id partition"
    timestamp:
      type: ISO8601
      required: true
    stratify_axis:
      value: "claim_type + source_corpus"
      required: true
    stratify_stratum:
      type: string
      required: true
      description: "The specific (claim_type, source_corpus) pair for this iteration"
      example: "(numeric, industry-report)"
    root_cause_title:
      type: string
      required: true
      description: "High-level grounding failure pattern for this claim type"
      examples:
        - "numeric-source-insufficient"
        - "mechanism-overclaiming-source"
        - "comparative-single-benchmark"
    hypothesis_summary:
      type: string
      required: true
      format: "Short predicate form, < 20 words, verb-object structure"
      description: "The specific source combination tried in this iteration -- the EXCLUSION TARGET"
      examples:
        - "APA 2021 meta-analysis + Nielsen 2019 industry report for numeric reach claims"
        - "WebSearch Statista 2023 + HBR 2020 for comparative effectiveness claims"
    action_taken:
      type: string
      required: true
      enum: [source_swap, source_add, claim_rewrite, claim_archive]
      description: "The one-variable rebuild action applied in the act stage"
    outcome_label:
      type: string
      required: true
      enum: [improved, failed, partial, canary_failure, escalated]
      descriptions:
        improved: "Rebuilt claim grounding_score >= grounding_target"
        failed: "Rebuilt claim grounding_score < grounding_target"
        partial: "Grounding score improved but still below grounding_target"
        canary_failure: "Verify canary was missed -- Module 15 scoring is unreliable. Loop paused."
        escalated: "Claim rebuilt twice without success; filed to cos-grounding repo. No further in-loop attempts."
    metric_delta:
      type: float
      required: false
      description: "Grounding score delta vs. prior iteration for this claim"
    stratify_note:
      type: string
      required: false
      description: "Canary claim text + expected grounding_score=0; or degenerate-case notes"
    active_mode:
      type: string
      required: true
      enum: [full, degraded]
      description: "Environment mode at time of this iteration"
      note: >
        All degraded-mode entries must carry active_mode=degraded. Degraded entries
        at grounding=0.60 MUST NOT trigger auto-filing to Module 21 (M21 v7.5.0
        at_threshold_degraded clause). Full-mode verification is deferred.
```

### Monitor

```yaml
monitor_config:
  plateau_window: 5
  similarity_metric: edit_distance
  similarity_threshold: 0.85

  plateau_condition: |
    Last 5 entries in attempt_ledger (same loop_id AND same stratify_stratum)
    ALL have outcome_label IN (failed, partial, escalated)
    AND pairwise similarity(hypothesis_summary) > 0.85 across window
    => plateau_detected

  plateau_meaning: >
    A (claim_type, source_corpus) stratum is systematically ungroundable with available
    sources. This may indicate: (1) the grounding_target is too high for this corpus type,
    (2) the claims in this stratum are structurally ungroundable, or (3) the source corpus
    requires human research beyond in-loop capability.

  action_on_plateau:
    escalation_required: true
    do_not_auto_continue: true
    message_format: |
      KF-LOOP PLATEAU ESCALATION
      Loop: kf-loop-cos-grounding
      Stratum: [claim_type, source_corpus]
      Last [plateau_window] iterations: all failed/partial/escalated with similar source hypotheses.

      Attempt ledger excerpt:
      [last 5 entries for this stratum]

      Resolution options:
      (1) Lower grounding_target for [source_corpus] corpus type in this stratum
      (2) Reclassify these claims as ungroundable for in-loop; file systematic cos-grounding bead
      (3) Pause loop -- human research required for this claim type / source combination
      (4) Override and continue with new evidence (requires explicit confirmation + new source direction)

  canary:
    description: >
      Monitor must accept synthetic ledger_excerpt input for validation.
    implementation: |
      Synthetic plateau excerpt: 5 entries, all outcome_label=failed, hypothesis_summary
      edit_distance < 0.15 (very similar). Expected output: plateau_detected=true.
      Non-plateau excerpt: 5 entries, alternating improved/failed. Expected: plateau_detected=false.
      Absence of canary check is a Critic linter HIGH finding.
```

---

## Adversarial Critic Pass (Inline)

This spec has at least one significant flaw -- find it.

**Framing:** The two probes below that identify Sev 2 findings have been fixed within this spec. The fixes are integrated into the stage configuration above. Two additional probes are documented as Sev 3 advisory (no fix required).

---

**Probe 1 -- Small-stratum problem: Wilson-CI infeasible on many strata [Sev 2, FIXED]**

The two-axis stratification (claim_type x source_corpus) produces up to 15 possible strata (3 x 5). The gate_window is 20 claims per stratum. In a typical COS review session, many strata will have far fewer than 20 failing claims. A numeric+no-source stratum might have 2 failing claims; Wilson-CI on n=2 produces a confidence interval from ~0.09 to ~0.91 -- too wide to distinguish WAIT from DIAGNOSE, and uninformative for promotion decisions.

**Risk (Sev 2):** Running Wilson-CI on n < 8 produces misleading gate outputs. A stratum with 2/2 successes computes ci_lower=0.34 -- below promote_threshold=0.90 -- forcing continued iteration even when the stratum is effectively resolved. Conversely, 2/2 successes could be treated as "probably converged" when the sample is statistically worthless.

**Fix applied:** Adaptive gate_window rule in gate_config. Strata with n < 8 receive unconditional WAIT (no Wilson-CI). Strata with 8 <= n < 20 use all available claims as the window with a logged note. Only strata with n >= 20 use the standard gate_window. This is not a semantic change to the promote_threshold -- it is a sample-validity guard. Sparse strata accumulate claims over multiple sessions before gate arithmetic is meaningful.

---

**Probe 2 -- Degraded mode promotion math [Sev 3, advisory -- no flaw]**

Question: with grounding_target=0.60 and promote_threshold=0.90 in degraded mode, can the loop ever promote?

Answer: yes. The binary pass/fail for each claim in degraded mode is (grounding_score >= 0.60). promote_threshold=0.90 means ci_lower >= 0.90 -- i.e., 90% of the gate_window claims must reliably score >= 0.60. The gate does not require ci_lower to reach 0.90 of the grounding score itself. A batch of web-accessible sources grounding 90% of numeric claims to >= 0.60 will promote. The math is valid.

**Advisory (Sev 3):** The spec should make this distinction explicit so implementers do not conflate "promote_threshold on the Wilson-CI lower bound" with "promote_threshold on the grounding score." The gate_config block now includes an explicit clarifying note. No structural change required.

---

**Probe 3 -- claim_archive removes production content with no review gate [Sev 2, FIXED]**

claim_archive is one of the four action_types in the act stage. The loop catalog note says "mark as unable to ground; escalate to cos-grounding repo." The original spec did not include a human-review gate before archiving.

**Risk (Sev 2):** Archiving a claim is a content production decision -- it removes an assertion from active COS outputs. A loop that autonomously archives claims based on failed grounding attempts could remove commercially relevant content that simply requires human research to ground. The loop has no mechanism to distinguish "ungroundable with automated sources" from "ungroundable with all sources"; a claim that fails three web searches may be groundable with a paid database or a human literature review.

**Fix applied:** claim_archive_review_gate block in act_config. The loop PAUSES before executing claim_archive and surfaces the full attempt history to the operator. Execution requires explicit human confirmation. This is not a soft recommendation -- the act stage MUST NOT proceed with claim_archive without confirmation. The review gate is structural, not advisory.

---

**Probe 4 -- Degraded mode and ship disposition in the reason chain [Sev 3, advisory]**

Module 05 research variant degraded_mode states: "ship disposition unavailable." The loop catalog entry flags this as a constraint. Question: does "ship disposition unavailable" prevent the reason chain from completing?

Answer: no. The reason chain needs the Expert research variant to propose a source combination and the Grounding module to score it. The rebuild hypothesis (Step 1 output) and the grounding score (Step 2 output) do not depend on ship disposition. Ship disposition is the final confidence signal that a claim is ready to publish as-is. In degraded mode, the Builder in Step 3 rebuilds the claim with soften or rebuild framing instead of ship-ready framing. The chain completes; the output is a soften/rebuild-dispositioned claim rather than a ship-confirmed claim.

**Implication documented in the reason chain:** Degraded mode produces rebuild-only hypotheses. No claim rebuilt in degraded mode carries ship-confirmed status. Full-mode verification (Claude Code + Asta) is required to reach ship disposition. observe entries for degraded iterations carry active_mode=degraded; downstream consumers must not treat these as ship-ready without a full-mode re-verification pass. This is an operational constraint, not a loop-breaking flaw.

---

## Deployment Notes

### Environment Modes

```yaml
environment_modes:
  full_mode:
    description: "Claude Code with Asta MCP connected"
    grounding_target: 0.85
    ship_disposition: available
    source_access: [Allen AI Semantic Scholar, peer-reviewed corpus, web-accessible]
    note: "Standard operating mode. All action_types available."

  degraded_mode:
    description: "Claude Projects -- no Asta/Alia MCP"
    grounding_target: 0.60
    ship_disposition: BLOCKED (per Module 05 research variant degraded_mode)
    source_access: [web-accessible only]
    note: >
      All ledger entries in degraded mode carry active_mode=degraded.
      Degraded-mode rebuilds at grounding=0.60 MUST NOT auto-file to Module 21
      (M21 v7.5.0 at_threshold_degraded clause). Full-mode re-verification is
      required before any degraded-mode rebuilt claim reaches ship status.
      At session start in degraded mode, surface this limitation:
      "[kf-loop-cos-grounding] DEGRADED mode: Asta MCP unavailable.
      Grounding capped at 0.60. Ship disposition blocked. Full-mode verification required."

  environment_detection:
    on_session_start: >
      Probe Asta MCP with a known-good DOI (e.g. "DOI:10.1145/3313831.3376744").
      If probe succeeds within 5 seconds: active_mode=full.
      If probe fails or times out: active_mode=degraded. Log immediately.
    persistent_degraded: >
      Claude Projects deployments without Asta/Alia MCP operate in permanent degraded_mode.
      Do not re-probe on every iteration. Set active_mode=degraded at session start and
      retain for the session.
```

### cos-grounding Repo Integration

This loop is a consumer of the cos-grounding repo, not a replacement for it. The division of labor is:

- **This loop:** automated grounding improvement for claims where alternative sources exist in web-accessible or scientific corpus search. Handles the majority of low-grounding claims from COS content sessions.
- **cos-grounding repo:** canonical grounding hub for claims requiring human research, paid databases, or verified citation work. Receives escalated claims from this loop.

Claim routing:
1. Check `~/Scripts/cos-grounding/findings/composed/` first (pre-verified citations). If a handoff packet covers the current claim or claim class, use it -- do not duplicate research.
2. Run in-loop research (Expert research variant) for claims not covered by pre-verified packets.
3. Escalate to cos-grounding repo (file a bead in `~/Scripts/cos-grounding/.beads/`) when: (a) claim has been rebuilt twice without success (escalated outcome), (b) claim_archive is confirmed by operator, or (c) monitor plateau escalation fires.

Handoff mechanism for escalated claims:
- Primary: Orchestra `push_artifact(destination="cos-grounding", ...)` if available
- Fallback: direct file to `~/Scripts/cos-grounding/claims/` with a corresponding bead in the cos-grounding bead store

Per CLAUDE.md: "When any COS-adjacent project surfaces a claim that needs source verification... route the work TO cos-grounding." This loop is the automated first-pass; cos-grounding is the canonical resolver for anything the loop cannot handle.

### Claim Type Priorities

When multiple strata have failing claims, stratify selects the dominant stratum by count. As a tiebreaker (equal count across strata), prioritize in this order:

1. (numeric, no-source) -- ungrounded quantitative claims are highest business risk; a figure with no source is an active liability
2. (numeric, industry-report) -- numeric claims sourced from industry reports often cite figures with no primary source; second priority
3. (mechanism, industry-report) -- industry reports frequently overstate causality; mechanism claims need peer-reviewed support
4. All other strata by count

This priority ordering is a tiebreaker only. If (comparative, web-accessible) has more failing claims than (numeric, no-source), stratify selects (comparative, web-accessible) per the standard GROUP BY COUNT DESC rule.

### Cross-Repo Work Routing

Any claim requiring external research beyond web-accessible sources -- academic papers not in Asta, proprietary research, primary data collection -- must be routed to cos-grounding via a bead. Do not attempt to obtain proprietary or paywalled sources within this loop. The loop's research scope is:
- Full mode: Allen AI Semantic Scholar corpus + public web
- Degraded mode: public web only

Anything beyond this scope is a cos-grounding bead, not a loop action.

---

## Quick Implementation Checklist

A reader implementing this loop from scratch should verify all of the following before deployment:

```
Pre-stratification:
[ ] failure_axis_key (claim_type, source_corpus) fields present and categorical in all evidence rows
[ ] Valid enum values enforced: claim_type in [numeric, mechanism, comparative]
[ ] Valid enum values enforced: source_corpus in [first-party-research, peer-reviewed, industry-report, web-accessible, no-source]
[ ] HALT logic implemented for missing or invalid axis values

Gate:
[ ] Adaptive gate_window: unconditional WAIT for n < 8; log for 8 <= n < 20
[ ] Gate branching: PROMOTE exits loop; DIAGNOSE goes to monitor; neither fires stratify->act
[ ] Gate canary: gate(successes=0, n_trials=gate_window) == DIAGNOSE

Recall:
[ ] Module 19 attempt_ledger filtered by loop_id=kf-loop-cos-grounding AND current stratum
[ ] Exclusion constraint targets hypothesis_summary, NOT root_cause_title
[ ] cos-grounding/findings/composed/ loaded before Expert fires

Reason chain:
[ ] Environment mode detected at session start (Asta probe)
[ ] Degraded mode: ship disposition blocked; degraded=true flag propagated through handoff
[ ] Claim escalation check: if >= 2 prior failed/partial entries for this specific claim -> skip chain, escalate
[ ] hypothesis_summary in short predicate form (< 20 words, verb-object structure)

Verify:
[ ] Canary claim injected (no-source claim, expected grounding_score=0)
[ ] Canary miss triggers HIGH finding and loop pause, not a passing outcome
[ ] circuit_breaker_exempt=true

Act:
[ ] One claim per iteration -- no bundling
[ ] claim_archive requires human-review confirmation before execution -- PAUSE and surface to operator

Observe:
[ ] active_mode field written to every ledger entry
[ ] escalated is a distinct outcome_label (claim filed to cos-grounding, no further in-loop attempts)
[ ] Degraded entries at grounding=0.60 carry active_mode=degraded; do not auto-file to Module 21

Monitor:
[ ] Synthetic plateau canary: 5-entry similar-failure excerpt -> plateau_detected=true
[ ] Non-plateau canary: mixed excerpt -> plateau_detected=false
[ ] Plateau escalation blocks auto-continue; presents four resolution options to operator
```
