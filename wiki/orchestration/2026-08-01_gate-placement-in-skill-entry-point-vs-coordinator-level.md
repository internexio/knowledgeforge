---
title: Gate Placement Decision — In-Skill vs Coordinator-Level Pre-flight Checks
source_mode: builder
novelty_type: transferable_framework
grounding_score: 0.75
staleness_risk: stable
importance: 3
pinned: false
created: 2026-08-01
domain: orchestration
topic: multi-stage-issue-workflow
tags: cos-skills, skill-design, agent-architecture, patterns
related_entries:
  - wiki/architecture/skills-vs-agents-design-boundary.md
  - wiki/orchestration/2026-05-30_preflight-cred-gap-detection-bead-build-halt-decompose.md
  - wiki/patterns/2026-06-25_agent-delegation-high-volume-research-scraping-tasks.md
---

# Gate Placement Decision — In-Skill vs Coordinator-Level Pre-flight Checks

## Pattern

When adding a mandatory pre-flight check to a skill-based system, deciding whether to embed the check INSIDE the entry-point skill (option a) or make it a coordinator-level prerequisite (option b) has clear tradeoffs. **Default to in-skill** because it guarantees the check runs automatically for every invocation without requiring callers to remember a separate step.

## Concrete Instance (COS Skills, 2026-08-01)

cos-analysis SKILL.md v2.4.0 adds an 8-dimension HAPE context pre-flight check:
- Cultural context
- Expertise level
- Emotional state
- Cognitive bandwidth
- Trauma/vulnerability
- Neurodiversity
- Life stage
- Platform/medium

Two placement options were considered:

**Option (a) — In-skill:** Embed the 8-dimension pre-flight as a gate inside cos-analysis/SKILL.md, before Tool 1 (Content Analysis). Runs automatically whenever cos-analysis is invoked. Check takes <5 seconds to assess.

**Option (b) — Coordinator-level:** Add the pre-flight as a separate step in any coordinator agent that calls cos-analysis. Callers must remember to invoke it before using cos-analysis.

## Decision Rationale

**Chose Option (a) — in-skill.**

**Why:**
- cos-analysis is the mandatory entry point for ALL COS content analysis work — there is no bypass
- Making callers responsible for the pre-flight creates a "caller must know" anti-pattern — callers can forget or bypass it
- The in-skill placement makes the check unavoidable and automatic
- The 8 dimensions take <5 seconds to assess and always affect downstream outputs (arousal targets, complexity ceiling, cos-ethics routing), so skipping them has real consequences

The decision maps to an inversion test: "If every caller had to remember to run the pre-flight separately, would the check reliably run?" Answer: no. The in-skill placement removes the dependency on caller behavior.

## When to Choose Option (a) — In-Skill

- The check is always relevant for ANY invocation of the skill
- The check's output directly shapes the skill's subsequent behavior (not orthogonal context)
- The check is fast (<5s) relative to the skill's main work
- You cannot trust callers to remember to run the check separately
- The check is specific to this skill's domain (not generic infrastructure)

## When to Choose Option (b) — Coordinator-Level

- The check is only relevant for CERTAIN invocation patterns, not all (e.g., only for streaming mode, only for async, only when routed through a specific orchestrator)
- The skill is called in many different contexts, some of which don't need the check
- The check is expensive and should be cached/reused across multiple downstream skills
- Callers belong to a small trusted set (3-5 internal agents) who you train on the requirement
- The check is generic infrastructure (auth, rate-limit precheck, quota validation) that should be centralized

## Anti-Pattern: Silently Bypassed Coordinator-Level Prerequisites

When a mandatory gate lives only at the coordinator level and callers are responsible for invoking it, the gate gets skipped when:
- A new caller (agent, external integration, test harness) bypasses the coordinator and calls the skill directly
- An async/batch invocation pattern bypasses the normal orchestration layer
- A developer adds a new call site and forgets about the prerequisite

The in-skill placement closes this gap: the check cannot be bypassed because it's part of the skill's contract.

## Generalizes To

**Any multi-layer system** (skill suite, agent chain, API workflow, microservice choreography) where you must decide whether a mandatory gate lives at the entry point vs. at the orchestration layer.

**General principle:** Embed checks at the narrowest scope where they're always relevant. If a check applies to ALL invocations of an entry point, embed it there. If it applies to only certain orchestration patterns, keep it at the orchestration layer.

## Corollary: Inverse Applies to Permissions

By contrast, a permission gate (auth, quota, capability assertion) that is SOMETIMES required should stay at the orchestrator level — not every skill invocation needs auth; only invocations from untrusted callers do. The in-skill vs coordinator choice depends on the gate's applicability scope, not its importance.

## Source Context

Pattern emerged 2026-08-01 during cos-analysis SKILL.md v2.4.0 design (cos-manager session). The 8-dimension HAPE check was initially proposed as a separate pre-call step in any coordinator using cos-analysis. Architectural review surfaced the risk: coordinators calling cos-analysis directly would skip the check, and test/batch invocations outside the normal orchestration layer would also bypass it. Embedding the check inside cos-analysis/SKILL.md (tool gate before Tool 1) guarantees it runs. Grounding: one concrete instance (COS Skills v2.4.0); staleness risk = stable because the principle applies broadly and is not dependent on COS-specific infrastructure.

## Related Decision Patterns

- **Skills vs Agents Design Boundary:** When to demote a component to a skill in the first place
- **Pre-flight cred-gap detection:** What pre-flight checks to run (orthogonal decision; this entry addresses WHERE they live)
- **Agent delegation for high-volume tasks:** When to orchestrate vs when to embed capability in the calling layer
