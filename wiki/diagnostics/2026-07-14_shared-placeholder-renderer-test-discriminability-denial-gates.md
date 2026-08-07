---
title: Shared placeholder renderer across two denial gates silently breaks test discriminability
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.88
staleness_risk: stable
importance: 4
pinned: false
created: 2026-07-14
domain: diagnostics
topic: testing
tags: [testing, quality-gate, adversarial, grounding]
related_entries: []
---

# Shared Placeholder Renderer Across Two Denial Gates Silently Breaks Test Discriminability

## The Pattern

When two different "denial" paths in a function both call the **same placeholder renderer**, and that renderer outputs hardcoded text that ignores the denial-specific `reason` field, test assertions on denial-specific strings can **silently fail to discriminate** which gate fired.

The failure mode:
- **Negative assertion** (`"error text" not in md`) passes when the WRONG gate fires, because the generic renderer doesn't include the error text
- **Positive assertion** (`"error text" in md`) fails when it should pass, because the correct gate fires but the renderer still doesn't include the text

Both look like test failures but the actual bug is in the renderer design, not the test.

## Concrete Example (client-project, 2026-07-14)

`generate_weekly_digest` had two early-return denial paths:

1. **Beta gate**: `is_beta_enabled(account_id)` → calls `render_not_enabled_placeholder(gate, ...)`
2. **User auth gate**: `has_account_access(user_id, account_id, client)` → ALSO calls `render_not_enabled_placeholder(denied, ...)`

`render_not_enabled_placeholder` output was hardcoded:
```
# Digest generation paused — account not enabled for beta
...
This account isn't on the private-beta allowlist yet...
```

It never included `denied.reason`, which contained "User X does not have access to account Y."

Tests:
```python
# These PASSED even when beta gate fired (wrong gate):
assert "does not have access" not in md  # True — generic message never has this

# This FAILED even when user auth gate fired (correct gate):
assert "does not have access" in md  # False — generic message still never has this
```

The debugging session spent multiple rounds thinking `monkeypatch` wasn't working, when in fact BOTH gates were rendering identically and the test had no way to tell them apart.

## Fix

Give each denial path its own renderer, or parameterize the renderer to include `reason`:

```python
# User auth gate — render inline, distinct from beta-gate placeholder:
return (
    f"# Access denied — {ctx.name}\n\n"
    f"**Account:** {ctx.name} ({account_id})\n\n"
    f"User {user_id!r} does not have access to account {account_id}. "
    f"Access is managed via [project] — contact support to update your account list.\n"
)
```

## Diagnostic Signal

When debugging a test where "my patch isn't working":
1. Add a debug print INSIDE the production function to confirm which path is executing
2. If the path IS executing but the assertion still fails, the renderer is the problem — not the patch
3. Look for shared renderer functions that don't surface path-specific details

## When This Applies

- Any function with 2+ early-return denial paths that reuse a single renderer
- Tests that use string-matching assertions on denial-path output
- Particularly dangerous when one path's negative assertion can pass even when the wrong path fires (masks test coverage gaps)

## When It Does NOT Apply

- Renderers that include the full `reason` field from a result object
- Denial paths that use completely different response shapes (e.g., HTTP status codes, exceptions)

## Key Insight

This bug is not visible from tests alone — `test_user_without_access` passing and `test_user_with_access` passing gives false confidence, because both gates render identically. The coverage gap only shows up when a test adds a **positive assertion on denial-specific text**.

The pattern fails silently because:
1. The test passes (the assertion runs and either matches or doesn't)
2. No error message points to "you have two gates but one renderer"
3. Multiple rounds of debugging focus on the production code (monkeypatch, fixtures, mocking) when the actual problem is renderer design

## Source Context

Sourced from client-project session `client-project-sa-c57-test-fix-2026-07-14`. The `generate_weekly_digest` function had beta-enabled and user-auth gates; tests for user-auth failures were failing because the shared placeholder renderer suppressed the user-specific denial reason. Debugging required tracing through multiple rounds of monkeypatch verification before identifying the renderer as the root cause.
