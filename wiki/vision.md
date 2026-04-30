---
type: vision
scope: project
status: active
version: 1
last_reviewed: 2026-04-30
half_life_days: 60
review_triggers:
  - roadmap_horizon_complete
  - phase_count_completed: 3
  - days_since_review: 60
---

# Project Vision

## What We're Building

KnowledgeForge is a compiled, multi-platform reasoning framework that gives Claude the right context at the right time — patching its predictable failure modes without adding overhead to requests that don't need it. It closes the gap between Claude Projects (semantic retrieval over all modules) and Claude Code (hook-driven, targeted context loading) while producing a single-source-of-truth that compiles to every platform.

## Why It Matters

LLMs fail predictably: they skip hypotheses, hide trade-offs, miss gaps, and over-engineer simple problems. Teams work around this with ever-longer system prompts — which make things worse by inflating context without improving targeting. KF patches exactly these failures via mode routing, selective loading, and structured elicitation — not by making Claude do more work, but by making it do the right work.

## Principles (max 5)

1. **Patch weaknesses, not scaffold strengths** — activate modes only when they prevent a known failure mode; if Claude handles it natively, don't add overhead.
2. **Deterministic first** — exhaust deterministic checks before invoking LLM judgment; before fixing, reproduce; before acting, triage.
3. **Single source of truth** — all platform variants compile from `knowledgeforge-core`; forks diverge, compilers stay honest.
4. **Context economy** — every token in the dynamic zone must earn its place; selective loading over exhaustive always-loaded context.
5. **Human in the loop for novel judgments** — KF routes, formats, and enforces structure; it does not autonomously generate strategy, vision, or irreversible decisions.

## What We're Explicitly Not Building

- Domain applications that depend on KF (COS, Science Advisor — separate products that use KF as infrastructure)
- A universal LLM framework (optimized for the Claude family; other providers serve as judges or routers only)
- Autonomous production agents operating without human direction on consequential systems
- A replacement for task managers, Git, or project planning tools (KF is an intelligence layer, not a project management layer)

## Revision Log

| Version | Date | What Changed | Why |
|---------|------|-------------|-----|
| 1 | 2026-04-30 | Initial creation | Proof-of-format seed for vision/roadmap system |
