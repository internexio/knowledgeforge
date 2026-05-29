---
title: Test isolation for shared file state — autouse fixture + post-test mtime guard
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 4
domain: patterns
topic: validation
tags: [pytest, conftest, autouse-fixture, post-test-guard, test-isolation, module-constants, shared-state, defense-in-depth]
related_entries:
  - patterns/2026-05-14_autouse-fake-stages-fixture-subprocess-pipeline-tests.md
  - diagnostics/2026-05-15_subprocess-test-isolation-env-vars-sandbox-all-paths.md
created: 2026-05-29
pinned: false
---

# Test Isolation for Shared File State — Autouse Fixture + Post-Test mtime Guard

## The Pattern

When a production module exposes a path-typed module-level constant pointing at a real file or directory (`ORCHESTRA_QUEUE_PATH = Path.home() / "agent-workflow" / "pending-suggestions.jsonl"`, `LOG_DIR = Path.home() / ".[project]" / "exec-log"`, etc.) and tests need to exercise code that writes through that constant, **isolate the path AND guard the production target**.

Concretely, in `conftest.py` add an autouse fixture:

1. **Redirect** each production module-level path constant to a subdirectory under `tmp_path` via `monkeypatch.setattr(module, "ATTR", tmp_path / subdir)`. This is the **isolation half**.
2. **Snapshot** the *real* production path's mtime (and optionally a directory snapshot for dir-typed constants) before the test runs.
3. **Yield** to the test.
4. **Assert** the real production path's mtime / directory contents are unchanged after the test runs. This is the **guard half**.

```python
@pytest.fixture(autouse=True)
def _isolate_state_paths(tmp_path, monkeypatch):
    for module, attr, subdir in _STATE_PATHS:
        monkeypatch.setattr(module, attr, tmp_path / subdir)

    queue_mtime_before = _file_mtime(_PROD_QUEUE)
    tier3_before       = _dir_snapshot(_PROD_TIER3)

    yield

    assert _file_mtime(_PROD_QUEUE) == queue_mtime_before, \
        f"test mutated real {_PROD_QUEUE}"
    assert _dir_snapshot(_PROD_TIER3) == tier3_before, \
        f"test created files in real {_PROD_TIER3}"
```

## Why Isolation Alone Is Insufficient

The autouse monkeypatch is a *necessary* defense but not sufficient. Failure modes the post-test guard catches that isolation alone misses:

1. **New code adds a write path the fixture didn't anticipate.** A new feature introduces a second module-level path constant; tests for that feature pass under the new code but accidentally write to production because nobody updated `_STATE_PATHS` in conftest.

2. **A test imports the path constant by value before the fixture runs**, then writes via the imported local — bypassing the monkeypatched module attribute. `from module import PATH` followed by `PATH.write_text(...)` writes to the *original* path; `monkeypatch.setattr(module, "PATH", ...)` doesn't retroactively rebind already-imported locals.

3. **Subprocess tests** that spawn fresh Python processes (e.g., an audit harness, a CLI invocation under test) don't inherit the parent's monkeypatched module state. They read the original module-level constant and write to the production path. (Mitigation: also `monkeypatch.setenv([project]_X_DIR, str(fake_dir))` and have the module honor the env override; the post-test guard catches it if the env override is missing.)

4. **A library upgrade** changes a vendored module path that conftest doesn't know about. Production code now writes through the new module's constant; tests pass and pollute prod.

In all four cases, isolation looks healthy but the real path was mutated. The mtime guard fails the test with a clear message naming the exact path that was touched.

## What to Guard

Pick the highest-traffic production paths and guard those — not every isolated path. The asymmetry: isolation redirects *many* paths (full coverage of known writes); the guard watches the *few* paths whose pollution would be most damaging (queues that surface in the morning brief, exec logs that humans review, audit ledgers).

Use `_file_mtime(path)` for individual files (returns `0.0` if absent, treated as a snapshot) and `_dir_snapshot(path)` returning the set of immediate children for directories.

## When This Applies

- A production module exposes path-typed module-level constants that tests need to exercise.
- Tests write through those constants as a side effect of exercising business logic (not testing the path selection itself).
- The real production paths must remain untouched during test runs (no phantom rows in queues, no stale logs leaking into the audit trail).

## When This Does NOT Apply

- **Pure unit tests that touch no module-level path constants at all.** No isolation needed; no guard needed.
- **In-memory fixtures (e.g., SQLite `:memory:`).** No on-disk shared state.
- **Tests for the production path constants themselves** (rare). Those should test the path *value*, not write through it.
- **Explicit integration/acceptance tests** that intentionally exercise real production paths. Mark those with `@pytest.mark.live` and run them separately; the guard doesn't apply.

