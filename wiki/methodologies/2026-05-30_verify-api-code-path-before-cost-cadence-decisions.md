---
title: Verify which API code path actually runs before quoting per-call cost or making cadence decisions
source_mode: direct, kf-expert
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-30
tags: cost-discipline, api-wrappers, premise-verification, scheduling-decisions, methodologies
related_entries:
  - methodologies/2026-05-29_deterministic-first-debugging.md
  - methodologies/2026-05-27_read-ground-truth-not-surface-signals-universal-antipattern.md
  - strategy/2026-05-29_llm-wrapper-api-pricing-diy-floor-calibration.md
---

# Verify Which API Code Path Actually Runs Before Quoting Per-Call Cost

## Pattern

When making a scheduling, cadence, or budget decision that depends on per-call API cost, verify which code path is actually executed in the project — direct vendor API vs a third-party wrapper. Different paths against the same vendor can diverge in cost by 100× or more. Anchoring a decision on the cost of an unused code path is a high-impact premise error.

## Concrete Instance (2026-05-30)

In sem-tools, an ne1 decision about whether to schedule `sem run-daily` daily was initially made under the false premise that `KeywordIntel.refresh_metrics` would burn ~$15/day in Google Ads quota. The premise was anchored on an existing global CLAUDE.md note that DataForSEO's `/v3/keywords_data/google_ads/search_volume` wrapper charges $0.075/call.

In reality, the project uses Google Ads API directly (`sem/core/apis/google_ads.py`, `KeywordIntel._get_google_ads()` → `GoogleAdsClient`), which is free up to 15,000 ops/day. Current usage is "dozens/day" per the project's own quota-awareness commit message (35b7479). The $0.075/call number applies only to a different, currently-unused code path (DataForSEO's wrapper, used only for ZIP-resolution keyword volume that the direct API does not expose).

The decision (Option C' — decompose run-daily into per-phase cron with weekly KeywordIntel) was made under the wrong premise, then revised mid-stream to Option A (single daily cron) once the user surfaced the free-tier reality. The follow-up implementation bead (ck6) was rewritten to reflect the corrected scope.

**Cadence impact:** A single false cost assumption almost caused unnecessary architectural fragmentation.
**Budget impact:** A claim of ~$15/day recurring cost was actually $0/day.

## Verification Steps

1. **Locate the actual call site** in the project (grep for the client class or HTTP path).
2. **Confirm which client/wrapper it imports** — does it import a third-party SDK, or does it construct requests directly?
3. **For that specific code path**, check the vendor's current docs for per-call cost AND any free-tier quota.
4. **Cross-check the project's own commit messages and comments** for usage-volume estimates and quota notes.
5. **Only then quote the cost** in a scheduling or budget decision.

Do not stop at step 2. The code path might import a wrapper **and** use it in only one scenario while using direct API calls elsewhere.

## When This Applies

- Anytime a cost or quota claim drives a cadence, decomposition, or budget decision.
- Anytime a project has BOTH a direct API client AND a wrapper around the same vendor (common when migrating between vendors or supporting multiple data sources).
- Anytime the user has scripts older than ~12 months that reflect outdated cost or capability assumptions (vendor pricing models drift — Yelp Fusion moved from free-with-rate-limits to $229+/mo flat between 2024 and 2026; Google Ads API added a free tier in 2023; DataForSEO has raised prices multiple times).
- Anytime a CLAUDE.md note, wiki entry, or project README quotes a memorable per-call price and a decision needs to anchor on it. The more memorable the price figure (and the more it would dominate a decision), the more important the verification.

## When This Does NOT Apply

- One-off scripts or experiments where the cost is being estimated rather than driving a decision.
- Vendor pricing that is uniformly documented and unchanged across the codebase (single code path, single cost).
- Decisions that have already factored in the cost uncertainty (e.g., "let's assume $0–20/day and decide based on that range").

## Anti-Pattern to Avoid

**Anchoring on a memorable cost figure from a CLAUDE.md note, wiki entry, or prior session without checking it applies to THIS code path.** The bigger the cost figure (and the more it would dominate a cadence or budget decision), the more important the verification. The false premise example above was amplified because:
- The cost figure ($15/day) felt large relative to daily operational costs
- It drove a architectural decision (decompose cron, add per-phase complexity)
- It was sourced from an authoritative location (global CLAUDE.md) that normally needs no verification
- The check (grep for the actual call) would have taken <2 minutes

## Companion Patterns

This complements several existing verification disciplines:

- **Deterministic-first debugging:** Same principle applied to code existence: verify by grep/git log before claiming absence
- **Read ground truth, not surface signals:** Don't infer outdated cost from a filename or a doc title; verify the current comparison axis
- **Verify the premise before filing a defensive bead:** Read the FULL code path before claiming a capability is missing — the guard might exist outside the obvious block boundary

This entry is narrower than those three: it focuses specifically on **API code paths and cost claims**, whereas the others apply to broader premise verification.

## Source Context

Discovered during 2026-05-30 sem-tools beads triage and ne1 decision revision. Initial ne1 decision to decompose `run-daily` into per-phase cron was made on the claim that `KeywordIntel.refresh_metrics` would consume ~$15/day quota. User surfaced the ground truth: Google Ads API is free up to 15K ops/day; sem-tools uses it directly (not DataForSEO); actual usage is dozens/day. The cost claim was anchored on a different code path (DataForSEO wrapper for ZIP-resolution, currently unused for quota-driven decisions). Decision was revised to Option A (single daily cron) mid-stream and implementation bead was rescoped. The false premise would have persisted without explicit code-path verification. Pattern codified to prevent similar cost-anchoring errors across projects with multi-vendor or direct-plus-wrapper code paths.
