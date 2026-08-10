# KnowledgeForge Changelog

Developer-facing version history. Each module tracks its own version independently.
The system version in `kf.yaml` (`7.33.0`) reflects the highest module version.

> **Note:** This file is generated from module `## Module Metadata` blocks.
> Canonical source for each module's history is `modules/NN_*.md`.

---

## M00 — v7.24.0

### 7.9.0 (2026-07-01)
_Driver: knowledgeforge-core-7gj_

- Added routing trigger for Expert research variant (M05 v7.3.0) — "find evidence for", "ground this claim", "what does the research say", "find supporting studies", "find peer-reviewed sources" now route to expert.research (grounded_evidence_set output) rather than being absorbed into expert.regular or falling through to no-mode.
- Added chain example: Ground this claim with research, then analyze it — Expert (research) then Expert (regular)
- Disambiguator td-research-vs-expert-regular (M04) is the resolution predicate for overlap with expert.regular; registered in Module 04 § Registered Trigger Disambiguators.

### 7.8.0 (2026-06-29)
_Driver: knowledgeforge-core-rgs_

- Per-Turn Mode Telemetry — directive tightening to close compliance
gap measured at 76.6% per-turn on τ²-bench telecom (kf-bench-95k).

Two additions to the placement rule:

Case 2 (text + tool-call): added "Response length does not exempt"
clause. Short single-sentence action turns before tool calls were
dropping the marker. Now explicit: a one-sentence action turn still
requires the marker in its trailing text block.

Case 3 (tool-only): added "Marker debt rule" — k consecutive
tool-only turns create k marker debts; the next text-bearing turn
must carry k+1 markers total (k deferred + 1 current). Single
deferred when k=2 precedes is under-paying the debt.

Added short-action-turn example ("Let me look that up." before a
tool call) alongside the existing text+tool-call example.

Module 00 (7.7.0 → 7.8.0). Identity strings updated.

### 7.7.0 (2026-06-21)
_Driver: knowledgeforge-core-rgs_

- Per-Turn Mode Telemetry — extended for tool-calling / agentic contexts.
τ²-bench Phase-1 probes exposed a structural gap: ~20% of mode-active
turns were untagged because tool-only assistant turns have no text slot
for the marker, and a single n=1 KF cell solved its task in 49.7s with
ZERO markers emitted. The directive's "LAST line of every response"
phrasing assumed every turn ends in text.
- Placement rule rewritten as three cases — text-only, text+tool-call,
and tool-only — with explicit tool-turn protocol. Tool-only turns now
use a deferred-marker carry-forward: PREPEND the tool-only turn's
mode/decision to the next text-bearing turn as the first line, then
continue the response and end with that turn's own current-turn
marker. Both markers are parseable by the existing regex.
- Reframed marker stakes — "A missing marker is a data-loss event
equivalent to dropping a required field in a JSON response" — moves
marker compliance from "remember to add HTML comment" to a structural
correctness requirement under tool-orchestration load.
- Added two examples — text+tool-call turn (marker before tool call)
and tool-only-then-text-turn pair (carry-forward). Existing
reckoning and builder/final-answer examples retained.
- Marker format unchanged; existing parser (kfbench/parse_modes.py)
reads new markers without modification. Per-turn coverage measurement
(counting multiple markers per text block, attributing across tool
orchestration episodes) is a separate kf-bench harness change, not a
core spec change.
- Identity string updated to 7.7.0 + title bumped to match version field
(auto-enforced by scripts/check-identity-drift.py pre-commit hook).

### 7.6.0 (2026-06-20)
_Driver: knowledgeforge-core-5lj_

- Added "Per-Turn Mode Telemetry" section to CC Rules — emit a single-line
HTML-comment marker as the LAST line of every response recording mode and
decision classification. Format: "KF-MODE: <mode> | DECISION: <class> |
ADVERSARIAL: <0|1>". Reckonings emit "KF-MODE: reckoning" as a first-class
value, never absence. External observability for kf-bench and longitudinal
monitoring — empty marker means broken instrumentation, populated marker
means this is what KF did.
- Placement contract — marker on its own line at end of response; if FINAL
ANSWER pattern is present, FINAL ANSWER comes first, then blank line, then
marker. External scorers read FINAL ANSWER byte-for-byte and cannot be
perturbed. Marker MUST NOT appear on or be merged with the FINAL ANSWER line.
- Telemetry, not behavior — directive explicitly forbids any tuning of mode selection, decision classification, response content, or budget. No benchmark-specific tuning.
- Identity string updated to 7.6.0 + title bumped to match version field (auto-enforced by scripts/check-identity-drift.py pre-commit hook).

### 7.5.0 (2026-06-13)
_Driver: knowledgeforge-core-f8a_

- Chain-syntax token update — legacy `@critic` with parenthetical-adversarial qualifier replaced with `@adversarial-critic` at three chain example sites (lines 744 ERA chain, 759 ML-infra chain, 763 entity audit chain) plus inline reference in Automatic Adversarial Verification block. Matches the agent name compiled out of Module 07
- Line 814 cross-cutting prose ("embedded in each mode — not separate agents") left unchanged — refers to infrastructure modules 12–25, not the Critic/adversarial-critic split.
- No behavior change for the orchestrator's routing; reference-name alignment only.

### 7.4.0 (2026-06-11)
_Driver: knowledgeforge-core-ev4_

- Added "Always-On Behavioral Patches" section to CC Rules — 4 principles (Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution) borrowed from Karpathy-inspired skills (multica-ai/andrej-karpathy-skills).
- Rationale — KF's selective-activation philosophy leaves many turns mode-less, missing behavioral patches that Karpathy-style always-on rules provide. Three Critic-caught bugs in the 2026-06-10 session would have been prevented in the original Builder pass with these rules in place.
- Cost — ~25 lines / ~300 tokens added to always-loaded kf-meta.md. ROI verified against this session's failure modes.
- Patches Claude's weakness (over-engineering, scope creep, missing assumptions) — does not violate the KF meta-principle since these are weakness-patches, not strength-scaffolding.

### 7.3.0 (2026-05-24)
_Driver: knowledgeforge-core-8xq_

- Module Reference rows for Semantic Wiki Search (22) and Entity Relationship Analysis (25) qualified to reflect M22 v7.3.0 Phase 1 scope reduction — M22's two-phase metadata-gated retrieval and ERA's entity-scoped metadata filter integration are Phase 2 (Deferred), not currently active
- No orchestrator behavior change. Cross-reference alignment with M22 Phase 1 reconciliation.

### 7.24.0 (2026-08-09)
_Driver: knowledgeforge-core-public-release-phase2_

- CC Rules — Per-Turn Mode Telemetry section wrapped in <!-- kf:if telemetry --> / <!-- kf:endif --> conditional block. When binding flag 'telemetry' is false (new default in claude-code.yaml), the telemetry directive is stripped from the compiled kf-meta.md output. When true (private/internal builds via --set telemetry=true), telemetry directive is included. This allows the public release to ship without the internal observability requirement while preserving it for internal deployments.
- {'Identity strings updated': '7.23.0 → 7.24.0.'}

