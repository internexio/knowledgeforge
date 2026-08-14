# KnowledgeForge Changelog

All notable changes to KnowledgeForge are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [7.36.0] - 2026-08-14

### Changed

- **Module 00 (Orchestrator) v7.24.0 → v7.25.0** — M26 awareness. Module reference
  table gains an M26 row (KF_Loop_Substrate, v1.2.0). M19 row updated to v7.5.0
  (attempt_ledger addition). M26 added to Related list. Identity strings updated.
  All platforms recompiled to pick up M00 changes.

---

## [7.35.0] - 2026-08-13

### Added

- **Loop catalog complete** — Four remaining KF-LOOP instantiation specs written to
  `specs/kf-loops/`. Module 26 bumped to v1.2.0; loop catalog entries promoted from
  DEFINED to BUILT with spec cross-references:
  - **kf-loop-adversarial-yield** — gate on per-mode in-range binary series (Wilson-CI);
    canary rotation enforced; low-traffic DIAGNOSE advisory trigger added.
  - **kf-loop-kb-health** — contradiction class requires topic-cluster pairwise input;
    canary namespace exclusion enforced; n_trials_minimum=5 gate guard added.
  - **kf-loop-pattern-extraction** — inverted Wilson-CI saturation gate; two-pass
    stratify for derived failure_signature labels; zero-iteration PROMOTE guard added.
  - **kf-loop-cos-grounding** — adaptive gate_window for sparse two-axis strata (15
    strata possible); claim_archive_review_gate requires human confirmation before
    archiving production content; degraded mode (Claude Projects, no Asta) documented.

---

## [7.34.0] - 2026-08-12

### Added

- **Module 26 — KF-LOOP Substrate (v1.2.0)** — Formalizes iterative self-improvement
  loops as a named orchestration primitive with shared substrate. Two invariants: I1
  (evidence stratification via deterministic GROUP BY) and I2 (cross-iteration attempt
  ledger with exclusion constraint). Five loops cataloged; one reference instance
  (mode-selection self-calibration). Wilson-CI gate. Gate branching semantics explicit
  (post adversarial-critic). Accretion candidate taxonomy fields added.
- **Module 14 (Metacognitive Monitor) v6.6.0 → v6.7.0** — `iteration_scope` block
  added to Check 1.
- **Module 19 (Memory Architecture) v7.4.0 → v7.5.0** — `attempt_ledger` added
  (DECISION-1 resolved: ledger placed in Module 19, Option a).

---

## [7.33.0] - 2026-08-09

### Added

- **OSS hygiene files for public release:**
  - `LICENSE` — Apache-2.0, copyright 2026 David Pedersen
  - `SECURITY.md` — vulnerability disclosure via security@internexio.com; scoped to
    prompt framework security surface (no production infrastructure)
  - `CONTRIBUTING.md` — module edit conventions, versioning rules, PR requirements;
    references `CLAUDE.md`, `check-identity-drift.py`, `verify-deterministic-build.sh`
  - `CODE_OF_CONDUCT.md` — professional conduct standards

---

## [7.32.0] - 2026-08-09

### Changed

- History scrub pipeline for public release — `scripts/scrub-manifest.yaml` added.
  14 internal paths removed from all commits. Content patterns sanitized (home directory
  paths, author email, internal endpoint URLs, source_session values, project name refs).
  `wiki/index.md` cleaned of 13 dangling entries pointing to removed wiki files.

---

## [7.31.0] - 2026-08-09

### Added

- **Platform bindings and distribution matrix for public release:**
  - `platform-bindings/vscode.yaml` — fixed 2 internal refs
  - New deferred binding stubs: `generic.yaml`, `cursor.yaml`, `chatgpt.yaml`,
    `gemini.yaml`
  - `docs/dist-matrix.md` — platform capability matrix and module coverage across all
    9 bindings (claude-code, claude-projects, vscode, plugin-bundle, codex, cursor,
    chatgpt, gemini, generic); output file counts, binding status legend, and "Adding a
    New Platform" guide

---

## [7.30.0] - 2026-08-09

### Changed

- **Hooks curation:** `kf-stats.py` added to deploy list — all 8 hooks now shipped
  by `scripts/deploy-hooks.sh`.
- **`platform-bindings/plugin-bundle.yaml`** — genericized internal references;
  consumer repo name list replaced with generic language; MCP connector and
  deduplication inventory entries genericized to operator-populated placeholders.

---

## [7.29.0] - 2026-08-09

### Changed

- **COS conditional blocks for public release:**
  - **Module 07 (Critic)** v7.5.0 → v7.6.0 — comms variant sections wrapped in
    `<!-- kf:if cos -->` blocks. Public builds (cos=false) strip COS MCP integration
    from the compiled critic skill and agent.
  - **Module 08 (Synthesizer)** v6.7.1 → v6.8.0 — comms-domain detect/emit blocks
    wrapped in `<!-- kf:if cos -->` blocks. Public builds strip COS template emit
    logic from synthesizer output.
  - **Module 11 (Calibrator)** v7.1.1 → v7.2.0 — comms-heavy detection and COS
    profile emit blocks wrapped in `<!-- kf:if cos -->` blocks. Public builds strip
    COS profile artifact emit from calibrator output.
  - `platform-bindings/claude-code.yaml` gains `cos: false` public default alongside
    existing `telemetry: false`.

---

## [7.28.0] - 2026-08-09

### Changed

- **Telemetry conditional block for public release:**
  - **Module 00 (Orchestrator)** v7.23.0 → v7.24.0 — Per-Turn Mode Telemetry section
    wrapped in `<!-- kf:if telemetry -->` blocks. Public builds (telemetry=false) strip
    the telemetry directive from the compiled `kf-meta.md`. Internal builds use
    `--set telemetry=true` to include it.
  - `platform-bindings/claude-code.yaml` gains `flags:` section with `telemetry:
    false` as the public default.

---

## [7.27.0] - 2026-08-09

### Added

- **Mid-chain premise invalidation** — deterministic re-entry when a downstream chain
  step signals that a prior step's premise has been invalidated:
  - **Module 00 (Orchestrator)** v7.22.0 → v7.23.0 — mid-chain re-entry rule added to
    Mode Chaining Behavior (STATIC ZONE). When `response.upstream_invalidation` is
    non-null at Sev2+, orchestrator halts chain and re-enters at `invalidated_step_id`.
    Sev1 logs only. Repeated invalidation of the same step escalates to user. Re-entry
    exempt from 3-failure circuit breaker.
  - **Module 03 (Coordination Patterns)** v7.5.0 → v7.6.0 — `response_schema` added
    to `hc-strategist-to-builder` with `upstream_invalidation` worked example.
    Three canonical ui-checks added. Registry count unchanged (13).
  - **Module 04 (Specification Templates)** v7.3.0 → v7.4.0 — `upstream_invalidation`
    optional field added to `handoff_contract` template. KF 7.4 field summary table added.
  - **Module 19 (Memory Architecture)** v7.3.1 → v7.4.0 — 4th canonical
    `re_routing_trigger` added: `downstream_step_premise_invalidation` (severity
    threshold: Sev2).
