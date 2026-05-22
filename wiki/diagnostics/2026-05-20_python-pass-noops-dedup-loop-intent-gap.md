---
title: 'if key in seen: pass` — Python no-op silently breaks dedup loops'
source_mode: critic
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-20
domain: code-quality
topic: intent-vs-execution
tags: python, anti-pattern, dedup, code-review, diagnostic
related_entries:
  - diagnostics/2026-05-15_check-exit-code-before-cli-output-parsing.md
---

# `if key in seen: pass` — Python no-op silently breaks dedup loops

## The bug

```python
seen: set[tuple[str, str]] = set()
groups: dict[tuple[str, str], list[CoverageResult]] = {}
for row in rows:
    key = (row["page_url"], row["head_query"])
    if key in seen:
        pass   # ← NO-OP. Does NOT continue/skip.
    groups.setdefault(key, []).append(...)
    seen.add(key)
```

The author intended: "when I've seen this key before, skip the rest of the loop body."

What Python actually does: `pass` is a literal no-op statement. The dedup check exists,
but nothing acts on it. The `setdefault().append()` runs on every iteration, accumulating
ALL rows into each group instead of just the first-seen.

## When it surfaces

Production-only. Unit tests typically seed one date / one run, so the dedup loop
is exercised with `seen` always empty. The bug only fires once the data grows
to have multiple rows-per-key (multiple audit dates, multiple runs, multiple
versions, etc.). For real-world example: two audit runs both contribute their full sub-query list
to an aggregator, breaking aggregate metrics and uncovered-item tracking.

The symptom manifests on **day 2 of a deployment** when the first data duplication occurs,
making it look like a regression in code deployed that day, not a bug in the dedup logic itself.

## Root cause analysis

`pass` is taught early as a placeholder for syntactically-required blocks. Many
developers reach for it reflexively when writing the SHAPE of an if/elif/else
or while-empty-body, intending to come back and fill it in. When the surrounding
loop body is dense, the empty `pass` blends in visually — the eye reads the
intent (`if seen: skip`) and the brain auto-completes the `continue`.

The bug is invisible to pylint/flake8/ruff default rule sets — `pass` is
syntactically valid, semantically valid, and statistically a normal token.
Mypy doesn't catch it either; types check out.

## Detection

Three reliable approaches:

### 1. Critic / code-review gate (Most reliable)

A human or LLM critic reading the loop FOR INTENT (not for syntax) catches it within seconds.
This is why a critic-as-reading-for-intent gate is essential in any review pipeline — automated
checks let this through; the critic-as-reader gate catches it immediately.

### 2. Regression test with multi-row data

Explicitly seed the test data with 2+ rows per key and assert the loop output groups by key
correctly. The original test suite did NOT have this case — adding it would have failed
the build immediately. This is the "production-confidence" test that would have prevented
the bug.

### 3. Manual `ast.walk` lint rule

Look for `If(...).body == [Pass()]` inside `For` loops. False-positive-prone (some loops
legitimately need a documented skip-no-action branch), so suppress with `# noqa: pass-no-op`
where intentional. This rule is not in any standard linter as of 2026-05.

## When This Applies

- Code reviews of deduplication or state-tracking loops
- Debugging data aggregation pipelines that show unexpectedly high cardinality or duplication counts
- Onboarding new Python developers who may not yet distinguish `pass` (no-op) from `continue`/`break` (control flow)
- Regression testing on data pipelines — always include a multi-occurrence test case

## When This Does NOT Apply

- `try/except: ... else: pass` — intentional no-action branch on success (valid idiom).
- `if condition: pass  # TODO: implement fallback` — fine IF the comment is present and the work is tracked in a bead.
- Test stubs with `pass` as the body of a test function not yet written — expected and unproblematic.
- Legitimate skip-with-explicit-intent: `if should_skip: pass  # intentional no-op per design` — document with comment.

## Fix patterns

Two correct intents commonly conflated with this bug:

### Skip the rest of this iteration (most common)

```python
if key in seen:
    continue  # ← Move to next loop iteration
groups.setdefault(key, []).append(...)
seen.add(key)
```

### Process only the first occurrence (idempotent append)

```python
if key not in seen:
    groups[key] = []
    seen.add(key)
groups[key].append(...)  # Safe on every iteration
```

Both are correct — it depends on the domain semantics of "what does seen before mean?"

## Cross-reference

Related family: **Intent expressed but not executed** — see also:
- `wiki/diagnostics/2026-05-15_check-exit-code-before-cli-output-parsing.md` — same family (shell regex extraction gains false match on help text when exit code check is missing)

## Source Context

Caught during F8 fan-out coverage-aggregator code review (sem-tools `geo/recommender.py`, lines 70-84).
Critic gate surfaced it during multi-agent F8 build (session `sem-tools-f8-fanout-build-2026-05-20`).
The bug would have fired on production day-2 when multiple audit runs accumulated, breaking coverage rollup.
