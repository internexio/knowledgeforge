# Memory Architecture

## Module Metadata

```yaml
module:
  title: Memory Architecture
  version: 7.3.1
  purpose: Four-tier memory system — persistent domain knowledge (Tier 0), routing index (Tier 1), mode state (Tier 2), and archived history (Tier 3) — that maintains routing accuracy across long sessions and knowledge continuity across sessions
  topics: [memory, context-management, session-persistence, consolidation, skeptical-verification, persistent-knowledge, routing-audit-log, metric-aggregates]
  contexts: [long-sessions, mode-transitions, context-pressure, state-management, cross-session-knowledge, routing-decision-audit]
  difficulty: advanced
  related: [00_Orchestrator, 03_Coordination_Patterns, 04_Specification_Templates, 14_Metacognitive_Monitor, 16_Operational_Bounds, 17_Temporal_Knowledge, 20_Permission_Model, 21_Knowledge_Accretion]
  added_in: "6.1"
  implements: "Directive 2 (Three-Tier Memory Architecture), extended to four tiers in 6.2"
  changelog:
    7.3.1:
      date: 2026-07-01
      driver: knowledgeforge-core-b3g
      changes:
        - Fixed Tier 3 body: access_pattern and search_protocol search_protocol step 2 corrected — removed stale "metadata pre-filter via search_memories" claim; replaced with Phase 1 (mempalace_search wing/room scope) / Phase 2 deferred split, matching M24 6.6.0 Retrieval Protocol.
        - Fixed CC Doc Tier 3 description — removed aspirational "metadata pre-filtering" claim; added Phase 1/Phase 2 split note.
        - Note: 7.3.0 changelog entry incorrectly claimed CC Doc Tier 3 was updated in gkf — that work was deferred to b3g.
    7.3.0:
      date: 2026-07-01
      driver: knowledgeforge-core-gkf
      changes:
        - Added "cc Substrate Projections (Claude Code)" subsection — places .claude/rules/ and auto-memory in the tier model without introducing new tiers.
        - .claude/rules/ is a compiled projection of Tier 0; activation_profile.trigger governs which compilation target is used (invariant → unscoped rule, path_bound → path-gated rule, task_bound → skill). Write-time invariant stated — manual rule edits are overwritten on next compile.
        - auto-memory (~/.claude/projects/<proj>/memory/MEMORY.md) is harness-managed scratch sitting below Tier 1 — not KF-managed, not a tier. Do not accrete to it.
        - Added comparison table: four KF tiers + auto-memory with scope and managed-by columns.
        - Updated CC Doc Tier 0 description to note cc substrate projections.
        - No schema changes. schema_version unchanged.
    7.2.1:
      date: 2026-05-11
      changes:
        - Added re_routing_triggers enumeration to routing_decision_log section — canonical events that set re_routed = true (resolves F3 from kf-7.2.0 audit redo; previously this definition lived only in project agent instructions prose)
        - Three canonical triggers — navigator_activation_after_initial_routing, user_explicit_redirect, critic_adversarial_wrong_mode_finding
        - Three non-triggers documented — chain_progression, variant_selection_within_mode, critic_revision_loop
        - Cross-refs added — Module 00 (writer), Module 16 metric #10 (consumer), Module 04 trigger_disambiguator (refinement target)
        - Added variant ID composition rule to selected_variant field — `<selected_mode>.<selected_variant>` is the canonical qualified form used by Module 16 metric #10 per_variant tracking; Modules 05 and 07 variants[].id stored unqualified (resolves F7 from kf-7.2.0 audit redo; new finding surfaced on second-pass parity check)
        - No schema field changes. schema_version remains 1.0.
    7.2.0:
      date: 2026-05-10
      changes:
        - Added routing_decision_log section (schema_version 1.0) — audit trail of every routing decision, separate concern from routing_index state (resolves ERA F4 from chain-log-01-tool-calling)
        - Retention — rolling 1000 entries + permanent re-route archive at wiki/operations/routing-log/{YYYY-MM}.md
        - Added tier_2_metric_aggregates schema for weekly metric persistence beyond rolling window
        - Data source for Module 16 metric #10 (mode_selection_accuracy) — primary measurement reads live log; calibration reads aggregates after window rolls
        - Source: docs/planning/Typed_Mode_Calling/ chain-logs 01–04 (Track C)
    6.6.1: |
      - Added routing_index_schema section with field-level contract and schema version (ERA finding F6)
      - Each module's read/write fields declared in contract
      - Schema version field enables detection of cross-module misalignment
      - Drift detection rule: absent fields log to Tier 2, surface at session end
    6.5.0: |
      - Tier 3 rewritten from "grep-only" to semantic vector search via MemPalace sidecar (Module 24)
      - Tier 3 now carries recall benchmarks: 96.6% R@5 (verbatim+semantic) vs ~60% (grep)
      - Added Module 22, 23, 24 cross-references to Related Modules
    6.2.0: |
      - Added Tier 0 (persistent domain knowledge) — accretion target layer (Module 21 integration)
      - Three-tier → four-tier model
      - Updated tier overview and core approach to reflect Tier 0
```