- New wiki entry: `orchestration/2026-08-09_kf-governance-over-async-transport.md`

---

## [7.26.0] - 2026-07-08

### Added

- **Integration opt-in/out system (`kf-integrations.yaml`):**
  - Canonical template declaring 7 integrations: mempalace, cos, asta, beads,
    gitnexus, gemini_routing, orchestra. Opt-out model (all enabled by default).
  - New hook utility: `kf_integrations.py` — `is_enabled(name)`, `get_config()`,
    `resolve_python_path()`, `resolve_br_path()`. Stdlib-only; no PyYAML required.
  - Integration guards added to hooks: `mempalace-wiki-mine.py`, `kf-route.py`,
    `kf_wiki_search.py`, `taskmaster-priority-awareness.py`.
  - `br-prime-safe.sh` — graceful `br prime` wrapper; reads integrations config,
    fails silently if beads is disabled or not on PATH.

### Changed

- **Module 08 (Synthesizer)** v6.7.0 → v6.7.1 — "COS MCP unavailable" clarified to
  cover any `mcp__cos-mcp__*` tool error, not only explicit disable. Detection signals
  run regardless of availability.
- **Module 11 (Calibrator)** v7.1.0 → v7.1.1 — same clarification as M08.

---

## [7.25.0] - 2026-07-08

### Added

- **Module 08 (Synthesizer) — comms-domain detection + COS template emit:**
  Phase 4.5 added. Evaluates 4 signals; emit trigger at ≥1 signal + ≥2 examples +
  confidence ≥0.6. New output: `cos_template_output`. Graceful degradation to wiki-only
  emit without COS MCP.
- **Module 11 (Calibrator) — comms-heavy detection + COS profile emit:**
  5-signal detection (explicit domain, directories, file patterns, package.json deps,
  no-primary-code); threshold 2+. New outputs: `cos_agent_profile_output` +
  `cos_audience_profile_output`. Adds CLAUDE.md comms section embedding. Graceful
  degradation to CLAUDE.md-only with placeholder section.
- New template files: `cos-template-emit.jinja2`, `cos-agent-profile.json.jinja`,
  `cos-audience-profile.json.jinja`.

---

## [7.24.0] - 2026-07-07

### Added

- **Module 07 (Critic) v7.3.0 → v7.4.0 — Communications (comms) variant:**
  When the artifact under review is a communications piece (marketing/sales copy, email,
  ad, blog draft, social post, press release), Critic delegates to COS MCP
  `analyze_full_comms` for 7-framework analysis and wraps results in standard Critic
  severity-ranked presentation. Detection: explicit user labels OR implicit structure
  (headline+CTA, persuasive register, audience targeting). Graceful degradation to
  native Critic without COS MCP.

---

## [7.23.0] - 2026-07-07

### Added

- **Module 22 (Semantic Wiki Search) Phase 2 activated** (v7.3.1 → v7.4.0):
  - Wing-derivation defect fixed; `mempalace.yaml` markers added to all 11 wiki
    subdirectories.
  - `kf_wiki_search.py` created: two-phase retrieval (metadata pre-filter + score
    fusion at 0.65 cosine + 0.20 importance + 0.15 recency weights).
  - `kf-route.py` extended with keyword-based domain inference; top-3 wiki results
    injected as `[Wiki context — M22 §2]` block in prompt.

---

## [7.22.0] - 2026-07-02

### Audit Remediation — Six Findings from 2026-07-02 CP Review

Module 00 was deployed at v7.9.0 while core was at v7.21.0. Six findings resolved
(two Sev 1, two Sev 2, two Sev 3); two additional adversarial-critic findings fixed.

### Fixed

- **Module 00 (Orchestrator) v7.9.0 → v7.22.0** — Always-On Behavioral Patches and
  Per-Turn Mode Telemetry added to STATIC ZONE. On Claude Code these were already
  present in `~/.claude/rules/kf-meta.md`; the STATIC ZONE addition makes Claude
  Projects equivalent.

### Added

- **Module 03 (Coordination Patterns) v7.4.0 → v7.5.0** — Handoff Contract Registry
  expanded 10 → 13:
  - Contract C: `hc-expert-to-strategist` — Expert→Strategist chain
  - Contract D: `hc-expert-research-to-expert-regular` — Research→Expert chain
  - Contract E: `hc-expert-research-to-builder` — with `degraded_ship_prohibited`
    cross-field check (Sev1: `ship` disposition prohibited when `degraded=true`)

### Changed

- **Module 05 (Expert Agent) v7.3.0 → v7.4.0** — Research variant `degraded_mode`
  extended: accretion boundary note (score exactly 0.6 + degraded = no auto-file),
  deployment note for MCP-unavailable environments.
- **Module 16 (Operational Bounds) v7.2.0 → v7.3.1** — `expert.research` added to
  `mode_selection_accuracy.per_variant` (9 variants total). Rationale text corrected:
  "Expert 4 variants" → "Expert 5 variants".
- **Module 21 (Knowledge Accretion) v7.4.0 → v7.5.0** — `grounding_gate` gains
  `at_threshold_degraded` clause; `above_threshold.condition` fixed from `>` to `>=`.

---

## [7.21.0] - 2026-07-01

### Changed

- **Module 24 (Verbatim History Mining) v6.5.1 → v6.6.0** — Phase 1 / Phase 2 split
  applied to Retrieval Protocol. `search_memories(filters={…})` was aspirational; actual
  Phase 1 signature is `mempalace_search(query, limit?, wing?, room?)` — no filter params.
  Phase 2 client-side post-filter deferred. Flow diagram, anti-pattern table, and Tier 3
  relationship section updated.
- **Module 19 (Memory Architecture) v7.3.0 → v7.3.1** — Tier 3 cross-refs corrected
  to Phase 1 tool surface.

---

## [7.20.0] - 2026-07-01

### Changed

- **Module 19 (Memory Architecture) v7.2.1 → v7.3.0** — `.claude/rules/` placed as a
  compiled Tier 0 projection (not a new tier); `activation_profile.trigger` governs
  compilation target. `auto-memory` defined as harness-managed scratch below Tier 1,
  not KF-managed. Full `tier_stack` YAML + comparison table added.

