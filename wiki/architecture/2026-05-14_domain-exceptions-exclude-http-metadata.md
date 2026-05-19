---
title: Domain exceptions should not carry HTTP metadata
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.75
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-14
tags: architecture, layering, error-handling, separation-of-concerns, fastapi, audit-pushback
related_entries: []
---

# Domain Exceptions Should Not Carry HTTP Metadata

## The Recurring Audit Suggestion (and Why It's Wrong-Shape)

Audits and refactor guides frequently prescribe collapsing error-handling duplication by putting HTTP-status and user-message metadata directly on the exception class:

```python
class DomainError(Exception):
    code: str
    http_status: int = 500       # ← couples domain to HTTP
    user_message: str = "..."    # ← couples domain to a presentation surface
```

Then a single `@app.exception_handler(DomainError)` converts every raise into an HTTPException by reading `.http_status` and `.user_message` off the exception.

This *looks* DRY but it leaks HTTP-protocol concerns into the domain layer. The domain doesn't know it's serving an HTTP API — the same exception might also fire from a background worker, a CLI tool, a scheduled job, or an internal service-to-service call. In all those contexts `http_status` is noise; `user_message` is the wrong audience.

## The Cleaner Shape: Mapping Stays at the Boundary

Keep domain exceptions free of presentation/protocol metadata:

```python
# app/domain/foo.py — domain-pure
class FooError(Exception):
    def __init__(self, code: str, ...):
        self.code = code
        # NO http_status, NO user_message
```

At the API boundary, declare a small mapping per handler context:

```python
# app/api/foo.py
class _ErrCode(NamedTuple):
    status: int
    message: str  # user-facing copy

_FOO_ERRORS: dict[str, _ErrCode] = {
    "not_found":   _ErrCode(HTTP_404, "Not found or not yours."),
    "rate_limit":  _ErrCode(HTTP_429, "Slow down."),
    "provider":    _ErrCode(HTTP_502, "Upstream model is temporarily down."),
}

def _http_for_code(exc, mapping, *, default_status, default_message):
    err = mapping.get(getattr(exc, "code", ""), _ErrCode(default_status, default_message))
    return HTTPException(status_code=err.status, detail={"code": exc.code, "message": err.message})

# Handler block (was 11 lines, now 6):
except FooError as exc:
    raise _http_for_code(
        exc, _FOO_ERRORS,
        default_status=HTTP_500,
        default_message="Couldn't do the thing.",
    ) from exc
```

The duplication-collapse benefit is preserved (one entry per code, one helper) without coupling the domain layer to HTTP.

## When the Audit's Prescription IS Correct

There's a narrow case where exception-carries-HTTP-metadata is defensible: a backend whose *only* surface is HTTP, and whose domain layer is genuinely never reused outside that surface. A pure FastAPI microservice that does nothing but HTTP — no background tasks, no CLI, no service-to-service RPC — could legitimately collapse the layers since the abstraction has no future tenant.

In practice: rare. Most non-trivial backends grow background workers and admin scripts; the layering hedge is cheap insurance against the inevitable second consumer.

## When NOT to Apply This Principle (i.e., do collapse the layers)

- Quick prototype where domain/API distinction is theatrical.
- Single-file FastAPI demo (the exception class IS at the API boundary already).
- Library-internal exceptions that should never escape the package.

## Concrete Grounding

COS audit `CODE_REVIEW_2026-05-12.md` finding DUP-L2 flagged three pairs of error-code dicts in `app/api/expert_council.py` (separate status-map and message-map dicts per domain — composition / run-executor / blindspot) and prescribed: `typed DomainError(Exception) with .code / .http_status / .user_message; generic FastAPI exception handler`.

Declined the prescription. The three exception classes (`CompositionGenerationError`, `RunExecutorError`, `BlindspotError`) live in `app/expert_council/{cohort_generator,executor,blindspot}.py` — upstream of the API layer. Coupling them to HTTP would leak the protocol into the domain modules, which are also called from non-HTTP paths (BackgroundTasks executor, eventual CLI tools, etc.).

Instead, collapsed the three dict PAIRS (status + message) into three single `dict[str, _ErrCode]` mappings (where `_ErrCode = NamedTuple(status, message)`) plus one `_http_for_code()` helper at the API boundary. Domain layer untouched; duplication collapsed; mapping localized to the HTTP adapter. Commit `2383d56`.

The audit's underlying concern (paired dicts drift) was real and got fixed. The audit's prescription about *where* to put the metadata was where the pushback applied.

## The Transferable Principle

When an audit recommends "move this metadata onto the exception class," ask:

1. What other consumers of this exception exist or might exist?
2. Is the metadata HTTP-shaped, CLI-shaped, RPC-shaped, or domain-shaped?
3. Would a CLI / worker call site need this metadata or be confused by it?

If the metadata is protocol-specific and other consumers exist (or realistically will), keep the mapping at the adapter boundary. Solve the duplication concern with a small helper, not by leaking layers.

## When This Applies

- Any backend with domain exceptions that could be reused outside HTTP (background jobs, CLI, scheduled tasks, internal APIs)
- Any audit that prescribes moving HTTP metadata onto exception definitions
- Any refactor where paired dictionaries (status codes + messages) are causing drift
- FastAPI backends with separable domain and API layers

## When This Does NOT Apply

- Single-surface systems with no realistic multi-consumer future (quick prototypes, demos)
- Library-internal exceptions that never leave the package
- Systems where the domain/HTTP boundary is already collapsed by design and that's acceptable

## Source Context

COS Expert Council audit (2026-05-12) DUP-L2 finding. Audit prescribed collapsing error-handling duplication by moving HTTP metadata onto domain exceptions. The prescription was technically correct about the duplication problem, but the solution location was wrong-shaped. The principle generalizes: audit pushback on layering decisions belongs in wiki when it reflects a broader tension between DRY and separation of concerns.
