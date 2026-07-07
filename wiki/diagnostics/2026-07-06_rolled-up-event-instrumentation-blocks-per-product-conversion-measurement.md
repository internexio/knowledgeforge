---
title: Rolled-up event instrumentation gap — a single event name across N products blocks per-product conversion measurement
source_mode: debugger
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: stable
importance: 4
pinned: false
created: 2026-07-06
domain: diagnostics
topic: analytics-instrumentation
tags:
  - analytics
  - instrumentation
  - funnel-measurement
  - GA4
  - event-tracking
  - kill-switch-design
  - conversion-attribution
related_entries:
  - diagnostics/2026-05-31_per-entity-status-classifier-unmeasured-vs-measured-null.md
  - diagnostics/2026-05-25_multi-dimensional-unique-schema-defaults-silent-flattening.md
  - patterns/2026-05-11_audit-log-event-vocabulary-mismatch.md
---

# Rolled-Up Event Instrumentation Gap — A Single Event Name Across N Products Blocks Per-Product Conversion Measurement

## Pattern

When a product suite fires a single generic conversion event (`free_tool_run`, `signup`, `demo_requested`, etc.) across N different products/surfaces without a distinguishing parameter, per-product conversion measurement is impossible from analytics alone. Product-side event splitting must happen BEFORE any downstream per-product kill-switch or funnel analysis can operate.

## Why It Matters Early

Setting kill-switch thresholds for a redesign (e.g., "if Product A conversion doesn't 2x by Week 4, abandon the retrofit") is meaningless if the analytics stack cannot distinguish Product A completions from Product B completions. You'll see pageviews per URL, but the actual conversion event (the thing that matters) will be rolled up.

The failure mode is silent: the analytics platform reports events correctly, dashboards render, event counts trend — but every per-product downstream decision built on the conversion event is unfounded.

## Fix

Two options, both valid:

1. **Add a `product_name` / `tool_name` parameter to the existing event** when it fires (per-fire attribution). Keeps the event ontology clean but requires downstream analytics to filter by parameter.

2. **Fire per-product event names** (`product_a_completed`, `product_b_completed`, etc.). Clutters the event namespace but makes per-product reports trivial.

Choose based on how the downstream reporting is built — GA4/Amplitude/Mixpanel handle either fine, but the query complexity differs.

## Diagnostic Procedure (Apply BEFORE Setting Kill-Switches)

1. Pull last 14+ days of event counts by name from the analytics platform.
2. Identify events that correspond to conversion goals.
3. For each conversion event, check: does the event name distinguish between the products/surfaces you plan to attribute?
4. If NO → block kill-switch design until instrumentation is split. Route the fix to the product-owner team as a P1.
5. If YES → proceed with kill-switch design using per-product baselines.

## Grounded Example (client-project, 2026-07-06)

GA4 event inventory for `semalytics.com` showed the `free_tool_run` event fires for ALL free tools (Ad Copy Analyzer, Email Subject Analyzer, MBTI-to-OCEAN, DISC assessment, personality-type test, cold outbound analyzer) — 7 tool pages total. Event count: 2 fires in the last 14 days. Cannot distinguish which tool ran without a `tool_name` parameter.

Meanwhile pageview data was well-differentiated:

- `/tools/ad-copy-analyzer/` = 1 pageview
- `/tools/email-subject-analyzer/` = 2 pageviews
- `/tools/mbti-to-ocean/` = 5 pageviews

Pageview-per-URL is easy. Conversion-per-URL is blocked until the event splits.

Impact on that session's work: Q3 kill-switch design required a note that "Week 2 checkpoint (7/19) can only measure PAGEVIEWS per tool, not conversions per tool, until per-product event splitting ships from product side." This was routed as a cross-repo P1 to the [project] product team.

## When It Does NOT Apply

- Single-product platforms (only one funnel to measure — no attribution ambiguity)
- Products where the CONVERSION happens on a distinct URL per product (URL alone attributes)
- Analytics platforms with automatic URL-parameter tagging that surfaces via reports (GA4 pagePath + eventName cross-tabulation catches some but not all cases — verify the specific query before relying on it)

## Cross-References

Family relationship: this is another instance of the "distinguish the N similar things" hygiene class:

- Multi-target deploys — "pushed" without naming targets (global CLAUDE.md workflow rule)
- `patterns/2026-05-11_audit-log-event-vocabulary-mismatch.md` — read-side must accept routing-suffixed forms (write-side had the suffix; here the write-side lacks a distinguisher altogether)
- `diagnostics/2026-05-25_multi-dimensional-unique-schema-defaults-silent-flattening.md` — SQL analog where default column values collapse multi-dimensional data
- `diagnostics/2026-05-31_per-entity-status-classifier-unmeasured-vs-measured-null.md` — reporting analog where "unmeasured" and "measured-null" get lumped together

## Rule of Thumb

Before designing a per-product decision gate (kill-switch, budget reallocation, prioritization ladder), verify that the underlying conversion event can be sliced along the product axis. If it cannot, the gate is meaningless until instrumentation ships. Route the instrumentation fix upstream as a hard blocker — don't set kill-switch thresholds on data you cannot actually measure at that resolution.
