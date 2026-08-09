# KnowledgeForge Core

**Version:** 7.27.0 · **Status:** Active development · **Modules:** 26 (00–25)

Single source of truth for the KnowledgeForge reasoning framework. All platform variants compile from here.

## What's New in 7.27.0

Mid-chain premise invalidation (core-e49). A downstream chain step can signal back
upstream via `upstream_invalidation` in its response schema. Sev2+ signals halt the
chain and re-enter at the named step; Sev1 logs and continues. Implemented across
M00 (re-entry predicate in STATIC ZONE), M03 (worked example contract), M04
(handoff_contract template), and M19 (4th canonical re_routing_trigger).

---

## What's New in 7.25.0

COS artifact emission for comms-domain work. Two agents now detect when they're operating in a communications context and emit COS-compatible artifacts alongside their standard KF output.

- **Module 08 (Synthesizer)** 6.6.1 → 6.7.0 — Phase 4.5 added: 4-signal comms-domain detection after pattern extraction. When a synthesized pattern is comms-domain (≥1 signal), has ≥2 examples, and confidence ≥ 0.6: emit `cos_template_output` (COS template JSON) alongside the standard wiki entry. Field mapping and emit trigger defined in `specs/cos-template-schema.md`. Template: `templates/cos-template-emit.jinja2`. COS MCP unavailable → wiki-only with surface note.
- **Module 11 (Calibrator)** 7.0.0 → 7.1.0 — 5-signal comms-heavy project detection at interview phase (threshold: 2+). Comms-heavy projects emit two companion files alongside CLAUDE.md: `cos-agent-profile.json` (writer personality from `profile_agent`) and `cos-audience-profile.json` (audience OCEAN from `audience_profile`). CLAUDE.md also gets a comms section embedding `style_label`, `strengths`, `blind_spots`, and audience `elm_route`. Schema refs: `specs/cos-profile-schemas.md`. Templates: `templates/cos-agent-profile.json.jinja`, `templates/cos-audience-profile.json.jinja`. COS MCP unavailable → CLAUDE.md-only with placeholder section.
- **Templates** — Three new Jinja2 emit templates added to `templates/`: `cos-template-emit.jinja2`, `cos-agent-profile.json.jinja`, `cos-audience-profile.json.jinja`.
- **knowledgeforge-cc** — Compiled and PR cleared. CC skills and agents updated for both modules.

---

## What Is KnowledgeForge?

KnowledgeForge (KF) is a reasoning orchestration layer for AI coding assistants. It patches known failure modes — skipping hypotheses, hiding trade-offs, missing gaps — by routing requests to specialized modes with targeted context injection.

KF modes: Builder · Critic · Debugger · Strategist · Expert · Synthesizer · Navigator · Coordinator · Calibrator

---

## Repository Role

| Repo | Role |
|------|------|
| **knowledgeforge-core** (this) | Canonical module specs, plans, wiki, compiler |
| `knowledgeforge-cp` | Claude Projects variant (compilation target) |
| `knowledgeforge-cc` | Claude Code variant (compilation target) |
| `knowledgeforge-cw` | Cowork variant |
| `knowledgeforge-web` | Web agents variant (future) |

Changes flow **into core first**, then compile out to variants. Never edit variant repos directly for module-level changes.

---

## Structure

```
modules/          # 26 canonical module specs (00–25)
plans/            # Architecture session documents
wiki/             # Tier 0 accreted knowledge
templates/        # Spec templates (Module 04) + COS emit templates (cos-template-emit, cos-agent-profile, cos-audience-profile)
taxonomy/         # Controlled vocabulary (Module 23)
model-profiles/   # Per-model weakness/strength maps
platform-bindings/ # Per-platform adaptation rules
compiler/         # kf-compile tooling (Phase 6)
docs/planning/    # Session notes, drift audits
tests/            # Routing and module test suites
```

---

## Implementation Phases

See `IMPLEMENTATION_PLAN.md` for full detail.

| Phase | Description | Days |
|-------|-------------|------|
| **0** | Repo setup and sync (current) | 1 |
| **1** | Pre-prompt routing hook (Gemma 3 4B via Ollama) | 2–4 |
| **2** | Decompose CLAUDE.md into skills + docs | 5–7 |
| **3** | Stop gate + state survival hooks | 8–10 |
| **4** | Module spec updates from research | 11–14 |
| **5** | Model profiles | 15–18 |
| **6** | Compiler MVP | 19–25 |
| **7** | Architectural changes | 26–35 |
| **8** | Web agents variant | 36–50 |
| **9** | Research ingestion pipeline | 51–55 |
| **10** | Monitoring and tuning | Ongoing |

