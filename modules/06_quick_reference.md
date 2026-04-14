# KnowledgeForge 6.6 Quick Reference

## Module Metadata

```yaml
module:
  title: KnowledgeForge 6.6 Quick Reference
  version: 6.6.0
  purpose: Quick lookup for all patterns, checklists, mode triggers, integration flows, and core concepts across the full KF 6.6 framework
  topics: [quick-reference, cheatsheet, mode-selection, integration-flows, checklists, anti-patterns]
  contexts: [all-interactions, lookup, orientation]
  difficulty: foundational
  related: [Agent_Instructions (orchestrator), 01_Navigator_Agent, 02_Builder_Agent, 03_Coordination_Patterns, 04_Specification_Templates, 05_Expert_Agent_Example, 07_Critic_Agent, 08_Synthesizer_Agent, 09_Debugger_Agent, 10_Strategist_Agent, 11_Calibrator_Agent, 12_Calibration_Layer, 13_Decision_Classification, 14_Metacognitive_Monitor, 15_Grounding_Scores, 16_Operational_Bounds, 17_Temporal_Knowledge, 18_Salience_Allocation, 19_Memory_Architecture, 20_Permission_Model, 21_Knowledge_Accretion, 22_Semantic_Wiki_Search, 23_Taxonomy_Enforcement, 24_Verbatim_History_Mining]
  changelog:
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

**KF modes patch Sonnet's weaknesses, not scaffold its strengths.**

Modes that win (Debugger, Strategist, Critic) impose constraints that *prevent* Sonnet's failure modes. Every mode and module must pass this test: does this add value Sonnet doesn't already provide?

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

| Mode | Trigger | Action | KF 6.0+ Changes |
|------|---------|--------|------------------|
| **Navigator** | Genuinely ambiguous intent only | Disambiguate → Route | Fires only on ambiguity; clear intents bypass |
| **Builder** | "Create an agent for..." | PDIA method → Complete spec → System prompt | + decision type tags per design choice |
| **Coordinator** | Multi-agent task | Map dependencies → Derive pattern from graph | Dependency-first; patterns are vocabulary, not menu |
| **Expert** | Domain-specific question | First-order + Adversarial depth analysis | + compound failures, blast radius, assumption inversion |
| **Critic** | "Review this spec", "Find gaps" | Challenge → Identify gaps → Prioritize fixes | + calibrated severity with confidence intervals |
| **Synthesizer** | "Extract patterns", "Find commonalities" | Analyze → Abstract → Create framework | + mandatory anti-patterns, temporal context |
| **Debugger** | "This isn't working", "Why is X failing" | Hypothesize → Test → Isolate root cause | + monitor-assisted diagnosis, temporal trace |
| **Strategist** | "What should I build next?", "Prioritize" | Evaluate → Trade-off analysis → Recommend | + decision type routing, calibrated rankings |
| **Calibrator** | "Setup CLAUDE.md", "Configure AI" | Assess complexity → Interview → Generate config | + complexity tiers, compliance templates |
| **Expert (infra)** | "Design infrastructure", "Plan deployment", "Size hardware" | Adversarial depth on architecture + model mapping → Architecture spec | + infrastructure domain adaptation (6.3) |
| **Expert (ERA)** | "Map entity relationships", "Audit module dependencies", "Model agent contracts", "What entities does X produce/consume?" | Entity graph analysis with adversarial depth → ERA Specification Template output | + ERA domain adaptation (6.6); disambiguator: produces structured entity/relationship artifact, not abstract pattern |

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
| **19 Memory Architecture** | Three-tier memory for long-session routing accuracy | Routing index (always loaded) → Mode state (on demand) → History (grep only) |
| **20 Permission Model** | Risk tiers + capability restrictions for sub-agents | LOW (auto) / MEDIUM (auto+log) / HIGH (human confirm) |

## Infrastructure Modules (New in 6.2)

| Module | Purpose | Key Concept |
|--------|---------|-------------|
| **21 Knowledge Accretion** | Compile-query-enhance loop for persistent knowledge | Accretion signal → file to Tier 0 or surface to user; example: ERA analyses of KF module structure are high-value accretion candidates (6.6) |

## Infrastructure Modules (New in 6.6)

| Module | Purpose | Key Concept |
|--------|---------|-------------|
| **ERA domain (Module 05)** | Entity Relationship Analysis — adversarial depth applied to entity graphs, module dependencies, and agent contracts | Implicit entity detection + cardinality violation analysis + handoff contract auditing; produces ERA Specification Template output (Module 04) |

## Infrastructure Modules (New in 6.5)

| Module | Purpose | Key Concept |
|--------|---------|-------------|
| **22 Semantic Wiki Search** | Tier 0 retrieval via metadata-gated semantic search | Filter-first: domain/topic/tag pre-filter → embedding re-rank |
| **23 Taxonomy Enforcement** | Controlled vocabulary shared across Tier 0 and Tier 3 | Fixed domain/topic/tag vocabulary validated at write time |
| **24 Verbatim History Mining** | Tier 3 retrieval via verbatim storage + semantic search | Verbatim + semantic = 96.6% R@5; pre-summarized = 84.2% |
| **25 Entity Relationship Analysis** | Pre-routing entity extraction + relationship mapping | Graph shape → routing escalation + entity-scoped memory filters |

## KF-N Shorthand → Module Mapping

Throughout KF documentation, infrastructure modules are referenced by shorthand (KF-1 through KF-9). This is the canonical mapping:

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

**Five checks (6.1):** Circular reasoning (state hashing), context overflow (utilization tracking), confidence degradation (rolling average), user-side health (repetition/escalation/correction detection), skeptical verification (stale state detection)

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

**Two-layer safety:** Monitor catches acute failures. Bounds catches chronic drift.

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

## Memory Architecture (KF-8, 6.1 — extended 6.2)

**Four tiers:**
- **Tier 0 — Persistent Knowledge:** Survives across sessions. `wiki/` directory (Claude Code) or project knowledge files (Claude Projects). Written by Knowledge Accretion (Module 21).
- **Tier 1 — Routing Index:** Always in context. ~150 chars/entry, max 30 entries. Modes engaged, decisions made, task state.
- **Tier 2 — Mode State:** Loaded on demand. One mode's state at a time. Swapped on transitions.
- **Tier 3 — History:** Never re-read in full. Grep-search only for specific identifiers.

**Skeptical verification:** Treat accumulated context as hints, not facts. Verify before acting on stale data.

**Consolidation:** Orient → Gather → Consolidate → Prune. Output is a diff, not a rewrite.

**Context pressure response:** At 75% → consolidate. At 80% → aggressive consolidation. At 85% → emergency compression with warning.

---

## Permission Model (KF-9, 6.1)

| Tier | Actions | Approval |
|------|---------|----------|
| **LOW** | Reckonings, routing, formatting, index updates | Auto |
| **MEDIUM** | Evaluative judgments, 2-mode chains, artifact drafts, profile updates | Auto + logging |
| **HIGH** | Novel judgments, 3+ mode chains, ODS→COS bridging (see ODS module set), irreversible recommendations | Human confirm |

**Risk escalation:** Chain length ≥ 3 → minimum MEDIUM. Low confidence → tier +1. Adversarial finding → HIGH.

**Capability profiles:** Each mode has read/write/escalate boundaries when operating as sub-agent. No sub-agent can modify another's output.

**Circuit breakers:** 3 consecutive failures → halt. 2 chain failures at same step → abort chain.

---

## Automatic Adversarial Verification (6.1)

**Fires on:** Builder output in chains, Strategist recommendations, ODS profiles (see ODS module set: ODS_00–ODS_10), any 3+ mode chain.

**Framing:** "Assume the output has at least one significant flaw. Find what the producing agent missed."

**Output:** Severity 2+ findings only. Clean pass or risk escalation.

**Yield tracking:** Healthy range 20%–80%. Below 20% = too soft. Above 80% = rebuild, don't patch.

---

## Anti-Patterns to Avoid (6.1)

**Don't build:** Decoy/anti-distillation mechanisms. Competitive defense, not applicable to B2B products.

**Don't optimize:** Global cache before local correctness. Cache awareness matters for cost, but don't let cache preservation distort prompt architecture at our scale.

**Don't copy:** Exact permission gate counts. Claude Code's six-layer model reflects its threat surface. Right-size to our actual risk surface.

**Don't copy:** Exact blocking budgets. The 15-second budget is tuned to Claude Code's terminal UX. Define budgets based on SEMalytics interaction patterns.

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
- **Decision Type Tags** — (NEW) Which choices are locked (reckonings) vs. judgment calls?

---

## Severity Framework

| Level | Meaning | Calibration (KF 6.0) |
|-------|---------|----------------------|
| **Critical** | Will cause failure or security breach | σ < 0.3 across N runs = confirmed |
| **High** | Significant bug or major issue | σ < 0.5 across N runs = likely |
| **Medium** | Notable improvement opportunity | σ > 0.5 = investigate further |
| **Low** | Style or minor enhancement | Calibrate only on request |

---

## Module Reference Table

| Module | Contains |
|--------|----------|
| `01_Navigator_Agent` | Ambiguity detection and intent disambiguation |
| `02_Builder_Agent` | Agent creation with PDIA + decision type metadata |
| `03_Coordination_Patterns` | Dependency-first multi-agent orchestration + verification flags + capability restrictions (6.1) |
| `04_Specification_Templates` | Reusable spec formats + sub-agent capability profiles (6.1) + ERA Specification Template (6.6) |
| `05_Expert_Agent_Example` | Adversarial depth domain specialist pattern |
| `06_Quick_Reference` | This document — quick lookup for all patterns and concepts |
| `07_Critic_Agent` | Quality assurance with calibrated confidence + adversarial variant (6.1) |
| `08_Synthesizer_Agent` | Pattern extraction with mandatory anti-patterns and temporal context |
| `09_Debugger_Agent` | Monitor-assisted systematic diagnosis |
| `10_Strategist_Agent` | Strategic decisions with decision type enrichment |
| `11_Calibrator_Agent` | Complexity-aware AI coder configuration |
| `12_Calibration_Layer` | Multi-run evaluation stability + bias detection |
| `13_Decision_Classification` | Four-type decision routing (reckoning/evaluative/predictive/novel) |
| `14_Metacognitive_Monitor` | Agent + user-side failure detection + skeptical verification (6.1) |
| `15_Grounding_Scores` | Knowledge trust levels + propagation rules |
| `16_Operational_Bounds` | Agent metric monitoring + cache/circuit breaker metrics (6.1) |
| `17_Temporal_Knowledge` | Versioned knowledge with temporal relationships + importance-weighted decay model + domain half-life table + pinning (6.3.1) |
| `18_Salience_Allocation` | Dynamic resource allocation by goal relevance + access-driven salience signal from wiki logs (6.3.1) |
| `19_Memory_Architecture` | Four-tier memory: persistent wiki (Tier 0) + routing index + mode state + history (6.1, extended 6.2) |
| `20_Permission_Model` | Risk tiers + capability restrictions + circuit breakers (6.1) |
| `21_Knowledge_Accretion` | Compile-query-enhance loop + accretion signals + knowledge base linter + autonomous maintenance cycle + access logging + consolidation protocol (6.3.1); ERA analyses of KF module structure are high-value accretion candidates (6.6) |

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
```