---

## [7.19.0] - 2026-06-30

### Changed

- **Module 21 (Knowledge Accretion) v7.3.0 → v7.4.0** — `native:true` gate clause
  activated. Three-signal content classifier: (a) general-advice shape, (b) no failure
  anchor, (c) no tool/path specificity — all three required. Conservative conjunction
  keeps expected suppression rate below 5%. Human override always wins. Suppression-event
  review added to linter (step 7); `native_suppression_tracking` block added to
  calibration section.

---

## [7.18.0] - 2026-06-29

### Changed

- **Module 00 (Orchestrator) v7.7.0 → v7.8.0** — two additions to Per-Turn Mode
  Telemetry placement rule, closing 76.6% → 100% coverage gap measured on τ²-bench
  telecom (kf-bench-95k, June 22):
  - **Case 2 "length does not exempt"** — a single-sentence action turn before a tool
    call still requires the marker in its text block.
  - **Case 3 "marker debt rule"** — k consecutive tool-only turns create k marker debts;
    the next text-bearing turn must carry k+1 markers total.

---

## [7.17.1] - 2026-06-29

### Fixed

- **`kf-compile.py`** (compiler-only; no module spec change) — `add_compile_header()`
  no longer prepends `<!-- Generated by kf-compile ... -->` when content starts with
  `---`. The leading comment pushed `---` to line 2, causing Claude Code's agent loader
  to silently skip all 11 KF agent files. Nightwatch `iteration_loop` was dark for
  3 consecutive nights (2026-06-27/28/29). Fix: return content unchanged when it starts
  with `---`; source attribution lives in `.kf-compile-manifest.json`. CP bundle stamp
  insertion updated to be frontmatter-aware.

---

## [7.17.0] - 2026-06-21

### Changed

- **Module 00 (Orchestrator) v7.6.0 → v7.7.0** — Per-Turn Mode Telemetry placement
  rule rewritten as three cases for tool-calling / agentic contexts (τ²-bench Phase-1
  exposed ~20% untagged turns in tool-orchestration loops):
  - Case 1 (text-only) — marker is the last line
  - Case 2 (text + tool-call) — marker is the last line of the text block, before tool calls
  - Case 3 (tool-only) — deferred carry-forward: PREPEND prior turn's mode/decision as
    the first line of the next text-bearing turn

  Reframes marker stakes: "A missing marker is a data-loss event equivalent to dropping
  a required field in a JSON response."

---

## [7.16.0] - 2026-06-21

### Changed

- **Module 23 (Taxonomy Enforcement) v6.9.0 → v6.10.0** — removed deprecated
  `orchestration` topic from the `patterns` domain (deprecated in 6.6.0). Migrated 4
  entries: 2 retagged to `validation`, 1 to `orchestration/queue-pattern`, 1 to
  `performance/cache`. Both deprecated `orchestration` topics now resolved across all
  domains.

---

## [7.15.0] - 2026-06-20

### Changed

- **Module 23 (Taxonomy Enforcement) v6.8.0 → v6.9.0** — expanded two domains:
  - Compiler: added `bootstrap-divergence` + `multi-repo-pipeline`; re-topicked 2 entries
  - Orchestration: added `queue-pattern` + `parallel-workflow` + `task-decomposition`;
    removed deprecated self-referential `orchestration` topic; migrated 4 entries

---

## [7.14.0] - 2026-06-20

### Changed

- **Module 23 (Taxonomy Enforcement) v6.7.1 → v6.8.0** — added `schema-evolution`
  topic to the `migrations` domain, retiring the self-referential `migrations → migrations`
  anti-pattern.

---

## [7.13.0] - 2026-06-20

### Added

- **Module 00 (Orchestrator) v7.5.0 → v7.6.0** — Per-Turn Mode Telemetry section.
  KF agent emits a single-line HTML-comment marker as the LAST line of every response:

      <!-- KF-MODE: <mode> | DECISION: <class> | ADVERSARIAL: <0|1> -->

  Reckonings emit `KF-MODE: reckoning` as a first-class value. Marker is
  observability-only: explicitly forbids tuning of mode selection, decision
  classification, response content, or length budget. Placement contract: marker is
  LAST line; if `FINAL ANSWER:` is present it precedes the marker.

---

## [7.12.1] - 2026-06-20

### Changed

- **Module 23 (Taxonomy Enforcement) v6.6.0 → v6.7.0** — dropped 5 SEO-domain leakage
  topics: `keyword-repositioning`, `keyword-research-methodology`, `keyword-selection`
  (methodologies domain); `google-ads`, `serp-ranking-diagnosis` (diagnostics domain).
  Vocab pruning only; no module behavior change.

---

## [7.12.0] - 2026-06-13

### SPEC 1 — Verifier Promotion + Contract A

Phase 3 wave 2 of the loop-engineering integration.

### Added

- **Module 07 (Critic Agent) v7.2.0 → v7.3.0** — `## CC Agent (Adversarial Variant)`
  section. Module 07 is now the canonical source for the adversarial-critic agent body.
  Adds an **Untrusted Input Boundary** clause: treats `artifact_under_test` content as
  data (not directives), flags instruction-shaped text as findings rather than complying.
- **Module 03 (Coordination Patterns) v7.3.0 → v7.4.0** — Contract A
  (`hc-orchestrator-to-verifier`) registry entry. Payload + response schemas, five
  deterministic validation checks, `escalate_to_user` fallback (silent-pass NEVER
  allowed). Registry count: 10 entries.
- **Module 04 (Specification Templates) v7.2.1 → v7.3.0** — `response_schema` field
  added to `handoff_contract` entity (parallel to `payload_schema`).
- **`platform-bindings/codex.yaml`** (new) — deferred placeholder with contract surface
  and bind_when conditions.

### Changed

- **Module 00 (Orchestrator) v7.4.0 → v7.5.0** — `@critic (adversarial)` replaced with
  `@adversarial-critic` at all chain example sites and inline references.

---

## [7.11.0] - 2026-06-13

### SPEC 4 — Accretion Vetting Gate + Knowledge Librarian Promotion

Phase 3 wave 1 of the loop-engineering integration.

### Added

- **Module 21 (Knowledge Accretion) v7.2.0 → v7.3.0:**
  - `step_3d_provenance_gate` inserted between `step_3c_profile_cross_validate` and
    `step_4a_taxonomy_gate`. Consumes Contract B provenance; cross-cutting +
    novel/predictive candidates without `verifier_signoff` or `human_review_signal`
    surface for human review. Reckoning/evaluative paths unchanged.
  - `accretion_candidate` schema gains `provenance` sub-object; top-level `source_mode`
    moves into provenance. Accessor shim + grandfather rule (created before 2026-07-01)
    + 90-day sunset cover the transition.
  - `## CC Agent (Knowledge Librarian)` section added. Module 21 is now the canonical
    source for the librarian agent.