---

## Modules

| # | Module | Purpose |
|---|--------|---------|
| 00 | Orchestrator | Agent identity + routing |
| 01 | Navigator | Ambiguity resolution |
| 02 | Builder | Spec and implementation generation |
| 03 | Coordination Patterns | Multi-agent coordination |
| 04 | Specification Templates | Reusable spec formats |
| 05 | Expert Agent | Deep analysis, adversarial depth |
| 06 | Quick Reference | Routing table + signal guide |
| 07 | Critic Agent | Review, validation, audit |
| 08 | Synthesizer Agent | Pattern extraction, abstraction |
| 09 | Debugger Agent | Diagnosis, root cause |
| 10 | Strategist Agent | Trade-off evaluation, prioritization |
| 11 | Calibrator Agent | AI coder configuration |
| 12 | Calibration Layer | Multi-pass evaluation, judge isolation |
| 13 | Decision Classification | Reckoning/evaluative/predictive/novel |
| 14 | Metacognitive Monitor | Self-detection of failure modes |
| 15 | Grounding Scores | Knowledge trust 0.0–1.0 |
| 16 | Operational Bounds | Circuit breakers, resource limits |
| 17 | Temporal Knowledge | Knowledge age and decay |
| 18 | Salience Allocation | Multi-task priority weighting |
| 19 | Memory Architecture | Tier 0–3 memory system |
| 20 | Permission Model | Allow/deny/mutate policies |
| 21 | Knowledge Accretion | Wiki filing, dedup, terminal state |
| 22 | Semantic Wiki Search | Two-phase retrieval, grep fallback |
| 23 | Taxonomy Enforcement | Controlled vocabulary validation |
| 24 | Verbatim History Mining | Conversation turn storage and recall |
| 25 | Entity Relationship Analysis | ERA domain routing |

---

## Setup

### Claude Project Setup

> **Before re-uploading:** Delete **all** existing project knowledge files first. Claude Projects does not replace files — it appends. Duplicate filenames (e.g., `06_Quick_Reference__1_.md`) create a live contradiction source where retrieval can't distinguish canonical from stale. Clean-slate each upload cycle.

