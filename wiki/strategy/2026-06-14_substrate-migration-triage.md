---
title: Substrate-migration triage — port/drop a dormant subsystem's backlog against the live substitute, never revive the corpse
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.90
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-14
domain: strategy
topic: trade-off-analysis
tags: triage, backlog, deprecation, decision-framework
related_entries:
  - wiki/methodologies/2026-05-29_dormant-subsystem-forensics-check-supervision-first.md
  - wiki/strategy/2026-06-10_drop-dependent-tier-constrained-loader-reclassification.md
  - wiki/architecture/2026-05-20_platform-deprecation-architectural-intent-preservation.md
  - wiki/methodologies/2026-05-23_salvage-vs-revert-mid-execution-conflict-framework.md
---

# Substrate-migration triage

**Pattern.** When a subsystem goes dormant but a *live* system already serves the same goal, do NOT revive the dead one to honor its backlog. Triage the dead subsystem's open work against the live substitute.

**Trigger.** You're about to build/clear a backlog item and discover (via verify-first: is the pipeline actually scheduled/running?) that its host subsystem is dormant — no schedule, stale logs, never produced output recently.

**Classify each backlog item:**
- **PORT** — idea is sound, only the substrate moved → re-home to the live system (preserve the full spec; hand to that system's owner).
- **DROP** — the live system already does it, or the item's *form* (e.g. a dead dashboard) is obsolete → close, don't port.
- **SUBSTRATE-INDEPENDENT** — infra/policy that applies regardless of host → keep but re-point its consumer.
- **KEEP-in-place** — only if reviving the dead subsystem is *independently* justified (rare; the live substitute usually moots it).

**Rules.**
1. Verify dormancy before disposition (don't assume from the bead text).
2. Preserve each item's spec in its close-reason — the close-reason is the anti-loss mechanism.
3. Hand keepers to the live system's owner; do a duplication-check against the live system FIRST (it may already do several).
4. Do not re-file keepers in the dead system's tracker.

**Anti-pattern — "reviving the corpse":** rescheduling a dead pipeline just to clear its backlog. It re-creates the original failure mode (e.g. the noise pile the backlog item existed to clean up) and spreads maintenance across a substrate nobody uses.

**Worked instance (2026-06-14).** [project] *Lookout* (reddit/social opportunity-scoring → bead pipeline) was dormant (orchestra-to-beads bridge last ran 2026-03-19). *moltbot* — the live COS-GTM engagement agent — covers the same ICP + platforms and already has reddit/linkedin prospect DBs. 7 Lookout feature beads triaged: 6 PORT→moltbot (lead-scoring, COS OCEAN profiling, engagement tracking, LinkedIn monitor, prospect→networking link, MemoryRouter accretion), 1 DROP (Telegram summary — redundant with moltbot's daily digest). Specs preserved in close-reasons + a port-backlog doc in moltbot's repo. Counterpoint in the same session: [project] *site-monitor* health checks were ALSO dormant but had no live substitute + clear ongoing value (paying-client uptime) → that one was REVIVED (health-only), not ported. The deciding question is always "does a live system already serve this goal?"

## Cross-References

- [[dormant-subsystem-forensics-check-supervision-first]] — pairs upstream: that entry diagnoses *why* a subsystem went dormant; this entry decides *what to do with its backlog* once dormancy is confirmed.
- [[drop-dependent-tier-constrained-loader-reclassification]] — same drop/port/patch decision-framework family applied at the architectural-tier scale; this entry applies it at the subsystem-backlog scale.
- [[platform-deprecation-architectural-intent-preservation]] — port-intent-across-substrates cousin; that entry ports across platform versions, this one ports across subsystems in the same operator's stack.
- [[salvage-vs-revert-mid-execution-conflict-framework]] — sibling triage framework for mid-execution conflicts; the disposition vocabulary (salvage/revert vs port/drop/keep) is related.

## Source Context

Grounded in the 2026-06-14 [project] session where Lookout's backlog was triaged against moltbot. Orchestra artifact `art_03ec9480` routed the candidate to KF-core via mini-claude. Cross-refs: [project]-d3yg (the revive case — site-monitor), [project]-gyc6 (the drop case — Telegram summary), [project]-0za4 (the KF-core dirty-clone routing blocker mini flagged that caused this entry to be filed via direct-mode rather than mini's local clone).
