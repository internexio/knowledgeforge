# Knowledge Accretion

## Module Metadata

```yaml
module:
  title: Knowledge Accretion
  version: 7.1.3
  purpose: Cross-cutting detection-and-routing behavior that recognizes when mode outputs contain knowledge worth persisting and either auto-files it (Claude Code) or surfaces it as a compilation candidate (Claude Projects)
  topics: [knowledge-persistence, compile-query-enhance, wiki-generation, accretion-signals, knowledge-base-maintenance]
  contexts: [all-mode-execution, knowledge-management, session-outputs, persistent-storage]
  difficulty: advanced
  related: [07_Critic_Agent, 08_Synthesizer_Agent, 09_Debugger_Agent, 10_Strategist_Agent, 02_Builder_Agent, 05_Expert_Agent_Example, 11_Calibrator_Agent, 12_Calibration_Layer, 14_Metacognitive_Monitor, 15_Grounding_Scores, 17_Temporal_Knowledge, 19_Memory_Architecture, 20_Permission_Model]
  added_in: "6.2"
  changelog:
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
  source_mode: [which mode produced it]
  source_session: redacted
  confidence: [mode's output confidence at time of production]
  grounding_score: [per Module 15]
  novelty_type: [new_pattern | contradiction | reusable_analysis | reusable_diagnostic | transferable_framework | template_candidate]
  knowledge_target: [where it should be filed — wiki section, concept article, or index entry]
  staleness_risk: [stable | slow_decay | fast_decay]
  importance: [integer 1-5 — base value independent of recency, aligns with Module 17 decay model]
  importance_source: [inferred | human_set]
  created: [ISO datetime]
  
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
      #     (scope=project per step_3 classification). Global-scoped candidates
      #     with trigger==path_bound are an error; reject at step_3c.
      #   - Empty list with trigger==path_bound triggers downgrade to task_bound.
      #   - Provenance: at v1, populated only when producing mode authors explicit
      #     globs in accretion_note. Entity→path resolver deferred to follow-up
      #     bead (knowledgeforge-core-8gp). Expected distribution at v1:
      #     ~90% invariant / ~10% task_bound / <1% path_bound.
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
        - If trigger == path_bound AND scope == global → reject candidate
          reason: "path_globs are repo-specific; cannot travel with a global-scoped wiki entry"
          log_to: compile_log_format with reason "scope_glob_cross_cut"
        # Future cross-cuts (when added in subsequent revisions) attach here.

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
    1. Scan all entries in the knowledge base (wiki/ or project knowledge files)
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
  source_mode: [mode]
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

## Over-Accretion Warning

More than 3 candidates in a single standard session → "High accretion rate. Review for genuine novelty before filing." Exception: compilation/bulk-analysis sessions.
