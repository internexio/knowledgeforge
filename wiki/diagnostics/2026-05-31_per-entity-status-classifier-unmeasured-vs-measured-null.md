---
title: Per-entity status classifiers must distinguish "unmeasured" from "measured-null"
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.80
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-31
domain: data-quality
topic: classification, reporting, measurement-logic
tags: patterns, diagnostics, data-quality, reporting, classification, three-valued-logic, measurement-validation
related_entries:
  - diagnostics/2026-05-28_removed-ads-retain-history-join-scope-mismatch-retrospective-analysis.md
  - diagnostics/2026-05-25_vendor-accepts-parameter-upstream-returns-zeros.md
  - diagnostics/2026-05-13_fabricated-default-fallback-at-call-site.md
  - methodologies/2026-05-27_read-ground-truth-not-surface-signals-universal-antipattern.md
---

# Per-Entity Status Classifiers Must Distinguish "Unmeasured" from "Measured-Null"

## Problem

A reporting pipeline classifies entities (accounts, hosts, tenants, runs, experiments) into status buckets — PASS / FAIL / WARN, healthy / degraded / critical, powered / underpowered, etc. The classifier is typically a ladder of conditions evaluated in order. When the underlying measurement has multiple possible "missing" causes, a naively-ordered ladder collapses them into one bucket and lies.

The specific bug shape: a "measurement passed AND empty result" branch fires for entities that were never measured at all. Empty result is overloaded — it means either:
- "we measured and got nothing significant" (genuine negative)
- "we never measured this entity" (N/A, not classifiable)

The classifier reports both as "negative result" and the report makes a confident claim about an entity it has zero data on.

## Symptom

**Before the fix:** A Phase 0b correlation report classified the AT&T Developer account as **"FAIL (within)"** in the per-account summary table. AT&T had n=313 analyzable ads (above the powered threshold n_for_02=194) and 0 FDR-significant correlations — the classifier saw "powered + 0 sig" and fired the FAIL branch. But AT&T had **ZERO cos_scores rows for ANY of its ads** (the scoring pass had been aborted mid-run when the legacy ETA copy-extraction bug surfaced). The right classification was "unscored — measurement never happened", not "we measured and found nothing".

**After the fix:** AT&T correctly classified as "unscored".

## Pattern: The Three-State Classifier

Express the classifier as an explicit ladder including a "scored" / "measured" predicate ABOVE the empty-result branch:

```python
status = (
    "PASS"          if (powered and n_sig > 0)
    else "FAIL"     if (powered and scored and n_sig == 0)
    else "underpowered" if scored
    else "unscored"
)
```

The literal change that fixed the bug was adding `and scored` to the FAIL branch. The principle generalizes: **every empty/null/zero result needs a "was this entity actually measured?" gate before it can be promoted to a negative finding**. If the gate fails, the right status is "N/A" or "unmeasured" — a non-claim — not a negative.

## Why This Fails Silently

This bug class is especially nasty because:

