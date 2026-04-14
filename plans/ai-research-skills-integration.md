# AI Research Skills → KnowledgeForge Integration Plan

**Source:** Orchestra-Research/AI-Research-SKILLs v1.5.3 | 87 SKILL.md files + JS installer
**Research date:** 2026-04-13 | **Plan version:** 1.0

---

## Strategic Value

This is a complete autonomous research orchestration system: 87 domain-expert skill files organized by numbered lifecycle stages, driven by a two-loop autoresearch orchestrator. The strategic value for KF is twofold: (1) the two-loop architecture (inner: rapid iteration, outer: reflective synthesis) maps directly to KF's Synthesizer mode gap — Synthesizer currently has no structured iteration protocol; (2) the pre-registration git protocol provides temporal proof of intent that KF Builder lacks.

The system also proves that SKILL.md files at 200-500 lines each are sufficient for expert-level procedural guidance — validating KF's mode agent architecture at a much larger scale (87 skills vs KF's 10 modes).

---

## Module Updates

### 1. Module 08 (Synthesizer) — Two-Loop Research Architecture

**What changes:** Add an inner/outer loop structure to Synthesizer for complex multi-pass pattern extraction.

**Why it works:** Synthesizer currently runs a single pass: analyze → abstract → define boundaries. For complex synthesis tasks (multi-session, multi-source), a single pass misses patterns that only emerge after iterative refinement. The autoresearch architecture provides the structure:

- **Inner loop (fast, autonomous):** Pick hypothesis → gather evidence → measure → record → next. Repeat 5-10 times.
- **Outer loop (reflective):** Review accumulated results → find patterns → update findings → decide direction (DEEPEN / BROADEN / PIVOT / CONCLUDE).

**Spec delta:**
```yaml
# Add to Synthesizer → Complex Synthesis Protocol
two_loop_synthesis:
  trigger: >
    Synthesis task involves 5+ sources, or spans multiple sessions,
    or initial single-pass synthesis produces low-confidence patterns.
  
  inner_loop:
    description: Rapid pattern extraction passes
    per_pass:
      - Select source subset or hypothesis to test
      - Extract patterns against current framework
      - Score pattern confidence (grounding × frequency × distinctiveness)
      - Record findings incrementally
    iteration_count: 5-10 passes before outer loop reflection
    output: Accumulated pattern candidates with per-pass confidence deltas

  outer_loop:
    description: Reflective synthesis and direction decision
    protocol:
      - Review all inner loop findings
      - Identify cross-pass patterns (what emerged across multiple passes?)
      - Update synthesis framework (new patterns, revised boundaries, dropped candidates)
      - Direction decision:
          DEEPEN: Strong pattern found, needs more evidence → more inner loops on same sources
          BROADEN: Pattern coverage thin → expand source set
          PIVOT: Initial framework doesn't fit evidence → revise hypothesis
          CONCLUDE: Synthesis complete → output
    
    conclude_criteria:
      - At least one pattern strongly supported (confidence > 0.8, grounding > 0.7)
      - Findings document reads as a coherent narrative, not a log
      - No critical open questions that would change the framework
      - Quality test: "A reader should be able to derive the framework's
        applicability boundaries from the findings alone."

  findings_template:
    sections:
      - Research Question
      - Current Understanding  # Updated after each outer loop
      - Key Results            # Patterns with evidence
      - Cross-Source Patterns  # What emerges across multiple passes
      - Anti-Patterns          # Existing requirement — failures and boundaries
      - Lessons and Constraints
      - Open Questions
      - Synthesis Trajectory   # Inner loop progress and inflection points

  loop_transition:
    rule: >
      No rigid boundary — judgment-driven. Typically every 5-10 inner
      loop passes, or when a pattern emerges, or when progress stalls.
    note: >
      This is deliberately not algorithmic. Premature outer loop
      wastes time synthesizing noise. Delayed outer loop misses
      emerging patterns. The agent's judgment drives the rhythm.
```

**Integration with Module 14 (Metacognitive Monitor):** The Monitor's "stuck detection" should trigger an outer loop reflection. If inner loop confidence isn't improving after 3 passes, force outer loop regardless of pass count.

