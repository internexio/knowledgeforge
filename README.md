# KnowledgeForge Core

**Version:** 7.2.0 · **Status:** Active development

Single source of truth for the KnowledgeForge reasoning framework. All platform variants compile from here.

## What's New in 7.2.0

Tool-calling architecture audit (Track C) — formalizes mode handoffs as typed contracts and makes mode-selection accuracy measurable. Cascade docs in `docs/planning/Typed_Mode_Calling/chain-log-{01..04}-tool-calling.md`.

- **Module 04** — `Handoff_Contract` and `trigger_disambiguator` entities. `validation_checks[].assertion` must reduce to one of five canonical forms (field-presence, enum-membership, cardinality, schema-conformance, cross-field). Resolves the "prose conventions for handoff payloads" gap that produced silent quality drift between modes.
- **Module 03** — Handoff Contract Registry: 8 active mode-to-mode edges registered as typed contracts with explicit payload_schema, fallback_path, and ≥1 deterministic validation check.
- **Module 05 / 07** — Expert and Critic now declare `variants[]` as first-class taxonomy. 4 variants each (Expert: regular / infrastructure / ml_infrastructure / era; Critic: regular / linter / audit / adversarial). Routing accuracy is now variant-aware.
- **Module 16** — New metric #10 `mode_selection_accuracy`. Re-routing rate is the deterministic primary; weekly adversarial sampling provides calibration. Variant-aware thresholds (90% overall, 95% per-variant).
- **Module 19** — `routing_decision_log` schema v1.0 (audit trail, separate from `routing_index` state) and `tier_2_metric_aggregates` for weekly persistence beyond the rolling window.
- **Module 00** — Orchestrator writes a log entry on every mode activation and evaluates metric #10 thresholds at chain completion.
- **Wiki** — Three accretion entries filed: `wiki/patterns/mode-variants-taxonomy.md`, `wiki/diagnostics/handoff-payload-schema-gap.md`, `wiki/methodologies/external-source-to-kf-mapping.md`.

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
templates/        # Spec templates (Module 04)
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
