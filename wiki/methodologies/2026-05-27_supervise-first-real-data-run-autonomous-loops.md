---
title: Supervise the first real-data run before letting an autonomous loop go overnight
source_mode: strategist
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.75
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-27
domain: strategy
topic: risk-assessment
tags: quality-gate, scheduling, token-cost
related_entries: []
---

# Supervise the First Real-Data Run Before Letting an Autonomous Loop Go Overnight

## Pattern

When extending a proven autonomous-overnight loop to a new phase that touches real money, production APIs, or real customer data, do NOT queue that phase for autonomous overnight execution on its first run. Supervise the first real-data run yourself, then hand it to the autonomous loop from cycle 2 onward.

## Concrete Grounding (Autonomous Overnight Cycle, 2026-05-27)

An autonomous overnight Claude Code session had just proven the loop works: it built a validation harness end-to-end against SYNTHETIC fixtures, closed 6 beads, and spent $0.12 against a $5 budget. The next phase (Phase 0b) would run the same harness against REAL ad accounts — real Google Ads API pulls, real customer performance data, and per-ad LLM scoring (10-100x the cost of the synthetic phase).

The strategic call: unblock the phase today (provision the API key, populate the real-account fixtures) but do NOT let the autonomous overnight session execute it on first contact. Instead, the operator supervises the first real-account run (watching spend + output quality), and only after that succeeds does the autonomous loop take over at scale from cycle 2 onward.

## Why This Matters

The synthetic-fixture success proves the CODE works; it does not prove the loop behaves safely against real-world data volume, cost, or edge cases. First real contact is exactly where cost blowups, data-exposure mistakes, and silent-garbage outputs happen — and those are precisely the failures an unsupervised overnight run cannot catch in time to prevent damage.

## When This Applies

- Any autonomous loop transitioning from synthetic/sandbox to real-money / real-customer-data / production-API for the first time
- When the blast radius of a failure includes financial loss or customer data exposure
- When the loop's internal cost meters or quality gates have not been validated against real-world data volume yet

## When This Does NOT Apply

- Subsequent runs after a supervised first run has validated cost + output quality
- Phases that remain fully sandboxed (no real spend, no real data)
- Autonomous fixes to internal-only systems where failure recovery cost is low

## Companion Guardrails Observed in the Same Session

**Set a hard per-session budget cap** when the work touches paid APIs (e.g., $20/account on first run, abort on overage). Cost meters detect overage after it happens; budget caps prevent the overage from accruing in the first place.

**Verify the loop is read-only** against the real data source before the first run if the work does not require writes. A read-only loop cannot corrupt customer data even if output quality is poor.

**Prime the idle queue with low-risk work** if you cannot give tonight's session the high-value work yet. An idle autonomous queue is worse than no queue — if you cannot give tonight's session the high-value work yet (because it needs supervision), prime it with low-risk maintenance work instead of letting it idle or, worse, inventing noise.

## Anti-Pattern to Watch: "Cycle Addiction"

Once an autonomous loop is proven, every problem starts looking like "let's autonomously fix it overnight." The tell is reaching to autonomously execute a task that is actually a 5-minute human decision or that touches unvalidated real-world surface. Resist; file a bead and supervise instead.

## Source Context

Session: `autonomous-overnight-cycle-2026-05-27`. A [project] iteration-loop autonomous session (Phase 0a, synthetic) had completed successfully. Phase 0b (real Google Ads data) was unblocked but deferred from autonomous execution pending operator supervision of the first run. The pattern emerged from the explicit decision to *unblock but defer execution* — a deliberate two-stage handoff that separates code-correctness validation (synthetic phase, autonomous) from real-world cost/quality validation (real phase, supervised first, then autonomous).
