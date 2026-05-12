---
title: Pin-tests for declarative policy manifests — cheap regression guard against accidental entry deletion
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.80
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-12
domain: patterns
topic: testing
tags: quality-gate, validation, testing, manifests, regression
related_entries: []
---

# Pin-tests for declarative policy manifests

## The Problem

A "declarative policy manifest" is a configuration file (TOML / YAML / JSON) whose entries are *operationally significant policy* — each entry causes the system to do something at runtime: monitor a log, scan a directory, apply a fix, allow a connection, route a request.

Examples:
- `stale_log_subjects.toml` — each entry is a log that gets monitored for staleness
- `script_error_patterns.toml` — each entry is an error regex that gets watched for
- `scan_targets` / `SCAN_TARGETS` list literals in Python (the same idea but expressed in code)
- Allow-lists, deny-lists, route tables, watched-paths, watched-topics

These manifests grow over time as the system learns about new substrate. Entries that get deleted by mistake — refactor accidents, careless rebases, half-completed migrations — silently *reduce* coverage. Nothing crashes. The next cycle just doesn't monitor that log / pattern / target anymore. You discover the regression weeks later when something fails that should have been alerted on.

## The Pattern

Add a unit test whose only job is to assert specific entries remain present in the shipped manifest:

```python
def test_shipped_c_manifest_includes_round2_subjects():
    """Round 2 (2026-05-12) additions must remain in the shipped manifest."""
    subjects = c_stale_logs._load_subjects()
    names = {s["name"] for s in subjects}
    expected_round2 = {
        "kanban-sync",
        "outbox-drain",
        "dreaming-health",
        # ... etc
    }
    missing = expected_round2 - names
    assert not missing, (
        f"Round-2 C-manifest entries missing: {sorted(missing)}. "
        f"Either the manifest was edited or the rename was reverted."
    )
    # If a rename happened: assert the old name is GONE
    assert "reflect-legacy" not in names, (
        "reflect-legacy should have been renamed to dreaming-cycle in Round 2"
    )
```

The test reads the *real* manifest (not a synthetic test fixture) and pins a specific set of entries. If anyone deletes one of those entries — intentionally or by accident — the test fails loudly with a self-explaining message ("Round-2 C-manifest entries missing: [outbox-drain]. Either the manifest was edited or the rename was reverted.").

## Three Modes of Use

### 1. Round-anchored pins (most common)

After a batch of additions (a "Round"), pin them as a group. Useful when the additions represent a deliberate policy expansion that should not regress. Naming: `test_shipped_X_manifest_includes_round<N>_<topic>`.

### 2. Critical-entry pins (use sparingly)

Pin ONE entry whose absence would be especially harmful — e.g., the single error pattern that catches a class of failures you've fought hard to prevent. Naming: `test_shipped_X_manifest_must_include_<critical_entry>`.

### 3. Rename-aware pins

When renaming an entry, the pin should assert BOTH new presence AND old absence:

```python
assert "new-name" in names      # new entry present
assert "old-name" not in names  # rename, not duplicate
```

This catches the "I added the new entry but forgot to delete the old one" mistake, which produces silent double-monitoring.

## When This Applies

- Declarative policy manifests where entries are operationally significant (each entry → runtime behavior)
- Allow-lists, deny-lists, route tables, watched-resources lists, error-pattern catalogs, alert-routing rules, retention policies
- Cases where the absence of an entry is itself a problem (NOT just the presence of a wrong entry — a separate test problem)
- Systems where manifest edits are common and pull-request review isn't sufficient to catch silent entry deletions

## When This Does NOT Apply

- Manifests that are pure data with no policy implication (e.g., a list of country codes — deleting an entry doesn't change behavior, just data scope)
- Manifests with frequent legitimate churn (e.g., a list of short-lived feature flags) — every flag deletion would force a test edit, which is friction without value
- Manifests under version control with strong code-owners / CODEOWNERS enforcement and mandatory review — if a human always sees the deletion before merge, the test is redundant
- Manifests so large the pin-test becomes a maintenance burden (>100 entries; pick a critical-entries-only approach instead)

## Anti-Patterns

- **Pinning the entire manifest by line count or hash**: brittle. Any legitimate addition forces a churn-edit to the test. Use named entries instead.
- **Forgetting to update pins after legitimate deletions**: the pin becomes a roadblock. When you DO need to delete a pinned entry, the test failure is the prompt to delete the pin too — and document WHY in the commit message.
- **Pinning entries that change names frequently**: if the underlying policy is stable but the name churns, the pin test will be a perpetual chore. Refactor the underlying policy first.

## Cost vs Value

Cost: ~5 lines of test code per round of additions. Runs in <10ms. No external dependencies — just imports the production loader and walks the parsed manifest.

Value: catches the silent-deletion-via-refactor failure mode, which is hard to detect any other way (no error, no warning, just reduced coverage on the next cycle). Especially valuable when manifests are edited by humans across PRs over time, since reviewers may not notice an entry was removed in a diff that primarily adds entries.

## Source Context

Adopted during [project] Dreaming Tier 1 Round-2 expansion, 2026-05-12. The Round-2 batch added 7 new C-manifest subjects and renamed 1 existing entry (`reflect-legacy` → `dreaming-cycle`). Pin-tests were added in the same commit so a future refactor that "cleans up" the manifest can't silently revert the coverage. The tests caught zero bugs during commit (everything was correct on first write) — the value is purely defensive against future deletions. Implementation: ~12 lines total split across two test functions in `dream/tests/test_categories_cde.py` and `dream/tests/test_categories_ab.py`. PR #1 commit 52aa2a7 in internexio/[project].
