---
title: Domain cooldown vs network rate-limit — when to keep them separate
source_mode: direct investigation
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.80
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-26
tags: architecture, rate-limiting, idempotency, patterns, distinctions, backend-patterns
related_entries: []
---

# Domain Cooldown vs Network Rate-Limit — When to Keep Them Separate

## The Distinction

Not every function with "rate_limit" in its name is a network rate-limit. There are two architecturally distinct concepts that often get conflated, especially during "consolidate into a central service" refactors:

**Network rate-limit** — throttles request frequency at the network boundary. Keyed on client identity (user.id or IP). In-memory or Redis. Records every request. Designed to bound load and prevent abuse.

**Domain cooldown** — throttles how often a *domain operation* can run against a *domain object*. Keyed on the domain object's ID (project_id, account_id, document_id). Database-backed. Records only on success. Designed to prevent expensive operations from being re-triggered.

Both raise 429 on rejection. That surface similarity hides three structural differences that determine whether they can share infrastructure.

## The Three Collapse-Test Axes

When evaluating "can this rate-limiter collapse into the central service?", check three axes. If any axis differs, **keep them separate**.

| Axis | Network rate-limit | Domain cooldown |
|--|--|--|
| **Keying dimension** | `user.id` or IP — who is sending the request | `project_id` or similar — what domain object is being mutated |
| **Storage durability** | In-memory or Redis (acceptable to lose counters on restart — request-rate is naturally bursty) | Database (must survive container restart — a user shouldn't be able to bypass the cooldown by triggering a restart) |
| **Recording timing** | Record at request time (every attempt counts toward the budget) | Record only after success (a transient backend failure must not lock the user out of retrying) |

The recording-timing axis is the most load-bearing. A central limiter that records every request is **wrong** for domain cooldowns — a transient Anthropic/Stripe/external-service failure would leave the user staring at a "you've hit your hourly limit" error despite zero useful work being produced.

## When Migration Is Wrong

A domain cooldown that gets migrated to a central network rate-limiter loses, in order of damage:

1. **Per-domain-object semantic.** A user with 10 projects gets 1 cooldown for the whole user instead of 1 per project. The cooldown's whole point is "don't re-run this expensive operation against THIS object too often" — keying on user destroys that.
2. **Restart resilience.** Container restart wipes the counter. User triggers expensive operation, container restarts (deploy, OOM, scheduled), user triggers again 30 seconds later.
3. **Success-conditional recording.** Transient external-service failures lock the user out for an hour with nothing to show.

## When to Use a Central Service

The central rate-limit service is right when ALL three axes match: client-keyed, restart-volatile-OK, request-time recording. Most HTTP-rate-limit use cases fit this — contact form throttling, anonymous trial limits, generic per-IP DDoS-light protection, per-user analyze-endpoint quotas.

When in doubt, ask: "If I migrate this and a backend service hiccups for 5 seconds, will the user be locked out with nothing to retry against?" If yes, it's a domain cooldown.

## Vocabulary Recommendation

Name domain cooldowns with `cooldown` in the function/class name rather than `rate_limit`. Examples:

- `check_regenerate_cooldown(project_id)` — clear
- `check_regenerate_rate_limit(project_id)` — looks like it should collapse into the central service, but can't
- `RegenerateCooldownActive` exception — clear
- `RegenerateRateLimitedError` exception — same confusion

The naming distinction is cheap polish that prevents future readers (or future-self) from mis-grouping the concept and proposing the wrong refactor.

## When This Applies

- Evaluating a centralization refactor that proposes migrating domain-specific operation throttles into a unified rate-limit service
- Designing a new domain operation that needs to rate-limit itself (per-object operation frequency guard)
- Auditing an API surface for "are we confusing these two concepts?" during architecture reviews

## When This Does NOT Apply

- Stateless HTTP request throttling (blanket rate-limits on endpoint access)
- IP-based DDoS protection (inherently request-keyed)
- Per-user quota enforcement (if the quota is legitimately per-user, not per-domain-object)
- One-time operations that don't mutate a persistent domain object

## Concrete Grounding

[project] session 2026-05-26: During investigation of cos-0od (consolidate rate-limiting into central service), encountered `app.services.post_suggestions.check_regenerate_rate_limit(supabase, project_id)`. Initial grep flagged it as a possible missed migration to the central service.

Five-minute investigation showed all three axes diverged:

- **Keying:** `project_id` (domain object), not `user.id` or IP
- **Storage:** Postgres table `post_suggestion_regenerate_log` with `last_run_at` column, not in-memory or Redis ZSET
- **Recording:** explicit `check_*` (read-only check) + `record_regenerate_run` (write only after generation+persist succeeds, per cos-w2e.10 design)

The split between `check_regenerate_rate_limit` (read-only check) and `record_regenerate_run` (write-after-success) is impossible to express through the central limiter's `enforce_rate_limit(request, ...)` API. The central service has no equivalent of "check now, record later, conditional on downstream success."

Conclusion: NOT a missed migration. Intentionally separate. Migration would break domain semantics.

The function should arguably be renamed to `check_regenerate_cooldown` for vocabulary clarity, but the architecture is correct as-is.

## Source Context

Grounded in [project] week 2 stale-audit (2026-05-26). A deliberate code investigation during architecture review of rate-limiting consolidation patterns. This pattern emerged from questioning an initial "missed migration" assumption and verifying the actual structural differences.

## Cross-References

Pairs with rate-limiting architecture patterns generally (no dedicated entry yet). Success-conditional recording is an idempotency-adjacent technique (no dedicated idempotency-patterns entry yet). The diagnostic move ("verify before migrating") is also an instance of [[2026-05-26_deterministic-scan-before-claiming-refactor-audit-beads]].
