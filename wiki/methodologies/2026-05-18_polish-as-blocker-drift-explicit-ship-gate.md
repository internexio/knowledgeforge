---
title: Polish-as-blocker drift — when iteration cycles need an explicit ship gate
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.8
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-18
tags: empirical, quality-gate, classification, delegation, validation
related_entries:
  - methodologies/2026-05-18_reframe-stated-scope-to-actual-goal-strategist-heuristic.md
  - methodologies/2026-05-15_pre-emptive-scope-sweep-downstream-verdict.md
---

# Polish-as-blocker drift — when iteration cycles need an explicit ship gate

## The Pattern

When a user asks an agent to "hold and iterate" on production-adjacent work, the agent tends to keep generating new fix candidates beyond the user's original stated concerns, conflating polish with blockers. The user must then intervene with an explicit "what are we holding for" question to force honest accounting. Build the ship gate into the iteration cycle instead.

## The Drift Mechanic (Why It Happens)

- Each smoke test or observation produces a new finding
- Each finding feels "load-bearing" in isolation (concrete, recent, specific)
- The agent treats each new finding as an additional blocker rather than as a polish item
- Iteration cycle has vague stop conditions, so finding-generation continues indefinitely
- Opportunity cost of holding is invisible to the agent (no clock running on the user's calendar)

The result: stated concerns are resolved, but the agent queues 3–4 more enhancement candidates as if they were blockers, delaying the ship decision.

## Mitigation — the Explicit Ship Gate

After resolving each stated user concern, the agent must run this checklist BEFORE flagging a new finding as a blocker:

1. **Did the user name this as a hold reason?** If no → it's an enhancement, not a blocker.
2. **Is it a regression from the production state?** If no → it's an enhancement.
3. **Does the user's actual use case touch this path?** If no → it's an enhancement.
4. **Default presentation when nothing else passes:**
   ```
   Stated concerns resolved. Ship recommendation: [yes / no].
   Pending enhancements (NOT blockers): [list].
   Authorize prod push?
   ```

The agent should generate that accounting **proactively** at each iteration boundary, not wait for the user to demand it. Built in: "Concerns resolved. Anything new is enhancement. Ship or continue?"

## When This Applies

- Iteration cycles with vague stop conditions ("iterate more before prod")
- Production-adjacent work where smoke tests produce a stream of findings
- Multi-commit work where the agent is the one running the verification loop
- Sessions where the user has stepped back to let the agent drive
- Agent roles (debugger, builder, critic) generating streams of "maybe issues" during validation

## When This Does NOT Apply

- The user is actively pair-iterating and approving each cycle (no drift possible because feedback closes the loop)
- Hard safety / correctness blockers (a fix that's actually broken — keep iterating)
- The user explicitly asks for a longer polish pass before shipping
- Compliance-driven work where "thorough iteration" is the stated acceptance criterion

## Grounding from cos-mcp-clarify-integration-phase2-3-prod-push Session

**Initial user request:** "Hold prod entirely — iterate more on test first (latency, prompt hardening, more smoke cases)." Three specific holds named.

**Agent action (problematic):** After fixing the two named issues (latency 47s → 5.5s; fake-claims caught Stripe-engineer fabrication) and running 2 of 3 planned smokes (both passing on the user's stated concerns), the agent kept queueing enhancements as if they were blockers:
- "3–4 weeks" soft-stat in smoke 2 — minor, hedged, occurred only on opt-in scoring path
- v2 prompt hardening (subject lines, length, tone) — feature work, not bug fixes
- Refile a rejected wiki entry — administrative task
- Smoke 3 (refine path) — would validate already-test-covered code

**User intervention:** Single diagnostic question: "What are we holding for?"

**Result:** This forced an honest accounting:
- All 3 stated concerns: ✅ resolved
- All "new findings" since the holds: ✅ polish, not blockers
- Recommendation: ship

**Outcome:** User authorized prod push within 2 messages of that question.

### Cost-Benefit

- **Cost of agent drift:** 30 minutes of extra iteration queuing additional items
- **Cost of user intervention:** 1 diagnostic question
- **Savings from clarity:** Cleared ambiguity and enabled immediate prod push instead of further delay
- **Lesson:** Ship gate should be automatic at iteration boundaries, not user-driven

## The Honest Accounting Checklist

When presenting a "new finding" from a smoke test or validation pass, agent should ask itself:

| Question | If Yes | If No |
|----------|--------|-------|
| Did user explicitly name this as a stated hold reason? | **BLOCKER** — Include in ship-gate summary | **ENHANCEMENT** — Surface as pending |
| Is this a regression from current-prod behavior? | **BLOCKER** — Must fix before ship | **ENHANCEMENT** — File separately |
| Does the user's named use case exercise this code path? | **BLOCKER** (maybe) — Depends on criticality | **ENHANCEMENT** — Lower priority |
| Is correctness actually broken (not just suboptimal)? | **BLOCKER** — Keep iterating | **ENHANCEMENT** — Ship as-is |

All four answers "no" → **Default to ship recommendation + list as pending enhancement.**

## Counterexample / Failure Mode to Watch

**Do not use this pattern to talk the user OUT of a real concern they haven't yet articulated.** The pattern is about distinguishing **stated-blockers from agent-generated-polish**, not about minimizing legitimate caution.

Some users WANT exhaustive iteration (compliance work, regulated industries, highly-available systems). Read the user's signal — if they asked for "thorough", thorough is correct.

Bad application: User says "iterate carefully on the payment pipeline." Agent says "All my stated concerns are resolved — ship?" without giving the user time to review. → That's dismissive, not helpful.

Good application: User says "iterate more on tests." Agent ships tests, runs smoke suite, finds "3–4 weeks" edge case, asks "This is a polish issue in an edge path — ship or continue?" → That's clarity.

## Cross-References

**Sister pattern:** [methodologies/2026-05-18_reframe-stated-scope-to-actual-goal-strategist-heuristic.md]
- Both involve catching scope drift, but reframe-to-goal applies BEFORE work starts (scope alignment)
- Polish-as-blocker applies AFTER stated concerns are resolved (delivery timing)

**Related:** [methodologies/2026-05-15_pre-emptive-scope-sweep-downstream-verdict.md]
- Similar due-diligence principle: surface scope changes before they cause rework
- This pattern applies to iteration cycles; scope-sweep applies to decision-downstream tasks

## Process Integration

**Timing:** At each iteration boundary (after running a validation pass, smoke test, or review cycle).

**Who:** Typically the Builder or Debugger agent, running the iteration loop. Can be called out by Critic during review ("You're queuing enhancements as blockers").

**Artifact:** The ship-gate summary response. Explicitly lists:
- Stated concerns status (all ✅ resolved)
- New findings classified (enhancement or blocker)
- Ship recommendation (yes / no / conditional)

## Source Context

Discovered 2026-05-18 during `cos-mcp-clarify-integration-phase2-3-prod-push` session when the user asked "What are we holding for?" after 30 minutes of the agent queuing additional validation items as blockers. Two named issues had been fixed and two smoke tests passed on the user's stated concerns, but the agent was treating each new finding (soft-stats, prompt variations, admin tasks) as additional reasons to hold. The single diagnostic question immediately clarified the distinction: all stated concerns resolved, everything new is enhancement, ship now. Pattern is empirically effective at preventing iteration drift when agent controls the validation loop.
