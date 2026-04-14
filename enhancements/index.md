# KF Enhancement Specs — Batch 1
**Source:** Analysis of "7 AI Skills Employers Can't Find" (Nate, YouTube 4cuT-LKcmWs)
**Date:** 2026-04-14
**Status:** Proposed

## Overview

Seven enhancements derived from mapping external AI job-market skill taxonomy against KF 6.5.
All gaps are input-side guards or output-side precision checks — areas where KF's routing and
structure are strong but validation of premises and output type is weak.

## Enhancement Index

| # | File | Mode Affected | Priority | Effort |
|---|------|--------------|----------|--------|
| 1 | [enh-001-sycophantic-guard.md](enh-001-sycophantic-guard.md) | Builder, Expert | P0 | Low |
| 2 | [enh-002-functional-correctness.md](enh-002-functional-correctness.md) | Critic | P0 | Low |
| 3 | [enh-003-harness-sizing.md](enh-003-harness-sizing.md) | Coordinator | P1 | Medium |
| 4 | [enh-004-token-economics-preflight.md](enh-004-token-economics-preflight.md) | Orchestrator | P1 | Medium |
| 5 | [enh-005-blast-radius-checklist.md](enh-005-blast-radius-checklist.md) | Expert | P2 | Low |
| 6 | [enh-006-spec-drift-checkpoint.md](enh-006-spec-drift-checkpoint.md) | Coordinator | P2 | Medium |
| 7 | [enh-007-context-hygiene.md](enh-007-context-hygiene.md) | Calibrator | P3 | Low |

## Implementation Order

**Phase 1 (prompt-level only, no logic change needed):**
- ENH-001: Sycophantic guard — add assumption flag to Builder/Expert prompts
- ENH-002: Functional correctness — add one line to adversarial Critic framing
- ENH-005: Blast radius checklist — add structured template to Expert HIGH-tier outputs

**Phase 2 (routing logic change):**
- ENH-003: Harness sizing — add pre-check step to Coordinator mode
- ENH-004: Token economics pre-flight — add gate before 3+ mode chains

**Phase 3 (checkpoint / compaction integration):**
- ENH-006: Spec drift — add mid-chain spec re-validation trigger
- ENH-007: Context hygiene — add dirty data audit to Calibrator setup checklist

## Design Principle

These enhancements patch input-side blind spots. KF currently validates structure and routes
correctly — but doesn't validate the premises that structure runs on. An agent that builds
correctly on bad assumptions produces a silent failure. These specs close that gap.