## Failure Mode It Prevents

The most painful version of this bug class: a **phantom-row incident**. A test runs a real production code path, writes an envelope with a test-sentinel `worker_session_id` (e.g., `"a" * 32`) to the production queue, and the next morning brief surfaces that sentinel row as a "phantom proposal" the human can't action — they investigate for hours, find no real source bead, file a bug, eventually trace it back to a test that ran without proper isolation.

Even worse: if the queue is deduplicated by content hash, the phantom row persists across test runs, accumulating garbage in production that only shows up when someone explicitly audits the queue.

## Concrete Grounding (the source session)

Discovered 2026-05-29 in [project] during the `[project]-w0hb` test build. While adding `iteration_loop/tests/test_orchestra.py` cases for fingerprint-dedup + reconcile-GC, the test author worried that scheduler integration tests using the live worker config (which lists `bd_id = "[project]-jgnz"`, a real worker bead) might cause `reconcile_proposals("[project]-jgnz", {})` to silently retire the real queued `rate-limiting-architectures` entry from `~/agent-workflow/pending-suggestions.jsonl`. The test suite was running passing tests *and* potentially mutating production state.

Investigation found `iteration_loop/tests/conftest.py` already implemented exactly this pattern (autouse `_isolate_state_paths` + `_PROD_QUEUE` mtime guard at lines 96–120). The docstring even cited the original phantom-proposal incident that motivated it (`[project]-817i`). The 56 tests passing **including the guard** proved deterministically that the real queue was untouched — not "we got lucky," but "the guard would have failed the test if we hadn't." This converted an in-the-moment anxiety into provable safety.

The pattern was already in this repo for queue/exec-log/tier3-timer paths and is being extracted here for reuse.

## Implementation Sketch

```python
# conftest.py
from pathlib import Path
import itertools.module as mod1
import itertools.module2 as mod2

_PROD_QUEUE = Path.home() / "agent-workflow" / "pending-suggestions.jsonl"
_PROD_TIER3 = Path.home() / ".[project]" / "tier3_timers"
_PROD_EXEC_LOG = Path.home() / ".[project]" / "exec-log"

_STATE_PATHS = [
    (mod1, "ORCHESTRA_QUEUE_PATH", "queue"),
    (mod1, "TIER3_TIMERS_DIR", "tier3"),
    (mod2, "EXEC_LOG_DIR", "exec-log"),
]

def _file_mtime(path: Path) -> float:
    """Return mtime of file, or 0.0 if absent."""
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return 0.0

def _dir_snapshot(path: Path) -> set:
    """Return set of immediate children in dir, or empty set if absent."""
    try:
        return set(p.name for p in path.iterdir())
    except FileNotFoundError:
        return set()

@pytest.fixture(autouse=True)
def _isolate_state_paths(tmp_path, monkeypatch):
    """Redirect production path constants to tmp_path, guard against leakage."""
    for module, attr, subdir in _STATE_PATHS:
        monkeypatch.setattr(module, attr, tmp_path / subdir)

    queue_mtime_before = _file_mtime(_PROD_QUEUE)
    tier3_before       = _dir_snapshot(_PROD_TIER3)
    exec_log_before    = _dir_snapshot(_PROD_EXEC_LOG)

    yield

    assert _file_mtime(_PROD_QUEUE) == queue_mtime_before, \
        f"test mutated real {_PROD_QUEUE}"
    assert _dir_snapshot(_PROD_TIER3) == tier3_before, \
        f"test created files in real {_PROD_TIER3}"
    assert _dir_snapshot(_PROD_EXEC_LOG) == exec_log_before, \
        f"test created files in real {_PROD_EXEC_LOG}"
```

## Cross-References

- [[deterministic-first-debugging]] — the post-test guard *is* a deterministic check: same input → same output, falsifying by design.
- [[subprocess-test-isolation-env-vars]] — complementary pattern for child processes; the guard catches env-override misses.
- [[autouse-fake-stages-fixture]] — autouse pattern for subprocess logic stubs; this pattern extends it to shared file state.
- The pattern composes with the schema-evolution "additive optional fields + tolerant reads" approach (when adding new path constants, both `_STATE_PATHS` and `_PROD_*` watchlists are additive — old tests stay valid).

## Source Context

Extracted from [project] `iteration_loop/tests/conftest.py` during the `[project]-w0hb` test build (2026-05-29). The pattern was already proven via 56 passing tests + the guard in production, and is documented here for reuse in other projects with similar module-constant path patterns.
