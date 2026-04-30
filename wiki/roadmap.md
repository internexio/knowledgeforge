---
type: roadmap
scope: project
domain: ""
status: active
horizon: Q2-2026
last_reviewed: 2026-04-30
half_life_days: 30
linked_vision_version: 1
linked_wiki_entries: []
---

# Project Roadmap

## Horizon Goal

Complete Phase 7 architectural changes and ship the web agents variant (Phase 8), closing the gap between hook-driven Claude Code routing and full multi-model orchestration via the web agents API.

---

## Phases

### Phase 7: Architectural Changes
**Status:** in_progress
**Depends on:** none (Phases 0–6 complete)
**Knowledge prerequisites:** none
**Outcome:** Reaction engine spec live in Module 16; two-loop synthesis architecture in Module 08; lazy dispatch decision documented (adopt or close); command-level scoped hooks for key modes in Module 14; monitor generation from module diffs in Module 21.
**Accretion note:** Reaction engine design rationale, two-loop synthesis patterns, lazy dispatch decision (and the reasoning that drove it).

---

### Phase 7b: Vision + Roadmap System
**Status:** in_progress
**Depends on:** none
**Knowledge prerequisites:** none
**Outcome:** `wiki/vision.md` and `wiki/roadmap.md` exist as project artifacts; `/kf-vision` and `/kf-roadmap` commands live in `knowledgeforge-cw`; M17 staleness integration, M21 phase-completion trigger, and M14 drift detection spec-complete in `knowledgeforge-core`.
**Accretion note:** File the vision/roadmap format spec as a wiki pattern (domain: orchestration, topic: planning-artifacts) for use when setting up new projects.

---

### Phase 8: Web Agents Variant
**Status:** ready
**Depends on:** Phase 7
**Knowledge prerequisites:** none
**Outcome:** FastAPI application (`knowledgeforge-web/`) serving all KF modes via OpenRouter; per-step multi-model routing working; cross-model judge isolation verified; COS integration endpoint live.
**Accretion note:** Multi-model routing patterns, per-step model selection heuristics, OpenRouter fallback chain design, latency vs. cost trade-off data from real runs.

---

## Deferred / Parking Lot

- **Phase 9 (Research Ingestion Pipeline)** — deferred until Phase 8 complete; pipeline processes packages via the web agents API which doesn't exist yet
- **Phase 10 (Evaluation Framework)** — deferred; requires multi-model baseline from Phase 8 to be meaningful
- **CORE_SYNC_TOKEN setup** — deferred; needed to activate GitHub Actions compile workflows for all three sync targets

## Revision Log

| Date | Change | Trigger |
|------|--------|---------|
| 2026-04-30 | Initial creation | Proof-of-format seed for vision/roadmap system |
