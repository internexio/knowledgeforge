---
title: Parallel-spec + parallel-critic pattern for independent beads
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 4
created: 2026-06-12
domain: orchestration
topic: multi-stage-issue-workflow
tags: [adversarial, chain, routing, quality-gate, throughput]
related_entries:
  - orchestration/2026-05-30_parallel-agent-triage-backlog-reconciliation.md
  - orchestration/2026-05-30_bead-tracker-workflow-pipeline-triage-decisions-build-deploy.md
  - methodologies/2026-05-22_adversarial-critic-convergence-trajectory-category-per-pass.md
pinned: false
---

# Parallel-Spec + Parallel-Critic Pattern for Independent Beads

## Problem Shape

Standard KF spec work runs sequentially: probe → Builder spec → adversarial-critic → revise → human gate → impl. When two specs are independent (neither depends on the other's output), running them sequentially is unnecessarily slow.

## Pattern

Parallel-spec orchestration:

1. **Phase 0 probes in parallel** (or one batch read) — both specs need different surfaces; reading them together avoids context-switching cost.

2. **Builder writes both specs sequentially in the same turn** — drafting one after the other in the same conversation lets the author maintain mental model of both. Cross-references between specs (e.g., "this bead's step_3c interacts with the other bead's step_2c lookup") are easier to keep consistent.

3. **Spawn two adversarial-critic agents in a single tool-use block** — true parallel execution; each Critic reviews one spec independently. They cannot see each other's findings, which is desirable (avoids groupthink bias).

4. **Absorb findings from both in the same revision pass** — apply edits to both spec docs in interleaved Edit calls. The author re-loads both specs' context at once, which is cheap once both are committed.

5. **Surface twin gates to the user** — present both gate options together, with a per-spec breakdown. User can approve / reject each independently.

6. **Sequence the impls** (one after the other) — implementation has real-world side effects (file edits, commits, downstream workflow triggers). Parallel impl is risky for state-changing operations; sequential impl is the safer pattern even when the specs were written in parallel.

## Wall-Clock and Cognitive Costs

Each Critic run takes ~3–5 min per spec when run in sequence. Parallel Critic runs complete in roughly the time of one spec's Critic cycle (~3–5 min for both).

Revision consolidation (step 4) costs slightly more than a single-spec revision because the author must track findings across two specs. However, this is offset by the elimination of a second Critic cycle — in serial orchestration, you'd run Critic once on spec A, revise, then run Critic again on spec B, revise again. The parallel approach does: Critic A + Critic B (parallel) → revise both. Net savings: one full Critic cycle.

Cognitive load during revision: moderate. The author re-loads both specs' context at once and applies changes in interleaved Edit calls. This is more efficient than remembering findings from one Critic cycle, then re-invoking the second Spec/Critic/Revision loop from scratch.

## When This Applies

- Two or more independent beads (no mutual blocking deps)
- Specs are similar in size and complexity (so parallel agent runs complete in similar time and the orchestrator can synthesize findings together)
- The author has enough context budget to hold both specs in mind during revision
- Each spec stands alone for review (so the user can gate them independently)

## When This Does NOT Apply

- One spec depends on the other's design decisions (sequential is required)
- Specs touch the same module section at the same lines (revision conflicts)
- The author's context is already heavy from prior work in the session (cognitive bandwidth is the bottleneck, not wall-clock)
- Specs need different Critic context (e.g., different file references, different constraints) — the parallel spawn loses the benefit if you have to re-explain

## Verified During

2026-06-12 KF session: beads 8gp (M25 entity → path-glob resolver) and 8zt (M21 linter violation counter for hook graduation). Specs written sequentially in one turn; adversarial-critic agents spawned in a single tool-use block in parallel; twin gates surfaced together; user approved both; impls ran sequentially.

Each Critic surfaced 5 findings (10 total). All absorbed across both specs in one revision pass. Wall-clock savings vs sequential: roughly halved the Critic-cycle time (one pair of parallel agent runs instead of two sequential rounds). Cognitive cost: moderate — the orchestrator had to track 10 distinct findings across 2 specs, but the user gate moment surfaced them cleanly with per-spec tables.

## Counter-Pattern

Spawning a single Critic to review both specs in one prompt is tempting (saves an Agent call) but produces shallower review — the Critic's attention is split, and one spec's findings tend to dominate the report. The parallel-with-separate-Critics pattern preserves review depth per spec.

## Source Context

Pattern emerged from 2026-06-12 KF Phase 1+2 session where two independent module-expansion specs (M25 + M21) were drafted, criticized, and approved in parallel. Directly applicable to any multi-spec KF workflow or multi-bead implementation sessions where specs are domain-isolated and can be reviewed independently.
