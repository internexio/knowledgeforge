---
title: Module 00 STATIC ZONE vs CC Rules — which zone reaches which deployment target
source_mode: expert → builder
novelty_type: transferable_framework
grounding_score: 0.90
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-07-02
domain: compiler
topic: multi-repo-pipeline
tags: [accretion, deployment, routing, classification, tier-0]
related_entries:
  - compiler/2026-06-10_extract-section-cc-marker-stop-condition-over-extraction.md
  - compiler/2026-06-14_bootstrap-divergence-intentional-on-static-to-compiled-promotion.md
  - methodologies/2026-06-10_kf-semver-three-surfaces-module-system-binding.md
---

# Module 00 STATIC ZONE vs CC Rules — Compilation Zone Routing

## What Was Learned

Module 00 (`00_orchestrator.md`) contains two zones with fundamentally different compilation behavior. Content placed in the wrong zone silently fails to reach certain deployment targets. This was the root cause of a Sev 2 audit finding (Task 3, 2026-07-02 KF 7.22.0 remediation).

## The Two Zones

**STATIC ZONE** (main module body)
- Survives compilation to **both** CC and CP unchanged
- Written verbatim into `00_Project_Instructions-Claude.md` (CP) and `.claude/agents/kf.md` (CC)
- Any behavioral directive that must reach ALL deployments goes here

**`## CC Rules` section** (near end of module file)
- Stripped from Claude Projects compiled output by `CP_STRIP_MARKERS` in `kf-compile.py`
- Compiled into `~/.claude/rules/kf-meta.md` for CC deployments only
- Content here is **CC-only** — CP deployments never see it

## The Bug This Caused

Always-On Behavioral Patches (Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution) and Per-Turn Mode Telemetry were added to `## CC Rules` in v7.7.0 and v7.6.0 respectively. This was correct for CC — they compiled into `kf-meta.md` and loaded as always-on rules. But CP deployments silently received neither directive. CP was operating without these patches from v7.6.0 through v7.21.0 (~8 version releases, approximately 3+ months).

The failure was **silent**: no error, no compile warning, no runtime signal. The compiled CP output simply lacked the sections.

## The Fix

Move any behavioral directive that must reach CP into the STATIC ZONE. The `## CC Rules` section can still emit the same content to `kf-meta.md` as a convenience (the CC Rules emitter remains valuable for the `~/.claude/rules/` integration), but it should be a **secondary reference** to canonical text in the STATIC ZONE — not the only copy.

Applied in 7.22.0: both sections now have canonical text in the STATIC ZONE; CC Rules section notes "see STATIC ZONE" rather than duplicating the full directive text.

## Decision Rule for Module Authors

> **"If this directive must reach a Claude Project user, it goes in the STATIC ZONE.
> If it's CC-only infrastructure (hook integration, settings fragments, rules file
> content), it goes in CC Rules."**

| Directive Type | Correct Zone |
|----------------|-------------|
| Behavioral patches (always-on reasoning rules) | STATIC ZONE |
| Per-turn telemetry markers | STATIC ZONE |
| Mode routing logic | STATIC ZONE |
| Hook integration (`kf-route.py`, `kf-stop-validator.py`) | CC Rules |
| Settings.json fragments | CC Rules |
| Rules file content that should ALSO reach CP | STATIC ZONE (primary) + CC Rules (emitter reference) |

## When This Applies

- Any time you add a behavioral directive to Module 00 and need it to reach Claude Projects
- Any audit of "why doesn't CP do X" — check which zone X lives in first
- Any new compiler target — check `CP_STRIP_MARKERS` in `kf-compile.py` to understand what that target strips

## When This Does NOT Apply

- CC-only infrastructure (hooks, settings) — CC Rules is the correct zone for these
- New modules (01–25) — they don't have the STATIC ZONE / CC Rules distinction; all content compiles via their tagged sections (`## CC Skill`, `## CC Doc`, etc.)

## Grounding

Root cause confirmed by examining `kf-compile.py` `CP_STRIP_MARKERS` constant (includes `CC_SECTION_MARKERS` plus `Section-Load Map`). Verified by diffing compiled CP output before and after the 7.22.0 fix — behavioral patch sections absent pre-fix, present post-fix. Confidence: 0.90 (direct code inspection + compile verification).

## Source Context

Discovered during KnowledgeForge 7.22.0 audit remediation (session 2026-07-02, bead kf-7.22.0-audit-remediation-2026-07-02). The bug manifested silently across 8+ version releases because the compilation pipeline never surfaced a warning. The decision framework here prevents recurrence by making the zone routing explicit: zones are tied to deployment targets, not to content type or convenience. Applies to Module 00 and its split-repo compilation flow (core → CC and CP); does not generalize to modules 01–25 which use tagged sections instead.