### Mode Combinations

```
Builder → Critic: Create spec, validate before implementation
Builder → Critic (adversarial): Auto-verification in chains (6.1)
Synthesizer → Builder: Extract pattern, create agents from pattern
Debugger → Strategist: Fix immediate issue, prevent systemically
Navigator → Any: Disambiguate then route (only if ambiguous)
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
16 Operational Bounds   ↔ 14, Coordinator, Strategist, 15, 19, 20
17 Temporal Knowledge   ↔ 15, Debugger, Synthesizer, 12, 19, 21
18 Salience Allocation  ↔ Coordinator, Strategist, 14, 15, 16, 19
19 Memory Architecture  ↔ Orchestrator, 03, 04, 14, 16, 17, 20, 21
20 Permission Model     ↔ Orchestrator, 03, 04, 13, 14, 16, 19, 21
21 Knowledge Accretion  ↔ Critic, Synthesizer, Debugger, Strategist, Builder, Expert, Calibrator, 12, 14, 15, 17, 19, 20
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
- [ ] Risk tier appropriate for output framing *(6.1)*
- [ ] Auto-verification triggered (if qualifying chain) *(6.1)*
- [ ] Accretion check applied (if output is evaluative+ and potentially novel) *(6.2)*

---

## Handoff Essentials

Every handoff includes:

1. What happened (source agent's output)
2. What was learned (new information)
3. What to do next (instruction for target)
4. What context carries forward (preserved state)
5. Position in dependency graph (where this fits in overall flow)
6. Decision type metadata (reasoning depth guidance for receiving agent)

---

## Context to Preserve

```yaml
session: id, current_step, dependency_graph
user: expertise, goals, constraints
task: objective, completed, pending, critical_path
decisions: what, who, why, reversible?, decision_type
artifacts: id, type, grounding_score, version
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

**Don't:**
- "You are a helpful assistant..."
- "Try to..." / "Attempt to..."
- Personality descriptions
- Exhaustive scenario lists
- Scope-definition ceremony (Expert)
- Pattern-selection-first (Coordinator)
