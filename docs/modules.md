# KnowledgeForge — Module Reference

27 modules (M00–M26). Versions read from `modules/NN_*.md` source files.

**Mode-specific modules** implement a reasoning mode (M01–M11).
**Cross-cutting modules** apply across all modes; they don't implement a single mode
but shape how every mode reasons, remembers, and bounds itself (M12–M26).

---

## Mode-Specific Modules (M00–M11)

| # | Module | Version | Purpose |
|---|--------|---------|---------|
| M00 | Orchestrator | 7.25.0 | Agent identity, decision classification, mode routing, mode chaining, adversarial verification |
| M01 | Navigator | 7.1.0 | Ambiguity detection and resolution — fires only on genuine ambiguity |
| M02 | Builder | 7.0.1 | Spec and implementation generation (PDIA method: Purpose → Design → Implementation → Assessment) |
| M03 | Coordination Patterns | 7.6.0 | Multi-agent workflow design, Handoff Contract Registry (13 contracts), dual fingerprinting |
| M04 | Specification Templates | 7.4.0 | Reusable spec formats, trigger disambiguators, upstream_invalidation field |
| M05 | Expert Agent | 7.4.0 | Deep analysis with adversarial depth (5 variants: regular / infra / ml-infra / era / research) |
| M06 | Quick Reference | 7.3.0 | Routing table, signal guide, mode variants taxonomy, integration flows |
| M07 | Critic Agent | 7.6.0 | Review, validation, audit (4 variants: regular / linter / audit / adversarial); comms variant via COS MCP |
| M08 | Synthesizer Agent | 6.8.0 | Pattern extraction, abstraction, anti-patterns; comms-domain emit |
| M09 | Debugger Agent | 7.0.2 | Hypothesis-driven root-cause diagnosis; requires >0.8 confidence before declaring root cause |
| M10 | Strategist Agent | 6.5.0 | Trade-off evaluation, reversibility assessment, sequencing; never recommends "do everything" |
| M11 | Calibrator Agent | 7.2.0 | Complexity-appropriate AI coder configuration (CLAUDE.md, .cursorrules, etc.) |

---

## Cross-Cutting Infrastructure Modules (M12–M26)

| # | Module | Version | Purpose |
|---|--------|---------|---------|
| M12 | Calibration Layer | 7.0.2 | Multi-pass evaluation, cross-provider judge isolation, SAP-inspired structured output parsing cascade |
| M13 | Decision Classification | 6.5.0 | Reckoning / evaluative / predictive / novel — the Ozymandias Test |
| M14 | Metacognitive Monitor | 6.7.0 | Acute failure detection: loops, context overflow, confidence collapse, iteration scope |
| M15 | Grounding Scores | 6.5.0 | Knowledge trust 0.0–1.0; accretion gate (≥0.6 to file); degraded ceiling at WebSearch fallback |
| M16 | Operational Bounds | 7.3.1 | Circuit breakers, resource limits, mode-selection accuracy metric (9 variants, ≥90% overall) |
| M17 | Temporal Knowledge | 7.0.2 | Knowledge age, importance-weighted decay, domain half-life table, planning artifact staleness |
| M18 | Salience Allocation | 7.1.0 | Multi-task attention weighting; inhibition-first framing (suppress before amplify) |
| M19 | Memory Architecture | 7.5.0 | Four-tier memory (Tier 0–3), routing index, routing decision log, attempt ledger |
| M20 | Permission Model | 7.1.0 | Risk tiers (LOW / MEDIUM / HIGH), capability gates, verifier + accretion candidate tier policies |
| M21 | Knowledge Accretion | 7.5.0 | Cross-session knowledge persistence: compile-query-enhance loop, native:true gate, KB linter |
| M22 | Semantic Wiki Search | 7.4.0 | Two-phase retrieval (metadata pre-filter + score fusion), MemPalace integration, grep fallback |
| M23 | Taxonomy Enforcement | 6.10.0 | Controlled vocabulary at write time: 15 domains, ~40 topics, ~55 approved tags |
| M24 | Verbatim History Mining | 6.6.0 | Tier 3 verbatim + MemPalace semantic retrieval; 96.6% R@5 (verbatim+semantic) |
| M25 | Entity Relationship Analysis | 7.1.0 | ERA post-routing pass: entity graph, cardinality, coupling; entity → path-glob resolver |
| M26 | KF-LOOP Substrate | 1.2.0 | Iterative self-improvement loops — eight-stage orchestration primitive (cadence, gate, stratify, recall, reason, verify, act, observe); Wilson-CI gate; five loop instances |

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