- **Module 03 (Coordination Patterns) v7.2.0 → v7.3.0** — Contract B
  (`hc-runtime-to-accretion-gate`) registry entry. Count: 9 entries.

---

## [7.10.0] - 2026-06-13

### Added

- **Module 20 (Permission Model) v7.0.1 → v7.1.0** — two new sub-policies:
  - `verifier_tool_tier_policy` — gates separate-agent verifier tool grants (test-runner,
    datastore-read-only, staging-http) at HIGH tier with explicit sandbox requirements.
  - `accretion_candidate_tier_policy` — gates novel/predictive-derived accretion
    candidates at HIGH tier regardless of target scope. Annotation tags do not satisfy
    HIGH-tier confirmation.

---

## [7.9.0] - 2026-06-12

### Added

- **Module 21 (Knowledge Accretion) v7.1.4 → v7.2.0** — Knowledge Base Linter
  violation-event counter. Unblocks the Phase 2 `cc_hooks` emitter. Storage in
  `.kf/linter/` (gitignored). Event log + JSON snapshot hybrid. Three-check gate on
  snapshot consumption: freshness, numeric re-derivation, `source_rule` existence.
  `linter_check.kind` restricted at v1 to stateless artifact patterns. Dotfile-exclusion
  scan rule added; `wiki/.linter_offset` moved to `.kf/linter/offset`.

---

## [7.8.0] - 2026-06-12

### Added

- **Module 25 (Entity Relationship Analysis) v7.0.3 → v7.1.0** — `entity_paths` field
  on ERA output, populated by a GitNexus-primary + session-cached-grep-fallback resolver.
  Glob derivation rules, deterministic comparison function (literal-char prefix + lex
  tiebreak), `resolver_source` demoted to diagnostic metadata. Closes the <1%
  `path_bound` bottleneck.

### Changed

- **Module 21 (Knowledge Accretion) v7.1.3 → v7.1.4** — `step_2c` entity_paths lookup;
  `step_3c` ERA-globs-on-global-scope handled via downgrade (not rejection); `path_globs_meta`
  sidecar field added.

---

## [7.7.1] - 2026-06-12

### Fixed

- **Module 21 (Knowledge Accretion) v7.1.2 → v7.1.3** — `step_5_file` path formula
  corrected. Was `{wiki_root}/{domain}/{topic}.md` (one file per topic) — actual wiki
  uses `{wiki_root}/{domain}/{YYYY-MM-DD}_{slug}.md` (one file per entry). Pre-existing
  spec bug; 218 wiki entries already followed the corrected formula.

---

## [7.7.0] - 2026-06-11

### Added

- **Module 00 (Orchestrator) v7.3.0 → v7.4.0** — Always-On Behavioral Patches section.
  Four Karpathy-inspired principles loaded as always-on rules (~300 tokens), patching
  failure modes that selective-activation misses:
  1. **Think Before Coding** — state assumptions, surface multiple interpretations,
     push back when a simpler approach exists
  2. **Simplicity First** — minimum code, no speculative features, no abstractions for
     single-use code
  3. **Surgical Changes** — touch only what's required; don't refactor working code or
     improve adjacent style
  4. **Goal-Driven Execution** — define success criteria before acting; loop until
     criteria met

---

## [7.6.0] - 2026-06-10

### M23 Vocabulary Drift Reconciliation (Option C — hybrid expand + grandfather)

### Added

- **Module 23 (Taxonomy Enforcement) v6.5.2 → v6.6.0:**
  - 5 new domains: `methodologies`, `diagnostics`, `orchestration`, `migrations`,
    `compiler`. Domain count 10 → 15. ~55 new topics from on-disk frontmatter
    (empirical baselines, not speculative).
  - Grandfathering section: entries created before 2026-06-10 exempt from domain/topic
    field requirement.
  - `patterns/orchestration` topic DEPRECATED (collision with new `orchestration`
    domain). Lazy migration on next touch.

### Changed

- **Module 21 (Knowledge Accretion) v7.1.1 → v7.1.2** — Gate 4a grandfather pre-check;
  linter schema-completeness and backdating-detection rules added.

---

## [7.5.0] - 2026-06-10

### Compiler Phase 2 — `cc_rules` and `settings.kf.json` Hook Fragment Emitters

### Added

- **`compiler/kf-compile.py`** — two new compile-time emitters for the `claude-code`
  target:
  - `cc_rules` — per-module YAML `cc_rules` entries compile into `.claude/rules/kf/*.md`
    with `paths:` frontmatter. Orphan cleanup on each compile.
  - `cc_settings_fragment` — per-module `cc_hooks` entries aggregate into
    `settings.kf.json`, shallow-merged into `.claude/settings.json` via sidecar manifest.
- Idempotency contract: `.claude/rules/kf/` (compile-time) vs
  `.claude/rules/kf-runtime/` (runtime) partition separation.

### Changed

- **Module 21 (Knowledge Accretion) v7.1.0 → v7.1.1** — `step_5b_emit_path_gated_rule`
  added to `claude_code_runtime.filing`.

---

## [7.4.0] - 2026-06-10

### Added

- **Module 21 (Knowledge Accretion) v7.0.6 → v7.1.0** — `activation_profile` block
  (`trigger`, `decidability`, `miss_cost`, `native`, `path_globs`) on
  `accretion_candidate` metadata. `native:true` added as a third gate clause (alongside
  novelty + reuse value) in deferred-activation mode at v1 (default `false`). Steps
  `step_2c_activation_profile` and `step_3c_profile_cross_validate` added to filing
  protocol.

---

## [7.3.1] - 2026-05-25

### Changed

- **Module 22 (Semantic Wiki Search) v7.3.0 → v7.3.1** — dup-check threshold
  recalibrated from 0.9 to 0.85. Empirical probing against the live MemPalace
  collection (2415 drawers) showed exact-content queries cap at ~0.889 cosine
  similarity due to chunked drawer storage; the 0.9 spec threshold was empirically
  unreachable. Hook code shipped at the calibrated value; end-to-end test confirmed.

---

## [7.3.0] - 2026-05-24

### M22 Phase 1 Reconciliation — MemPalace Adoption

Original v6.5.0 spec assumed direct ChromaDB integration; MemPalace (already installed +
connected as MCP, wraps ChromaDB internally) is the actual vector store. Post-adversarial
review found 5 sev-2+ flaws in the initial draft; scope reduced to minimum-viable
MemPalace wrapping for Phase 1.

