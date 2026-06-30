---
title: Reframe stated scope to actual goal before sequencing — large-scope strategist heuristic
source_mode: strategist
novelty_type: reusable_diagnostic
grounding_score: 0.7
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-18
tags: strategist, methodology, scope-management, goal-clarification, requirements-clarity, reframe
related_entries:
  - methodologies/2026-05-15_pre-emptive-scope-sweep-downstream-verdict.md
  - methodologies/2026-05-13_find-consumer-first-before-data-migration.md
  - methodologies/2026-05-13_verify-audit-claims-before-designing-fix.md
domain: methodologies
topic: scope-management
---

# Reframe stated scope to actual goal before sequencing — large-scope strategist heuristic

## The Pattern

When a user's stated scope is large (touches many systems, delivers many features, achieves "parity"), the **stated scope often differs from the actual goal by 60–80%**. Before sequencing the work, pause and verify alignment using three diagnostic questions.

**Specific trigger phrases that should activate this check:**
- "ensure all [X] are available in [Y]"
- "feature parity between A and B"
- "complete the [X] surface"
- "wire up all [X]"
- Any noun-quantifier ("all", "every", "complete", "full", "comprehensive") attached to a feature surface

## Diagnostic Method (3 Questions, ~2 Minutes)

Ask the user these three questions in sequence:

1. **Who is the consumer?** A specific named integration / dogfood path → narrow scope. A hypothetical future user → wide scope.
2. **What's the demo?** What artifact or moment proves this worked? If unclear, scope is wrong. (This forces the user to articulate concrete, not abstract, success.)
3. **What gets cut if we stay narrow?** List which "missing" items the actual goal does NOT depend on. The list is usually 60–80% of the original scope.

The reframe output is a much tighter scope pinned to an explicit goal and a specific consumer.

## When This Applies

- Strategy or sequencing sessions with multi-feature scope
- Integration / migration / refactor planning
- Any time "build out X" or "ensure all X" is the framing
- The user hasn't already explicitly framed it as MVP / demo / single-feature

## When This Does NOT Apply

- Compliance-driven scope (you actually do need to cover everything — security audit, regulatory, accessibility mandate)
- Library / framework releases where downstream consumers ARE hypothetical-many
- The user has already explicitly locked the scope as "full parity required"
- Stated scope is already tied to a specific demo or named consumer

## Grounding from cos-mcp-clarify-integration-phase2-3

**Initial framing (overstated):**
"1. Ensure all production features are available in the API/MCP, 2. test, 3. integrate into clarify.ai"

Critic gap analysis surfaced 11 missing MCP tools across: audience, buyers-committee, expert-council, projects, website-tools, SEO-planner, etc. Work appeared multi-day.

**After applying the 3 diagnostic questions:**

1. **Who is the consumer?** "Ship a Clarify cold-email demo + dogfood for YouTube content" (specific, named, single-use path) — not generic API consumers.
2. **What's the demo?** "User inputs prospect profile, system suggests optimized email copy using audience intelligence" (concrete moment).
3. **What gets cut if we stay narrow?** Buyers-committee tools, expert-council tools, website-tools, SEO-planner tools — none are needed for the cold-email demo.

**Reframed scope:** 4 tools initially (audience_profile, optimize_email_for_prospect, MBTI→OCEAN, credits_balance) → ultimately **2 tools** (audience_profile + composite optimize_email).

**Outcome:** Shipped Phase 2 + 3 in a single ~2-hour session vs. estimated multi-day for original "parity" scope. CI green, smoke test successful, prod-push gate reached.

### Cost-Benefit

- **Cost of reframe:** ~2 minutes (asking 3 questions + listening)
- **Savings:** Avoided multi-day scope creep; shipped in 2 hours instead
- **ROI:** 15× speedup from 2-minute diagnostic

## Counterexample / Failure Mode to Watch

**Do not reframe a TRUE parity requirement to a demo.** A compliance ask ("API must support all OAuth scopes our docs claim") or a published contract ("library must support all browser versions we advertised") is not a candidate for goal-reframe — the scope IS the goal.

Test: Does the reframed goal still produce a demo the user can name? If not, you've cut too far — revert to the original scope.

## Sister Pattern: Phase 0 Dogfood

Once you have the reframed goal, **manually walk the workflow with current tools BEFORE building new ones**. This reveals which atomic operations are missing vs. which can be composed.

In the Clarify session, the user explicitly skipped Phase 0 and built directly; outcome was acceptable (2-hour ship), but the counterfactual ("would Phase 0 have changed the composite tool's input schema?") remains unverified. For future multi-tool integrations, recommend Phase 0 before tool composition.

## Process Integration

**Timing:** In the planning/strategy phase, before sequencing.

**Who:** Typically the Strategist agent or mode, triggered by large-scope framing. Can also be called out by Critic during gap analysis ("This looks like stated-vs-actual scope mismatch; let's reframe").

**Artifact:** Updated scope statement in the work plan or bead description. Optionally: a planning note capturing the reframe reasoning.

## Related Patterns

- **[[pre-emptive-scope-sweep-downstream-verdict]]** — similar due-diligence, but applied POST-decision to knock out redundant downstream tasks. This pattern applies PRE-sequencing.
- **[[find-consumer-first-before-data-migration]]** — same principle (consumer-first thinking) applied to data migration design; this generalizes to ANY scope conversation.
- **[[verify-audit-claims-before-designing-fix]]** — pre-design due-diligence to avoid executing plans against stale assumptions.

## Source Context

Discovered 2026-05-18 during `cos-mcp-clarify-integration-phase2-3` session. User opened with large "feature parity" framing; applying the 3-question diagnostic revealed actual goal was "ship Clarify cold-email demo." Reframe cut scope from 11 tools to 2 and compressed multi-day estimate to single 2-hour session with successful CI/smoke-test. The 3-question method is mechanically simple but empirically effective at aligning stated scope with actual goal before work begins.
