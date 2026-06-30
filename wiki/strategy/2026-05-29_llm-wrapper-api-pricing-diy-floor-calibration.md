---
title: Pricing LLM-wrapper APIs against the DIY-floor constraint
source_mode: expert
novelty_type: transferable_framework
grounding_score: 0.78
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-05-29
tags: pricing, strategy, trade-off-analysis, api
related_entries: []
domain: strategy
topic: trade-off-analysis
---

# Pricing LLM-Wrapper APIs Against the DIY-Floor Constraint

## Problem

When pricing an API that wraps LLM calls (e.g., analysis, scoring, classification, generation), product teams often anchor to competitor pricing or enterprise-SaaS psychographics. This approach misses the binding constraint: developers can always build a wrapper themselves for the cost of raw LLM calls (~$0.005–0.02 per structured call at 2026 cheap-model rates, accounting for prompt engineering, token waste, and retries).

This DIY floor caps your ceiling. Price above it, and integrators wrap their own LLM. Your margin gets compressed between:
- **Floor:** Per-call COGS (your infrastructure + LLM API costs)
- **Ceiling:** DIY cost for an integrator to build the same wrapper

## Method

### Step 1: Calculate the True DIY Floor

Estimate what a developer pays to wrap an LLM themselves:

```
DIY per-call cost = (prompt_tokens + avg_output_tokens) / 1M × model_cost_per_1M_tokens
                    + retry_waste_factor (1.15–1.4)
                    + prompt_engineering_amortized (add 20–30% for tuning overhead)
```

**Example (2026 rates):**
- Claude Haiku: $0.80 per 1M input tokens, $4 per 1M output tokens
- Structured extraction task: 500 input + 200 output tokens per call
- Retries/waste: 1.25× multiplier
- DIY cost = ((500 × 0.80 + 200 × 4) / 1M) × 1.25 = $0.0015 per call
- With engineering overhead (25%): $0.00188, round to **$0.002 per call**

Cheap-model range (Gemini Flash, Haiku, smaller open models): **$0.002–0.01 per call**
Mid-tier (Sonnet, GPT-4o-mini): **$0.01–0.02 per call**

### Step 2: Set PAYG Pricing as a Multiple of DIY

Never price PAYG below DIY (you lose money on every call). Price at **2–4× the DIY floor**, not at enterprise psychographics:

```
PAYG_price_per_call = DIY_floor × 2.5  (modest calibration + convenience markup)
```

**Do NOT attempt:**
- $0.50–1.00 per call for cheap-model wrapping (you're pricing like a premium service when you're a commodity wrapper)
- Anchoring to enterprise API competitors ($500+/mo) when your product is a thin wrapper over commodity LLMs

**Example pricing:**
- DIY floor: $0.002 per call
- Your PAYG: $0.005–0.008 per call (2.5–4× markup for calibration quality + uptime)
- Integrator's ROI: Uses your API, saves engineering time vs. building their own wrapper

### Step 3: Audit Subscription Tiers for Margin Bleed

When offering subscription tiers with bundled credits, recalculate margin arithmetic:

```
Tier: $29/month with 10,000 credits
Cost per call to you (COGS): $0.002
Per-tier COGS: 10,000 × $0.002 = $20
Revenue: $29
Gross margin: ($29 - $20) / $29 = 31%

Tier: $99/month with 100,000 credits
Cost per call to you: $0.002
Per-tier COGS: 100,000 × $0.002 = $200
Revenue: $99
Gross margin: ($99 - $200) / $99 = NEGATIVE 101% (unsustainable)
```

The second tier bleeds negative margin. Too-generous credit allotments compress effective per-call price below sustainable levels. Always **re-derive margin arithmetic from the credit→$ rate**, not from a blanket "70% gross margin target."

### Step 4: Verify Differentiation Justifies Markup

The calibration/quality markup (2–4× DIY floor) only holds if you genuinely deliver better results. Check:

```
Does your wrapper provide:
- ✓ Better accuracy than naive prompt engineering? (measured, not claimed)
- ✓ Lower latency via caching + request coalescing?
- ✓ Failure recovery (retries, fallback models)?
- ✓ Structured output validation before billing the call?

If no to multiple above → your moat is thin.
Reduce markup toward 1.2–1.5× DIY floor, or accept commoditized pricing.
```

Real example: A wrapper that achieves 92% accuracy when naive prompting yields 78% can justify 3–4× markup. A wrapper that just passes through to Claude with default parameters cannot.

## When This Applies

- Launching a new LLM-based API service (analysis, extraction, scoring, generation)
- Repricing an existing LLM-wrapper API to match market realities
- Evaluating whether a subscription tier is economically viable
- Building a pricing model for internal/embedded LLM-based services with per-call costs
- Deciding whether to build or buy LLM wrapper functionality

## When This Does NOT Apply

- APIs where LLM calls are a small component of total COGS (e.g., hybrid system with heavy compute/storage overhead — LLM is <5% of cost)
- Products that don't wrap an LLM (e.g., pure classification database, no generative component)
- Internal-only tools with no pricing model
- Scenarios where competitor pricing is contractually binding (e.g., licensing agreements)

## Constraints & Failure Modes

**Margin bleed from subscription tiers:** Generous credit allotments can drive effective per-call price BELOW COGS. Always recalculate.

**Thin differentiation:** If your wrapper is transparent passthrough (no calibration, no validation), DIY cost is your ceiling. You cannot sustain 2–4× markup without commoditizing.

**Underestimating retry/waste factor:** Naive calculations ignore prompt failures, token waste, and re-runs. Real DIY cost is higher than raw LLM API rates. Add 1.2–1.4× multiplier.

## Source Context

Productizing an LLM-based analysis service. Initial pricing anchor was enterprise SaaS comparables ($500+/mo), but customer research revealed DIY feasibility: "We could wrap Claude ourselves for ~$100/month infrastructure." This compressed ceiling. Re-anchored to DIY floor ($0.002 per call, 10K/month tier = $20 COGS) + modest markup (3–4×) = $0.006–0.008 per call = $60–80/month tier. Now defensible against DIY substitution and achieves healthy margin.