1. Create (or open) a Claude Project at [claude.ai](https://claude.ai)
2. Go to **Project Instructions** → paste the full contents of `00_Project_Instructions-Claude.md` from `knowledgeforge-cp/`
3. Under **Project Knowledge**, upload all 25 knowledge files from `knowledgeforge-cp/` (Module 00 is already covered by step 2):

**Core Agents (11 files)**
- `01_Navigator_Agent.md` — Ambiguity detection and routing
- `02_Builder_Agent.md` — Specification generation (PDIA method)
- `03_Coordination_Patterns.md` — Multi-agent workflow design + Handoff Contract Registry (13 contracts)
- `04_Specification_Templates.md` — Reusable spec formats + trigger disambiguators
- `05_Expert_Agent_Example.md` — Deep analysis, adversarial depth (5 variants: regular / infra / ml-infra / era / research)
- `06_Quick_Reference.md` — Routing table and signal guide
- `07_Critic_Agent.md` — Review, validation, adversarial variant (4 variants: regular / linter / audit / adversarial)
- `08_Synthesizer_Agent.md` — Pattern extraction and abstraction
- `09_Debugger_Agent.md` — Hypothesis-driven root-cause diagnosis
- `10_Strategist_Agent.md` — Trade-off evaluation, sequencing
- `11_Calibrator_Agent.md` — Complexity-appropriate AI coder configuration

**Cognitive Infrastructure (14 files)**
- `12_Calibration_Layer.md` — Multi-pass evaluation, judge isolation
- `13_Decision_Classification.md` — Reckoning / evaluative / predictive / novel routing
- `14_Metacognitive_Monitor.md` — Acute failure detection (loops, overflow, confidence collapse)
- `15_Grounding_Scores.md` — Evidence quality scoring (0.0–1.0)
- `16_Operational_Bounds.md` — Metrics, circuit breakers, mode-selection accuracy (9 variants)
- `17_Temporal_Knowledge.md` — Knowledge age, decay, planning artifact staleness
- `18_Salience_Allocation.md` — Multi-task attention weighting
- `19_Memory_Architecture.md` — Four-tier memory, routing index, routing decision log
- `20_Permission_Model.md` — Risk tiers (LOW/MEDIUM/HIGH) and capability gates
- `21_Knowledge_Accretion.md` — Cross-session knowledge persistence, compile-query-enhance loop
- `22_Semantic_Wiki_Search.md` — Metadata-gated semantic search over Tier 0 wiki
- `23_Taxonomy_Enforcement.md` — Fixed controlled vocabulary (10 domains, ~40 topics, ~55 tags)
- `24_Verbatim_History_Mining.md` — Verbatim Tier 3 storage + MemPalace semantic retrieval
- `25_Entity_Relationship_Analysis.md` — ERA post-routing pass: entity graph, cardinality, coupling

> **Note:** Module 25 (ERA) is required. The orchestrator unconditionally runs ERA as a post-routing, pre-execution pass on Builder, Coordinator, Expert, Strategist, and Critic requests. Omitting it leaves five routing paths unguarded.

> **Note:** The research variant in Module 05 (Expert) requires the Asta/Alia Semantic Scholar MCP connected to your Claude Project. Without it, research variant permanently operates in degraded mode (WebSearch fallback, grounding capped at 0.6, ship disposition unavailable). All other modes work normally without the MCP.

4. Start a conversation — the system automatically classifies and routes every request.

---

### Mode Triggers

| Signal | Mode | Notes |
|--------|------|-------|
| "Create", "build", "generate spec", "write", "implement", "scaffold" | **Builder** | PDIA method; auto-verify on chain output |
| "Review", "validate", "find gaps", "audit", "sanity check", "LGTM?" | **Critic** | 4 variants: regular / linter / audit / adversarial |
| "Health check the knowledge base", "lint the wiki" | **Critic (linter)** | Scans for staleness, contradictions, redundancy |
| "Hosting audit", "infrastructure inventory", "SPOF analysis" | **Critic (audit)** | Decomposition readiness + extraction priority |
| "Not working", "debug", "failing", "why is this", "root cause" | **Debugger** | Hypothesis-driven; requires >0.8 confidence |
| "Prioritize", "trade-offs", "should I", "which option", "ROI" | **Strategist** | Explicit trade-offs + reversibility assessment |
| "Find patterns", "extract", "what do these have in common" | **Synthesizer** | Every pattern requires ≥1 anti-pattern |
| "Setup project", "CLAUDE.md", "AI coder config", "guardrails" | **Calibrator** | Complexity-appropriate; no over-engineering |
| "Deep analysis", "blast radius", "threat model", "architecture review" | **Expert (regular)** | Adversarial depth; emits decision_type_exercised |
| "Design infrastructure", "plan service topology", "GPU sizing", "model deployment" | **Expert → Builder (infra/ML)** | Expert analyzes; Builder produces architecture doc |
| "Competitive moat", "defensibility", "hard to copy" | **Expert → Strategist** | Expert enumerates; Strategist rates durability |
| "Find evidence for", "ground this claim", "what does the research say" | **Expert (research)** | Asta MCP required; WebSearch fallback = degraded |
| "Map entity relationships", "audit module dependencies", "model agent contracts" | **Expert (ERA) → Builder** | Entity graph + ERA Specification Template |
| "Workflow", "multi-agent", "orchestrate", "fan out", "delegate" | **Coordinator** | Dependency-first; derives pattern from graph |
| Genuinely ambiguous intent (different output types for top-2 candidates) | **Navigator** | One targeted question; then routes |

---

## Compile Maps

Human-navigable maps showing exactly which module section compiled into which output file. Click any source link to jump directly to that section.

| Platform | Map |
|----------|-----|
| Claude Code (`knowledgeforge-cc`) | [load-map-claude-code.md](load-map-claude-code.md) |
| Claude Projects (`knowledgeforge-cp`) | [load-map-claude-projects.md](load-map-claude-projects.md) |

Maps are regenerated on each compile run (`compiler/kf-compile.py`). See `CHANGELOG.md` for release-level history.

---

## The Core Problem (Why This Exists)

Claude Projects outperforms Claude Code because CP has semantic search over all module files — it finds the right module when needed. CC requires the agent to *know* to load something before it knows it needs it.

**The solution (Phase 1):** A `UserPromptSubmit` hook runs a fast local LLM (Gemma 3 4B via Ollama) before Claude sees the prompt. It classifies the request and injects routing directives, replicating CP's semantic retrieval at ~200ms overhead and zero API cost.