---

## Core Approach

Long sessions degrade routing accuracy because accumulated context competes with active task state for context window space. The fix is not summarization (which loses structure) but tiered memory with a compact index that preserves routing-critical information at all times. Cross-session knowledge continuity is handled by a persistent layer (Tier 0) that survives session boundaries.

**Primary function:** Maintain accurate mode routing and decision context across 20+ turn sessions without linear context growth, and preserve valuable knowledge across sessions via persistent domain storage.

**Key insight:** An always-loaded index of ~150 characters per entry provides sufficient signal for correct routing decisions. Detailed state only needs to load when that mode is active. Persistent knowledge only needs to load when relevant to the current query.

**Design principle:** Treat accumulated context as hints, not facts. Verify before acting on any recalled state.

---

## Four Tiers

### Tier 0: Persistent Domain Knowledge (Cross-Session — 6.2)

The persistent knowledge layer survives across sessions. It is the accretion target — where compiled knowledge lives so that queries "add up" over time. Managed by Module 21 (Knowledge Accretion).

```yaml
persistent_knowledge:
  location:
    claude_code: wiki/ directory on filesystem
    claude_code_projection: ".claude/rules/*.md — compiled projection of Tier 0 entries (7.3.0). Not a separate tier — same knowledge, substrate-optimized format. See cc Substrate Projections section."
    claude_project: Project knowledge files (manually updated by user from accretion candidates)
  scope: Cross-session — persists indefinitely until archived or superseded
  
  contents:
    - Compiled knowledge articles (patterns, diagnostics, frameworks, analyses)
    - Pattern catalogs from Synthesizer
    - Reusable diagnostic libraries from Debugger
    - Decision framework templates from Strategist
    - Configuration templates from Calibrator
    
  update_mechanism: Module 21 accretion system (auto-file in Claude Code, surface to user in Claude Projects)
  
  quality_gates:
    - Grounding score ≥ 0.6 (Module 15)
    - Permission tier appropriate (MEDIUM base, HIGH for customer-facing — Module 20)
    - Temporal metadata present (Module 17)
    - Novelty confirmed (not duplicate of existing entry)
    
  access_pattern:
    - Not always loaded (unlike Tier 1)
    - Loaded when relevant to current query
    - Searched during accretion checks (is this novel?)
    - Scanned during linter health checks (Critic variant)
    
  relationship_to_tier_1:
    - Tier 1 (routing index) may reference Tier 0 entries by path
    - Tier 0 entries do not reference Tier 1 (session-scoped state is transient)
```

### Tier 1: Routing Index (Always Loaded)

The routing index stays in every prompt. It is the orchestrator's working memory — compact enough to never cause context pressure, detailed enough to route correctly.

```yaml
routing_index:
  location: Always in context (static zone of prompt)
  size_budget: ~150 characters per entry, max 30 entries (~4,500 chars total)
  
  entry_format: "[mode] [action] [outcome] [decision_type] [open/closed]"
  
  contents:
    - Modes engaged this session (with sequence)
    - Decisions made (with type classification and reversibility)
    - Active task state (objective, current step, blockers)
    - Artifacts produced (id, type, status)
    - User expertise level and stated goals
    - Open questions or deferred items
    
  example:
    ```
    SESSION INDEX (turn 14)
    user: advanced | goal: build ODS profiling pipeline
    task: ODS Module 03 spec | step: Builder active | blocker: none
    [1] Strategist: chose event-driven over polling (evaluative, reversible) ✓
    [2] Builder: Module 01 spec complete (draft, grounding 0.8) ✓
    [3] Critic: Module 01 reviewed — 2 high findings, revised ✓
    [4] Builder: Module 02 spec complete (draft, grounding 0.7) ✓
    [5] Builder: Module 03 in progress...
    open: COS bridging approach undecided (predictive, deferred to Module 07)
    ```
    
  update_rules:
    - Update after every mode completion or decision
    - Closed items compressed to single line
    - Open items retain full context
    - When entries exceed 30: consolidate oldest closed items into summary line
```

