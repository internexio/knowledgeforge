---
title: Validator-after-ownership-gate pattern for shared CRUD scaffolds
source_mode: direct
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-13
tags: security, refactoring, defense-in-depth, fastapi, shared-scaffold, cross-tenant-isolation
related_entries: []
---

# Validator-After-Ownership-Gate Pattern for Shared CRUD Scaffolds

## What

When extracting a shared scaffold for multiple PATCH/DELETE endpoints that share the same fetch + ownership-check + write boilerplate, expose the domain-specific validation as a callback (closure or function) that runs **after** the ownership check, never before or during.

Signature shape:

```python
async def patch_resource_field(
    resource_id: str,
    *,
    user: User | None,
    session_id: str,
    db: Any,
    update_kwargs: dict,
    validator: Callable[[dict], Awaitable[None]] | None = None,
) -> dict:
    # 1. Parse ID → 400 on malformed
    # 2. Fetch resource → 404 on missing
    # 3. Ownership check → 403 on mismatch  ← MUST happen before validator
    # 4. Run validator (it sees the fetched row, can raise HTTPException)
    # 5. Apply update_kwargs → 500 on falsy result
    # 6. Return the updated row
```

Each endpoint defines its validator as a closure capturing its request body, then passes it to the scaffold.

## When to Apply

You have N endpoints (typically 3+) that all share this structure:

```
parse_id → fetch_owned → validate_domain_rules → write → return
```

…where only the `validate_domain_rules` step differs per endpoint. The audit pattern that drove this is N≥3 with ~70 LOC each, of which ~11 LOC are pure boilerplate.

## When NOT to Apply

- **N=2**: just deduplicate manually; the abstraction tax exceeds the savings.
- **Validators share state**: if validators need to coordinate (e.g., multi-stage validation pipelines), use a `ValidatorChain` class instead.
- **Different fetch shapes**: if some endpoints need richer joins than others, parameterize the fetch instead — don't make every endpoint pay for the heaviest read.

## Critical: Validator Runs AFTER Ownership

The ordering is **security-load-bearing**. If a validator runs before the ownership check, an unauthorized caller can probe the validator's behavior:

- 422 with specific detail → "this resource has property X" (info leak)
- 404 vs 422 distinguishes "exists but invalid for me" from "doesn't exist"
- Timing differences between validator code paths could reveal resource state

By running the validator only after the requester passes the ownership gate, all of those probes return 403 instead — revealing only "you don't own anything by this ID", which is the strict information minimum.

Pin this with a test:

```python
async def test_validator_not_reached_when_ownership_fails():
    called = False
    async def spy(_conv): nonlocal called; called = True
    with pytest.raises(HTTPException) as exc:
        await patch_conversation_field(
            ..., user=None, session_id="attacker", validator=spy
        )
    assert exc.value.status_code == 403
    assert called is False
```

## Why a Closure (Not a Protocol or Class)

For 3 call sites with body-shape-dependent validation, a closure is the right level of indirection. Each endpoint's validator captures its own Pydantic body model naturally:

```python
async def update_conversation_personas(
    body: ConversationPersonasUpdateRequest, ...
):
    async def validate(conversation: dict) -> None:
        if not conversation.get("project_id") and body.persona_ids:
            raise HTTPException(400, "...")
        # ... uses body.persona_ids in scope
    updated = await patch_conversation_field(..., validator=validate)
```

A Protocol or class hierarchy buys nothing here — there's no shared validator state, no inheritance tree, no second implementation, and the closure's variable capture is exactly what each endpoint needs.

## When This Applies

- FastAPI (or any REST framework) PATCH/DELETE endpoints with shared ownership logic
- Multi-tenant systems where ownership checks are uniform across endpoints
- When refactoring N≥3 endpoints to reduce boilerplate and improve consistency
- When you need to extract domain-specific validation without compromising security gates
- When validators need read access to the fetched resource (not just request body)

## When This Does NOT Apply

- Single-endpoint use case (N=1); no refactoring benefit
- Endpoints with completely different database access patterns
- Validators that must execute before ownership checks (rare; re-examine threat model)
- POST/creation endpoints (ownership doesn't apply until after creation)

## Grounding

Implemented in [project] as `backend/app/services/conversation_patcher.py::patch_conversation_field` (STR-M6 from CODE_REVIEW_2026-05-12), collapsing three near-identical `update_conversation_*` endpoints (personas / references / campaign). Net LOC change in `api/chat.py`: -87 / +51. Validator-after-ownership ordering is pinned by `test_validator_not_reached_when_ownership_fails` in `backend/app/tests/test_conversation_patcher.py`.

Commit: `a0180ec` on master.

## Source Context

Pattern extracted from conversation endpoint consolidation in COS backend refactoring (STR-M6). The security-critical ordering constraint emerged during code review when a draft implementation placed validation before the ownership gate, creating a timing-based information leak. Testing revealed the information leak and validated the fix.
