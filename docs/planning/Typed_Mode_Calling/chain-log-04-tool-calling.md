# Chain-Log 04 — Critic Phase (Tool-Calling Audit)

**Cascade:** Stage 2 KF chain — ERA → Strategist → Builder → Critic
**Track:** C (audit-then-metric)
**Target:** KF 7.1.0
**Phase input:** chain-log-03 Builder output (9 patches P1–P9, Stage 3 handoff block)
**Loop exit protocol:** max=1 (per Module 07)

---

## 1. Completeness Check

Mechanical pass against Builder output. Every patch is checked against three structural requirements, every handoff_contract_instance against five required fields, every changelog entry against chain-log traceability.

### 1.1 Patch-level structural requirements

| Patch | Decision type tagged | Reversibility stated | ≥1 deterministic test | Status |
|-------|----------------------|----------------------|------------------------|--------|
| P1 trigger_disambiguator entity | reckoning (entity definition) | single-commit revert | 3 deterministic checks | PASS |
| P2 Handoff_Contract entity | reckoning (entity definition) | single-commit revert | 4 deterministic checks | PASS |
| P3 Critic variants[] | reckoning (schema enumeration) | single-commit revert | 4 deterministic checks | PASS |
| P4 Expert variants[] + decision_type_exercised | evaluative_judgment (BC default) | single-commit revert | 4 deterministic checks | PASS |
| P5 routing_decision_log hook | reckoning (schema definition) | single-commit revert | 5 deterministic checks | PASS |
| P6 metric #10 | evaluative_judgment (threshold setting) | single-commit revert | 4 deterministic checks | PASS |
| P7 Handoff Contract Registry | reckoning (registration of 8 instances) | single-commit revert | 4 deterministic checks across 8 edges | PASS |
| P8 orchestrator log-writing | reckoning (static-zone behavior) | single-commit revert | integration test specified | PASS |
| P9 orchestrator metric #10 awareness | evaluative_judgment (threshold reaction) | single-commit revert | integration test specified | PASS |

**Completeness rate:** 9/9. No structural omissions.

### 1.2 Handoff Contract Registry (P7) — per-edge completeness

8 edges checked against required fields (id, source_mode, source_variant, target_mode, target_variant, trigger, payload_schema, fallback_path, validation_checks).

| Edge ID | Source | Target | Payload schema | Fallback path | ≥1 validation_check | Status |
|---------|--------|--------|-----------------|---------------|----------------------|--------|
| hc-builder-to-critic-autoverify | builder | critic.regular | ✓ | escalate_to_user | 2 checks | PASS |
| hc-expert-to-builder | expert.any | builder | ✓ | route_to_navigator | 2 checks (1 Sev1) | PASS |
| hc-strategist-to-builder | strategist | builder | ✓ | request_strategist_revision | 2 checks | PASS |
| hc-synthesizer-to-builder | synthesizer | builder | ✓ | route_to_strategist | 1 check | PASS |
| hc-critic-to-builder-revision | critic.regular | builder | ✓ | escalate_to_user (loop_exit) | 2 checks | PASS |
| hc-debugger-to-strategist | debugger | strategist | ✓ | route_to_navigator | 1 check | PASS |
| hc-critic-audit-to-strategist | critic.audit | strategist | ✓ | route_to_navigator | 1 check | PASS |
| hc-strategist-to-calibrator | strategist | calibrator | ✓ | escalate_to_user | 1 check | PASS |

**Per-edge completeness:** 8/8. Every Stage 1 / ERA-identified handoff edge is covered. No orphan handoffs in the active mode set.

### 1.3 Changelog traceability

Builder pre-drafted KF 7.1.0 changelog references chain-log-01, chain-log-02, chain-log-03 by ID and section. Stage 3 completion_signal mandates chain-log-04 attachment to PR. Traceability — PASS.

---

## 2. Adversarial Pass on Builder Output

