---
title: Terse-by-design — orchestrators add overhead only when patching known LLM failure modes
date: 2026-05-18
domain: strategy
topic: scope-management
tags: [token-cost, routing, quality-gate]
type: pattern
status: stable
grounding_score: 0.92
staleness_risk: stable
importance: 4
pinned: true
novelty_type: new_pattern
source_mode: synthesizer
created: 2026-05-18
related_entries:
  - wiki/architecture/scaffolding-vs-patching-pattern.md
  - wiki/architecture/neuro-symbolic-pattern-validation.md
---

# Terse-by-design — Orchestrators Add Overhead Only When Patching Known LLM Failure Modes

## What

When designing an orchestrator prompt (CLAUDE.md, agent system prompt, routing skill), do not scaffold the LLM's existing strengths. Add framework overhead only when it prevents a *known* failure mode: skipping hypotheses, hiding trade-offs, missing gaps, over-engineering simple problems.

Most user requests need *no* mode activation. The orchestrator's job is to recognize the small subset that does, route them correctly, and stay out of the way for everything else.

## Why This Matters

Orchestrator overhead has a real cost:

- **Every line of CLAUDE.md is loaded on every turn** — bloated orchestrators degrade tool-selection reasoning by stealing the model's attention budget.
- **"Style-in-the-orchestrator" patterns** (answering *in the style of* a mode from the main session) double-process every request and produce verbose, ceremonial output where a one-line answer would do.
- **More framework ≠ better reasoning.** The marginal CLAUDE.md line is more likely to dilute than improve quality past ~5K tokens.

Token cost compounds across multi-turn sessions. A 10K-token orchestrator adds 1.5–2% token drag per turn (Haiku mode). Over 200 turns, that's 2–3 wasted full-context windows.

## Heuristic for the Cut

For each candidate section in your orchestrator, ask:

**What specific Claude failure mode does this section prevent?**

If the answer is "none — it scaffolds something Claude already does," cut it. Examples of failure modes worth scaffolding:

| Failure Mode | Scaffolding |
|--------------|-------------|
| Skipping hypothesis generation in debugging | Debugger protocol's Phase 1–3 sequence |
| Hiding trade-offs in design recommendations | Strategist's explicit trade-off table requirement |
| Missing adversarial gaps in self-review | Critic auto-verification at end of evaluative+ chains |
| Over-engineering simple yes/no questions | Decision classification (Reckoning vs. Evaluative) |
| Reckonings padded with multi-paragraph reasoning | Ozymandias Test: flag 5+ paragraph answers to yes/no questions |
| Orphaned session state from prior turns | Temporal reset protocol (mark stale context at turn start) |

## Practical Thresholds (KF 7.0 Reference Implementation)

- **Thin orchestrator target:** 5–8K tokens. KF 7.0 ships at 3,346 tokens. Below 5K is fine if every section earns its place.
- **Decomposition pattern:** Move mode protocols to skill files loaded on demand (`.claude/skills/<framework>/<mode>.md`). Move cross-cutting rules to numbered docs (`docs/<framework>/NN_*.md`). Routing-only logic stays always-loaded.
- **Always-loaded vs on-demand:** Only the meta-principle + decision classification quick-reference stay always-loaded. Mode protocols are loaded by the hook-driven router when relevant.

### Concrete Reduction Example (KF 7.0→7.1)

- Initial draft monolithic CLAUDE.md: ~30K tokens (would have been "complete" by checklist standards)
- Final thin orchestrator: 3,346 tokens (~89% reduction)
- All 9 mode protocols moved to `.claude/skills/kf/*.md` (loaded on demand by `UserPromptSubmit` hook)
- Cross-cutting rules moved to `docs/knowledgeforge/NN_*.md`
- Builder + Critic adversarial passes both confirmed: no missing functionality; the cut is real reduction, not deferral

## Anti-Patterns

| Anti-Pattern | Effect | Correct Approach |
|---|---|---|
| **Style-in-the-orchestrator** | Double-process every request; confused identity | Route to skill, don't answer "as Critic would" in main session |
| **Always-on mode rules** | Every mode's full protocol in CLAUDE.md; bloats every turn | Load mode protocols on demand via router |
| **Defensive checklists** | Sections that say "before answering, check X, Y, Z" for things Claude already does | Remove; Claude doesn't need permission to be smart |
| **"It might help" additions** | Nice-to-have sections with no documented failure mode | Hard cut — no marginal benefit is worth 10 extra tokens per turn |
| **Mode scaffolding instead of patching** | Building a "Debugger persona" to address missed hypotheses (always-on) | Build a conditional hypothesis-injection patch that triggers only on detection |

## Decision Classification as Terse-by-Design Example

The **Ozymandias Test** is a canonical success:

> **If a yes/no question needs multi-paragraph reasoning, it's not a reckoning. Upgrade.**

This single rule eliminates ~30% of verbose non-routing output. It's:
- Testable: look at the answer structure
- Failure-mode specific: prevents "over-engineered simple problems"
- Always-on but doesn't bloat: adds 1 line to the orchestrator
- Actionable: triggers immediate mode route or clarification

Contrast this with "always explain your reasoning" (bloats every answer) or "be concise" (vague, doesn't change behavior).

## When This Applies

- **Designing a new CLAUDE.md or system prompt** — apply the failure-mode heuristic before adding any section
- **Reviewing bloated orchestrators** — use the cut protocol: "What failure mode does this prevent?" If none, remove it
- **Multi-turn session degradation** — if model performance drops after 50+ turns, orchestrator token bloat is a likely culprit; measure and prune
- **Onboarding contributors to a framework** — teach via this entry + the KF meta-principle; prevents "let's add more rules" scope creep

## When This Does NOT Apply

- **Initial exploration phase** — when failure modes are unknown, scaffolding to learn is acceptable; extract and compress once patterns stabilize
- **Safety-critical systems** — where defensive checklists prevent catastrophic failures (safety gates > terse code)
- **Single-turn interactions** — token cost is less acute; focus on correctness over brevity

## Source Context

Grounded in the KF 7.0 → 7.1 refactor completed 2026-05-18. The monolithic CLAUDE.md draft (initial ~30K tokens) attempted to be "complete" — every mode rule, every cross-cutting guideline, always-loaded. The thin orchestrator cut it by 89%, moving protocols to on-demand skill files and cross-cutting rules to numbered docs. All functionality preserved; token cost crushed.

Builder + Critic adversarial passes confirmed the reduction is real (no missing scaffolding for genuine failure modes), not a deferral of important rules.

## Related

- `wiki/architecture/scaffolding-vs-patching-pattern.md` — the parent principle; this entry applies it to orchestrator design
- `wiki/architecture/neuro-symbolic-pattern-validation.md` — validates that symbolic structure (framework) should exist only where neural (LLM) execution fails
- KF 7.0 meta-principle in `CLAUDE.md` — "patch weaknesses, don't scaffold strengths"
- Module 21 (Knowledge Accretion) — novelty classification filters out reckonings + routine outputs; terse-by-design lets the filter work
- Module 19 (Memory Architecture) — token budget telemetry surfaces orchestrator bloat over time
