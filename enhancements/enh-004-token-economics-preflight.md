# ENH-004: Token Economics Pre-flight
**Mode:** Orchestrator (KF meta-layer)
**Priority:** P1
**Effort:** Medium — adds gate logic to chain dispatch
**Status:** Proposed

## Problem

KF launches 3+ mode chains without any cost estimation. For simple chains this is fine.
For deep chains on large inputs (Expert → Strategist → Builder → adversarial Critic),
compute cost is non-trivial and the user may not have consciously chosen to pay it.

Nate's formulation: "Is it worth it to build an agent for this job? You have to be able to
go through and calculate the cost per token for a given task and reliably say, if I put an
agent against this and it burns 100 million tokens, I can prove this is worth doing or I
can prove it's not worth doing — and I can do that *ahead of time*."

KF's circuit breaker fires on failure (3 consecutive). There's no pre-flight gate that asks
"is this chain worth launching in the first place?"

## What This Is Not

This is not token accounting or billing integration. It's a **depth/cost awareness check**:
- How deep is this chain?
- How large is the input?
- Is the user choosing this deliberately or defaulting into it?

The point is not to be cheap — it's to make cost a conscious choice, not an accidental one.

## Proposed Fix

Add a **Token Economics Pre-flight** that fires before any 3+ mode chain is dispatched.

### Trigger Condition
- Chain length ≥ 3 modes, OR
- Expert mode activation on input > ~2k tokens, OR
- Any chain involving adversarial Critic (adds a full review pass)

### Pre-flight Assessment

KF estimates cost tier (not exact tokens — relative depth):

| Signal | Cost Tier |
|--------|-----------|
| 2-mode chain, small input | LOW — no gate |
| 3-mode chain, medium input | MEDIUM — proceed with note |
| 3+ mode chain, large input | HIGH — surface before proceeding |
| Expert + adversarial Critic | HIGH — surface before proceeding |

### HIGH Tier Behavior

Surface before launching the chain:

```
Cost Tier: HIGH
Chain: @expert → @strategist → @builder → @critic (adversarial)
Input size: large (~8k tokens in context)
Estimated depth: 4 full mode passes

This chain will produce high-quality output but is compute-intensive.
Worth it if: the decision is novel, high-stakes, or hard to reverse.
Probably not worth it if: you want a quick directional answer.

Options:
  A. Proceed — launch full chain (recommended for novel/high-stakes)
  B. Scope down — @strategist only (faster, lower quality)
  C. Abort — answer differently

(Default: A — proceed)
```

### MEDIUM Tier Behavior

Log but don't gate:

```
[Cost note: 3-mode chain on medium input — proceeding.]
```

### LOW Tier Behavior

No output. Invisible.

## Implementation

**In KF orchestrator system prompt, add to chain dispatch logic:**

> Before dispatching any chain of 3+ modes, assess cost tier based on chain length and input
> size. LOW: proceed silently. MEDIUM: log the note, proceed. HIGH: surface the pre-flight
> assessment with options and default (proceed). Do not block — default and proceed if user
> doesn't respond.

## Acceptance Criteria
- Pre-flight fires on 3+ mode chains before dispatch
- HIGH tier surfaces options with clear default
- LOW tier is completely invisible (no overhead for simple chains)
- Pre-flight note is < 5 lines — not a deliberation, a flag
- User can bypass entirely by responding with "proceed" / "go" to any pre-flight

## Anti-Patterns
- Requiring explicit approval before every chain — friction death
- Showing token count estimates (looks like billing anxiety, not cost awareness)
- Firing on 2-mode chains — common, cheap, should be invisible
- Blocking chains — always default and proceed, never hard block
