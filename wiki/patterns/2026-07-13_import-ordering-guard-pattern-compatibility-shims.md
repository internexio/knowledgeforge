---
title: Import ordering guard pattern for compatibility shims
source_mode: builder
novelty_type: reusable_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-13
domain: patterns
topic: composition
tags: [python, compatibility, import-ordering, shim, defensive-programming]
related_entries: []
---

# Import ordering guard pattern for compatibility shims

## Problem

When a compatibility shim must run before a library is imported (e.g., to monkey-patch missing attributes that the library expects), the ordering constraint is typically enforced only by a code comment. Comments rot: a future editor can move the shim import below the library import without any runtime signal, silently breaking the compatibility guarantee.

## Pattern

Add a hard `ImportError` guard AFTER the shim import but BEFORE the library import. The guard inspects the state the shim should have established and raises immediately if it finds the state missing.

```python
# bridge.py — wraps uszipcode (legacy) with a sqlalchemy_mate 2.x shim

# The shim patches sqlalchemy_mate at import time; MUST come first.
from mypackage._compat import legacy_shim as _shim  # noqa: F401

# Ordering guard — catches mis-placed shim import inside this module.
# NOTE: does NOT protect against `import legacy_lib` in other modules
# before this bridge is loaded — that blows up at their import time.
import sqlalchemy_mate as _sqla_mate
if not hasattr(_sqla_mate, "ExtendedBase"):
    raise ImportError(
        "legacy_shim did not install ExtendedBase — "
        "the shim import is missing or was placed after the library import. "
        "All legacy_lib access must go through this bridge module."
    )
del _sqla_mate  # keep bridge namespace clean

# Now safe to import the legacy library.
from legacy_lib import PublicClass, PublicType

__all__ = ["PublicClass", "PublicType"]
```

## When This Applies

- A compatibility shim must monkey-patch a third-party package before it is imported
- The bridge module is the canonical import point (all other code imports from the bridge, never directly from the library)
- The shim is idempotent (checks `hasattr` before patching), so legitimate double-import is safe

## When This Does NOT Apply

- The guard catches mis-ordered imports **inside the bridge module** only. It does not catch: other modules importing the library directly before the bridge loads, or the shim running too late due to `sys.modules` caching
- If the library is already cached in `sys.modules` before the shim runs, the damage is already done — the guard will pass but the library is in a broken state. Mitigate with a module docstring warning: "Do NOT import `legacy_lib` directly — always use this bridge"
- Do not use `assert` instead of `if + raise ImportError` — `assert` is silently stripped by `python -O`

## Concrete Grounding

Implemented in `client-project` commit `12b7dbb` in `src/semalytics_ads/geo/uszipcode_bridge.py`. The shim patches `sqlalchemy_mate 2.x` to restore `ExtendedBase`, `EngineCreator`, and `types.CompressedJSONType` that `uszipcode 1.0.1` expects but that were removed from sqlalchemy_mate 2.x. The guard verifies `hasattr(sqlalchemy_mate, "ExtendedBase")` before `from uszipcode import SearchEngine, SimpleZipcode`. All 538 tests pass with the guard present; the guard fires only when the shim line is absent or mis-ordered.

## Related Patterns

- Bridge module pattern: wrap a problematic dependency behind a single import surface so callsites never see the library directly
- `del _temp_name` to clean bridge namespace after the guard check

## Source Context

Surfaced from client-project geo-refactor phase 4 (session sa-y9g) during uszipcode/sqlalchemy_mate compatibility shim implementation. The pattern emerged as the canonical solution for enforcing import-ordering constraints on monkey-patch shims at compile time rather than runtime-failure time.
