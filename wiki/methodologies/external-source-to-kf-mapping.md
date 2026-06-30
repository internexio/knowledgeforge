---
title: External Source → KF Mapping (Practitioner-Guide-to-Spec Translation)
source_mode: expert_era
source_session: redacted
created: '2026-05-10T00:00:00Z'
date: '2026-05-10'
confidence: 0.75
grounding_score: 0.75
grounding_source: 'Stage 2 cascade — tool-calling-architecture-audit. Source: practitioner
  article

  "The Roadmap to Mastering Tool Calling in AI Agents" (7-step guide). Each step

  was mapped through KF abstractions (modes-as-tools, orchestrator-as-model,

  chains-as-tool-calls) to surface architecture-level gaps. Translation

  methodology generalized across 7 article principles → 9 KF patches.

  '
source_fingerprint: tool-calling-audit-track-c-era-3
novelty_type: transferable_framework
staleness_risk: low
importance: 4
pinned: true
accreted_in: 7.2.0
related:
- wiki/patterns/mode-variants-taxonomy.md
- wiki/diagnostics/handoff-payload-schema-gap.md
- wiki/architecture/scaffolding-vs-patching-pattern.md
- modules/25_entity_relationship_analysis.md
domain: methodologies
topic: decision-framework
---

# External Source → KF Mapping (Practitioner-Guide-to-Spec Translation)

## Methodology

When an external source (engineering article, paper, practitioner guide, frontier-provider documentation) describes a class of capability that KF does not natively express, run this translation pattern instead of either (a) ignoring the source or (b) copying it directly.

```
External principle  →  KF abstraction layer  →  Affected modules  →  Patches
```

Three steps, in order. Skipping any of them produces either superficial copying or missed insights.

---

## Step 1 — Identify the KF Abstraction

Most external sources describe their abstractions in the source's native vocabulary (e.g., "tool", "function", "agent"). The first translation step is to find the KF analogue — which is rarely 1:1.

| External vocabulary | KF analogue | Notes |
|---------------------|-------------|-------|
| "Tool" / "function" | Mode | Both are units the orchestrator dispatches to |
| "Tool definition" / "schema" | Module 04 spec template | Both define inputs/outputs/preconditions |
| "Tool call" | Mode activation + handoff | Both transfer control with payload |
| "Agent" (in tool-calling articles) | Orchestrator (Module 00) | The thing that decides which tool/mode |
| "Function-calling protocol" | Module 03 chain pattern + Module 04 handoff_contract | Both describe transfer semantics |

The asymmetry is informative: KF separates orchestrator (deciding) from coordination patterns (sequencing) from spec templates (typing) where frontier-native function-calling fuses them.

---

## Step 2 — Map Principle to Affected Modules

Once the abstraction is found, walk the source's principles through KF modules. For each principle, ask:

1. Which KF module owns this concern?
2. Is the concern formally expressed there, or is it a prose convention?
3. If prose-only, what's the structural gap?

Worked example (tool-calling article):

| Article principle | KF concern | Owning module | Status |
|-------------------|------------|---------------|--------|
| Tool definitions as contracts | Mode handoff payload schemas | Module 04 (template) + Module 03 (registry) | Prose-only → GAP |
| Decision type-aware reasoning | decision_type classification | Module 13 + Module 00 gate | Formal (since 6.6.1) |
| Variant-aware tool selection | Mode variants | Modules 05, 07 | Prose-only → GAP |
| Routing audit trail | Routing decision log | Module 19 | Missing → GAP |
| Selection accuracy as metric | Operational bound metric | Module 16 | Missing → GAP |

The "Status" column is the source of patches. "Formal" → no patch needed. "Prose-only" or "Missing" → patch.

---

## Step 3 — Surface KF-Native Differentiators

The point of mapping is not to copy the external source but to identify where KF abstractions provide capabilities the source doesn't. Frontier-native function-calling, for example, has:

- ✓ Native function schemas
- ✓ Native validation
- ✗ No decision-type-aware verification gates
- ✗ No reversibility classification
- ✗ No accretion check after evaluative+ output
- ✗ No variant-aware routing accuracy metric

The KF patches that close the gaps in steps 1–2 also provide the differentiators in step 3 *for free*, because they're built on top of existing KF infrastructure (decision types, reversibility, auto-verify gates, accretion). This is the defensibility thesis: closing a gap with KF-native semantics produces architectural depth that pure imitation cannot.

---

## When to Run

Apply this methodology when:

- A frontier provider ships a capability that "feels like" KF but isn't expressed in KF's vocabulary.
- An engineering article describes a class of pattern (testing patterns, evaluation harnesses, observability stacks) that overlaps KF concerns.
- Quarterly defensibility audits — compare KF orchestration vs. frontier-native orchestration capabilities.

Do **not** apply for:

- Tactical/implementation-detail external sources (specific library tutorials, debugging stories).
- Sources that map 1:1 to a single existing module (use direct module update instead).

---

## Yield Pattern

Article-to-KF mapping in this cascade produced:

- **7 ERA findings** from a 7-step practitioner guide (1 finding per principle, with structural reduction).
- **9 atomic patches** across 6 modules (sub-10 ceiling).
- **3 accretion candidates** (this entry, mode-variants-taxonomy, handoff-payload-schema-gap).
- **0 escalations** to user (clean cascade exit).

The pattern repeats: external sources tend to surface 1–2 structural gaps per principle. A 7-principle source produces ~5–10 findings; a 12-principle source ~10–18. Track C cascade ceiling (~10 atomic units) constrains scope at single-source granularity — a multi-source synthesis would need a separate compaction pass.

---

## Cross-Reference

This methodology is a generalization of the article-to-KF translation that produced this cascade. Future audits driven by external sources should reference this entry, follow the three-step pattern, and surface their findings in the same atomic-unit shape so they can be sequenced into Track C-equivalent cascades without re-discovering structure each time.
