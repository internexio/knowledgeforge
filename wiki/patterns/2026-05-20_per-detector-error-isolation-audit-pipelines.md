---
title: Per-detector error isolation in multi-detector audit pipelines
source_mode: direct
novelty_type: new_pattern
grounding_score: 0.7
staleness_risk: stable
importance: 3
created: 2026-05-20
domain: patterns
topic: validation
tags: validation, quality-gate, error-classification, grounding, empirical
related_entries:
  - patterns/2026-05-20_hybrid-llm-embedding-coverage-audit-pattern.md
---

# Per-detector error isolation in multi-detector audit pipelines

## The Problem

Audit pipelines often run multiple independent detectors against the same input — for example, a spam-risk audit might run a cloaking check (extra HTTP fetches), a bias-listicle check (DOM pattern match), and a templated-content check (cross-page signature analysis). When written naively, one failing detector aborts the entire audit pass for that input, even though the other detectors would have produced valid findings.

The cost: binary success/failure per URL, loss of partial signal, and audit coverage gaps when any single detector is flaky or unavailable.

## The Pattern

Wrap each detector in its own `try/except` inside the orchestrator. Collect findings into a list. Log individual failures at WARNING level. Return the partial result.

```python
def _run_spam_detectors(self, url, soup, domain) -> list[dict]:
    findings = []
    if domain:  # bias_listicle needs domain — skip when missing
        try:
            bl = check_bias_listicle(url, soup, domain)
            if bl is not None:
                findings.append(bl)
        except Exception as exc:
            logger.warning("bias_listicle failed for %s: %s", url, exc)
    try:
        cl = check_cloaking(url, self._http)
        if cl is not None:
            findings.append(cl)
    except Exception as exc:
        logger.warning("cloaking failed for %s: %s", url, exc)
    return findings
```

Three design properties matter:

### 1. Per-detector try/except scope

Each detector is its own scope. One detector's `RuntimeError` cannot mask another's valid finding. Verified by mocking one detector to raise and confirming the other still runs.

### 2. Skip-when-context-missing, not fail-when-context-missing

When a detector requires context the caller may not have (e.g., `bias_listicle` needs the owning `domain` to know which brand is "self-promoting"), gate it with an `if domain:` rather than raising on `domain=None`. A null context is a perfectly valid state — the audit just won't have that signal.

### 3. Detectors return `None` for "ran cleanly, no finding"; non-`None` for a finding

This lets the orchestrator distinguish "detector said no" from "detector errored" without exception machinery for the common case.

## When This Applies

- Any pipeline running N independent detectors, scorers, or probes against the same input.
- Detectors with heterogeneous failure modes (network, parse, computation).
- Use cases where partial signal is valuable — "we found 2 of 3 possible spam patterns" still helps the user make a decision.
- Audits where detector coverage gaps are less harmful than losing all detectors' output because one failed.

## When This Does NOT Apply

- Pipelines where detectors have order/data dependencies (`detector_b` reads `detector_a`'s output). Use orchestrated chaining with explicit failure semantics instead.
- Safety-critical pipelines where a missing signal must abort downstream action. There, fail-loud is correct.
- Detectors whose failures are highly correlated (a network outage breaks them all). Per-detector isolation buys nothing; better to detect the global condition once.
- Situations where partial output is worse than no output (e.g., fraud detection where a false negative costs more than missing detection entirely).

## Anti-Pattern: Single Outer Try/Except

Do not wrap the entire `_run_spam_detectors` in a single `try/except`. That collapses every detector's failure into one error, you lose the signal of which detector failed, and a flaky detector kills the working ones.

```python
# WRONG — collapses all detector failures into one exception
try:
    findings = [
        check_bias_listicle(...),
        check_cloaking(...),
        check_templated_content(...),
    ]
except Exception as exc:
    logger.error("audit failed: %s", exc)
    return []
```

This loses 66% of potential signal.

## Tradeoff: Silent Failure vs. Obvious Crash

The cost of per-detector isolation is that a silently failing detector becomes a silent gap in signal coverage rather than an obvious crash. Mitigate with:

- **WARNING-level logs naming the specific detector and URL** — enables detection via log aggregation.
- **Metrics on detector-error rate, alerting when one detector consistently fails** — signals a real bug (not transient noise) that requires investigation.
- **Structured error reporting:** include detector name, input URL, exception type, and timestamp for post-hoc analysis.

## Grounding

Verified by:

- A monkeypatched test where `check_bias_listicle` raises `RuntimeError` and `check_cloaking` still runs and returns `[]` cleanly.
- A second test where `domain=None` and `bias_listicle` is correctly skipped (not raised).
- The pattern composes with the broader audit pass: a failing detector in `_run_spam_detectors` does not corrupt the citability scorer or eligibility check that ran earlier in the same `_score_page` call.

Grounding score 0.7 reflects: pattern implemented and tested against known failure cases, but not yet evaluated at production scale with real error distributions or alerting effectiveness.

## Source Context

Extracted from sem-tools spam-risk audit builder session (2026-05-20, `sem-tools-f10.1-spam-detector-wiring`). Reference implementation: `sem-tools/sem/geo/content_optimizer.py:_run_spam_detectors` (commit 639a16b).

Pattern generalizes detector orchestration decisions made during audit-pipeline infrastructure design and tested in F10 spam detection framework build.
