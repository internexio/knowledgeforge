# Knowledge Accretion

## Module Metadata

```yaml
module:
  title: Knowledge Accretion
  version: 7.3.0
  purpose: Cross-cutting detection-and-routing behavior that recognizes when mode outputs contain knowledge worth persisting and either auto-files it (Claude Code) or surfaces it as a compilation candidate (Claude Projects)
  topics: [knowledge-persistence, compile-query-enhance, wiki-generation, accretion-signals, knowledge-base-maintenance]
  contexts: [all-mode-execution, knowledge-management, session-outputs, persistent-storage]
  difficulty: advanced
  related: [07_Critic_Agent, 08_Synthesizer_Agent, 09_Debugger_Agent, 10_Strategist_Agent, 02_Builder_Agent, 05_Expert_Agent_Example, 11_Calibrator_Agent, 12_Calibration_Layer, 14_Metacognitive_Monitor, 15_Grounding_Scores, 17_Temporal_Knowledge, 19_Memory_Architecture, 20_Permission_Model]
  added_in: "6.2"
  changelog:
    7.3.0:
      date: 2026-06-13
      driver: knowledgeforge-core-f8a
      spec: docs/planning/2026-06-13_spec-4-accretion-vetting-gate.md
      changes:
        - Added step_3d_provenance_gate between step_3c_profile_cross_validate and step_4a_taxonomy_gate. Gate consumes Contract B provenance (loop_id, run_id, decision_tag, source_mode, signals[]) emitted by [project] runtime. Cross-cutting candidates derived from novel/predictive decisions require verifier_signoff OR human_review_signal in provenance.signals[] — otherwise surface_for_human_review. Project candidates derived from novel/predictive surface for human review regardless. Reckoning/evaluative paths unchanged. Missing provenance → surface_for_human_review with provenance_missing flag; user chooses destination.
        - Added provenance sub-object to accretion_candidate schema (loop_id, run_id, decision_tag enum, source_mode, signals[]). source_mode MOVED from top-level into provenance.source_mode (breaking schema change on the top-level field).
        - Schema transition — accessor shim `candidate.provenance?.source_mode ?? candidate.source_mode` applies at step_2c trigger lookup, default_importance.source_mode_boost, and compile_log_format. Grandfather rule — entries with top-level source_mode AND created < 2026-07-01 are exempt from provenance completeness check; Critic linter raises Sev 3 but does not block. Shim fallback sunsets 90 days after cutover.
        - Added ## CC Agent (Knowledge Librarian) section. Module 21 is now canonical source for the librarian agent body; cc/.claude/agents/knowledge-librarian.md becomes compile-output. Librarian's Step 1–4 protocol unchanged; gate logic at step_3d fires upstream of librarian invocation (librarian trusts upstream gating, no untrusted-input clause needed).
        - Cross-references Module 20 v7.1.0 accretion_candidate_tier_policy (HIGH tier for novel/predictive-derived candidates) and Module 03 v7.3.0 hc-runtime-to-accretion-gate Contract B entry.
    7.2.0:
      date: 2026-06-12
      driver: knowledgeforge-core-8zt
      spec: docs/planning/2026-06-12_module-21-linter-violation-counter-spec.md
      changes:
        - Added violation-event counter to Knowledge Base Linter. Linter gains two new responsibilities — event recording (append to .kf/linter/events.log) and snapshot aggregation (write .kf/linter/counter.json keyed by rule filename). Storage in .kf/linter/ avoids wiki contamination (already gitignored via .kf/ pattern).
        - Counter window — 30 days. Graduation threshold — ≥3 events across ≥2 distinct sessions (per Phase 2 spec 5fd Section 5).
        - linter_check.kind restricted at v1 to stateless artifact patterns — frontmatter_field_missing, frontmatter_field_value_disallowed, body_pattern_present, body_pattern_absent. Temporal-ordering kinds (e.g., "event X preceded event Y in session") require session log infrastructure deferred to follow-up bead.
        - Added dotfile-exclusion to linter scan (step 6.5) — prevents linter from checking its own state files against wiki schema rules.
        - Existing wiki/.linter_offset state file moved to .kf/linter/offset for consistency (per-machine operational state out of wiki partition).
        - cc_hooks emitter consumes graduation snapshot at compile time with three-check gate — snapshot freshness (rejects snapshots older than window_days), numeric re-derivation (catches snapshot tampering by recomputing eligibility from stored counts), and source_rule existence check.
        - Semver — minor bump justified — event log has no external contract surface; snapshot is the contract and is rebuilt-not-rotated. Section 3a of spec defends in detail.
    7.1.4:
      date: 2026-06-12
      driver: knowledgeforge-core-8gp
      spec: docs/planning/2026-06-12_module-25-entity-path-glob-resolver-spec.md
      changes:
        - step_2c_activation_profile.compute.path_globs gains a new lookup path — for ERA-consuming modes (Builder, Coordinator, Expert, Strategist, Critic), join era.entity_paths values into a flat deduped list. If >5 globs, keep 5 most-specific per the M25 7.1.0 glob comparison function.
        - step_3c_profile_cross_validate gains a downgrade rule — when ERA produced the globs (path_globs_meta entry has source: era) AND scope == global, DOWNGRADE trigger to task_bound and clear path_globs (instead of rejecting). Reason: ERA commonly produces globs for architectural patterns that are also global-scoped; silent rejection would make the M25 resolver invisible. Log to compile.md as era_global_glob_downgrade.
        - Manually-authored path_globs (no path_globs_meta entry) still reject on global scope per Phase 1 rule. Distinguishing source is via the new optional path_globs_meta sidecar.
        - Backwards-compatible — when ERA absent OR no entity_paths produced, existing Phase 1 logic applies unchanged.
    7.1.3:
      date: 2026-06-12
      driver: knowledgeforge-core-3ym
      changes:
        - step_5_file path formula corrected — was {wiki_root}/{domain}/{topic}.md (one file per topic), now {wiki_root}/{domain}/{YYYY-MM-DD}_{slug}.md (one file per entry) to match established convention. 218 entries on disk already followed this pattern; the spec was the stale party. Pre-existing bug surfaced by e0x Critic finding [5].
        - Added slug derivation rule (kebab-case from title), domain-field reference (with grandfather fallback per M23), and same-day collision suffixing (-2, -3...).
        - No behavior change for actual writes — every wiki entry written in the last 18 months used the corrected formula. Spec-vs-reality alignment only.
    7.1.2:
      date: 2026-06-10
      driver: knowledgeforge-core-e0x
      spec: docs/planning/2026-06-10_module-23-vocabulary-drift-reconciliation-spec.md
      changes:
        - Gate 4a (taxonomy validation) gains grandfather pre-check — entries whose creation timestamp is before 2026-06-10 (M23 v6.6.0 release) skip the domain/topic vocabulary validation if those fields are absent. See M23 Grandfathering section for timestamp resolution order (created → git first-commit → file mtime).
        - Knowledge Base Linter gains two new rules — (a) schema-completeness check is grandfather-aware; (b) created: vs git-first-commit divergence beyond ±1 day raises a MEDIUM finding (possible-backdated-entry).
        - No behavior change for entries created after 2026-06-10 — Gate 4a enforces the expanded M23 v6.6.0 vocabulary strictly on new entries.
    7.1.1:
      date: 2026-06-10
      driver: knowledgeforge-core-261
      spec: docs/planning/2026-06-10_cc-rules-and-hook-emitter-spec.md
      changes:
        - Added step_5b_emit_path_gated_rule to claude_code_runtime.filing — when activation_profile.trigger == path_bound AND scope == project, also write .claude/rules/kf-runtime/<slug>.md with paths: frontmatter populated from path_globs
        - KF-internal provenance metadata (kf_source, kf_bead, kf_activation_profile) lives in an HTML comment block at the bottom of the runtime rule file, NOT in the paths-bearing YAML frontmatter — avoids any substrate-parser ambiguity around unknown YAML siblings
        - On-error policy — wiki write already succeeded; log step_5b errors to compile.md and continue without rolling back the wiki entry
        - Cross-references Phase 2 cc target spec for emitter behavior; see knowledgeforge-core-261 implementation
    7.1.0:
      date: 2026-06-10
      driver: knowledgeforge-core-poz
      spec: docs/planning/2026-06-10_module-21-activation-profile-spec.md
      changes:
        - Added activation_profile block to accretion_candidate metadata (trigger, decidability, miss_cost, native, path_globs)
        - Added native:true as a third gate clause alongside novelty + reuse value
        - v1 ships native in deferred-activation mode (default false, no auto-emission) — gate envelope unchanged
        - Added step_2c_activation_profile (assignment) and step_3c_profile_cross_validate (scope cross-cut) to the claude_code_runtime filing protocol
        - Profile is substrate-agnostic; downstream dispatchers consume it (Module 22, future cc rules/hook emitters per Phase 2 spec 5fd)
        - Backwards-compatibility: existing modes do not auto-emit native:true; no behavioral change to v7.0.x gate yield
    7.0.6:
      date: 2026-05-24
      driver: knowledgeforge-core-8xq
      changes:
        - Updated step_4b_embedding to reflect MemPalace adoption — embedding happens inside MemPalace's mine pipeline (which wraps ChromaDB internally), not via direct ChromaDB calls from this module
        - step_4b_embedding's metadata description corrected — Phase 1 of Module 22 does NOT consume frontmatter at retrieval time; metadata is preserved at write time for Phase 2 readiness
        - rebuild_trigger reference clarified — Module 22's index rebuild is automatic via mempalace-wiki-mine.py (PostToolUse hook), not invoked from this module
    7.0.5:
      date: 2026-04-30
      changes:
        - Added Roadmap Phase Completion Trigger — `/kf-roadmap complete-phase <n>` now runs accretion review against the phase's pre-committed accretion_note; source_mode set to roadmap_phase; novelty_types restricted to [new_pattern, transferable_framework, reusable_analysis, reusable_diagnostic]. Roadmap and vision files themselves added to explicit Non-Triggers / planning artifacts list.
        - Added bidirectional prerequisite satisfaction check protocol for phase completion.
    7.0.4:
      date: 2026-04-29
      changes:
        - Expanded Terminal State — added quality_test heuristic, two missing indicators (boundaries/limitations explicit, anti-patterns documented), accretion_pending flag for Tier 2 intermediate filing, and user-promoted promotion path. Source: plans/ai-research-skills-integration.md ([project]-swd.9)
    7.0.3:
      date: 2026-04-29
      changes:
        - Expanded Source Fingerprint Deduplication — added partial match case (same finding_key, different content → update existing entry), no-database principle statement, and Critic-finding-specific fingerprint formula
        - 7.0.0 only handled exact match (skip) and no match (create); partial match left undefined. Source: plans/background-agents-integration.md ([project]-swd.8)
    7.0.2:
      date: 2026-04-29
      changes:
        - Added Dispatcher Boundary section formalizing gate-vs-dispatch separation — Module 21 owns the gate (novelty, reuse value, grounding ≥ 0.6, taxonomy compliance, candidate metadata). Downstream routers own dispatch (tier selection, physical write path). Downstream routers that bypass the Module 21 gate are a Critic linter HIGH finding.
        - No behavior change. Clarifies boundary for MemoryRouter and similar downstream dispatcher implementations.
    7.0.1:
      date: 2026-04-18
      changes:
        - Two-tier wiki accretion — project wiki ({project_root}/wiki/) for project-scoped knowledge, global wiki (~/.claude/wiki/) for cross-cutting patterns. Decision rule based on transferability. Bootstrap project wiki/ on first filing.
    7.0.0:
      date: 2026-04-14
      changes:
        - Add source_fingerprint deduplication — check before accreting, embed in frontmatter
        - Add terminal state requirement — only self-contained, complete, closed-loop artifacts accrete to Tier 0
    6.6.1: |
      - Added accretion_calibration section with yield tracking, novelty threshold, and reuse threshold (ERA finding F7)
      - Novelty and reuse value heuristics now have calibrated definitions and thresholds
      - Yield % surfaced in Critic linter health check output
      - Calibration records stored in wiki/accretion-calibration.yaml (Claude Code)
      - Healthy yield range: 20%–70%; actions defined for out-of-range conditions
    6.5.0: |
      - Filing protocol extended with taxonomy gate (Module 23 validation, new Step 4a) and embedding step (Module 22 upsert, new Step 4b)
      - Filing to disk is now Step 5, after both gates pass
      - Quality checklist updated with taxonomy and embedding checkboxes
      - Tier 3 description in memory_tiers updated to reflect MemPalace sidecar (Module 24)
      - Related Modules updated to include Modules 22, 23, 24
    6.3.1: |
      - Added autonomous maintenance cycle with cost-budgeting (heuristic-first, LLM-optional)
      - Added access logging with LRU+LFU composite salience scoring
      - Added lineage-safe consolidation protocol (merge with provenance, never delete with live lineage)
      - Added rotating linter coverage guarantee (offset-based, coverage SLA)
      - Extended accretion_candidate metadata with importance (int 1-5, aligns with Module 17)
      - Added default_importance inference table for auto-filed entries (mode + novelty type → inferred importance)
      - Added importance_source field (inferred | human_set) with 30-day linter nudge for unconfirmed entries
    6.2.0: |
      - Initial module — closes the compile-query-enhance loop
      - Accretion signal detection across all modes
      - Dual runtime: Claude Code (auto-file) vs. Claude Project (surface to user)
      - Knowledge base linter via Critic health check variant
      - Tier 0 persistent domain knowledge layer (extends Module 19)
      - Grounding-gated accretion quality (Module 15 integration)
      - Permission-aware filing (Module 20 integration)
      - Temporal metadata on all accreted entries (Module 17 integration)
      - Metacognitive over-accretion monitoring (Module 14 integration)
      - Calibrated accretion for production knowledge bases (Module 12 integration)
```