### Routing Index Schema Contract (6.6.1)

Field-level contract for all modules that read or write the routing index. Bump `schema_version` when any required field is added, renamed, or removed.

```yaml
routing_index_schema:
  schema_version: "1.0"

  required_fields:
    session_header:
      format: "SESSION INDEX (turn N)"
      fields:
        - name: user_expertise
          key: "user"
          type: string  # beginner | intermediate | advanced
          written_by: [orchestrator]
          read_by: [all modes]
        - name: primary_goal
          key: "goal"
          type: string
          written_by: [orchestrator, navigator]
          read_by: [all modes]
        - name: active_task
          key: "task"
          type: string
          written_by: [orchestrator, active mode]
          read_by: [all modes]
        - name: current_step
          key: "step"
          type: string
          written_by: [active mode]
          read_by: [orchestrator]
        - name: blocker
          key: "blocker"
          type: string | "none"
          written_by: [active mode]
          read_by: [orchestrator, navigator]

    entry_fields:
      format: "[N] [mode]: [action] ([decision_type], [reversible?]) [status]"
      fields:
        - name: sequence_number
          type: integer
          written_by: [orchestrator]
          read_by: [all modes]
        - name: mode
          type: string
          written_by: [orchestrator]
          read_by: [all modes]
        - name: action
          type: string  # free text, past tense
          written_by: [completing mode]
          read_by: [all modes]
        - name: decision_type
          type: string  # reckoning | evaluative | predictive | novel
          written_by: [completing mode]
          read_by: [orchestrator, strategist, calibrator]
        - name: reversible
          type: boolean
          written_by: [completing mode]
          read_by: [orchestrator, strategist]
        - name: status
          type: string  # ✓ | ... | ✗
          written_by: [orchestrator]
          read_by: [all modes]

    open_items:
      format: "open: [description] ([decision_type], [resolution_target])"
      written_by: [any mode that defers a decision]
      read_by: [orchestrator, navigator]

  optional_fields:
    - name: artifact_reference
      description: ID + type + grounding_score for artifacts produced this session
      written_by: [builder, expert, synthesizer, calibrator]
      read_by: [critic, strategist]

  drift_detection:
    rule: |
      If a mode reads a field that is absent from the routing index, log the gap
      to Tier 2 state and surface it at session end rather than silently defaulting.
      Field absence is a schema drift signal, not a missing data signal.
    version_check: |
      When routing index schema_version does not match a module's expected version,
      flag SCHEMA_DRIFT in Tier 2 state. Continue with best-effort field mapping
      and surface drift at session end.
```

### Routing Decision Log (NEW 7.2)

Audit trail of routing decisions, separate from the `routing_index` (which tracks state). The log is the data source for Module 16 metric #10 (`mode_selection_accuracy`). State and audit trail are kept as separate concerns: state answers "what is the current task and what modes are open?", the log answers "for each routing decision, which mode/variant was selected, by which predicate, and was it re-routed?". Resolves ERA F4 (no routing-decision logging).

