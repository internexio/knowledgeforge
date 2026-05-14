---
title: Autouse fake-stages fixture for neutralizing subprocess-invoking pipeline tests
source_mode: builder
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.9
staleness_risk: stable
importance: 3
domain: patterns
topic: validation
tags: [quality-gate, adversarial, grounding]
related_entries: [patterns/2026-05-11_atomic-write-stubs-for-readwrite-pipelines.md, patterns/2026-05-12_pin-tests-declarative-policy-manifests.md]
created: 2026-05-14
pinned: false
---

# Autouse fake-stages fixture for neutralizing subprocess-invoking pipeline tests

When refactoring a multi-stage pipeline to replace mocks with real
subprocess calls (LLM API, external service, etc.), every existing test
that goes through the pipeline will silently start hitting the real
backend — slow, flaky, expensive, and sometimes networked. The naive
fix is to monkeypatch the subprocess hook in every test that exercises
the pipeline. This scales poorly: N tests × M stages = N×M monkeypatches.

The pattern: write ONE autouse fixture at the test-module level that
stubs every stage hook with a canned passthrough output. Per-test
overrides remain trivial — monkeypatch the same hook with a custom
return. Tests that don't care about the new subprocess just keep
working.

## When This Applies

- A pipeline (composer of multiple steps) is being refactored from
  in-process mocks to real subprocess / network calls.
- Existing tests exercise the pipeline end-to-end and care about
  routing/dispatch behavior, not the specific stage outputs.
- The stages are reachable via module-level functions (not deeply
  nested in closure-bound state).

## When This Does NOT Apply

- Tests legitimately need to exercise the real backend (integration
  tier — keep those separate, gated on a marker like `pytest -m live`).
- The pipeline doesn't expose stage hooks at module level (refactor
  first so hooks ARE module-level functions, THEN apply the fixture).
- Stage stubs would diverge too much across tests — at that point the
  per-test monkeypatch IS the right call.

## The Pattern

```python
@pytest.fixture(autouse=True)
def fake_stages(monkeypatch):
    """Replace real subprocess-invoking stages with canned outputs.

    Per-test overrides remain possible by re-monkeypatching the same
    hook (monkeypatch.setattr(mod, '_stage_N', custom_fn)).
    """
    def _stage_1_stub(input):
        return {"verdict": "clean", ...}  # canned passthrough
    def _stage_2_stub(input, s1):
        return {"action_tier": input["proposed_tier"], ...}
    def _stage_3_stub(input, s1, s2):
        return {"score": input["raw_grounding"] * 0.9, ...}
    monkeypatch.setattr(module, "_stage_1", _stage_1_stub)
    monkeypatch.setattr(module, "_stage_2", _stage_2_stub)
    monkeypatch.setattr(module, "_stage_3", _stage_3_stub)
```

The fixture runs before every test in the module. Tests that want
custom behavior for a single stage just re-monkeypatch that one stage;
the autouse stubs handle the rest.

## Trade-off

The risk: a future test inadvertently exercises the autouse stubs when
it meant to exercise real behavior, masking a regression. Mitigation:

1. Co-locate the autouse fixture with the tests it serves (NOT in
   conftest.py — keep its scope visible).
2. Document the per-test override pattern in the fixture docstring.
3. Add at least one test that asserts the real stage IS called (e.g.,
   verifying schema validation, prompt composition) — these tests do
   NOT use the autouse fixture or override it explicitly.

## Concrete Example from This Session

When `baking_pipeline.py` replaced `_stage_1_critic_mock` /
`_stage_2_strategist_mock` / `_stage_3_calibrator_mock` with real
`claude --print` subprocess wrappers (commits B + C), every existing
test using `bp.bake_and_route(...)` would have hit the live LLM API.

The `test_baking_pipeline.py::fake_stages` autouse fixture
(commit `6dba2f7`) replaces all three hooks at module scope with
canned passthrough outputs. 14 existing tests in that file kept
passing without per-test edits. Two adjacent files
(`test_tier3_demotion.py`, `test_wiki_linter.py`) each have one
end-to-end test that needs the same treatment — those got explicit
per-test monkeypatches because they're single-test files. The
autouse pattern paid for itself at 14 tests; below ~5 tests
per-test monkeypatch is fine.

Critic-specific behavior tests (verdict rejection paths, schema
violations, chain failures) live in `test_critic_adversarial.py`
where the kf_chain.invoke call is mocked at the source — these
tests verify the REAL Stage 1 wrapper logic against a stubbed
subprocess, which is the right boundary.

## Grounding from This Session

Pattern applied across `test_baking_pipeline.py`, `test_tier3_demotion.py`,
`test_wiki_linter.py`, and `scripts/iteration_loop_acceptance_audit.py`
(its `_isolated_dirs` context manager is the same pattern at a different
scope). 14 + 1 + 1 = 16 e2e tests kept passing through a pipeline
refactor that introduced live subprocess calls; the 12 Critic-specific
unit tests verify the real wrapper logic at the right boundary.
Total test count grew 273 → 305 with zero false-pass risk because the
fakes are explicit and per-stage.

## Source Context

Discovered during [project] iteration-loop v0 implementation (Stage 1/2/3 real KF chain integration, May 2026). The baking pipeline was refactored to invoke real Claude subprocess calls (`claude --print`) instead of in-process mock functions. This pattern enabled safe refactoring without manually updating dozens of existing end-to-end tests.