---

## Core Approach

KnowledgeForge modes produce valuable outputs — patterns, diagnostics, frameworks, analyses — that are consumed once and forgotten. Knowledge Accretion closes the loop: outputs that have reuse value get compiled back into the knowledge base so the system gets smarter through use, not just through manual ingestion.

**Primary function:** Detect when a mode's output contains knowledge worth persisting and route it to storage (auto-file) or surface it for human compilation (Claude Projects).

**Key insight:** The compile-query-enhance loop. Raw sources are compiled into structured knowledge. Queries operate on that knowledge. Query outputs that contain novel findings file back to enhance the knowledge base. The knowledge base grows through use.

**Design principle:** Accretion is selective, not exhaustive. Over-accretion pollutes the knowledge base with noise. Under-accretion loses valuable knowledge. The accretion signal must be calibrated to persist only what has genuine reuse value.

**Meta-principle alignment:** This patches a real weakness — knowledge evaporation between sessions — without adding overhead to simple interactions. Accretion signals fire only when novel, reusable knowledge is produced. Reckonings and routine outputs pass through without accretion checks.

---

## The Accretion Signal

During any mode's execution, flag output as `ACCRETION_CANDIDATE` when it meets three conditions:

1. **Novelty:** The output contains knowledge not already present in the existing knowledge base.
2. **Reuse value:** The knowledge would benefit future queries beyond the current session.
3. **Non-native:** The model does not already exhibit this behavior natively (v1: default false; see activation policy below).

Failing any condition → not a candidate. Drop silently for conditions 1 and 2 (no surfacing, no metadata generation, no filing). For condition 3 (native suppression), append a suppression event to `compile.md` with the candidate body and `suppressed_by: native` reason so over-suppression is detectable in linter health checks.

**v1 activation policy for the `native` clause:** The `native` field defaults to `false`. No mode auto-emits `native: true` at v1. The clause is structurally present (third condition) but practically inert because the only assignment source at v1 is human review via the `importance_source: inferred → human_set` lifecycle. Mode self-evaluation of "is this thing I just produced something I produce natively?" is circular; auto-evaluation criteria are deferred to a separate calibration bead (see `knowledgeforge-core-och`).

### Detection by Source Mode

| Source Mode | Accretion Trigger | Example |
|-------------|-------------------|---------|
| Synthesizer | Pattern not in existing knowledge base | New design pattern extracted from 3+ examples |
| Critic | Finding that contradicts existing knowledge | Linter health check discovers stale assertion |
| Expert | Novel analysis with reuse value | Domain deep-dive that future queries would benefit from |
| Debugger | Resolved diagnostic with reusable root cause | Root cause pattern applicable beyond the specific bug |
| Strategist | Decision framework with transferable criteria | Trade-off matrix reusable for similar future decisions |
| Builder | Specification that establishes a reusable template | New spec pattern worth adding to template library |
| Calibrator | Configuration pattern for a novel stack combination | Config template reusable for similar projects |
| Roadmap phase complete | Learnings surfaced during `/kf-roadmap complete-phase <n>` | Pattern, decision, or anti-pattern identified when closing a phase |

### Roadmap Phase Completion Trigger (7.0.5)

When `/kf-roadmap complete-phase <n>` fires, it runs an accretion review as a standard step. This is a **human-prompted accretion event** — not an automatic signal. The command displays the phase's `accretion_note` (pre-committed learning intent) and asks whether learnings worth filing emerged.

```yaml
roadmap_phase_completed:
  trigger: "/kf-roadmap complete-phase <n>"
  action: run_accretion_review
  source: phase.accretion_note  # The pre-committed intent from roadmap creation
  prompt: |
    Phase [N] complete — were there learnings worth filing?
    Accretion note: "[phase.accretion_note]"
    - Any patterns, decisions, or anti-patterns to preserve?
    - Any wiki entries to update?
    (Answer "none" if nothing warrants filing — that's valid.)
  on_learning_identified:
    route_to: Module 21 accretion filing protocol (standard flow)
    novelty_types_allowed: [new_pattern, transferable_framework, reusable_analysis, reusable_diagnostic]
    source_mode: roadmap_phase
```

**Bidirectional link — prerequisite satisfaction check:**
When a new wiki entry is filed via phase-completion accretion, check `wiki/roadmap.md` for any phase with `knowledge_prerequisites` listing that entry's path. If found, surface:
> *"Phase [N] listed this as a knowledge prerequisite. It may now be ready to start."*

**What does NOT accrete:**
- The roadmap file itself (`wiki/roadmap.md`) — planning artifacts are not knowledge artifacts
- Phase status updates (in_progress → completed) — operational state, not reusable knowledge
- The vision file (`wiki/vision.md`) — strategic orientation document, not a wiki entry

### Non-Triggers

Accretion does NOT fire on:

- Reckonings (factual lookups — already known)
- Routine mode outputs that apply existing knowledge without extending it
- Outputs with grounding score below 0.6 without explicit caveat handling
- Session-specific context with no transferable value (e.g., "user prefers tabs")
- Roadmap or vision file updates (these are planning artifacts, not knowledge entries)

---

## Source Fingerprint Deduplication

**Principle:** Store deduplication state in the artifact itself. No external dedup database needed — wiki entries are the source of truth for what has been captured. Works offline. No state synchronization required.

Every wiki entry MUST include a `source_fingerprint` in its frontmatter:

```yaml
---
source_fingerprint: [SHA-256 hash or stable identifier of the source artifact]
---
```

**Before accreting any artifact:**
1. Compute or extract the `source_fingerprint` of the candidate
2. Grep existing wiki entries for that fingerprint
3. **Exact match** → skip accretion (duplicate source, already captured)
4. **Partial match** (same `finding_key`, different content hash) → update the existing entry with the new content; preserve the original `source_fingerprint`, add `updated_at`
5. **No match** → proceed with accretion, embed fingerprint in new entry

**Fingerprint construction:**
- For Critic findings: hash of (source_mode + finding_key + core_content_hash)
- For conversation turns: hash of (session_id + turn_index)
- For documents: hash of content (first 500 chars + length)
- For URLs: the URL itself (canonical form)
- For tool outputs: hash of (tool_name + input_hash + output_hash)

The partial match case handles knowledge that evolves — the finding is the same but has been refined. Updating the existing entry is preferable to creating a duplicate with marginally different content.

---

## Terminal State Requirement

A knowledge artifact reaches terminal state when it is complete, self-contained, and doesn't require session context to be understood.

**Quality test:** *"A reader unfamiliar with this session should be able to derive actionable conclusions from this artifact alone."* If that's not true, it's not terminal.

Only **terminal artifacts** accrete to Tier 0 (wiki). Intermediate artifacts stay in Tier 2 (working state) with an `accretion_pending` flag until they reach terminal state or are explicitly promoted by the user.

**Terminal state indicators** — an artifact is terminal when ALL of the following hold:
1. Core question answered with evidence (findings are self-contained)
2. No critical open questions that would change the conclusions
3. Boundaries and limitations are explicit
4. Anti-patterns documented where applicable
5. No active revision loop (Critic ↔ Builder cycle has closed)
6. Grounding score ≥ 0.6 (Module 15)

**Intermediate artifacts** (file to Tier 2 with `accretion_pending: true`):
- Draft specs mid-revision
- Partial debugging hypotheses
- Research notes with open questions
- Any artifact with `reproduction_status: failed` (Module 09)

Intermediate artifacts in Tier 2 are reviewed on the next health check cycle. They either reach terminal state naturally (revision loop closes, open questions resolve) or are explicitly promoted by the user.

**Rationale:** Tier 0 is a trust layer. Accreting intermediate work pollutes it with uncertain or incomplete knowledge that later sessions treat as authoritative.

---

## Accretion Calibration (6.6.1)

Accretion is only valuable if it is selective. An uncalibrated accretion gate drifts toward over-filing (noise degrades retrieval quality) or under-filing (missed knowledge). This section defines the calibration protocol that keeps the gate effective over time.

