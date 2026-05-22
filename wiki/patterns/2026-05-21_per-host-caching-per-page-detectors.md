---
title: Per-host caching for per-page detectors with per-host signal
source_mode: builder
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-21
domain: patterns
topic: orchestration
tags: patterns, caching, api-cost-control, detector-design, integration, performance
related_entries:
  - patterns/2026-05-20_per-detector-error-isolation-audit-pipelines.md
  - patterns/2026-05-13_content-addressed-cache-versioned-hash-prefix.md
  - patterns/2026-05-13_per-request-instantiated-service-dead-cache-state.md
---

# Per-Host Caching for Per-Page Detectors with Per-Host Signal

## Problem

A detector function has a per-page signature (`check_thing(url, soup)`) but the actual evidence it reads is host-scoped (e.g., Wayback Machine homepage history, WHOIS, domain reputation feed). If the audit pipeline calls the detector once per page, you'll hit the upstream API N times for one logical signal — wasting calls, money, and rate-limit budget.

## Why Not Just Change the Signature?

Two reasons to keep the per-page signature:

1. It's the unit the rest of the system speaks: findings are per-page, `affected_urls` is a list of URLs, downstream dedup runs on findings.
2. Direct callers (tests, ad-hoc scripts) want a function they can call against a single page.

## Pattern

Keep the detector's per-page signature. Add caching at the **wiring layer** (the orchestrator that loops over pages), not inside the detector itself. The wrapper:

```python
def _check_thing_cached(self, url: str, soup) -> Finding | None:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if host in self._cache:
        cached = self._cache[host]
        if cached is None:
            return None
        # Re-issue the finding anchored to THIS page's URL.
        return Finding(
            pattern=cached.pattern,
            severity=cached.severity,
            evidence=cached.evidence,
            remediation=cached.remediation,
            affected_urls=[url],
        )
    finding = check_thing(url, soup, self._http)
    self._cache[host] = finding
    return finding
```

Key moves:

- Cache stores the **finding** (or None for negative result), not raw signal bytes.
- On cache hit, **re-issue with the current URL** so each page reports against itself. Downstream dedup logic (e.g., "one rec per pattern per domain") still folds them.
- Cache lives on the orchestrator instance (per-run), not module-level, so a long-lived service doesn't grow an unbounded cache.

## Architectural Layers

The pattern cleanly separates concerns:

| Layer | Responsibility |
|-------|-----------------|
| **Detector** | `check_thing(url, soup, http_client)` — reads page HTML, calls host-scoped APIs when needed, returns finding anchored to the input URL |
| **Wiring/Orchestrator** | `_check_thing_cached` — loops over pages, caches results by host, re-anchors cached findings to each new URL before returning |
| **Downstream** | Dedup and reporting — receives per-page findings (some with identical patterns from the same host), folds them via domain+pattern+severity logic |

This layering preserves the detector's single-page contract while eliminating redundant API calls at the orchestration boundary.

## When to Apply

- Per-page detector + per-host (or per-anything-coarser-than-page) signal.
- Multi-page audits that loop the detector — typically domain-wide content audits.
- API-bound signals (cost or rate-limit pressure).
- When downstream dedup logic is already prepared to handle multiple findings with the same pattern/host/severity.

## When NOT to Apply

- Signal is genuinely per-page (cloaking, bias-listicle, page-load performance) — no upside, just complexity.
- Cache miss cost is negligible (free local heuristics) — premature optimisation.
- Cache hits would mask important variation (rare — usually the signal is identical per host).
- Downstream logic cannot tolerate duplicate findings from the same host — fix downstream dedup first.

## Anti-Patterns

### Caching Inside the Detector Function

```python
# WRONG
def check_thing(url, soup, http_client):
    host = urlparse(url).netloc
    if host in MODULE_CACHE:
        return MODULE_CACHE[host]
    result = expensive_api_call(host)
    MODULE_CACHE[host] = result  # Leaks state across audit runs
    return result
```

**Problem:** Leaks state across audit runs, makes tests harder (tests get cache artifacts from previous test runs), breaks single-page callers (they inherit stale cache from other runs).

### Caching Raw Signal, Re-Running Comparison Per Page

```python
# WRONG
def check_thing_cached(url, soup, http_client):
    host = urlparse(url).netloc
    if host not in self._cache:
        self._cache[host] = expensive_api_call(host)
    api_result = self._cache[host]
    # Re-run the comparison for this page — defeats the point
    return _compare_api_result_to_page(api_result, soup)
```

**Problem:** More complex than caching the finding directly; no real benefit if the comparison outcome doesn't meaningfully vary per page (which it usually doesn't for host-scoped signals).

### Returning the Cached Finding Verbatim (Same affected_urls Every Time)

```python
# WRONG
def _check_thing_cached(self, url: str, soup) -> Finding | None:
    host = urlparse(url).netloc.lower()
    if host in self._cache:
        return self._cache[host]  # Same affected_urls every time — breaks per-page accounting
    finding = check_thing(url, soup, self._http)
    self._cache[host] = finding
    return finding
```

**Problem:** Each page on the same host reports the same `affected_urls` (e.g., `[example.com/page-1]`), breaking per-page recommendation accounting and causing misleading dedup summaries downstream.

## Grounding

**Verified in sem-tools F10.2c spam-risk audit builder:**

- **Detector:** `check_expired_domain_rebuild(url, soup, http_client)` — looks read-page-shaped but issues two Wayback calls (CDX + archive content) per call.
- **Wiring:** `ContentOptimizer._check_expired_domain_cached` keys by host on `self._expired_domain_cache: dict[str, SpamRiskFinding | None]`.
- **Verification:** Test `test_run_spam_detectors_caches_expired_domain_per_host` runs two pages on the same host and asserts CDX + archive each fire exactly once across the pair, while both pages still receive their own `expired_domain_rebuild` finding anchored to their respective URLs.

## Trade-Offs

### Benefit: Reduced API Cost

If an audit loops 50 pages on a 10-host domain, per-host caching reduces API calls from 50 to 10 (1 per unique host). For Wayback Machine (CDX quota-gated), this is a 5x savings in quota spend.

### Cost: Cache Invalidation Complexity

A per-run cache (on the orchestrator instance) is simple: just a dict that gets garbage-collected. But if you want the cache to survive across multiple audit runs (e.g., a long-lived service re-auditing domains), you'll need:
- TTL eviction (old findings become invalid as content changes)
- Size bounds (prevent unbounded growth)
- Invalidation signals (explicit cache-bust on deployment or config changes)

**Mitigation:** Start with per-run caches (simplest). Graduate to process-level singleton caches only if you observe high cache-hit rates AND can justify the eviction logic.

## Source Context

Extracted from sem-tools F10.2c spam-risk batch audit session (`sem-tools-f10.2-spam-risk-batch`). The `ContentOptimizer` class demonstrates this pattern for multiple host-scoped detectors (expired domain rebuild, WHOIS age, Wayback presence). Pattern generalizes to any detector with per-page API surface but per-host signal reading.

Related entry: `patterns/2026-05-20_per-detector-error-isolation-audit-pipelines.md` — covers orchestration of multiple detectors with independent failure modes; this entry adds the caching dimension for cost-control.
