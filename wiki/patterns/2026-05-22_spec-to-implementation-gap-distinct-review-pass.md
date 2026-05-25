---
title: Spec-to-implementation gap as a distinct review category
source_mode: critic
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-22
domain: patterns
topic: validation
tags: quality-gate, grounding, adversarial
related_entries: ["2026-05-21_critic-verification-pass-second-pass-validation.md", "2026-05-13_verify-audit-claims-before-designing-fix.md"]
---

# Spec-to-implementation gap as a distinct review category

## The diagnostic

A specification can be internally consistent (multiple critic passes confirm self-consistency, cross-references resolve, no contradictions) AND describe behavior that no actual code implements. Spec-only review is necessary but not sufficient. The spec-vs-implementation diff is its own review pass.

## Concrete instance (knowledgeforge-core-8xq, Module 22 reconciliation)

Module 22 v7.3.0 spec described:
- Hook integration at `mempalace-wiki-mine.py` calling `tool_check_duplicate`
- Phase 1 Success Criteria: "Dup-check wired into accretion path"
- CC Doc imperative: "the hook MUST call tool_check_duplicate"

After 5 critic passes confirming spec internal consistency, a sixth-pass dragnet revealed: the hook had NO `tool_check_duplicate` call. The spec was reviewing as-if-implemented but reality was as-if-unimplemented. The Phase 1 Success Criteria were structurally unsatisfiable until the actual hook code landed.

The first 4 critic passes had focused on:
- Pass 1: structural defects in the spec
- Pass 2: cross-references to other spec modules
- Pass 3: multi-table dragnet within a quick-reference module
- Pass 4: reverse-direction references

All of these are SPEC-TO-SPEC consistency checks. None of them looked at the actual code that should satisfy the spec.

## When this applies

- After any multi-pass review of a spec where the spec describes integration with code (hooks, scripts, services)
- When a spec uses imperative "must call X" or "wires Y into Z" language
- Before declaring a spec "shipped" if there's a separate implementation phase
- When a spec carries Phase-N Success Criteria and those criteria depend on code that hasn't landed yet

## When this does NOT apply

- Specs that describe internal consistency only (no integration claims)
- Specs in early draft phase where deferral is already documented
- Specs that don't reference external systems or code artifacts

## How to run the check

1. Grep the spec for active-voice obligations: "must call", "wires", "extends", "modifies", "before/after X"
2. For each obligation, identify the target file/function/system
3. Read the target. Does the spec'd behavior actually exist in code?
4. If not — either implement now, or add an explicit Implementation Status section to the spec marking the obligation as pending
5. If deferring: reframe Success Criteria to explicitly mark them as "target state, NOT currently satisfied"

## Anti-pattern: relying on critic passes alone

Adversarial-critic agents read FILES. They can verify spec-to-spec consistency, cross-references, controlled-vocabulary compliance. They DO NOT execute code or verify behavior. If the spec describes integration that doesn't exist in the integration target, no number of spec-reading passes will catch it.

The fix is not "more critic passes" but "different review angle." Add a spec-to-implementation diff as a distinct verification step.

## Recovery pattern (what we did in knowledgeforge-core-8xq)

1. Added an explicit "Implementation Status" section to the spec — a table marking which Phase 1 components have landed vs are pending
2. Reframed Phase 1 Success Criteria as "target state, NOT currently satisfied"
3. Filed a separate bead for the implementation work (knowledgeforge-core-rk4) with dependency on the spec bead
4. Updated kf.yaml changelog to acknowledge the spec-to-implementation distinction

This preserved the value of the 5 prior critic passes (spec was made coherent) while honestly representing that the contract is the spec, not the deployed system.

## Reusable rule

For any spec that touches code:
- Spec consistency review (critic): N passes
- Spec-to-implementation diff (read the target code): 1 explicit pass
- Implementation status disclaimer: required if the implementation is deferred

The disclaimer prevents the spec from over-claiming what's live.

## Source Context

Identified during knowledgeforge-core-8xq Module 22 reconciliation (5th critic pass). The issue emerged when conducting a final dragnet for missing integration code — spec was passing all consistency checks but described behavior that hadn't been implemented. 

This discovery led to the realization that adversarial-critic agents have a structural blind spot: they verify spec-to-spec consistency excellently but cannot verify spec-to-code fidelity. A sixth review angle (implementation status audit) was needed to catch the gap.

Filed under `patterns/validation` per Module 23 controlled vocabulary. (Note: many wiki entries use a `methodologies` category that is not yet in Module 23 v6.5.2's approved domains. This entry uses the controlled vocabulary as-is.)