```yaml
accretion_calibration:

  yield_definition:
    metric: "Percentage of flagged accretion candidates confirmed novel and reusable
             by the Critic linter on next health check"
    healthy_range: "20% to 70%"
    below_20_percent: |
      Gate is too permissive — flagging too many candidates, most of which are redundant.
      Action: Tighten novelty heuristic. Increase grounding score floor.
      Likely cause: Mode outputs flagged when they apply existing knowledge without extending it
      (per Non-Triggers rule — enforce more strictly).
    above_70_percent: |
      Gate may be too restrictive — valid novel knowledge passing through without accreting.
      OR: Modes are producing consistently high-value novel outputs (healthy signal).
      Action: Review skipped candidates from last cycle. If valuable knowledge was missed,
      lower novelty threshold. If the 70%+ yield is accurate, no action needed.

  novelty_threshold:
    definition: |
      An output is novel if it contains at least one of:
        (a) A pattern, framework, or finding not present in any existing Tier 0 entry
        (b) A correction or update to an existing Tier 0 entry (supersedes relationship)
        (c) A synthesis that combines two or more existing entries into a new insight
    non_novel_by_definition:
      - Application of an existing pattern without extension
      - Restatement of a Tier 0 entry in different words
      - Session-specific context (user preferences, one-off decisions)

  reuse_threshold:
    definition: |
      An output has reuse value if a hypothetical future session querying on the same
      topic would benefit from finding this entry in Tier 0 rather than regenerating it.
    signals:
      strong_reuse: Output is a diagnostic pattern, decision framework, or structural analysis
        that required significant reasoning to produce and is likely to recur.
      weak_reuse: Output is a factual answer or narrow domain finding unlikely to recur
        in a different context.
    threshold: Strong reuse signals → accrete. Weak reuse signals → skip.

  yield_tracking:
    log_location:
      claude_code: wiki/accretion-calibration.yaml
      claude_projects: Surface yield report in linter health check output (user-maintained)
    log_format:
      per_session:
        candidates_flagged: integer
        candidates_filed: integer
        candidates_skipped: integer
        skip_reasons: array[string]
    rolling_window: Last 10 sessions
    linter_integration: |
      The Critic linter variant (Module 07, linter protocol step 2) includes a calibration
      check as part of each health check run:
        - Pull yield stats from accretion-calibration.yaml (Claude Code) or user-provided log
        - If yield < 20%: surface "ACCRETION_GATE: too permissive — tighten novelty heuristic"
        - If yield > 70% and review of skipped candidates shows missed value: surface
          "ACCRETION_GATE: may be too restrictive"
        - Otherwise: surface yield % as a health metric alongside KB health assessment
    calibration_cycle: Run after every 5 linter health checks or when yield exits healthy range.
```

---

## Accretion Candidate Metadata

Every candidate gets tagged with:

```yaml
accretion_candidate:
  # source_mode MOVED to provenance.source_mode in 7.3.0 (SPEC 4 D2). The top-level
  # source_mode field below is preserved for grandfather-window entries
  # (created < 2026-07-01) only and slated for removal 90 days after cutover.
  # New entries MUST populate provenance.source_mode; consumers MUST use the
  # accessor shim: candidate.provenance?.source_mode ?? candidate.source_mode
  source_mode: [DEPRECATED 7.3.0 — see provenance.source_mode below]
  source_session: redacted
  confidence: [mode's output confidence at time of production]
  grounding_score: [per Module 15]
  novelty_type: [new_pattern | contradiction | reusable_analysis | reusable_diagnostic | transferable_framework | template_candidate]
  knowledge_target: [where it should be filed — wiki section, concept article, or index entry]
  staleness_risk: [stable | slow_decay | fast_decay]
  importance: [integer 1-5 — base value independent of recency, aligns with Module 17 decay model]
  importance_source: [inferred | human_set]
  created: [ISO datetime]

  # ---------------------------------------------------------------------------
  # Provenance — added 7.3.0 (SPEC 4 D2)
  # ---------------------------------------------------------------------------
  #
  # Required for candidates emitted post-2026-06-13 by [project] runtime (Contract B,
  # Module 03 hc-runtime-to-accretion-gate). Consumed by step_3d_provenance_gate to
  # route cross-cutting novel/predictive candidates through surface_for_human_review.
  # Grandfather rule: entries with top-level source_mode AND created < 2026-07-01
  # are exempt from the gate's provenance completeness check; Critic linter raises
  # Sev 3 finding "schema migration pending — provenance fields absent" but does
  # not block. Shim fallback (`?? candidate.source_mode`) sunsets 90 days post-cutover.
  #
  provenance:
    loop_id: string         # required when emitted by [project]; null when direct orchestrator
    run_id: string          # required when emitted by [project]; null when direct orchestrator
    decision_tag: string    # required; enum [reckoning, evaluative_judgment, predictive_judgment, novel_judgment]
    source_mode: string     # required; moved from top-level in 7.3.0
    signals: array          # optional; entries:
                            #   {type: verifier_signoff, ref: <pointer>}
                            #   {type: human_review_signal, ref: <pointer>}
                            # Presence of verifier_signoff OR human_review_signal
                            # is the vetting signal consumed by step_3d.
  
  # Default importance inference (when human assignment isn't available at filing time):
  default_importance:
    rule: "Auto-filed entries infer importance from source mode + novelty type. Human override always wins."
    inference_table:
      contradiction: 4          # Contradictions threaten knowledge base integrity
      new_pattern: 3            # Patterns are reusable but need validation
      reusable_analysis: 3      # Analyses have clear reuse value
      transferable_framework: 4 # Frameworks shape future decisions
      reusable_diagnostic: 2    # Diagnostics are useful but narrow
      template_candidate: 2     # Templates are useful but low-consequence
    source_mode_boost:
      # source_mode lookup uses accessor shim (added 7.3.0, SPEC 4 D2b):
      #   source_mode = candidate.provenance?.source_mode ?? candidate.source_mode
      # Grandfather-window entries (created < 2026-07-01) may still carry only the
      # top-level source_mode; shim resolves cleanly. Sunsets 90 days post-cutover.
      Expert: +1                # Expert deep dives tend to be high-value (cap at 5)
      Strategist: +1            # Strategic frameworks have outsized reuse (cap at 5)
    floor: 1
    ceiling: 5
    staleness_override:
      fast_decay: "Cap at 3 — high importance + fast decay creates noisy archival churn"
    linter_check:
      trigger: "Entries with importance_source: inferred AND age > 30 days"
      severity: LOW
      message: "Entry still at inferred importance. Consider human review to confirm or adjust."
  
  # Staleness risk definitions:
  # stable: Knowledge unlikely to change (design patterns, mathematical relationships, architectural principles)
  # slow_decay: Knowledge valid for months/years but eventually superseded (best practices, tool recommendations, API patterns)
  # fast_decay: Knowledge valid for weeks/months (version-specific behavior, current pricing, active bug workarounds)

  # ---------------------------------------------------------------------------
  # Activation profile — added 7.1.0
  # ---------------------------------------------------------------------------
  #
  # Substrate-agnostic metadata describing HOW a downstream dispatcher should
  # surface this candidate. Computed in core, consumed by downstream routers.
  # The profile is dispatch-input only — except `native`, which is gate-input
  # (see Three-Condition Test above). The profile NEVER references substrate
  # concepts like "is there a rules dir" or "settings.json exists" — those
  # are downstream-target concerns, not core concerns.
  #
  activation_profile:
    trigger: invariant | path_bound | task_bound
      # invariant: applies regardless of which files the session touches
      # path_bound: applies only when files matching path_globs are read
      # task_bound: applies only when a specific mode/skill is invoked
      #
      # Trigger is descriptive metadata about WHEN this knowledge is relevant.
      # Downstream dispatchers map it onto substrate (e.g., cc maps
      # invariant→unscoped rule, path_bound→path-scoped rule, task_bound→skill).

    decidability: true | false
      # Does a mechanical predicate exist for "this rule was applied / violated"?
      # true  → eligible for hook-class enforcement downstream
      # false → advisory only; downstream may only render as guidance
      # Dispatch input. Not consulted at the gate.

    miss_cost: low | medium | high
      # If this knowledge is not surfaced when relevant, what is the cost?
      # low    → minor inefficiency, easy correction
      # medium → recurring rework, possible quality regression
      # high   → defect class, lost data, broken deploy, customer-visible bug
      # Dispatch input. Selects between tiers; not consulted at the gate.

    native: true | false
      # Does the model already exhibit this behavior natively?
      # true  → SUPPRESS at gate (third condition; do not persist)
      # false → proceed to filing protocol
      # Codifies the KF meta-principle: patch weaknesses, do not scaffold
      # strengths. See `~/.claude/rules/kf-meta.md` and Module 13 commentary.
      # Gate input. The one gate-clause field in this block.
      # v1: default false; no mode auto-emits true; criteria deferred to
      # follow-up calibration bead (knowledgeforge-core-och).

    path_globs: [string]      # optional; required only when trigger == path_bound
      # Glob patterns identifying the files for which this knowledge is relevant.
      # Substrate-agnostic shape (string globs). Downstream cc target uses these
      # verbatim as the `paths:` frontmatter on a generated rule file.
      # Constraints:
      #   - Repo-specific by nature → travels ONLY with project-scoped candidates
      #     for manually-authored globs. ERA-resolver-produced globs on
      #     global-scope candidates DOWNGRADE to task_bound at step_3c
      #     (7.1.4+) instead of rejecting.
      #   - Empty list with trigger==path_bound triggers downgrade to task_bound.
      #   - Provenance: populated by ERA's entity → path-glob resolver (M25 7.1.0+)
      #     OR by producing mode emitting explicit globs in accretion_note.
      #     See path_globs_meta below for source distinction. Expected
      #     post-resolver distribution: ~60% invariant / ~25% task_bound /
      #     ~15% path_bound (calibrate post-ship). Pre-resolver baseline was:
      #     ~90% invariant / ~10% task_bound / <1% path_bound.

    path_globs_meta: [object]     # optional sidecar to path_globs (added 7.1.4, bead 8gp)
      # Per-glob metadata: source provenance. Only ERA-resolver-produced
      # globs need an entry; manually-authored globs may omit their entry
      # (treated as source: manual for the purpose of step_3c logic).
      # Shape: [{glob: <string>, source: era|manual}, ...]
      # Used by step_3c to distinguish ERA-driven downgrades from
      # manual-author rejections on global scope.
```

---

## Two Runtime Behaviors

### Claude Code (Filesystem Access)

When running as a Claude Code agent with filesystem access, accretion is automatic with logging.

