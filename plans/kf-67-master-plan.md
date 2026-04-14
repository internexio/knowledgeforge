# KF 6.7 Integration Master Plan

**Source:** AI Tinkerers Research 2026-04-13 | 6 repos + 7 URLs
**Plan version:** 1.0

---

## Scope

This plan sequences all integration work identified across six project-specific plans into a single implementation roadmap. It resolves cross-project dependencies, assigns version targets, and identifies the critical path.

---

## Change Inventory by Module

| Module | Changes | Source Projects |
|--------|---------|-----------------|
| **02 Builder** | Pre-registration git protocol, `@alias` debiasing (research) | AI Research Skills, BAML |
| **03 Coordination** | Dual fingerprinting for Critic↔Builder loop, plugin slot validation (accretion) | Agent Orchestrator |
| **07 Critic** | Boundary scoring for severity classification | BAML |
| **08 Synthesizer** | Two-loop research architecture (inner/outer), CONCLUDE criteria | AI Research Skills |
| **09 Debugger** | Reproduce-before-fix mandatory step, CI failure feedback loop | Background Agents, Agent Orchestrator |
| **12 Calibration** | SAP-inspired structured output cascade, cross-provider judge isolation, trajectory tracking | BAML, Orchestra, AI Research Skills |
| **14 Metacognitive Monitor** | Stop hook completion gate, PostToolUse edit-count nudge, command-level scoped hooks, PostToolUse metadata bus | Hooks-mastery, Orchestra, Agent Orchestrator |
| **16 Operational Bounds** | Reaction engine (subsumes circuit breakers), pure decision functions | Agent Orchestrator, Background Agents |
| **17 Temporal Knowledge** | Research staleness gate, PreCompact transcript backup | Orchestra, Hooks-mastery |
| **19 Memory Architecture** | PreCompact/PostCompact survival chain, SessionStart silent injection, `$CLAUDE_ENV_FILE` persistence | Orchestra, Hooks-mastery |
| **20 Permission Model** | PermissionRequest input mutation | Hooks-mastery |
| **21 Knowledge Accretion** | Monitor generation from diffs, artifact-embedded dedup, terminal state concept | Background Agents, AI Research Skills |
| **Navigator (01)** | Lazy command dispatch (all modes), routing table augmentation | Orchestra, AI Research Skills |

---

## Dependency Graph

