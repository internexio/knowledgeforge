---
title: HTTP adapter bugs hidden by broad try/except + continue — mandatory integration test for production adapter call paths
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-25
domain: diagnostics
topic: error-handling
tags: quality-gate, api, empirical, testing, integration-tests, error-handling, silent-failure
related_entries:
  - diagnostics/2026-05-23_live-smoke-as-verification-gate-mocks-pass-prod-breaks.md
  - diagnostics/2026-05-13_unittest-mock-patch-targets-shift-module-to-package.md
  - patterns/2026-05-14_autouse-fake-stages-fixture-subprocess-pipeline-tests.md
revises: null
superseded_by: null
---

# HTTP adapter bugs hidden by broad try/except + continue — mandatory integration test for production adapter call paths

## Pattern: The Silent-Failure Surface

An HTTP adapter that wraps a third-party API can carry **multiple protocol-mismatch bugs** that all silently pass through to "success" output when:

1. The adapter's call site uses broad `try/except Exception: continue` (defensive against rate limits, transient errors, network blips)
2. There are no integration tests on the adapter (or tests mock at the wrong layer — they mock the adapter itself rather than its HTTP client)
3. Downstream consumers tolerate empty results (e.g., a loop over `results` that does nothing when empty)

In this configuration, a completely broken adapter can run end-to-end for months — logging "Stored N records" with N=0 every time, or returning empty lists silently — and nobody notices until someone asks "why is this dataset empty?"

## Concrete Grounding — 2026-05-25 DataForSEO historical_serps adapter

The `get_historical_serps` method in `sem/core/apis/dataforseo.py:238-297` had **two independent protocol bugs** that had been there since the adapter was written:

### Bug 1: Wrong outgoing field names

- Sent: `date_from` / `date_to`
- API expects: `from_date` / `to_date`
- API response: status_code 40501 "Invalid Field: 'date_from'."
- But the adapter caught this as `if task_result["status_code"] != 20000: logger.warning(...); continue` and returned an empty list.

### Bug 2: Wrong incoming response key