```yaml
claude_code_runtime:
  detection:
    - During mode execution, evaluate output against accretion triggers
    - Check existing wiki/ directories for duplicate or superseding entries

  filing:
    step_2c_activation_profile:
      # Added 7.1.0. Runs after the three-condition gate, before step_3 scope classification.
      # Assigns trigger/decidability/miss_cost/native. Does NOT validate scope cross-cuts.
      compute:
        trigger:
          # Inferred from the mode that produced the candidate + the candidate's content shape.
          # source_mode lookup uses accessor shim (added 7.3.0, SPEC 4 D2b):
          #   source_mode = candidate.provenance?.source_mode ?? candidate.source_mode
          # Lookup table:
          #   Synthesizer (new_pattern), Strategist (transferable_framework) → default invariant
          #   Builder (template_candidate), Calibrator (template_candidate)  → default invariant
          #   Critic linter (contradiction)                                  → default invariant
          #   Expert (reusable_analysis)                                     → invariant unless ERA emitted entity-scoped filters → path_bound
          #   Debugger (reusable_diagnostic)                                 → path_bound if filename/path appears in candidate body; else task_bound
          # Modes may override the default by emitting trigger explicitly in their accretion_note.

        decidability:
          # Heuristic: does the candidate body include a mechanical predicate?
          #   true  if body contains imperative + observable predicate
          #         ("Run X before Y", "All Z must include W")
          #   false otherwise
          # Modes may override.

        miss_cost:
          # Heuristic: rough mapping from novelty_type + grounding.
          # Default table:
          #   contradiction             → high
          #   reusable_diagnostic       → medium
          #   reusable_analysis         → medium
          #   transferable_framework    → medium
          #   new_pattern               → low
          #   template_candidate        → low
          # Boost by one tier if grounding ≥ 0.85.
          # Modes may override.

        native:
          # v1: always false (see Three-Condition Test activation policy). The gate clause
          # still fires when native==true, but v1 has no auto-emission of native==true.

        path_globs:
          # Populated only when trigger == path_bound AND the producing mode authored explicit globs.
          # At v1, ERA→path-glob resolver is deferred (bead knowledgeforge-core-8gp); expect <1% of candidates to populate this field.

      partial_validate:
        - If trigger == path_bound AND path_globs is empty → downgrade trigger to task_bound; log downgrade in compile_log
        - If trigger != path_bound AND path_globs is non-empty → strip path_globs (log warning)
        # NOTE: path_bound+global cross-cut is NOT evaluated here — see step_3c below.

      next: step_3_scope_classification

    step_3_scope_classification:
      question: "Would this help someone working on a DIFFERENT project?"
      yes → global:
        wiki_root: "~/.claude/wiki/"
        compile_log: "~/.claude/wiki/compile.md"
        signals:
          - Reusable technique applicable to any project using this stack
          - Framework behavior not specific to this repo (Svelte 5, Laravel, etc.)
          - Architectural principle or cross-cutting design pattern
      no → project:
        wiki_root: "{project_root}/wiki/"
        compile_log: "{project_root}/wiki/compile.md"
        signals:
          - References filenames, APIs, or config paths unique to this repo
          - Documents a decision made for this project (architectural, tooling, naming)
          - Describes a bug or behavior fix specific to this codebase
      unclear → project:
        reason: "Safer default — project-scoped knowledge can be promoted to global later; the reverse requires re-evaluation"

    step_3b_bootstrap:
      condition: "wiki_root does not exist on filesystem"
      actions:
        - Create {wiki_root} directory
        - Create {wiki_root}/compile.md with header "# Knowledge Accretion Log\n\n"
        - "Do not create index.md or subdirectories — those are created on first filing"

    step_3c_profile_cross_validate:
      # Added 7.1.0. Runs after step_3 (scope known) and step_3b (bootstrap done), before step_4a (taxonomy).
      # Validates the cross-cuts between activation_profile and scope.
      validate:
        # Updated 7.1.4 (bead 8gp) — split into two sub-rules based on path_globs source.
        - If trigger == path_bound AND scope == global AND all path_globs entries have a path_globs_meta sidecar with source: era → DOWNGRADE candidate (do NOT reject)
          action: "Set trigger to task_bound; clear path_globs; clear path_globs_meta"
          reason: "ERA-resolved globs commonly appear on globally-scoped candidates (architectural patterns spanning multiple repos); task_bound is the correct semantic for cross-repo entity-anchored knowledge"
          log_to: compile_log_format with reason "era_global_glob_downgrade"
        - If trigger == path_bound AND scope == global AND any path_globs entry lacks an era-source sidecar (manually-authored) → reject candidate
          reason: "manually-authored path_globs are repo-specific; cannot travel with a global-scoped wiki entry"
          log_to: compile_log_format with reason "scope_glob_cross_cut"
        # Future cross-cuts (when added in subsequent revisions) attach here.

      next: step_3d_provenance_gate

    step_3d_provenance_gate:
      # Added 7.3.0 (SPEC 4 D1). Runs after step_3 (scope known) and step_3c (profile
      # cross-cuts validated), before step_4a (taxonomy). Consumes Contract B provenance
      # (Module 03 hc-runtime-to-accretion-gate) emitted by [project] runtime.
      description: |
        Cross-cutting wiki entries (~/.claude/wiki/) derived from novel or predictive
        decisions require an external vetting signal — separate-verifier sign-off OR
        human review. Project-scoped wiki entries ({project_root}/wiki/) derived from
        novel or predictive decisions also surface for human review before filing.
        Reckoning/evaluative candidates pass through unchanged.
      inputs:
        - provenance (per Contract B): {loop_id, run_id, decision_tag, source_mode, signals[]}
      gates:
        cross_cutting_novel_or_predictive:
          condition: |
            scope == global AND decision_tag ∈ {novel_judgment, predictive_judgment}
          require: |
            verifier_signoff OR human_review_signal in provenance.signals[]
          on_fail: surface_for_human_review
          log_to: compile_log_format with reason "cross_cutting_unvetted_surfaced"
        project_novel_or_predictive:
          condition: |
            scope == project AND decision_tag ∈ {novel_judgment, predictive_judgment}
          action: surface_for_human_review
          rationale: |
            Module 13 → Module 20 v7.1.0 accretion_candidate_tier_policy maps
            novel/predictive to HIGH risk tier. The `unvetted` tag is an annotation,
            not a checkpoint. Auto-file with annotation silently bypasses Module 20's
            HIGH-tier human-confirmation requirement. Surfacing for human review
            preserves the audit trail.
          log_to: compile_log_format with reason "project_unvetted_surfaced"
        cross_cutting_reckoning_or_evaluative:
          condition: |
            scope == global AND decision_tag ∈ {reckoning, evaluative_judgment}
          action: proceed (existing path)
        project_reckoning_or_evaluative:
          condition: |
            scope == project AND decision_tag ∈ {reckoning, evaluative_judgment}
          action: proceed (existing path)
      provenance_completeness_check:
        condition: |
          provenance missing OR provenance.decision_tag absent
        action: |
          surface_for_human_review with provenance_missing: true; user decides
          file destination (project unvetted | cross-cutting with override | discard)
        log_to: compile_log_format with reason "incomplete_provenance"
        grandfather_exemption:
          # Per SPEC 4 D2b grandfather rule. Pre-cutover entries lacking provenance
          # do not block at this check; Critic linter raises Sev 3 instead.
          condition: |
            entry.created < 2026-07-01 AND top-level source_mode is present
          action: proceed (existing path) with linter_finding Sev3 "schema migration pending — provenance fields absent"
      surface_for_human_review_protocol:
        show_to_user:
          - candidate body (full)
          - provenance summary (loop_id, run_id, decision_tag, source_mode, signals)
          - proposed scope (global | project)
          - reason for surfacing
        user_options:
          - file_to_project (with `unvetted: true` frontmatter)
          - file_to_global_with_override (Module 20 HIGH-tier confirmation logged)
          - discard
      unvetted_tag_lifecycle:
        # Per SPEC 4 D5. Entries filed with unvetted: true via this protocol.
        - Appear in compile.md log with reason flagged
        - Skipped by Critic linter contradiction-detection unless invoked with --include-unvetted
        - May be promoted to vetted by human review + explicit frontmatter flip
        - Stale unvetted entries (age > 60 days, no promotion) surface as Critic linter
          Sev 3 finding "Unvetted entry past review window — promote or archive"
      next: step_4a_taxonomy_gate

    step_4a_taxonomy_gate:
      action: "Validate entry.domain, entry.topic, and all entry.tags against Module 23 controlled vocabulary"
      on_fail: "Reject with nearest-match suggestion. Do not proceed to embedding or disk write."
      tag_count: "1–5 tags required. Reject outside this range."
      grandfather_precheck:
        # Added 7.1.2 (bead e0x). When the entry's creation timestamp resolves to
        # before 2026-06-10 (M23 v6.6.0 release) AND the entry has neither domain
        # nor topic field, the gate skips domain/topic vocabulary validation.
        # Tags validation still applies. See M23 Grandfathering section for the
        # creation-timestamp resolution order (created → git first-commit → file mtime).
        condition: "creation_timestamp < 2026-06-10 AND entry.domain is absent AND entry.topic is absent"
        action: "Skip domain/topic vocabulary validation. Tags must still be approved."
        rationale: "Pre-gate entries are exempt; lazy migration on next touch (M23 v6.6.0)."

    step_4b_embedding:
      action: "Embedding happens inside MemPalace's mine pipeline — Module 21 does not invoke an embedder directly. The mempalace-wiki-mine.py PostToolUse hook fires on every wiki write and calls `python -m mempalace mine` which ChromaDB-indexes the entry."
      metadata_written: "Frontmatter fields (domain, topic, tags, importance, created_at, last_accessed, grounding_score, staleness_risk) are present in the on-disk markdown for human readers and Phase 2 readiness. Module 22 Phase 1 does NOT consume these at retrieval time."
      rebuild_trigger: "No manual rebuild needed — mempalace-wiki-mine maintains the index incrementally on every Write/Edit/MultiEdit. If MemPalace's index is lost, run `python -m mempalace mine <wiki_dir>` to re-index from disk."

    step_5_file:
      # Path formula updated 7.1.3 (bead 3ym) — was {wiki_root}/{domain}/{topic}.md
      # (one file per topic), which conflicted with the established
      # one-file-per-entry convention used on disk (218 entries follow
      # YYYY-MM-DD_<slug>.md across all wiki/ subdirs).
      - Write compiled markdown to {wiki_root}/{domain}/{YYYY-MM-DD}_{slug}.md
      - slug = kebab-case of title (lowercase; non-alphanumeric → hyphen; collapse runs; trim leading/trailing hyphens)
      - {domain} comes from the entry's domain: field (M23 controlled vocabulary; grandfathered entries may legitimately lack this field — see M23 Grandfathering section); when absent, derive from the directory hint in knowledge_target
      - {YYYY-MM-DD} is the entry's created: date (filing time, not authoring time of the source material)
      - Include metadata header (yaml frontmatter with accretion_candidate fields)
      - Update {wiki_root}/index.md with new entry (title, path, novelty_type, created date)
      - Append accretion event to {wiki_root}/compile.md log
      - Filename collisions on same-day same-slug — suffix with `-2`, `-3`, etc. before the .md extension

    step_5b_emit_path_gated_rule:
      # Added 7.1.1 (Phase 2 spec 5fd). Runs after step_5 wiki write, before user_surface.
      # Mirrors the wiki entry into the cc rules substrate as a runtime-accreted
      # path-gated rule. Only fires for path_bound + project candidates.
      condition: activation_profile.trigger == path_bound AND scope == project AND path_globs is non-empty
      action:
        - Write .claude/rules/kf-runtime/<slug>.md with `paths:` YAML frontmatter populated from path_globs
        - Body: candidate body content (markdown)
        - Append KF-internal provenance to an HTML comment block at the bottom of the file (kf_source, kf_bead, kf_candidate_id, kf_created, kf_activation_profile)
        - Provenance is in an HTML comment, NOT in the YAML frontmatter — avoids substrate-parser ambiguity around unknown YAML siblings to the `paths:` key (see Phase 2 spec 5fd Critic finding [4])
      partition_note:
        - .claude/rules/kf/ is the COMPILE-TIME partition (owned by kf-compile.py emit_cc_rules_partition)
        - .claude/rules/kf-runtime/ is the RUNTIME partition (owned by this step)
        - Compile-time orphan cleanup operates only on kf/, NOT kf-runtime/
      on_error:
        - Wiki write (step_5) has already succeeded; do NOT roll back the wiki entry
        - Log step_5b error to compile.md with reason "step_5b_rule_emit_failed: <message>"
        - Continue to user_surface
      cleanup:
        - Runtime kf-runtime/ entries are NOT automatically deleted on next compile
        - The Module 21 linter (Knowledge Base Linter, see below) flags stale entries (no matching code for the paths: globs) for human archival
        - Auto-deletion is OUT of scope at v1 — avoids silent loss

  user_surface:
    project_scoped: "Filed [description] to wiki/[path]"
    global_scoped: "Filed [description] to ~/.claude/wiki/[path]"
    - Include one-line summary of what was accreted and why

  compile_log_format:
    # Source line uses accessor shim (added 7.3.0, SPEC 4 D2b):
    #   source_mode = candidate.provenance?.source_mode ?? candidate.source_mode
    # Grandfather-window entries (created < 2026-07-01) may still carry only the
    # top-level source_mode; shim resolves cleanly. Sunsets 90 days post-cutover.
    ```
    ## [ISO datetime] — [novelty_type]
    Source: [mode] | Session: [id] | Grounding: [score]
    Scope: project | global
    Target: [wiki_root]/[path]
    Summary: [one-line description]
    ```

  duplicate_handling:
    - Check both wiki roots before filing (project and global may have overlapping entries)
    - If existing entry covers same topic: compare timestamps and grounding scores
    - Higher grounding supersedes lower grounding
    - Newer entry with equal grounding supersedes older entry
    - Log supersession in compile.md with link to both entries
```

