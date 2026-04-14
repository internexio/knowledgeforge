# ENH-006: Specification Drift Checkpoint
**Mode:** Coordinator (long chains), Compaction Protocol
**Priority:** P2
**Effort:** Medium — requires checkpoint trigger in Coordinator + compaction hook
**Status:** Proposed

## Problem

KF locks intent at the start of a mode. On multi-step chains and long agentic runs, the
original specification drifts out of active context. The agent continues executing — against
a faded version of the goal.

Nate's formulation: "Over a long task, the agent effectively forgets the specification unless
you construct your agent harness correctly and the agent is forcibly reminded of the specification."

He cites the "RLHF loop on Claude that went viral" as an example of forcible spec reminder
working in practice.

KF's compaction protocol handles session continuity (session-end flush, importance-weighted
decay). But there's no **mid-chain spec re-validation** — a checkpoint that asks "are we
still solving the right problem?" partway through a long execution.

## When Spec Drift Occurs in KF

1. **Long mode chains (3+):** By the time adversarial Critic fires, the original intent
   stated at the start of @builder may be 8k+ tokens back in context.

2. **Multi-session work:** A task started in one session, continued in another. The
   compaction summary captures what happened, not what was originally intended.

3. **Mid-chain pivots:** User refines scope partway through. The new scope replaces the
   original in recent context, but earlier mode outputs were built against the old scope.

## Proposed Fix

Two components: a **Coordinator checkpoint** and a **compaction spec anchor**.

### Component 1: Coordinator Mid-Chain Checkpoint

For chains of 3+ modes, Coordinator inserts a spec re-validation step between mode 2 and
mode 3 (before the output-producing mode runs):

```
Spec Checkpoint (mid-chain):
Original goal: [extract from chain start — first user statement of intent]
Current trajectory: [what modes 1-2 have produced so far]
Alignment check: [is the trajectory still solving the original goal?]

[ ] Aligned — proceed to next mode
[ ] Drifted — [describe drift] — adjust before proceeding
```

If drifted: surface the drift and proposed correction before launching the next mode.
If aligned: invisible (no output, just proceed).

### Component 2: Compaction Spec Anchor

When context is compacted (session approaching limit), the spec anchor is preserved
verbatim — not summarized.

Add to compaction protocol:

> Preserve verbatim (never summarize):
> - The user's original stated intent for the current task
> - Any explicit constraints or out-of-scope declarations
> - The current mode chain and which step we're on

This ensures the next session resumes with the original spec intact, not a lossy summary
of it.

### What "Original Specification" Means

KF extracts the original spec from the first substantive user message in the chain:
- What they want built/decided/reviewed
- Any explicit constraints ("don't use X", "must work with Y")
- The success condition (what done looks like)

This is locked at chain start and treated as the reference point for all checkpoints.

## Failure Example Without This

Chain: @builder → @critic → @strategist

User's original intent: "Build a lightweight auth system for internal tools."
@builder produces a full OIDC implementation with SSO.
@critic reviews it (semantically correct).
@strategist recommends rollout sequence for enterprise SSO.

No one noticed the spec drifted from "lightweight internal auth" to "enterprise SSO" between
@builder and @critic. The final output is coherent and wrong.

With the checkpoint: after @critic, spec re-validation catches "enterprise SSO" ≠ "lightweight
internal auth" and surfaces the drift before @strategist runs.

## Acceptance Criteria
- Spec checkpoint fires between mode 2 and mode 3 on all 3+ mode chains
- Aligned checks are invisible (no output)
- Drift is surfaced with: original spec, current trajectory, proposed correction
- Compaction preserves original spec verbatim (not summarized)
- Mid-chain pivots update the locked spec (user can explicitly redefine scope)

## Anti-Patterns
- Checking alignment after every single mode — overhead exceeds value
- Summarizing the original spec during compaction — defeats the purpose
- Treating spec drift as always bad — sometimes the user meant to pivot; distinguish
  user-initiated pivots from silent model drift
- Blocking the chain on detected drift — surface and proceed with correction, don't block
