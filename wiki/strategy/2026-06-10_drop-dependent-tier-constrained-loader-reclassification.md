---
title: Drop the dependent tier when a critic surfaces that an architecture's loading mechanism is more constrained than the spec assumed
source_mode: strategist, critic
novelty_type: transferable_framework, reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-10
domain: strategy
topic: trade-off-analysis
tags: quality-gate, empirical, stable, adversarial, deployment
related_entries:
  - wiki/architecture/2026-05-20_platform-deprecation-architectural-intent-preservation.md
  - wiki/architecture/scaffolding-vs-patching-pattern.md
  - wiki/patterns/2026-06-10_mcp-tool-response-shape-live-verification-before-parsing.md
  - wiki/methodologies/2026-05-18_read-spec-heuristic-taxonomy-gate-iteration.md
---

# Drop the Dependent Tier When a Critic Surfaces an Architectural Loading Constraint

## Pattern

When a critic surfaces that an architecture's loading/dispatch/triggering mechanism is more constrained than the spec assumed, the cheapest correct move is usually to **DROP the dependent tier from the architecture** — not to patch around the constraint by building a new loader, polluting an existing one, or hand-waving about manual workarounds. Patching forward compounds the original misread; dropping forces honest reclassification of every artifact that was depending on the fictional tier.

## Concrete Grounding

**2026-06-10 — CLAUDE.md → rules/ migration for the user's Claude Code global config**

### v1 Strategist Plan: Three-Tier Architecture

- **Tier A:** `~/.claude/rules/*.md` (always-on, every turn)
- **Tier B:** `~/.claude/CLAUDE.md` residual (always-on, every turn)
- **Tier C:** `~/.claude/docs/lookup/*.md` (loaded on demand by KnowledgeForge's `kf-route.py` UserPromptSubmit hook)

The v1 plan migrated ~12KB of low-frequency reference content (API key inventory, infrastructure inventories, framework patterns) into Tier C on the assumption that the kf-route loader would pull them in when relevant.

### v1 Critic Finding (Verified Live)

`~/.claude/hooks/kf-route.py`'s loader has a hard-coded `MODULE_MAP` of 13 KF compiled modules (`12_calibration_layer.md`…`24_verbatim_history_mining.md`). There is **NO** directory scan of `~/.claude/docs/lookup/` or any other path. Files placed in `docs/lookup/` would be dormant on disk — invisible to Claude unless an explicit `Read` was issued.

### Three Options on the Table

- **A) Drop Tier C:** re-classify every "→ lookup/" cell into STAY (justify always-on cost), ARCHIVE (user's private reference, NOT auto-loaded), or DELETE (genuine dead weight). Honest about what the system actually does. Cost: re-plan, ~30 min.

- **B) Build a new loader:** extend kf-route.py with a directory scan + topic match. Substantial scope (~hours), changes a tested KF component, blocks migration on upstream/downstream coordination.

- **C) Shoehorn into MODULE_MAP:** add lookup files as faux KF modules. Pollutes KF compiler invariants, creates false equivalence between user-content and KF-compiled-content, drift risk.

v2 strategist chose **A**. The plan kept the same effort estimate (~3h total) — savings from dropping Tier C reinvested in (a) honest re-classification, (b) breadcrumbs back to archive paths, (c) canary verification of project-local rules. CLAUDE.md size reduction estimate fell from v1's ~68% to v2's honest ~37% (actual delivered: 35%, very close to estimate).

## Why Dropping Is Usually Right

1. **The misread compounds:** Patching forward presumes the design intent of the constrained mechanism. Often the constraint exists for a reason (kf-route's MODULE_MAP is hard-coded because KF modules are version-locked; dynamic loading would break compiler invariants). Building around the constraint without understanding the WHY tends to break the why.

2. **Honest classification is durable:** Once each artifact has been re-classified as "must-always-load" vs "occasional reference" vs "delete," the architecture stays clean even if future loaders get built. The classifications are not wasted work.

3. **Cost asymmetry favors drop:** Dropping is typically 10x cheaper than building. Patching is typically 5x cheaper than building but leaves debt. Drop pays now; patch pays later.

## When Dropping Is the Wrong Move

- The dependent tier is genuinely load-bearing and there's no "always-on" alternative big enough to absorb the content (e.g., when CLAUDE.md is already over its size cap).
- The constraint is a bug, not a design choice — patching forward fixes the bug while delivering the feature.
- The cost of the missing tier is asymmetric — one undiscovered edge case has unbounded blast radius.

## Diagnostic Signal

A spec or proposal that:

- Mentions a load-on-demand mechanism in passing
- Cites it as the reason a tier "doesn't pay always-on cost"
- Does NOT show evidence of having read the loader source

**Always read the loader's source before committing to a plan that depends on it.** Same energy as "verify the premise before filing a defensive bead" but applied to the architecture-spec stage. This is the critical gate that prevents the v1 → v2 rework cycle.

## When This Applies

- Evaluating a proposed multi-tier architecture where one tier relies on a load-on-demand mechanism
- Conducting an architecture review and encountering a tier whose loading contract is "implicit" or "assumed"
- Diagnosing scope creep in a planned migration that introduced new tiers
- Making strategic choices between three unattractive options (drop / build / shoehorn) when a constraint surfaces

## When This Does NOT Apply

- The loader is tested and its source is known to support the required loading pattern
- The constraint is transient (temporary lack of a feature; platform has stated the feature is coming)
- The cost of loading all tier content always-on is negligible (< 10% memory / latency impact)

## Related Entries

- [[platform-deprecation-architectural-intent-preservation]] — similar family: when a platform mechanism changes, separate intent from syntax. This entry separates intent from loading availability.
- [[mcp-tool-response-shape-live-verification-before-parsing]] — same family of "verify the integration surface before depending on its shape." That entry covers reading the responder; this one covers reading the loader.
- [[verify-premise-before-defensive-bead]] (conceptual) — the universal "read full context" rule applied to architectural premises.
- [[scaffolding-vs-patching-pattern]] — this entry is a specialization of that pattern: when a tier is scaffolded around a fictional loading capability, dropping the tier is the patching move.

## Source Context

Grounded in CLAUDE.md → rules/ migration v1→v2 pivot (2026-06-10). A strategist and critic pass over a planned config restructuring uncovered that a critical load-on-demand tier had no viable loader. The decision to drop rather than patch is a reusable framework for handling similar constraint-discovery moments.