### Claude Project (No Filesystem Access)

When running in Claude Projects without filesystem access, accretion surfaces candidates to the user for manual compilation.

```yaml
claude_project_runtime:
  detection:
    - Same trigger logic as Claude Code
    
  surface_format:
    ```
    ---
    **Accretion candidate** ([novelty_type])
    
    This [pattern/finding/analysis] has reuse value beyond this session.
    Here's the compiled article ready to add to project knowledge:
    
    ---
    [formatted markdown article with metadata header]
    ---
    
    **Suggested location:** [knowledge_target]
    **Staleness risk:** [stable/slow_decay/fast_decay]
    ```
    
  routing_index_tag:
    - After surfacing: tag in routing index as `accretion_surfaced`
    - Prevents re-flagging the same candidate in subsequent turns
    
  batching:
    - If multiple candidates emerge in one session, batch them at session end
    - Present as a numbered list with individual articles
    - "This session produced [N] knowledge candidates. Here they are:"
```

---

## The Feedback Loop

The compile-query-enhance cycle works as follows:

```
┌──────────────────────────────────────────────────┐
│                                                  │
│   1. COMPILE: Raw sources → Structured wiki      │
│      (manual ingestion, initial knowledge base)  │
│                                                  │
│   2. QUERY: User queries → Mode execution        │
│      (modes operate on compiled knowledge)       │
│                                                  │
│   3. ENHANCE: Mode outputs → Accretion check     │
│      (novel outputs file back into wiki)         │
│                                                  │
│   4. VALIDATE: Critic linter → Health check      │
│      (periodic consistency and staleness review) │
│                                                  │
│            ┌──── Loop back to 2 ────┐            │
│            │                        │            │
└──────────────────────────────────────────────────┘
```

Each cycle makes the knowledge base more complete, more current, and more internally consistent.

---

## Knowledge Base Linter (Critic Health Check Variant)

The Critic Agent gains a new trigger: "health check the knowledge base." This is the linter behavior — distinct from reviewing a single artifact.

```yaml
linter_behavior:
  trigger: "Health check the knowledge base" or "Lint the wiki" or periodic scheduling
  
  protocol:
    1. Scan all entries in the knowledge base (wiki/ or project knowledge files), EXCLUDING dotfiles (added 7.2.0 — prevents linter from checking its own state files against wiki schema rules)
    2. For each entry, check:
       - Staleness: Has staleness_risk window expired? Flag entries past their expected lifetime.
       - Contradiction: Does this entry contradict any other entry? Flag both with specific conflict.
       - Redundancy: Is this entry substantially duplicated by another? Flag for merge.
       - Grounding decay: Has the grounding score's basis changed? (e.g., API behavior changed, library deprecated)
       - Orphan references: Does this entry reference other entries that don't exist?
       - Schema completeness (added 7.1.2): For entries whose creation timestamp is on or after 2026-06-10 (M23 v6.6.0 release), check that `domain` and `topic` are present and validate against the M23 controlled vocabulary. Grandfathered entries (creation pre-v6.6.0) are exempt — see M23 Grandfathering section.
       - Backdating detection (added 7.1.2): Compare each entry's `created:` field against the first-commit date for the entry's file in git history. Divergence beyond ±1 day raises a MEDIUM finding (`possible-backdated-entry`). Catches the honor-system bypass of the grandfather gate.
    3. Produce maintenance backlog ranked by impact:
       - CRITICAL: Contradictions between entries (knowledge base is self-inconsistent)
       - HIGH: Stale entries with fast_decay past window (actively misleading); post-v6.6.0 entries with missing or invalid domain/topic schema
       - MEDIUM: Redundant entries (noise, not harm); possible-backdated-entry findings
       - LOW: Orphan references, minor formatting issues
    4. Record violation events (added 7.2.0 — bead 8zt): for each cc_rules entry with a linter_check block whose kind is in {frontmatter_field_missing, frontmatter_field_value_disallowed, body_pattern_present, body_pattern_absent}, evaluate the pattern against wiki entries matching linter_check.target_files. Append matches to .kf/linter/events.log (tab-separated: ISO_timestamp\tsession_id\trule_filename\tevent_type). Temporal-ordering kinds (e.g., "event X preceded event Y in session") are NOT supported at v1 — deferred to follow-up bead.
    5. Aggregate graduation snapshot (added 7.2.0): after scanning, rotate events older than 30 days from .kf/linter/events.log. Compute per-rule counts (events, distinct session_ids, first/last seen, eligibility — eligible_for_graduation = event_count ≥ 3 AND len(session_ids) ≥ 2). Write .kf/linter/counter.json (overwriting). Snapshot is the source of truth for cc_hooks emitter graduation decisions.
    6. Add new "Graduation candidates" finding section to output — rules that crossed the threshold this run; recommendation includes the cc_hooks frontmatter stub the module author would add (the linter recommends the structure, but the author decides command, matcher, and source_rule wiring per their domain knowledge).
    
  output_format:
    ```
    ## Knowledge Base Health Check — [date]
    
    Entries scanned: [N]
    
    ### Critical ([count])
    [contradictions with specific entry references]
    
    ### High ([count])  
    [stale entries with recommended action: update/archive/delete]
    
    ### Medium ([count])
    [redundancies with merge recommendations]
    
    ### Low ([count])
    [orphan references, formatting]
    
    ### Health summary
    [overall assessment: healthy / needs attention / degraded]
    ```
    
  accretion_integration:
    - Contradictions found during linting are themselves ACCRETION_CANDIDATEs (novelty_type: contradiction)
    - The linter may produce corrected entries that supersede stale ones
    
  coverage_rotation:
    description: "Ensures every entry is linted at least once per N cycles"
    mechanism:
      - Linter stores wiki/.linter_offset — the index of the last entry processed
      - Each run starts from the stored offset, wraps around, writes the new offset
      - Guarantees every entry is linted at least once per ceil(total_entries / entries_per_run) cycles
    cost_budgeted_runs:
      - When a run can't cover all entries (token budget exhausted), the rotating offset ensures no entry is permanently skipped
      - Coverage SLA: every entry linted at least once per 8 weeks
    anti_pattern:
      name: "Silent Coverage Gaps"
      looks_like: "Wiki grows to 300 entries, linter processes 50 most-recently-modified, oldest 250 never linted"
      fix: "Rotating offset + coverage SLA. The offset forces the linter to progress through the full entry list rather than always starting from the top."
```

---

## Autonomous Maintenance Cycle (6.3.1)

The linter (above) runs on-demand. The maintenance cycle makes it recurring — a perceive-plan-act loop that keeps the knowledge base healthy without manual scheduling.

```yaml
maintenance_cycle:
  behavior: "Perceive current knowledge state → Plan maintenance actions → Act (consolidate, promote, flag for pruning)"
  
  runtime:
    claude_code:
      mechanism: "cron/launchd job triggering wiki linter with maintenance flags"
      cadence:
        under_50_entries: "Manual — not worth automating"
        50_to_100_entries: "Monthly"
        over_100_entries: "Weekly"
    claude_projects:
      mechanism: "User-triggered only — no background process possible"
      recommendation: "Run 'health check the knowledge base' at the start of monthly planning sessions"
      
  cost_budgeting:
    principle: "Each cycle has a token budget. Exhaust cheap checks before spending on LLM calls."
    execution_order:
      1_zero_cost: "Frontmatter validation (required fields present, types correct)"
      2_zero_cost: "Staleness window check (created date + staleness_risk → past window?)"
      3_zero_cost: "Orphan reference scan (do referenced entry IDs exist?)"
      4_zero_cost: "Rotating coverage offset advancement"
      5_llm_cost: "Semantic contradiction detection (only if budget remains)"
      6_llm_cost: "Consolidation candidate identification (only if budget remains)"
    budget_exceeded: "Log which checks were skipped. Next cycle picks up from the rotating offset."
    
  anti_pattern:
    name: "The Runaway Janitor"
    looks_like: "LLM called for every check — $3/day maintaining a 40-entry wiki"
    why_it_fails: "Maintenance cost exceeds knowledge base value. Users disable the cycle entirely."
    fix: "Heuristic-first, LLM-optional. Steps 1-4 are free. Steps 5-6 only fire when the cheap checks pass and budget remains."
```

---

## Access Logging & Salience Signals (6.3.1)

Access patterns reveal which knowledge is actually useful. Logging retrieval events enables decay-aware pruning (Module 17) and salience-informed surfacing (Module 18).

```yaml
access_logging:
  log_location: "wiki/.access_log.jsonl"
  format: "One JSON line per wiki entry retrieval"
  fields:
    entry_path: "Path to the retrieved entry"
    timestamp: "ISO datetime of retrieval"
    session_id: "Session identifier"
    mode: "Which KF mode triggered the retrieval"
    
  computed_fields:
    description: "Populated by tooling (weekly rollup job), not by humans at creation time"
    access_count: "Total retrievals across all sessions"
    last_accessed: "Most recent retrieval timestamp"
    
  rollup:
    frequency: "Weekly"
    output: "wiki/.access_summary.json — per-entry access counts and recency"
    
  composite_salience:
    description: "LRU + LFU hybrid — recency-weighted frequency"
    formula: "salience = access_count * recency_weight"
    recency_weight: "2^(-days_since_last_access / 14)"
    rationale: "A single access 2 days ago outweighs 10 accesses from 6 months ago. The 14-day half-life balances recent relevance against historical frequency."
    
  proactive_surfacing:
    top_accessed: "Surface proactively in relevant mode activations when topic matches"
    bottom_accessed: "Zero access in 60+ days AND not pinned → flag for archival review"
    
  anti_pattern:
    name: "Frequency Bias"
    looks_like: "Structural references (CLAUDE.md always loads a certain entry) inflate access scores"
    why_it_fails: "Entries that are structurally loaded appear highly salient even if no human ever queries them directly."
    fix: "Distinguish organic retrieval (mode-driven, query-matched) from structural loading (always-loaded references, index entries). Exclude structural loads from salience scoring."
    
  integration_note: "Feeds into Module 18 (Salience Allocation) as a new signal source for knowledge-level attention allocation."
```