**Priority:** T2 — Adapt. Estimated effort: 4 hours (spec addition + integration with Monitor).

---

### 2. Module 02 (Builder) — Pre-Registration Git Protocol

**What changes:** Require spec commits to precede implementation commits, providing temporal proof that the specification existed before the code.

**Why it works:** AI Research Skills requires protocol commits (`research(protocol): {hypothesis}`) before results commits (`research(results): {hypothesis}`). Applied to KF Builder: spec commit before implementation commit creates a verifiable record that the design wasn't reverse-engineered from the code. This is valuable for architectural review and for accretion (Module 21) — the commit order proves the spec is a genuine design document, not post-hoc documentation.

**Spec delta:**
```yaml
# Add to Builder → Output Protocol
pre_registration:
  principle: >
    Specification commits must precede implementation commits.
    The spec is a contract — it should exist before the code it describes.
  
  git_protocol:
    spec_commit_prefix: "spec({module}): {description}"
    impl_commit_prefix: "impl({module}): {description}"
    rule: >
      Builder produces spec → commit with spec() prefix →
      implementation proceeds → commit with impl() prefix.
      Temporal ordering is verifiable via git log.
  
  epistemic_tagging:
    confirmatory: >
      Implementation matches locked spec = confirmatory.
      High confidence that spec was genuinely pre-registered.
    exploratory: >
      Implementation diverges from spec = exploratory.
      Spec must be updated with deviation rationale before merge.
  
  benefit:
    - Architectural review can verify spec existed before code
    - Accretion (Module 21) can distinguish design specs from post-hoc docs
    - Deviation tracking: how often does implementation match spec?
    
  skip_conditions:
    - Rapid prototyping (exploratory phase, no spec commitment)
    - Hotfix (spec follows fix, not the other way)
    - When explicitly tagged as "no pre-registration" by user
```

**Priority:** T2 — Adapt. Estimated effort: 2 hours (spec addition + git commit convention).

---

### 3. Module 12 (Calibration Layer) — Trajectory Tracking as First-Class Object

**What changes:** Add structured experiment/calibration trajectory tracking with visualization support.

**Why it works:** AI Research Skills treats trajectory as a first-class JSON object (`run_id`, `hypothesis`, `metric_value`, `delta`, `wall_time_min`) that feeds SVG trajectory visualization. KF's Calibration Layer measures quality but doesn't track the trajectory of quality over time in a structured format. Adding trajectory tracking enables "Karpathy plots" — visual evidence of whether KF's calibration is improving, plateauing, or regressing.

**Spec delta:**
```yaml
# Add to Calibration Layer → Longitudinal Tracking
trajectory:
  format:
    entries:
      - run_id: string
        mode: string
        metric: string  # What was measured
        value: number
        delta_from_previous: number
        timestamp: ISO datetime
        wall_time_min: number  # How long the calibration took
        notes: string  # What changed since last run

  storage:
    location: .kf/calibration/trajectory.jsonl
    append_only: true
    retention: Last 100 entries (older archived)

  analysis_triggers:
    plateau: 5 consecutive entries with |delta| < 0.02 → flag to user
    regression: 3 consecutive entries with negative delta → investigate
    improvement: Positive delta sustained over 5+ entries → document what worked

  visualization:
    format: SVG line chart (metric value over time, per-mode series)
    reference: AI Research Skills "Karpathy plot" pattern
    generation: On request or after 10+ new entries since last plot
```

**Priority:** T3 — Reference. Estimated effort: 3 hours (spec + trajectory format). Implement when KF benchmarking is active.

---

### 4. Module 21 (Knowledge Accretion) — CONCLUDE as Terminal State

**What changes:** Add a "terminal state" concept to accretion — a formal declaration that a knowledge thread is complete and ready for compilation.

**Why it works:** AI Research Skills' CONCLUDE criteria ("findings.md reads like a paper backbone — a human could write the abstract from it") provides a concrete quality test for when synthesis output is ready to be accreted as a complete knowledge artifact vs. an intermediate work product. KF currently has no distinction between "this is a draft finding" and "this is a concluded analysis ready for the knowledge base."

