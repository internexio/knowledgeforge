# KnowledgeForge 7.2 Quick Reference

## Module Metadata

```yaml
module:
  title: KnowledgeForge 7.2 Quick Reference
  version: 7.3.0
  purpose: Quick lookup for all patterns, checklists, mode triggers, integration flows, and core concepts across the full KF 7.2 framework
  topics: [quick-reference, cheatsheet, mode-selection, integration-flows, checklists, anti-patterns, variant-taxonomy, routing-audit-log]
  contexts: [all-interactions, lookup, orientation]
  difficulty: foundational
  related: [Agent_Instructions (orchestrator), 01_Navigator_Agent, 02_Builder_Agent, 03_Coordination_Patterns, 04_Specification_Templates, 05_Expert_Agent_Example, 07_Critic_Agent, 08_Synthesizer_Agent, 09_Debugger_Agent, 10_Strategist_Agent, 11_Calibrator_Agent, 12_Calibration_Layer, 13_Decision_Classification, 14_Metacognitive_Monitor, 15_Grounding_Scores, 16_Operational_Bounds, 17_Temporal_Knowledge, 18_Salience_Allocation, 19_Memory_Architecture, 20_Permission_Model, 21_Knowledge_Accretion, 22_Semantic_Wiki_Search, 23_Taxonomy_Enforcement, 24_Verbatim_History_Mining, 25_Entity_Relationship_Analysis]
  changelog:
    7.3.0:
      date: 2026-05-24
      driver: knowledgeforge-core-8xq
      changes:
        - Four locations updated for M22 / M25 Phase 1 reality (initial pass missed three; caught by third critic pass):
          * Infrastructure Modules table (line 192) — M22 row: "metadata-gated semantic search" → Phase 1 dup-check gate; Phase 2 deferred
          * Infrastructure Modules table (line 205) — M25 row: entity-scoped filters qualified — Tier 0 (M22) Phase 2 Deferred, Tier 3 (M24) active
          * Module Reference Table — M22 row (line 604) and M25 row (line 607) qualified
          * Integration Graph (line 708) — M25 ↔ 22 marked Phase 2 Deferred
    7.2.0:
      date: 2026-05-11
      changes:
        - Resolved F1 from kf-7.2.0 audit redo — content updated from 6.6.1 to 7.2.0 baseline
        - Title and version bumped to 7.2; meta-principle, identity, and framework refs updated
        - Added Mode Variants section — Critic (regular/linter/audit/adversarial) and Expert (regular/infrastructure/ml_infrastructure/era) variant taxonomy formalized per 05/07 v7.2.0
        - Agent Modes table — variant rows added under Critic and Expert
        - KF-4 Operational Bounds table — added metric #10 (mode_selection_accuracy) row with thresholds
        - KF-8 Memory Architecture — added routing_decision_log subsection (schema v1.0) + variant ID composition rule (F7)
        - Added Handoff Contract Registry section — 8 registered handoffs from Module 03
        - Added Trigger Disambiguator section — Module 04 template purpose and assertion forms
        - Module Reference Table — added 22, 23, 24, 25 (previously missing); annotated 03, 04, 05, 07, 16, 19 with 7.2 additions
        - Related list — added 25_Entity_Relationship_Analysis (previously missing)
        - Quality Checklist — added routing_decision_log write item
        - Module 25 moved from "New in 6.5" section to "New in 6.6" (correct provenance)
        - Source — kf-7.2.0 audit redo (F1, F7)
    7.0.0: |
      - Carried forward 7.0.x downstream module updates (deterministic-first meta-principle, accretion two-tier filing, Module 25 standalone)
    6.6.1: |
      - ERA-driven fixes: Navigator output-type predicate, loop_exit_protocol, handoff contracts
    6.6.0: |
      - Added Expert (ERA) row to Agent Modes table
      - Added Infrastructure Modules (New in 6.6) table entry for ERA
      - Updated Module 21 reference to include ERA as example use case
      - Added ERA flows to Integration Flows and Mode Combinations
      - Bumped title and version to 6.6
    6.5.0: |
      - Version alignment with KF 6.5
      - Added modules 22, 23, 24 to related list
    6.4.0: |
      - Added Architectural Identity section with neuro-symbolic validation (Duggan et al., ICRA 2026)
    6.3.1: |
      - Added 6.3.1 content to KF-6 (decay formula, domain half-life table, pinning) and KF-7 (access-driven salience)
      - Bumped version to 6.3.1
    6.3.0: |
      - Added Expert (infra) mode row to Agent Modes table
      - Added infrastructure chain patterns to Mode Combinations
      - Added infrastructure planning flows to Integration Flows
      - Updated version references to 6.3
    6.2.0: |
      - Added Module 21 (Knowledge Accretion) to all reference tables
      - Added KF-10 shorthand mapping
      - Updated integration flows for accretion
      - Updated cross-linking matrix for Module 21
    6.1.0: |
      - Added Memory Architecture quick reference (Module 19)
      - Added Permission Model quick reference (Module 20)
      - Added anti-patterns section (D9)
      - Updated integration flows for auto-verification and memory
      - Updated cross-linking matrix for modules 19-20
      - Updated module reference table
```

---

## The Core Pattern

```
UNDERSTAND → REASON → SPECIFY → NAVIGATE
```

Every interaction. No exceptions.

---

## The Meta-Principle

**Reasoning:** KF modes patch Sonnet's weaknesses, not scaffold its strengths.

**Execution:** Deterministic first. Before invoking LLM judgment, exhaust deterministic checks. Before fixing, reproduce. Before acting, triage.

Modes that win (Debugger, Strategist, Critic) impose constraints that *prevent* failure modes. Every mode and module must pass this test: does this add value Sonnet doesn't already provide?

---

## Architectural Identity