### 7.23.0 (2026-08-09)
_Driver: knowledgeforge-core-e49_

- {'STATIC ZONE — Mode Chaining Behavior': 'Added deterministic mid-chain re-entry rule. When a chain step returns upstream_invalidation at Sev2+, the orchestrator halts forward chain execution and re-enters at invalidated_step_id carrying evidence_ref. Sev1 logs only. Same step invalidated twice in one chain escalates to user with both evidence refs. Re-entry is exempt from the 3-failure circuit breaker. Rule is deterministic (boolean predicate over response fields, no LLM judgment).'}
- {'STATIC ZONE — Circuit Breakers': 'Added re-entry exemption paragraph — upstream_invalidation re-entry is not a mode failure and is exempt from the failure counter.'}
- {'Routing Index Integration': 'Updated re_routing_triggers cross-reference from 3 canonical events (7.2.1) to 4 (downstream_step_premise_invalidation added in Module 19 7.4.0).'}
- {'Module Reference': 'M03 row updated — hc-strategist-to-builder now has response_schema with upstream_invalidation worked example (M03 v7.6.0). M04 row updated — upstream_invalidation optional response field added (7.4.0). M19 row updated — 4 canonical re_routing_triggers (7.4.0).'}
- {'Identity strings updated': '7.22.0 → 7.23.0 (title + static zone).'}
- {'CP COMPILE-OUTWARD DELTA': 'STATIC ZONE edits in this version (re-entry rule + circuit-breaker exemption) require a Claude Projects upload-set recompile. CP lags at 7.22.0 until recompiled.'}

### 7.22.0 (2026-07-02)
_Driver: kf-remediation-2026-07-02_

- {'Task 0': 'Version reconciliation — bumped Module 00 from 7.9.0 to 7.22.0 to align with kf.yaml system version. Module 00 identity strings updated (title + static zone). No orchestrator behavior change since 7.9.0 — this catches up the module version only.'}
- {'Task 1/M16': 'Module Reference M16 row updated — per_variant now tracks 9 variants (added expert.research per M16 v7.3.0).'}
- {'Task 2/M03': 'Module Reference M03 row updated — Handoff Contract Registry now 13 contracts (Contracts C/D/E added per M03 v7.5.0 — hc-expert-to-strategist, hc-expert-research-to-expert-regular, hc-expert-research-to-builder).'}
- {'Task 2/M05': 'Module Reference M05 row updated — research variant formalized (fifth entry in variants[]; 5 variants total).'}
- {'Task 3': 'Always-On Behavioral Patches and Per-Turn Mode Telemetry embedded in STATIC ZONE. Previously these sections lived only in'}
- {'Task 4/M05': 'Research variant trigger in STATIC ZONE extended with deployment note — environments without Asta/Alia Semantic Scholar MCP operate soften/rebuild-only.'}

### 7.2.1 (2026-05-11)

- Module Reference table updated with 7.2.0 annotations for affected modules (03, 04, 05, 07, 16, 19) — F2 from kf-7.2.0 audit redo
- Mode Selection Accuracy Awareness — added one-line note on weekly adversarial calibration source (F4)
- Changelog — added 7.1.0 stub for downstream module updates (F5)
- Routing Index Integration — added cross-reference to Module 19 re_routing_triggers canonical set (7.2.1)
- Module Reference row for 19 now mentions re_routing_triggers + variant ID composition rule (7.2.1)
- No orchestrator behavior change. Source — kf-7.2.0 audit redo findings F2/F4/F5

### 7.2.0 (2026-05-10)

- Static Zone — write routing_decision_log entry on every mode activation (Module 19 schema v1.0); re_routed entries require re_route_reason and archive permanently
- Static Zone — Mode Selection Accuracy Awareness section added; orchestrator evaluates Module 16 metric
- Identity string updated to 7.2.0
- {'Source': 'docs/planning/Typed_Mode_Calling/ chain-logs 01–04 (Track C)'}

### 7.1.0 (2026-05-05)

- No orchestrator behavior change. Version tracks downstream module updates — 01 Navigator → 7.1.0, 18 Salience Allocation → 7.1.0.

### 7.0.6 (2026-04-30)

- Module Reference table updated for M14 (6.6: vision principle drift detection), M17 (7.0.2: planning artifact staleness predicate), M21 (7.0.5: roadmap_phase_completed trigger; vision/roadmap non-triggers)
- No orchestrator behavior change. Version tracks downstream module updates.

### 7.0.5 (2026-04-29)

- Propagated deterministic-first meta-principle from Static Zone to CC Agent and CC Rules compiled outputs
- CC Agent (kf.md) Meta-Principle section now includes both reasoning and execution principles
- CC Rules (kf-meta.md) Meta-Principle now includes both reasoning and execution principles
- Static Zone had this principle since 7.0.0; compiled outputs were missing it (Phase 4 bead [project]-swd.15)

### 7.0.4 (2026-04-29)

- Module Reference table updated for Module 07 (loop_exit_protocol vs convergence_loop distinction — 7.0.2) and Module 21 (Dispatcher Boundary contract — 7.0.2) and Module 03 (formula term claimed — 7.0.1)
- No orchestrator behavior change. Version tracks downstream module updates.

### 7.0.3 (2026-04-18)

- Knowledge Accretion cross-cutting concern updated to two-tier filing: {project_root}/wiki/ for project-scoped, ~/.claude/wiki/ for cross-cutting. Decision rule and bootstrapping documented.
- Runtime behavior line updated to reflect two-tier accretion

### 7.0.2 (2026-04-17)

- Identity string updated from 6.6.1 to 7.0.0
- Meta-principle split into two labeled pairs — (reasoning) and (execution) — to parallel "Deterministic first"
- ERA activation phrasing fixed — "pre-routing pass" → "post-routing, pre-execution pass" (resolves contradiction with "on requests routed to")
- Static zone token budget target added — 5–8K tokens, tied to Phase 2 CLAUDE.md decomposition goal
- 7.0.0 changelog expanded to reflect Phases 1–4 scope; note references plans/ for full rollout details
- {'Module Reference table': "replaced stale '25_ERA_Agent (optional)' with '25_Entity_Relationship_Analysis' — Module 25 is now standalone, not conditional on Module 05 ERA section size"}

### 7.0.0 (2026-04-14)

- Add 'Deterministic first' meta-principle to orchestrator
- Orchestrator portion of 7.0.0 rollout (Phases 1–4 — pre-prompt routing hook, CLAUDE.md decomposition, Stop/state-survival hooks, 13 module spec updates). See knowledgeforge-core/plans/ for full scope.

### 6.6.1


### 6.6.0


### 6.5.0


### 6.4.0


### 6.3.1


### 6.3.0


### 6.2.0


### 6.1.0


## M01 — v7.1.0

### 7.1.0


### 6.6.3


### 6.6.2


### 6.6.1


