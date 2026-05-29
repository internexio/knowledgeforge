---
title: Feasibility-gate a validation thesis on data power before building the harness; defer-don't-kill when untestable
source_mode: strategist
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-28
domain: research-methodology
topic: experiment-design, decision-framework
tags: validation, experiment-design, statistical-power, decision-framework, research-methodology
related_entries:
  - methodologies/2026-05-27_supervise-first-real-data-run-autonomous-loops.md
  - methodologies/2026-05-14_healthy-system-gate-trap-empirical-thresholds.md
  - methodologies/2026-05-23_salvage-vs-revert-mid-execution-conflict-framework.md
---

# Feasibility-Gate a Validation Thesis on Data Power Before Building the Harness; Defer-Don't-Kill When Untestable

## The Problem

A team invested in a multi-phase validation harness (retrospective correlation = Phase 0b, prospective A/B = Phase 0c) to test a product's core thesis: "COS-derived audience scoring improves Google Ads performance." Only AFTER building 0b and running it did the real blocker surface: the single available advertiser was far too small to power ANY version of the test. Weeks of work, zero actionable result.

The lesson is transferable: before building a validation methodology, run a back-of-envelope **power / volume feasibility check** against the data you can actually access — for BOTH the retrospective and prospective forms of the test. If neither can reach statistical power on available data, building the harness is wasted effort.

## The Framework

### Step 1: Enumerate Validation Forms

List all the ways you plan to validate the thesis:
- Retrospective (correlation on historical data)
- Prospective (A/B test on new data)
- Qualitative (user interviews, observational)
- Comparative (vs. competitor, vs. baseline)

Focus the power check on the quantitative forms — qualitative validation has different rules.

### Step 2: For Each Quantitative Form, Calculate "Minimum Detectable Effect at Available N"

