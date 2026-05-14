---
title: unittest.mock.patch targets shift when a module becomes a package
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-13
domain: diagnostics
topic: testing
tags: [python, unittest, mock, patch, refactoring, module-to-package, testing-gotcha]
related_entries: [patterns/2026-05-13_collapse-duplicate-fetchers-rich-canonical.md, patterns/2026-05-13_phased-god-module-split-facade-first.md]
---

# Gotcha: `unittest.mock.patch` targets shift when a module becomes a package

## The trap

Suppose you have:

```python
# foo.py
from app.core.deps import get_thing

def do_work():
    return get_thing()
```

Tests patch the import:

```python
with patch("foo.get_thing", return_value=mock):
    do_work()
```

This works because `patch("foo.get_thing", ...)` rebinds the *name*
`get_thing` inside module `foo` — and that's exactly the name `do_work`
resolves at call time.

Now refactor `foo.py` into a package:

```
foo/
  __init__.py    # from foo.fetcher import do_work
  fetcher.py     # from app.core.deps import get_thing; def do_work(): ...
```

The public-facing name `foo.do_work` still works — `__init__.py`
re-exports it. But `patch("foo.get_thing", ...)` is now a no-op (or
worse: patches a name that the actual call site doesn't see).

The reason: `do_work` lives in `foo.fetcher` now. Its `get_thing` lookup
resolves in `foo.fetcher`'s namespace, not `foo`'s. Whatever the test
patches in `foo` is never consulted.

## The fix

Repoint patches to the submodule that contains the call site:

```python
# BEFORE
with patch("foo.get_thing", return_value=mock):
    ...

# AFTER
with patch("foo.fetcher.get_thing", return_value=mock):
    ...
```

The test logic doesn't change — only the patch target string.

## How to detect this on refactor

When splitting a `module.py` into a `module/` package, search for every
`patch("module.<name>"` occurrence in the test suite:

```bash
rg 'patch\("module\.[a-z_]+"' tests/
```

For each match, decide where the name actually gets looked up after the
split, and repoint accordingly. If unsure: it's the submodule whose code
calls the name, not the package's `__init__.py`.

## Why `__init__.py` re-exports don't save you

Even if `foo/__init__.py` does `from .deps import get_thing` to make
`foo.get_thing` resolve as a name, `patch` rebinds at the namespace where
it was told to look. The CALL SITE in `foo.fetcher` looks up `get_thing`
in `foo.fetcher`'s module dict — which has its own `get_thing` binding
from its own `from app.core.deps import get_thing` import. That binding
is independent of `foo.get_thing`.

This is the classic "where to patch" rule from the unittest.mock docs
applied to package refactors: **patch where the name is looked up, not
where it's defined.**

## When this applies

- Refactoring a single-file module into a package structure
- Tests use `patch()` with the old module path
- The code being tested calls an imported name (not an attribute)
- The tests would not fail loudly — they would silently patch the wrong namespace

## When this does NOT apply

- Tests use `patch.object()` to patch attributes directly (e.g., `patch.object(obj, "method")`)
- Code uses fully-qualified names like `app.core.deps.get_thing()` (rare; not conventional in Python)
- The import is moved to `__init__.py` AND all tests are updated together in the same refactor

## Detection heuristic

After a module-to-package refactor, run your test suite:
- If tests pass but the underlying service returns production data (or connections fail unexpectedly), the patches likely aren't working.
- If tests fail loudly with mocked values not being used, patches are fine but logic may be broken.
- Silent patch failures are the worst — mock is being applied to a name the code never looks up.

## Concrete grounding

Discovered during the STR-M2 refactor in [project] (2026-05-13), splitting
`backend/app/services/project_context.py` (1140 LOC) into a package.
The existing test `test_project_context_breakdown.py` had 3 patches:

```python
patch("app.services.project_context.get_supabase_client", ...)
```

After the split, `get_supabase_client` is called from
`app.services.project_context.fetcher`. All three patches needed:

```python
patch("app.services.project_context.fetcher.get_supabase_client", ...)
```

A single replace-all on the test file fixed it. Without the fix the
tests would not have failed loudly — `patch` would have silently rebound
an unrelated name. They would have hit the real Supabase client and
either errored on missing connection or returned production data. This
kind of latent test-failure mode is why the gotcha matters.

Commit `f961fb2` on master. All 998 backend tests pass after the fix.
The patch-target shift was flagged during code review and surfaced as
a critical auditable pattern.

## Related patterns

See also:
- **Phased god-module split** — the refactoring strategy that triggers this issue
- **Collapse duplicate fetchers** — another pattern from the same STR-M2 refactor; it references this diagnostic as the sibling issue that arises during package conversion

## Source Context

Discovered during the COS STR-M2 refactor session (cos-str-m2-project-context-split), refactoring a 1140-line monolithic service into a package structure. The patch-target shift was caught during code review (CODE_REVIEW_2026-05-12) and validated as a high-importance diagnostic for any future module-to-package conversions. Grounding score reflects direct reproduction, fix, and test validation.
