---
title: pytest autouse + tmp_path_factory env-var setup is unreliable when test also uses tmp_path fixtures — patch the function directly
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.82
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-14
domain: debugging
topic: hypothesis-testing
tags: grounding, adversarial, quality-gate
related_entries: []
---

# pytest autouse + tmp_path_factory env-var setup is unreliable when test also uses tmp_path fixtures

## Problem

When a pytest `autouse` fixture uses `tmp_path_factory.mktemp(...)` to write a file and then calls `monkeypatch.setenv(KEY, path_to_file)` to point an env var at it, the env var may not be read correctly by production code during tests that ALSO use other fixtures that involve `tmp_path` (e.g., a `temp_harness_db` fixture that accepts `tmp_path`).

The symptom: the production function reads the real on-disk config file (the one the env var was supposed to override) instead of the test-authored file. All assertions immediately before the production call show the patch worked, but the production call behaves as if the env var was never set.

## Root Cause

Fixture setup ordering between `tmp_path_factory` (session-scoped) and `tmp_path` (function-scoped) combined with `monkeypatch.setenv` leads to non-deterministic behavior. The autouse fixture writes to a session-scoped temp dir; the test's `tmp_path`-dependent fixture may interfere with env state during its own setup phase. A second `monkeypatch.setenv` call in the test body appears to succeed but doesn't take effect at the production call site.

## Reliable Fix

**Do NOT rely on file-backed env var manipulation when testing functions that gate on a config file.** Instead, patch the function that reads the config directly:

```python
# BAD — unreliable when other tmp_path fixtures are in play:
monkeypatch.setenv("SEMADS_BETA_ALLOWLIST", str(tmp_path / "beta.toml"))

# GOOD — patches the reader function directly, works reliably:
monkeypatch.setattr(
    "semalytics_ads.auth.beta_allowlist.load_allowlist",
    lambda: ["acct"],
)
```

Patch `load_allowlist` in **its own module** (not in the importing module's namespace) so that all callers — including those that imported it at module load time — see the patched version.

## Additional Complication: Circular Imports Block Module-String setattr

When trying `monkeypatch.setattr("semalytics_ads.digest.weekly.is_beta_enabled", ...)`, pytest resolves the string by importing the module. If that module is involved in a circular import (`digest → api → dashboard → digest`), the setattr raises `ImportError` even though the module is already in `sys.modules`. **Always patch at the module that DEFINES the function, not at the module that imports it.**

## When This Applies

- Autouse fixtures that use `tmp_path_factory` + `monkeypatch.setenv`
- Tests that also depend on `tmp_path`-consuming fixtures (e.g., DB setup)
- Any config reader that falls back to an on-disk default when the env var is absent

## When It Does NOT Apply

- Tests that have no other `tmp_path` fixtures (autouse works reliably in isolation)
- Tests that specifically exercise the file-reading path end-to-end

## Debugging Method

When a monkeypatched env var appears to work in assertions but the production function ignores it:
1. Add an inline debug print INSIDE the production function to log what the reader returns at the actual call site
2. If test-body assertions and the inline print disagree → env var not in effect at call time → switch to function-level patching
3. If they agree but the result is still wrong → the patch works but you're asserting on the wrong thing (different root cause)

## Source Context

Observed directly in client-project session 2026-07-14 fixing `test_generate_weekly_digest_user_without_access_returns_placeholder`. The autouse `beta_allowlist_all` fixture set `SEMADS_BETA_ALLOWLIST` via `tmp_path_factory`. Multiple `monkeypatch.setenv` and `monkeypatch.setattr` attempts failed. Patching `semalytics_ads.auth.beta_allowlist.load_allowlist` directly resolved the issue immediately.
