---
title: Pre-emptive scope sweep of downstream tasks after a strategic verdict supersedes them
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-15
tags: methodologies, scope-management, strategic-decisions, project-management, bead-tracking
related_entries:
  - methodologies/2026-05-13_verify-audit-claims-before-designing-fix.md
  - methodologies/2026-05-13_critic-triage-routing-strategist-vs-defer-doc.md
---

# Pre-emptive scope sweep of downstream tasks after a strategic verdict supersedes them

## The Pattern

When a strategic decision verdict closes (e.g., "revise the spec to match shipped code rather than rewrite the engine"), the verdict implicitly rescopes the downstream tasks that depended on the OLD strategy. Closing those tasks individually defers the same scope conversation N times.

The fix: **sweep all downstream-of-verdict beads in one pass BEFORE picking up the first one**, classifying each as:

- **Scope intact** — task is independent of the verdict; full work remains
- **Description stale** — task is real but the bead text references the pre-verdict premise; touch up via a comment, don't reopen scope
- **Reduced-scope** — the original gap evaporated under the verdict but some residual real work survives; document and execute the residual
- **Wontfix** — the verdict makes the task obsolete

The sweep costs ~5–10 minutes of bead review and a few comment edits. The savings: avoiding wasted starts on now-obsolete work and the painful "wait, this evaporated too" realization mid-implementation.

## When This Applies

- A `decision`-type bead with verdict locked (not provisional)
- Multiple `task` beads that explicitly depend on that decision (DEPENDS ON edge)
- The verdict reshapes the implicit scope of those tasks, not just unblocks them

## When This Does NOT Apply

