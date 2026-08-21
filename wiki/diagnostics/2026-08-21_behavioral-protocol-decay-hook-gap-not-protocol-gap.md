---
title: Behavioral protocol decay in long sessions is a hook injection gap, not a protocol design gap
source_mode: strategist
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 3
pinned: false
created: 2026-08-21
domain: diagnostics
topic: workflow-discipline
tags: decay, quality-gate, classification
related_entries: []
---

# Behavioral Protocol Decay = Hook Gap, Not Protocol Gap

## The Pattern

When a behavioral rule (de-AI enforcement, decision tagging, citation requirements) starts working at session open but fades as the session grows, the instinct is to redesign the rule or add more protocol. That's the wrong diagnosis.

The actual cause: rules stated once in system prompt or session context get pushed back in the attention window as context grows. The model's compliance degrades not because the rule is wrong but because it's no longer prominently visible.

## The Correct Diagnosis

Ask: "Does the rule exist in the hook layer or only in the context layer?"

- **Context layer only** → will decay. No amount of protocol redesign fixes this.
- **Hook layer** (UserPromptSubmit injection) → re-asserted every turn, doesn't decay.

## The Fix

Move the rule from context (stated once) to hook injection (stated every turn). The rule text doesn't change — only its delivery mechanism does.

## When This Diagnostic Applies

- User reports "it worked at first but now it's not following the rule"
- Rule is behavioral (style, classification, citation) rather than structural (what to build)
- Session is long (>20 turns) or context-heavy

## When It Does NOT Apply

- Short sessions where context pressure is low
- One-time rules that don't need to persist (e.g., "for this response only, do X")
- Structural rules embedded in the system prompt at the harness level (already always-on)

## Implementation Pattern

Behavioral rules that need to persist across long sessions belong in a UserPromptSubmit hook that:

1. Reads the rule text from a stable source (not hardcoded)
2. Injects it into the prompt on every turn
3. Doesn't require Claude to re-learn or re-interpret the rule mid-session
4. Can be updated without session restart

This is distinct from Tier 0 system prompt rules (which are harness-level always-on) and from ad-hoc instructions in session context (which decay with context age).

## Grounding

Surfaced 2026-08-21 during kf-loop design session. The observation: "Too often it starts working but then decays. Eventually I am back to nagging the LLM." Resolved by identifying the hook gap and building the kf-loop enforcement layer. The diagnostic is transferable to any LLM behavioral enforcement context, not just KnowledgeForge.

## Source Context

Originated in the `kf-loop-enforcement` session as a strategic observation during the design of persistent behavioral enforcement across long Claude Code sessions. The pattern identifies why hook-based rule injection is necessary for behavioral persistence, not a workaround for poor protocol design.
