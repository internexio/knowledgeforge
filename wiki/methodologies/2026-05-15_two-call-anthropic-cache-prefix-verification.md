---
title: Two-call Anthropic cache prefix verification — synthetic probe before shipping cached prompts
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-15
tags: anthropic, prompt-caching, verification, staging-audit, contract-tests
related_entries:
  - methodologies/2026-05-13_verify-audit-claims-before-designing-fix.md
  - patterns/2026-05-13_content-addressed-cache-versioned-hash-prefix.md
---

# Two-call Anthropic Cache Prefix Verification

## The Diagnostic

`cache_control: ephemeral` on a system block is silent — there is no exception, log line, or build-time signal when caching does not actually fire. Three common failure modes are invisible until you measure raw API usage:

1. **Block under the model's minimum.** Sonnet 4.5 caches blocks >= 1024 tokens. A 300-token system prompt with `cache_control` set returns no error; it just never caches.
2. **Prefix drift across customers.** If any per-customer data (brand voice, persona, account name) ends up in the cached block, the prefix is no longer byte-identical across calls, and cross-customer cache hits silently disappear.
3. **Stale char-based token estimates.** A `len(text) // 4` estimate can underestimate by 5–10%. A 4096-char string that "should" be 1024 tokens may actually be 980 — silently no-ops.

Contract tests on prefix-byte-stability (e.g., "two calls with different brand_voice produce identical `system_blocks()` bytes") prove **necessary** conditions for caching but not **sufficient**. The block can be byte-identical and still no-op for reasons (1) and (3).

The only way to know caching works is to call the real Anthropic API and inspect `cache_creation_input_tokens` / `cache_read_input_tokens` on the `usage` field.

## The Two-Call Probe

Two calls is the minimum sufficient probe:

| Call | What it proves |
|------|---------------|
| **1** | `cache_creation_input_tokens > 0` → block is >= the model's cache minimum, `cache_control` is wired correctly, and the block is large enough to be worth caching |
| **2** | `cache_read_input_tokens > 0` → the second call's prefix matched call 1's — prefix is byte-stable across calls |

To prove the cross-customer claim simultaneously, vary the per-customer data between call 1 and call 2. If cache_read still fires with **different brand voice + different page**, you have proven:
- prefix is stable across customers (per-customer data is in the user message, not the cached block)
- cache hits actually fire (not just "could in theory")

Both claims in one probe.

## Concrete Grounding (COS cos-k50)

cos-k50 introduced a shared `SEO_PLAYBOOK` system block consumed by two SEO planner generators (`metadata_proposal`, `content_proposals`). AC #5 required "real audit showing `cost_attribution.tokens_in_cached > 0`".

Direct verification on staging (in-container Python script) called `AnthropicCachedProposalGenerator` twice with:
- Different page (page-a vs page-b)
- Different brand voice (warm/casual vs formal/technical)
- Same SEO_PLAYBOOK system block

Raw Anthropic usage:

```
Call 1: cache_creation_input_tokens = 1620, cache_read = 0       # cache miss, write
Call 2: cache_read_input_tokens     = 1620, cache_creation = 0   # cache hit, read
```

Three things confirmed in one ~30-second probe:
1. SEO_PLAYBOOK exceeds the 1024-token minimum (1620 actual tokens — chars/4 estimate of 1506 was conservative)
2. Prefix is byte-identical across calls (call 2's read count equals call 1's write count)
3. Cross-customer cache hits fire despite different brand voice (the load-bearing claim — per-customer data is in the user message, not the cached prefix)

Total wall-clock: ~30 seconds. No JWT, no audit orchestration, no staging project setup required.

## The Verification Recipe

```python
# In-container on staging — direct generator call, bypass orchestration.
from app.services.<your_module> import YourCachedGenerator

gen = YourCachedGenerator(api_key=os.environ["ANTHROPIC_API_KEY"])

# Call 1: customer A, payload A
r1 = await gen.generate(payload=payload_a, customer_data=customer_a)
assert r1.tokens_in_cache_write > 0, "block under minimum or cache_control not wired"

# Call 2: customer B, payload B (DIFFERENT from call 1 to prove cross-customer hit)
r2 = await gen.generate(payload=payload_b, customer_data=customer_b)
assert r2.tokens_in_cached > 0, "prefix drifted between calls — check what is in cached block"
assert r2.tokens_in_cached == r1.tokens_in_cache_write, "partial prefix match — cache fragmented"
```

The third assertion (`cached_read == cache_write`) is the strongest form: it proves the **entire** cached prefix matched, not just a subset.

## When This Applies

- Any new code adding `cache_control` to a prompt
- Any refactor that moves data between cached and uncached paths (especially: moving "shared" data to a playbook constant)
- Any change to the cached block's content (additions, deletions, reordering)
- After an SDK upgrade, model upgrade, or change to `cache_control` field handling
- Before closing a bead whose AC includes "shows cache hits"

## When This Does NOT Apply

- Single-consumer cached blocks where contract tests already pin both the block bytes and a token-count floor (the byte test + token test cover the same failure modes)
- Caching of message-level content (not system blocks) where the cache key includes message history — call 2 won't hit without preserving the message chain

## The Deeper Lesson

`cache_control` failure is silent. Contract tests can prove the necessary preconditions (block stability, byte-identity across customers) but not the sufficient one (the model actually returns cache hit telemetry). The only way to prove caching works is to ask the model.

Run the probe before declaring a cached-prompt feature done. Two API calls cost ~$0.001 and take 30 seconds. The alternative — discovering weeks later via cost dashboards that the cache hit rate is 0% — is much more expensive.

## Source Context

Discovered during COS cos-k50 closing verification (session: [project] 2026-05-15). The bead's AC #5 required "real audit shows `cost_attribution.tokens_in_cached > 0`". Rather than orchestrating a full audit through the API + JWT + project + crawled pages path, the direct two-call generator probe verified the underlying mechanism in ~30 seconds. The probe proved three things simultaneously (block exceeds cache minimum, prefix byte-stable across calls, prefix byte-stable across customers) where existing contract tests had only proven one (byte-stability across `system_blocks()` invocations). Pattern is reusable for any future cached-prompt rollout in COS or KF — block_assembler.py work, future stream_rewrite migration, post_suggestions inline-pad (cos-o3f).
