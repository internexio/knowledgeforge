---
title: Adaptive gate_window floor for sparse multi-axis Wilson-CI strata
source_mode: builder
novelty_type: reusable_diagnostic
grounding_score: 0.65
staleness_risk: stable
importance: 3
pinned: false
created: 2026-08-13
domain: orchestration
topic: queue-pattern
tags: quality-gate, grounding, scheduling, chain, stable
related_entries: []
---

# Adaptive gate_window floor for sparse multi-axis Wilson-CI strata

## Problem

When a Wilson-CI gate operates on a multi-dimensional stratification axis, the number of possible strata can be large (e.g., claim_type × source_corpus = 3 × 5 = 15 strata). A fixed gate_window (e.g., 20) is infeasible for most strata because they will never accumulate enough observations for the Wilson-CI confidence interval to be meaningful. With n < 8 observations, the 95% CI spans nearly the full [0, 1] range — the gate output is noise, not signal.

## Solution: Adaptive gate_window floor

Apply a three-tier adaptive gate_window based on observed n (sample count) for the stratified axis value:

- **n < 8:** unconditional WAIT. Do not compute Wilson-CI. The interval is too wide to support any gate decision. Accumulate more evidence.
- **8 ≤ n < 20:** reduced window. Use n as the effective window. Wilson-CI output is advisory — treat DIAGNOSE with lower confidence, do not auto-PROMOTE.
- **n ≥ 20:** standard gate_window. Full Wilson-CI semantics apply.

The threshold n=8 is the practical minimum for Wilson-CI to produce intervals narrow enough to distinguish WAIT from DIAGNOSE at 95% confidence (at n=8 with all successes, ci_lower ~= 0.63; at n=8 with 7/8, ci_lower ~= 0.53).

## When This Applies

Any iterative loop that uses Wilson-CI gating AND stratifies on a composite or high-cardinality axis. First application: kf-loop-cos-grounding (claim_type × source_corpus = 15 possible strata).

## When This Does NOT Apply

- Single-axis stratification with low cardinality (≤ 5 values)
- Loops where all strata are guaranteed to accumulate n ≥ 20 before gate evaluation
- Non-Wilson-CI gates (threshold gates, saturation gates)

## Anti-patterns

- **Fixed gate_window regardless of stratum density:** spurious DIAGNOSE/WAIT for sparse strata
- **n_minimum too high:** collapses all sparse strata into permanent WAIT
- **Skipping sparse strata entirely:** leaves unaddressed failures in loop's blind spot

## Source Context

Derived during kf-loop-cos-grounding spec authoring (2026-08-13, knowledgeforge-core). Sev 2 adversarial finding: two-axis stratification produces 15 strata; gate_window=20 infeasible for most. Wilson-CI small-sample behavior verified analytically.