**Spec delta:**
```yaml
# Add to Knowledge Accretion → Accretion Quality
terminal_state:
  definition: >
    A knowledge thread reaches terminal state when its accumulated
    findings constitute a complete, self-contained knowledge artifact
    that doesn't require the session context to be understood.
  
  quality_test: >
    "A reader unfamiliar with the session should be able to derive
    actionable conclusions from this artifact alone."
  
  indicators:
    - Core question answered with evidence
    - Boundaries and limitations explicit
    - Anti-patterns documented (where applicable)
    - No critical open questions that would change the conclusions
  
  accretion_behavior:
    terminal_artifact: File to Tier 0 with full metadata
    intermediate_artifact: File to Tier 2 (session state) with accretion_pending flag
    rule: >
      Only terminal artifacts accrete to Tier 0. Intermediate work products
      stay in Tier 2 until they reach terminal state or are explicitly
      promoted by the user.
```

**Priority:** T2 — Adapt. Estimated effort: 1 hour (spec addition).

---

### 5. Navigator (Module 01) — Skill Routing Table Pattern

**What changes:** Document the skill routing table concept as a reference pattern for KF's mode routing.

**Why it works:** AI Research Skills maintains a `skill-routing.md` file that maps task types to specific domain skills. This is a manually-maintained routing table — the autoresearch orchestrator consults it to decide which of 87 skills to invoke. KF's Navigator currently routes via semantic intent matching against trigger phrases. A supplementary routing table (maintained in Tier 0) could improve routing accuracy for edge cases where trigger phrases are ambiguous.

**Spec delta:**
```yaml
# Add to Navigator → Routing Augmentation
routing_table:
  location: .kf/routing_table.yaml (or wiki/routing/mode_routing.md)
  format:
    - task_pattern: "regex or keyword pattern"
      mode: target_mode
      confidence: float
      notes: "When to prefer this over semantic routing"
  
  usage:
    - Check routing table BEFORE semantic intent classification
    - If table match confidence > 0.8: use table route
    - If table match confidence < 0.8: fall through to semantic routing
    - Table is supplementary, not replacement
  
  maintenance:
    - Updated when Navigator fires (new ambiguity resolved = new table entry)
    - Reviewed during Critic linter runs
    - Accretion candidate when routing decisions reveal new patterns
```

**Priority:** T3 — Reference. Document now, implement when routing accuracy data is available.

---

## Patterns Noted but Not Adopted

| Pattern | Reason for deferral |
|---------|-------------------|
| 87 domain-specific SKILL.md files | Validates the approach but KF's 10 modes are at a different abstraction level |
| `/loop 20m` + OpenClaw cron dual continuity | Session continuity mechanisms. Relevant for autonomous deployment, not current interactive use. |
| `src/` discipline (move reusable code out of experiments) | Good practice but not a framework concern — it's a development discipline |
| Paper as terminal state (LaTeX output) | KF's outputs are specs, analyses, and diagnostics — not papers |
| Interactive npm installer with agent framework detection | Distribution mechanism. Not relevant to KF's deployment model. |

---

## Implementation Sequence

```
1. Two-loop synthesis architecture (Module 08)  ← highest value, fills Synthesizer gap
2. Terminal state concept (Module 21)           ← enables quality gate for accretion
3. Pre-registration git protocol (Module 02)    ← development discipline
4. Trajectory tracking (Module 12)              ← reference architecture for benchmarking
5. Routing table augmentation (Module 01)       ← reference, implement with data
```

---

## Cross-Reference with Other Plans

The two-loop architecture (item 1) benefits from:
- **Orchestra plan:** PreCompact hooks preserve synthesis state across compaction
- **Hooks-mastery plan:** Stop hook enforces CONCLUDE criteria before allowing session end
- **Agent Orchestrator plan:** Reaction engine triggers outer loop when inner loop stalls

---

## Version Target

Two-loop synthesis architecture is a significant addition to Module 08. Combined with terminal state concept for Module 21, these warrant inclusion in **KF 6.7.0** or could be held for **6.8.0** if the hooks infrastructure (6.7.0) is prioritized first.