- **Reports look correct in cases where every entity HAS been measured.** The bug only surfaces when the entity set grows to include unmeasured cases — often LATER in a project's life, after a new entity is added or after a pipeline failure leaves rows blank.
- **The empty-result branch is usually written FIRST** (it's the common case). Adding the "measured" gate later requires re-reading the whole ladder; reviewers miss it unless they specifically look for it.
- **Downstream consumers cannot distinguish easily.** Humans reading the report, dashboards, and alert rules cannot distinguish "FAIL because we tried and found nothing" from "FAIL because we never tried" without going back to source data.

## When This Generalizes

- **Per-host monitoring:** "host has 0 healthy probes" — is the prober broken or is the host actually unhealthy?
- **Per-tenant feature usage:** "tenant has 0 events" — did they not use it or did the event collector fail for that tenant?
- **Per-run experiment results:** "run shows no effect" — was the treatment applied or did the manipulation check fail?
- **Per-customer churn analysis:** "customer shows no engagement signals" — are they disengaged or did the signal pipeline stop ingesting their data?

In each case, the cardinality of states is: **NOT_MEASURED → MEASURED_EMPTY → MEASURED_NONEMPTY**. The classifier must distinguish at least these three; a two-state classifier (PASS / FAIL) is wrong by construction whenever "measurement failure" is possible.

## Diagnostic Checklist: Audit Existing Classifiers

When reviewing a report-generation function, look for:

1. Any branch that reads a measurement value (count, sum, list length) **WITHOUT first checking whether the measurement was attempted**
2. Common patterns to search for:
   - `if n_sig == 0:` or `if len(results) == 0:` without a preceding measurement check
   - Missing predicates like `scored`, `instrumented`, `data_available`, `has_observations`, `n_attempts > 0`
3. For each offending branch, add the measurement gate **above** the empty-result check

Example audit pattern:

```python
# WRONG: missing measurement gate
status = "FAIL" if n_sig == 0 else "PASS"

# RIGHT: measurement gate first
status = "FAIL" if (measured and n_sig == 0) else "UNSCORED" if not measured else "PASS"
```

## When This Applies

- Any report or dashboard that classifies entities based on derived metrics (counts, statistical tests, aggregates)
- Pipelines where "measurement never happened" is a possible state (optional measurements, conditional scoring, pipeline failures, late-added entity types)
- Systems with multiple data-source variants where some entities may not flow through all sources

## When This Does NOT Apply

- Closed-world systems where every entity is guaranteed to be measured (rare; verify the guarantee)
- Two-state classifiers where "unmeasured" is truly impossible by design (e.g., mandatory system configurations)
- One-off analyses where the entity set is static and hand-verified to be complete

## Related Patterns

- **Three-valued logic in SQL:** TRUE / FALSE / NULL is the canonical formalism for this distinction. The classifier-ladder bug is essentially "treated NULL as FALSE in a Boolean context."
- **Distinguish 'absence of evidence' from 'evidence of absence'** — the philosophical version of the same point
- **Fabricated-default fallback at call site** (`diagnostics/2026-05-13...`) — similar anti-pattern where a missing measurement is masked by a synthetic default value
- **Vendor accepts parameter, upstream returns zeros** (`diagnostics/2026-05-25...`) — related: a measurement *attempt* silently returned empty rather than erroring

## Grounding

Verified 2026-05-31 in `~/Scripts/[project]/scripts/phase_0b_correlate.py`. The bug was the classifier line:

```python
status = (
    "PASS (within)" if (powered and n_sig > 0)
    else "FAIL (within)" if (powered and n_sig == 0)   # BUG: fires on unscored too
    else "underpowered" if scored
    else "unscored"
)
```

The fix added the `and scored` guard to the FAIL branch:

```python
else "FAIL (within)" if (powered and scored and n_sig == 0)
```

**Behavior delta verified on the same data:** AT&T (n=313, n_sig=0, scored=False) correctly reclassified from "FAIL (within)" → "unscored". The meta-verdict above (CONDITIONAL based on powered_signal_accounts membership) had ALREADY excluded AT&T via the `n_sig > 0` predicate — so the bug was confined to the per-account summary lines, but it produced a confident wrong label on a row the rest of the report was honest about.

## Source Context

Discovered 2026-05-31 during the Phase 0b verdict-template fix in [project]. The phase had completed a correlate-to-performance study; the per-account summary table classified accounts into PASS/FAIL/underpowered/unscored. AT&T Developer account appeared as FAIL despite having zero measured correlations (the scoring pipeline had errored), making "unscored" the only honest classification. The bug occurred because the FAIL branch checked for "powered and n_sig == 0" without first verifying that scoring had actually completed for that account. This is a reusable diagnostic pattern because the three-state classifier structure (NOT_MEASURED → MEASURED_EMPTY → MEASURED_NONEMPTY) appears across domain-specific reporting wherever measurements can fail or be omitted.