---

## Consolidation Protocol (6.3.1)

When two entries cover semantically overlapping content, consolidation merges them without losing provenance.

```yaml
consolidation_protocol:
  trigger: "Two entries identified as semantically overlapping — by linter, by human, or by Critic during review"
  
  merge_rules:
    lossless_provenance: "Merged entry's derived_from lists both source entry slugs"
    supersession: "Merged entry's metadata includes supersedes pointing to each original"
    archival: "Original entries get status: archived — never deleted while lineage pointers exist"
    
  trigger_thresholds:
    current: "Human-initiated or Critic-flagged during linter runs"
    future: "Automatic detection deferred — requires semantic similarity tooling, practical at 100+ entries"
    
  relationship_fields:
    derived_from: "[list of source entry slugs that were merged]"
    supersedes: "[list of entry slugs this entry replaces — same fields as Module 17 temporal relationships]"
    
  anti_pattern:
    name: "Lineage Sprawl"
    looks_like: "Every minor edit creates a new derived_from edge. 400 lineage nodes for 30 concepts after 6 months."
    why_it_fails: "Lineage graph becomes unnavigable. The provenance chain that's supposed to help debugging becomes its own debugging problem."
    fix: "Lineage applies only to consolidation and archival events. Routine edits are in-place updates, not new nodes. The distinction: if you're merging or removing entries, track lineage. If you're correcting a typo or updating a version number, edit in place."
```

---

## Integration with Existing Modules

### Module 19 (Memory Architecture) — Tier 0

Knowledge Accretion adds a conceptual Tier 0 to the memory architecture:

```yaml
memory_tiers:
  tier_0:
    name: Persistent Domain Knowledge
    scope: Survives across sessions
    implementation:
      claude_code:
        project_wiki: "{project_root}/wiki/ — project-scoped knowledge (codebase decisions, stack-specific bugs, per-project patterns)"
        global_wiki: "~/.claude/wiki/ — cross-cutting knowledge (transferable patterns, framework behavior, architectural principles)"
        decision_rule: "Would this help someone on a DIFFERENT project? Yes → global; No → project (default)"
      claude_project: Project knowledge files (manually updated by user from accretion candidates)
    contents: Compiled knowledge articles, pattern catalogs, diagnostic libraries, framework references
    update_mechanism: Accretion system (Module 21)
    
  tier_1:
    name: Routing Index
    scope: Session-scoped, always loaded
    # (existing — unchanged)
    
  tier_2:
    name: Mode-Specific State
    scope: Loaded on demand per active mode
    # (existing — unchanged)
    
  tier_3:
    name: Verbatim History
    scope: Persists across sessions via MemPalace sidecar; semantic retrieval with importance-weighted decay
    # (Module 24 — updated in 6.5.0)
```

Tier 0 is what the accretion system writes to. It is the persistent layer that makes queries "add up" across sessions.

### Module 15 (Grounding Scores) — Quality Gate

Accretion candidates carry grounding scores. Low-grounding candidates require special handling.

```yaml
grounding_gate:
  threshold: 0.6
  
  above_threshold:
    action: Normal accretion — file or surface without caveat
    
  below_threshold:
    action: Surface with explicit caveat
    framing: "This [finding/pattern] has reuse value but low grounding ([score]). Recommend verification before adding to knowledge base."
    auto_file: false — always surface to user regardless of runtime
    
  rationale: Prevents speculative knowledge from polluting the base. A 0.4-grounded pattern might be correct but needs verification before it becomes part of the trusted knowledge layer.
```

### Module 20 (Permission Model) — Risk Classification

```yaml
accretion_permissions:
  base_tier: MEDIUM
  description: "Modifying persistent knowledge base has moderate consequence — correctible but costly to undo if bad knowledge propagates."
  
  domain_escalation:
    customer_facing_knowledge_bases:
      tier: HIGH
      description: "Knowledge bases that feed customer-facing products (e.g., COS evidence tiers, Science Advisor claims) require human confirmation before filing."
      examples:
        - Science Advisor evidence tier reclassification
        - COS claim validation status changes
        - ODS scoring methodology updates
      approval: human_confirm
      
  logging:
    required: true
    fields: [source_mode, novelty_type, knowledge_target, grounding_score, staleness_risk, timestamp]
    
  auto_file_rules:
    claude_code:
      MEDIUM: Auto-file with full logging
      HIGH: Surface for human confirmation, do not auto-file
    claude_project:
      all_tiers: Surface to user (no auto-filing possible)
```

### Module 17 (Temporal Knowledge) — Temporal Metadata

Every accreted entry carries temporal metadata for lifecycle management.

```yaml
accretion_temporal_metadata:
  created: [ISO datetime — when the knowledge was produced]
  source_session: redacted
  staleness_risk: [stable | slow_decay | fast_decay]
  
  staleness_windows:
    stable: null  # No automatic expiry — linter checks on extended schedule
    slow_decay: 180 days  # Re-validate every 6 months
    fast_decay: 30 days   # Re-validate monthly
    
  lifecycle_integration:
    - New accretion entries start in ACTIVE state
    - Linter flags entries past staleness window → REVIEW state
    - Human or Critic confirms validity → back to ACTIVE (with reset timer)
    - Human or Critic confirms stale → SUPERSEDED or ARCHIVED
    
  temporal_relationships:
    - Accreted entries can carry extends/revises/supersedes/contradicts relationships to existing entries
    - These relationships are populated at filing time and validated during linter passes
```

### Module 12 (Calibration Layer) — Calibrated Accretion

For high-stakes knowledge bases, accretion candidates should be calibrated before filing.

```yaml
calibrated_accretion:
  trigger: "Knowledge base accretion for production knowledge bases"
  location_in_calibration: calibration_triggers.always_calibrate
  
  protocol:
    - Run accretion assessment N times (default N=3)
    - Check: Is this genuinely novel? (novelty stable across runs?)
    - Check: Is the knowledge_target correct? (filing location stable?)
    - Check: Is the grounding score accurate? (grounding stable across runs?)
    - If all three stable → confirmed candidate
    - If any unstable → surface with caveat for human judgment
    
  rationale: A single assessment might flag routine knowledge as novel (false positive) or file to the wrong location. Multiple runs catch these errors before they reach the knowledge base.
```

### Module 14 (Metacognitive Monitor) — Over-Accretion Detection

The Monitor gains a profile for detecting accretion failure modes.

```yaml
accretion_monitoring:
  over_accretion:
    description: "Mode is flagging too many outputs as ACCRETION_CANDIDATE"
    detection: "More than 3 accretion candidates in a single standard session, or candidates with grounding below 0.5. Exception: sessions explicitly scoped as compilation or bulk-analysis passes may produce higher candidate counts without triggering this warning."
    severity: warning
    intervention: FLAG_UNCERTAINTY — "High accretion rate this session. Review candidates for genuine novelty before filing."
    
  under_accretion:
    description: "Novel knowledge is being produced but not flagged"
    detection: "Difficult to detect automatically — surfaced during linter health checks when the knowledge base has gaps that session outputs would have filled"
    severity: informational
    intervention: none (addressed through linter recommendations)
    
  accretion_drift:
    description: "Knowledge base growing in directions misaligned with its stated purpose"
    detection: "Linter health check finds entries that don't fit the knowledge base's domain scope"
    severity: medium
    intervention: FLAG_UNCERTAINTY — "Recent accretions are drifting from the knowledge base's core domain. Review filing targets."
```

### Module 07 (Critic Agent) — Linter Trigger

The Critic gains the knowledge base linter variant (detailed in the Linter section above). The key integration point: linter findings that surface contradictions are themselves accretion candidates, creating a self-correcting loop.

### Module 08 (Synthesizer Agent) — Phase 4 Accretion Check

Synthesizer's Phase 4 (Validation) gains an accretion step: after extracting patterns, evaluate whether any pattern is novel relative to the existing knowledge base. If yes, flag as `ACCRETION_CANDIDATE` with `novelty_type: new_pattern`.

---

## Examples

### Example 1: Synthesizer Pattern Accretion

```
Session: User provides 5 examples of API retry strategies across different services.
Mode: Synthesizer extracts "Exponential Backoff with Circuit Breaker" pattern.

Accretion check: Is this pattern in the existing knowledge base?
  → Searched wiki/patterns/ — no existing entry for this combination.
  → Novelty confirmed.

Candidate:
  source_mode: Synthesizer
  confidence: 0.88
  grounding_score: 0.8 (derived from 5 concrete examples)
  novelty_type: new_pattern
  knowledge_target: wiki/patterns/retry-strategies.md
  staleness_risk: stable

Claude Code: Auto-filed to wiki/patterns/retry-strategies.md. Updated index.md.
  → "Filed 'Exponential Backoff with Circuit Breaker' pattern to wiki/patterns/retry-strategies.md"

Claude Project: Surfaced compiled article to user with metadata header.
  → "This pattern has reuse value. Here's the compiled article ready to add to project knowledge:"
```

### Example 2: Critic Contradiction Detection (Linter)

```
Trigger: "Health check the knowledge base"
Mode: Critic (linter variant)

Scan: 47 entries in wiki/
Finding: wiki/architecture/api-auth.md states "JWT tokens should be short-lived (15 min)"
         wiki/patterns/session-management.md states "JWT expiry of 1 hour is standard practice"

Accretion candidate:
  source_mode: Critic (linter)
  confidence: 0.95
  grounding_score: 0.7 (both entries have grounding, but they contradict)
  novelty_type: contradiction
  knowledge_target: wiki/architecture/api-auth.md (needs resolution)
  staleness_risk: slow_decay

Output:
  CRITICAL: Contradiction between api-auth.md and session-management.md on JWT expiry.
  Recommended action: Resolve to a single standard with context-dependent guidance.
```

### Example 3: Expert Reusable Analysis

```
Session: User asks about PostgreSQL partitioning strategies for time-series data at 500M+ rows.
Mode: Expert produces deep analysis covering range partitioning, partition pruning, maintenance automation, and benchmark data.

Accretion check: Does the knowledge base have partitioning guidance at this depth?
  → wiki/databases/ has basic PostgreSQL entries but nothing on partitioning at scale.
  → Novelty confirmed — this analysis has reuse value for future database scaling questions.

Candidate:
  source_mode: Expert
  confidence: 0.82
  grounding_score: 0.6 (mix of documented behavior and inference from benchmarks)
  novelty_type: reusable_analysis
  knowledge_target: wiki/databases/postgresql-partitioning-at-scale.md
  staleness_risk: slow_decay (PostgreSQL partitioning behavior evolves across major versions)

Grounding gate: 0.6 — at threshold. Filed with note: "Benchmark data is version-specific (PG 16). Re-validate on major version upgrades."
```

---

## Anti-Patterns

### Anti-Pattern 1: Knowledge Hoarding (Over-Accretion)

**Looks like:** Every mode output gets flagged as an accretion candidate. The knowledge base grows rapidly but becomes noisy, with many low-value entries that make search and retrieval harder.

