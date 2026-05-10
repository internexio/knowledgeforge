# Changelog

All notable changes to KnowledgeForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The authoritative machine-readable changelog is `kf.yaml`. This file mirrors major releases
in human-readable form. For per-module change history, see the `changelog:` block at the top
of each module spec in `modules/`.

---

## [7.2.0] - 2026-05-10

### 🛠️ Tool-Calling Architecture Audit (Track C)

Cascade — ERA → Strategist → Builder → Critic. Source article: *"The Roadmap to Mastering
Tool Calling in AI Agents"* (7-step practitioner guide), mapped through KF abstractions
(modes-as-tools, orchestrator-as-model). Defensibility audit driver.

Cascade docs: `docs/planning/Typed_Mode_Calling/chain-log-{01..04}-tool-calling.md`.

### Added

- **Module 04 — `Handoff_Contract` entity.** Formal mode-to-mode contract template with
  required fields: `source_mode`, `source_variant`, `target_mode`, `target_variant`,
  `payload_schema`, `fallback_path`, `validation_checks`. Each contract requires ≥1
  deterministic check. The `assertion` field must reduce to one of five canonical forms:
  field-presence, enum-membership, cardinality, schema-conformance, cross-field. Resolves
  ERA F2 (handoff payload schema gaps) and F5 (Handoff naming inconsistency).
- **Module 04 — `trigger_disambiguator` entity.** Formal predicate-based resolution of
  ambiguous trigger phrases. Predicate enum: `output_type_difference`, `domain_specificity`,
  `chain_context`, `user_disambiguation`. Default fallback is always `user_disambiguation`
  — never silent-fail to wrong route. Resolves F1 root cause and F6.
- **Module 03 — Handoff Contract Registry.** 8 active mode-to-mode handoff edges
  registered as `handoff_contract` instances: Builder→Critic auto-verify,
  Expert→Builder, Strategist→Builder, Synthesizer→Builder, Critic→Builder revision,
  Debugger→Strategist, Critic-audit→Strategist, Strategist→Calibrator. Each entry has
  explicit `payload_schema`, `fallback_path`, and ≥1 deterministic `validation_check`
  using the canonical assertion forms.
- **Module 16 — Metric #10 `mode_selection_accuracy`.** Primary measurement is
  re-routing rate (`1 - re_routed_events / total_routing_events`) over a rolling 100-event
  window — deterministic, sourced from Module 19 `routing_decision_log`. Calibration is
  a weekly Critic-adversarial sample of 20 decisions; Sev 2+ findings count as routing
  failures undetected by re-routing rate. Variant-aware thresholds: 90% overall, 95%
  per-variant. Drift rule: if adversarial-sample failure rate exceeds (1 - primary) by
  >5pp, primary is under-counting. Resolves F1 + F4.
- **Module 19 — `routing_decision_log` schema v1.0.** Audit trail of every routing
  decision (separate concern from `routing_index` state). Fields include `timestamp`,
  `turn_number`, `request_text` (truncated), `candidate_modes`, `selected_mode`,
  `selected_variant`, `trigger_phrase_matched`, `predicate_used`, `re_routed`,
  `re_route_reason`. Retention: rolling 1000 entries + permanent re-route archive at
  `wiki/operations/routing-log/{YYYY-MM}.md`. Resolves F4.
- **Module 19 — `tier_2_metric_aggregates` schema.** Weekly metric persistence beyond the
  rolling window. Stores `total_routing_events`, `re_routed_events`, `per_mode_accuracy`,
  `per_variant_accuracy`, `adversarial_sample_failure_rate`, `calibration_drift_flag`.
  Permanent retention. Source data for metric #10 calibration after window rolls.
- **Wiki — 3 accretion entries.** `wiki/patterns/mode-variants-taxonomy.md` (the new
  pattern of mode label + variants[] taxonomy as architectural primitive),
  `wiki/diagnostics/handoff-payload-schema-gap.md` (reusable ERA finding category for
  multi-mode-chain audits), `wiki/methodologies/external-source-to-kf-mapping.md`
  (3-step methodology for translating practitioner guides through KF abstractions).

### Changed

- **Module 05 — Expert `variants[]` formalized** — `regular`, `infrastructure`,
  `ml_infrastructure`, `era`. Each variant declares `trigger_phrases`, `output_format`,
  `output_template`, `typical_chain_position`, `decision_type_typical`, `risk_tier`.
  `decision_type_exercised` output field (required since 6.6.1) now annotated with
  explicit enum constraint and `consumed_by: orchestrator_auto_verify_gate` note.
  Backward-compat default rule preserved until KF 7.3.0. Resolves F1 + F3.
