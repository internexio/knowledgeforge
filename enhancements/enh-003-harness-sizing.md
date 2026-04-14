# ENH-003: Harness Sizing Pre-Check
**Mode:** Coordinator
**Priority:** P1
**Effort:** Medium — adds a pre-step to Coordinator routing logic
**Status:** Proposed

## Problem

Coordinator currently jumps directly to workflow design: map dependencies, derive coordination
pattern, produce the workflow. This is correct — but it skips a critical upstream question:

**Is this task correctly scoped for the harness we actually have?**

Nate's formulation: "One of the most interesting subsets of this skill right now is the ability
to know is a given project correctly scoped for the agentic harness I have."

The three harness types have fundamentally different scope limits:

| Harness | Scope Ceiling | Failure Mode When Overloaded |
|---------|---------------|------------------------------|
| Single-threaded (one Claude session) | Small, bounded tasks | Context overflow, quality degradation |
| Planner + sub-agents | Medium, parallelizable tasks | Coordination overhead exceeds value |
| Persistent planner (long-horizon) | Large, multi-day workflows | Spec drift, state loss between sessions |

Without a sizing check, Coordinator will design a beautiful workflow for a harness that can't
run it — or under-design a workflow for a task that needs more infrastructure than assumed.

## Proposed Fix

Add a **Harness Sizing Pre-Check** as the first step in Coordinator mode, before dependency
mapping begins.

### Three Questions (answered by KF, not asked of user)

1. **What harness are we operating in?**
   - Single Claude Code session (default assumption)
   - Defined multi-agent setup (user has specified agents/tools)
   - Long-horizon persistent system (stateful, multi-session)

2. **What is the task scope?**
   - Classify: bounded (clear end state, < 1 hour) / medium (parallelizable, hours to days) /
     large (multi-session, stateful, weeks)

3. **Is scope matched to harness?**
   - Match: proceed to dependency mapping
   - Mismatch: surface before designing

### Mismatch Handling

If task scope exceeds harness capability, surface before designing:

```
Harness Sizing Note:
This task (scope: large/multi-session) is being run in a single Claude Code session
(scope ceiling: bounded). Two options:
  A. Scope down: define a bounded first milestone that fits this session
  B. Acknowledge: design for the full scope knowing this session handles phase 1 only

Which approach? (Default: A — scope down to first milestone)
```

If task scope is under harness capability (over-engineering):

```
Harness Sizing Note:
This task appears small enough for direct execution without multi-agent coordination.
Coordinator overhead may exceed value here. Recommend: route to Builder directly.
Proceed with coordination anyway? (Default: No — route to Builder)
```

### Inferred Harness Signals

KF infers harness from context — no questions asked unless ambiguous:
- "Build X" with no agent specification → single-session assumed
- "Coordinate agents A, B, C" → multi-agent confirmed
- "Design a system that runs nightly" → long-horizon, flag it

## Implementation

**In Coordinator agent system prompt, prepend:**

> Before mapping dependencies, perform harness sizing:
> 1. Infer operating harness from context (single-session, multi-agent, long-horizon)
> 2. Classify task scope (bounded / medium / large)
> 3. Check match. If matched, proceed. If mismatched, surface the gap and default resolution
>    before designing. If under-engineered for coordination, recommend Builder instead.

## Acceptance Criteria
- Coordinator performs harness sizing before any dependency mapping
- Mismatches are surfaced with two explicit options + a default
- Over-engineering detected and redirected to Builder with user confirmation
- No questioning the user when harness is unambiguous — inference only
- Does not slow matched cases — sizing is a fast classification, not a deliberation

## Anti-Patterns
- Asking "what harness are you using?" — infer it
- Blocking on harness sizing — surface and default, then proceed
- Running harness sizing on non-Coordinator requests
- Treating "single session" as incapable — it handles most tasks fine
