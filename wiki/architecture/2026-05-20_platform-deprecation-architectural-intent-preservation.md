---
title: Platform deprecation — preserve architectural intent, replace syntactic constraint
source_mode: builder + strategist
novelty_type: reusable_diagnostic + transferable_framework
grounding_score: 0.85
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-05-20
domain: architecture
topic: decision-classification
tags: trade-off-analysis, empirical, temporal, metadata-filter
related_entries:
  - wiki/patterns/2026-05-16_discriminated-enum-extension-7-point-checklist.md
  - wiki/migrations/big-bang-rename-supabase-fastapi-react.md
  - wiki/methodologies/2026-05-20_primary-source-vendor-guidance-reanchor.md
---

# Platform Deprecation — Preserve Architectural Intent, Replace Syntactic Constraint

## Core Pattern

When a paid-search, payment, cloud-infrastructure, or any third-party platform architecture depends on a deprecated mechanic:

**Separate the architectural intent from the syntactic implementation.** The architectural slot usually persists; the syntax updates; the constraint mechanism may shift (e.g., from syntax-bounded to negative-list-bounded + bid-bounded + monitoring-bounded).

## Concrete Instance: Google Ads Broad Match Modifier (BMM)

Google deprecated Broad Match Modifier (`+keyword +keyword` syntax) in February 2021 and absorbed the behavior into Phrase match. A "Catch-All Broad ad group with required modifiers + waterfall negatives" architecture, ported from 2008-era reference notes to 2026, requires:

### Step 1: Strip deprecated syntax

**Problem:** The `+` token is no longer accepted; import systems either reject it or auto-convert to Phrase match, silently changing match behavior.

**Fix:** Remove `+` prefix from keyword text before import. The intent (tokens must be present) doesn't change; only the syntactic form disappears.

### Step 2: Preserve the waterfall negative discipline

**What survives:** Ad-group-level negatives that block Exact + Phrase keywords from cannibalizing the Broad ad group. These are the **substantive constraint**, not the keyword syntax.

**Mechanism shift:** The constraint moves from syntactic ("keywords must contain these tokens") to semantic-plus-operational ("Google's broad-match expansion may go wide; compensate with elevated monitoring and circuit breakers").

### Step 3: Acknowledge expanded semantics

**Reality:** Pure Broad in 2026 expands more aggressively than BMM did in 2021. Traffic shape will differ.

**Compensation tactics:**
- **Tighter bid cap** — 50% of comparable Core ad-group CPC (forces quality-score and relevance to earn volume)
- **Ad-group-level tCPA override** — 1.5× campaign tCPA once Smart Bidding activates (constrains upside spend per conversion)
- **Elevated monitoring for 7 days post-launch:**
  - Daily search-terms pull (not weekly)
  - Impression-share circuit breaker if it exceeds architectural threshold (e.g., 25% of campaign)
  - Junk-traffic (low-relevance terms) response cadence within 24 hours

## When This Applies

- Porting a system design built against an old platform version to the current platform state
- Reference materials pre-date a platform-policy change (BMM 2021, expanded text ads → RSA 2022, max-conversion evolution, Google's match-type redefinition, etc.)
- A domain expert in the platform immediately flags the deprecated syntax during artifact review (this is the grounding signal — the practitioner's muscle memory catches the gap)
- The architectural reasoning still reads as sound *after* the syntax error is highlighted

## When This Does NOT Apply

**Red flag:** The architectural intent itself was load-bearing on the deprecated mechanic.

Litmus test: *Would this architecture make sense if you described it in platform-agnostic terms?*

- **Yes** → Port it. The slot is right; only the implementation is wrong.
- **No** → Redesign. The architecture was never sound; deprecation exposed the flaw.

**Examples of "No":**
- A system that relies on BMM's exact token-matching as a substitute for proper negative-list discipline. (Real issue: the ad group needs stricter negatives, not a syntax hack.)
- A pricing model built around a platform feature that was always a hack. (Real issue: the model needs rearchitecture, not a workaround.)

## Signal to Spot the Gap

- **Reference materials from before the deprecation date** — the user or codebase inherits patterns from an archived era
- **Immediate recognition by a platform expert** — domain practitioners have muscle memory about what changed and when
- **The reasoning survives verification** — after flagging the syntax error, the core intent checks out

This last signal is critical. If an expert says "yeah, that's wrong syntax, but the approach is still good," you're in the "preserve and port" case. If the expert says "no, that approach doesn't work anymore," you're in the redesign case.

## Companion Pattern

**Load-bearing assumption verification** — architectural assumptions about platform mechanics should be re-verified at the point of implementation, not inherited from reference material. This is especially critical when the reference is >18 months old in fast-moving platforms.

**Protocol:**
1. Identify assumptions (e.g., "BMM forces token presence")
2. Check the current platform docs (Google Ads, Stripe, AWS, etc.) to verify the assumption still holds
3. If the platform changed, classify the gap (syntax-only vs core-redesign)
4. Apply this pattern if syntax-only; redesign if core

## When This Pattern Becomes a Debt Risk

If reference materials are:
- > 3 years old in high-volatility platforms (paid-search, AWS, LLM APIs)
- > 2 years old in medium-volatility platforms (Stripe, cloud infra)
- > 5 years old in stable platforms (databases, core programming languages)

…then inherited patterns should be assumed risky until verified. Don't skip the verification step.

## Reusable Template

```
[System] deprecated [mechanic] on [date].
Architectural intent: [goal the old mechanic achieved]
Current platform form: [what replaced it, if anything]

Intent still valid? YES / NO
Syntax survives? YES / NO

If intent=YES, syntax=NO:
  - Replace syntax with [new form]
  - Shift constraint from [old mechanism] to [new mechanism]
  - Compensation tactics: [monitoring, caps, gates, etc.]

If intent=NO:
  - Redesign required
  - Root issue: [what the old system was hiding]
  - New approach: [architecture that works on current platform]
```

## Source Context

Grounded in 5SB paid-ads BMM correction (2026-05-20). A 25-year paid-search veteran reviewed an ad-group structure ported from iFloor 2007–2008 reference notes and immediately flagged the `+` syntax as deprecated. The architectural intent (catch-all broad ad group with discipline) was sound; only the syntactic form and constraint mechanism needed updating. This entry captures the pattern so the next cross-platform deprecation gets the same structured analysis.