### 6.2.0


### 6.1.0


## M02 — v7.0.1

### 7.0.1 (2026-04-29)

- Pre-registration git protocol — added skip_conditions (rapid prototyping, hotfix, explicit opt-out) and deviation rationale requirement for exploratory commits
- {'7.0.0 had commit prefixes and tagging; missing when NOT to pre-register and what exploratory commits must include. Source': 'plans/ai-research-skills-integration.md ([project]-swd.10)'}

### 7.0.0 (2026-04-14)

- Add pre-registration git protocol — spec commits precede impl commits with confirmatory/exploratory tagging

### 6.6.1


### 6.2.0


### 6.1.0


## M03 — v7.6.0

### 7.6.0 (2026-08-09)
_Driver: knowledgeforge-core-e49_

- {'Added response_schema to hc-strategist-to-builder — worked example of the upstream_invalidation signal (Module 04 7.4.0). Builder returns verdict enum plus optional upstream_invalidation populated when a discovered constraint invalidates the Strategist recommendation. Three validation checks': 'ui-check-1 (cross-field — all four subfields non-null when upstream_invalidation is non-null), ui-check-2 (enum-membership — severity ∈ {Sev1, Sev2, Sev3}), ui-check-3 (cross-field — Sev2/Sev3 requires evidence_ref non-null and resolves). Registry count stays 13 — no new contract added.'}

### 7.5.0 (2026-07-02)
_Driver: kf-remediation-2026-07-02_

- Added Contract C — hc-expert-to-strategist. Covers the Expert→Strategist chain used in moat analysis ("Review our API security and tell me what to fix first"), ML-infra planning, and competitive moat chains. Payload carries first_order_findings, adversarial_depth, design_implications, decision_type_exercised. Three validation checks (decision_type_exercised_present, enum, adversarial_depth_present). Fallback route_to_navigator.
- Added Contract D — hc-expert-research-to-expert-regular. Covers the 7.9.0 chain "ground this claim with research, then analyze it". Payload carries grounded_evidence_set, composite_grounding_score, degraded flag, disposition enum. Three validation checks (grounded_evidence_set_present, degraded_ceiling_visible, per_claim_grounding_present). Fallback route_to_navigator. Research-variant payloads must carry degraded flag so downstream Expert regular knows the ceiling.
- Added Contract E — hc-expert-research-to-builder. Covers the 7.9.0 chain "find evidence for X and build a report". Same grounded_evidence_set payload as Contract D plus report_structure_directive. Three validation checks. Fallback route_to_navigator.
- {'Registry validation comment updated — count is 13 entries (post-7.5.0 wave': '10 prior + C/D/E).'}

### 7.4.0 (2026-06-13)
_Driver: knowledgeforge-core-f8a_

- Added Contract A — hc-orchestrator-to-verifier registry entry. Orchestrator dispatches to adversarial-critic on evaluative+ producing-mode output OR active chain ≥3 modes. Payload schema covers artifact_under_test (pointer, NOT producing-mode context), producing_mode (enum), decision_type_exercised (enum), chain_position, revision_cycle_count (max 1), tool_grants (subset of test-runner | datastore-read-only | staging-http; HIGH tier per Module 20 verifier_tool_tier_policy).
- response_schema declared on Contract A — verdict (enum), evidence_ref (pointer, NOT prose), deterministic_checks array, optional llm_findings. New Module 04 handoff_contract entity field (v7.3.0).
- Five deterministic validation checks — artifact_under_test_resolves (Sev1), decision_type_exercised_gates_firing (Sev3, skips on reckoning), revision_cycle_within_limit (Sev1), response_schema_conforms (Sev1), evidence_ref_resolves (Sev2, treat_as_verdict_fail). Fallback_path is escalate_to_user — silent-pass NEVER allowed.
- Registry validation comment updated — count is 10 entries post-SPEC-1 merge.

### 7.3.0 (2026-06-13)
_Driver: knowledgeforge-core-f8a_

- {'Added Contract B — hc-runtime-to-accretion-gate registry entry. [project] loop runtime emits accretion candidates with provenance (loop_id, run_id, decision_tag enum, source_mode, signals[]) to Module 21 step_3d_provenance_gate. Three deterministic validation checks (provenance_present Sev1, provenance_decision_tag_enum Sev1, candidate_body_schema_conforms Sev2). Fallback_path': 'surface_for_human_review (never silent-promote to cross-cutting tier).'}
- Registry validation comment updated — count is 9 entries post-SPEC-4 merge. SPEC 1 (hc-orchestrator-to-verifier) will bring count to 10 in wave 2; both bumps land in the same Phase 3 wave window.

### 7.2.0 (2026-05-10)

- Added Handoff Contract Registry — 8 active mode-to-mode handoffs registered as handoff_contract instances per Module 04 entity (resolves ERA F2 from chain-log-01-tool-calling)
- Edges — Builder→Critic auto-verify, Expert→Builder, Strategist→Builder, Synthesizer→Builder, Critic→Builder revision, Debugger→Strategist, Critic-audit→Strategist, Strategist→Calibrator
- Each entry has explicit payload_schema, fallback_path, and ≥1 deterministic validation_check using the canonical assertion forms (Module 04 P2-Δ1)
- {'Source': 'docs/planning/Typed_Mode_Calling/ chain-logs 01–04 (Track C)'}

### 7.0.2 (2026-04-29)

- {'Dual fingerprinting section completed — added explicit delta dispatch rule, loop_exit_protocol cross-ref, and benefit statement. 7.0.0 had the fingerprint definitions and dispatch rules; missing the delta condition and 6.6.1 alignment note. Source': 'plans/agent-orchestrator-integration.md ([project]-swd.6)'}

### 7.0.1 (2026-04-29)

- Claimed `formula` term for mode-chain recipes exclusively — directed downstream implementations to use alternative terms (recipe, playbook, pattern, workflow) for non-mode workflows. Prevents namespace collision with non-KF formula usage (e.g., watch-pattern recipes in [project]).
- No behavior change. Term hygiene only.

### 7.0.0 (2026-04-14)

- Add dual fingerprinting (state + dispatch) for Critic ↔ Builder loop to prevent redundant re-review
- Add spec drift checkpoint for 3+ mode chains — re-validates intent between mode 2 and mode 3

### 6.6.1


### 6.2.0


### 6.1.0


## M05 — v7.4.0

### 7.4.0 (2026-07-02)
_Driver: kf-remediation-2026-07-02_

- {'research variant degraded_mode': 'added accretion boundary note — degraded output at exactly 0.6 MUST NOT auto-file (M21 v7.5.0 at_threshold_degraded clause enforces this). Downstream accretion consumers must check the degraded flag; the M21 gate does so automatically.'}
- {'Added deployment note under research variant': 'deployments without Asta/Alia Semantic Scholar MCP connected permanently operate in degraded_mode. Ship disposition is permanently unavailable; outputs are soften/rebuild-only. Document this limitation to consumers at session start if research variant is requested.'}

