---
title: Stale-signal feedback loop in log-scanning workers — 7-day recency filter pattern
source_mode: builder
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-11
domain: diagnostics
topic: queue-observability-pitfall
tags: observability, signal-collection, feedback-loops, monitoring, patterns
related_entries:
  - orchestration/2026-05-29_append-only-queue-fingerprint-dedup-reconcile-gc.md
  - diagnostics/2026-07-07_baking-pipeline-dispatch-false-silently-discards-proposal-text.md
  - diagnostics/2026-06-12_count-by-refreshed-field-dedup-liveness-detection.md
---

# Stale-Signal Feedback Loop in Log-Scanning Workers — 7-Day Recency Filter Pattern

## Pattern: Stale-Signal Feedback Loop in Log-Scanning Workers

### What it is

When a signal-collection worker reads from a rolling log (routing log, error log, event store) without a recency filter, a single historical event can create a self-sustaining proposal feedback loop:

1. Worker reads log, finds event E at time T (e.g. a single critic rejection on day 1)
2. Worker passes E to LLM synthesis → LLM generates proposal P about E
3. P enters the bake pipeline → critic/strategist rejects P (e.g. stale premise, no entities)
4. The rejection of P is itself logged as a new routing event R
5. Next night: worker reads log, finds E (still there) + R (new rejection of P)
6. Both signals feed synthesis → LLM regenerates a *new* variant of P
7. Loop repeats nightly — signal density grows, proposal keeps getting generated and rejected

**Observed in:** `[project]/iteration_loop/workers/project_reviewer.py` — the `_collect_routing_signals` function read the KF routing log (`~/.claude/wiki/operations/routing-log/YYYY-MM.md`) with no recency filter. A single July-2 wiki-linter rejection event seeded a `"[[project]] reliabi"` meta-proposal that regenerated nightly for 8 days. Each nightly rejection appeared as a new routing entry, amplifying the signal on subsequent nights.

**Additional discovery:** The routing log keyword filter (`"re_routed" in line`) matched EVERY line in the log because `"re_routed"` is a JSON key present in every JSONL entry — making the filter effectively a no-op for exclusion. The stale-event problem was compounded by the filter including all entries indiscriminately.

### The Fix

Add a `lookback_days` recency filter to the signal collector:

```python
def _collect_routing_signals(routing_log_root: Path, lookback_days: int = 7) -> str:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=lookback_days)
    # ...
    for line in text.splitlines():
        stripped = line.strip()
        if not any(k in stripped for k in friction_keywords):
            continue
        # Parse timestamp, skip stale events:
        try:
            entry = json.loads(stripped)
            ts_str = entry.get("timestamp", "")
            if ts_str:
                ts = datetime.fromisoformat(ts_str)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts < cutoff:
                    skipped_stale += 1
                    continue
        except (json.JSONDecodeError, ValueError):
            pass  # fail-open: include undated lines
        relevant.append(stripped)
    
    # Surface event count + stale-skip count in output so LLM synthesis
    # can judge signal density before generating proposals:
    header = f"routing friction signals (last {lookback_days}d): {len(relevant)} event(s)"
    if skipped_stale:
        header += f" [{skipped_stale} older event(s) excluded as stale]"
```

Two key design choices:
- **Fail-open on parse failure**: lines without a parseable timestamp are included rather than silently dropped — better to surface an undated signal than to miss a real friction event.
- **Surface occurrence count in output**: the header tells the LLM how many events were found in the window. A single event vs. 10 events is meaningful context for deciding whether to generate a proposal.

### When this pattern applies

- Any worker that reads from an append-only event log (routing log, error log, audit trail, git log, etc.) to detect "recurring problems"
- The worker passes raw signal lines to an LLM for synthesis
- The log accumulates historical events indefinitely (no TTL, no rotation)
- The worker's own output (or its downstream rejection) can itself appear in the log it reads

### When it does NOT apply

- Workers that read from a bounded/cleared queue (e.g. Orchestra pending-suggestions.jsonl — this has TTL-based expiry)
- Deterministic rule-based workers (no LLM synthesis step — they don't generate proposals that get logged back as signals)
- Workers that already deduplicate against the output channel (dedup protects against duplicate emissions, not against stale re-generation)

### Detection signal

If a worker generates the same proposal headline nightly, and the proposal is consistently rejected by critic with reasoning like "stale premise" or "single event, no recurrence pattern" — this feedback loop is the likely cause. Inspect the signal-collection function for:

1. Missing recency filter
2. Log keyword matching that catches ALL entries (because the keyword appears as a JSON key, not just in values)

### Prevention

- Always pair a time-window filter with log-scanning signal collectors (default: 7 days)
- When the signal collector output includes event count, add it to the LLM prompt so it can self-regulate
- Consider filtering out entries where `source_beads_issue_id` equals the worker's own anchor bead (prevents secondary echo from the worker's own rejected proposals feeding back into it)

## Source Context

**Session:** [project]-dnqa-recency-filter (2026-07-11). A 7-day recency filter was added to `project_reviewer.py`'s `_collect_routing_signals` function after detecting an 8-day feedback loop where a single stale wiki-linter rejection from July-2 kept regenerating a proposal nightly. The routing log carried no timestamp parsing, so all events were included regardless of age. Adding the recency window (with a cutoff date of `now - timedelta(days=7)`) eliminates the feedback loop by ensuring only recent friction signals feed the LLM synthesis step.

<!-- KF-MODE: builder | DECISION: novel -->
