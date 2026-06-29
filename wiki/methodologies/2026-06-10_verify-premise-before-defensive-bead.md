---
title: Verify the premise before filing a defensive/hardening bead
source_mode: rule_promotion
source_session: redacted
source_fingerprint: rules/verify-premise-before-defensive-bead.md@2026-06-10
novelty_type: behavioral_guardrail
grounding_score: 0.92
staleness_risk: stable
importance: 5
pinned: false
created: 2026-06-10
domain: methodologies
topic: verification
tags: methodology, verification, premise-checking, defensive-bead, anti-rework, bead-management, read-full-context
related_entries:
  - methodologies/2026-05-26_deterministic-scan-before-claiming-refactor-audit-beads.md
  - methodologies/2026-06-09_read-bead-status-before-claiming-verify-explicit-deferral.md
  - methodologies/2026-06-18_cross-scope-search-blindness-operator-insistence-as-broaden-signal.md
  - methodologies/2026-05-13_verify-audit-claims-before-designing-fix.md
---

# Verify the Premise Before Filing a Defensive / Hardening Bead

## The Rule

When the bead's body is "X is missing and should be added," **read the FULL relevant function/route/config** — not just up to where the obvious end-of-block appears. A `Read` that stops at line N can miss a `->where()` constraint, a `middleware()` chain, an `@property` declaration on line N+5 that already addresses the concern.

**Symptom of skipping this:** bead gets filed, then closed minutes/days later as "already done — premise was wrong."

## Verified Examples

**2026-05-26 (tuan-dev-x56):** Filed claim that Laravel catch-all route had no slug constraint; the constraint had existed since the route's first commit (2025-10-14, line 404), but the earlier Read window stopped at line 399. Bead closed immediately as "premise wrong."

**2026-06-10 ([project]-2quf):** Filed claim that `bd` is a zsh alias not on launchd PATH causing exec-consumer failures. Verification ran `which bd` and `type bd` — `bd` is a real binary at `/opt/homebrew/bin/bd`, on PATH. Real cause was bd embedded-mode lock contention.

**2026-06-10 ([project]-fys7):** Filed claim that nw-maintenance.sh was pruning the bridge's stdout. Verification ran `grep -nE "tmp|prune|rm" scripts/nw-maintenance.sh` — the script never touches /tmp. Real cause was macOS `com.apple.tmp_cleaner`.

In all three cases the wasted work was a filed bead + investigation of a non-problem. The correct move cost one extra `Read` or `grep`.

## Application

Before filing any bead whose title starts with "X is missing", "X lacks Y", or "add Z to X":

1. Read the FULL file or function, not just the obvious entry point
2. Run a targeted search (`grep -n "constraint\|middleware\|where\|@property"`) for the feature you're claiming is absent
3. Only file the bead after the search confirms the gap

## Scope

Applies to **defensive/hardening beads** — beads that add a guard, constraint, or check that you believe is currently absent. Does NOT apply to:
- Beads that extend clearly absent functionality
- Beads filed after an actual failure (the failure is the premise verification)
- Refactoring beads where the current code is observed directly

## Project-Specific Extensions

Project-local `.claude/rules/` may add project-specific verification procedures with concrete commands. See `<[project]>/CLAUDE.md` "Pre-claim verification rule" for an example specialization (`<[project]>` resolves to `~/Scripts/[project]` on laptop, `~/Mini/[project]` on Mini).

## Composes With

- **[[2026-05-26_deterministic-scan-before-claiming-refactor-audit-beads]]** — same "verify before you claim" family; that entry covers refactor/audit beads, this one covers defensive/hardening beads.
- **[[2026-06-09_read-bead-status-before-claiming-verify-explicit-deferral]]** — related verification discipline applied to bead status rather than code state.
- **[[2026-06-18_cross-scope-search-blindness-operator-insistence-as-broaden-signal]]** — same family: both address failure modes where an agent's too-narrow read produces a confident but wrong negative finding.
- **[[2026-05-13_verify-audit-claims-before-designing-fix]]** — same shape applied to audit findings.