```yaml
routing_decision_log:
  schema_version: "1.0"

  trigger: "On every mode activation by orchestrator (including variant selection)"

  log_entry:
    fields:
      - name: timestamp
        type: ISO8601
        required: true

      - name: turn_number
        type: integer
        required: true

      - name: request_text
        type: string
        required: true
        max_length: 200                    # Truncate; operational data, not user data

      - name: candidate_modes
        type: array<{mode_id: string, variant_id: string | null, confidence: float}>
        required: true
        min_length: 1

      - name: selected_mode
        type: string
        required: true

      - name: selected_variant
        type: string | null
        required: true                     # null if mode has no variants
        # 7.2.1: Stored UNQUALIFIED to match variants[].id in Modules 05/07
        # (e.g., "regular", "era", "linter" — not "expert.era" or "critic.linter").
        # Qualified form '<selected_mode>.<selected_variant>' is the canonical join
        # key for per-variant aggregation (Module 16 metric #10 per_variant tracking).
        # Consumers MUST compose the qualified ID at read time, not at write time.

      - name: trigger_phrase_matched
        type: string
        required: true

      - name: predicate_used
        type: string | null                # references trigger_disambiguator.predicate.type (Module 04)
        required: false

      - name: re_routed
        type: boolean
        required: true
        default: false

      - name: re_route_reason
        type: string | null
        required: false                    # required when re_routed = true
        validation:
          rule: "If re_routed is true, re_route_reason must be non-null"

  retention:
    rolling_window:
      size: 1000 entries
      eviction: oldest first

    permanent_archive:
      condition: "re_routed = true"
      destination: "wiki/operations/routing-log/{YYYY-MM}.md"
      rationale: "Re-routing events are training data for trigger_disambiguator refinement"

  re_routing_triggers:
    # Canonical events that cause an orchestrator writer to set re_routed = true.
    # Added in 7.2.1 to close audit finding F3 — definition previously lived only
    # in project agent instructions prose. Module 19 is the schema owner and must
    # enumerate the set so downstream consumers (Module 16 metric #10, linter)
    # can validate re_routed entries without cross-reading the orchestrator.
    canonical_set:
      - id: navigator_activation_after_initial_routing
        description: |
          Orchestrator initially routed to mode X, then activated Navigator to
          disambiguate. The Navigator-issued routing decision is the re_routed entry;
          re_route_reason should reference the disambiguation question.
        writer: Module 00 (project agent instructions / orchestrator)
        re_route_reason_format: "navigator_disambiguated: <question>"

      - id: user_explicit_redirect
        description: |
          User message explicitly redirects from the currently-active mode
          ("no, use Debugger instead" / "actually I want a Critic review").
          Next mode activation is the re_routed entry.
        writer: Module 00 (project agent instructions / orchestrator)
        re_route_reason_format: "user_redirect: <user_quote_truncated_80_chars>"

      - id: critic_adversarial_wrong_mode_finding
        description: |
          Critic adversarial pass surfaces a finding at Sev 2+ whose category is
          "wrong mode for this task" or "wrong variant for this task". Next mode
          activation (re-execution under corrected routing) is the re_routed entry.
        writer: Module 00 (orchestrator), triggered by Module 07 (Critic adversarial)
        re_route_reason_format: "critic_adversarial_finding: <finding_id>"
        severity_threshold: 2

    non_triggers:
      # Events that look like re-routing but are NOT re_routed = true
      - id: chain_progression
        description: "Normal mode-to-mode handoff in a planned chain (e.g., Builder → Critic auto-verify). Each activation gets its own log entry with re_routed = false."
      - id: variant_selection_within_mode
        description: "Choosing critic.linter vs critic.audit at routing time is a routing decision, not a re-route. Logged with re_routed = false."
      - id: critic_revision_loop
        description: "Critic ↔ Builder convergence loop (Module 07 loop_exit_protocol). Loop iterations are not re-routes; the final exit is."

    consumer: Module 16 metric #10 (mode_selection_accuracy) — re_routing rate is the primary measurement
    refinement_target: Module 04 trigger_disambiguator — re_routed entries are training data for predicate tightening

  aggregation_persistence:
    purpose: |
      Beyond the rolling 1000-entry log, persist aggregate metric values for
      historical calibration. Module 16 metric #10 reads aggregates here when
      raw log entries have rolled out of the window.
    location: tier_2_metric_aggregates
    schema:
      window_id: ISO8601 (week start)
      total_routing_events: integer
      re_routed_events: integer
      per_mode_accuracy: object<mode_id, float>
      per_variant_accuracy: object<{mode_id, variant_id}, float>
    retention: permanent (until manual archive)

  privacy:
    request_text:
      retention: 200 chars truncated
      pii_filtering: not applied — operational scope
      access: orchestrator + linter (Critic linter variant) only

  drift_detection:
    schema_version_check:
      rule: |
        When a module reads routing_decision_log entries with schema_version != 1.0,
        flag SCHEMA_DRIFT in Tier 2 state and surface at session end. Continue with
        best-effort field mapping.

  consumed_by:
    - Module 16 metric #10 (mode_selection_accuracy) — primary measurement
    - Critic linter variant — re-routing pattern analysis during health checks
    - Orchestrator — session-end metric calculation
```

### Tier 2: Mode-Specific State (Loaded On Demand)

Detailed working state for the currently active mode. Only one mode's state is loaded at a time. Swapped on mode transitions.

