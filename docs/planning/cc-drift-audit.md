# CC Drift Audit — knowledgeforge-cc vs knowledgeforge-core

**Date:** 2026-04-14
**Core version:** 7.0.0-alpha (modules sourced from CP 6.6.1)
**CC version:** 6.6.1
**Audited by:** Phase 0 automated diff + inspection

---

## Summary

CC is at version parity (6.6.1) but has one missing module and uses the original CP filename conventions (not the lowercase standardized names used in core). No improvements in CC to upstream — CC is a subset of CP.

**Drift verdict:** Minor. CC is mostly current. One module gap, one naming convention difference.

---

## File Inventory

| Status | CC File | Core Equivalent | Notes |
|--------|---------|----------------|-------|
| ✅ Present | `00_Agent_Instructions.md` | `00_orchestrator.md` | Same content, different name |
| ✅ Present | `01_Navigator_Agent.md` | `01_navigator.md` | |
| ✅ Present | `02_Builder_Agent.md` | `02_builder.md` | |
| ✅ Present | `03_Coordination_Patterns.md` | `03_coordination_patterns.md` | |
| ✅ Present | `04_Specification_Templates.md` | `04_specification_templates.md` | |
| ✅ Present | `05_Expert_Agent_Example.md` | `05_expert_agent.md` | |
| ✅ Present | `06_Quick_Reference.md` | `06_quick_reference.md` | |
| ✅ Present | `07_Critic_Agent.md` | `07_critic_agent.md` | |
| ✅ Present | `08_Synthesizer_Agent.md` | `08_synthesizer_agent.md` | |
| ✅ Present | `09_Debugger_Agent.md` | `09_debugger_agent.md` | |
| ✅ Present | `10_Strategist_Agent.md` | `10_strategist_agent.md` | |
| ✅ Present | `11_Calibrator_Agent.md` | `11_calibrator_agent.md` | |
| ✅ Present | `12_Calibration_Layer.md` | `12_calibration_layer.md` | |
| ✅ Present | `13_Decision_Classification.md` | `13_decision_classification.md` | |
| ✅ Present | `14_Metacognitive_Monitor.md` | `14_metacognitive_monitor.md` | |
| ✅ Present | `15_Grounding_Scores.md` | `15_grounding_scores.md` | |
| ✅ Present | `16_Operational_Bounds.md` | `16_operational_bounds.md` | |
| ✅ Present | `17_Temporal_Knowledge.md` | `17_temporal_knowledge.md` | |
| ✅ Present | `18_Salience_Allocation.md` | `18_salience_allocation.md` | |
| ✅ Present | `19_Memory_Architecture.md` | `19_memory_architecture.md` | |
| ✅ Present | `20_Permission_Model.md` | `20_permission_model.md` | |
| ✅ Present | `21_Knowledge_Accretion.md` | `21_knowledge_accretion.md` | |
| ✅ Present | `22_Semantic_Wiki_Search.md` | `22_semantic_wiki_search.md` | |
| ✅ Present | `23_Taxonomy_Enforcement.md` | `23_taxonomy_enforcement.md` | |
| ✅ Present | `24_Verbatim_History_Mining.md` | `24_verbatim_history_mining.md` | |
| ❌ **Missing** | — | `25_entity_relationship_analysis.md` | ERA module not in CC |
| ➕ CC-only | `README.md` | — | Module index (not a module spec) |
| ➕ CC-only | `wiki/architecture/` | — | Accreted wiki (same as core) |

---

## Gaps

### Module 25 Missing (ERA)

**File:** `25_Entity_Relationship_Analysis.md`
**Impact:** ERA routing (`"Map entity relationships"`, `"audit module dependencies"`) will fall through to Expert without ERA domain context.
**Fix:** Copy `modules/25_entity_relationship_analysis.md` from core into `docs/knowledgeforge/25_Entity_Relationship_Analysis.md` in CC. Low risk.

---

## Naming Convention Drift

CC uses original CP naming (PascalCase with `_Agent` suffixes). Core standardized to lowercase with underscores. This is a presentation-only difference — CC works fine. When Phase 2 (decomposition) runs on CC, the new skills/docs will use the standardized names.

**No action needed now.** Tracked as a known difference.

---

## Upstream Opportunities

None. CC has no content improvements over core. CC is a subset of CP with one module missing.

---

## Actions Required

| Priority | Action | Owner |
|----------|--------|-------|
| P2 | Copy ERA module (25) to CC docs | Phase 2 prep |
| P3 | Normalize filenames during Phase 2 decomposition | Phase 2 |