Seven candidate concerns evaluated. Findings classified by severity per Module 07 conventions (Sev 1 = blocker; Sev 2 = must resolve or escalate; Sev 3 = informational, defer permitted).

### 2.1 Findings table

| ID | Severity | Concern | Resolution |
|----|----------|---------|------------|
| C1 | Sev 2 | `validation_checks[].assertion` field accepts prose strings; "deterministic" semantics implicit, not enforced by schema. Risk — prose assertion that cannot be mechanically evaluated would silently degrade fast-fail behavior. | DELTA-PATCH P2-Δ1 (this phase) — adds spec convention rule. |
| C2 | Sev 2 | Metric #10 historical calibration depends on routing_decision_log; rolling retention of 1000 entries truncates long-window trend analysis. | RESOLVED in Builder phase via P5 `aggregation_persistence` to tier_2_metric_aggregates (weekly rollup, permanent). No delta required. |
| C3 | Sev 3 | trigger_disambiguator predicate enumeration (output_type_difference, domain_specificity, chain_context, user_disambiguation) — no defined behavior when zero predicates apply. | RESOLVED in Builder phase — `user_disambiguation` is the explicit fallback predicate (route to Navigator). Confirmed via P1 patch text. |
| C4 | Sev 3 | Module 06 (Quick Reference) does not list variants[] for Expert/Critic. Discoverability gap, not a schema-validity gap. | DEFER to Stage 3 documentation pass. Module 06 is reference-only; correctness is preserved. Logged as F7-extension. |
| C5 | Sev 3 | F7 from chain-log-01 (Module 25 ERA Agent ambiguity) carries forward — Stage 3 doc pass. | Already deferred per Stage 1 carry-forward and chain-log-03 Stage 3 pre-flight blocker note. No change. |
| C6 | Sev 2 | Architectural location of handoff registration — entity in Module 04 (P2) vs. instances in Module 03 (P7). Risk — duplication or drift between schema definition and registry. | RESOLVED by Builder placement: Module 04 owns the type definition (Handoff_Contract entity), Module 03 owns the registry of instances (handoff_contract_instance entries). Single-source-of-truth contract is maintained. No delta required. |
| C7 | Sev 3 | `decision_type_exercised` backward-compatibility — default to `evaluative_judgment` until KF 7.2.0 risks systematic mis-tagging during the migration window. | ACCEPTED with explicit rationale — Builder migration note specifies that Expert agents emitting the field explicitly take precedence over default. Conservative default is the lower-risk path. No delta. |

### 2.2 Severity rollup

- **Sev 1 findings:** 0
- **Sev 2 findings:** 3 (C1, C2, C6) — 2 resolved by Builder, 1 resolved this phase via delta-patch
- **Sev 3 findings:** 4 (C3, C4, C5, C7) — all resolved or explicitly deferred with rationale

### 2.3 Loop exit protocol

Module 07 loop_exit_protocol max=1 — single revision cycle applied this phase to address C1. No remaining Sev 1 or unresolved Sev 2 findings. Cascade exits cleanly without escalation.

---

## 3. Delta-Patch (Critic revision cycle)

### Patch P2-Δ1 — validation_checks deterministic semantics

**Target:** Module 04 Specification Templates, `Handoff_Contract` entity, `validation_checks` field schema definition. **Append to existing P2 patch text** (chain-log-03 §1 Patch P2). Not a separate commit — folded into Stage 3 task T02.

