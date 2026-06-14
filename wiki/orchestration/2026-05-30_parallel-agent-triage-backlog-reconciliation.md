---
title: Parallel-agent triage for backlog reconciliation
source_mode: kf-coordinator, kf-strategist
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 4
domain: patterns
topic: orchestration
tags: [delegation, routing, quality-gate, throughput, empirical]
related_entries:
  - orchestration/context-manager-protocol.md
  - methodologies/2026-05-24_probe-before-chain-reconciliation.md
  - methodologies/2026-05-16_upstream-noise-flood-bulk-close-source-pointer.md
created: 2026-05-30
pinned: false
---

# Parallel-Agent Triage for Backlog Reconciliation

## The Pattern

When a backlog (issue tracker, TODO list, bug queue) has accumulated ≥10 open items written days/weeks/months ago as forward plans, many of them describe work that has since shipped, been re-scoped, or become obsolete. Going through them serially costs 15–30 min/item (premise verification + read + classify) — most of which is wasted on already-done items.

Instead: spawn ⌈N/8⌉ parallel general-purpose agents, each given ~8 items and instructed to:
1. Read the item (issue body + acceptance + notes).
2. Identify the concrete artifact the item claims to need (function, route, table, UI, doc).
3. grep / read the codebase to determine whether that artifact already exists.
4. Classify with file:line evidence into discrete buckets (SHIPPED, OPEN, NEEDS-SPEC, READY-TO-BUILD, AMBIGUOUS).
5. Return a structured per-item report (one block per item, ~50 words each).

The orchestrator aggregates, auto-closes the clearly-shipped ones with the agent's evidence, files draft proposals for the ambiguous ones, and surfaces the rest for human decision.

## Why Parallel Beats Serial

- Most items are read-only investigations until classification is done. Parallel agents don't conflict.
- Reading the codebase is the time-dominant step. Splitting N items across ⌈N/8⌉ agents cuts wall-clock to roughly 1 agent's serial run.
- The agent's narrow context (just its 8 items) reduces context-pressure compared to one orchestrator doing all N.
- Per-item evidence cited as file:line is verifiable post-hoc; the orchestrator doesn't need to re-investigate.

## Concrete Uses (This Session)

### Use 1: 30-Bead Backlog Reconciliation

- **Setup:** 30 open beads at start of session, accumulated from weeks of prior sessions.
- **Approach:** 3 parallel general-purpose agents, ~10 beads each (backend/infra, frontend/bugs, site/SEO/planning groupings).
- **Results:** 6 confirmed SHIPPED (auto-closed with file:line reasons), 2 BC/EC epics re-scoped to frontend-only (backends found shipped), 3 planning beads narrowed (strategy docs resolved most intent). Net: ~16 of 30 items either closed or materially shortened in one pass.
- **Wall-clock:** ~30 min of triage time (agents ran in ~12 min in parallel; aggregation + bd mutations took the rest).

### Use 2: cos-moh BC/EC Router Parity Semantic Scan

- **Setup:** A single bead claiming "router parity scan" between two ~1000-line Python routers. The structural scan (grep for symbol counts) found "no clear duplication." The original premise was about router-level RunResource/CohortResource patterns.
- **Approach:** 1 deep general-purpose agent doing a semantic scan across both routers + their orchestrator/persistence modules.
- **Results:** Original premise was wrong (route shapes look alike, lifecycles differ — no actionable router-level duplication). The ACTUAL duplication lives one layer down in the blindspot subsystem: 3 HIGH-severity drift items (enum case mismatch BC vs EC, parse/validate trio with silent analysis-min-length drift, near-identical call-with-parse-retry wrapper). Filed as 2 follow-up refactor beads with concrete file:line evidence.
- **Insight:** Even when the original framing is wrong, the agent surfaces a sharper actual finding.

## Tuning

- **Beads per agent:** ~8 is good. <5 wastes parallelism overhead; >12 starts to overwhelm context and report quality drops.
- **Cap parallel agents:** 4 max. More risks runaway and worse log readability.
- **Prompt template length:** Tight (≤600 words). Long prompts get worse classifications because the agent's instructions compete with the codebase reads.
- **Output format:** Strict per-item block. Free-form summaries at the end of an agent's report are unreliable — better to aggregate from the structured blocks.

## When To Apply

- ≥10 open items in a backlog written days+ ago.
- After time away (returning to a project).
- Before any major planning session (clear stale before deciding what to build).
- Periodic hygiene (weekly/monthly).

## When NOT to Apply

- Backlogs <5 items (overhead exceeds benefit; do it serially).
- Items requiring runtime / browser / external-system verification (agents can't do this headless).
- Items in domains the agents don't have context for (e.g., specific to a third-party product with no codebase signal).

## Anti-Patterns

- Using one agent serially for 30 items: loses ~3× wall-clock improvement.
- Asking agents to "summarize" rather than classify into a fixed taxonomy: produces unstructured prose that's hard to act on.
- Auto-closing without file:line evidence: looks fast but creates a "rebuilt-because-someone-closed-as-shipped-but-it-wasn't" failure mode. Always require evidence in the close reason.
- Spawning >4 parallel agents: log readability collapses, debugging becomes painful.

## Integration with bd / Native Issue Trackers

The orchestrator should:
- Auto-close SHIPPED items with evidence-rich `--reason` strings (auditable, reversible).
- File new refactor/follow-up beads for sub-findings (don't try to fit everything in the original bead's close-reason).
- Add `bd dep add` calls when the agent surfaces dependencies between items.
- Leave AMBIGUOUS items open with a "scan-could-not-classify: <reason>" note (so a human can pick up where the agent gave up).

## When This Applies

Specific conditions where this pattern is useful:

- A backlog has accumulated ≥10+ items from earlier sessions or planning phases
- Most items are describable as concrete artifacts (functions, routes, docs) that can be detected via grep/code-read
- Parallel investigation doesn't conflict (items are read-only during classification phase)
- The purpose is premise verification (did we already ship this?) rather than design exploration

## When This Does NOT Apply

- Items require live-system validation (agent can't run the app headless)
- Backlog is <5 items (serial review is faster)
- Items mix strategic, architectural, and tactical decisions at different levels of abstraction (narrow agents will surface conflicts, not resolve them)

## See Also

Related patterns:
- **probe-before-chain** — verify handoff brief inputs before running multi-mode chains (similar verification-first discipline)
- **upstream-noise-flood-bulk-close** — related pattern for mass-closing classified items
- **critic-triage-routing** — routing findings to appropriate decision-makers based on severity and scope

## Source Context

Pattern emerged from 2026-05-30 backlog reconciliation in COS and COS-MOH projects. Two concrete applications in same session: (1) 30-bead backlog closed/narrowed in parallel via 3 agents, ~12 min wall-clock, (2) router parity scan that corrected initial premise and surfaced hidden duplication in a subsystem. Directly transferable to any project with accumulated issue backlogs where premise verification (not design) is the bottleneck.
