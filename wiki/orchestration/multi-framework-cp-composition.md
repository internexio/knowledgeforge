---
title: Three-Framework CP Composition Template
source_mode: synthesizer
source_session: redacted
created: '2026-04-21T00:00:00Z'
date: '2026-04-21'
confidence: 0.9
grounding_score: 0.9
grounding_source: VisionForge Unified composition chain (chain-log/00 through 06-accretion-candidates.md).
  ERA identified 6 implicit contracts, 5 coupling hotspots, 6 failure modes before
  first bundle file written. Adversarial Critic found 13 wrong Leonardo filenames
  — a finding that would have been Step 4 if ERA had included filename verification.
novelty_type: transferable_framework
staleness_risk: stable
importance: 4
pinned: false
accreted_in: '6.5'
related:
- wiki/orchestration/kf-version-gap-bridging.md
- wiki/orchestration/adversarial-filename-audit.md
- wiki/orchestration/schema-first-elicitation-order.md
- wiki/infrastructure/flat-namespace-prefix-convention.md
- modules/25_era.md
- modules/02_builder.md
- modules/07_critic_agent.md
- modules/10_strategist.md
---

# Three-Framework CP Composition Template

## Pattern

When composing 3+ independent Claude Project knowledge bundles into a unified bundle — where frameworks have different version lineages, different frontmatter conventions, and at least one shared backbone that all others depend on — run this fixed step order before emitting any bundle file:

1. **Source inventory** — version, entry point, file count, frontmatter convention, integration contracts for each framework
2. **ERA** — map cross-framework overlaps, implicit contracts, cardinality conflicts; classify entities as genuine duplicate / partial overlap / net-new gap
3. **Module census** — classify every source module as `core`, `adapter`, `duplicate`, `obsolete`, or `gap`; identify gap modules absent from all sources
4. **Strategist decisions** — resolve architectural ambiguities before Builder emits anything; document decision type and reversibility
5. **Builder emit** — write bundle files only after steps 1–4 are on disk
6. **Adversarial Critic** — assume at least one significant flaw; run explicit filename verification against actual disk state

**Applicability:** Three or more frameworks with different version lineages, different frontmatter conventions, and at least one shared backbone framework that all others depend on. Conditions: (a) one framework is the routing backbone, (b) at least one downstream framework was built against an older backbone version, (c) target environment imposes structural constraints (flat files, no MCP at runtime).

---

## Why ERA Is the Critical Gate

ERA (step 2) prevents discovering mid-build that two frameworks share an entity with incompatible confidence semantics or cardinality assumptions.

The COS→Leonardo OCEAN handoff looks clean at inventory level: COS produces OCEAN profiles, Leonardo consumes them. ERA reveals the confidence cardinality mismatch — COS operates at high-confidence inference mode, Leonardo L02 explicitly marks its OCEAN-to-visual crosswalk as hypothesis-grade. Without ERA, the `confidence` field is absent from the handoff artifact and FLUX prompts are generated from stacked low-confidence hypotheses with no user signal. The pipeline completes; output is silently degraded.

**Do the ERA pass even when overlaps seem obvious.**

---

## Anti-Pattern — "Inventory and Build"

Skip ERA, go directly from inventory to emitting files. In VisionForge: the COS→Leonardo OCEAN handoff looked clean at inventory level. ERA revealed the confidence cardinality mismatch. Without ERA, the `confidence` field is absent from the handoff artifact and FLUX prompts are generated from stacked low-confidence hypotheses with no user signal. The pipeline completes; output is silently degraded.

---

## Evidence from VisionForge

- ERA identified 6 implicit contracts (C1–C6), 5 coupling hotspots (H1–H5), and 6 adversarial failure modes (F1–F6) before a single bundle file was written
- Strategist resolved all 6 architectural decisions using ERA findings as direct inputs
- Adversarial Critic found 13 wrong Leonardo filenames in CLAUDE.md — a Step 6 finding that would have been Step 4 if filename verification had been added to the ERA pass checklist

---

## Reuse Context

Reference this entry when:
- Composing any 3+ framework knowledge bundle targeting a Claude Project
- Evaluating whether an ERA pass is "worth it" before a bundle build — evidence says yes every time
- Designing the chain-log structure for a new composition project (the 7-step structure is the reusable artifact)
- Any environment where: one framework is routing backbone, at least one downstream built against older backbone version, target environment imposes structural constraints (flat files, no MCP at runtime)
