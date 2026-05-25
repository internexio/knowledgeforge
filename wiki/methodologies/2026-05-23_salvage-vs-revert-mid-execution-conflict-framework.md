---
title: Salvage-vs-Revert Decision Framework for Mid-Execution Discovered Conflicts
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-23
domain: strategic-execution
topic: conflict-recovery
tags: decision-framework, recovery, conflict-resolution, mid-execution-pivot, content-strategy, sunk-cost
related_entries:
  - methodologies/2026-05-23_seo-repositioning-failing-rank-for-unranked-head-term.md
  - methodologies/2026-05-15_pre-emptive-scope-sweep-downstream-verdict.md
---

# Salvage-vs-Revert: Decision Framework for Mid-Execution Discovered Conflicts

## When This Framework Applies

You are mid-execution on a multi-step strategic plan. A discovery during execution (content audit, dependency check, data refresh) reveals that an earlier step in the plan was based on an incorrect assumption. The earlier step is already deployed / committed / shipped. The remaining steps were premised on the earlier step being correct.

The decision is no longer "execute the next step" — it is "which path forward causes the least damage." There are typically three paths, and the right one depends on quantifiable trade-offs, not gut feel.

## The Three Paths

### 1. Full Revert
Roll back the earlier (deployed) step entirely. Return to the state before the plan began.

**Cost:** Time lost, any accrued value (rank, backlinks, audience signal) discarded, plan restarts from step 1.

**Benefit:** Honest reset; no compounding of the conflict.

### 2. Salvage / Differentiate
Keep the earlier step in place but adapt it (re-anchor, re-scope, redirect a sub-piece) so it no longer conflicts. Subsequent steps then plan around the adapted state.

**Cost:** Smaller value capture (may only get 30-50% of original plan upside).

**Benefit:** Preserves some work value, lower time investment than revert, adapts downstream steps in place.

### 3. Consolidate / Redirect
Sacrifice one branch entirely — typically by 301-redirecting (in SEO context), deleting (in code context), or absorbing the conflicting work into the surviving branch. Cleanest but most aggressive; least reversible.

**Cost:** Most irreversible; accrued value on the sacrificed branch is lost.

**Benefit:** Lowest ongoing conflict cost; one clean winner instead of compromise.

## Decision Criteria (Apply In Order)

### Criterion 1 — Is the earlier step doing useful work even if imperfect?

If the earlier step delivered SOME value (e.g., a re-anchor that captured a smaller but real keyword instead of the dream one), salvage is usually right. If the earlier step actively makes things worse (e.g., a deployed change that breaks something users depend on), favor revert or consolidate.

**Gut check:** Remove the earlier step and ask: "Did I lose something of real value?" If yes, the step was useful despite the conflict. Salvage it. If no, reverting is less costly.

### Criterion 2 — How much does the earlier step's footprint matter?

Footprint = backlinks, established rank, accrued usage, downstream dependencies, brand signal. High footprint argues against destructive paths (revert / consolidate) and toward salvage. Low footprint makes all three paths viable; pick the cleanest.

**Calculation:** If the step has been live for months and already accrued external reference (backlinks, citations, user navigation patterns), its footprint is HIGH. If it's 2 days old with no external signal, footprint is LOW.

### Criterion 3 — What is the magnitude of the salvage compromise?

If the salvage path captures only 1% of the value the original plan promised, the salvage is essentially a face-saving exercise — revert is more honest. If the salvage captures 50%+ of the value with low conflict-resolution cost, salvage is clearly right. The 1%–50% range is judgment-dependent.

**Quantification:** Estimate the original plan's promised value in a single metric (traffic, SEO opportunity, user count, whatever). Estimate what salvage captures. Divide. If the ratio is <5%, revert. If >50%, salvage. If between, weigh the cost of time spent on salvage vs. restart.

### Criterion 4 — Is the conflict reversibility itself a concern?

A 301 redirect is mostly reversible (can swap back if needed) but loses any rank accrued under the redirect. A page revert is fully reversible but the time lost is not. A consolidate is least reversible but lowest ongoing cost. Weight these against expected need for future course-correction.

**Forward-looking:** If there's ambiguity around whether the conflict is real (conflicting data sources, pending clarification), reversibility matters. If you're 90% certain the conflict is real, reversibility matters less.

## Concrete Case (2026-05-23, COS / semalytics.com)

