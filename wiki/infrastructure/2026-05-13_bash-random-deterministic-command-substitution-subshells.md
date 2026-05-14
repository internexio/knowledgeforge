---
title: Bash $RANDOM in command-substitution subshells is deterministic across rapid calls
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-13
domain: infrastructure
topic: quality-gate
tags: quality-gate, empirical, stable, tier-1
related_entries: [infrastructure/2026-05-12_empty-stdin-crontab-wipe-footgun.md, patterns/2026-05-11_atomic-write-stubs-for-readwrite-pipelines.md]
---

# Bash $RANDOM in command-substitution subshells is deterministic across rapid calls

## The bug

A bash helper that uses `$RANDOM` returns **identical values** when invoked in rapid succession via command substitution `$(...)`:

```bash
apply_jitter() {
    local BASE="$1"
    local JITTER_PCT=$(( (RANDOM % 51) - 25 ))
    local JITTERED=$(( BASE + (BASE * JITTER_PCT / 100) ))
    [ "$JITTERED" -lt 1 ] && JITTERED=1
    echo "$JITTERED"
}

for i in {1..10}; do
    apply_jitter 300
done
# Observed output: 267 267 267 267 267 267 267 267 267 267
# Expected: 10 distinct values across [225, 375]
```

## Root cause

Each `$(apply_jitter ...)` spawns a fresh subshell. Bash auto-seeds `$RANDOM` in a new subshell from the parent's PID and the current timestamp (second-resolution). Ten subshells spawned within the same wall-clock second from the same parent get the **same initial seed** — so the first `$RANDOM` read in each subshell returns the same value.

The bug is invisible when:
- Calls are spaced > 1s apart (seed differs because timestamp differs)
- Multiple `$RANDOM` reads happen within the same subshell (subsequent reads differ)
- The helper is called as `apply_jitter 300; result=$JITTERED_GLOBAL` (no subshell)

The bug is visible when:
- The helper is called as `result=$(apply_jitter 300)` in tight succession
- The first `$RANDOM` read in each subshell is the only one that matters
- Validation tests "loop and collect" — exactly the shape that reveals it

## The fix

Use `/dev/urandom` for entropy. Fresh per-call regardless of subshell state:

```bash
apply_jitter() {
    local BASE="$1"
    local R
    R=$(od -An -N2 -tu2 /dev/urandom 2>/dev/null | tr -d ' ')
    [ -z "$R" ] && R="$RANDOM"               # fallback for systems w/o /dev/urandom
    local JITTER_PCT=$(( (R % 51) - 25 ))
    local JITTERED=$(( BASE + (BASE * JITTER_PCT / 100) ))
    [ "$JITTERED" -lt 1 ] && JITTERED=1
    echo "$JITTERED"
}
```

Validation after fix: 1000 samples at BASE=300 produced 51 distinct values, full coverage of -25..25 percentage range.

## When this applies

Any time you write a bash helper that:
1. Uses `$RANDOM` for entropy or jitter
2. Is intended to be called via `$(helper ...)` command substitution
3. Might be called more than once per second

Examples that trip this:
- Retry-with-jitter loops
- Random sampling helpers
- Synthetic ID generation
- Test data scaffolding

## When this does NOT apply

- Helpers called via direct invocation (no `$(...)`), e.g. `helper; result=$GLOBAL`
- Helpers called only once per script run
- Helpers where the first `$RANDOM` read is followed by additional `$RANDOM` reads that produce the actual output

## Diagnostic trap

Standard "test your math" validation passes because the math is right. The bug only surfaces when you also check **distribution** across many calls. A test like:

```bash
echo "BASE=300: $(apply_jitter 300)"      # one sample → looks fine
```

does not catch this. A test like:

```bash
seen=$(for i in {1..1000}; do apply_jitter 300; done | sort -u | wc -l)
echo "Distinct values: $seen"             # if << 50, you have this bug
```

does catch it.

## Alternative fixes considered

- **Seed `RANDOM=$(date +%s%N)` inside the function:** macOS BSD `date` does not support `%N`, outputs literal `%N`. Linux-only.
- **`perl -e 'print int(rand(51)) - 25'`:** Works but adds a perl dependency per call.
- **`awk 'BEGIN { srand(); print ... }'`:** Same root cause — `srand()` uses time-based default seed, deterministic within a wall-clock second across processes.
- **Pass result via global variable instead of `$(...)`:** Avoids the bug but breaks function purity.

`/dev/urandom` is the cleanest fix on macOS + Linux.

## Source Context

Discovered 2026-05-13 in [project] project during implementation of paperclip-pattern-1 backoff jitter. See `~/Scripts/[project]/docs/planning/2026-05-13-paperclip-steals/01-backoff-jitter/SPEC.md` for the production usage. Related to [[content-addressed-cache-versioned-hash-prefix]] (write-then-rename atomicity pattern) and [[empty-stdin-crontab-wipe-footgun]] (another bash automation gotcha).
