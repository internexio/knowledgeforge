# ENH-001: Sycophantic Confirmation Guard
**Mode:** Builder, Expert (any mode that builds on user-supplied facts)
**Priority:** P0
**Effort:** Low — prompt addition only
**Status:** Proposed

## Problem

When a user provides factual premises ("our conversion rate is 4%", "this API returns JSON"),
Builder and Expert accept them uncritically and construct outputs on top of them. If the premise
is wrong, the output is confidently, structurally correct — and functionally wrong.

This is Nate's "sycophantic confirmation" failure: the agent confirms incorrect data and builds
an entire system around it. The failure is invisible because the output looks right.

KF currently fires the adversarial Critic *after* output is produced. Nothing guards the
input assumptions at the start. By the time Critic runs, the bad premise is baked in.

## Failure Example

User: "Build a pricing model. We have 50k MAU, 3% conversion, $29/mo plan."
Builder builds correctly on those numbers.
Actual MAU: 5k. Actual conversion: 0.3%. The model is off by 10x — but looks perfect.

## Proposed Fix

Add an **Assumption Surface** step at the start of Builder and Expert when user-supplied
factual data is present.

### Trigger Condition
Any of the following in the user's request:
- Specific numbers or metrics ("our X is Y")
- Claims about system state ("the API does X", "users expect Y")
- Business facts used as inputs to a recommendation ("we have X customers")

### Behavior

Before building, surface the load-bearing assumptions explicitly:

```
Assumptions I'm building on:
• [Fact A] — source: you stated this. If wrong, [consequence].
• [Fact B] — source: you stated this. If wrong, [consequence].

If any of these are estimates or approximations, flag them now — I'll adjust the output accordingly.
```

Then proceed. The user can correct or confirm. No blocking — just surface.

### What NOT to Do
- Do not ask about every detail ("what's your tech stack?") — only load-bearing facts
- Do not re-ask after user confirms — one pass only
- Do not fire on reckonings or light evaluative tasks — only Builder/Expert chains where
  bad premises would silently corrupt the output

## Implementation

**In Builder agent system prompt, add to pre-build checklist:**

> Before building, identify any factual premises from the user's request that the output
> depends on. If present, surface them as explicit assumptions with consequence statements.
> One pass — then build.

**In Expert agent system prompt, add to analysis setup:**

> Before deep analysis, identify load-bearing factual assumptions from user-provided context.
> Surface each with: what it is, where it came from (user-stated), and what breaks if it's wrong.
> Flag uncertainty explicitly. Then proceed.

## Acceptance Criteria
- Builder surfaces assumptions when user provides specific metrics/facts
- Expert surfaces assumptions before any HIGH-risk analysis
- Neither mode blocks on assumption surface — it's informational, not a gate
- Does not fire on requests with no user-supplied factual data

## Anti-Patterns
- Asking "are you sure?" — paternalistic, slows flow
- Surfacing obvious assumptions ("you want this in English") — noise
- Re-surfacing after user confirms — trust the user
- Firing on every request — only when load-bearing premises are present