**For correlations (Pearson's r, Fisher-z):**
- Collect sample size: How many data points can you access? (n = number of ads, number of days, number of accounts — whichever is the bottleneck)
- At that n, what is the minimum |r| you can detect at 80% power?
- Formula shortcut: `r ≈ sqrt(chi_sq(df=1, 0.05/2) / n)` for symmetric two-tailed test, or use online calculators

**For A/B tests (proportions, means):**
- Collect sample size per arm: How many observations (impressions, clicks, conversions) per arm?
- At that per-arm n, what is the minimum effect size (Cohen's d, relative lift %) you can detect at 80% power?
- Formula: use standard power calculator (G*Power, Python's statsmodels, or web tools)

### Step 3: Define Your Pre-Registered Effect Size (the Thesis)

Before analyzing, decide: **What effect size would you consider proof that the thesis is true?**

Examples:
- "A correlation of r ≥ 0.20 between COS score and ad performance"
- "A 15% relative lift in click-through rate (prospective A/B)"
- "An increase in conversion rate from 2% to 2.3%"

This is your ground truth. Write it down.

### Step 4: Compare: Available N vs. Required N

- **Available N:** The sample size you calculated in Step 2
- **Required N:** The sample size needed to detect your pre-registered effect at 80% power
- **Ratio:** required_n / available_n

### Step 5: Make the Gating Decision

#### If required_n / available_n ≤ 1.2 (Your data is well-powered or over-powered)

**Proceed.** You have sufficient data to run the test and reach a conclusion.

#### If 1.2 < required_n / available_n ≤ 5 (Borderline under-powered)

**Proceed with caveats.** Your test will reach a conclusion, but the **power to detect your pre-registered effect is lower than 80%** — perhaps 50–75%. Any null result is inconclusive (the effect might exist but be too small for you to detect). Any positive result is real (fewer false positives in low-powered tests). Explicitly note in your protocol: "This test is under-powered; null results are inconclusive; positive results are confirmatory."

#### If required_n / available_n > 5 (Severely under-powered)

**DEFER, do not build.** Your test cannot reach power on available data. The right move:

1. **Name the problem explicitly:** "The thesis is **untested, not disproven.** We lack sufficient data access to power a valid test."
2. **Do not build infrastructure to validate it on insufficient data.** The harness will run, but the result will be a null-from-underpowering misread as a false kill signal.
3. **Proceed with the thesis on its validation-independent value** — if the product is good for other reasons (cost, speed, user satisfaction, architectural simplicity), ship it. Gate the premium claim (the unproven differentiator) separately.
4. **Plan for re-validation when data access improves** — e.g., "Once we have real customer accounts running this feature, we'll revisit the A/B test on their larger data volume."

## Concrete Grounding

**Retrospective (Phase 0b):** After a data fix (recovering removed ads), the analyzable sample reached n=26 for ONE advertiser. Minimum detectable |r| at n=26, 80% power ≈ 0.53. The pre-registered threshold was r=0.20. Required n to detect 0.20 at 80% power ≥ 194 ads across ≥2 independent advertisers. Ratio: 194 / 26 ≈ 7.5. **Verdict: severely under-powered.** Nothing survived FDR correction. Inconclusive, not a verdict.

**Prospective (Phase 0c):** The specification needed ~20K impressions per arm (≥700 impr/day per ad group) for a powered two-arm A/B test. The advertiser's largest ad group ran ~51 impr/day — **approximately 14× short**. A powered test would take 3+ years on that volume. Same root cause as 0b: no high-volume advertiser in the available dataset.

**Decision:** DEFER, not kill. The product proceeds on its validation-independent value (cost-savings, deployment speed). The unproven differentiator's premium claim stays gated until a higher-volume data source (real customer accounts) makes the test feasible.

## When This Applies

- Before committing resources to build a validation harness (retrospective analysis, A/B test, survey, experiment)
- When the thesis' validation depends on a fixed, limited dataset (your customer base, historical data, a beta group)
- When an early null result could kill a promising-but-unproven feature
- When you want to distinguish "we tested it and it failed" from "we never had enough data to test it fairly"

## When This Does NOT Apply

- When data volume is plentiful and you have already confirmed power ≥ 80% (just run the test)
- When the thesis is cheap to test directly — e.g., a UI change with immediate user feedback. Skip the power ceremony for fast iteration.
- When you're testing on synthetic/staging data where you control volume. Inject more data.
- Qualitative validation (interviews, observational studies). Power analysis applies to quantitative methods only.

## Practical Implementation

### Minimal feasibility checklist

Before opening an editor to build a validation harness:

1. **What is the thesis?** (Write it down in one sentence.)
2. **What quantitative forms of evidence would prove or disprove it?** (List all of them.)
3. **For each form: What is n?** (Sample size of the data you can access, right now.)
4. **For each form: What is the required n to detect your pre-registered effect at 80% power?** (Use an online power calculator if you don't have formulas memorized.)
5. **For each form: Is required_n / available_n > 5?** (If yes, any result will be inconclusive.)
6. **If ALL forms are required_n / available_n > 5: STOP. Defer. Write down why in the ticket or plan document.** (Do not build the harness.)
7. **If at least ONE form is powered (required_n / available_n ≤ 5): Proceed** — that one form will give you a conclusion.

This checklist takes 30–60 minutes for most product theses. Building a harness without it can waste weeks.

## The Key Distinction: Untested vs. Disproven

**Untested thesis:** You lack sufficient data to power a test. The thesis could be true, false, or meaningless — you cannot tell. Do not ship a high-confidence claim on an untested thesis.

**Disproven thesis:** You ran a powered test and got a null result (or a negative result). The null is real; the thesis is false, or the effect is smaller than you needed.

The boundary matters:

- Kill a **disproven** thesis — you have evidence.
- **Defer** an **untested** thesis — you do not have evidence yet, but that doesn't mean it's false. Gate the premium claim; ship the validation-independent value.

If you build a harness on insufficient data and get a null, you will be tempted to read it as disproven. It is not. It is untested-with-noise. Avoid the trap.

## Related Patterns

- **Healthy-system-gate-trap** (`methodologies/2026-05-14_healthy-system-gate-trap-empirical-thresholds.md`) — gates that never trigger because the success condition doesn't accumulate data in working systems. This pattern avoids gates entirely on under-powered tests.
- **Supervise the first real-data run** (`methodologies/2026-05-27_supervise-first-real-data-run-autonomous-loops.md`) — once power is confirmed, validate the harness code before autonomous execution.
- **Salvage-vs-revert decision framework** (`methodologies/2026-05-23_salvage-vs-revert-mid-execution-conflict-framework.md`) — when a validation result mid-execution conflicts with a prior assumption, how to decide what to keep.

## Source Context

Session: `cos-on-ads-wedge-validation` (client-project Phase 0b/0c). A product team attempted to validate "COS-derived audience scoring improves Google Ads performance" via a retrospective harness (Phase 0b) and prospective A/B test design (Phase 0c). After building 0b and running it, the data volume bottleneck became clear: both validation forms were severely under-powered on available advertiser data. The framework emerged from explicitly deferring the validation (naming it untested, not disproven) and proceeding with the product's validation-independent value (cost-savings, faster-deployment claims). The distinction between untested and disproven, and the decision to defer rather than kill, is the core reusable insight.
