---
title: Post-flip structural verification — distinguish routing success from downstream success in config-pointer migrations
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
domain: debugging
topic: root-cause-analysis
grounding_score: 0.75
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-23
tags: grounding, routing, quality-gate, deployment, empirical
related_entries:
  - wiki/methodologies/2026-05-21_saas-migration-pre-cancel-checklist-silent-failure-config-pointer-risk.md
---

# Post-Flip Structural Verification

When migrating a routing configuration that selects between two providers (vendor_a → vendor_b, db_a → db_b, source_a → source_b), the smoke test that verifies the migration MUST distinguish two failure modes:

1. **Structural failure** — the code path still routes to the old provider (the flip didn't take effect)
2. **Downstream failure** — the new provider is being called, but produces no usable output for reasons unrelated to the flip (auth, quota, config mismatch, downstream service issues)

These are different bugs with different fixes. Conflating them leads to false rollback of a successful flip.

## Verification protocol

After executing a config flip:

1. **Confirm the DB/config state changed** (the cheap check). UPDATE returned N rows, SELECT confirms new values.
2. **Trigger the code path** that reads the config (e.g. re-run the affected command).
3. **Verify in logs that the NEW provider's code branch was exercised.** Look for vendor-specific log lines (`logger.info("DataForSEO: checking N keywords")` rather than `logger.info("SEMrush: checking N keywords")`), HTTP requests to the new vendor's domain, or method names that only exist on the new code path.
4. **Separately assess downstream output.** If 0 results landed, ask: was that because the new provider was never called (structural failure → flip didn't work), or because it was called and returned 0 / errored (downstream failure → flip worked, separate issue)?

## When to use

- Vendor API migrations where one provider is being canceled / deprecated
- Database connection-string flips during cutover
- Feature-flag flips that route between two implementations
- Search/RAG source swaps (e.g. vector store A → B)

## When NOT to use

- Schema migrations (the verification target is row counts / column values, not code paths)
- Pure data backfills (no routing decision involved)
- Stateless transformations where there is no "old" path to disambiguate from

## Anti-pattern this prevents

> "We flipped the config and re-ran the command. It returned 0 results. The flip must have failed. Rolling back."

In a recent session this exact reading was the initial hypothesis after flipping `sem_domains.rank_source` from `semrush` to `dataforseo` for 4 domains. The smoke test showed `lacabar.com: checked 0/95 keywords`. Grepping the log revealed `INFO: sem.seo.rank_tracker - DataForSEO: checking 95 keywords for lacabar.com` — proof the new code path was exercised. The 0-match result traced to a DataForSEO IP whitelist and a location-targeting config issue, neither of which the flip caused. Rolling back the flip would have re-introduced the silent-failure 403 path it was designed to close.

## Concrete grounding (the diagnostic moves)

```bash
# Step 1: confirm config change
sqlite3 data/sem.db "SELECT domain, rank_source FROM sem_domains;"

# Step 2: trigger the code path
sem seo rank-check 2>&1 > /tmp/postflip.log
# NOTE redirect order: > file 2>&1 (NOT 2>&1 > file — the latter only captures stdout)

# Step 3: grep for new-provider-specific log lines
grep "DataForSEO: checking" /tmp/postflip.log
# If present: structural success. If absent: structural failure — flip didn't route.

# Step 4: separately assess downstream
grep "Access denied\|whitelist\|403\|401\|quota" /tmp/postflip.log
# These point at downstream issues unrelated to the flip itself.
```

## Related

- `2026-05-21_saas-migration-pre-cancel-checklist-silent-failure-config-pointer-risk.md` — the entry that defines why the config-pointer flip is load-bearing in vendor migrations; this entry covers how to verify the flip after executing it.

## When this applies

- Any vendor migration where a config field (boolean, foreign key, enum value) switches code paths between old and new implementations
- Particularly critical when the old vendor is being canceled and silent failures (zero results, no error) are the risk
- The flip is structural (binary: old path or new path), not gradual (canary rollout)

## When this does NOT apply

- Gradual feature-flag rollouts where both code paths run in shadow
- Migrations where both vendors run for validation before old cancellation
- Scenarios where the output format is identical — you can't distinguish "old API called" from "new API called" via log inspection

## Source context

Pattern derived from semrush → DataForSEO rank-source migration (2026-05-23). When domain records carried `rank_source='semrush'`, a database flip to `'dataforseo'` should have triggered the new data-pull code path. The initial observation was zero results, which raised the hypothesis that the flip failed. The diagnostic moves — confirm DB state, trigger code path, grep for new-vendor logs, separately assess downstream errors — surfaced that the flip succeeded structurally but the new provider was returning zero results due to IP whitelist and location targeting config. This diagnostic pattern generalizes to any routing-based provider migration.