### Changed

- **Module 22 (Semantic Wiki Search)** — full rewrite + scope reduction. Phase 1 = dup-check
  only via direct Python import from `mempalace.mcp_server`. Wing/room scoping, score
  fusion, and orchestrator-context retrieval moved to Phase 2.
- **Module 21 (Knowledge Accretion) v7.0.6** — `step_4b_embedding` rewritten: embedding
  happens inside MemPalace's mine pipeline. CC Doc Gate 4b rewritten from "blocking
  embedding gate (pre-write)" to "detect-and-warn dup-check (post-write PostToolUse)".
- **Module 23 (Taxonomy Enforcement) v6.5.2** — M22 cross-reference updated: Phase 1
  does not consume taxonomy vocab at retrieval time; write-time enforcement remains
  mandatory.
- **Module 00 (Orchestrator) v7.3.0** — Module Reference rows for M22 and M25 qualified
  to Phase 1 reality.
- **Module 25 (ERA) v7.0.3** — Memory Retrieval Enhancement section qualified: entity-
  scoped metadata filter integration with M22 is Phase 2.
- **Module 06 (Quick Reference) v7.3.0** — Module Reference Table, Infrastructure
  Modules table, and Integration Graph qualified to Phase 1 reality.

---

## [7.2.1] - 2026-05-11

### Editorial Back-Port from CP

F1–F7 findings from the kf-7.2.0 audit redo. Applied to compiled CP artifacts on
2026-05-11; this release lifts them into core modules so future compiles don't revert
them. No orchestrator behavior change.

### Changed

- **Module 00 (Orchestrator) v7.2.1** — Module Reference table annotated; Mode Selection
  Accuracy section adds weekly adversarial calibration cadence note; `re_routing_triggers`
  cross-reference added; variant ID storage rule documented.
- **Module 04 (Specification Templates) v7.2.1** — `16_Operational_Bounds` added to
  `related` list.
- **Module 06 (Quick Reference) v7.2.0** — Brought from 6.6.1 to 7.2 baseline: Mode
  Variants section, KF-4 metric #10, KF-8 Routing Decision Log, Handoff Contract Registry,
  Trigger Disambiguator, Module Reference extended to 22/23/24/25.
- **Module 19 (Memory Architecture) v7.2.1** — `re_routing_triggers` enumeration: 3
  canonical triggers + 3 non-triggers; `selected_variant` field annotated with
  unqualified-storage + read-time-composition rule.

---

## [7.2.0] - 2026-05-10

### Tool-Calling Architecture Audit — Typed Mode Handoffs, Mode-Selection Accuracy Metric

Cascade — ERA → Strategist → Builder → Critic. Source: *"The Roadmap to Mastering Tool
Calling in AI Agents"* mapped through KF abstractions (modes-as-tools,
orchestrator-as-model). Audit trail in `docs/planning/Typed_Mode_Calling/`.

### Added

- **Module 04 (Specification Templates)** — `Handoff_Contract` entity with required fields
  (`source_mode`, `target_mode`, `payload_schema`, `fallback_path`, `validation_checks`).
  `validation_checks[].assertion` restricted to five canonical forms.
- **Module 04 (Specification Templates)** — `trigger_disambiguator` entity. Predicate-based
  resolution of ambiguous trigger phrases. Default fallback always `user_disambiguation`.
- **Module 03 (Coordination Patterns)** — Handoff Contract Registry. 8 active mode-to-mode
  edges registered: Builder→Critic auto-verify, Expert→Builder, Strategist→Builder,
  Synthesizer→Builder, Critic→Builder revision, Debugger→Strategist, Critic-audit→Strategist,
  Strategist→Calibrator.
- **Module 16 (Operational Bounds)** — Metric #10 `mode_selection_accuracy`. Primary
  measurement: re-routing rate over rolling 100-event window. Calibration: weekly
  Critic-adversarial sample of 20 decisions. Thresholds: 90% overall, 95% per-variant.
- **Module 19 (Memory Architecture)** — `routing_decision_log` schema v1.0 (audit trail
  of every routing decision; rolling 1000 entries + permanent re-route archive).
- **Module 19 (Memory Architecture)** — `tier_2_metric_aggregates` schema for weekly
  metric persistence beyond rolling window.

### Changed

- **Module 05 (Expert Agent)** — Expert `variants[]` formalized: `regular`,
  `infrastructure`, `ml_infrastructure`, `era`. `decision_type_exercised` annotated with
  enum constraint and `consumed_by: orchestrator_auto_verify_gate`.
- **Module 07 (Critic Agent)** — Critic `variants[]` formalized: `regular`, `linter`,
  `audit`, `adversarial`. Adversarial variant declares explicit `chain_context`
  `activation_predicate`.
- **Module 00 (Orchestrator)** — writes `routing_decision_log` entry on every mode
  activation; evaluates metric #10 thresholds at chain completion.

### Wiki

New entries: `patterns/mode-variants-taxonomy.md`, `diagnostics/handoff-payload-schema-gap.md`,
`methodologies/external-source-to-kf-mapping.md`.

---

## [7.1.0] - 2026-04-29

### Module 25 — Entity Relationship Analysis + Inhibition-First Framing

### Added

- **Module 25 — Entity Relationship Analysis (ERA)** (`25_entity_relationship_analysis.md`)
  — adversarial checklist for relationship-graph reasoning. Compiled to both CC Skill and
  CC Doc. ERA post-routing pass: entity graph, cardinality, coupling.
- User education layer: `00_User_Quickstart.md`, Navigator Loop Detection (step 4),
  `kf-fit-check` CC Skill.

### Changed

- **Module 18 (Salience Allocation)** — inhibition-first framing spec note; salience
  scoring now starts from "what to suppress" rather than "what to amplify," aligned with
  imagination-as-suppression evidence.
- Compiler fix: titled `## CC Skill` sections now handled by prefix-aware stop condition.

### Wiki

New entries: `imagination-as-suppression` (architecture), `disambiguation-loop-hint`
(orchestration patterns).

---

## [7.0.5] - 2026-04-25

### Fixed

- Deterministic-first meta-principle propagated to compiled outputs. Now reads
  consistently across orchestrator and all platform variants: "Before invoking LLM
  judgment, exhaust deterministic checks. Before fixing, reproduce. Before acting, triage."

---

## [7.0.4] - 2026-04-22

### Added

- **Module 07 (Critic Agent)** — loop exit protocol with `circuit_breaker_exemption`
  block. Critic can now exit a verification loop cleanly when the same finding fires
  twice without new evidence, instead of triggering the 3-failure circuit breaker.
