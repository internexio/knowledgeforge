---
title: Phased probe-first arc for risky multi-spec refactors (Probe → ERA → Strategist → Builder → Critic → Phase 3)
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.9
staleness_risk: stable
importance: 4
created: 2026-06-14
domain: methodologies
topic: deployment-sequencing
tags: [adversarial, quality-gate, chain]
related_entries:
  - orchestration/2026-06-12_parallel-spec-parallel-critic-pattern-independent-beads.md
  - methodologies/2026-05-22_adversarial-critic-convergence-trajectory-category-per-pass.md
  - methodologies/2026-05-29_deterministic-first-debugging.md
pinned: false
---

# Phased Probe-First Arc for Risky Multi-Spec Refactors

## Problem Shape

When a single change touches 3+ modules with cross-spec runtime dependencies AND novel-judgment artifacts (new sub-policies, new gate semantics, new contracts), going straight to implementation produces avoidable rework. Symptoms: spec gaps caught only at impl time, line-number drift between spec and code, cross-spec ordering bugs, adversarial findings that should have surfaced earlier.

## Pattern

Run the refactor as a 4-phase chain with **human gates** at each boundary:

1. **Phase 0 — Read-only probe.** Enumerate every file the spec will touch. Verify current state matches spec assumptions (line numbers, section names, version strings, existing contracts). No writes. Output: probe report + adversarial findings on the probe itself. **Gate: confirm probe accuracy before Phase 1.**

2. **Phase 1 — ERA (Entity Relationship Analysis).** Build the entity graph for the change. Map which modules reference what, which contracts break, which gates survive. Surface hidden couplings *before* designing the fix. Output: ERA artifact + adversarial findings. **Gate.**

3. **Phase 2 — Builder produces locked specs.** Each spec PDIA-formatted, decision-tagged (reckoning / evaluative / predictive / novel), followed by an auto-adversarial-critic pass. Apply `loop_exit_protocol` cycle 1 (max=1); persistent Sev2+ escalates. Multi-spec refactors author all specs in the same phase. Output: locked specs ready to commit. **Gate: spec-commit (terminal deliverable, human approval).**

4. **Phase 3 — Implementation.** Out of scope until Phase 2 gate clears. One change per submission, read-only probe first per change, atomic-commit boundaries within each PR.

## When This Applies

- Refactor touches 3+ modules with cross-spec runtime dependencies
- At least one decision in the change is novel-judgment territory
- Implementation cost would exceed redesign cost if architectural mistakes surface late
- The architectural shape is not yet evidence-grounded (probe is needed to verify assumptions)
- The work crosses repo boundaries (e.g., core → cc derived variant)

## When This Does NOT Apply

- Single-module bug fix where root cause is already grounded
- Single-file refactor with small dependency surface
- Adding one config field with no contract implications
- Routine cc back-port / compile-output regeneration
- Pure cleanup work (e.g., quoting fix across N modules — covered by `loop_exit_protocol` directly without phasing)

## Grounding

KF-core loop-engineering integration session (2026-06-13/14) ran this arc end-to-end on three specs (SPEC 1 verifier promotion, SPEC 4 vetting gate, SPEC 5 plugin packaging). Outcome: 7 core commits + 3 cc PR merges with zero unplanned conflict-rebase or scope-recovery work. Adversarial findings at Phase 2 surfaced 10 Sev2+ issues that would have become impl-time defects if discovered later. Revision cycle 1 absorbed all of them; `loop_exit_protocol` max=1 was never exceeded.

## Source Context

This pattern codifies what the existing Module 00 chain syntax (`@expert → @strategist → @builder → AUTO: @critic (adversarial)`) implies, but adds the explicit phase-gate semantics that the bare chain syntax doesn't enforce. Pairs with `loop_exit_protocol` (Module 07) for revision-cycle bounds.