- **Module 07 — Critic `variants[]` formalized** — `regular`, `linter`, `audit`,
  `adversarial`. The adversarial variant declares an explicit `chain_context`
  `activation_predicate` ("active chain pattern includes adversarial verification step;
  decision_type_exercised >= evaluative_judgment"). Aggregate "Critic accuracy"
  metrics that conflated 4 distinct output formats per mode label are now
  variant-disaggregated. Resolves F1.
- **Module 04 — Usage Notes table extended** — "Handoff" row renamed to "Handoff
  Contract"; "Trigger Disambiguator" row added; legacy "Handoff" row preserved for
  backward reference. KF 7.2 field summary table added.
- **Module 16 — Corrective Action Summary table extended** — 5 new rows for metric #10
  thresholds (90/80% overall, 95/85% per-variant, calibration drift).
- **Module 00 — Orchestrator Static Zone updated** —
  - Writes `routing_decision_log` entry on every mode activation (per Module 19 schema).
  - Re-routing events (Navigator firing after initial routing, user explicit redirect,
    Critic adversarial finding "wrong mode" at Sev 2+) MUST set `re_routed: true` with
    `re_route_reason`; entries archive permanently.
  - Mode Selection Accuracy Awareness section: orchestrator evaluates Module 16 metric
    #10 thresholds at chain completion. Per-variant tracking is mandatory.
  - Identity string updated `7.0.0` → `7.2.0`.

### Resolved Findings

| ID | Severity | Concern | Resolution |
|----|----------|---------|------------|
| F1 | Sev 1 | Mode-label collisions (Critic 4 variants, Expert 4 variants) | `variants[]` formalized; metric #10 variant-aware |
| F2 | Sev 2 | Handoff payload schema gaps (8 edges, all prose-only) | `Handoff_Contract` entity + 8-edge registry |
| F3 | Sev 2 | `decision_type_exercised` not on schema | Enum constraint + `consumed_by` annotation |
| F4 | Sev 2 | No routing-decision logging | `routing_decision_log` schema + orchestrator behavior |
| F5 | Sev 3 | Handoff naming inconsistency | Absorbed into F2 (Usage Notes rename) |
| F6 | Sev 3 | Trigger phrase overlaps | Absorbed into F1 (`trigger_disambiguator`) |
| F7 | Sev 3 | Module 25 / Module 03 orphan references | Deferred to Stage 3 docs pass |

Critic phase added P2-Δ1: `validation_checks[].assertion` canonical-form constraint
(folded into Module 04 commit). Cascade exited with 0 Sev 1 findings unresolved.

---

## [7.1.0] - 2026-04-23

User education layer — `00_User_Quickstart.md`, Loop Detection (Module 01), `kf-fit-check`
skill. Module 01 version aligned to system. Compiler fix: titled CC Skill sections now
handled by prefix-aware stop condition. Disambiguation loop hint pattern filed to
`wiki/orchestration/`.

## [7.0.2] - 2026-04-23

Intermediate during user education layer work (superseded by 7.1.0 same day).

## [7.0.1] - 2026-04-16

Module 25 (ERA) now compiles to CC — added CC Doc section, CC platform binding entry,
M25 in `kf_module_index.txt`. Module 25 version bumped to 6.6.0.

## [7.0.0] - 2026-04-14

Phase 1 — UserPromptSubmit hook with Gemini Flash Lite. Phase 2 — skill files,
cross-cutting docs, slash commands in `knowledgeforge-cc`. Phase 3 — Stop gate,
PreCompact/PostCompact, PostToolUse, SessionStart hooks. Phase 4 — 15 module spec
updates (research items 1-13 + ENH-006/007). Phase 5 — 5 model profiles (Sonnet, Opus,
GPT-5, OLMo, Gemini Flash Lite). Phase 6 — compiler MVP; CC and CP variants now compiled
from core.

## [7.0.0-alpha] - 2026-04-14

Established `knowledgeforge-core` as single source of truth. Copied all 26 canonical
modules from `knowledgeforge-cp`. Organized plan documents from architecture sessions.
Created `CLAUDE.md`. Initial directory structure established.

## [6.6.1] - 2026-04-13

KF 6.x final state — CP as source of truth. 25 modules (00–24) plus ERA (25).
Architecture sessions produced 9 integration plans.

---

For the per-module changelog entries (the most granular history), see the `changelog:`
block at the top of each `modules/NN_*.md` file.
