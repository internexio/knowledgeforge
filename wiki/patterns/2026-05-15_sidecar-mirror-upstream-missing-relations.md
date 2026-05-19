---
title: Sidecar mirror — recording upstream-missing relations for downstream readers
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.75
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-05-15
domain: patterns
topic: integration
tags: integration-patterns, workarounds, upstream-limitations, jsonl-sidecar, observability, multi-db-awareness
related_entries:
  - patterns/2026-05-14_file-based-stub-deferred-dispatch-surfaces.md
  - infrastructure/2026-05-14_file-based-timer-poll-deferred-ack-semantics.md
  - architecture/2026-05-15_schema-marker-multi-producer-jsonl-contract.md
  - infrastructure/2026-05-13_posix-append-pipe-buf-concurrent-jsonl-writers.md
---

# Sidecar Mirror — Recording Upstream-Missing Relations for Downstream Readers

## Pattern

When an upstream tool you can't patch fails to record a relation you need, **don't fix the tool**. Instead, record the relation in a [project]-side sidecar JSONL file at creation time, and have downstream consumers read the sidecar to fill in the gap.

The tool's primary action still succeeds. The sidecar captures the missing edge. Consumers join the two.

## Concrete Example ([project], 2026-05-15)

**Problem.** `gt convoy create <name> <bead-id-1> <bead-id-2> ...` creates a convoy bead in town beads (`hq-cv-*`) that's supposed to track multiple beads via a `tracks` dependency edge. But the `bd` binary that backs `gt` is single-DB — it can only resolve IDs in the database it's pointed at. Rig-prefixed bead IDs (`tu-*`, `cos-*`, `[project]-*`) live in separate `.beads/` databases. Result: convoy is created, but `Tracking: 0 issues` — the edges never get written because the lookup fails.

A routes file at `~/gt/.beads/routes.jsonl` *exists* and maps prefixes to paths, but `bd` doesn't consume it; only `gt bead show` (the gt-level wrapper) does. So `bd link convoy bead --type=tracks` from town beads can't find rig beads. The fix lives in the upstream gt/bd binary, which by project policy is out of scope for [project].

**Sidecar fix.** After every successful `gt convoy create`, gastown-router writes one line to `~/agent-workflow/convoy-tracking.jsonl`:

```json
{"convoy_id": "hq-cv-bq8ex", "name": "Site Scan 2026-05-15", "bead_ids": ["tu-a57", "tu-509", "tu-8za"], "created_at": "2026-05-15T23:00:48.361014Z"}
```

`nw-morning`'s "Latest convoy" section reads the sidecar:

```python
def convoy_tracking_sidecar(convoy_id: str) -> list[str]:
    if not CONVOY_TRACKING_FILE.exists():
        return []
    for line in CONVOY_TRACKING_FILE.open():
        rec = json.loads(line)
        if rec.get("convoy_id") == convoy_id:
            return list(rec.get("bead_ids") or [])
    return []
```

Convoy in the brief now shows actual membership ("tracking 3 beads via sidecar") instead of the bd-side `Tracking: 0`.

## When to Apply

- Upstream tool succeeds at the primary action but fails to record a relation you need
- You can't (or shouldn't) patch the upstream tool
- The relation is naturally available at the point-of-creation in your wrapper
- Downstream consumers can read the sidecar at low cost
- The sidecar's scope is small (one relation type, low row volume)

## When NOT to Apply

- The upstream tool is patchable → patch it; sidecars rot when the real fix lands
- The relation isn't available at creation time → you'd be guessing
- Multiple writers race the sidecar → use a real database or `fcntl.flock()`-locked appends (see related infrastructure entry on POSIX atomic append)
- Consumers can't tolerate stale sidecar state → the sidecar is eventually-consistent
- The relation schema is unstable → the sidecar becomes brittle to schema changes; use a structured marker (see related architecture entry on multi-producer JSONL contracts)

## Caveats

- **The sidecar is now load-bearing.** Backup, versioning, and cleanup all apply. Don't treat it as a temporary debugging artifact.
- **Document the upstream limitation it papers over.** Otherwise future readers will wonder why the sidecar exists, and remove it when the upstream eventually fixes the bug.
- **Keep open the underlying upstream bead.** The sidecar is mitigation, not resolution. Demote priority since user-impact is solved, but don't close.
- **Plan for retirement.** When the upstream tool is patched to record the relation correctly, the sidecar becomes dead weight. Have a deprecation strategy.

## Implementation Detail: Avoiding Corruption

For sidecar files appended by multiple writers (e.g., gastown-router + other convoy producers), the critical safety net is POSIX's `PIPE_BUF` guarantee: writes up to `PIPE_BUF` bytes (typically 4KB on modern systems) are atomic.

Keep each JSON line **compact** (no pretty-print spacing) and **under 512 bytes** to stay well below `PIPE_BUF`. See related infrastructure entry on POSIX atomic append for the full analysis.

```python
# Write compactly; don't add newlines inside the record
line = json.dumps(record, separators=(",", ":"))  # compact
sidecar_path.write_text(line + "\n", encoding="utf-8")  # atomic append
```

## Grounding

Shipped 2026-05-15 in commit `7ad1de8`. Verified end-to-end:
- 3-bead test convoy → router wrote sidecar with all 3 IDs
- `nw-morning` rendered "tracking 3 beads via sidecar" with the IDs listed
- Convoy brief showed actual tracked bead count instead of upstream tool's `Tracking: 0`

Tracking bead `[project]-w4wj` remains open at P3 with notes pointing to the sidecar workaround. The pattern is broadly reusable for any [project] wrapper around a multi-DB-unaware tool.

## Related Patterns

- **Decorator wrappers** — extend behavior without modifying the wrapped function. Sidecars are the same idea applied at the data layer.
- **Outbox pattern** (DB transactions): writing intent locally before fanning out to remote systems. Sidecars are dual — recording outcome locally because the remote system doesn't.
- **Change-data-capture mirrors** — sidecars record state changes upstream tools fail to expose.
- **File-based stub (sibling entry)** — deferred external dispatch using files; different problem space (dispatch deferral vs. missing-relation recording).

## When This Becomes an Anti-Pattern

If you notice:
1. The sidecar is recording relations the upstream tool *should* be recording (spec gap) → open upstream bead and prioritize the fix
2. Multiple sidecars for the same tool → the upstream tool has deeper design issues; coordinate with upstream maintainers
3. Consumers constantly failing to read the sidecar → it's not actually solving the problem; re-evaluate the design

## Source Context

Discovered during [project] morning-loop foundation work (2026-05-15), session `[project]-morning-loop-foundation-2026-05-15`. The convoy-tracking pipeline was failing to link multi-rig beads because the `bd` binary couldn't resolve rig-prefixed IDs. Rather than fork `bd` or block on upstream changes, the sidecar pattern emerged from the observation that gastown-router has the convoy ID and all rig bead IDs at creation time — it just needed a place to record the relation that downstream readers could access.
