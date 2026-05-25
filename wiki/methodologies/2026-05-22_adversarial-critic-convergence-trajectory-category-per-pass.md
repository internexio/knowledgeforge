---
title: Adversarial-critic convergence trajectory — each pass uncovers a new CATEGORY of error
source_mode: critic
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-22
domain: methodologies
topic: prioritization
tags: quality-gate, adversarial, empirical, orchestration
related_entries:
  - methodologies/2026-05-21_critic-verification-pass-second-pass-validation.md
  - methodologies/2026-05-13_critic-triage-routing-strategist-vs-defer-doc.md
---

# Adversarial-critic convergence trajectory: each pass uncovers a new CATEGORY

## The pattern

When running an adversarial-critic in iterative passes against the same artifact (spec, plan, design), each pass surfaces a NEW CATEGORY of error, not the same category at finer detail. Convergence in spirit happens after the major categories are exhausted, but the critic's "assume a flaw exists" bias means it will continue to surface progressively more obscure issues. Knowing the category-per-pass progression helps decide when to accept "good enough" and ship vs continue polishing.

## Concrete trajectory observed (knowledgeforge-core-8xq, Module 22 reconciliation, 6 passes)

| Pass | Findings | Category |
|---|---|---|
| 1 | 5 sev-2+ | Structural / scope: CLI gap, wing derivation, unachievable success criterion, vague wing inference, M21+M23 cross-refs |
| 2 | 3 sev-2+ | Stale Phase-2-as-current cross-refs in M00 and M25; M21 CC Doc Gate 4b describing blocking gate; KnowledgeGraph SQLite open at import time |
| 3 | 2 sev-2+ | Multi-table dragnet — M06 had 3 more rows stale beyond the one fixed; `except Exception` insufficient for argparse SystemExit |
| 4 | 1 sev-2+ + 2 self-found | Reverse-direction refs — non-M22 modules describing capabilities REQUIRING M22 Phase 2 |
| 5 | 1 sev-2+ | Spec-to-implementation gap — 6+ passes reviewed only spec artifacts; never compared spec against actual hook code |
| 6 | 2 sev-2+ | Residual Implementation Status disclaimer scope; bead-state-trust assumption |

The categories are distinct:
- Pass 1: structural (the spec itself is wrong in big ways)
- Pass 2: cross-references (other modules reference the changed module's behavior)
- Pass 3: multi-table dragnet (same file has multiple lists referencing the same concept)
- Pass 4: reverse-direction refs (modules describing capabilities that DEPEND on the changed module's contract)
- Pass 5: spec-to-implementation gap (spec ≠ code)
- Pass 6: disclaimer scope / bead-state trust (finishing-touches)

After Pass 6, the chain is in finishing-touches territory. Continuing would find wording mismatches between table cells, slight inconsistencies in how Phase 1 vs Phase 2 is described in different sections, etc. — diminishing returns.

## When to apply

- Multi-pass adversarial review of any spec / plan / architecture document
- Cross-module reconciliation efforts where the changed module affects many siblings
- Decision: "how many critic passes is enough?"

## When NOT to apply

- Single-pass code review with a clear scope — adversarial-critic finds bugs against well-defined criteria, not the iterative discovery pattern
- Small/local edits to a single file with no cross-references — usually one pass suffices
- Time-sensitive ship-or-fail decisions — accept the trade-off explicitly; convergence is not a hard requirement

## Decision rule for stopping

Stop when the next pass would find ONLY:
- Wording inconsistencies between sibling tables
- Stylistic mismatches (verbose vs concise)
- Finishing-touch wording issues that don't change behavior

These are signal that the chain has reached "convergence in spirit." Adversarial critic will keep finding things forever because it's biased to do so; the human (or orchestrator) must call convergence.

## Empirical convergence trajectory

Findings per pass: 5 → 3 → 2 → 1+2 → 1 → 2. The 1+2 in pass 4 included self-dragnet finds AFTER the critic's findings, suggesting the orchestrator was learning the categories and pre-empting the critic. By pass 6, the critic was finding finishing-touch issues like "the disclaimer in section X doesn't propagate to section Y 80 lines below."

## Anti-pattern: treating critic convergence as required

The adversarial-critic is INSTRUCTED to assume a flaw exists ("Reports severity 2+ findings only. Bias toward surfacing, not soothing."). It will never naturally return zero findings unless explicitly told it's a convergence check. Treating "zero findings" as the stopping criterion produces indefinite polishing.

## When This Applies

- Multi-pass adversarial review of any spec / plan / architecture document
- Cross-module reconciliation efforts where the changed module affects many siblings
- Decision: "how many critic passes is enough?"

## When This Does NOT Apply

- Single-pass code review with a clear scope
- Small/local edits to a single file with no cross-references
- Time-sensitive ship-or-fail decisions where convergence cannot be required

## Source Context

Extracted from knowledgeforge-core-8xq Module 22 reconciliation session (6 critic passes spanning May 21–22, 2026). The pattern emerged during the closure of structural findings and became distinct enough to generalize. Predecessor pattern: [Critic verification pass](methodologies/2026-05-21_critic-verification-pass-second-pass-validation.md) — which this entry complements by providing a framework for deciding WHEN to stop the iteration cycle.
