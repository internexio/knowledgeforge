---
title: Default to extension over sibling for existing infrastructure
source_mode: critic
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.7
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-13
domain: infrastructure
topic: component_scope
tags: patterns,methodologies,architecture,empirical,stable
related_entries:
  - infrastructure/2026-05-13_deployment-gap-audit-shadow-mode-patterns.md
  - infrastructure/2026-05-12_self-watchdog-autonomous-fix-cycles.md
  - patterns/2026-05-13_phased-god-module-split-facade-first.md
---

# Default to Extension Over Sibling for Existing Infrastructure

## The Pattern

When adding capabilities adjacent to an existing operational component (a script, daemon, watchdog, plist), the default move is **extend the existing component** rather than create a sibling. Sibling components require explicit scope justification — they introduce coordination gaps, dual-maintenance burden, and operator-confusion-by-multiplication.

The trigger for "sibling instead of extend" should be one or more of:

1. **Explicit scope conflict:** The existing component's spec explicitly forbids the new capability (e.g., a bash script cannot reasonably host a Python integration without substantial rewrites, and the Python piece is substantial enough to warrant autonomy).
2. **Scope dominance:** The new capability would dominate the existing component, making it a tail-wagging-dog situation.
3. **Reliability incompatibility:** The existing component has hard reliability constraints incompatible with the new feature's risk profile (e.g., a production-critical monitor cannot take on experimental instrumentation).
4. **Explicit partition:** The phase boundaries in the project spec explicitly partition the work into separate components (this is a design *decision*, not a side effect of organizational inertia).

If none of these triggers fire, default to extension. Operators expect **one script to do one thing for one domain**; sibling introduces a "which one do I check first?" cognitive cost and divergence in configuration, logging, and restart procedures.

## When This Applies

Any addition to:
- Cron-scheduled scripts (should a single cron line invoke one script or two?)
- launchd-scheduled jobs (should the operator understand both plists or just one?)
- Long-running watchdogs, monitors, or sweepers
- Bash helpers that other scripts source

Decisions about whether to extend or sibling will determine operator load and debugging friction for years to come.

## When This Does NOT Apply

- The existing component's spec explicitly designates "additive-only via sibling" — this is a **design commitment**, not a drift (e.g., happy-orchestrator.sh designates per-repo watchdog scripts as siblings by architectural intent).
- The two domains are genuinely orthogonal — not overlapping concerns (e.g., a polecat-watchdog for GasTown session heartbeats ≠ a separate watchdog for an unrelated subsystem with its own failure modes).
- The new capability has a fundamentally different scheduling cadence that cannot share with the existing component without architectural change (e.g., 30-second ticker vs. 30-minute ticker — different kernel wakeup cost; merging them into one plist requires buffering and state coordination that doesn't exist in the 30s ticker).

When the scheduling cadence differs *and* merging them would require non-trivial coordination machinery, that is a legitimate trigger for sibling.

## Grounding

Two concrete instances within [project] on the same day (2026-05-13):

### Instance 1: Iteration-loop v0 Phase 1 — Sibling Rejected, Extension Embraced

**Builder #1 plan** proposed `~/Scripts/[project]/scripts/iteration_loop_watchdog.sh` as a sibling to existing `polecat-watchdog.sh`, with its own launchd plist (`com.[project].iteration-loop-watchdog.plist`, StartInterval=300).

**Critic re-pass** flagged this as Sev 1 #2 — scope drift and orphaned scheduling responsibility. Evidence chain:

- README §1 Phase 1: "Implement reservation expiry (MAX_CYCLE_DURATION_SEC = 1800s default) — **owned by polecat-watchdog, not the pipeline.**"
- README §1 Phase 4: "polecat-watchdog extension. **Extends existing polecat FSM**."

The spec explicitly designated EXTENSION at Phase 4, not sibling at Phase 1. Builder's sibling-watchdog plan effectively pulled Phase 4's wiring into Phase 1 as a separate process, creating two sources of truth for the same concern: "has the iteration loop stalled?"

**Builder #2 plan** dropped the sibling. Phase 1 ships ONLY the Python heartbeat-check primitive (`scripts/iteration_loop_check_heartbeat.py` as a CLI tool). Phase 4 will wire it into the existing 179-line `polecat-watchdog.sh` (additive call after the existing gt-* scan loop), keeping operator responsibility in one place.

Result: Single launchd plist (polecat), single cron-line recipient (polecat.sh), single runbook for "why is the watchdog silent?"

### Instance 2: Healthcheck Watchdog Addition — Sibling Justified by Cadence Difference

Within the same session, a **pane-tailer watchdog** was added as a scheduled job (separate launchd plist, `com.[project].pane-tailer.plist`, StartInterval=30). This was a **justified sibling** because:

- The existing healthcheck plist runs every **5 minutes** (300s).
- The pane-tailer observation needs **30-second** granularity (detect stale buffers before they compound).
- Merging 30s and 300s cadences into a single plist requires state coordination logic that doesn't exist in either component — the operators would have to manage that coupling.

However, within the healthcheck script itself (same cron line, same plist), a **silent-session watchdog** was added as a function call (not a sibling script), because:

- Same 5-minute cadence as existing healthcheck.
- Related responsibility (server health + session health = operator concerns go together).
- Addition: ~15 lines in the existing script, no new plist needed.

This is the right call: the existing healthcheck already had responsibilities for process cleanup and server state; adding silent-session detection is a natural extension of "what should a health monitor check?"

## How to Apply

When Builder proposes adding a new operational component (script, plist, cron line), ask:

1. Is there an existing component in the same domain (same launchd label, same cron schedule, same long-running process)?
2. If yes, would the new capability fit naturally as a function call or loop iteration **after** the existing component's main logic?
3. If yes: default to extension. Add the code to the existing script. Update the existing plist if needed. Single responsibility, single operator touchpoint.
4. If no to any of the above: Escalate to sibling only if one of the four triggers above **explicitly fires**. Quote the spec, the cadence mismatch, or the reliability constraint.

**Critic should challenge sibling proposals** by:

- Quoting the spec's phase boundaries (README scope guardrails are the spec's voice saying "don't sibling-this").
- Checking the launchd label / cron line / process name — is there an existing component already doing this type of work?
- Verifying the scheduling cadence — does merging cadences require non-trivial coordination?
- Asking for the **explicit trigger** — which of the four did it hit? Make the architect articulate it.

## Related Patterns

- **[[deployment-gap-audit-shadow-mode-patterns]]** — same session; sibling components that lack scheduling validation will appear "deployed" but be silently inert until explicitly verified.
- **[[phased-god-module-split-facade-first]]** — when a component grows too large, facade-first keeps callers in one place during refactor; this pattern prevents siblings from accumulating in the first place by extending early.
- **[[self-watchdog-autonomous-fix-cycles]]** — once a component is extended rather than sibling'd, use external monitoring to detect when that single component stops functioning.

## Source Context

Discovered during Iteration Loop v0 Phase 1 specification review on 2026-05-13 (session `2026-05-13_iteration-loop-v0-phase-1-kf-chain`). The initial Builder proposal created a sibling watchdog that conflicted with the Phase 4 extension design in the README. Critic triage flagged it as Sev 1 #2 (scope drift). The pattern surfaced as a reusable decision framework during root-cause analysis: "should we create siblings, or extend?" The session also validated the inverse case (pane-tailer justifiably sibling'd due to cadence mismatch) and the right call within a component (healthcheck + silent-watchdog bundled in the same script).