KnowledgeForge is a **neuro-symbolic architecture**: symbolic orchestration (decision classification, mode triggers, chain patterns, quality gates) routing to neural execution (Claude reasoning within activated modes).

This is empirically validated. Duggan et al. (ICRA 2026) tested neuro-symbolic vs. end-to-end on structured long-horizon tasks:
- **~3× success rate** improvement over end-to-end
- **~100× training energy efficiency**
- **Generalizes to unseen task variants** where pure neural models fail completely

**Three findings that map directly to KF design decisions:**

| Paper Finding | KF Equivalent |
|---------------|---------------|
| Composable structure > more data. 50 structured demos beat 300 full-trajectory demos. | Pareto reduction, mode chaining as compositional planning |
| Structure on natively-handled tasks *degrades* performance | Pass-through optimization, the meta-principle |
| Execution fidelity > planning correctness | Infrastructure modules (M12, M14, M15) as execution quality gates |

**Citation:** Duggan et al., "The Price Is Not Right," ICRA 2026. Tufts HRI Lab.

---

## Agent Modes

| Mode | Variant | Trigger | Action | Key Additions |
|------|---------|---------|--------|---------------|
| **Navigator** | — | Genuinely ambiguous intent only (output-type predicate) | Disambiguate → Route | Fires only on ambiguity; clear intents bypass (6.6.1) |
| **Builder** | — | "Create an agent for..." | PDIA method → Complete spec → System prompt | Decision type tags per design choice |
| **Coordinator** | — | Multi-agent task | Map dependencies → Derive pattern from graph | Dependency-first; patterns are vocabulary |
| **Expert** | regular | Domain-specific question | First-order + Adversarial depth analysis | compound failures, blast radius, assumption inversion |
| **Expert** | infrastructure | "Design infrastructure", "Plan deployment", "Architecture topology" | Adversarial depth on architecture → Architecture spec | Infra domain adaptation (6.3) |
| **Expert** | ml_infrastructure | "Size hardware", "GPU planning", "Model deployment" | Model→hardware mapping with adversarial depth | ML infra domain adaptation (6.3) |
| **Expert** | era | "Map entity relationships", "Audit module dependencies", "Model agent contracts" | Entity graph analysis → ERA Specification Template | ERA domain adaptation (6.6); structured graph output |
| **Critic** | regular | "Review this spec", "Find gaps" | 4-step review → Severity-ranked findings | Calibrated severity with confidence intervals |
| **Critic** | linter | "Health check the knowledge base", "Lint wiki" | Staleness + contradiction + redundancy + grounding decay scan | Maintenance backlog ranked by impact (6.2) |
| **Critic** | audit | "Hosting audit", "Infrastructure inventory", "Decomposition readiness" | Inventory → topology → SPOF → readiness ratings | Hosting Audit template (6.3) |
| **Critic** | adversarial | Auto-fires after Builder / Strategist / 3+ mode chains / Expert with `decision_type_exercised: evaluative+` | "Find the failure mode the producer missed" | Auto-verification (6.1); gate uses decision_type_exercised (6.6.1) |
| **Synthesizer** | — | "Extract patterns", "Find commonalities" | Analyze → Abstract → Create framework | Mandatory anti-patterns, temporal context |
| **Debugger** | — | "This isn't working", "Why is X failing" | Hypothesize → Test → Isolate root cause | Monitor-assisted diagnosis, temporal trace |
| **Strategist** | — | "What should I build next?", "Prioritize" | Evaluate → Trade-off analysis → Recommend | Decision type routing, calibrated rankings |
| **Calibrator** | — | "Setup CLAUDE.md", "Configure AI" | Assess complexity → Interview → Generate config | Complexity tiers, compliance templates |

