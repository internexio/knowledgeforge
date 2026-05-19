---
title: Subprocess test isolation needs env-var overrides plus default-sandbox-all-paths
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-15
domain: diagnostics
topic: test-isolation
tags: [quality-gate, empirical, adversarial, stable, grounding]
related_entries:
  - diagnostics/2026-05-15_check-exit-code-before-cli-output-parsing.md
  - infrastructure/2026-05-15_silent-success-scripts-state-artifact-freshness.md
  - patterns/2026-05-14_autouse-fake-stages-fixture-subprocess-pipeline-tests.md
---

# Subprocess Test Isolation: Env Vars Plus Default-Sandbox-All-Paths

## Pattern

Two compounding failure modes when test fixtures sandbox shared filesystem state:

1. **Pytest `monkeypatch.setattr` does not reach subprocesses.** When a test calls `subprocess.run([sys.executable, "...script.py..."])`, the child process imports the target module fresh — module-level constants like `EXEC_LOG_DIR = Path.home() / ".[project]" / "exec-log"` are re-evaluated against the real `Path.home()`. The in-process monkeypatch is invisible to the child.

2. **"Sandbox only explicitly-requested paths" leaks any path the test author doesn't enumerate.** A context manager that takes a dict of `{const_name: tmp_override}` and only patches the listed entries will silently fail to sandbox any other write-site that a deeper code path happens to trigger. Discovered when `check_c4_tier1_skip_path_savings` routed a Tier-1 proposal whose `bake_and_route` → `exec_dispatch.dispatch_tier1_exec` wrote to the real `~/.[project]/exec-log/` because the check requested only `ORCHESTRA_QUEUE_PATH` in its monkeypatches dict.

## When This Applies

- Any production module whose state-write location is a module-level Path constant
- Any test suite where some tests exercise the full pipeline (multiple write sites) while others exercise only one stage
- Any test harness invoked both in-process and as a subprocess (acceptance harnesses, smoke scripts, CLI dispatch tests)

## When This Does NOT Apply

- Modules that read their target path from env vars at every call (`os.environ.get(...)` inside the function) — those already work cross-subprocess without per-call patching
- Test suites that never spawn subprocesses AND have a strict per-test path catalog reviewed at PR time
- Pure-logic modules with no filesystem writes

## Resolution (Both Halves)

**Half 1 — env-var override on the production constant:**
```python
EXEC_LOG_DIR = Path(os.environ.get("[project]_EXEC_LOG_DIR", str(Path.home() / ".[project]" / "exec-log")))
```
Then in the autouse fixture, `monkeypatch.setenv("[project]_EXEC_LOG_DIR", str(tmp_path / "exec-log"))` — child subprocesses inherit env vars and will read the sandboxed path.

**Half 2 — default-sandbox all known paths in the context manager:**
```python
targets = {
    "orchestra.ORCHESTRA_QUEUE_PATH": (orchestra, "ORCHESTRA_QUEUE_PATH", "pending-suggestions.jsonl"),
    "exec_dispatch.EXEC_LOG_DIR":     (exec_dispatch, "EXEC_LOG_DIR", "exec-log"),
    # ...all other known write sites
}
for key, (mod, attr, default_name) in targets.items():
    override = monkeypatches.get(key, tmp / default_name)  # default if not explicitly requested
    setattr(mod, attr, override)
```
Now the caller still gets to specify paths it wants to inspect (via `monkeypatches`), but every other known write site is sandboxed by default.

## Defensive Guard

Even with both halves in place, add a post-yield assertion that the production paths weren't mutated:
```python
@pytest.fixture(autouse=True)
def _isolate_state_paths(tmp_path, monkeypatch):
    # ... redirect all module attrs ...
    queue_mtime_before = _file_mtime(_PROD_QUEUE)
    tier3_before = _dir_snapshot(_PROD_TIER3)
    yield
    assert _file_mtime(_PROD_QUEUE) == queue_mtime_before
    assert _dir_snapshot(_PROD_TIER3) == tier3_before
```
This catches the case where a NEW test or NEW write site bypasses both the env var and the module-attr patch. Without this guard, the leak surfaces hours or days later as a phantom row in a downstream consumer (the 2026-05-15 [project] morning brief surfaced 4 leaked "Archive Q4.log" proposals over two days before discovery).

## Grounding

Direct empirical evidence from [project] session 2026-05-15:
- Phantom proposals with `worker_session_id = "a" * 32` (pytest fixture sentinel) appeared in `~/agent-workflow/pending-suggestions.jsonl`, `~/.[project]/exec-log/`, and `~/.[project]/tier3_timers/` — a fingerprint impossible without test-fixture leakage
- 41 sentinel rows accumulated across 2 days
- Cleanup verified: after applying both halves, full `pytest iteration_loop/tests/` (324 tests) produces zero sentinel rows in any production path
- Bead [project]-817i closed with the conftest + audit-script fix

## Source Context

[project] iteration-loop test-pollution investigation, 2026-05-15. Full subprocess integration tests exposed a dual-failure mode: `monkeypatch.setattr` doesn't propagate to child processes (fixed via env-var override + module-level `os.environ.get`), and selective-sandboxing context managers accidentally leak unspecified paths (fixed via default-sandbox-all-targets pattern). The pattern generalises to any test harness that mixes in-process and subprocess invocations with filesystem side effects.