**Why it fails:** A knowledge base with 500 entries where 400 are routine observations is worse than 100 high-signal entries. Search precision degrades. Linter passes take longer. Users lose trust in the knowledge base's value.

**Failure example:** Debugger resolves a typo in a config file. The fix is flagged as `reusable_diagnostic` and filed to the wiki. Six months later, the knowledge base has hundreds of trivial fixes alongside genuinely reusable diagnostic patterns, and nobody can find the useful ones.

**Instead:** Apply the three-condition test strictly. Novelty alone isn't enough — the knowledge must also have reuse value for future queries beyond the current session AND not codify a behavior the model exhibits natively. A typo fix is novel but not reusable. A reminder to "use a clear variable name" is reusable but native.

### Anti-Pattern 2: Knowledge Amnesia (Under-Accretion)

**Looks like:** Accretion signals never fire. Valuable patterns, frameworks, and diagnostics are produced session after session but never compiled. Users re-ask the same deep questions. The knowledge base stagnates.

**Why it fails:** The system does the same deep work repeatedly. Users notice they're "training" the system from scratch each session. The compile-query-enhance loop never closes.

**Failure example:** The Strategist produces a detailed trade-off framework for build-vs-buy decisions. Three weeks later, the user faces an identical decision. The framework was consumed and forgotten. The Strategist redoes the analysis from scratch.

**Instead:** After every mode produces output at evaluative depth or higher, actively check: "Would a future query on a similar topic benefit from having this analysis pre-compiled?" If yes, flag it.

---

## Quality Checklist

Before filing any accretion candidate:

- [ ] Novelty confirmed — not a duplicate of existing knowledge base entry
- [ ] Reuse value confirmed — benefits future queries beyond current session
- [ ] Grounding score meets threshold (≥ 0.6) or caveat applied
- [ ] Temporal metadata complete (created, staleness_risk, source_session)
- [ ] Knowledge target is specific (not just "wiki/")
- [ ] Permission tier appropriate (MEDIUM base, HIGH for customer-facing)
- [ ] Article is self-contained — readable without session context
- [ ] Metadata header present (yaml frontmatter with all candidate fields)
- [ ] Taxonomy gate passed — domain, topic, and tags all from Module 23 controlled vocabulary
- [ ] Embedding computed and upserted into Tier 0 vector index (Module 22)

---

## Dispatcher Boundary (7.0.2)

Module 21 owns the **gate**: what qualifies as an accretion candidate (novelty + reuse value + grounding ≥ 0.6 + taxonomy compliance). It does not own the **dispatch**: where the candidate physically lands.

Downstream implementations may interpose a router between Module 21's gate and the destination (e.g., Tier 0 wiki, Tier 2B file store, Tier 3 archive). These routers do not relax Module 21's gate. They route candidates that have already passed the gate.

### Boundary Contract

| Concern | Module 21 | Downstream router (e.g., MemoryRouter) |
|---|---|---|
| Novelty detection | ✓ | — |
| Reuse value evaluation | ✓ | — |
| Grounding threshold (≥ 0.6) | ✓ | — |
| Taxonomy validation (Module 23) | ✓ | — |
| Candidate metadata generation | ✓ | — |
| Tier selection (T0 / T2B / T3) | — | ✓ |
| Discard of non-accretion content | — | ✓ |
| Physical write path | — | ✓ |

A downstream router that writes content directly to Tier 0 without passing through the Module 21 gate violates this contract. Surface as a Critic linter finding (severity HIGH).

A downstream router that re-applies its own novelty or grounding check on already-gated candidates is redundant but not a violation. The gate is Module 21's responsibility; downstream routers may add routing logic on top of gated output but must not substitute for the gate.

---

## Constraints

- Accretion adds metadata overhead — only fire on outputs at evaluative depth or higher
- In Claude Projects, accretion depends on user action — surfaced candidates may be ignored
- Knowledge base quality depends on linter discipline — schedule regular health checks
- Over-accretion is harder to fix than under-accretion (pruning is more work than adding)
- Grounding gate at 0.6 is a starting threshold — calibrate per knowledge base maturity
- Auto-filing in Claude Code modifies persistent state — full logging required per Module 20

---

## Success Criteria

- Knowledge base grows through use, not just through manual ingestion
- Accreted entries have genuine reuse value (measured: are accreted entries referenced in future sessions?)
- Linter health checks catch contradictions and stale entries before they cause downstream errors
- Over-accretion rate stays below 30% of total accretion candidates (measured: what percentage of accreted entries are referenced within 3 months?)
- No customer-facing knowledge base is modified without human confirmation
- Compile-query-enhance loop completes at least once per 10 substantive sessions

---

## Attribution

| Element | Source |
|---------|--------|
| Compile-query-enhance loop | Karpathy's LLM Knowledge Base pattern (April 2026) |
| Accretion signal detection by mode | Our design |
| Dual runtime (Claude Code vs. Claude Project) | Our design — adapts to deployment context |
| Knowledge base linter via Critic variant | Our design — self-correcting knowledge loop |
| Grounding-gated accretion | Our design — bridges Module 15 to persistent storage |
| Tier 0 persistent domain knowledge | Our design — extends Module 19's three-tier model |

---

## Next Steps

1. **Implement in Claude Code** → Build wiki/ directory structure and auto-filing logic
2. **Calibrate accretion thresholds** → Run 20 sessions, measure accretion rate, tune novelty detection
3. **Schedule linter cadence** → Define health check frequency per knowledge base maturity
4. **Build accretion metrics** → Track: accretion rate, reuse rate, linter yield, staleness detection rate
5. **Integrate with Science Advisor** → COS evidence tiers are a prime candidate for accretion-enhanced knowledge base

---

## Related Modules

- `07_Critic_Agent.md` — Knowledge base linter variant (health check trigger)
- `08_Synthesizer_Agent.md` — Phase 4 accretion check for novel patterns
- `09_Debugger_Agent.md` — Reusable diagnostic accretion
- `10_Strategist_Agent.md` — Transferable decision framework accretion
- `02_Builder_Agent.md` — Template candidate accretion
- `05_Expert_Agent_Example.md` — Reusable analysis accretion
- `11_Calibrator_Agent.md` — Novel configuration pattern accretion
- `12_Calibration_Layer.md` — Calibrated accretion for production knowledge bases
- `14_Metacognitive_Monitor.md` — Over-accretion detection
- `15_Grounding_Scores.md` — Grounding gate on accretion quality
- `17_Temporal_Knowledge.md` — Temporal metadata on accreted entries
- `19_Memory_Architecture.md` — Tier 0 persistent domain knowledge layer
- `20_Permission_Model.md` — Accretion permission rules (MEDIUM base, HIGH for customer-facing)
- `22_Semantic_Wiki_Search.md` — reads the Tier 0 vector index this module writes
- `23_Taxonomy_Enforcement.md` — taxonomy validation is Gate 4a of the filing protocol
- `24_Verbatim_History_Mining.md` — high-importance Tier 3 entries may be promoted to Tier 0 via this module

## CC Doc

# Module 21: Knowledge Accretion — Execution Protocol
**Apply when:** [KF-ROUTE] load list includes M21, or mode produces evaluative+ output and accretion check is needed

Detect when a mode's output contains knowledge worth persisting to the knowledge base.

## Three-Condition Test

Flag as `ACCRETION_CANDIDATE` when ALL THREE are met:
1. **Novelty:** Knowledge not already present in the existing knowledge base.
2. **Reuse value:** Would benefit future queries beyond the current session.
3. **Non-native:** The model does not already exhibit this behavior natively (v1: default false, see activation policy below).

Novelty alone is not enough. A unique observation with no transferable value is not a candidate. A reusable observation that the model already exhibits without instruction is also not a candidate (suppressed at the gate; logged to compile.md for audit).

**v1 activation policy:** `native` defaults to `false`. No mode auto-emits `native: true` at v1. The gate clause is structurally present but practically inert; auto-evaluation criteria are deferred to bead `knowledgeforge-core-och`.

## Triggers by Source Mode

| Source Mode | Novelty Type |
|-------------|--------------|
| Synthesizer | `new_pattern` |
| Critic (linter) | `contradiction` |
| Expert | `reusable_analysis` |
| Debugger | `reusable_diagnostic` |
| Strategist | `transferable_framework` |
| Builder | `template_candidate` |
| Calibrator | `template_candidate` |

## Non-Triggers

Reckonings, routine outputs applying existing knowledge, grounding < 0.6 (surface with caveat instead), session-specific context.

## Candidate Metadata

```yaml
accretion_candidate:
  grounding_score: [0.0–1.0]
  novelty_type: [see table above]
  knowledge_target: [specific wiki section]
  staleness_risk: stable | slow_decay | fast_decay
  created: [ISO date]
  activation_profile:
    trigger: invariant | path_bound | task_bound
    decidability: true | false
    miss_cost: low | medium | high
    native: true | false      # v1: always false (deferred-activation; see full schema in main body)
    path_globs: [string]      # required only when trigger == path_bound
  provenance:                 # added 7.3.0 (SPEC 4 D2)
    loop_id: string           # null when direct orchestrator
    run_id: string            # null when direct orchestrator
    decision_tag: reckoning | evaluative_judgment | predictive_judgment | novel_judgment
    source_mode: string       # moved from top-level in 7.3.0
    signals: [object]         # optional; verifier_signoff or human_review_signal entries
```

## Activation Profile

Computed at `step_2c` after the three-condition gate. Carries dispatch-time signals for downstream routers; does not affect gate eligibility (except `native`, which is gate input). Full schema in main body. Common shapes:

| Mode | Default trigger | Default decidability | Default miss_cost |
|---|---|---|---|
| Synthesizer | invariant | varies | low |
| Strategist  | invariant | varies | medium |
| Builder / Calibrator | invariant | varies | low |
| Critic linter | invariant | true | high |
| Expert | invariant (path_bound if ERA + author globs) | varies | medium |
| Debugger | path_bound if filename in body else task_bound | true | medium |

At v1, `trigger: path_bound` is sparse (<1% expected) because the entity→path resolver is deferred to bead `knowledgeforge-core-8gp`. Designs that depend on a balanced trigger distribution should wait.

## Grounding Gate

```
grounding ≥ 0.6 → Normal accretion flow
grounding < 0.6 → Surface with caveat; do not auto-file
```

## Filing Protocol Gates

**Gate 4a (Taxonomy, M23):** Before disk write, validate `domain`, `topic`, and `tags` against controlled vocabulary. On fail: reject with nearest-match suggestion. Never auto-assign. This IS a blocking gate. **Grandfather pre-check (7.1.2, bead e0x):** entries whose creation timestamp resolves to before 2026-06-10 AND have neither `domain` nor `topic` skip domain/topic validation; tags still validate. See M23 Grandfathering section.

**Gate 4b (Duplicate check, M22 Phase 1):** AFTER disk write (PostToolUse), `mempalace-wiki-mine.py` calls `tool_check_duplicate(content, threshold=0.9)` via direct Python import from `mempalace.mcp_server`. This is **detect-and-warn**, not block — the file is already on disk by the time the hook fires. On `is_duplicate=true`: emit `[Module 22] near-duplicate detected for <path>` to stderr. On MemPalace unavailable: emit `[Module 22 FALLBACK]` and proceed. The mining run proceeds regardless of the dup result.

