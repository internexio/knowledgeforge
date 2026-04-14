# CW Drift Audit — knowledgeforge-cw vs knowledgeforge-core

**Date:** 2026-04-14
**Core version:** 7.0.0-alpha (modules sourced from CP 6.6.1)
**CW version:** 6.6.1
**Audited by:** Phase 0 inspection

---

## Summary

CW is at version parity (6.6.1) and is architecturally ahead of CC — it's already decomposed into agents + skills, which is what Phase 2 plans to do for CC. CW has two innovations not in core that should be upstreamed:

1. **Loop Exit Protocol** — prevents infinite Critic ↔ Builder loops; circuit breaker exemption
2. **ERA Domain adversarial checklist** — extends Module 25 with compound failure analysis

CW also carries COS-specific agents/skills that are intentionally out of core scope.

**Drift verdict:** Significant structural divergence (by design — CW is the decomposed format). Two upstream candidates.

---

## Architecture Comparison

| Dimension | Core / CP | CW |
|-----------|-----------|-----|
| Format | Monolithic module files | Decomposed: agents + skills |
| Orchestrator | Single CLAUDE.md / 00_orchestrator.md | Thin CLAUDE.md (6.6.1) |
| Modes | Inline in module specs | Separate `.claude/agents/*.md` |
| Cross-cutting | Inline in module specs | Separate `.claude/skills/*/SKILL.md` |
| Routing | CLAUDE.md table | Agent description-driven (CC-native) |
| Commands | — | `.claude/commands/` |

CW has already implemented the Phase 2 decomposition pattern. It should be the **reference implementation** for Phase 2.

---

## Agent Inventory (CW `.claude/agents/`)

| Agent | Core Equivalent | Notes |
|-------|----------------|-------|
| `adversarial-critic.md` | Part of Module 07 (auto-verification) | CW splits this out explicitly |
| `builder.md` | Module 02 | |
| `calibrator.md` | Module 11 | |
| `coordinator.md` | Module 03 | |
| `critic.md` | Module 07 | |
| `debugger.md` | Module 09 | |
| `expert.md` | Module 05 | |
| `knowledge-librarian.md` | Module 21 (accretion) | Explicit agent for wiki filing |
| `navigator.md` | Module 01 | |
| `strategist.md` | Module 10 | |
| `synthesizer.md` | Module 08 | |
| `cos-router.md` | ❌ CW/COS-specific | Not in core scope |
| `cos-science-advisor.md` | ❌ CW/COS-specific | Not in core scope |
| `mktg-campaign.md` | ❌ CW/COS-specific | Not in core scope |

**Gap:** CW has no direct equivalent of the `kf` orchestrator agent — the thin CLAUDE.md serves that role.

---

## Skill Inventory (CW `.claude/skills/`)

| Skill | Core Equivalent | Notes |
|-------|----------------|-------|
| `calibration-layer/` | Module 12 | |
| `coordination-patterns/` | Module 03 | |
| `decision-classification/` | Module 13 | |
| `era-domain/` | Module 25 | ⬆️ **Upstream candidate** — has adversarial checklist extension |
| `grounding-scores/` | Module 15 | |
| `knowledge-accretion/` | Module 21 | |
| `loop-exit-protocol/` | ❌ Not in core | ⬆️ **Upstream candidate** — novel protocol |
| `memory-architecture/` | Module 19 | |
| `metacognitive-monitor/` | Module 14 | |
| `operational-bounds/` | Module 16 | |
| `permission-model/` | Module 20 | |
| `quick-reference/` | Module 06 | |
| `salience-allocation/` | Module 18 | |
| `semantic-wiki-search/` | Module 22 | |
| `specification-templates/` | Module 04 | |
| `taxonomy-enforcement/` | Module 23 | |
| `temporal-knowledge/` | Module 17 | |
| `verbatim-history-mining/` | Module 24 | |
| `cos-bigfive/` | ❌ COS-specific | Not in core scope |
| `cos-case-studies/` | ❌ COS-specific | Not in core scope |
| `cos-engagement/` | ❌ COS-specific | Not in core scope |
| `cos-frames/` | ❌ COS-specific | Not in core scope |
| `mktg-orchestrator/` | ❌ COS-specific | Not in core scope |

---

## Upstream Candidates

### 1. Loop Exit Protocol (HIGH VALUE)

**Source:** `knowledgeforge-cw/.claude/skills/loop-exit-protocol/SKILL.md`
**Origin:** 6.6.1 ERA finding F1
**What it does:**
- Caps automatic Critic ↔ Builder loop at 1 revision cycle
- After one revision, persistent Sev 2+ findings → escalate to user with draft + options
- Explicitly exempts loop from the 3-failure circuit breaker (loop iterations are not failures)

**Where it should land in core:**
- Add to Module 07 (Critic) as a "Loop Exit Protocol" section
- Reference from Module 16 (Operational Bounds) — circuit breaker exemption
- Note in Module 03 (Coordination Patterns) — chain behavior

**Risk:** Low. Purely additive. Current core has no loop exit protocol; this fills a gap.

---

### 2. ERA Domain Adversarial Checklist (MEDIUM VALUE)

**Source:** `knowledgeforge-cw/.claude/skills/era-domain/SKILL.md`
**What it adds beyond Module 25:**
- Compound failures: hidden join paths, blast radius on relationship changes, cardinality violations at runtime, brittleness test
- Blast radius analysis specific to entity relationships
- Disambiguator: ERA triggers Expert → Builder chain; "what do these have in common" → Synthesizer

**Where it should land in core:**
- Merge into Module 25 (Entity Relationship Analysis) as an "Adversarial Checklist" section
- The module currently has the standard ERA protocol; this adds the adversarial depth layer

**Risk:** Low. Additive to existing module.

---

## Actions Required

| Priority | Action | Phase |
|----------|--------|-------|
| P1 | Use CW as reference implementation for Phase 2 decomposition | Phase 2 |
| P2 | Upstream Loop Exit Protocol into Module 07 (Critic) + Module 16 | Phase 4 |
| P2 | Upstream ERA adversarial checklist into Module 25 | Phase 4 |
| P3 | Review CW adversarial-critic agent split — consider explicit agent in CC | Phase 2 |
| P3 | Review knowledge-librarian agent — explicit accretion agent has value | Phase 2 |