```yaml
mode_state:
  location: Dynamic zone of prompt — loaded when mode activates, unloaded when mode completes
  size_budget: No hard limit, but subject to context utilization monitoring (Module 14)
  
  contents_by_mode:
    builder:
      - In-progress specification sections
      - Design decisions pending
      - Integration points identified
      - Pattern being applied (if any)
      
    critic:
      - Artifact under review
      - Findings accumulated so far
      - Severity assessments with confidence
      - Adversarial hypotheses being tested
      
    debugger:
      - Hypothesis tree (active, eliminated, untested)
      - Evidence collected
      - Diagnostic path so far
      - Elimination reasoning
      
    strategist:
      - Options under evaluation
      - Trade-off matrix in progress
      - Criteria and weights
      - Stakeholder considerations
      
    synthesizer:
      - Examples being analyzed
      - Patterns extracted so far
      - Anti-patterns identified
      - Applicability boundaries
      
    expert:
      - First-order findings
      - Adversarial depth state (which checks completed)
      - Compound failure combinations tested
      - Assumption inversions documented
      
    calibrator:
      - Complexity assessment result
      - Interview responses collected
      - Stack decisions made
      - Compliance requirements identified

  # Metric aggregates persistence — NEW 7.2 (extends Tier 2)
  # Survives rolling-window eviction of routing_decision_log entries.
  # Source data for Module 16 metric #10 calibration over weekly windows.
  tier_2_metric_aggregates:
    purpose: |
      Per-week aggregate of routing-decision metrics, persisted beyond the
      1000-entry rolling window of routing_decision_log. Module 16 metric #10
      reads from here when raw log entries have rolled out.
    schema:
      window_id: ISO8601                   # Week start, UTC Monday
      total_routing_events: integer
      re_routed_events: integer
      per_mode_accuracy: object<mode_id, float>
      per_variant_accuracy: object<{mode_id, variant_id}, float>
      adversarial_sample_failure_rate: float | null   # Filled weekly per Module 16
      calibration_drift_flag: boolean
    retention: permanent (until manual archive)
    write_trigger: weekly aggregation pass at end of each UTC week
    writer: orchestrator (Module 00)
    consumed_by: [Module 16 metric #10 calibration, Critic linter variant]
      
  swap_protocol:
    on_mode_entry:
      1. Save current mode state to Tier 2 storage
      2. Load new mode's state (if resuming) or initialize fresh
      3. Update routing index with mode transition
    on_mode_exit:
      1. Capture mode output and key decisions
      2. Update routing index with results
      3. Mode state persists in Tier 2 for potential re-entry
```

### Tier 3: Verbatim History (Semantic Retrieval via MemPalace)

Full verbatim conversation turns stored with importance metadata. Accessed via semantic vector search; Phase 1 applies wing/room scope filter via `mempalace_search(query, wing?, room?, limit?)`; domain/topic/date_range/importance_min post-filter is Phase 2 (deferred). Not grep. Importance-weighted exponential decay governs effective availability over time. See Module 24 for full implementation spec.

```yaml
conversation_history:
  location: MemPalace sidecar (github.com/Drlordbasil/MemPalace) — persists across sessions
  access_pattern: "Semantic vector search; Phase 1 — wing/room scope via mempalace_search(query, wing?, room?, limit?); Phase 2 (deferred) — domain/topic/date_range/importance_min client-side post-filter"
  fallback: Grep-searchable when MemPalace is unavailable — log fallback; expect reduced recall
  
  recall_benchmarks:
    verbatim_semantic: "96.6% R@5 — target operating mode"
    presummarized_semantic: "84.2% R@5 — 12.4-point permanent loss from pre-compression"
    verbatim_grep: "~55–65% R@5 — phrasing-dependent fallback"
    
  when_to_search:
    - Routing index references a decision but detail is needed
    - User asks "why did we decide X" and index entry is insufficient
    - Mode state references prior output that was compressed
    - Cross-session pattern detection requires prior examples
    
  search_protocol:
    1. Extract domain/topic/tag signals and date range from current query
    2. Scope filter: mempalace_search(query, wing=<project_wing>, room=<topic_room>, limit=20) — Phase 1 only; no domain/topic/date_range/importance_min params exist at Phase 1
    3. Semantic re-rank filtered candidates
    4. Apply importance-weighted decay adjustment
    5. Return top-K verbatim turns; verify before using
    
  storage_principle: "Store verbatim. Compress at delivery if requested. Never compress before storage."
    
  never_do:
    - Re-read full conversation history wholesale
    - Summarize before storing (permanent 12.4-point recall loss)
    - Use history fragments without verification against current state
```

---

### cc Substrate Projections (Claude Code — 7.3.0)

The four-tier model is substrate-agnostic. When running as Claude Code with filesystem access, two additional on-disk artifacts participate in session memory without introducing new tiers.