- Adapter walked: `result["items"][i]["se_results"]`
- Actual shape: `result["items"][i]["items"]` (the inner `items[]` holds the ranked SERP entries; `se_results` doesn't exist as a key in the Labs historical_serps response shape)
- Even if Bug 1 hadn't existed, every snapshot would have parsed to an empty `organic_items` list

### How the bugs hid

- The CLI's backfill loop swallowed exceptions per-keyword: every kw would log "Historical task failed for 'kw'" at WARNING level and continue. With 95 keywords, the warning storm scrolled past and got filtered as transient noise.
- The CLI's success message format was `"Stored {total_stored} rank records"`. When `total_stored=0` every time, it printed "Stored 0 rank records" — looks like a legitimate "no data found" rather than a broken integration.
- There were ZERO tests on `get_historical_serps`. Test suite had 266 passing tests including the keyword_intel adapter integration via heavy mocking, but never exercised the historical_serps response-parsing code path.

### What surfaced it

A live probe (single keyword, single call, inspecting `response.json()` directly) for a different reason — wanted to estimate cost before running a batch backfill. The probe immediately revealed: (a) request returns 40501; (b) when run without date fields, response has `items[]` not `se_results[]`. Both fixes took ~10 lines.

## Mandatory test pattern (regression guard)

For any HTTP adapter method that's called from production code paths, write at minimum these tests using a mocked HTTP client (not a mocked adapter):

### 1. Outgoing-shape test

Capture the request body the adapter sends; assert the field names match what the API actually expects. This catches Bug 1 (caller naming mismatch with API).

### 2. Response-parse test

Feed a fixture matching the **REAL API response shape** (not what you think it should be — what it actually returns when you call it manually); assert the adapter extracts the expected fields. This catches Bug 2 (response walking the wrong keys).

### 3. End-to-end fixture test

Chain (1) and (2): given a real fixture in, expect a real domain-object out. This catches integrations where the shape mapping works but the semantic wiring is wrong (e.g., off-by-one in pagination, wrong sort order assumption).

### Sample test structure (Python/pytest, mocked `client._http`)

```python
def test_adapter_uses_correct_field_names():
    client = _client_with_mocked_http(canned_success_response)
    client.method_under_test(date_from="2022-01-01", date_to="2026-01-01")
    posted = client._http.post.call_args.kwargs["json"][0]
    assert posted["from_date"] == "2022-01-01"  # API's name
    assert "date_from" not in posted              # caller's name shouldn't leak

def test_adapter_parses_real_response_shape():
    real_fixture = load_fixture("dataforseo_historical_serps_success.json")
    client = _client_with_mocked_http(real_fixture)
    result = client.get_historical_serps(...)
    assert len(result.organic_items) > 0
    assert result.organic_items[0].url is not None
    assert "se_results" not in str(result)  # verify it didn't walk the wrong key
```

## When this pattern applies

- Any HTTP adapter that integrates a third-party API
- Any class that hides HTTP details behind a "client" interface
- Any adapter where the response shape isn't pinned by a schema (JSON Schema, OpenAPI, etc.) and verified at parse time
- **Especially** when the calling code uses `try/except Exception: continue` for resilience — the silent-fail surface is the whole integration
- Adapters that wrap vendor APIs with hand-written request/response mapping (no code-generated client from OpenAPI/gRPC)

## When this does NOT apply

- First-party APIs you own end-to-end where wire-shape drift is visible at the API definition layer
- Adapters validated at construction time by a typed contract (gRPC + protobuf, OpenAPI codegen) where wire-shape mismatch raises at deserialization
- Adapters that fail loudly (raise rather than continue) — the next-layer-up will surface the bug on first call
- Single-vendor adapters with live smoke tests that already exercise the request/response boundary (though the three test types above still prevent regressions)

## Related patterns (already in knowledge base)

This is the read-side analog of the `safe_emit` write-side pattern documented in CLAUDE.md 2026-05-25: "Integration tests for silent-fail sidecars are MANDATORY." The principle is the same — when a layer is *designed* to swallow failures (whether for resilience or for sidecar isolation), every consumer of that layer needs an integration test that monkeypatches the destination AND runs the real path to verify events / data actually reach the boundary.

The current entry extends that principle from emit-sidecars to HTTP-adapters: broad try/except swallowing adapter failures is the read-side equivalent of sidecars swallowing write failures.

The "live-smoke as the verification gate" pattern (2026-05-23) assumes adapters work and tests them live. This pattern is orthogonal: it diagnoses when the adapter itself is broken. The two patterns work together — mocks verify adapter shape contracts, smoke tests verify the live path works, and together they catch the failure modes neither alone can surface.

## Anti-patterns

- Writing only unit tests on the adapter itself without mocking the HTTP layer — mocks of mocks verify nothing about the real adapter contract
- Skipping response-shape tests because "we've validated the API's schema externally" — external schema docs drift from live responses; the fixture is the source of truth
- Assuming the calling code's live integration will catch adapter bugs immediately — if the caller logs "N=0 records" and continues, the bug can hide for months
- Treating adapter tests as "done" after one pass — every API vendor bump (they happen monthly) should re-verify the response shape against a live call

## Source Context

Discovered during sem-tools session 2026-05-25 (ueg historical SERP backfill). DataForSEO historical_serps adapter had two independent bugs (wrong request field names, wrong response key traversal) that had been latent since the adapter was written. Both shipped past a 266-test suite because: (a) no tests existed on the adapter at all, (b) the calling CLI swallowed failures with try/except Exception: continue, (c) downstream consumers (the rank-data loop) tolerated empty results silently. A single live probe surfaced both bugs in seconds. The pattern is reusable for any production HTTP adapter where the calling code assumes resilience via exception-swallowing rather than failing loudly. Grounding score 0.85 reflects direct observation of two independent bug classes in the same adapter within one session, plus the broad applicability of the test structure to any vendor-integration scenario.
