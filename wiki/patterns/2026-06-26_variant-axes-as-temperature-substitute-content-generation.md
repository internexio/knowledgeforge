---
title: Variant axes as a temperature-substitute for content generation without sampling control
source_mode: builder
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.7
staleness_risk: stable
importance: 3
pinned: false
created: 2026-06-26
tags: [agent-workflow, content-generation, prompt-engineering, skill-design, variation]
related_entries:
  - patterns/mode-variants-taxonomy.md
  - diagnostics/2026-05-18_vary-input-smoke-runs-llm-failure-modes.md
  - diagnostics/2026-06-17_ai-fingerprint-patterns-seven-recurring-tells-marketing-prose.md
domain: patterns
topic: synthesis
---

# Variant axes as a temperature-substitute for content generation without sampling control

## Pattern

When an agent skill generates copy and the user requests "higher temperature," "less generic," or "non-formulaic" output, but the agent has no direct sampling-temperature control, generate N≥2 explicit angle variants with distinct hook patterns instead of attempting within-draft variation.

## Concrete instantiation

A multi-platform social-broadcast skill (`/social-post` in `client-project`) was asked to produce "high temperature" copy. The skill spec mandates **2 variants per platform** on explicit, named axes:

- **Variant A — Confessional / problem-first.** Opens with a problem the reader has lived through. Earns Stage 1 trust by surfacing the failure mode before the methodology.
- **Variant B — Methodology-led / contrarian.** Opens with the counterintuitive claim or specific evidence. Leads with the moat / data point / structural insight.

The two-variant rule forces variation that single-draft "be creative" or "vary the style" instructions don't reliably produce. The user gets meaningful choice (different reader personalities respond to different hooks) rather than two slightly-different versions of the same draft. A de-AI scrub pass then applies to both variants independently.

## Why this works

- "Higher temperature" within a single draft is implicit — the agent has no honest way to do it without sampling control.
- Explicit angle axes (e.g., "Confessional vs Methodology-led") are concrete and produceable. The agent reasons its way to two different drafts because the axes describe genuinely different framings, not styling tweaks.
- The variants compound under downstream selection: the user picks the better one for their audience, eliminating the "two-mediocre-versions" failure mode of pure rerolls.

## When it applies

- Content generation workflows where the agent cannot tune temperature directly (no API-level sampling control exposed).
- Skills that produce copy intended for downstream human selection.
- Workflows where the user signals "make it varied" / "not boilerplate" / "less AI-feeling."
- Multi-platform broadcast packs where each variant can also map to a different audience personality (High-A reader vs High-C reader).

## When it does NOT apply

- Single-output tasks (the user wants ONE answer, not options).
- Deterministic outputs (API specifications, configuration files, type signatures) — variants would be linguistic noise.
- Workflows where adversarial-vs-defensive paired generation is the explicit pattern (different shape, similar surface).

## Implementation contract for skills using this pattern

1. Name the axes explicitly in the skill spec (not "vary the angle" — name the axes).
2. Mandate N=2 minimum. Three is allowed if a clear third axis exists; four is rarely earned.
3. Apply the same downstream gates (de-AI scrub, COS critique, fact-check) to each variant independently.
4. Deliver all variants — do not pre-select. Surface in the chat as labeled fenced blocks for easy comparison.

## Grounding

Implemented in `/social-post` skill at `.claude/skills/social-cross-post/SKILL.md` in the client-project project, session 2026-06-26. First live invocation generated an 8-variant pack (4 platforms × 2 axes) from a single source blog post. The two variants per platform were meaningfully distinct in opening frame, and one variant per platform was marked "recommended primary" based on audience-fit reasoning. Pack committed at `wiki/outbound/social_drafts/2026-06-26_b2b-buying-committees-4-personality-types/` and pushed in commit `d41762b`.
