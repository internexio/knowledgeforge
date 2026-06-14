---
title: Worktree-isolated subagents cannot spawn other subagents — apply protocol inline as fallback
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: fast_decay
importance: 2
created: 2026-06-14
domain: diagnostics
topic: workflow-discipline
tags: [delegation, empirical]
related_entries:
  - orchestration/2026-06-12_parallel-spec-parallel-critic-pattern-independent-beads.md
pinned: false
---

# Worktree-Isolated Subagents Cannot Spawn Other Subagents

## Problem Shape

When the orchestrator dispatches a subagent with the `Agent` tool using `isolation: worktree`, that subagent does not have access to the `Agent` tool itself within its context. Concretely: a worktree-isolated subagent cannot spawn `adversarial-critic`, `knowledge-librarian`, or any other named agent to verify its own work.

This breaks any pattern that assumes "every Builder-style output gets an auto-adversarial pass" — because the worktree subagent IS the Builder, and the orchestrator's normal Module 00 auto-verification trigger doesn't fire inside the subagent's sandbox.

## Detection

Symptoms inside a worktree subagent prompt:
- Subagent reports "Task tool not available in worktree" or equivalent
- Subagent reports it ran the adversarial review "inline" / "self-executed"
- No actual `adversarial-critic` agent invocation in the parent transcript for this subagent's output

## Pattern (mitigation)

Two acceptable fallbacks:

1. **Subagent applies the adversarial-critic protocol inline.** In the worktree prompt, instruct the subagent: "You have permission to apply the adversarial-critic protocol to your own output — assume the output has at least one significant flaw; find compound failures, unstated assumptions, integration failure points, design philosophy traps; report Sev2+ only; apply revision cycle 1 if findings; halt with report if persistent Sev2+ after cycle 1." This is a degraded form of separate-agent verification (the same context produces both the artifact and the critique), but it preserves the protocol's findings discipline and revision-cycle bounds.

2. **Orchestrator runs adversarial-critic AFTER subagent returns.** The orchestrator receives the subagent's commit on its branch, then dispatches `adversarial-critic` against the committed content from the orchestrator's own context. This restores the separate-context guarantee but loses the in-worktree iteration loop (orchestrator must dispatch a follow-up subagent to revise).

Choose (1) when iteration speed matters and the subagent is competent at self-criticism; (2) when the spec is high-stakes and separate-context verification is load-bearing.

## When This Applies

- Subagent dispatched via `Agent` tool with `isolation: worktree`
- Workflow assumes the subagent will auto-trigger child agents (adversarial-critic, knowledge-librarian, etc.)
- The subagent's output goes through a quality gate that the team usually delegates to a separate agent

## When This Does NOT Apply

- Subagents dispatched without `isolation: worktree` (those may have full Agent-tool access; verify per-harness)
- Top-level orchestrator turns (the orchestrator can spawn agents normally)
- Single-pass tasks where no quality gate is needed

## Grounding

KF-core 2026-06-13/14: three worktree-isolated subagents (SPEC 5, SPEC 4, SPEC 1 implementations) all reported "Task tool not available, applied adversarial-critic protocol inline" or equivalent. Each found at least one Sev2 finding inline and resolved it in revision cycle 1. The pattern was acceptable for those specs (mid-stakes), but the team should consider option (2) for higher-stakes work.

## Source Context

This is a harness-level constraint, not a design choice. May invalidate when the Claude Code agent harness gains nested-agent support. `staleness_risk: fast_decay` reflects this — re-verify next time a worktree subagent is dispatched and check whether the `Agent` tool is now exposed.
