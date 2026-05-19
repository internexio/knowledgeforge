---
title: bd types.custom validator cache requires unset+reset to refresh after edit
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-05-15
tags: quality-gate, empirical, stable
related_entries: [diagnostics/2026-05-13_bd-search-idempotency-grep-trap.md]
domain: infrastructure
topic: server-configuration
---

# bd types.custom validator cache requires unset+reset to refresh

## Symptom

Running `bd create --type=<custom-type>` (or any code path that creates issues of a custom type, e.g. `gt convoy create`) fails with:

    Error: validation failed for issue <id>: invalid issue type: <type>

Even though:

- `~/.beads/config.yaml` (or equivalent) declares `types.custom` containing the type
- `bd config get types.custom` returns the correct comma-separated list including the type
- `bd config list` confirms the value is set

The validator inside `bd` is consulting a stale cache that doesn't match what the config-getter reads.

## Diagnosis sequence

Run from the directory containing the affected `.beads/`:

```bash
bd config get types.custom              # → returns the expected value
bd create --type=<custom-type> --title="probe" ...   # → still rejects
```

If the value is right but creation still rejects, the validator is stale.

## Fix

Force a config write by unsetting and re-setting to the same value:

```bash
bd config unset types.custom
bd config set types.custom "agent,role,rig,convoy,slot,queue,event,message,molecule,gate,merge-request"
bd create --type=<custom-type> --title="probe" --priority=4 --description="cache refresh verification"
# ✓ Created issue: ...
```

The value passed to `set` can be identical to what `get` returns — the act of writing forces the validator to refresh.

## When it applies

Hit this pattern THREE distinct times in a single session on three separate beads databases:

- `~/gt/.beads` — rejected `--type=convoy` despite types.custom listing convoy
- `~/gt/town/.beads` — same; required `bd migrate` first because schema_version was behind
- `~/gt/tuannw/.beads` — rejected `--type=agent` during `gt sling` polecat spawn (retry-with-backoff was masking the issue until the timeout)

All three were resolved by the unset+reset, no other intervention.

## When it does NOT apply

- The config value was actually wrong or missing → set it correctly (the validator isn't stale, the config is).
- The bead database schema is behind → run `bd migrate` first.
- The issue type really isn't in the canonical custom-types list for this project.

## Grounding

Observed three times empirically in the session 2026-05-15. Fix is reliable on first attempt each time. Root cause (likely a persisted validator config inside the bd binary that doesn't auto-refresh from `config.yaml`) is unconfirmed — this entry documents the user-facing remediation, not the bug's internal mechanism. Worth reporting upstream to beads but per project rules (br/gt/beads changes live in [project]), the workaround is the canonical fix here.

## Related diagnostics

When the unset+reset doesn't help, also check:
- `bd doctor --check=conventions` for migration backlog
- `bd dolt status` for server/database mismatch
- The validator may be reading from a different `.beads` than you think — `bd config list` shows the active path

## Source Context

Direct diagnostic from [project] morning-loop-foundation session (2026-05-15). This pattern emerged during gt/bd integration testing across three separate beads databases in the GasTown mayor rig infrastructure.