#### .claude/rules/ — Tier 0 Compiled Projection

`.claude/rules/*.md` files are compiled outputs of Tier 0 wiki entries — **not a fifth tier**. A wiki entry that has been compiled to a rules file exists in both places simultaneously: the wiki entry is the authoritative Tier 0 record; the rules file is a substrate-optimized projection of the same knowledge, auto-loaded by the Claude Code harness.

The projection pathway is governed by `activation_profile.trigger` (Module 21 § Accretion Candidate Metadata):

| trigger value | Compiled to | Loading behavior |
|---|---|---|
| `invariant` | `.claude/rules/*.md` (unscoped) | Loaded every session |
| `path_bound` | `.claude/rules/kf-runtime/*.md` with `paths:` frontmatter | Auto-loaded when matching files are in context |
| `task_bound` | `.claude/skills/*.md` | Loaded on demand when mode or skill is invoked |

**Write-time invariant:** A wiki entry and its compiled rules file must stay in sync. If the wiki entry is updated without recompiling, the rules file is a stale projection. Manual edits to compiled rules files are overwritten on the next `kf-compile.py` run. The compiler is the canonical source; the rules file is the artifact.

#### auto-memory — Below-Tier-1 Scratch

`~/.claude/projects/<proj>/memory/MEMORY.md` is Claude Code's native auto-memory. It is **not a KF-managed tier** — it is a flat scratch file that the Claude Code harness maintains independently. Its lifecycle is:
- Written by: Claude Code harness (not KF modes or Module 21)
- Scope: Session-scoped scratch, may persist across sessions but is not content-addressed or decay-managed
- Position in stack: sits conceptually below Tier 1, orthogonal to the KF tier model

```yaml
# Full stack for Claude Code sessions
tier_stack:
  tier_0:
    location: "wiki/"
    scope: cross-session persistent
    managed_by: Module 21 accretion system
  tier_1:
    location: always in context
    scope: session routing index
    managed_by: orchestrator
  tier_2:
    location: mode state files, on demand
    scope: active mode working state
    managed_by: active mode
  tier_3:
    location: MemPalace sidecar
    scope: verbatim history, semantic retrieval
    managed_by: Module 24 / MemPalace
  auto_memory:
    location: "~/.claude/projects/<proj>/memory/MEMORY.md"
    scope: session scratch (flat, harness-managed)
    managed_by: Claude Code harness — NOT KF
    note: |
      Do not accrete to auto-memory — accretion targets Tier 0 (wiki/).
      Do not treat auto-memory as a source of truth — verify against
      routing index and current tool state.
```

---

## Skeptical Verification Rule

Before acting on any information from the routing index or recalled state, verify it still holds.

```yaml
skeptical_verification:
  principle: "Accumulated context is a hint, not a fact."
  
  verification_triggers:
    - About to make a decision based on a prior turn's conclusion
    - About to reference an artifact that may have been revised
    - Index entry is more than 10 turns old
    - Mode state was loaded from a previous session segment
    
  verification_actions:
    - Check: Does the current request contradict the stored state?
    - Check: Has the user corrected or updated this information?
    - Check: Is the stored decision still relevant to the current task?
    - If any check fails: flag the discrepancy and resolve before proceeding
    
  example:
    index_says: "Strategist: chose PostgreSQL (reckoning, locked)"
    user_now_says: "Actually, we're going with SQLite for the prototype"
    action: Update index, flag downstream decisions that assumed PostgreSQL, surface affected artifacts
```

---

## Consolidation Cycle

When context pressure builds or a natural breakpoint occurs, consolidate rather than summarize.

```yaml
consolidation:
  triggers:
    - Context utilization exceeds 75% (Module 14 alert threshold)
    - Mode chain completes (natural breakpoint)
    - 10+ turns since last consolidation
    - User explicitly requests session checkpoint
    
  phases:
    orient:
      action: Scan routing index for staleness markers
      output: List of entries that need attention (old, potentially outdated, superseded)
      
    gather:
      action: Identify completed items, closed decisions, and finalized artifacts
      output: Set of items eligible for compression
      
    consolidate:
      action: |
        - Merge related closed items into single summary entries
        - Convert verbose decision records into index-format entries
        - Flag contradictions between historical entries and current state
        - Promote key learnings to index (things that affect future routing)
      output: Updated routing index with reduced entry count
      
    prune:
      action: |
        - Remove entries for completed subtasks with no forward reference
        - Archive mode-specific state for completed modes
        - Cap total index at 30 entries
      output: Pruned index within size budget
      
  output_format: diff
  rule: Show what changed and why. Never silently rewrite the index.
  
  example_diff:
    ```
    CONSOLIDATION (turn 22 → turn 22)
    MERGED: [2,3,4] → "Modules 01-02 built and reviewed (approved, grounding 0.8+)"
    PRUNED: [1] Strategic context assessment (complete, no forward refs)
    KEPT: [5] Builder Module 03 in progress
    KEPT: open item — COS bridging undecided
    NET: 6 entries → 3 entries
    ```
```

