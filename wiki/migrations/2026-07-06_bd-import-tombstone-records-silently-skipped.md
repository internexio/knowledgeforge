---
title: bd import from pre-dolt JSONL — tombstone records silently skipped (line count vs import count discrepancy)
source_mode: direct
novelty_type: new_pattern
grounding_score: 0.80
staleness_risk: stable
importance: 2
pinned: false
created: 2026-07-06
domain: migrations
topic: schema-evolution
tags: deployment, empirical, stable, filesystem
related_entries: []
---

# bd import from pre-dolt JSONL — Tombstone Records Silently Skipped

## Pattern

When running `bd import <file>.jsonl` to migrate a legacy pre-dolt beads store, the reported "Imported N issues" count will be LESS than the line count of the JSONL file. The gap is NOT a bug or data loss — it reflects tombstone records that `bd import` silently skips by design.

## Example

```
$ wc -l mcp_agent_mail/.beads/issues.jsonl
     168

$ bd import .beads/issues.jsonl
Imported 115 issues from .beads/issues.jsonl

$ python3 -c "
import json
total=0; statuses={}
with open('.beads/issues.jsonl') as f:
    for line in f:
        b=json.loads(line)
        total+=1
        s=b.get('status','?')
        statuses[s]=statuses.get(s,0)+1
print(statuses)
"
{'closed': 110, 'open': 5, 'tombstone': 53}
```

168 lines − 53 tombstones = 115 imported. Exactly matches.

## What Are Tombstones?

Tombstone records are deletion markers in the JSONL append-log format — entries with `"status": "tombstone"` that mark previously-deleted issues. They are part of the log's internal accounting (for MVCC/sync purposes) but do not represent live issues. `bd import` correctly omits them from the new dolt store.

## Verification Protocol for Migrations

Before filing a discrepancy as a bug, always decompose the JSONL by status:

```python
import json
with open('.beads/issues.jsonl') as f:
    statuses = {}
    for line in f:
        s = json.loads(line).get('status', '?')
        statuses[s] = statuses.get(s, 0) + 1
print(statuses)
# Expected shape: {'closed': N, 'open': M, 'tombstone': K}
# Import count = N + M (tombstones skipped)
```

Then verify: `bd list` across all statuses to confirm (closed count + open count = imported count).

## When This Applies

- Migrating any pre-dolt SQLite-era beads store to embedded dolt via `bd import`
- Any JSONL that was append-only (never compacted) will accumulate tombstones over time
- Larger, older stores accumulate more tombstones (this 168-line store from Feb 2026 had 31% tombstones)

## When This Does NOT Apply

- JSONL files that have been compacted (tombstones stripped) — import count will match line count
- `bd import` from a fresh export (e.g. `bd export`) which typically strips tombstones

## Source Context

Verified 2026-07-06 during [project]-9bks migration of `mcp_agent_mail/.beads/issues.jsonl` (168 lines, created Feb 2026). Exact accounting: 110 closed + 5 open + 53 tombstone = 168 lines; `bd import` reported 115; `bd list --status=closed` confirmed 110; `bd list --status=open` confirmed 5. Zero discrepancy once tombstones accounted for.