```yaml
# Append to Module 04 Handoff_Contract entity definition
# (under validation_checks field, immediately after the field_type and required_fields lines)

validation_checks:
  description: |
    Boundary checks executed at handoff time against the payload before
    the target mode receives control. Every check MUST be expressible as
    a deterministic boolean predicate over the payload (or, for impl-time
    checks, over the orchestrator's runtime state). Prose assertions are
    permitted only as documentation of the predicate's intent — the
    assertion text itself MUST be reducible to one of the following
    canonical forms:

      - field-presence:     "<field_path> is non-null"
      - enum-membership:    "<field_path> matches enum: [<values>]"
      - cardinality:        "len(<field_path>) {==, >=, <=} <int>"
      - schema-conformance: "<field_path> validates against <schema_ref>"
      - cross-field:        "<predicate over multiple field_paths>"

    Assertions that cannot be reduced to one of these forms MUST be
    rejected at spec-test time (test_module_04_handoff_contract.py adds
    a new check: every validation_checks[].assertion parses to a
    canonical form).

  schema_drift_test_addition: |
    tests/spec/test_module_04_handoff_contract.py adds:
      - check: every validation_checks[].assertion in registered
        handoff_contract_instance entries (Module 03) parses to one
        of the five canonical forms
      - check_type: deterministic
      - failure_action: spec_test_fail (block PR)
```

**Reversibility:** single-line schema addition + one new spec test; revert is single-commit.

**Affected Stage 3 task:** T02 (already specified). Test-artifact list grows by zero files (test added to existing `test_module_04_handoff_contract.py`).

