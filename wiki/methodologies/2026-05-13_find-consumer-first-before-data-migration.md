---
title: Find-consumer-first before designing data migrations
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.75
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-13
tags: methodologies, diagnostics, migrations, empirical, workflow
related_entries:
  - wiki/migrations/big-bang-rename-supabase-fastapi-react.md
  - wiki/methodologies/2026-05-13_verify-audit-claims-before-designing-fix.md
  - wiki/patterns/2026-05-11_atomic-write-stubs-for-readwrite-pipelines.md
domain: methodologies
topic: verification
---

# Find-consumer-first before designing data migrations

## The pattern

Before proposing a migration path for an existing data store (JSONL log, table, config file, or CSV), run a 5-minute probe to answer:

1. **Who writes to it today?** (grep for the path; check cron/launchd/systemd jobs; look for upstream sources)
2. **Who reads from it today?** (grep for the path; look for downstream consumers in the same repo and nearby repos)
3. **Are there sibling files?** (data files often come in pairs — input/output, pending/routed, queue/dead-letter — and the sibling tells you what the existing pipeline already does)

Skipping this probe means designing migrations against assumed-dead corpora that are actually live flows. The migration design will be wrong in shape — e.g., "wrap each existing entry in new envelope" implies a one-time bulk transform; reality may be a continuous flow that ALSO needs envelope wrapping, changing the entire migration strategy.

## Why this matters

Data files often look dormant from a single-file inspection (last write some time ago, large historical corpus, naming sounds archival). The reality is usually one of:

- **Active write + active read** — full pipeline still running. Migration must handle ongoing writes, not just history.
- **Active write + dead read** — accumulation file with no consumer. Migration can rename + start fresh.
- **Dead write + active read** — historical corpus being drained. Migration depends on read pattern.
- **Dead write + dead read** — true archive. Migration is unconstrained.

The first case is the trap. Each requires a different migration shape; mis-classifying the file class leads to operator surprise (cron job breaks; downstream tool throws on new schema).

## Concrete probe shell

```bash
# 1. Find writers
crontab -l 2>/dev/null | grep -i "$FILENAME"
ls ~/Library/LaunchAgents/ | grep -iE "$KEYWORD"  # macOS
grep -rE "$FILENAME" /etc/cron* 2>/dev/null  # linux

# 2. Find readers (in this codebase + nearby repos)
grep -rE "$FILENAME" ~/Scripts/ --include="*.py" --include="*.sh"

# 3. Find sibling files (data pipelines often come in pairs)
ls -la "$(dirname $FILEPATH)" | grep -E "$KEYWORD"

# 4. Verify freshness
ls -la "$FILEPATH" | head -1  # mtime
tail -1 "$FILEPATH"            # most recent entry timestamp
```

5 minutes, four commands (writers / readers / siblings / freshness), answers the writer/reader/sibling question. Skip at peril.

## When this applies

- Schema migration design (rewriting envelope shape)
- File-format migration (CSV → JSONL → SQL)
- Path migration (renaming, relocating)
- Tool migration (replacing a writer/reader script)
- Deduplication or consolidation of accumulators

## When this does NOT apply

- The file is brand new (created in this work-stream)
- The migration is purely additive (adding a column with default; no consumer impact)
- The file is in a sandbox/temp directory you control end-to-end
- The file is explicitly marked deprecated/archived in an upstream manifest

## Grounding

Discovered 2026-05-13 during iteration-loop v0 Phase 0 → Phase 3 prep:

### Initial framing (wrong)

`pending-suggestions.jsonl` (584 entries, last write 2026-05-13 06:01) was treated as a dead corpus. Three migration paths proposed: stub-map / new-kind-variant / archive-and-fresh. Strategist initially recommended a partition-by-`kind` approach. Path C (archive + rename) was rejected on grounds of "loses queryability of historical site-monitor heuristics."

### 5-minute probe revealed (right)

- **Writer:** `~/Scripts/tuan-dev/tuannw/scripts/site-monitor.sh` (cron `5 * * * *` — every hour)
- **Reader:** `~/Scripts/[project]/scripts/gastown-router.py` (writes routed entries to sibling `routed-suggestions.jsonl` with `"routed_via": "gastown"` annotation)
- **Sibling:** `routed-suggestions.jsonl` exists in same dir; appended to within the hour

### Implications that flipped the design

- gastown-router is OUT of v0 scope per README scope guardrails (explicit: "Fix the gastown-router unregistered-beads-issue-type bug | NOT a v0 task").
- Any migration that rewrites the on-disk shape of pending-suggestions.jsonl would break gastown-router's reads.
- Therefore: migration must be a READ-TIME interpretation in the new consumer (v0 surface router treats kind-less entries as `legacy_suggestion` in memory), NOT a write-time file rewrite. Existing entries stay flat on disk; gastown-router unaffected.

If the probe had been skipped, the chosen migration would have either broken gastown-router (file-rewrite approach) or required out-of-scope modifications to gastown-router (writer migration). The probe avoided this entirely.

### Cost-benefit

- **Cost of probe:** ~5 minutes (4 commands + read of one script)
- **Cost of skipping probe:** estimated +1 day to revert the broken migration + write the read-time interpretation + apologize to whoever's site-monitor depended on routed-suggestions.jsonl

## Related

- **[[critic-triage-routing-strategist-vs-defer-doc]]** — the routing pattern that ensures probes like this surface BEFORE design lands
- **[[verify-audit-claims-before-designing-fix]]** — same class of pre-design due-diligence; different artifact (audit doc vs. runtime data)
- The legacy-suggestion `kind` variant in the iteration-loop v0.3 architecture (the spec-amendment shape that resulted)

## Source Context

Discovered during iteration-loop v0 Phase 1 specification and baking-pipeline implementation (2026-05-13). The candidate surface router faced a data migration decision: should pending-suggestions.jsonl be rewritten to add explicit `kind` field, or should the new router handle both old and new schemas at read-time? The writer/reader/sibling probe answered: there's an active cron writer, active downstream reader in gastown-router (out of v0 scope), and the sibling file shows a two-stage routing pipeline. This meant the migration had to be read-time, not write-time. The probe prevented a design that would have broken the gastown-router pipeline.