- **Module 21 (Knowledge Accretion)** — terminal state spec: quality test,
  missing-indicator handling, `accretion_pending` flag.

---

## [7.0.3] - 2026-04-20

### Added

- **Module 07 (Critic Agent) + Module 17 (Temporal Knowledge)** — boundary scoring and
  research staleness gate. Findings older than the temporal staleness threshold require
  re-grounding before counting.
- **Module 21 (Knowledge Accretion)** — `source_fingerprint` deduplication: partial
  match case, dedup principle, Critic-finding-specific fingerprint formula.

---

## [7.0.2] - 2026-04-18

### Added

- **Module 03 (Coordination Patterns)** — dual fingerprinting protocol completed: delta
  rule, expected benefit, cross-reference to `loop_exit_protocol`. Each chain step carries
  both input fingerprint and state-delta fingerprint, enabling exact loop detection.

---

## [7.0.1] - 2026-04-15

### Added

- **Module 02 (Builder Agent)** — pre-registration git protocol: skip conditions,
  deviation rationale required when implementation diverges from pre-registered plan.
- **Module 09 (Debugger Agent)** — CI failure feedback loop: fingerprint comparison
  logic for repeated CI failures from the same root cause.
- **Module 16 (Operational Bounds)** — Pure Decision Functions: decision catalog +
  testability format.
- **Module 20 (Permission Model)** — Allow-With-Mutation expanded: hook contract, audit
  trail, deny-vs-mutate decision rule.

---

## [7.0.0] - 2026-04-13

### Compiler Pipeline — Single Source of Truth, Hook-Driven Routing, CI Automation

KnowledgeForge 7.0.0 is a full infrastructure build — six phases completed across one
development cycle. The framework went from a manually-maintained set of files to a
compiled, hook-driven, CI-automated system. All module specs now live in
`knowledgeforge` (core). Variant repos (`knowledgeforge-cc`, `knowledgeforge-cp`) are
compilation targets — never edited directly for module-level changes.

### Phase 1 — Pre-Prompt Routing Hook

- `kf-route.py` fires as a `UserPromptSubmit` hook before Claude sees any prompt
- Calls Gemini Flash Lite with a compact module index (~2K tokens) to classify the
  request and inject `[KF-ROUTE]` directives
- Replicates Claude Projects' semantic retrieval in Claude Code at ~200ms overhead

### Phase 2 — Decomposed Skills and Docs

- Monolithic orchestrator decomposed into discrete `## CC Skill` and `## CC Doc`
  sections per mode
- Skills load on-demand via the hook layer; docs are reference material
- Cross-cutting cognitive infrastructure modules (12–24) compile into
  `.claude/docs/knowledgeforge/` for dynamic loading

### Phase 3 — Session Lifecycle Hooks

Five hooks completing the session lifecycle:

- `kf-stop-validator.py` (Stop) — per-mode completion checklists block premature stops
- `kf-precompact.py` (PreCompact) — saves routing index + active mode state before
  context compaction
- `kf-postcompact.py` (PostCompact) — restores state after compaction
- `kf-edit-nudge.py` (PostToolUse) — appends checkpoint nudge after every 10 file edits
- `kf-session-start.py` (SessionStart) — restores previous session state on launch

### Phase 4 — Module Spec Updates

15 modules updated with spec-level changes from six integration plans. Key additions:
deterministic-first meta-principle (M00), pre-registration git protocol (M02), dual
fingerprinting + spec drift checkpoint (M03), context hygiene rules.

### Phase 5 — Model Profiles

Five model profiles for all KF-relevant models, each mapping strengths, weaknesses, and
KF overhead calibration: `claude-sonnet-4`, `claude-opus-4`, `gpt-5`,
`gemini-flash-lite`, `gemma-3-4b`.

### Phase 6 — Compiler MVP

- `kf-compile.py` extracts tagged sections from canonical module specs and writes them
  to variant repo paths. Dry-run, diff, and full-compile modes.
- Three GitHub Actions workflows: `compile-cc.yml`, `sync-hooks-cc.yml`, `compile-cp.yml`

---

## [6.6.3] - 2026-04-12

### Added

- **Module 01 (Navigator Agent)** — `kf-fit-check` CC Skill: surfaces whether KF
  overhead is appropriate for the current request, helping users learn when to bypass
  mode activation entirely.
- `00_User_Quickstart.md` — user onboarding entry point; first-run guidance, mode
  trigger cheatsheet, when-not-to-use-KF examples.

---

## [6.6.2] - 2026-04-11

### Added

- **Module 01 (Navigator Agent)** — Step 4 Loop Detection: detects when the user is
  re-asking the same routing question and offers a confusion-detection bypass.

---

## [6.6.1] - 2026-04-10

### Changed

- Version bump and consistency pass across all modules to align with CC/CP variant
  compilation prep work that became 7.0.0.

---

## [6.5.0] - 2026-04-09

### Memory Upgrade — Semantic Search, Taxonomy Enforcement, Verbatim History Mining

Three new modules completing the KF memory system from write-time vocabulary control
through query-time semantic retrieval across Tier 0 and Tier 3.

### Added

- **Module 22 — Semantic Wiki Search** — Metadata-gated two-phase retrieval over wiki/
  (Tier 0). Phase 1: domain/topic/tag pre-filter. Phase 2: vector similarity scoring.
  Score fusion: 0.65 semantic + 0.20 importance + 0.15 recency-weighted decay. Grep
  fallback with mandatory logging.

- **Module 23 — Taxonomy Enforcement** — Fixed controlled vocabulary enforced at write
  time. Three-tier hierarchy: domain → topic → tags. 10 domains, ~40 topics, 55 approved
  tags. Write-time rejection with nearest-match suggestions. Vocabulary extension protocol
  requires justification, sample entries, version bump, and index rebuild.

- **Module 24 — Verbatim History Mining** — Tier 3 rewrite from grep-only to semantic
  vector search via MemPalace. Core finding: verbatim + semantic = 96.6% R@5 vs 84.2%
  R@5 with pre-summarized — 12.4-point permanent recall loss from pre-compression.
  Importance-weighted exponential decay with half-lives from 7 days (importance 1) to
  90 days (importance 5).

### Changed

- **Module 19 (Memory Architecture)** — Tier 3 description updated to MemPalace sidecar
  with semantic retrieval; recall benchmarks added.
- **Module 21 (Knowledge Accretion)** — Filing protocol extended with Gate 4a (taxonomy
  validation) and Gate 4b (embedding); filing is now Step 5, after both gates pass.

---

## [6.4.0] - 2026-04-07

### Neuro-Symbolic Identity — Empirical Validation, Cost Observability

