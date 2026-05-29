---
title: bd CLI dependency-wiring inversion + two-pass create-then-wire pattern
source_mode: direct
novelty_type: tool_quirk_and_workaround_pattern
grounding_score: 0.85
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-05-27
tags: beads, bd-cli, dependency-wiring, cli-semantics, shell-scripting, batch-issue-creation, gotcha, two-pass-pattern
domain: infrastructure
topic: cli-automation
related_entries: []
---

# bd CLI dependency-wiring inversion + two-pass create-then-wire pattern

## The gotcha

`bd` (the beads CLI) has inconsistent dependency-direction semantics across subcommands. The natural-language reading of `--deps "blocks:X"` suggests "this issue is blocked by X" — but the actual semantics is the opposite.

| Command | Semantics |
|---|---|
| `bd dep add A B` | "A depends on B" / "B blocks A" — **depender first** |
| `bd link A B` | "B blocks A" — **blocker is second positional arg** (matches `bd dep add`) |
| `bd create --deps "blocks:X"` | "**this issue blocks X**" — i.e., the new issue is the blocker, X is downstream — **opposite of natural reading** |

The inversion is silent. The bead gets created, the relationship gets stored, but `bd ready` shows the wrong items as unblocked.

## Symptoms when you hit it

- `bd ready` shows downstream gates / terminal beads as unblocked
- `bd ready` does NOT show the entry-point bead (which should be ready) — it appears blocked
- `bd dep list <entry-point-bead> --direction=down` shows the bead is "depending on" beads that should be downstream from it
- `bd dep list <entry-point-bead> --direction=up` returns "No issues depend on..." when there should be many

## The fix (one-time correction)

For each (depender, blocker) pair you intended, run:

```bash
bd dep remove "$blocker" "$depender"   # remove the inverted dep
bd dep add    "$depender" "$blocker"   # add the correct dep
```

The pair-flipping pattern in a fix script:

```bash
PAIRS=(
  "$DEPENDER_A $BLOCKER_A"
  "$DEPENDER_B $BLOCKER_B"
  # ...
)
for pair in "${PAIRS[@]}"; do
  read -r depender blocker <<< "$pair"
  bd dep remove "$blocker" "$depender" 2>/dev/null || true
  bd dep add    "$depender" "$blocker" 2>/dev/null || true
done
```

`|| true` makes the fix idempotent — re-running is a no-op once deps are correct.

## The pattern to use going forward

When generating a script that creates a graph of beads with dependencies, use **two passes**:

```bash
# Pass 1: create all beads (no --deps, just --parent for hierarchy)
EPIC=$(bd create "..." --type epic --silent)
BEAD_A=$(bd create "..." --type task --parent "$EPIC" --silent)
BEAD_B=$(bd create "..." --type task --parent "$EPIC" --silent)
# ... rest of beads

# Pass 2: wire deps with unambiguous semantics
bd dep add "$BEAD_B" "$BEAD_A"   # B depends on A (B is downstream)
# ... rest of edges
```

Verify with:
- `bd ready` — should show only the entry-point bead (+ epic, which always appears) as unblocked
- `bd dep list <entry-point> --direction=up` — should show all immediate downstream dependents
- `bd dep tree <terminal-bead>` — should show the full upstream chain

## When this applies

- Any session that batch-creates 2+ beads with dependencies
- Any time you're tempted to use `--deps "blocks:X"` in `bd create` to express "this is blocked by X"
- Any debugging session where `bd ready` shows surprising items

## When this does NOT apply

- Single-bead creation without deps
- Using the interactive `bd create-form` (which prompts unambiguously)
- Using `bd dep add` directly — no inversion issue there

## Concrete grounding from the originating session

Session built a 14-bead Phase 0 epic for the client-project project. Initial `scripts/create-beads.sh` used `--deps "blocks:$PRIOR_BEAD"` for every dependency. After execution:

- `bd ready` returned only the epic + the FINAL gate bead (P0B-GATE / sa-qp2.17) — exactly inverted from intent
- `bd dep list sa-qp2.1 --direction=down` returned the three beads that should have depended ON sa-qp2.1, not the other way around
- `bd show sa-qp2.17` listed P0B-07 and P0B-08 under "BLOCKS" (with arrow `←`) — i.e., P0B-GATE was registered as blocking those, not blocked by them

A `scripts/fix-bead-deps.sh` with 30 paired `bd dep remove` + `bd dep add` calls corrected every edge. Post-fix verification:
- `bd ready` returned sa-qp2.1 (the actual scaffold bead) + epic ✓
- `bd dep tree sa-qp2.17` showed the full upstream chain back through P0A-GATE to sa-qp2.1 ✓

Both scripts (`create-beads.sh` with corrected two-pass pattern + `fix-bead-deps.sh` for the one-time correction) are committed at `client-project@0747dc3`.

## Cross-references

If a project sets up beads via a generated script, prefer the two-pass pattern over `--deps`. The cost is one extra loop at the end of the script; the savings are not discovering an inverted graph after `bd init` is already done and a `rm -rf .beads/` is awkward (state may not be cleanly disposable).

## Source Context

Discovered during client-project Phase 0 bead scaffolding session (2026-05-27). Candidate content source: claude direct translation of multi-bead artifact + symptom diagnosis during `bd ready` verification.