**Variant disambiguation:** Mode-selection accuracy metric (KF-4 metric #10) tracks per-variant routing correctness. Aggregate "Critic accuracy" is meaningless when the label spans 4 output formats.

---

## Mode Variants (7.2)

Formalized in 7.2 via `variants[]` field on Expert (Module 05) and Critic (Module 07) agent specs. Each variant declares its own `trigger_phrases`, `output_format`, `output_template`, `typical_chain_position`, `decision_type_typical`, and `risk_tier`.

**Critic variants:**

| Variant ID (in 07) | Qualified Form (in 16) | Trigger | Output Format | Typical Chain Position |
|--------------------|-----------------------|---------|---------------|------------------------|
| `regular` | `critic.regular` | Direct review request | Severity-ranked findings | Standalone or chain tail |
| `linter` | `critic.linter` | Knowledge base health | Maintenance backlog | Standalone (periodic) |
| `audit` | `critic.audit` | Infrastructure inventory | Hosting Audit template | Audit chain head |
| `adversarial` | `critic.adversarial` | Auto-fires (no direct trigger) | Sev 2+ findings only | Chain tail (auto-verification) |

**Expert variants:**

| Variant ID (in 05) | Qualified Form (in 16) | Trigger | Output Format | Typical Chain Position |
|--------------------|-----------------------|---------|---------------|------------------------|
| `regular` | `expert.regular` | Domain-specific question | First-order + adversarial depth | Standalone or chain head |
| `infrastructure` | `expert.infrastructure` | Architecture / topology design | Architecture spec input | Chain head (→ Builder) |
| `ml_infrastructure` | `expert.ml_infrastructure` | Hardware / model sizing | Deployment spec input | Chain head (→ Strategist → Builder) |
| `era` | `expert.era` | Entity relationship mapping | ERA spec input | Chain head (→ Builder) |

**Variant ID composition rule (7.2.1):** Modules 05 and 07 declare variants with **unqualified** IDs (`regular`, `era`, etc.). Module 19 `routing_decision_log` stores `selected_mode` and `selected_variant` as separate string fields, both unqualified. The **qualified form** `<selected_mode>.<selected_variant>` (e.g., `critic.linter`) is the canonical join key for per-variant aggregation in Module 16 metric #10. Consumers MUST compose the qualified ID at read time, never at write time. See Module 19 `routing_decision_log.log_entry.fields.selected_variant`.

**Per-variant routing accuracy threshold:** >= 95% (KF-4 metric #10). Below 85% → halt the variant and audit `trigger_disambiguator` (Module 04).

---

## Infrastructure Modules (New in 6.0)

| Module | Purpose | Key Concept |
|--------|---------|-------------|
| **12 Calibration Layer** | Multi-run evaluation stability + bias detection | "8.2 ± 0.4 across 5 runs, no position bias" |
| **13 Decision Classification** | Route decisions to appropriate reasoning depth | Reckoning → Evaluative → Predictive → Novel |
| **14 Metacognitive Monitor** | Detect agent failure before bad output | Circular reasoning, context overflow, confidence collapse |
| **15 Grounding Scores** | Trust levels (0.0–1.0) per knowledge entry | conclusion = min(premises) × inference_confidence |
| **16 Operational Bounds** | Keep metrics within healthy ranges | Acute failures (Monitor) + chronic drift (Bounds) |
| **17 Temporal Knowledge** | Versioned knowledge with lifecycle management | extends / revises / supersedes / contradicts |
| **18 Salience Allocation** | Dynamic resource allocation by goal relevance | salience = goal_relevance × urgency × grounding_quality |

## Infrastructure Modules (New in 6.1)

| Module | Purpose | Key Concept |
|--------|---------|-------------|
| **19 Memory Architecture** | Four-tier memory (extended 6.2) | Tier 0 wiki + routing index + mode state + history |
| **20 Permission Model** | Risk tiers + capability restrictions for sub-agents | LOW (auto) / MEDIUM (auto+log) / HIGH (human confirm) |

## Infrastructure Modules (New in 6.2)

| Module | Purpose | Key Concept |
|--------|---------|-------------|
| **21 Knowledge Accretion** | Compile-query-enhance loop for persistent knowledge | Accretion signal → file to Tier 0 or surface to user |

## Infrastructure Modules (New in 6.5)

| Module | Purpose | Key Concept |
|--------|---------|-------------|
| **22 Semantic Wiki Search** | Tier 0 retrieval via MemPalace (Phase 1: dup-check gate; Phase 2 deferred: metadata-gated retrieval) | Phase 1: `tool_check_duplicate` via direct Python import, detect-and-warn. Phase 2 (acu): domain/topic/tag pre-filter + score fusion, workload-triggered |
| **23 Taxonomy Enforcement** | Controlled vocabulary shared across Tier 0 and Tier 3 | Fixed domain/topic/tag vocabulary validated at write time |
| **24 Verbatim History Mining** | Tier 3 retrieval via verbatim storage + semantic search | Verbatim + semantic = 96.6% R@5; pre-summarized = 84.2% |

## Infrastructure Modules (New in 6.6)

| Module | Purpose | Key Concept |
|--------|---------|-------------|
| **25 Entity Relationship Analysis** | Post-routing, pre-execution entity extraction + relationship mapping | Graph shape → routing escalation. Entity-scoped memory filters: Tier 3 (M24) active; Tier 0 (M22) is Phase 2 Deferred per M25 v7.0.3 |
| **ERA domain (Module 05)** | Expert variant — adversarial depth applied to entity graphs, module dependencies, agent contracts | Implicit entity detection + cardinality violation + handoff contract auditing; produces ERA Specification Template (Module 04) |

## KF-N Shorthand → Module Mapping

Throughout KF documentation, infrastructure modules are referenced by shorthand (KF-1 through KF-10). This is the canonical mapping:

| Shorthand | Module | Name |
|-----------|--------|------|
| KF-1 | 12_Calibration_Layer | Calibration Layer |
| KF-2 | 14_Metacognitive_Monitor | Metacognitive Monitor |
| KF-3 | 15_Grounding_Scores | Grounding Scores |
| KF-4 | 16_Operational_Bounds | Operational Bounds |
| KF-5 | 13_Decision_Classification | Decision Classification |
| KF-6 | 17_Temporal_Knowledge | Temporal Knowledge |
| KF-7 | 18_Salience_Allocation | Salience Allocation |
| KF-8 | 19_Memory_Architecture | Memory Architecture (6.1) |
| KF-9 | 20_Permission_Model | Permission Model (6.1) |
| KF-10 | 21_Knowledge_Accretion | Knowledge Accretion (6.2) |

---

## Decision Types (KF-5)

```
Question 1: Does this have a verifiable correct answer?
  YES → RECKONING (lookup, minimal tokens)
  NO  → Question 2

Question 2: Is there historical data or established criteria?
  YES → Current state? → EVALUATIVE JUDGMENT
        Future state?  → PREDICTIVE JUDGMENT
  NO  → NOVEL JUDGMENT (flag for human, expanded reasoning)
```

**Ozymandias Test:** If a yes/no question requires multi-paragraph reasoning, it's not a reckoning.

---

## Response Patterns

**Information:** Answer → Context (if needed) → Next steps

**Creation:** Acknowledge → Generate → Usage guide → What's next

**Problem:** Diagnose → Solution → Steps → Prevention

**Specification:** Complete enough to implement without questions. Each design decision tagged with decision type.

**Quality Assurance:** Challenge → Document gaps → Recommend fixes. Severity calibrated with confidence intervals.

**Pattern Extraction:** Analyze examples → Abstract pattern → Define applicability. Mandatory anti-pattern per pattern.

**Diagnosis:** Generate hypotheses → Test systematically → Identify root cause. Monitor-assisted stuck detection.

**Strategic Decision:** Classify decision type → Analyze options → Explicit trade-offs → Recommend with calibrated confidence.

---

## Coordination: Dependency-First

```
1. List all subtasks
2. Map hard dependencies (A's output feeds B)
3. Map soft dependencies (A's output improves B)
4. Draw the dependency graph
5. Identify parallel clusters (no hard deps between them)
6. Identify sequential chains (hard dep chains)
7. Identify coordination points (multiple inputs converge)
8. The pattern is whatever the graph says it is
```

**Patterns are vocabulary, not a selection menu:**
- **Sequential** emerges from single-chain dependencies
- **Parallel** emerges from independent clusters
- **Hierarchical** emerges from complex dynamic workflows
- **Consensus** emerges from iterative reconciliation needs
- **Hybrid** emerges from most real workflows

---

## Expert: Adversarial Depth Protocol

After first-pass analysis, run four checks:

1. **Compound Failures** — What attack chains combine individual findings?
2. **Blast Radius** — If this single issue triggers, what cascades?
3. **Assumption Inversion** — What would need to be true for my assessment to be wrong?
4. **Design Implications** — What do findings reveal about the system's design philosophy?

`decision_type_exercised` output field is REQUIRED (6.6.1). Auto-verify gate reads this, not incoming request classification.

---

## Calibration Layer (KF-1)

**When to calibrate:**
- Always: Production specs, irreversible decisions, benchmarks
- On request: Standard reviews, moderate-stakes evaluations
- Skip: Quick feedback, low-stakes, reckonings

**Bias taxonomy:** Position, knowledge, format (literature) + verbosity, label, cultural (our additions).
**Key distinction:** Calibratable bias (adjust score) vs. structural bias (discard evaluation).

---

## Metacognitive Monitor (KF-2)

**Six checks (6.6):** Circular reasoning (state hashing), context overflow (utilization tracking), confidence degradation (rolling average), user-side health (repetition/escalation/correction detection), skeptical verification (stale state detection), vision principle drift (Builder/Strategist output vs `wiki/vision.md` principles — once per session per principle, never blocks)

**Five interventions:**
```
CONTINUE → FLAG_UNCERTAINTY → COMPRESS_CONTEXT → SWITCH_STRATEGY → ASK_CLARIFICATION → ESCALATE
```

**Strategy ladder:** DIRECT_ANSWER → DECOMPOSE → SEARCH → VERIFY → ESCALATE

**Stuck = 3 strategy switches without improvement, or same loop twice in 10 steps.**

**ESCALATE means actual escalation** — Orchestra inbox, human, or different agent. Not "try harder."

---

## Grounding Scores (KF-3)

```
1.0  Directly observed (API response, file read)
0.8  Computed from grounded data (deterministic transform)
0.6  High-confidence inference from grounded observations
0.4  Linguistic inference with partial verification
0.2  LLM output with some support
0.1  Pure LLM output, no verification
```

**Propagation:** conclusion = min(premise groundings) × inference confidence
**Decay:** Unverified knowledge decays toward 0.5 over time. Rate varies by domain.

---

## Operational Bounds (KF-4)

| Metric | Healthy Range | Out-of-Bounds Action |
|--------|---------------|---------------------|
| Context utilization | 40%–80% | Compress / hand off to fresh agent |
| Error rate (rolling 10) | < 15% | Switch to verification mode |
| Confidence calibration | ±10% drift | Flag for review / adjust floor |
| API cost per hour | Within budget | Queue non-urgent / pause non-critical |
| Cache hit rate *(6.1)* | ≥ 80% | Audit prompt changes / verify static-dynamic boundary |
| Circuit breaker *(6.1)* | < 3 consecutive failures | Halt mode / surface diagnostics |
| Transition cost *(6.1)* | < 15% chain cost | Review chain design / inline handling |
| Consolidation *(6.1)* | ≥ 20% reduction | Close completed work / check Tier 2 retention |
| Token cost per mode *(6.4)* | ≤ 40% of chain budget | Audit which mode dominates; verify it's pulling its weight |
| **Mode selection accuracy** *(7.2)* | **Overall ≥ 90%; per-variant ≥ 95%** | **<90 → trigger Module 13 review; <80 → ESCALATE halt; per-variant <95 → audit trigger overlap; <85 → halt variant + Module 04 review** |

**Two-layer safety:** Monitor catches acute failures. Bounds catches chronic drift.

**Mode selection accuracy (metric #10 detail):**
- Primary measurement — re-routing rate from Module 19 `routing_decision_log` (deterministic, every chain completion)
- Calibration — weekly adversarial sampling pass (offline; 5pp drift threshold)
- Tracked per-variant across 8 variants: 4 Critic + 4 Expert
- Aggregate "Critic" or "Expert" accuracy is meaningless without disaggregation
- Join key is qualified `<mode>.<variant>` — composed at read time from Module 19's separate `selected_mode` and `selected_variant` fields (7.2.1)

---

## Temporal Knowledge (KF-6)

**Four relationships:** extends, revises, supersedes, contradicts

**Lifecycle:** acquired → active → consolidated → (reinforced | decayed | superseded | archived)

**Three queries:**
- **Temporal:** "What did I know about X as of date Y?"
- **Diff:** "What changed about X between A and B?"
- **Hygiene:** "What's superseded but not cleaned up?"

**Decay model (6.3.1):**
```
effective_importance = importance × 2^(-days_since_access / half_life_days)
```
- `importance`: 1–5 scale set at creation; scales the decay rate
- `pinned: true` exempts entry from all staleness pressure
- Entries below 0.2 effective importance flagged for archival

**Domain half-life table (6.3.1):**

| Domain | Half-life | Notes |
|--------|-----------|-------|
| Code snippets / API patterns | 30 days | Fast-moving; break quickly |
| Campaign observations | 30 days | Campaign-specific |
| AI/ML techniques | 60 days | Field moves quarterly |
| Audience insights | 90 days | Behavioral data shifts |
| Architecture / integration patterns | 365 days | Outlast implementations |
| Mathematical / algorithmic patterns | Pinned | Timeless |

**Planning artifact staleness (7.0.2):** `vision.md` half_life 60d, `roadmap.md` half_life 30d. Advisory-only — never blocks execution.

---

## Salience Allocation (KF-7)

```
salience = goal_relevance × urgency × grounding_quality
```

- Competitive inhibition: highest salience wins resource contention
- Starvation prevention: minimum 5% allocation floor for all queued tasks
- Aging boost: waiting tasks gain salience over time
- Feedback loop: track if high-salience tasks produce high-value output
- **Access-driven signal (6.3.1):** wiki access logs (LRU+LFU from Module 21) feed salience scoring — frequently-retrieved knowledge weighted higher

---

## Memory Architecture (KF-8, 6.1 — extended 6.2, 7.2)

**Four tiers:**
- **Tier 0 — Persistent Knowledge:** Survives across sessions. `wiki/` directory (Claude Code) or project knowledge files (Claude Projects). Written by Knowledge Accretion (Module 21). Two-tier filing (7.0.3): `{project_root}/wiki/` for project-scoped, `~/.claude/wiki/` for cross-cutting.
- **Tier 1 — Routing Index:** Always in context. ~150 chars/entry, max 30 entries. Modes engaged, decisions made, task state. Schema versioned (6.6.1, schema_version "1.0").
- **Tier 2 — Mode State:** Loaded on demand. One mode's state at a time. Swapped on transitions. Also stores `tier_2_metric_aggregates` for weekly metric persistence (7.2).
- **Tier 3 — History:** Verbatim storage + semantic search via MemPalace sidecar (6.5). 96.6% R@5.

**Skeptical verification:** Treat accumulated context as hints, not facts. Verify before acting on stale data.

**Consolidation:** Orient → Gather → Consolidate → Prune. Output is a diff, not a rewrite.

**Context pressure response:** At 75% → consolidate. At 80% → aggressive consolidation. At 85% → emergency compression with warning.

### Routing Decision Log (7.2, schema v1.0)

Audit trail of routing decisions — separate concern from routing_index state.

**Trigger:** On every mode activation by orchestrator (including variant selection).

**Required fields:** `timestamp`, `turn_number`, `request_text` (≤200 chars), `candidate_modes`, `selected_mode`, `selected_variant`, `trigger_phrase_matched`, `predicate_used` (optional), `re_routed`, `re_route_reason` (required when `re_routed = true`).

**Variant ID storage (7.2.1):** `selected_mode` and `selected_variant` stored as separate string fields, both unqualified. Match `variants[].id` in Modules 05/07 directly. Qualified form `<selected_mode>.<selected_variant>` (e.g., `expert.era`) is the canonical join key for Module 16 metric #10 — composed at read time, never at write time.

**Retention:**
- Rolling window — 1000 entries, oldest-first eviction
- Permanent archive — `re_routed = true` entries persist at `wiki/operations/routing-log/{YYYY-MM}.md`
- Weekly aggregation — written to `tier_2_metric_aggregates` for historical calibration

**Canonical re_routing triggers (7.2.1):**
1. `navigator_activation_after_initial_routing` — orchestrator routed, then Navigator disambiguated
2. `user_explicit_redirect` — user message overrides current mode ("use Debugger instead")
3. `critic_adversarial_wrong_mode_finding` — adversarial pass surfaces Sev 2+ "wrong mode/variant for this task" finding

**Non-triggers:** chain progression (Builder → Critic auto-verify), variant selection at routing time, Critic ↔ Builder convergence loop iterations.

**Consumer:** KF-4 metric #10 (mode_selection_accuracy) primary measurement.

---

## Permission Model (KF-9, 6.1)

| Tier | Actions | Approval |
|------|---------|----------|
| **LOW** | Reckonings, routing, formatting, index updates | Auto |
| **MEDIUM** | Evaluative judgments, 2-mode chains, artifact drafts, profile updates | Auto + logging |
| **HIGH** | Novel judgments, 3+ mode chains, ODS→COS bridging, irreversible recommendations | Human confirm |

**Risk escalation:** Chain length ≥ 3 → minimum MEDIUM. Low confidence → tier +1. Adversarial finding → HIGH.

**Capability profiles:** Each mode has read/write/escalate boundaries when operating as sub-agent. No sub-agent can modify another's output.

**Circuit breakers:** 3 consecutive failures → halt. 2 chain failures at same step → abort chain. Critic ↔ Builder revision loop is EXEMPT (Module 07 loop_exit_protocol).

---

## Automatic Adversarial Verification (6.1)

**Fires on:** Builder output in chains, Strategist recommendations, ODS profiles, any 3+ mode chain, Expert output with `decision_type_exercised` ≥ evaluative_judgment (6.6.1).

**Framing:** "Assume the output has at least one significant flaw. Find what the producing agent missed."

**Output:** Severity 2+ findings only. Clean pass or risk escalation.

**Yield tracking:** Healthy range 20%–80%. Below 20% = too soft. Above 80% = rebuild, don't patch.

---

## Handoff Contract Registry (7.2)

Eight active mode-to-mode handoffs registered in Module 03 using the Module 04 `handoff_contract` entity. Each has explicit `payload_schema`, `fallback_path`, and ≥1 deterministic `validation_check`.

| Contract ID | Edge | Fallback |
|-------------|------|----------|
| `hc-builder-to-critic-autoverify` | Builder → Critic (auto-verify) | escalate_to_user |
| `hc-expert-to-builder` | Expert → Builder | route_to_navigator |
| `hc-strategist-to-builder` | Strategist → Builder | retry_with_repair |
| `hc-synthesizer-to-builder` | Synthesizer → Builder | retry_with_repair |
| `hc-critic-to-builder-revision` | Critic → Builder (revision loop) | escalate_to_user |
| `hc-debugger-to-strategist` | Debugger → Strategist | route_to_navigator |
| `hc-critic-audit-to-strategist` | Critic (audit) → Strategist | retry_with_repair |
| `hc-strategist-to-calibrator` | Strategist → Calibrator | retry_with_repair |

**Five canonical assertion forms** (Module 04, P2-Δ1):
1. `field-presence` — `<field_path> is non-null`
2. `enum-membership` — `<field_path> matches enum: [<values>]`
3. `cardinality` — `len(<field_path>) {==, >=, <=} <int>`
4. `schema-conformance` — `<field_path> validates against <schema_ref>`
5. `cross-field` — `<predicate over multiple field_paths>`

Every `validation_checks[].assertion` MUST reduce to one of these forms. Prose assertions silently degrade fast-fail to LLM judgment.

---

## Trigger Disambiguator (7.2)

Module 04 template entity for resolving cases where a trigger phrase activates multiple candidate modes or variants. Replaces prose-only convention with explicit predicate enum.

**Purpose:** Cross-mode overlap resolution (e.g., "review" could fit Critic or Expert) and intra-mode variant resolution (e.g., "audit" between `critic.regular` and `critic.audit`) fail fast at routing time.

**Predicate types:** `output_type_mismatch` (Navigator activation rule), `domain_specificity` (variant resolution), `keyword_priority` (registered trigger phrases).

**Refinement signal:** `re_routed = true` entries in Module 19 routing_decision_log are training data for tightening predicates.

---

## Anti-Patterns to Avoid (6.1)

**Don't build:** Decoy/anti-distillation mechanisms. Competitive defense, not applicable to B2B products.

**Don't optimize:** Global cache before local correctness. Cache awareness matters for cost, but don't let cache preservation distort prompt architecture at our scale.

**Don't copy:** Exact permission gate counts. Claude Code's six-layer model reflects its threat surface. Right-size to our actual risk surface.

**Don't copy:** Exact blocking budgets. The 15-second budget is tuned to Claude Code's terminal UX. Define budgets based on SEMalytics interaction patterns.

**Don't aggregate:** "Critic accuracy" or "Expert accuracy" without per-variant disaggregation. Same mode label spans 4 distinct output formats; aggregate is meaningless (7.2).

**Don't qualify at write time:** Variant IDs are stored unqualified in `routing_decision_log` (matches Module 05/07 `variants[].id`). Composing the qualified `<mode>.<variant>` form at write time creates a parallel-but-incompatible field set (7.2.1).

**General rule:** Every directive should be right-sized for our scale. Production-tested patterns are reference architectures, not specifications to clone.

---

## PDIA Method (Building Agents)

**P**urpose — One sentence. What problem does this solve?

**D**esign — Capabilities, inputs, outputs, constraints, integration. Each design decision tagged with decision type.

**I**mplementation — System prompt (behavior, not personality)

**A**ssessment — Success criteria, test scenarios, failure modes. Include testability metadata for calibrated evaluation.

---

## Specification Minimum

Every spec needs:

- **Purpose** — Why does this exist?
- **Inputs** — What goes in? (with types)
- **Outputs** — What comes out? (with format)
- **Constraints** — What limits apply?
- **Success Criteria** — How do we know it works?
- **Decision Type Tags** — Which choices are locked (reckonings) vs. judgment calls?
- **Variants** *(7.2)* — If the agent has multiple operating modes, declare each variant explicitly with its own trigger phrases, output format, and chain position. IDs stored unqualified.

---

## Severity Framework

| Level | Meaning | Calibration |
|-------|---------|-------------|
| **Critical (1)** | Will cause failure or security breach | σ < 0.3 across N runs = confirmed |
| **High (2)** | Significant bug or major issue | σ < 0.5 across N runs = likely |
| **Medium (3)** | Notable improvement opportunity | σ > 0.5 = investigate further |
| **Low (4)** | Style or minor enhancement | Calibrate only on request |

---

## Module Reference Table

| Module | Contains |
|--------|----------|
| `01_Navigator_Agent` | Ambiguity detection (output-type predicate — 6.6.1) |
| `02_Builder_Agent` | Agent creation with PDIA + decision type metadata |
| `03_Coordination_Patterns` | Dependency-first multi-agent orchestration + verification flags + capability restrictions (6.1) + Handoff Contract Registry — 8 contracts (7.2) |
| `04_Specification_Templates` | Reusable spec formats + sub-agent capability profiles (6.1) + ERA Specification Template (6.6) + Trigger Disambiguator + Handoff Contract templates with 5 canonical assertion forms (7.2) |
| `05_Expert_Agent_Example` | Adversarial depth domain specialist + decision_type_exercised gates auto-verify (6.6.1) + variants[] formalized — regular/infrastructure/ml_infrastructure/era (7.2) |
| `06_Quick_Reference` | This document — quick lookup for all patterns and concepts |
| `07_Critic_Agent` | Quality assurance with calibrated confidence + adversarial variant (6.1) + linter variant (6.2) + audit variant (6.3) + loop_exit_protocol (6.6.1) + variants[] formalized — regular/linter/audit/adversarial (7.2) |
| `08_Synthesizer_Agent` | Pattern extraction with mandatory anti-patterns and temporal context |
| `09_Debugger_Agent` | Monitor-assisted systematic diagnosis |
| `10_Strategist_Agent` | Strategic decisions with decision type enrichment |
| `11_Calibrator_Agent` | Complexity-aware AI coder configuration |
| `12_Calibration_Layer` | Multi-run evaluation stability + bias detection |
| `13_Decision_Classification` | Four-type decision routing (reckoning/evaluative/predictive/novel) |
| `14_Metacognitive_Monitor` | Agent + user-side failure detection + skeptical verification (6.1) + vision principle drift check (6.6) |
| `15_Grounding_Scores` | Knowledge trust levels + propagation rules |
| `16_Operational_Bounds` | Agent metric monitoring + cache/circuit breaker metrics (6.1) + token cost per mode (6.4) + metric #10 mode_selection_accuracy (7.2) |
| `17_Temporal_Knowledge` | Versioned knowledge + importance-weighted decay + domain half-life table + pinning (6.3.1) + planning artifact staleness (7.0.2) |
| `18_Salience_Allocation` | Dynamic resource allocation + access-driven salience from wiki logs (6.3.1) |
| `19_Memory_Architecture` | Four-tier memory (6.1, extended 6.2) + routing_index_schema (6.6.1) + routing_decision_log schema v1.0 + tier_2_metric_aggregates (7.2) + re_routing_triggers + variant ID composition rule (7.2.1) |
| `20_Permission_Model` | Risk tiers + capability restrictions + circuit breakers (6.1) |
| `21_Knowledge_Accretion` | Compile-query-enhance loop + linter (6.2) + autonomous maintenance + access logging (6.3.1) + accretion_calibration (6.6.1) + Dispatcher Boundary (7.0.2) + roadmap_phase_completed trigger (7.0.5) |
| `22_Semantic_Wiki_Search` | Tier 0 retrieval — Phase 1 (v7.3.0): `tool_check_duplicate` dup-gate, detect-and-warn. Phase 2 deferred (acu): metadata-gated semantic search + score fusion |
| `23_Taxonomy_Enforcement` | Controlled vocabulary shared across Tier 0 and Tier 3 |
| `24_Verbatim_History_Mining` | Tier 3 retrieval — verbatim + semantic search via MemPalace sidecar (96.6% R@5) |
| `25_Entity_Relationship_Analysis` | Post-routing, pre-execution entity extraction + relationship mapping + graph shape → routing escalation. Entity-scoped filters: M24 (Tier 3) active; M22 (Tier 0) Phase 2 Deferred per M25 v7.0.3 |

---

## Integration Flows

### Common Flows

```
Question → Navigator (if ambiguous) → Expert (+ adversarial depth) → User
Problem → Debugger (+ KF-2 monitor) → [Fix/Builder]
Creation → Builder (+ KF-5 decision tags) → Critic (+ KF-1 calibration) → [Revise/Deploy]
Multiple examples → Synthesizer (+ KF-6 temporal) → Framework → Builder
Decision needed → KF-5 classify → Strategist (+ KF-1 calibration) → Builder → Implementation
Setup → Calibrator (complexity assess) → [Strategist if complex] → Config → Critic → Deploy
Evaluation → KF-1 calibration → Confidence interval → Decision
```

### Flows with Auto-Verification (6.1)

```
Creation chain → Builder → AUTO: Critic (adversarial) → [Revise if findings] → Deploy
Strategy chain → Expert → Strategist → AUTO: Critic (adversarial) → Deliver
ODS profiling → ODS modules (ODS_00–ODS_10) → AUTO: Critic (adversarial, political mapping focus) → Profile
3+ mode chain → [modes] → AUTO: Critic (adversarial, compound risk) → Deliver
```

### Flows with Routing Audit (7.2)

```
Mode activation → orchestrator writes routing_decision_log entry (Module 19 schema v1.0)
re_routed = true → entry archived to wiki/operations/routing-log/{YYYY-MM}.md
Chain completion → KF-4 metric #10 evaluates rolling 100-event window → corrective action if out of bounds
Weekly → tier_2_metric_aggregates write + adversarial calibration sampling pass
```

### Infrastructure Flows

```
Agent execution → KF-2 monitor (agent-side + user-side) → [Intervene/Continue]
Knowledge ingestion → KF-3 grounding score → KF-6 temporal version → Storage
Resource contention → KF-7 salience → Allocation decision
Complex setup → KF-5 classify → Strategist (if novel) → Calibrator → Config
Agent chronic drift → KF-4 bounds → Corrective action
Long session → KF-8 routing index → Consolidation (if pressure) → Continue
Action classification → KF-9 permission tier → [Auto/Log/Human gate]
Circuit breaker → KF-4 bounds → Halt + diagnostics
Mode output → KF-10 accretion check → [File to Tier 0 / Surface to user / Skip] (6.2)
Knowledge base → Critic (linter variant) → Maintenance backlog → [Update/Archive/Delete] (6.2)
Infrastructure planning → Expert (infra domain) → Builder (architecture spec) → Critic (adversarial) (6.3)
Hosting audit → Critic (audit variant) → SPOF analysis + readiness ratings (6.3)
Model deployment → Expert (ML infra) → Strategist (phasing) → Builder (deployment plan) (6.3)
Moat analysis → Expert (architecture) → Strategist (durability + reinforcement loops) (6.3)
Entity mapping → Expert (ERA domain) → Builder (ERA Specification Template) → AUTO: Critic (adversarial) (6.6)
Routing audit → orchestrator → routing_decision_log → KF-4 metric #10 → [pass / corrective action] (7.2)
```

### Mode Combinations

```
Builder → Critic: Create spec, validate before implementation
Builder → Critic (adversarial): Auto-verification in chains (6.1)
Synthesizer → Builder: Extract pattern, create agents from pattern
Debugger → Strategist: Fix immediate issue, prevent systemically
Navigator → Any: Disambiguate then route (only if output-type predicate fires)
Calibrator → Strategist → Calibrator: Complex stack decision round-trip
Strategist → Calibrator → Critic: Stack decision → config → validation
Any Mode → Debugger: Something breaks during execution
KF-2 → Coordinator: Monitor detects stuck agent → reassign
KF-7 → Coordinator: Salience reallocation during resource contention
KF-8 → Any: Routing index informs mode selection (6.1)
KF-9 → Any: Permission tier gates output framing (6.1)
KF-10 → Tier 0: Accretion files novel knowledge to persistent storage (6.2)
Critic (linter) → KF-10: Linter contradictions feed back as accretion candidates (6.2)
Expert (infra) → Builder: Analyze infrastructure requirements, produce architecture document (6.3)
Critic (audit) → Expert (infra) → Builder: Inventory → analyze → architecture plan (6.3)
Expert (ML infra) → Strategist → Builder: Model requirements → phased deployment → plan (6.3)
Expert (architecture) → Strategist: Competitive moat enumeration → durability analysis (6.3)
Critic (audit) → Strategist → Builder: Inventory → extraction priority → migration plan (6.3)
Expert (ERA) → Builder: Entity graph analysis → ERA Specification Template output (6.6)
Expert (ERA) → Builder → AUTO: Critic (adversarial): Full ERA chain with verification (6.6)
```

---

## Cross-Linking Matrix

```
12 Calibration Layer    ↔ Critic, Strategist, Debugger, Expert, Builder, Synthesizer, 13, 19, 20, 21
13 Decision Classification ↔ Navigator, Strategist, Expert, Calibrator, Builder, 12, 19, 20
14 Metacognitive Monitor ↔ Coordinator, Debugger, 12, 15, 16, 18, 19, 21, all modes
15 Grounding Scores     ↔ Expert, Critic, 14, 17, 12, 18, 19, 20, 21
16 Operational Bounds   ↔ 14, Coordinator, Strategist, 15, 19, 20, 04 (7.2 metric #10 ↔ trigger_disambiguator)
17 Temporal Knowledge   ↔ 15, Debugger, Synthesizer, 12, 19, 21
18 Salience Allocation  ↔ Coordinator, Strategist, 14, 15, 16, 19, 21 (6.3.1 access signal)
19 Memory Architecture  ↔ Orchestrator, 03, 04, 14, 16, 17, 20, 21, 22, 24 (Tier 0/Tier 3 retrieval); 05, 07 (variant ID storage — 7.2.1)
20 Permission Model     ↔ Orchestrator, 03, 04, 13, 14, 16, 19, 21
21 Knowledge Accretion  ↔ Critic, Synthesizer, Debugger, Strategist, Builder, Expert, Calibrator, 12, 14, 15, 17, 19, 20, 22, 23, 24
22 Semantic Wiki Search ↔ 19 (Tier 0), 21, 23 (taxonomy validation)
23 Taxonomy Enforcement ↔ 19, 21, 22, 24 (shared vocabulary)
24 Verbatim History Mining ↔ 19 (Tier 3), 21, 23
25 Entity Relationship Analysis ↔ 00 (post-routing pass), 19, 22 (entity-scoped filters: Phase 2 Deferred), 24 (entity-scoped filters: active)
```

---

## Quality Checklist

Before any response:

- [ ] Addresses specific question asked
- [ ] Depth matches user expertise
- [ ] Actionable without follow-up
- [ ] Clear next steps provided
- [ ] No unnecessary hedging
- [ ] Decision types classified (if applicable)
- [ ] Severity calibrated (if evaluative)
- [ ] Adversarial depth applied (if Expert mode)
- [ ] Dependencies mapped (if coordination)
- [ ] Routing index updated (if decision made or mode completed) *(6.1)*
- [ ] **routing_decision_log entry written (on every mode activation)** *(7.2)*
- [ ] Risk tier appropriate for output framing *(6.1)*
- [ ] Auto-verification triggered (if qualifying chain) *(6.1)*
- [ ] Accretion check applied (if output is evaluative+ and potentially novel) *(6.2)*
- [ ] decision_type_exercised present (if Expert output) *(6.6.1)*
- [ ] variants[] resolved to specific variant_id (if Critic/Expert mode) *(7.2)*

---

## Handoff Essentials

Every handoff includes:

1. What happened (source agent's output)
2. What was learned (new information)
3. What to do next (instruction for target)
4. What context carries forward (preserved state)
5. Position in dependency graph (where this fits in overall flow)
6. Decision type metadata (reasoning depth guidance for receiving agent)
7. **Handoff Contract reference (7.2)** — applicable `handoff_contract_id` from Module 03 registry, payload conforming to declared schema

---

## Context to Preserve

```yaml
session: id, current_step, dependency_graph
user: expertise, goals, constraints
task: objective, completed, pending, critical_path
decisions: what, who, why, reversible?, decision_type
artifacts: id, type, grounding_score, version
routing_audit:  # NEW 7.2
  last_log_entry_id: <uuid>
  re_routed_count_this_session: integer
  current_per_variant_accuracy: <map qualified_id → float>
```

---

## When Stuck

1. What is the actual goal? (surface vs. underlying)
2. What decision type is this? (reckoning/evaluative/predictive/novel)
3. What depth is appropriate? (beginner/intermediate/advanced)
4. What constraints apply?
5. What comes next?

If still stuck: ask ONE clarifying question, then proceed.

---

## Error Response Pattern

```
I couldn't [task] because [reason].

To resolve:
1. [Option A]
2. [Option B]

To prevent: [guidance]
```

---

## System Prompt Rules

**Do:**
- Behavior over description
- Boundaries over permissions
- Examples over rules
- Decision type tags per design choice
- Variant declaration per multi-mode agent (7.2)
- Handoff contracts on chain edges (7.2)

**Don't:**
- "You are a helpful assistant..."
- "Try to..." / "Attempt to..."
- Personality descriptions
- Exhaustive scenario lists
- Scope-definition ceremony (Expert)
- Pattern-selection-first (Coordinator)
- Aggregate mode-accuracy metrics without per-variant disaggregation (7.2)