KF 6.4 establishes KF's architectural identity as a neuro-symbolic system. Duggan et al.
(ICRA 2026) validated the pattern independently: symbolic orchestration routing to neural
execution outperforms end-to-end by ~3× on success rate and ~100× on energy efficiency.

### Added

- **Architectural Identity section** in Module 06 (Quick Reference) — neuro-symbolic
  pattern definition, empirical results table, KF design-decision mapping.
- **Token Cost Per Mode metric (#9)** in Module 16 (Operational Bounds) — per-mode token
  tracking with 40% chain budget ceiling, rolling 20-activation average.
- `wiki/architecture/neuro-symbolic-pattern-validation.md` — filed to Tier 0; importance
  4, grounding 0.85.

---

## [6.3.2] - 2026-04-07

### Fixed

- **Module 17 (Temporal Knowledge)** — removed verbatim duplicate of entire file (merge
  artifact from v6.3.1); added `18_Salience_Allocation` to `related` field.
- **Module 18 (Salience Allocation)** — added `21_Knowledge_Accretion` to `related`
  field (broken reciprocal reference).
- **Module 06 (Quick Reference)** — added 6.3.1 content to KF-6 and KF-7 sections.

---

## [6.3.1] - 2026-04-07

### Knowledge Maintenance — Autonomous Decay, Pinning, and Consolidation

### Changed

- **Module 17 (Temporal Knowledge)** — importance-weighted exponential decay model;
  knowledge pinning (pinned entries exempt from staleness pressure); domain half-life
  table; decay-staleness_risk consistency check.
- **Module 18 (Salience Allocation)** — access-driven salience signal from wiki access
  logs; access frequency and recency feed the salience score formula.
- **Module 21 (Knowledge Accretion)** — autonomous maintenance cycle with cost budgeting
  (heuristic-first, LLM-optional); access logging with LRU+LFU composite salience;
  lineage-safe consolidation protocol; rotating linter coverage guarantee.

---

## [6.3.0] - 2026-04-05

### Infrastructure Planning — First-Class Triggers, Templates, Domain Checklists

### Added

- Infrastructure planning mode triggers in Module 00: infrastructure architecture design,
  hosting audit / SPOF analysis, self-hosted model deployment / GPU sizing, competitive
  moat / defensibility analysis.
- **Infrastructure Architecture Specification template** in Module 04 — service catalog,
  networking topology, hardware plan, model-to-hardware mapping, hot-swap / failover,
  phased deployment, security model, competitive moat analysis.
- **Hosting Audit & Decomposition Readiness template** in Module 04 — server inventory,
  networking audit, SPOF analysis, decomposition readiness ratings, extraction priority
  ranking.
- **Expert infrastructure domain adaptations** in Module 05: `infrastructure_architecture`,
  `ml_infrastructure`, `hosting_audit` domains with compound failures, blast radius
  probes, assumption inversions, design implications.

---

## [6.2.0] - 2026-04-04

### Knowledge Accretion — Closing the Knowledge Evaporation Loop

### Added

- **Module 21 — Knowledge Accretion** (`21_knowledge_accretion.md`) — cross-cutting
  knowledge persistence.
  - Accretion signal detection across all modes (novelty + reuse value conditions)
  - Dual runtime: Claude Code (auto-file to Tier 0) vs Claude Projects (surface to user)
  - `ACCRETION_CANDIDATE` flag system with category tagging
  - Knowledge base linter via Critic health check variant
  - Grounding-gated accretion: candidates below 0.6 require caveat before filing
  - Extends Module 19 to four tiers (Tier 0 as accretion target layer)

### Changed

- **Module 19 (Memory Architecture)** — extended from three-tier to four-tier model;
  Tier 0 (persistent domain knowledge) added as accretion target layer.
- **Module 07 (Critic Agent)** — knowledge base linter variant added; linter
  contradictions feed back as accretion candidates (self-correcting loop).
- **Module 08 (Synthesizer Agent)** — accretion check in Phase 4.
- **Modules 12, 14, 15, 17, 20** — accretion integration points added.
- All remaining modules — version bumped to 6.2.0.

---

## [6.1.0] - 2026-04-01

### Production-Tested Orchestration Architecture

The orchestrator completely rewritten as a behavioral prompt; two new cognitive
infrastructure modules added. Architecture directives from analysis of production-tested
patterns in Anthropic's own Claude Code infrastructure.

### Added

- **Module 19 — Memory Architecture** — three-tier memory system for long-session routing
  accuracy:
  - Tier 1 (routing index): always loaded, ~150 chars/entry, max 30 entries
  - Tier 2 (mode state): loaded on demand when a mode activates, swapped on transitions
  - Tier 3 (history): never re-read in full — grep-only for specific identifiers
  - Context pressure response at 75% / 80% / 85% utilization thresholds

- **Module 20 — Permission Model** — layered risk classification and capability gates:
  - LOW (reckonings, routing, formatting) — auto-approve
  - MEDIUM (evaluative judgments, 2-mode chains) — auto-approve with logging
  - HIGH (novel judgments, 3+ mode chains, irreversible recommendations) — human
    confirmation required
  - Circuit breakers: 3-failure threshold and 2-chain-step threshold

### Changed

- **Module 00 (Orchestrator)** — complete rewrite as behavioral prompt. Static/dynamic
  boundary established: static zone (core rules, decision classification, mode triggers,
  routing index) stays identical across all modes for cache preservation. Automatic
  adversarial verification on qualifying chains (Builder output, Strategist
  recommendations, 3+ mode chains). Circuit breakers.
- **Module 07 (Critic Agent)** — adversarial variant: distinct activation triggers,
  framing ("assume at least one significant flaw exists, find it"), yield tracking
  (healthy 20–80%).
- **Module 14 (Metacognitive Monitor)** — user-side session health monitoring:
  repetition detection, escalation signals, correction frequency tracking.
- All remaining modules — version bumped to 6.1.0.

---

## [6.0.0] - 2026-03-28

### Cognitive Architecture Overhaul

### Added

- **Module 12 — Calibration Layer** — multi-run stability scoring and bias detection
- **Module 13 — Decision Classification** — Reckoning / evaluative / novel judgment routing
  (the Ozymandias Test)
- **Module 14 — Metacognitive Monitor** — self-monitoring, stuck state detection,
  confidence tracking
- **Module 15 — Grounding Scores** — evidence quality scoring (0.0–1.0) and citation
  grounding
- **Module 16 — Operational Bounds** — scope constraints, guard rails, context
  utilization targets (40–80%)
- **Module 17 — Temporal Knowledge** — knowledge cutoff awareness and recency weighting
- **Module 18 — Salience Allocation** — attention and detail weighting across response
  components

### Changed

- **Meta-principle established:** KF modes patch Claude's weaknesses, not scaffold its
  strengths — modes only activate when they prevent a known failure mode.
- **Navigator redesigned** — fires only on genuine ambiguity; clear intents bypass
  entirely.
- Decision classification runs on every request before routing: reckoning → direct
  answer < 50 tokens; evaluative/predictive → mode activation; novel → expanded
  reasoning + human review flag.

---

## [5.1.0] - 2026-01

### Added

- **Module 11 — Calibrator Agent** — generates complexity-appropriate AI coder
  configuration files (CLAUDE.md, .cursorrules, .windsurfrules); right-sizes guardrails
  so hobby projects don't get enterprise scaffolding.

---

## [5.0.0] - 2026-01

### Expanded Agent Platform

### Added

- **Module 07 — Critic Agent** — systematic quality assurance; surfaces gaps,
  contradictions, unstated assumptions, and edge cases; read-only reviewer
- **Module 08 — Synthesizer Agent** — extracts reusable patterns from examples; every
  pattern requires anti-patterns; creates frameworks with applicability boundaries
- **Module 09 — Debugger Agent** — systematic problem diagnosis through hypothesis
  generation, testing, and elimination; requires >0.8 confidence before declaring root
  cause
- **Module 10 — Strategist Agent** — evaluates options with explicit trade-offs and
  reversibility assessment; forces prioritization — never recommends "do everything"

---

## [4.0.0] - 2024

### The Great Simplification

A complete architectural overhaul. Consolidated from 41 files down to 7, focusing on
essential patterns that deliver maximum value.

### Changed

- **Major:** Consolidated 41 files into 7 focused components
- Unified agent mode structure across Navigator, Builder, QA, and Strategist
- Consistent UNDERSTAND → REASON → SPECIFY → NAVIGATE workflow
- Simplified agent definitions to core behaviors only

---

## [3.1.0] - Previous release

The comprehensive multi-file architecture. Real-world usage revealed opportunities for
significant simplification.

- 41 files across multiple directories
- Granular agent configurations, extensive documentation per component

---

## [3.0.0] - Foundation release

- Initial multi-agent framework
- Core reasoning patterns (UNDERSTAND → REASON → SPECIFY → NAVIGATE)
- Navigator, Builder, QA, and Strategist modes
- Claude Projects integration

---

## [2.x] - Early iterations

Identified the four core agent modes; established the importance of clear routing
(Navigator) and separate quality review (QA / Critic).

---

## [1.0.0] - Initial concept

- First proof of concept
- Single-agent reasoning enhancement
- Basic structured output patterns

---

## Version Philosophy

| Version | Focus |
|---------|-------|
| 1.0 | Proof of concept |
| 2.x | Feature exploration |
| 3.0–3.1 | Comprehensive coverage (41 files) |
| 4.0 | The Great Simplification — 41 files → 7 |
| 5.0 | Expanded agent modes: Critic, Synthesizer, Debugger, Strategist |
| 5.1 | Calibrator Agent |
| 6.0 | Cognitive architecture: 7 infrastructure modules, meta-principle |
| 6.1 | Production-tested orchestration: 3-tier memory, permission model, adversarial verification |
| 6.2 | Knowledge Accretion (M21): cross-session learning, 4-tier memory |
| 6.3 | Infrastructure Planning: Expert domain adaptations, architecture + hosting audit templates |
| 6.3.1 | Knowledge Maintenance: importance-weighted decay, autonomous maintenance cycle |
| 6.4 | Neuro-symbolic identity: empirical validation, token cost observability |
| 6.5 | Memory upgrade: semantic wiki search (M22), taxonomy enforcement (M23), verbatim history mining (M24) |
| 6.6 | Navigator polish: loop detection, kf-fit-check, user quickstart |
| 7.0 | Compiler pipeline: single source of truth, hook-driven routing, CI automation |
| 7.0.x | Module completions: pre-registration git, dual fingerprinting, loop exit protocol, accretion dedup |
| 7.1 | M25 Entity Relationship Analysis; inhibition-first salience framing |
| 7.2 | Typed mode handoffs (Handoff_Contract); mode-selection accuracy metric; routing decision log |
| 7.3 | M22 Phase 1 MemPalace: dup-check gate at calibrated 0.85 threshold |
| 7.4 | M21 activation_profile on accretion candidates |
| 7.5 | Compiler Phase 2: cc_rules + settings.kf.json emitters |
| 7.6 | M23 vocab: 5 new domains, ~55 new topics, grandfathering policy |
| 7.7 | Always-on behavioral patches (Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven) |
| 7.8 | M25 entity → path-glob resolver (GitNexus-primary + grep fallback) |
| 7.9 | M21 linter violation-event counter |
| 7.10 | M20 sub-policies: verifier + accretion candidate tool tier policies |
| 7.11 | SPEC 4: accretion vetting gate, Contract B, Knowledge Librarian agent |
| 7.12 | SPEC 1: adversarial-critic Untrusted Input Boundary; Contract A |
| 7.13 | Per-turn KF-MODE telemetry marker |
| 7.14–7.16 | M23 vocab expansion + cleanup (compiler + orchestration domains) |
| 7.17–7.18 | Per-turn marker: tool-calling three-case rule; 76.6% → 100% compliance |
| 7.19 | M21 native:true gate activated (three-signal content classifier) |
| 7.20 | M19 tier model: .claude/rules/ as compiled Tier 0 projection |
| 7.21 | M24 + M19 MemPalace Phase 1/2 split: actual tool surface documented |
| 7.22 | Audit remediation: Always-On in STATIC ZONE, 13-contract registry, grounding gate boundary |
| 7.23 | M22 Phase 2 active: semantic wiki search operational |
| 7.24 | M07 Critic comms-domain variant via COS MCP |
| 7.25 | M08/M11 COS emit: Synthesizer + Calibrator comms-domain structured output |
| 7.26 | M07 adversarial inverse-premise check; kf-integrations opt-in/out; br-prime-safe.sh |
| 7.27 | Mid-chain re-entry rule; upstream_invalidation signal |
| 7.28–7.32 | Public release: telemetry/COS conditional blocks, OSS hygiene, dist matrix, history scrub |
| 7.33 | Apache-2.0 LICENSE, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md |
| 7.34 | M26 KF-LOOP Substrate: eight-stage iterative loop primitive, five loop catalog entries, Wilson-CI gate |
| 7.35 | Loop catalog complete: adversarial-yield, kb-health, pattern-extraction, cos-grounding specs |
| 7.36 | M00 v7.25.0 with M26 awareness: module reference table, routing, identity strings updated |