---

## Context Pressure Response

When the Metacognitive Monitor (Module 14) signals context pressure, use the consolidation cycle rather than generic summarization.

```yaml
context_pressure_response:
  at_75_percent:
    action: Run consolidation cycle (orient + gather + consolidate + prune)
    target: Reduce index to essential entries, archive completed mode state
    
  at_80_percent:
    action: Aggressive consolidation — compress all closed items to single-line entries
    additionally: Unload inactive mode state from Tier 2
    
  at_85_percent:
    action: Emergency compression — retain only current mode state + routing index
    warning: "Context compressed. Decisions from turns 1-N are in index form only. Ask me to verify any specific detail before relying on it."
    
  never_do:
    - Summarize conversation as a narrative paragraph (loses structure)
    - Discard the routing index (loses routing accuracy)
    - Silently compress without flagging what was lost
```

---

## Integration Points

### With Orchestrator (Agent Instructions)

The routing index lives in the orchestrator's static prompt zone. Every routing decision reads the index first.

```yaml
orchestrator_integration:
  - Routing index is part of the static prompt zone
  - Mode selection reads index to understand session history
  - Decision classification checks index for prior decisions on same topic
  - Mode chaining reads index to determine what has already been done
```

### With Metacognitive Monitor (14_Metacognitive_Monitor)

Monitor triggers consolidation and provides context utilization data.

```yaml
monitor_integration:
  - Monitor's context_overflow thresholds trigger consolidation phases
  - Monitor tracks whether consolidation actually reduced context pressure
  - If consolidation fails to reduce pressure → ESCALATE (hand off to fresh agent)
  - Skeptical verification integrates with monitor's confidence tracking
```

### With Coordination Patterns (03_Coordination_Patterns)

Mode chains use the routing index to maintain handoff context across transitions.

```yaml
coordination_integration:
  - Handoff protocol reads from routing index for session state
  - Mode transitions update the index before swapping Tier 2 state
  - Dependency graph state persists in index, not in individual mode state
```

### With Temporal Knowledge (17_Temporal_Knowledge)

The routing index acts as a lightweight temporal record of the session.

```yaml
temporal_integration:
  - Index entries carry implicit temporal ordering (entry number = sequence)
  - Consolidation preserves temporal relationships (supersedes, extends)
  - History search (Tier 3) uses temporal knowledge query patterns
```

### With Operational Bounds (16_Operational_Bounds)

Consolidation efficiency is an operational metric.

```yaml
bounds_integration:
  - Track consolidation frequency (too frequent = tasks too large or context too small)
  - Track post-consolidation context utilization (should drop meaningfully)
  - Track routing accuracy pre/post consolidation (should not degrade)
```

---

## Constraints

- Routing index must never exceed the size budget (~4,500 chars). If it does, consolidation is mandatory.
- Only one mode's Tier 2 state is loaded at a time. Loading a second mode's state requires saving the first.
- Tier 3 (history) is never loaded in bulk. Only targeted search for specific identifiers.
- Skeptical verification adds minimal overhead during normal operation but is mandatory before acting on stale data.
- Consolidation produces a diff, not a rewrite. Silent changes to the index are forbidden.
- The index format is terse by design. Readability matters less than density and routing accuracy.

---

## Success Criteria

- After 20+ turns, the orchestrator routes correctly using only the routing index (no re-reading early turns)
- Context utilization plateaus rather than growing linearly with conversation length
- Consolidation reduces context pressure by at least 20% when triggered
- Skeptical verification catches at least one stale-state error per 50-turn session
- Mode transitions complete without losing decision history
- Emergency compression (85%) preserves enough state to continue or hand off gracefully

---

## Attribution

| Element | Source |
|---------|--------|
| Three-tier memory pattern | Claude Code source architecture (MEMORY.md + topic files + transcripts) |
| Skeptical verification rule | Claude Code "treat memory as hint, not fact" pattern |
| Consolidation cycle (Orient → Gather → Consolidate → Prune) | Claude Code autoDream system, adapted for session-scoped use |
| Size budgets (~150 chars/entry, 30 entry cap) | Claude Code MEMORY.md constraints, adapted |
| Diff-based consolidation output | Our design |
| Context pressure integration | Our design (bridges to Module 14) |

