---
title: pytest factory fixture pattern for parameterized stubs
source_mode: builder
source_session: redacted
novelty_type: reusable_pattern
grounding_score: 0.75
staleness_risk: stable
importance: 2
domain: patterns
topic: validation
tags: [quality-gate, grounding, adversarial]
related_entries: []
created: 2026-07-13
pinned: false
---

# pytest Factory Fixture Pattern for Parameterized Stubs

## Problem

Test files need a reusable stub (e.g., a mock object with specific attributes set) that accepts parameters per test call. Standard pytest fixtures inject a fixed value — they cannot accept call-time arguments. Module-level helper functions work but scatter stub-construction logic across files.

## Pattern

Define a fixture that **returns a factory function** rather than a ready-made value. Tests receive the factory via injection and call it with their specific arguments. Shared across a test directory via `conftest.py`.

```python
# tests/detectors/conftest.py
from unittest.mock import MagicMock
import pytest

@pytest.fixture
def search_engine_factory():
    """Return a factory for building uszipcode SearchEngine stubs.

    Usage in tests:
        def test_something(search_engine_factory):
            se = search_engine_factory("TX", "Austin")
            ...
    """
    def _make(state: str = "WA", major_city: str = "Seattle") -> MagicMock:
        se = MagicMock()
        z = MagicMock()
        z.state = state
        z.major_city = major_city
        z.post_office_city = None
        se.by_zipcode.return_value = z
        return se
    return _make
```

Tests — including class-based tests — receive the fixture via standard injection:

```python
class TestBuildLocationPath:
    def test_full_path(self, search_engine_factory):
        se = search_engine_factory("WA", "Seattle")
        path = _build_location_path("98101", se)
        assert path == "United States - Washington - Seattle - 98101"

    def test_state_expanded(self, search_engine_factory):
        se = search_engine_factory("TX", "Austin")
        ...
```

pytest injects fixtures into class-based test methods (any `test_*` method in a class starting with `Test`) exactly as it does for standalone test functions.

## When This Applies

- A stub object needs different configuration per test call (different attributes, different return values)
- The stub is reused across multiple test files in a subdirectory — put it in that directory's `conftest.py`
- Tests are class-based (pytest still injects fixtures into class test methods)
- You want IDE discoverability and co-location of the stub definition with the tests that use it (vs. an import from a helper module)

## When This Does NOT Apply

- The stub is always identical across tests → use a plain fixture that returns the value directly (no factory wrapper needed)
- The stub is used across multiple test directories → put it in the root `tests/conftest.py` instead of a sub-conftest
- The factory needs pytest's own scope controls (session/module/function) → consider `pytest_lazyfixture` or parameterize instead
- Do NOT import directly from `conftest.py` (`from conftest import _make_...`) — pytest does not guarantee conftest is importable as a module. Use fixture injection exclusively.

## Contrast with Module-Level Helpers

Before: stub defined as a module-level private function (`_make_search_engine`) in each test file that needs it — no sharing, each redefinition is a divergence risk.

After: single `search_engine_factory` fixture in `conftest.py` — future test files in the same directory get it for free via injection.

## Concrete Grounding

Implemented in `client-project` commit `12b7dbb` in `tests/detectors/conftest.py`. Previously `_make_search_engine()` was defined inline in `tests/detectors/test_zip_targeting_gaps_export.py`. After consolidation, both `TestBuildLocationPath` and `TestZipTargetingGapsExtras` use `search_engine_factory` via injection. 14/14 detector tests pass; stub behavior is unchanged.

## When This Applies
[Specific conditions where this knowledge is useful]

## When This Does NOT Apply
[Explicit boundaries]

## Source Context

Extracted from client-project geo-refactor phase 4 (session client-project-sa-y9g-geo-refactor-phase4, 2026-07-13). The pattern consolidates parameterized mock-object creation across test subdirectories, replacing scattered `_make_*` helper functions with a reusable factory-fixture pattern. The pattern improves stub discoverability via IDE fixture resolution and avoids parameter-passing boilerplate in test method signatures.
