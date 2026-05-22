---
title: SaaS migration pre-cancel checklist — silent-failure config-pointer risk
source_mode: strategist
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-21
tags: empirical, quality-gate, deployment, grounding
related_entries:
  - wiki/methodologies/2026-05-13_find-consumer-first-before-data-migration.md
  - wiki/diagnostics/2026-05-21_server-side-state-outlives-client-fixes-saas-wrappers.md
  - wiki/methodologies/2026-05-18_read-spec-heuristic-taxonomy-gate-iteration.md
---

# SaaS migration pre-cancel checklist — silent-failure config-pointer risk

## Problem

When canceling a paid SaaS to replace it with self-hosted or free-tier APIs, the naive sequence (export data → cancel → migrate later) loses two classes of value silently:

1. **Stale config pointers.** Configuration entries somewhere in the codebase still reference the dying vendor. After cancel, those code paths return zero results with no error — just silent logs ("No configured API for X") that nobody notices until reports show flatlined data.

2. **Importer asymmetry.** Most "import" tools cover the most-common export format (e.g., one report type) and silently drop fields they can't map. You don't know what was lost until you try to query for it later.

## The required sequence

Order matters. Steps 1–2 must complete BEFORE the cancel; 3–6 can run after as long as exports are saved.

```
1. Final fresh capture from the dying vendor
   — Run whatever data-pull command uses the vendor as a source. ONE LAST TIME
     while it still works. Verify rows landed (SELECT MAX(checked_at) FROM ...).

2. Switch all stale config pointers to the replacement backend
   — Grep the codebase + database for the vendor name in config keys, table
     columns, env vars, cron scripts. Update each to the replacement.
   — Smoke test: run the data-pull command again, verify rows now show the new
     source. This is the moment to catch silent-failure risk.

3. Export everything from the vendor (manual or API)
   — Cover both supported-importer formats AND archival-only formats.
   — Note that "archival" data without an importer still has value — keep CSVs.

4. Import the supported formats
   — Use --dry-run first to verify destination tables populated as expected.
   — Audit field-level coverage: which fields parsed but never wrote? Many
     importers drop columns silently. Read the import code, not just the docs.

5. Replacement backfill for what the vendor used to provide
   — If the replacement has its own historical-data endpoint (e.g., DataForSEO
     historical SERPs at $0.0001/query), use it now while data is fresh.

6. Cancel.
```

## The silent-failure check

Before cancellation, run this query against your config:

```sql
SELECT key, value FROM <config_table> WHERE value LIKE '%<vendor>%';
-- or equivalently for env-style config:
grep -rln '<vendor>' .env config/ scripts/
```

Every match is a silent-failure surface. Fix each, then re-grep.

## Importer asymmetry — how to spot it

Read the importer's actual write path. Many parse a wide CSV but only INSERT into 2–3 tables. Fields parsed and displayed (e.g., via `--dry-run`) but never written are lost on cancel.

The grep pattern is: look for parsed variables that don't appear in any INSERT/UPDATE statement. Example from a real session:

```python
# parsed (line 242–251 of importer):
position, cpc, volume, kd, intents = parse_columns(row)

# written (line 384–388):
db.execute("INSERT INTO seo_keywords (...) VALUES (...)", [...])
# ^ volume, cpc, kd, position never appear here — they're dropped
```

If preserving those fields matters, write the importer extension BEFORE running the import on the final export.

## When this applies

- Any SaaS subscription cancellation where data continuity matters.
- Migration from one paid API to another (same risk class).
- Subscription downgrade to a tier that loses historical access.

## When this does NOT apply

- Pure data-only migrations where no operational code reads the vendor (e.g., one-time historical backfill into a warehouse you control).
- Vendors offering full data archival in their cancellation flow (rare; check).
- Migrations where the replacement is already running in shadow for a validation window — you've already de-risked the config-pointer issue.

## Concrete grounding

Surfaced during a SEMrush → sem-tools cutover. Repo audit revealed 4 of 5 tracked domains had `rank_source='semrush'` in `sem_domains`. Without the config-pointer flip step (step 2), `sem seo rank-check` would log "No configured API for X (rank_source=semrush)" and return zero rows on every run post-cancel. Detected via cross-project capability audit only — no monitoring alert would have caught it.

---

## Source context

Pattern derived from SEMrush cancellation planning (2026-05-21). When migrating from SEMrush historical data to DataForSEO, the risk of stale config pointers in downstream consumers (scripts, cron jobs, API routes) became apparent only during the pre-cancel capability audit. The sequence emerged as a framework to surface config dependencies BEFORE they become silent failures.
