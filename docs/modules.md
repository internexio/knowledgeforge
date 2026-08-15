# KnowledgeForge — Module Reference

27 modules (M00–M26). Versions read from `modules/NN_*.md` source files.

**Mode-specific modules** implement a reasoning mode (M01–M11).
**Cross-cutting modules** apply across all modes; they don't implement a single mode
but shape how every mode reasons, remembers, and bounds itself (M12–M26).

---

## Mode-Specific Modules (M00–M11)

| # | Module | Version | Purpose |
|---|--------|---------|---------|
| M00 | [Orchestrator](../modules/00_orchestrator.md) | 7.25.0 | Agent identity, decision classification, mode routing, mode chaining, adversarial verification |
| M01 | [Navigator](../modules/01_navigator.md) | 7.1.0 | Ambiguity detection and resolution — fires only on genuine ambiguity |
| M02 | [Builder](../modules/02_builder.md) | 7.0.1 | Spec and implementation generation (PDIA method: Purpose → Design → Implementation → Assessment) |
| M03 | [Coordination Patterns](../modules/03_coordination_patterns.md) | 7.6.0 | Multi-agent workflow design, Handoff Contract Registry (13 contracts), dual fingerprinting |
| M04 | [Specification Templates](../modules/04_specification_templates.md) | 7.4.0 | Reusable spec formats, trigger disambiguators, upstream_invalidation field |
| M05 | [Expert Agent](../modules/05_expert_agent.md) | 7.4.0 | Deep analysis with adversarial depth (5 variants: regular / infra / ml-infra / era / research) |
| M06 | [Quick Reference](../modules/06_quick_reference.md) | 7.3.0 | Routing table, signal guide, mode variants taxonomy, integration flows |
| M07 | [Critic Agent](../modules/07_critic_agent.md) | 7.6.0 | Review, validation, audit (4 variants: regular / linter / audit / adversarial); comms variant via COS MCP |
| M08 | [Synthesizer Agent](../modules/08_synthesizer_agent.md) | 6.8.0 | Pattern extraction, abstraction, anti-patterns; comms-domain emit |
| M09 | [Debugger Agent](../modules/09_debugger_agent.md) | 7.0.2 | Hypothesis-driven root-cause diagnosis; requires >0.8 confidence before declaring root cause |
| M10 | [Strategist Agent](../modules/10_strategist_agent.md) | 6.5.0 | Trade-off evaluation, reversibility assessment, sequencing; never recommends "do everything" |
| M11 | [Calibrator Agent](../modules/11_calibrator_agent.md) | 7.2.0 | Complexity-appropriate AI coder configuration (CLAUDE.md, .cursorrules, etc.) |

---

## Cross-Cutting Infrastructure Modules (M12–M26)

| # | Module | Version | Purpose |
|---|--------|---------|---------|
| M12 | [Calibration Layer](../modules/12_calibration_layer.md) | 7.0.2 | Multi-pass evaluation, cross-provider judge isolation, SAP-inspired structured output parsing cascade |
| M13 | [Decision Classification](../modules/13_decision_classification.md) | 6.5.0 | Reckoning / evaluative / predictive / novel — the Ozymandias Test |
| M14 | [Metacognitive Monitor](../modules/14_metacognitive_monitor.md) | 6.7.0 | Acute failure detection: loops, context overflow, confidence collapse, iteration scope |
| M15 | [Grounding Scores](../modules/15_grounding_scores.md) | 6.5.0 | Knowledge trust 0.0–1.0; accretion gate (≥0.6 to file); degraded ceiling at WebSearch fallback |
| M16 | [Operational Bounds](../modules/16_operational_bounds.md) | 7.3.1 | Circuit breakers, resource limits, mode-selection accuracy metric (9 variants, ≥90% overall) |
| M17 | [Temporal Knowledge](../modules/17_temporal_knowledge.md) | 7.0.2 | Knowledge age, importance-weighted decay, domain half-life table, planning artifact staleness |
| M18 | [Salience Allocation](../modules/18_salience_allocation.md) | 7.1.0 | Multi-task attention weighting; inhibition-first framing (suppress before amplify) |
| M19 | [Memory Architecture](../modules/19_memory_architecture.md) | 7.5.0 | Four-tier memory (Tier 0–3), routing index, routing decision log, attempt ledger |
| M20 | [Permission Model](../modules/20_permission_model.md) | 7.1.0 | Risk tiers (LOW / MEDIUM / HIGH), capability gates, verifier + accretion candidate tier policies |
| M21 | [Knowledge Accretion](../modules/21_knowledge_accretion.md) | 7.5.0 | Cross-session knowledge persistence: compile-query-enhance loop, native:true gate, KB linter |
| M22 | [Semantic Wiki Search](../modules/22_semantic_wiki_search.md) | 7.4.0 | Two-phase retrieval (metadata pre-filter + score fusion), MemPalace integration, grep fallback |
| M23 | [Taxonomy Enforcement](../modules/23_taxonomy_enforcement.md) | 6.10.0 | Controlled vocabulary at write time: 15 domains, ~40 topics, ~55 approved tags |
| M24 | [Verbatim History Mining](../modules/24_verbatim_history_mining.md) | 6.6.0 | Tier 3 verbatim + MemPalace semantic retrieval; 96.6% R@5 (verbatim+semantic) |
| M25 | [Entity Relationship Analysis](../modules/25_entity_relationship_analysis.md) | 7.1.0 | ERA post-routing pass: entity graph, cardinality, coupling; entity → path-glob resolver |
| M26 | [KF-LOOP Substrate](../modules/26_kf_loop_substrate.md) | 1.2.0 | Iterative self-improvement loops — eight-stage orchestration primitive (cadence, gate, stratify, recall, reason, verify, act, observe); Wilson-CI gate; five loop instances |

---

## Notes

**M26 (KF-LOOP Substrate)** uses its own version sequence starting at 1.0.0 because it
was added after the rest of the system matured. All other modules version in the 6.x–7.x
range.

**Cross-cutting modules are always loaded** in Claude Code (via the always-on rules and
docs layer) and are uploaded as knowledge files in Claude Projects. They shape the
reasoning posture of every mode without requiring explicit activation.

**Mode-specific modules activate on demand** — the orchestrator routes to them when the
request matches their trigger signals.

For the full routing table and mode trigger signals, see `platforms/claude-code/` or
`platforms/claude-projects/06_Quick_Reference.md`.