**Plan:** Three-phase psychographic-marketing SEO pillar: (1) re-anchor Page B to head term "psychographic segmentation" (6,600 vol), (2) cross-link sibling pages, (3) build cluster pages.

**Discovery mid-Phase-3:** Page B's new anchor "psychographic segmentation" was already owned by `/guides/psychographic-segmentation/` (an existing well-developed page). Phase 1 had created cannibalization. The remaining Phase 3 work (cluster pages "psychographic-vs-demographic", "psychographic-segmentation-examples", "what-is-psychographic-marketing") was partially redundant with that existing page.

**Decision walk-through:**

- *Criterion 1:* Phase 1 re-anchor delivered some signal (better than the original 10-vol anchor) but the cannibalization cost > the signal gain. Salvage if a differentiated anchor exists, otherwise revert.
- *Criterion 2:* Page B had no meaningful current rank or backlinks worth preserving — footprint LOW. All three paths viable.
- *Criterion 3:* Differentiation candidates topped out at 70 vol/mo ("ocean marketing"). 70 / 6,600 = ~1%. Marginal salvage. BUT — 70 vol > 10 vol original anchor, and the content was already OCEAN-heavy so the rewrite was small. Salvage path retained more value than revert.
- *Criterion 4:* Re-anchor is easily reversible. Consolidate (301 to existing page) was more decisive but less reversible.

**Decision:** Salvage / Differentiate to "ocean marketing" (70 vol/mo). Same-day corrective ship (cos-6bq).

**Cluster pages decision (separate sub-decision):** Pages 2 and 3 of original Phase 3 were genuinely covered by the existing page. Decision: cancel those two, ship only the new one that targeted a distinct keyword (psychographic vs demographic, 880 vol). 1 of 3 shipped + 2 absorbed by existing page. Equivalent decision frame: criterion 3 said "remaining pages capture ~0% incremental value because existing page covers them" → consolidate/absorb.

## What This Framework Does NOT Say

- It does not say salvage is always right. Sometimes the honest call is to revert and admit the plan was wrong. The 1%-of-original-value salvage is often face-saving, not value-maximizing.
- It does not say discoveries should be ignored to maintain plan integrity. Sunk cost is a trap. The fact that the original plan was committed to does not increase the value of pursuing it.
- It does not eliminate the cost of the pivot itself. Pivoting takes time — sometimes the right call is to ship the planned next step and address the conflict in a later cycle when context is clearer.

## Anti-Pattern: Powering Through

The failure mode this framework counters is **powering through** — completing the remaining planned steps as if the discovery did not happen, hoping it can be "fixed later." This compounds the conflict and makes recovery more expensive. The moment you notice the discovery, stop the next step and decide which path. The cost of pausing to decide is low; the cost of compounding the conflict is high.

## When This Does NOT Apply

- **The discovery is provisional or uncertain.** If conflicting data sources haven't been triangulated yet, defer the decision until you have high confidence in the conflict's reality.
- **Time-to-decision cost is prohibitive.** If the four-criterion walk-through takes longer than executing the next step, defer the decision and execute, then sweep in the next cycle.
- **The plan's remaining steps are independent of the conflict.** If the earlier step's correctness doesn't affect the next 2-3 steps, execute those steps and revisit the conflict later.

## Related Patterns & Tools

- **SEO Repositioning Pattern** (`methodologies/2026-05-23_seo-repositioning-failing-rank-for-unranked-head-term.md`) — specific instance of salvage applied to a page-rank decision
- **Pre-emptive scope sweep** (`methodologies/2026-05-15_pre-emptive-scope-sweep-downstream-verdict.md`) — related pattern for handling downstream task re-scoping after a strategic verdict
- **Vendor-swap semantics recalibration** (`methodologies/2026-05-23_vendor-swap-semantics-recalibration-audit.md`) — related conflict-discovery pattern when swapping dependencies

## Source Context

Framework crystallized from a 2026-05-23 SEO session where a content audit mid-Phase-3 surfaced cannibalization from Phase 1 work shipped 4 commits earlier. The four-criterion structure emerged from the actual decision walk-through that day, presented to the user as options, and validated by the user picking the differentiate-and-salvage path. The 1%-of-value framing for the smaller anchor matched the user's "salvage, not victory" honest read.

Grounding: 0.85 (the framework was applied and validated on a real strategic decision with quantifiable trade-off analysis, but the SEO outcome is not yet measurable — Phase 3 changes shipped same-day, but ranking verification requires 30-90 days of GSC data).
