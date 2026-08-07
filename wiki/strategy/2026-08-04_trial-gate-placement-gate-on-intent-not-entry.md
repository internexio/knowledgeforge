---
title: Trial gate placement — gate on intent not entry
source_mode: strategist,builder
novelty_type: transferable_framework
grounding_score: 0.75
staleness_risk: stable
importance: 3
pinned: false
created: 2026-08-04
domain: strategy
topic: trade-off-analysis
tags: conversion, freemium, trial-gate, ux-patterns, saas, onboarding
related_entries:
  - wiki/strategy/2026-07-29_court-lorenzini-trust-as-gtm-edge-framework.md
  - wiki/diagnostics/2026-07-29_saas-metrics-exclusion-two-tier-internal-account-filter-pattern.md
---

# Trial gate placement — gate on intent not entry

## Pattern

For freemium SaaS products with a meaningful free tier, place the trial/account gate at the first click of a high-value action rather than at product entry (homepage load, first visit, or onboarding flow).

**Wrong placement:** Homepage → "Start Free Trial" → email → product
**Right placement:** Homepage → free feature (immediate value) → "Full Analysis" click → trial gate → email → product

## Why it works

**Users who click "Full Analysis" have already seen value** — they've already been sold. The gate's job is capture, not persuasion. They've expressed specific intent for the gated feature and are at peak purchase momentum.

**Homepage visitors haven't seen value yet.** Gating them on entry forces them to commit before they understand what they're committing to. This inflates early drop-off and trains users to bounce from feature previews.

**The free tier acts as a live demo.** Every free interaction is a conversion touchpoint. It surfaces objections, demonstrates core value, and signals that the product works before asking for email/password.

## Implementation details

### Gate trigger
The trial modal fires on the first click of a gated action (e.g., "Full Analysis") by an unauthenticated user. Modal appears in-context over the existing page — no redirect, no loss of context. The user stays on their result.

### Modal design
Shows what they'll unlock (blurred content visible beneath the modal creates FOMO and demonstrates scope). Single email field. Copy frames the email as delivery of existing value: **"Where should we send your full report?"** not "Create an account."

### Magic link (not password)
Lower friction than password creation. User clicks link in email and lands directly on their specific result with the gated feature unlocked. **Critical:** the specific result URL must be preserved through the auth flow. Dropping users on a generic dashboard forces them to re-find their content and breaks the conversion chain.

### A/B test at the gate
Two CTAs work well here:
- **Friction minimizer:** "7-day free trial, no credit card"
- **Value-anchored:** "50% off first month"

They attract different segments; measuring which converts better informs pricing strategy and buyer psychographics.

### Soft expiry
When the trial expires, Phase 1 (free tier) continues to work. The gate reappears only for gated features. Copy focuses on what's available, not what was lost: **"Your trial ended, but your analyses didn't"** not "Your trial has expired."

### Viral loop
Make Phase 1 (free) shareable. Each share is a live demo for the recipient. When recipients visit the shared URL, they see Phase 1 and the trial gate — the sharer becomes an implicit advocate without referral mechanics.

## When this applies

- Product has a meaningful free tier (not just a time-limited full trial)
- The free tier demonstrates enough value to create upgrade intent
- The gated feature is a natural "next step" from the free experience
- You want self-serve conversion (not just outbound sales → demo flow)
- Target audience has low patience for early barriers to entry (founders, practitioners, researchers)

## When this does NOT apply

- Free tier has zero utility (password managers, team collaboration tools where value requires teammates)
- The product requires account creation for any interaction (personalization-first products)
- Enterprise-only products where all users need to be vetted before access
- Paid-first positioning where freemium would dilute price signal (per Lorenzini's "pricing as trust" framework)

## Anti-patterns

- **Gating at the homepage before any value is demonstrated** — no context for "why" the user should commit
- **Redirecting away from user's current context to a signup page** — loss of context and momentum
- **Hard-gating at trial expiry (blocking the free tier too)** — punishes expired users and destroys retention
- **Email + password form instead of magic link at the gate** — cognitive friction at peak purchase intent
- **Dropping users on generic dashboard after auth** — forces re-navigation to the specific result they wanted

## Trade-offs versus early-gate model

| Dimension | Early Gate (Homepage) | Late Gate (Intent-Click) |
|-----------|---------------------|--------------------------|
| **Signup volume** | Higher (captures visitors) | Lower (captures committed users) |
| **Signup quality** | Lower (curiosity-driven, no context) | Higher (intent-driven, value-proven) |
| **Free-to-trial conversion** | Lower (less context before upsell) | Higher (users already sold on value) |
| **Cost per acquired trial** | Higher (more signups, fewer convert) | Lower (fewer signups, more convert) |
| **Viral potential** | Limited (gated demo not shareable) | High (free results are shareable) |
| **Retention at expiry** | Lower (users haven't invested in workflow) | Higher (users have results invested in) |

The early-gate model optimizes for signup quantity; the late-gate model optimizes for conversion quality and viral expansion.

## Grounding

Derived from designing the COS free trial gate flow in August 2026 (cos-progressive-analysis-ux-redesign session). The strategist analysis explicitly surfaced this as the key placement decision: whether to gate at homepage entry or at the "Full Analysis" button click. The builder mode worked out the implementation details in full:
- Modal in-context rendering (no redirect)
- Magic link auth flow (preserve result URL through auth)
- Soft expiry model (free tier survives trial end)
- Viral loop mechanics (shareable Phase 1 results)
- A/B testing framework (friction minimizer vs. value-anchored CTAs)

Grounding score: 0.75 reflects one concrete product instance (COS), but the underlying principle (gate on proven value intent, not on entry) generalizes broadly to freemium SaaS. Staleness risk: stable because the cognitive principle (momentum, context, intent-matching) is not dependent on COS-specific infrastructure or trends.

## Related decision patterns

- **Court Lorenzini's Trust-as-GTM-Edge Framework:** Complements this entry. Lorenzini's anti-freemium stance ("pricing signals how you value yourself") sits in tension with the late-gate model presented here. Both are valid positioning moves — this entry assumes freemium is the chosen vehicle; Lorenzini documents the trade-off cost.
- **SaaS metrics exclusion:** Covers analytics filtering when internal accounts inflate funnel metrics (orthogonal concern; this entry assumes metrics are clean).

## Source Context

Strategist + Builder modes, cos-progressive-analysis-ux-redesign session, August 2026. The session's core question was "where should we place the trial gate?" — at homepage entry or at feature action. The strategist pass surfaced the intent-vs-entry trade-off; the builder pass worked out modal UX, auth flow, expiry model, and viral mechanics. Novlety: no existing wiki entry covers this specific placement trade-off or the implementation framework.
