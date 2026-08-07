---
title: KF CC Deployment Parity Check — 7-Check Deterministic Audit Methodology
source_mode: expert
novelty_type: reusable_diagnostic
grounding_score: 0.82
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-11
domain: diagnostics
topic: deployment-validation
tags: [deployment, validation, audit, parity-check, knowledgeforge]
related_entries:
  - compiler/2026-07-02_module-00-static-zone-vs-cc-rules-compilation-zone-routing.md
  - compiler/2026-07-11_kf-mode-marker-must-land-in-first-20-lines-compiled-agent-files.md
  - infrastructure/2026-07-06_bash-orchestrator-config-array-loaded-at-startup-restart-required.md
---

# KF CC Deployment Parity Check — 7-Check Deterministic Audit Methodology

## What It Is

A structured 7-check deterministic audit for validating whether a knowledgeforge-cc compiled artifact deployment is in parity with a target source version. All checks are grep/read only — no LLM judgment required. Can be run by any agent or scripted without human intervention.

## The 7 Checks (as executed for 7.22.0 target)

### Check 1 — Identity strings

Verify version strings in three locations:
- Source repo `modules/00_orchestrator.md` metadata header
- Compiled `~/.claude/agents/kf.md` compile header (line 6)
- Compiled `~/.claude/rules/kf-meta.md` compile header (line 4)

Expected: compiled files ≥ target version. Flag if at 7.9.0 or earlier (stale compile).

```bash
grep -n "version" ~/Scripts/knowledgeforge-core/modules/00_orchestrator.md | head -3
grep -n "version" /path/to/knowledgeforge-cc/.claude/agents/kf.md | head -3
grep -n "version" /path/to/knowledgeforge-cc/.claude/rules/kf-meta.md | head -3
```

### Check 2 — Task 3 relocation (Always-On + Telemetry in kf-meta.md)

Confirm Always-On Behavioral Patches and Per-Turn Mode Telemetry are in kf-meta.md (not hand-maintained in kf.md). Compile header should show `section: CC Rules | type: rules`.

```bash
grep -n "Always-On Behavioral Patches\|Per-Turn Mode Telemetry" ~/.claude/rules/kf-meta.md
head -6 ~/.claude/rules/kf-meta.md  # check compile header
```

### Check 3 — Telemetry spec level (7.8.0 additions)

Confirm two specific 7.8.0 clauses in kf-meta.md:
- "Response length does not exempt" (Case 2 of telemetry placement)
- Marker debt rule k+1 (Case 3 of telemetry placement)

```bash
grep -n "Response length does not exempt\|k+1\|marker debt" ~/.claude/rules/kf-meta.md
```

### Check 4 — M16 metric #10 variant count

Source M16 (`modules/16_operational_bounds.md`) should list 9 Critic/Expert variants under `per_variant:`. Compiled CC M16 may be condensed (quick-reference only); check source to confirm the 9-variant list is present.

```bash
grep -A12 "per_variant:" ~/Scripts/knowledgeforge-core/modules/16_operational_bounds.md
```

Expected 9: `critic.regular`, `critic.linter`, `critic.audit`, `critic.adversarial`, `expert.regular`, `expert.infrastructure`, `expert.ml_infrastructure`, `expert.era`, `expert.research`.

NOTE: Compiled CC M16 is a 39-line condensed doc — omits per_variant table. This is expected behavior of the condensed format, not a bug, unless per_variant is explicitly required in CC docs.

### Check 5 — M03 Handoff Contract Registry count

Source M03 (`modules/03_coordination_patterns.md`) should have 13 contracts including C/D/E (`hc-expert-to-strategist`, `hc-expert-research-to-expert-regular`, `hc-expert-research-to-builder`).

```bash
grep -c "^  - id: hc-" ~/Scripts/knowledgeforge-core/modules/03_coordination_patterns.md
grep -n "^  - id: hc-" ~/Scripts/knowledgeforge-core/modules/03_coordination_patterns.md
```

### Check 6 — M05 research variant deployment mode (MCP connectivity)

This is the most common failure point. Asta MCP `enabled: true` in `kf-integrations.yaml` is necessary but NOT sufficient — the MCP must also be registered in `~/.claude/settings.json` or `.mcp.json`. Without registration, research variant runs permanently degraded.

```bash
grep -A2 "asta:" ~/.claude/kf-integrations.yaml
grep -i "asta" ~/.claude/settings.json ~/.mcp.json 2>/dev/null
```

If `settings.json` has no Asta entry → FAIL. Fix: register in `settings.json` (infra config, no recompile needed).

### Check 7 — check-identity-drift.py

Run pre-commit hook standalone against current tree.

```bash
python3 ~/Scripts/knowledgeforge-core/scripts/check-identity-drift.py; echo "EXIT:$?"
```

Expected: `EXIT:0`

## Results from 2026-07-11 Audit (7.22.0 Target)

| Check | Result | Notes |
|-------|--------|-------|
| 1. Identity strings | PASS | Compiled at 7.26.0 (above 7.22.0), repo M00 at 7.22.0 |
| 2. Task 3 relocation | PASS | Both sections in kf-meta.md, compile header confirms |
| 3. Telemetry spec | PASS | Both 7.8.0 clauses present |
| 4. M16 variant count | PARTIAL | Source: 9 correct. Compiled M16 condensed, omits per_variant |
| 5. M03 contract count | PASS | 13/13 incl. C/D/E |
| 6. Research variant | FAIL | Asta not in settings.json; permanently degraded |
| 7. Identity drift | PASS | EXIT:0 |

## When This Applies

- Validating a CC deployment after compile from knowledgeforge-core
- Responding to parity check requests from other agents (Orchestra inbox)
- Pre-session verification when working in a new Claude Code environment
- Diagnosing "why does the research variant feel degraded" complaints
- Verifying that a compiled artifact matches a known-good source version

## When This Does NOT Apply

- Claude Projects (CP) deployment — different compilation path, no settings.json
- Checking CP parity (CP has no hooks, no compiled agents folder)
- First-time install verification (use install.sh output check instead)
- Comparing two different CC deployments' feature coverage (use diff tooling instead)

## Key Finding: Two-Tier MCP Connectivity

**Check 6 is the most common gap.** `kf-integrations.yaml` `enabled: true` only gates the KF hooks — it does NOT register the MCP server itself. The MCP must be separately registered in `~/.claude/settings.json` under `mcpServers` or via `.mcp.json`. Always verify both layers.

This discovered during the 2026-07-11 audit: the research variant was feature-complete in the compiled agent, but the underlying Asta MCP was never registered in the local settings, causing silent degradation (no error, but all research-variant calls fell back to degraded paths).

## Source Context

Developed during kf-vscode-phase3-orchestra-parity-audit session (2026-07-11). The 7-check suite emerged from validating that a new CC deployment in a VSCode agent environment matched the published 7.22.0 specification. Check 6 (MCP connectivity) uncovered a widespread configuration gap that had been invisible because the system failed gracefully (no errors, just slower research mode). The methodology is deterministic — no LLM judgment required — so it can be automated or embedded into CI/CD validation pipelines.