Filing to disk is Step 5, gated only by 4a. Gate 4b runs post-write and is informational. Phase 2 (M22 v7.4+, deferred) will add a pre-write embedding gate.

**Step 2c (Activation profile assignment):** Between gate and step_3, assign `trigger / decidability / miss_cost / native` per mode lookup tables. Populate `path_globs` only when mode authors them. Partial validation only (no scope cross-cut yet).

**Step 3c (Profile cross-validation):** After step_3 scope is known, reject `trigger: path_bound + scope: global` candidates (path_globs are repo-local). Log rejection to compile.md.

**Step 3d (Provenance gate, 7.3.0 SPEC 4):** After step_3c, consume Contract B `provenance` (loop_id, run_id, decision_tag, source_mode, signals[]). Cross-cutting + novel/predictive without `verifier_signoff` or `human_review_signal` in `signals[]` → `surface_for_human_review`. Project + novel/predictive → `surface_for_human_review` regardless. Reckoning/evaluative paths proceed unchanged. Missing provenance → `surface_for_human_review` with `provenance_missing: true` (grandfather window: pre-2026-07-01 entries with top-level `source_mode` proceed with Sev 3 linter finding). User options after surfacing: `file_to_project` (with `unvetted: true`), `file_to_global_with_override` (Module 20 HIGH-tier confirmation logged), `discard`.

## Over-Accretion Warning

More than 3 candidates in a single standard session → "High accretion rate. Review for genuine novelty before filing." Exception: compilation/bulk-analysis sessions.

## CC Agent (Knowledge Librarian)

---
name: knowledge-librarian
description: |
  Spawned by the orchestrator when the accretion check identifies a candidate for the
  knowledge base. Evaluates novelty against existing wiki entries, writes accepted entries
  to the appropriate categorical directory under wiki/ (one per M23 v6.6.0 domain:
  architecture, compiler, debugging, diagnostics, infrastructure, integration, methodologies,
  migrations, orchestration, patterns, strategy — plus reserved-for-future anti-patterns,
  performance, research, security), and updates wiki/index.md.
  Do NOT invoke directly — the orchestrator spawns this after producing evaluative+ outputs that
  pass the novelty + reuse value test. (Exception: the /kf-reflect command may also spawn this
  agent for session-end accretion writes.)
model: haiku
tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
color: gray
---

Evaluate knowledge accretion candidates for novelty and file accepted entries to the wiki knowledge base.

**Reference modules:** `21_Knowledge_Accretion.md`, `15_Grounding_Scores.md`, `22_Semantic_Wiki_Search.md`, `23_Taxonomy_Enforcement.md`, `17_Temporal_Knowledge.md`

**Delegation constraint:** Do not spawn other agents. This is a single-level delegation system — the orchestrator handles all routing.

## Inputs Expected

When spawned, expect:
- The candidate content (pattern, framework, analysis, diagnostic, template)
- Candidate metadata: source_mode, novelty_type, grounding_score, staleness_risk, knowledge_target
- The original context (what session/query produced this)

## Novelty Evaluation Protocol

**Step 1: Search existing wiki entries**

Read `wiki/index.md` to get the list of existing entries. If `wiki/index.md` does not yet exist, create it with a `# Wiki Index` heading and an empty entry list — this is the bootstrap case on a fresh wiki. For relevant entries, read the full file.

In addition to the index, Glob the categorical directories directly to catch any entries that may not yet be indexed:
- `wiki/architecture/*.md`
- `wiki/compiler/*.md`
- `wiki/debugging/*.md`
- `wiki/diagnostics/*.md`
- `wiki/infrastructure/*.md`
- `wiki/integration/*.md`
- `wiki/methodologies/*.md`
- `wiki/migrations/*.md`
- `wiki/orchestration/*.md`
- `wiki/patterns/*.md`
- `wiki/strategy/*.md`

Future-reserved directories per M23 v6.6.0 (currently empty but may populate): `wiki/anti-patterns/*.md`, `wiki/performance/*.md`, `wiki/research/*.md`, `wiki/security/*.md`.

Check: Does any existing entry cover this knowledge substantially?
- Full overlap → do not file (avoid redundancy)
- Partial overlap → file with `revises` or `extends` relationship, note what's new
- No overlap → proceed to filing

**Step 2: Grounding gate**

Check the grounding_score:
- ≥ 0.6 → proceed to filing normally
- < 0.6 → surface with caveat: "This [finding/pattern] has reuse value but low grounding ([score]). Recommend verification before adding to knowledge base." Do not auto-file.

**Step 3: Taxonomy validation (Module 23 v6.6.0+)**

Before filing, validate `domain`, `topic`, and `tags` against the controlled vocabulary. Reject invalid terms and suggest nearest-match alternatives. Do not file entries with unrecognized taxonomy.

**As of M23 v6.6.0**, the controlled vocabulary includes 15 domains: `architecture`, `patterns`, `anti-patterns`, `performance`, `integration`, `research`, `strategy`, `infrastructure`, `debugging`, `security`, **`methodologies`**, **`diagnostics`**, **`orchestration`**, **`migrations`**, **`compiler`** (bolded = added in 6.6.0). Each domain has its own approved topic list — see `modules/23_taxonomy_enforcement.md` for the full vocabulary block.

**Deprecation note (6.6.0):** The `patterns/orchestration` topic is DEPRECATED — it still validates on grandfathered entries, but new entries that conceptually fit there should use the `orchestration` domain (with a specific topic like `multi-stage-issue-workflow` or `recovery`) instead.

**Grandfathering (6.6.0) — applies to NOVELTY-CHECK reads, not to new writes:**

When reading EXISTING wiki entries in Step 1 (novelty check) and Step 6 (duplicate handling), entries whose creation timestamp resolves to before 2026-06-10 (M23 v6.6.0 release) may lack `domain` and `topic` fields entirely. This is expected — they are grandfathered.

For novelty/similarity checks against grandfathered entries:
- Use the entry's directory (e.g., `wiki/methodologies/`) as a domain proxy
- Use the `tags:` field for finer-grained matching
- Do NOT discard a grandfathered entry from the similarity sweep just because `domain`/`topic` are absent

For NEW entries the librarian writes itself, `domain` and `topic` ARE required — see Entry Format below. Grandfathering applies ONLY to reading existing on-disk entries, never to writing new ones.

**Step 4: Temporal metadata**

Assign staleness windows based on staleness_risk:
- stable: no automatic expiry
- slow_decay: re-validate within 180 days
- fast_decay: re-validate within 30 days

## Entry Format

Every filed entry follows this structure:

```markdown
---
title: [Descriptive title]
source_mode: [builder | critic | expert | debugger | strategist | synthesizer | calibrator]
novelty_type: [new_pattern | contradiction | reusable_analysis | reusable_diagnostic | transferable_framework | template_candidate]
grounding_score: [0.0-1.0]
staleness_risk: [stable | slow_decay | fast_decay]
importance: [1-5]
pinned: [true | false]
created: [YYYY-MM-DD]
domain: [single value from M23 controlled vocabulary — see Step 3]
topic: [single value from the topic list under the chosen domain — see Step 3]
tags: [1-5 values from the approved tag list, comma-separated]
related_entries: [list of related wiki entries by filename]
---

# [Title]

[Self-contained body — readable without session context.
Include: core knowledge, applicability conditions, key constraints,
and concrete examples.]

## When This Applies
[Specific conditions where this knowledge is useful]

## When This Does NOT Apply
[Explicit boundaries]

## Source Context
[Brief: what query/session produced this, for provenance]
```

## Filing Protocol

**Filename:** `YYYY-MM-DD_[slug].md` where slug is kebab-case title summary.

Example: `2026-04-05_exponential-backoff-circuit-breaker-pattern.md`

**Category selection** — pick the single best-fit directory under `wiki/`. The directory MUST match the entry's `domain:` field (e.g., `domain: methodologies` → `wiki/methodologies/`). As of M23 v6.6.0, every domain in the controlled vocabulary has its own directory; the category table below is a fit guide, but the directory-domain binding is now strict for new entries.

| Category | Domain | Use for |
|----------|--------|---------|
| `architecture/` | `architecture` | High-level system structure, layering, module boundaries, deployment topology |
| `compiler/` | `compiler` | Source → derived artifact pipelines, codegen, transformation rules |
| `diagnostics/` | `diagnostics` | Symptom + root-cause patterns, failure-mode taxonomies, debugging heuristics |
| `infrastructure/` | `infrastructure` | Deployment, packaging, scheduling, env-management, cron/systemd patterns |
| `methodologies/` | `methodologies` | Process patterns, audit/review frameworks, workflow templates |
| `migrations/` | `migrations` | Schema migration patterns, backward-compat shims, rollout strategies |
| `orchestration/` | `orchestration` | Multi-agent coordination, handoff contracts, routing logic |
| `patterns/` | `patterns` | Code/design patterns, anti-patterns, recurring solution shapes |
| `strategy/` | `strategy` | Trade-off analysis, prioritization frameworks, risk-assessment patterns |
| `integration/` | `integration` | External-tool / MCP / vector-DB / LLM-API integration patterns |
| `debugging/` | `debugging` | Active debug sessions, hypothesis-testing protocols (the ACT of debugging; cf `diagnostics/` for documented residue) |

**Reserved-for-future-use directories** (in M23 vocab, not yet populated): `anti-patterns/`, `performance/`, `security/`, `research/`.

If a candidate fits multiple categories, prefer the more specific (e.g., `infrastructure/` over `patterns/` for a cron pattern). If none fit, default to `patterns/` and note the category ambiguity in the entry's `Source Context` section.

**Filing steps:**
1. Glob the categorical directories for existing entries (per the list in Step 1 above)
2. Verify novelty (read relevant existing entries)
3. Validate taxonomy (Module 23) — reject invalid domain/topic/tags
4. Select category per the table above
5. Write entry to `wiki/[category]/[filename]`
6. Update `wiki/index.md` — append entry reference under the category section:
   ```
   - [YYYY-MM-DD] [Title] — [novelty_type] — `[category]/[filename]`
   ```
   (If the index has no per-category sections yet, group by category as you add entries.)
7. Surface one-line confirmation: "Filed: wiki/[category]/[filename]"

## Duplicate Handling

If an existing entry covers the same topic:
- Higher grounding supersedes lower grounding
- Newer entry with equal grounding supersedes older entry
- When superseding: note the supersession relationship in both entries
- Log supersession in index.md

## What NOT to File

Do not file:
- Reckonings (factual lookups)
- Routine outputs applying existing knowledge
- Session-specific context (user preferences, one-off decisions)
- Outputs with grounding < 0.6 without caveat (caveat and surface, don't auto-file)
- Outputs where an existing entry already covers the same knowledge
- Entries with taxonomy terms not in the controlled vocabulary (Module 23)

## Constraints

- Each entry must be self-contained — readable without the original session context
- Do not file without checking existing entries first
- Grounding < 0.6 → surface with caveat, never auto-file
- Taxonomy validation is mandatory before filing
- Index update is mandatory after every filing
- Surface one-line confirmation to user after every filing
- Cannot modify entries created by other agents without versioning (use `revises` relationship)