### 7.3.0 (2026-07-01)

- Added research variant (fifth entry in variants[]) — grounded evidence retrieval with Asta/Alia Semantic Scholar MCP, composite grounding scores per claim, disposition routing (ship/soften/rebuild)
- runtime_dependency field declared per-variant (research only so far); degraded_mode specifies WebSearch fallback behaviour when MCP unavailable
- Trigger disambiguator td-research-vs-expert-regular registered in Module 04 to resolve "what does the research say" / "find evidence for" overlap with expert.regular
- Module 00 adds routing trigger for research variant (7.8.0 → 7.9.0)

### 7.2.0 (2026-05-10)

- Formalized variants[] field on agent spec — regular, infrastructure, ml_infrastructure, era (resolves ERA F1 from chain-log-01-tool-calling)
- Each variant declares trigger_phrases, output_format, output_template, typical_chain_position, decision_type_typical, risk_tier
- decision_type_exercised output field (already required since 6.6.1) now annotated with explicit enum constraint and consumed-by note for Module 00 auto-verify gate (resolves F3)
- Mode-selection accuracy metric (Module 16
- {'Source': 'docs/planning/Typed_Mode_Calling/ chain-logs 01–04 (Track C)'}

### 6.6.1


### 6.6.0


### 6.3.0


### 6.2.0


### 6.1.0


## M06 — v7.3.0

### 7.3.0 (2026-05-24)
_Driver: knowledgeforge-core-8xq_

- Four locations updated for M22 / M25 Phase 1 reality (initial pass missed three; caught by third critic pass):
* Infrastructure Modules table (line 192) — M22 row: "metadata-gated semantic search" → Phase 1 dup-check gate; Phase 2 deferred
* Infrastructure Modules table (line 205) — M25 row: entity-scoped filters qualified — Tier 0 (M22) Phase 2 Deferred, Tier 3 (M24) active
* Module Reference Table — M22 row (line 604) and M25 row (line 607) qualified
* Integration Graph (line 708) — M25 ↔ 22 marked Phase 2 Deferred

### 7.2.0 (2026-05-11)

- Resolved F1 from kf-7.2.0 audit redo — content updated from 6.6.1 to 7.2.0 baseline
- Title and version bumped to 7.2; meta-principle, identity, and framework refs updated
- Added Mode Variants section — Critic (regular/linter/audit/adversarial) and Expert (regular/infrastructure/ml_infrastructure/era) variant taxonomy formalized per 05/07 v7.2.0
- Agent Modes table — variant rows added under Critic and Expert
- KF-4 Operational Bounds table — added metric
- KF-8 Memory Architecture — added routing_decision_log subsection (schema v1.0) + variant ID composition rule (F7)
- Added Handoff Contract Registry section — 8 registered handoffs from Module 03
- Added Trigger Disambiguator section — Module 04 template purpose and assertion forms
- Module Reference Table — added 22, 23, 24, 25 (previously missing); annotated 03, 04, 05, 07, 16, 19 with 7.2 additions
- Related list — added 25_Entity_Relationship_Analysis (previously missing)
- Quality Checklist — added routing_decision_log write item
- Module 25 moved from "New in 6.5" section to "New in 6.6" (correct provenance)
- Source — kf-7.2.0 audit redo (F1, F7)

### 7.0.0


### 6.6.1


### 6.6.0


### 6.5.0


### 6.4.0


### 6.3.1


### 6.3.0


### 6.2.0


### 6.1.0


## M08 — v6.8.0

### 6.8.0


### 6.7.1


### 6.7.0


### 6.6.1


### 6.2.0


### 6.1.0


## M09 — v7.0.2

### 7.0.1 (2026-04-29)

- Expanded CI Failure Feedback Loop — added fingerprint comparison logic (same/different/subset), trigger condition, determinism note
- Missing from 7.0.0 initial implementation: what to do when fingerprint changes (new issue introduced) or partially changes (subset). Source: plans/agent-orchestrator-integration.md ([project]-swd.11)

### 7.0.0 (2026-04-14)

- Add Phase 4b (Failure Reproduction) between root cause and remediation; add reproduction_status output field
- Add CI failure feedback loop — fingerprint failure sets, dispatch only new failures, escalate after N retries

### 6.2.0


### 6.1.0


## M10 — v6.5.0

### 6.2.0


### 6.1.0


## M12 — v7.0.2

### 7.0.2 (2026-04-29)

- {'Judge isolation': 'add fallback rule (intra-family tier difference when cross-provider unavailable), add specific model examples, add ~80% multi-model benefit quantification'}
- {'SAP cascade': 'expand to full 5-strategy sequence (fence extract, multi-object scan, fault-tolerant fix, raw string fallback), add BAML-aligned scoring (StrippedNonAlphaNumeric +3, single_to_array_coercion +1), add fabrication flag and DefaultFromNoValue propagation rule, switch grounding mapping from cost-based multipliers to level-based absolute values (0.8/0.6/0.4/0.1)'}

### 7.0.1 (2026-04-29)

- (intermediate — superseded by 7.0.2)

### 7.0.0 (2026-04-14)

- Add cross-provider judge isolation rule — judge must be different family from agent
- Add SAP-inspired structured output parsing cascade with grounding score integration

### 6.2.0


### 6.1.0


## M13 — v6.5.0

### 6.2.0


### 6.1.0


## M14 — v6.6.0

### 6.6.0


### 6.2.0


### 6.1.0


## M15 — v6.5.0

### 6.2.0


### 6.1.0


## M16 — v7.3.1

### 7.3.1 (2026-07-02)
_Driver: kf-remediation-2026-07-02-adversarial-fix_

- Fixed mode_selection_accuracy rationale text — "Expert 4 variants" → "Expert 5 variants" (was not updated when expert.research was added in 7.3.0; caught by adversarial-critic pass).

### 7.3.0 (2026-07-02)
_Driver: kf-remediation-2026-07-02_

- {'Added expert.research to per_variant tracking list (resolves audit finding': 'research-variant routing errors were misattributed to expert.regular — the exact overlap td-research-vs-expert-regular exists to police). "8 Critic/Expert variants" phrasing updated to 9.'}

### 7.2.0 (2026-05-10)

- Added metric
- Healthy range — >=90% overall, >=95% per-variant; calibration drift threshold 5pp
- Corrective Action Summary extended with 5 new rows
- {'Source': 'docs/planning/Typed_Mode_Calling/ chain-logs 01–04 (Track C)'}

### 7.0.1 (2026-04-29)

- Expanded Pure Decision Functions section — added context_pressure_response function and formal Given/When/Then testability format
- decision_catalog now covers circuit_break and context_pressure_response; spawn_decision deferred (implementation-specific, not core KF bounds)
- {'Source': 'plans/background-agents-integration.md Phase 4 item ([project]-swd.13)'}

### 7.0.0 (2026-04-14)

- Add pure decision functions requirement for circuit breakers — input/output only, truth-table expressible

### 6.4.0


### 6.2.0


### 6.1.0


## M17 — v7.0.2

### 7.0.2 (2026-04-30)

- Added Planning Artifact Staleness section — vision (half_life_days: 60) and roadmap (half_life_days: 30) staleness gates with per-artifact severity calibration. In-progress phase stagnation signal added (> 2× expected duration). Aligns with /kf-vision and /kf-roadmap command staleness review modes.

### 7.0.1 (2026-04-29)

- {'Research Staleness Gate completed — added trigger predicate (staleness_risk != stable), proportional severity based on staleness ratio (age/half-life), explicit do-not-block rule, and updated caveat format. 7.0.0 had binary gate; missing the proportionality and trigger condition. Source': 'plans/orchestra-integration.md ([project]-swd.7)'}

### 7.0.0 (2026-04-14)

- Add research staleness gate with domain half-life table; flags stale research before building on it

### 6.3.1


### 6.2.0


### 6.1.0


## M18 — v7.1.0

### 7.1.0 (2026-04-23)

- Version alignment with KF system 7.1.0
- Add inhibition-first framing spec note to Competitive Inhibition section
- References wiki/architecture/imagination-as-suppression-validates-patching.md
- No implementation change — spec-level observation for Phase 1 hook design

### 6.3.1


### 6.2.0


### 6.1.0


## M19 — v7.4.0

### 7.4.0 (2026-08-09)
_Driver: knowledgeforge-core-e49_

- Added fourth canonical re_routing_trigger — downstream_step_premise_invalidation. Fires when a downstream chain step returns response.upstream_invalidation at Sev2+ (per Module 04 handoff_contract response_schema, 7.4.0). routing_decision_log entry sets re_routed = true; re_route_reason carries invalidated_step_id + evidence_ref from the upstream_invalidation signal. Cross-refs — Module 00 re-entry rule (writer), Module 04 upstream_invalidation field (source), Module 16 metric
- No schema_version change. No changes to existing three triggers or non-triggers.

### 7.3.1 (2026-07-01)
_Driver: knowledgeforge-core-b3g_

- {'Fixed Tier 3 body': 'access_pattern and search_protocol search_protocol step 2 corrected — removed stale "metadata pre-filter via search_memories" claim; replaced with Phase 1 (mempalace_search wing/room scope) / Phase 2 deferred split, matching M24 6.6.0 Retrieval Protocol.'}
- Fixed CC Doc Tier 3 description — removed aspirational "metadata pre-filtering" claim; added Phase 1/Phase 2 split note.
- {'Note': '7.3.0 changelog entry incorrectly claimed CC Doc Tier 3 was updated in gkf — that work was deferred to b3g.'}

### 7.3.0 (2026-07-01)
_Driver: knowledgeforge-core-gkf_

- Added "cc Substrate Projections (Claude Code)" subsection — places .claude/rules/ and auto-memory in the tier model without introducing new tiers.
- .claude/rules/ is a compiled projection of Tier 0; activation_profile.trigger governs which compilation target is used (invariant → unscoped rule, path_bound → path-gated rule, task_bound → skill). Write-time invariant stated — manual rule edits are overwritten on next compile.
- auto-memory (~/.claude/projects/<proj>/memory/MEMORY.md) is harness-managed scratch sitting below Tier 1 — not KF-managed, not a tier. Do not accrete to it.
- {'Added comparison table': 'four KF tiers + auto-memory with scope and managed-by columns.'}
- Updated CC Doc Tier 0 description to note cc substrate projections.
- No schema changes. schema_version unchanged.

### 7.2.1 (2026-05-11)

- Added re_routing_triggers enumeration to routing_decision_log section — canonical events that set re_routed = true (resolves F3 from kf-7.2.0 audit redo; previously this definition lived only in project agent instructions prose)
- Three canonical triggers (at 7.2.1) — navigator_activation_after_initial_routing, user_explicit_redirect, critic_adversarial_wrong_mode_finding; fourth trigger added in 7.4.0 (downstream_step_premise_invalidation)
- Three non-triggers documented — chain_progression, variant_selection_within_mode, critic_revision_loop
- Cross-refs added — Module 00 (writer), Module 16 metric
- Added variant ID composition rule to selected_variant field — `<selected_mode>.<selected_variant>` is the canonical qualified form used by Module 16 metric
- No schema field changes. schema_version remains 1.0.

### 7.2.0 (2026-05-10)

- Added routing_decision_log section (schema_version 1.0) — audit trail of every routing decision, separate concern from routing_index state (resolves ERA F4 from chain-log-01-tool-calling)
- Retention — rolling 1000 entries + permanent re-route archive at wiki/operations/routing-log/{YYYY-MM}.md
- Added tier_2_metric_aggregates schema for weekly metric persistence beyond rolling window
- Data source for Module 16 metric
- {'Source': 'docs/planning/Typed_Mode_Calling/ chain-logs 01–04 (Track C)'}

### 6.6.1


### 6.5.0


### 6.2.0


## M20 — v7.1.0

### 7.1.0 (2026-06-13)
_Driver: knowledgeforge-core-f8a_

- Added verifier_tool_tier_policy — gates separate-agent verifier (adversarial-critic) tool grants beyond Read/Glob/Grep by HIGH tier with explicit bind-side requirements (sandbox, read-replica, network-isolation). Cross-spec dependency for SPEC 1 verifier promotion.
- Added accretion_candidate_tier_policy — novel/predictive-derived accretion candidates surface for human review at HIGH tier regardless of target scope (project or cross-cutting). Annotation tags do not satisfy HIGH-tier confirmation. Cross-spec dependency for SPEC 4 vetting gate.
- Both policies fit the existing risk_escalation block shape (rule/trigger/action). No behavioral revolution; additive rules with explicit Module 07 + Module 21 integration points.
- Phase 3-prep PR landing before SPEC 1 and SPEC 4 implementation; eliminates documentation drift from specs referencing a Module 20 surface that does not exist yet.

### 7.0.1 (2026-04-29)

- Expanded Allow-With-Mutation section — added hook output contract, audit trail spec (.kf/state/permission_mutations.jsonl with fields), and explicit deny-vs-mutate decision rule
- 7.0.0 had mutation policies table and implementation note; missing the concrete hook interface, audit path, and when to prefer mutation over denial
- {'Source': 'plans/hooks-mastery-integration.md ([project]-swd.12)'}

### 7.0.0 (2026-04-14)

- Add allow-with-mutation permission tier — path normalization, safety flags, cost annotation policies

### 6.2.0


## M21 — v7.5.0

### 7.5.0 (2026-07-02)
_Driver: kf-remediation-2026-07-02_

- Added at_threshold_degraded clause to grounding_gate — resolves boundary ambiguity when degraded=true research output lands at exactly 0.6. Degraded-mode cap of 0.6 is artificial (WebSearch fallback ceiling), not earned; without this clause the gate would auto-file it as normal accretion. at_threshold_degraded forces caveat + no-auto-file, consistent with M05 research variant degraded_mode (ship disposition blocked). Boundary behavior is now deterministic and stated here and in M05.

### 7.4.0 (2026-06-30)
_Driver: knowledgeforge-core-och_

- {'Activated native:true gate clause — adds content-classifier heuristic at step_2c.compute.native. A candidate is native:true when ALL THREE signals are present simultaneously': '(a) general-advice shape (no named framework, stack, or project-specific concept), (b) no failure anchor (no observed failure, error, or counterexample cited), (c) no tool/path/command specificity (no CLI, API, path, or library named). Conservative conjunction — most project-specific or empirically-grounded candidates fail at least one signal.'}
- {'Added assignment-source hierarchy': 'human_set override > content classifier > calibration probe (offline). Human override always wins.'}
- {'Added linter step 7': 'suppression-event review — reads compile.md native suppressions from current calibration window, computes suppression rate, surfaces NATIVE_GATE warning when rate > 25%, includes 5-item sample for human spot-check.'}
- {'Added native_suppression_tracking block to accretion_calibration': 'per-session logging of native_suppressions + suppression_rate, quarterly calibration probe procedure, false-negative threshold > 10%.'}
- Updated CC Doc Three-Condition Test and Candidate Metadata sections to match activated state.
- {'Semver': 'minor (not major) — gate structure unchanged; criteria are additive to a previously-inert field. Expected suppression rate is low (<5% of candidates based on project-specificity of typical KF accretion corpus). Future calibration bead bears re-evaluation if yield materially changes.'}
- {'Removes all "v1': 'deferred to bead knowledgeforge-core-och" references — replaced by actual specification.'}

### 7.3.0 (2026-06-13)
_Driver: knowledgeforge-core-f8a_

- Added step_3d_provenance_gate between step_3c_profile_cross_validate and step_4a_taxonomy_gate. Gate consumes Contract B provenance (loop_id, run_id, decision_tag, source_mode, signals[]) emitted by [project] runtime. Cross-cutting candidates derived from novel/predictive decisions require verifier_signoff OR human_review_signal in provenance.signals[] — otherwise surface_for_human_review. Project candidates derived from novel/predictive surface for human review regardless. Reckoning/evaluative paths unchanged. Missing provenance → surface_for_human_review with provenance_missing flag; user chooses destination.
- Added provenance sub-object to accretion_candidate schema (loop_id, run_id, decision_tag enum, source_mode, signals[]). source_mode MOVED from top-level into provenance.source_mode (breaking schema change on the top-level field).
- Schema transition — accessor shim `candidate.provenance?.source_mode ?? candidate.source_mode` applies at step_2c trigger lookup, default_importance.source_mode_boost, and compile_log_format. Grandfather rule — entries with top-level source_mode AND created < 2026-07-01 are exempt from provenance completeness check; Critic linter raises Sev 3 but does not block. Shim fallback sunsets 90 days after cutover.
- Added
- Cross-references Module 20 v7.1.0 accretion_candidate_tier_policy (HIGH tier for novel/predictive-derived candidates) and Module 03 v7.3.0 hc-runtime-to-accretion-gate Contract B entry.

### 7.2.0 (2026-06-12)
_Driver: knowledgeforge-core-8zt_

- Added violation-event counter to Knowledge Base Linter. Linter gains two new responsibilities — event recording (append to .kf/linter/events.log) and snapshot aggregation (write .kf/linter/counter.json keyed by rule filename). Storage in .kf/linter/ avoids wiki contamination (already gitignored via .kf/ pattern).
- Counter window — 30 days. Graduation threshold — ≥3 events across ≥2 distinct sessions (per Phase 2 spec 5fd Section 5).
- linter_check.kind restricted at v1 to stateless artifact patterns — frontmatter_field_missing, frontmatter_field_value_disallowed, body_pattern_present, body_pattern_absent. Temporal-ordering kinds (e.g., "event X preceded event Y in session") require session log infrastructure deferred to follow-up bead.
- Added dotfile-exclusion to linter scan (step 6.5) — prevents linter from checking its own state files against wiki schema rules.
- Existing wiki/.linter_offset state file moved to .kf/linter/offset for consistency (per-machine operational state out of wiki partition).
- cc_hooks emitter consumes graduation snapshot at compile time with three-check gate — snapshot freshness (rejects snapshots older than window_days), numeric re-derivation (catches snapshot tampering by recomputing eligibility from stored counts), and source_rule existence check.
- Semver — minor bump justified — event log has no external contract surface; snapshot is the contract and is rebuilt-not-rotated. Section 3a of spec defends in detail.

### 7.1.4 (2026-06-12)
_Driver: knowledgeforge-core-8gp_

- step_2c_activation_profile.compute.path_globs gains a new lookup path — for ERA-consuming modes (Builder, Coordinator, Expert, Strategist, Critic), join era.entity_paths values into a flat deduped list. If >5 globs, keep 5 most-specific per the M25 7.1.0 glob comparison function.
- step_3c_profile_cross_validate gains a downgrade rule — when ERA produced the globs (path_globs_meta entry has source: era) AND scope == global, DOWNGRADE trigger to task_bound and clear path_globs (instead of rejecting). Reason: ERA commonly produces globs for architectural patterns that are also global-scoped; silent rejection would make the M25 resolver invisible. Log to compile.md as era_global_glob_downgrade.
- Manually-authored path_globs (no path_globs_meta entry) still reject on global scope per Phase 1 rule. Distinguishing source is via the new optional path_globs_meta sidecar.
- Backwards-compatible — when ERA absent OR no entity_paths produced, existing Phase 1 logic applies unchanged.

### 7.1.3 (2026-06-12)
_Driver: knowledgeforge-core-3ym_

- step_5_file path formula corrected — was {wiki_root}/{domain}/{topic}.md (one file per topic), now {wiki_root}/{domain}/{YYYY-MM-DD}_{slug}.md (one file per entry) to match established convention. 218 entries on disk already followed this pattern; the spec was the stale party. Pre-existing bug surfaced by e0x Critic finding [5].
- Added slug derivation rule (kebab-case from title), domain-field reference (with grandfather fallback per M23), and same-day collision suffixing (-2, -3...).
- No behavior change for actual writes — every wiki entry written in the last 18 months used the corrected formula. Spec-vs-reality alignment only.

### 7.1.2 (2026-06-10)
_Driver: knowledgeforge-core-e0x_

- Gate 4a (taxonomy validation) gains grandfather pre-check — entries whose creation timestamp is before 2026-06-10 (M23 v6.6.0 release) skip the domain/topic vocabulary validation if those fields are absent. See M23 Grandfathering section for timestamp resolution order (created → git first-commit → file mtime).
- {'Knowledge Base Linter gains two new rules — (a) schema-completeness check is grandfather-aware; (b) created': 'vs git-first-commit divergence beyond ±1 day raises a MEDIUM finding (possible-backdated-entry).'}
- No behavior change for entries created after 2026-06-10 — Gate 4a enforces the expanded M23 v6.6.0 vocabulary strictly on new entries.

### 7.1.1 (2026-06-10)
_Driver: knowledgeforge-core-261_

- {'Added step_5b_emit_path_gated_rule to claude_code_runtime.filing — when activation_profile.trigger == path_bound AND scope == project, also write .claude/rules/kf-runtime/<slug>.md with paths': 'frontmatter populated from path_globs'}
- KF-internal provenance metadata (kf_source, kf_bead, kf_activation_profile) lives in an HTML comment block at the bottom of the runtime rule file, NOT in the paths-bearing YAML frontmatter — avoids any substrate-parser ambiguity around unknown YAML siblings
- On-error policy — wiki write already succeeded; log step_5b errors to compile.md and continue without rolling back the wiki entry
- Cross-references Phase 2 cc target spec for emitter behavior; see knowledgeforge-core-261 implementation

### 7.1.0 (2026-06-10)
_Driver: knowledgeforge-core-poz_

- Added activation_profile block to accretion_candidate metadata (trigger, decidability, miss_cost, native, path_globs)
- Added native:true as a third gate clause alongside novelty + reuse value
- v1 ships native in deferred-activation mode (default false, no auto-emission) — gate envelope unchanged
- Added step_2c_activation_profile (assignment) and step_3c_profile_cross_validate (scope cross-cut) to the claude_code_runtime filing protocol
- Profile is substrate-agnostic; downstream dispatchers consume it (Module 22, future cc rules/hook emitters per Phase 2 spec 5fd)
- {'Backwards-compatibility': 'existing modes do not auto-emit native:true; no behavioral change to v7.0.x gate yield'}

### 7.0.6 (2026-05-24)
_Driver: knowledgeforge-core-8xq_

- Updated step_4b_embedding to reflect MemPalace adoption — embedding happens inside MemPalace's mine pipeline (which wraps ChromaDB internally), not via direct ChromaDB calls from this module
- step_4b_embedding's metadata description corrected — Phase 1 of Module 22 does NOT consume frontmatter at retrieval time; metadata is preserved at write time for Phase 2 readiness
- rebuild_trigger reference clarified — Module 22's index rebuild is automatic via mempalace-wiki-mine.py (PostToolUse hook), not invoked from this module

### 7.0.5 (2026-04-30)

- Added Roadmap Phase Completion Trigger — `/kf-roadmap complete-phase <n>` now runs accretion review against the phase's pre-committed accretion_note; source_mode set to roadmap_phase; novelty_types restricted to [new_pattern, transferable_framework, reusable_analysis, reusable_diagnostic]. Roadmap and vision files themselves added to explicit Non-Triggers / planning artifacts list.
- Added bidirectional prerequisite satisfaction check protocol for phase completion.

### 7.0.4 (2026-04-29)

- {'Expanded Terminal State — added quality_test heuristic, two missing indicators (boundaries/limitations explicit, anti-patterns documented), accretion_pending flag for Tier 2 intermediate filing, and user-promoted promotion path. Source': 'plans/ai-research-skills-integration.md ([project]-swd.9)'}

### 7.0.3 (2026-04-29)

- Expanded Source Fingerprint Deduplication — added partial match case (same finding_key, different content → update existing entry), no-database principle statement, and Critic-finding-specific fingerprint formula
- {'7.0.0 only handled exact match (skip) and no match (create); partial match left undefined. Source': 'plans/background-agents-integration.md ([project]-swd.8)'}

### 7.0.2 (2026-04-29)

- Added Dispatcher Boundary section formalizing gate-vs-dispatch separation — Module 21 owns the gate (novelty, reuse value, grounding ≥ 0.6, taxonomy compliance, candidate metadata). Downstream routers own dispatch (tier selection, physical write path). Downstream routers that bypass the Module 21 gate are a Critic linter HIGH finding.
- No behavior change. Clarifies boundary for MemoryRouter and similar downstream dispatcher implementations.

### 7.0.1 (2026-04-18)

- Two-tier wiki accretion — project wiki ({project_root}/wiki/) for project-scoped knowledge, global wiki (~/.claude/wiki/) for cross-cutting patterns. Decision rule based on transferability. Bootstrap project wiki/ on first filing.

### 7.0.0 (2026-04-14)

- Add source_fingerprint deduplication — check before accreting, embed in frontmatter
- Add terminal state requirement — only self-contained, complete, closed-loop artifacts accrete to Tier 0

### 6.6.1


### 6.5.0


### 6.3.1


### 6.2.0


## M22 — v7.4.0

### 7.4.0


### 7.3.1


### 7.3.0


### 6.5.0


## M23 — v6.10.0

### 6.9.0 (2026-06-20)
_Driver: knowledgeforge-core-sd3_

- Compiler vocab expansion — added bootstrap-divergence (covers
static-to-compiled-promotion divergence patterns) and
multi-repo-pipeline (covers compile pipelines crossing
source-and-derived repos). Re-topicked 2 entries:
diagnostics/2026-05-23_compile-pipelines-complete-tracked-work-
invisibly issue-tracking -> multi-repo-pipeline; and
compiler/2026-06-14_bootstrap-divergence-intentional-on-static-
to-compiled-promotion ci-cd -> bootstrap-divergence. Compiler
topic count 2 -> 4.
- Orchestration vocab expansion (minimum-3 set) — added
queue-pattern, parallel-workflow, task-decomposition. Removed
deprecated self-referential `orchestration` topic — both entries
that used it migrated to queue-pattern (coalesce-at-enqueue,
append-only-queue). Two further entries split out of the generic
multi-stage-issue-workflow bucket: parallel-spec-parallel-critic
-> parallel-workflow; split-by-blocking-axis -> task-decomposition.
Orchestration topic count 4 -> 6 (added 3, removed 1 deprecated).
- The patterns-domain deprecated `orchestration` topic (line 118) is a separate deprecation and remains; one entry (parallel-agent- triage-backlog-reconciliation) still uses it. Out of sd3 scope — may be handled by a future bead.
- Summary tables at end of doc updated for both domains.
- Closes sd3 entirely (all 3 sub-tasks done — migrations in 6.8.0, compiler + orchestration in 6.9.0).

### 6.8.0 (2026-06-20)
_Driver: knowledgeforge-core-sd3_

- Added schema-evolution topic to migrations domain. Migrated the one
existing migrations entry (2026-06-12_schema-evolution-additive-
optional-fields.md) off the self-referential migrations -> migrations
topic to migrations -> schema-evolution. Same anti-pattern as the
deprecated orchestration self-topic; this resolves it for the
migrations domain.
- Total migrations topic count 1 -> 2 (error-classification +
schema-evolution). Summary table at end of doc updated to match.
- Partial close of sd3 (migrations sub-task). Compiler + orchestration sub-tasks still open — they need operator decisions on re-topic vs re-domain (compiler) and minimum-vs-full new topic set (orchestration).

### 6.7.1 (2026-06-20)
_Driver: knowledgeforge-core-a05_

- Fix YAML parse warning surfaced during kf-cc compile — 6.7.0 changelog had a bullet starting with a backtick (`` `seo-strategy`...``) which YAML rejects as a non-token. Rephrased to start with a word. No semantic change; vocab unchanged.

### 6.7.0 (2026-06-20)
_Driver: knowledgeforge-core-a05_

- Pruned 5 SEO-domain leakage topics flagged in 6.6.0 — `keyword-repositioning`, `keyword-research-methodology`, `keyword-selection` from methodologies; `google-ads`, `serp-ranking-diagnosis` from diagnostics. The four entries actually using these topics (plus 3 more under the orphan `seo-strategy` domain) belong in sem-tools/wiki/, not KF-core — relocation tracked by successor bead knowledgeforge-core-56c. M23 vocab cleanup lands now so new SEO entries can no longer accrete into KF-core under these topics.
- Total methodologies topic count 21 → 18. Total diagnostics topic count 28 → 26. Summary tables at end of doc updated to match.
- The seo-strategy domain (never in vocab; grandfathered) and its 7 entries remain in place until the move bead executes — see -56c for plan.

### 6.6.0 (2026-06-10)
_Driver: knowledgeforge-core-e0x_

- Added 5 new domains (methodologies, diagnostics, orchestration, migrations, compiler) covering 51% of wiki entries previously in directories absent from v6.5.x vocab. Topic lists are empirical baselines extracted from on-disk frontmatter (55 topics observed across the 5 directories), not speculative derivations.
- Total domain count 10 → 15. Tag cap unchanged at 57/60 approved tags.
- Added Grandfathering section after Vocabulary Extension Protocol — entries with creation timestamp before 2026-06-10 are NOT retroactively required to carry domain/topic fields. New entries strict; existing entries lazy-migrate.
- Creation timestamp resolution order — created: frontmatter → git first-commit date
→ file mtime. Git fallback covers the 3 entries identified during Phase 0 audit
that lack created: entirely.
- Forgery resistance — linter MEDIUM finding on ±1 day created: vs git first-commit
divergence. Cultural norm, not cryptographic enforcement.
- Deprecated patterns/orchestration topic (collision with new orchestration domain).
DEPRECATED-not-deleted — still validates on grandfathered entries; new entries
should use the new orchestration domain.
- Extension event counting interpretation locked: one bead = one Vocabulary
Extension Protocol invocation = one event (regardless of how many domains added).
This bead consumes 1 of v6.x's 5-event budget; 4 remain.

### 6.5.2


### 6.5.1


### 6.5.0


### 6.10.0 (2026-06-21)
_Driver: knowledgeforge-core-cys_

- Removed the patterns-domain deprecated `orchestration` topic
(deprecated in 6.6.0). The 4 entries that still used it
were migrated per-entry: per-detector-error-isolation-audit-
pipelines (patterns / validation); conditional-update-for-
atomic-queue-claim (orchestration / queue-pattern — re-domain);
per-host-caching-per-page-detectors (performance / cache —
re-domain); default-policy-tri-state-parameters-composite-
endpoints (patterns / validation). The earlier parallel-agent-
triage entry was handled by e48926a.
- Symmetric with the orchestration-domain self-topic removal in
6.9.0; both deprecated `orchestration` topics now resolved.
Patterns topic count 6 -> 5. Summary table updated to match.
- Closes cys entirely (per-entry calls done + optional M23 patch to drop the deprecated topic).

## M24 — v6.6.0

### 6.6.0 (2026-07-01)
_Driver: knowledgeforge-core-b3g_

- Phase 1 / Phase 2 split applied to Retrieval Protocol — mirrors the M22 split done in bead 8xq.
- {'Phase 1 (current)': 'MemPalace actual tool surface — mempalace_search(query, limit?, wing?, room?). No domain/topic/date_range/importance_min pre-filter parameters exist; calling with those args silently drops them (confirmed against live tool schema).'}
- {'Phase 2 (deferred)': 'client-side post-filter on semantic results — apply domain/topic/date_range/importance_min after retrieval. Activates when M22 Phase 2 (bead acu) ships and cross-tier filter infrastructure is live.'}
- Fixed MCP Tools table — search_memories(query, filters, top_k) was aspirational; replaced with actual mempalace_search(query, limit?, wing?, room?) signature.
- Fixed Retrieval Protocol step 2 — removed fake metadata pre-filter call; added Phase 1 (wing/room filter, semantic re-rank) + Phase 2 deferred block.
- Fixed CC Doc Retrieval Protocol step 2 to match.
- {'Anti-pattern table updated — "Skipping metadata pre-filter" warning retained but qualified': 'at Phase 1, apply wing/room scope at minimum; domain/topic/importance_min are Phase 2 client-side filters.'}
- Updated M19 Tier 3 cross-refs — access_pattern and search_protocol corrected to Phase 1 reality.
- Closes knowledgeforge-core-b3g.

### 6.5.1


### 6.5.0


## M25 — v7.1.0

### 7.1.0 (2026-06-12)
_Driver: knowledgeforge-core-8gp_

- Added entity_paths resolver — ERA now produces entity_paths dict (glob patterns keyed by entity) alongside the existing memory_filter.
- Recommended resolver shape — GitNexus-primary with session-cached grep fallback. Cache key is (entity_name, repo_root) to prevent multi-repo session contamination.
- Glob derivation rules — single-file, N-in-dir, N-across-dirs, max-5-cap. Comparison function specified deterministically (literal-character prefix count + lexicographic tiebreak).
- Added resolver_source diagnostic metadata — records which resolver (gitnexus, grep, or none) produced the entity_paths. No current consumer; future drift-detection bead may read it.
- Forward-compatible — existing ERA consumers (M22 Phase 2, M24, downstream modes) ignore the new field cleanly; M21 path_globs lookup is the only currently-active consumer.
- Closes the <1% path_bound bottleneck identified in Phase 1 spec (y4b) Section 4.

### 7.0.3 (2026-05-24)
_Driver: knowledgeforge-core-8xq_

- Memory Retrieval Enhancement section qualified — entity-scoped metadata filter integration with M22 is Phase 2 (Deferred). `mempalace_check_duplicate` (Phase 1) has no metadata filter parameter; passing entity/relationship/domain filters in Phase 1 is silently dropped. ERA's other outputs (entity list, relationship map, graph shape) remain consumed by downstream modes.
- Tier 3 (M24) integration unchanged.

### 7.0.2 (2026-04-29)

- Upstream ERA adversarial checklist from knowledgeforge-cw era-domain skill — compound failures (hidden join paths, blast radius, cardinality violations, brittleness test), blast radius probes, assumption inversions, design implications
- Add KF-specific ERA applications — module dependency audit, mode chain contracts, routing index schema
- Add adversarial probes to CC Doc section for Expert mode execution

### 7.0.1 (2026-04-17)

- Module is now fully standalone — Module 00 and Module 07 updated to reference this as a first-class cross-cutting module (not optional, not conditional on Module 05 ERA section size)

### 6.6.0


### 6.5.0

