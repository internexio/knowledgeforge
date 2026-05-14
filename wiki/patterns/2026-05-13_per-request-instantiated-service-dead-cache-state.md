---
title: Per-request-instantiated service with instance-attribute caches is dead state
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-13
domain: patterns
topic: validation
tags: quality-gate, grounding, adversarial
related_entries: []
---

# Per-Request-Instantiated Service with Instance-Attribute Caches Is Dead State

## What

When a service class holds instance-attribute caches (e.g. `self._knowledge_cache: dict[str, str] = {}`) or session-tracking state (e.g. `self._session_diagnoses: dict[str, list[str]] = {}`) but is instantiated per request inside route handlers, the cache and the state are dead. Every request gets a fresh empty dict; nothing accumulates; no cache hit is possible.

Equally important: the "this state grows unbounded" comment or worry that often appears next to such fields is **fictional** under the per-request lifecycle, because the dict goes out of scope when the handler returns. The unbounded-growth concern only becomes real after you fix the dead-state bug by converting to a singleton — at which point you have to also add bounded-size and/or TTL eviction.

## When to Look for It

Three signals together:

1. A service class with internal `_cache` / `_session_*` / `_memo_*` instance attributes.
2. Production call sites that construct it directly inside a handler (`agent = MyService()` in `def handler(...): ...`).
3. No module-level singleton getter or DI binding for the class.

Grep heuristic: `grep -rn 'MyService()' app/` against the route layer. If you see direct constructions in handlers, the cache is dead.

## What to Do When You Find It

Two coupled fixes — do not ship one without the other:

### 1. Make It a Module-Level Singleton

Match the codebase's existing factory pattern (look for `def get_knowledge_base()` / `def get_database_service()` style; copy that). All production handlers go through the factory; tests can still instantiate directly to get fresh instances per test.

### 2. Bound the Previously-Dead State

Caches need eviction policy. Per-key TTL plus lazy eviction (run on every track/read; no background thread) plus a thread-safe `Lock` is the minimum, because the singleton lives across all worker requests including concurrent async ones.

**Do not skip step 2.** You will replace "cache never hits" with "cache grows forever, OOMs in week 2."

## Why This Happens

A reviewer writes the cache field expecting the service to be a singleton; another engineer later wires it into routes without checking the lifecycle. The cache field looks load-bearing in code review and in tests (tests instantiate it once and exercise the cache), so the defect doesn't show up. Production tells you nothing — `cache_hit_rate` is just always zero. Only profiling token costs or instrumenting `cache_creation_input_tokens` vs `cache_read_input_tokens` will surface it.

## Concrete Grounding (cos-week4-audit-2026-05-13)

`backend/app/services/cos_agent.py::COSAgent` had two such fields:

- `_knowledge_cache: dict[str, str]` — meant to avoid re-reading knowledge modules from disk
- `_session_diagnoses: dict[str, list[str]]` — meant to avoid Claude re-issuing the same diagnostic name within a session

`COSAgent()` was instantiated in two production sites:

- `app/services/chat_pipeline.py:315` — the main chat hot path
- `app/api/chat.py:1390` — the chat_unified analysis sub-service

The cache class attribute existed since the class was written. No production code had ever benefited from it. There was even a comment about `_session_diagnoses` "growing forever" which could not happen under the per-request lifecycle.

Fix shipped as commit `d1c8056`:

- Added `get_cos_agent()` factory mirroring `get_knowledge_base()`
- Extracted `_session_diagnoses` into a new `DiagnosisTracker` class with `MAX_DIAGNOSES_PER_SESSION = 20`, 24h TTL, lazy eviction, and a `threading.Lock` for concurrent async access
- Both production call sites switched to `get_cos_agent()`

After the fix, `_knowledge_cache` actually accumulates across requests, and the "session-diagnoses grow forever" worry that was fictional under per-request became real and was addressed by the new tracker class.

## When This Does NOT Apply

- **Stateless services** (e.g. simple validators with no instance state). Singleton vs per-request makes no behavioral difference; pick by test ergonomics.
- **Services that intentionally need per-request state** (e.g. a request context object). The "dead-state" framing only applies when the field is *intended* to persist across calls.
- **Dependency-injected scopes** where the framework manages lifecycle (FastAPI `Depends` with `Depends(get_service)` and the service is scoped at app level via `lru_cache` — already a singleton in disguise).

## Source Context

Discovered during COS backend code-review audit (2026-05-13). Grounding via commit `d1c8056` and instrumentation of `cache_creation_input_tokens` vs `cache_read_input_tokens` metrics in production.