- Verdict only unblocks downstream tasks without changing their nature
- Downstream tasks are truly independent (verdict doesn't touch their substance)
- Only one downstream task — no leverage from sweeping
- The verdict is provisional or under review (sweep only when locked)

## Classification Detail

### Scope Intact
**Signal:** The task's core work survives the verdict undiminished.
- Example: Task was "implement three new routes" and the spec still requires three routes (verdict didn't touch routing)
- Action: Proceed with full implementation
- Confidence check: Did the verdict touch ANY of the domain this task addresses? If no, scope is intact.

### Description Stale
**Signal:** The task is real and necessary, but the bead description references a now-superseded premise.
- Example: Original bead text: "Reshape ObjectionCluster + dynamic_forecast per schema redesign in cos-3bu.1" → verdict was "don't reshape, match shipped code instead" → but the bead's residual work (frontend contract patch) still stands
- Action: Add a comment to the bead: "Scope adjusted post [verdict]: residual work is [specific]. Original context in bead description is superseded." Proceed.
- Confidence check: Can you complete this task WITHOUT touching the pre-verdict premise? If yes, it's stale-description.

### Reduced-Scope
**Signal:** The verdict evaporated a gap that the original task was supposed to close, but OTHER real work survives.
- Example: Task was "dynamic_forecast + ObjectionCluster reshape" (two things), verdict was "don't reshape schema", but now the backend emits dynamic_forecast in a different format and the frontend still needs a TS contract patch
- Action: Document what evaporated and what survived in a comment. Execute the residual work. Close the task noting "Verdict superseded [evaporated part]; [residual part] complete."
- Confidence check: Is there a concrete artifact (code, config, schema) that STILL needs to change under the new strategy? If yes, capture it and execute it. If no, move to wontfix.

### Wontfix
**Signal:** The verdict made the task unnecessary entirely. No residual work survives.
- Example: Task was "dynamic_forecast feature + ObjectionCluster reshape" and the verdict was "spec is revised to NOT require dynamic_forecast" — the full gap closed upstream
- Action: Close the task with explanation. "Post-verdict [x]: original gap closed in Phase 1 via [upstream change]. No residual work."
- Confidence check: Is there ANY real artifact you'd produce that doesn't exist today? If no, it's wontfix.

## Concrete Grounding: COS cos-3bu Epic

**Decision bead:** cos-3bu.2 (engine model decision, Option 2 = "revise spec to match code")
**Verdict locked:** 2026-05-15
**Downstream beads:** cos-3bu.3 through cos-3bu.9

### Sweep Results (6 downstream beads)

| Bead | Original scope | Verdict impact | Classification | Action | Outcome |
|------|---|---|---|---|---|
| cos-3bu.3 | Persona schema reconciliation | Spec revised to NOT require schema reshape | Wontfix | Close | Closed in Phase 1 |
| cos-3bu.5 | Output schema + dynamic_forecast + ObjectionCluster reshape | Spec revised to match shipped code | Reduced-scope | Residual: frontend TS contract patch | Completed; closed |
| cos-3bu.6 | Frontend routing split (three routes) | Spec still requires three routes (verdict didn't touch routing) | Scope intact | Full implementation | Proceeding as-is |
| cos-3bu.7 | Library persona model (flat schema) | Schema changed but library still needed | Description stale | Touch up reference from "flat" to "4-vector" | Proceeding; spec-aligned |
| cos-3bu.8 | Results view tabs (tab-3 deferred dynamic_forecast) | Tab-3 content reframed (buying_signals replaces deferred forecast) | Description stale | Touch up annotation: buying_signals, not forecast | Proceeding; updated description |
| cos-3bu.9 | T3 prompt bug (dynamic_forecast missing) | Spec revised to match code; feature no longer required | Wontfix | Close | Closed |

### Cost-Benefit

- **Sweep cost:** ~10 minutes (reading 6 beads + 3 comment edits)
- **Saved:** 3 redundant scope conversations that would have surfaced during implementation (discovery delay + rework + context-switch)
- **Net ROI:** Avoid ~5 hours of "wait, this changed" surprises scattered across three sessions

### Critical Insight

Three of six downstream beads needed scope or description action. Closing them individually (as discoveries during work) would have tripled the reckoning cost. Sweeping pre-emptively costs minutes; deferring costs hours.

## Process Integration

**Timing:** Run this sweep immediately after the verdict locks, before picking up the first downstream task.

**Who:** The engineer/agent picking up the post-verdict work queue. Can be solo (10-minute review pass) or collaborative (5-minute sweep + team comment review).

**Artifact:** Comments on the beads themselves (becomes part of the work record). Optionally: a sweep summary note linking the decision bead to the classification results (useful for cross-team handoff).

**Downstream:** Once classified, pick up tasks in this order: Scope Intact → Reduced-Scope (with residual documented) → Description Stale → Wontfix closed. This ensures you build momentum on clearly-scoped work before touching ambiguous tasks.

## Related Patterns

- **[[verify-audit-claims-before-designing-fix]]** — similar pre-execution due-diligence for audit-driven refactors (different artifact, same principle: don't execute plans against stale snapshots)
- **[[critic-triage-routing-strategist-vs-defer-doc]]** — the upstream decision-making framework that produces verdicts requiring this sweep
- **[[spec-commit-before-impl-commit]]** — spec is locked BEFORE sweeping; this pattern assumes that contract is honored

## Source Context

Discovered 2026-05-15 during cos-3bu BC v2 epic, post-cos-3bu.2 Option-2 verdict (revise spec to match shipped code). Picking up cos-3bu.5 first surfaced that its original "dynamic_forecast + ObjectionCluster reshape" scope had evaporated because the spec was revised in Phase 1 to NOT require those things.

KF Critic review of the early picks surfaced this as finding #6: "Closing .5 in isolation may just defer the same conversation by one bead." Subsequent sweep across all 6 downstream beads revealed 3 needed scope/description action; executing them in one pass took ~10 minutes total vs. an estimated ~3 × 5-minute discoveries scattered across future sessions. Pattern is immediately applicable to any decision-driven work queue with multiple dependent tasks.