---

## Related Modules

- `Agent Instructions (orchestrator)` — Routing index lives in static prompt zone
- `03_Coordination_Patterns.md` — Mode chains use index for handoff context
- `04_Specification_Templates.md` — Context object template extended with memory tier references
- `14_Metacognitive_Monitor.md` — Context pressure triggers consolidation
- `16_Operational_Bounds.md` — Consolidation efficiency as operational metric
- `17_Temporal_Knowledge.md` — Index provides session-scoped temporal record
- `20_Permission_Model.md` — (6.1) Index updates are LOW-risk; consolidation is MEDIUM-risk (modifies session state, requires logging)
- `21_Knowledge_Accretion.md` — (6.2) Tier 0 persistent domain knowledge; accretion system writes to this layer
- `22_Semantic_Wiki_Search.md` — (6.5) Tier 0 retrieval implementation; metadata-gated semantic search over wiki/
- `23_Taxonomy_Enforcement.md` — (6.5) Controlled vocabulary shared across Tier 0 and Tier 3 entries
- `24_Verbatim_History_Mining.md` — (6.5) Tier 3 retrieval implementation; MemPalace sidecar + semantic search

## CC Doc

# Module 19: Memory Architecture — Execution Protocol
**Apply when:** [KF-ROUTE] load list includes M19, or session has extended beyond 10 turns or context pressure builds

Maintain routing accuracy across long sessions using a four-tier memory model. Treat accumulated context as hints, not facts.

## Four-Tier Model

**Tier 0 — Persistent Domain Knowledge (Cross-Session)**
Location: `wiki/` directory. Contents: compiled knowledge articles, pattern catalogs, diagnostic libraries, decision frameworks. Not always loaded — loaded when relevant. Searched during accretion checks and linter runs.

**cc substrate projection:** `.claude/rules/` files are compiled projections of Tier 0 entries — not a separate tier. `trigger: invariant` → unscoped rule (every session); `trigger: path_bound` → path-gated rule (matching files only); `trigger: task_bound` → skill (on demand). Auto-memory (`~/.claude/projects/<proj>/memory/`) is harness-managed scratch below Tier 1 — do not accrete to it.

**Tier 1 — Routing Index (Always Loaded)**
Orchestrator's working memory. Budget: ~150 chars per entry, max 30 entries (~4,500 chars total).

Format:
```
SESSION INDEX (turn N)
user: [expertise_level] | goal: [primary_goal]
task: [current_task] | step: [current_step] | blocker: [if_any]
[1] [mode]: [action] ([decision_type], [reversible?]) [status]
open: [unresolved items]
```

Update after every mode completion or decision. Closed items compressed to single line. When entries exceed 30: consolidate oldest closed items into summary.

**Tier 2 — Mode-Specific State (Loaded On Demand)**
Detailed working state for currently active mode only. One mode's state at a time. On mode exit: capture output and key decisions, update routing index.

**Tier 3 — Verbatim History (Semantic Retrieval via MemPalace)**
Full verbatim conversation turns with importance metadata. Phase 1: wing/room scope filter via `mempalace_search(query, wing?, room?, limit?)`; no domain/topic/date_range/importance_min params at Phase 1. Phase 2 (deferred): client-side post-filter on those fields. Store verbatim, retrieve semantically. 96.6% R@5 with verbatim + semantic; 84.2% with pre-summarized (12.4-point permanent loss). Never compress before storage.

## Skeptical Verification Rule

Before acting on recalled state: (1) Does current request contradict stored state? (2) Has user corrected this? (3) Is the stored decision still relevant? If any check fails → flag and resolve before proceeding.

## Consolidation Cycle

Trigger when: context > 75%, mode chain completes, or 10+ turns since last consolidation.

Four phases: Orient (scan for stale entries) → Gather (identify closed decisions) → Consolidate (merge closed items, flag contradictions) → Prune (cap at 30 entries).

Rule: Output a diff showing what changed and why. Silent index rewrites are forbidden.

## Context Pressure Response

```
75%: Run consolidation cycle
80%: Aggressive consolidation — compress all closed items to single-line
85%: Emergency compression — retain only current mode state + routing index
     Warn: "Context compressed. Decisions from turns 1-N are in index form only."
```