```
                    ┌─────────────────────────────┐
                    │  FOUNDATION LAYER            │
                    │  (must land first)           │
                    │                              │
                    │  .kf/ directory structure    │
                    │  PreCompact/PostCompact hooks│
                    │  SessionStart injection      │
                    └──────────┬──────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
   ┌────────────────┐ ┌───────────────┐ ┌────────────────┐
   │ ENFORCEMENT    │ │ OBSERVATION   │ │ SPEC UPDATES   │
   │                │ │               │ │ (no code deps) │
   │ Stop gate      │ │ Edit-count    │ │                │
   │ Permission     │ │ nudge         │ │ Reproduce-     │
   │ mutation       │ │ Metadata bus  │ │ before-fix     │
   │ Scoped hooks   │ │ Transcript    │ │ Boundary       │
   └────────┬───────┘ │ backup        │ │ scoring        │
            │         └───────┬───────┘ │ Cross-provider │
            │                 │         │ judge           │
            │                 │         │ Dual            │
            │                 │         │ fingerprinting  │
            │                 │         └────────┬───────┘
            │                 │                  │
            └─────────────────┼──────────────────┘
                              │
                              ▼
                    ┌─────────────────────────────┐
                    │  ARCHITECTURAL CHANGES       │
                    │  (larger effort, more risk)  │
                    │                              │
                    │  Reaction engine (M16)       │
                    │  Two-loop synthesis (M08)    │
                    │  Pure decision functions     │
                    │  Lazy command dispatch       │
                    │  SAP output cascade (M12)    │
                    └─────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Foundation (KF 6.7.0-alpha) — ~8 hours

These create the `.kf/` state infrastructure that everything else builds on.

| # | Change | Module | Effort | Source |
|---|--------|--------|--------|--------|
| 1 | `.kf/` directory structure + state file formats | 19 | 1h | All |
| 2 | PreCompact/PostCompact survival chain | 19 | 4h | Orchestra |
| 3 | SessionStart silent injection | 19 | 1h | Orchestra, Hooks |
| 4 | `$CLAUDE_ENV_FILE` session vars | 19 | 30m | Hooks |
| 5 | PreCompact transcript backup | 17 | 1h | Hooks |

**Validation gate:** Fresh Claude Code session → work for 20+ turns → trigger compaction → verify state survives → resume work without re-prompting.

---

### Phase 2: Enforcement + Observation (KF 6.7.0-beta) — ~12 hours

These add the mandatory quality enforcement and passive observation layers.

| # | Change | Module | Effort | Source |
|---|--------|--------|--------|--------|
| 6 | Stop hook completion gate with mode checklists | 14 | 4h | Hooks |
| 7 | PermissionRequest input mutation | 20 | 3h | Hooks |
| 8 | PostToolUse edit-count nudge | 14 | 2h | Orchestra |
| 9 | Command-level scoped hooks | 14 | 2h | Hooks |
| 10 | PostToolUse metadata bus | 14 | 3h | Agent Orchestrator |

**Validation gate:** Builder mode activated → produce spec → attempt to stop with missing PDIA elements → blocked → complete spec → allowed to stop.

**Depends on:** Phase 1 (`.kf/state/active_mode` file from SessionStart injection).

---

### Phase 3: Spec Updates (KF 6.7.0-rc) — ~8 hours

No code dependencies. Pure spec changes that can land in parallel with Phases 1-2.

| # | Change | Module | Effort | Source |
|---|--------|--------|--------|--------|
| 11 | Reproduce-before-fix mandatory step | 09 | 1h | Background Agents |
| 12 | Cross-provider judge isolation | 12 | 1h | Orchestra |
| 13 | Boundary scoring for severity | 07 | 2h | BAML |
| 14 | Dual fingerprinting for Critic↔Builder | 03 | 2h | Agent Orchestrator |
| 15 | Research staleness gate | 17 | 2h | Orchestra |
| 16 | Artifact-embedded dedup | 21 | 2h | Background Agents |
| 17 | Terminal state concept | 21 | 1h | AI Research Skills |
| 18 | Pre-registration git protocol | 02 | 2h | AI Research Skills |
| 19 | CI failure feedback loop pattern | 09 | 2h | Agent Orchestrator |

**Validation gate:** Critic review of updated module specs for internal consistency.

---

### Phase 4: Architectural Changes (KF 6.8.0) — ~25 hours

Larger structural changes with higher risk. Deferred to 6.8 to keep 6.7 focused.

| # | Change | Module | Effort | Risk | Source |
|---|--------|--------|--------|------|--------|
| 20 | Reaction engine (subsumes circuit breakers) | 16 | 6h | Medium | Agent Orchestrator |
| 21 | Two-loop synthesis architecture | 08 | 4h | Low | AI Research Skills |
| 22 | Pure decision functions for operational logic | 16 | 4h | Medium | Background Agents |
| 23 | SAP-inspired structured output cascade | 12 | 4h | Medium | BAML |
| 24 | Lazy command dispatch (all mode agents) | 01, all | 12h | High | Orchestra |
| 25 | Monitor generation from code diffs | 21 | 3h | Low | Background Agents |

**Validation gate:** Full KF pipeline verification — mode chain (Builder → Critic → Builder) with all new infrastructure active. Regression check against existing mode quality.

---

### Phase 5: Research Items (KF 6.9+) — effort TBD

Items requiring empirical testing before spec commitment.

| # | Change | Module | Prerequisite | Source |
|---|--------|--------|-------------|--------|
| 26 | `@alias` debiasing for decision classification | 02 | Measurement of current classification bias | BAML |
| 27 | Trajectory tracking + Karpathy plots | 12 | Active benchmarking program | AI Research Skills |
| 28 | Routing table augmentation | 01 | Routing accuracy data from production use | AI Research Skills |
| 29 | Declarative resilience patterns | 16 | Autonomous deployment architecture | BAML |
| 30 | Durable Objects session architecture | Infra | Multi-tenant hosting decision | Background Agents |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Stop hook infinite loop (broken `stop_hook_active` guard) | Medium | High (blocks all sessions) | Test with intentional incomplete output; verify guard fires |
| PostCompact over-injection re-triggers compaction | Medium | High (compaction loop) | Hard token budget on PostCompact output; test with near-full context |
| Lazy dispatch misroutes due to thin router | Medium | Medium (wrong mode activated) | A/B test: current vs lazy dispatch on 20 representative prompts |
| Reaction engine auto-escalates too aggressively | Low | Medium (unnecessary user interruptions) | Conservative defaults: auto=false for new reactions; opt-in |
| Edit-count nudge is ignored despite tool-response injection | Low | Low (agents skip tool responses less than prompt) | Monitor adoption rate; adjust threshold if needed |

---

## Cross-Cutting Principle

The single most transferable insight across all sources: **reproduce before fix, triage before act, deterministic before LLM.** This trio should become a KF meta-principle alongside the existing "patch weaknesses, don't scaffold strengths."

**Proposed addition to Agent Instructions static zone:**
```
Meta-principle: Deterministic first. Before invoking LLM judgment,
exhaust deterministic checks (structural validation, pattern matching,
state comparison). Before fixing, reproduce. Before acting, triage.
```

---

## Accretion Candidates Summary

| ID | Target | Tier | Status |
|----|--------|------|--------|
| ACCRETION_01 | wiki/hooks/stop-hook-completion-gate.md | T1 | Implement in Phase 2 |
| ACCRETION_02 | wiki/memory/compaction-survival-hooks.md | T1 | Implement in Phase 1 |
| ACCRETION_03 | wiki/calibration/schema-aligned-parsing.md | T2 | Phase 4 |
| ACCRETION_04 | wiki/builder/lazy-command-dispatch.md | T2 | Phase 4 |
| ACCRETION_05 | wiki/calibration/eval-methodology.md | T1 | Phase 3 |
| ACCRETION_06 | wiki/coordination/reaction-engine.md | T2 | Phase 4 |
| ACCRETION_07 | wiki/debugger/reproduce-before-fix.md | T1 | Phase 3 |
| ACCRETION_08 | wiki/synthesizer/two-loop-research.md | T2 | Phase 4 |
| ACCRETION_09 | wiki/memory/session-start-context-injection.md | T1 | Phase 1 |
| ACCRETION_10 | wiki/accretion/artifact-embedded-state.md | T2 | Phase 3 |

---

## Version Targets

| Version | Content | Estimated Effort |
|---------|---------|-----------------|
| **6.7.0** | Phases 1-3: Hook infrastructure + enforcement + spec updates | ~28 hours |
| **6.8.0** | Phase 4: Architectural changes (reaction engine, two-loop, lazy dispatch) | ~25 hours |
| **6.9.0+** | Phase 5: Research items requiring empirical validation | TBD |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Compaction survival rate | 100% of routing state preserved | Test across 10 compaction events |
| Stop gate enforcement | 0 incomplete outputs bypass gate | Audit 20 Builder + Critic sessions |
| Edit-count nudge adoption | >80% of nudges result in checkpoint within 3 edits | Log analysis |
| Reproduce-before-fix compliance | 100% of Debugger outputs include reproduction_status | Critic review |
| Adversarial verification yield | >20% of auto-verify passes surface actionable issues | Calibration tracking |