**Decision type:** reckoning (specification of an existing schema field's allowed values).

**Cross-impact on P7:** All eight registered handoff_contract_instance entries in P7 already use canonical forms (verified mechanically against the five forms — every existing assertion maps to field-presence, enum-membership, or cardinality). No P7 edits required. Convention is descriptive of current Builder output, not a forcing change.

---

## 4. Accretion Gate (Module 21)

Three accretion candidates surfaced in chain-log-01 (ERA phase). Each evaluated against Module 21's two-gate protocol (novelty gate + reuse-value gate).

### 4.1 Candidate ac-era-1 — Mode-label-with-variants taxonomy

```yaml
accretion_candidate:
  id: ac-era-1
  source_chain: chain-log-01-tool-calling
  category: new_pattern
  importance: 4

  novelty_gate:
    prior_pattern_search:
      wiki_query: "mode variants OR sub-mode OR variant taxonomy"
      results: 0 prior entries
      verdict: PASS (no prior pattern)

  reuse_value_gate:
    projected_reuse_contexts:
      - any future mode-as-tool refactor where a base mode acquires sub-types
      - Expert/Critic future expansion (e.g., security_critic, performance_critic)
      - Synthesizer variants if research vs. design synthesis bifurcate
      - cross-portfolio: [project] event taxonomy (similar variant pressure on nw.* events)
    verdict: PASS (≥3 plausible reuse contexts)

  filed_to: wiki/patterns/mode_variants_taxonomy.md
  metadata:
    importance: 4
    decision_type: reckoning
    grounded_in: [chain-log-01 §F1, chain-log-03 §1 Patch P3, §1 Patch P4]
    reversibility: not applicable (descriptive pattern, not a constraint)
```

### 4.2 Candidate ac-era-2 — Handoff payload schema gap (ERA finding category)

```yaml
accretion_candidate:
  id: ac-era-2
  source_chain: chain-log-01-tool-calling
  category: reusable_diagnostic
  importance: 3

  novelty_gate:
    prior_pattern_search:
      wiki_query: "handoff schema gap OR payload contract OR boundary contract"
      results: 0 prior entries
      verdict: PASS

  reuse_value_gate:
    projected_reuse_contexts:
      - every future ERA pass on a multi-mode chain
      - VisionForge L01–L13 module boundaries (parallel structural concern)
      - COS Decision Ensemble cross-provider handoffs (analogous boundary contract)
    verdict: PASS

  filed_to: wiki/diagnostics/handoff_payload_schema_gap.md
  metadata:
    importance: 3
    decision_type: reckoning
    grounded_in: [chain-log-01 §F2, chain-log-03 §1 Patch P2, §1 Patch P7]
    reversibility: not applicable
```

### 4.3 Candidate ac-era-3 — Article-to-KF principle mapping methodology

```yaml
accretion_candidate:
  id: ac-era-3
  source_chain: chain-log-01-tool-calling
  category: transferable_framework
  importance: 4

  novelty_gate:
    prior_pattern_search:
      wiki_query: "external source mapping OR principle import OR cross-domain audit"
      results: 0 prior entries
      verdict: PASS

  reuse_value_gate:
    projected_reuse_contexts:
      - future audits driven by external research papers or engineering articles
      - Karpathy compile-query-enhance loop mapping (Module 21 already grounded here)
      - Duggan et al. neuro-symbolic validation (already informally applied)
      - any future provider-native orchestration capability comparison (defensibility audits — quarterly per user-stated strategic risk)
    verdict: PASS

  filed_to: wiki/methodologies/external_source_to_kf_mapping.md
  metadata:
    importance: 4
    decision_type: evaluative_judgment
    grounded_in: [chain-log-01 §entity_graph, chain-log-01 §coupling_analysis]
    reversibility: not applicable
    cross_reference: defensibility audit cadence (quarterly)
```

### 4.4 Accretion summary

3 candidates evaluated. 3 pass both gates. 3 file commits added to Stage 3 handoff (wiki/ directory writes — non-blocking to spec/impl commits, can ship in same PR or follow-up).

**Stage 3 handoff addendum:** 3 wiki/ file commits to be added to atomic_tasks list (T10–T12 if filed in same PR; or deferred to a follow-up doc PR per David's preference). Recommended — deferred to follow-up doc PR to keep this PR scope tight (single architectural concern: tool-calling defensibility).

---

## 5. Pass/Fail Gate (final)

| Gate criterion | Status |
|----------------|--------|
| All Sev 1 findings cleared | PASS (zero Sev 1 findings) |
| All Sev 2 findings resolved or escalated | PASS (3/3 — 2 by Builder, 1 by Critic delta P2-Δ1) |
| Loop exit protocol respected (max=1) | PASS (single revision cycle applied) |
| Atomic task count ≤10 | PASS (9 tasks, 12 if accretion writes folded in — recommendation is to defer accretion to follow-up doc PR) |
| Track C two-phase audit produced grounded metric | PASS (metric #10 with deterministic primary measurement + adversarial calibration) |
| Stage 3 handoff schema fully populated | PASS |
| Spec-commit-before-impl-commit ordering preserved | PASS (T01–T07 specs precede T08–T09 impls) |
| Reversibility stated for every patch | PASS (9/9 single-commit revert) |
| External source (article) traceably mapped to KF changes | PASS (every patch carries chain-log reference; ac-era-3 codifies the methodology) |

**Cascade exit:** CLEAN. Ready for Stage 3 Claude Code handoff.

---

## 6. Final Stage 3 Handoff Adjustments

Two amendments to chain-log-03 §3 Stage 3 Handoff Block, applied here:

1. **T02 patch reference extended:** "chain-log-03 §1 Patch P2 + chain-log-04 §3 Patch P2-Δ1." Test artifact `tests/spec/test_module_04_handoff_contract.py` gains one additional check (canonical-form validation for assertion strings). Atomic task count remains 9.

2. **Pre-flight blocker (chain-log-03) — accretion candidates:** Now resolved. Recommended path is a follow-up wiki/ doc PR (T10–T12 deferred). Three accretion candidates fully specified in §4 above — ready to file when David triggers.

---

## 7. Cascade Termination

ERA → Strategist → Builder → Critic chain complete. No re-loop into Builder. No escalation to user required (all Sev 2 closed). Stage 3 handoff is implementable as written by chain-log-03 §3 + this chain-log §6 amendments.

**Deliverables for David:**
- chain-log-01-tool-calling.md (ERA)
- chain-log-02-tool-calling.md (Strategist)
- chain-log-03-tool-calling.md (Builder + Stage 3 handoff)
- chain-log-04-tool-calling.md (Critic + final pass/fail gate + accretion gates)

**Recommended next action:** Trigger Claude Code session on `knowledgeforge-core` repo with branch `feat/tool-calling-audit-c`, attach all four chain-logs, execute T01 → T09 per spec-commit-before-impl-commit protocol.

**Critic phase complete. Cascade closed.**
