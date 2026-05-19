---
title: Check exit code before parsing CLI output — failures emit help that greedy-matches success regexes
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: stable
importance: 5
pinned: false
created: 2026-05-15
domain: debugging
topic: error-classification
tags: empirical, quality-gate, grounding, adversarial, stable
related_entries: []
---

# Check exit code before parsing CLI output

## The trap

Shell wrappers around CLIs commonly parse the tool's stdout/stderr with regex or sed to extract a name, ID, or path. When the CLI **fails**, it often prints its `--help` text, and the help text contains argument descriptions that mention success-shaped content. Regex extractors that don't first gate on exit code will greedy-match the help text and emit a plausible-but-wrong value, which then propagates into downstream calls that fail again with a different, more confusing error.

The original error is masked by the cascading regex result. Debugging chases the wrong path for months.

## Concrete trigger ([project], 2026-05-15)

`scripts/patrol-lib.sh` on Mac Mini was logging `Patrol _idle_patrol failed: polecat worktree errored` every 15 minutes for two months — 228 cumulative failures. The polling loop then called `gt polecat status [project]/worktree`, got `not found`, and confirmed "errored". No polecat named "worktree" had ever existed in the rig.

The actual chain:

1. `gt sling <bead-id> [project] ...` exited non-zero (bead route was misconfigured).
2. `gt sling`'s failure path printed its full `--help` text, including the flag description `--base-branch  Override base branch for polecat worktree (e.g., 'develop', 'release/v2')`.
3. The wrapper's regex `sed -n 's/.*polecat \([a-z_-]*\).*/\1/p'` greedy-matched `polecat worktree` from that help line.
4. `polecat_name` got set to `"worktree"` — a literal substring of the help text.
5. The polling loop then queried `gt polecat status [project]/worktree`, got `not found`, and logged "polecat worktree errored".

The script never noticed the original `gt sling` failure because it had `|| true` after the assignment and ignored `$?`. The misleading "polecat worktree errored" message was identical to a real polecat error, so the alarm-tier looked normal.

## The rule

Always check exit code **before** parsing stdout / stderr:

```bash
output=$(some-cli arg1 arg2 2>&1)   # NO `|| true` here
rc=$?

if [[ $rc -ne 0 ]]; then
    log "ERROR" "$tool failed (rc=$rc): $(echo "$output" | head -3 | tr '\n' ' | ')"
    return 1
fi

# Only NOW parse for the success-shaped fields.
extracted=$(echo "$output" | sed -n '...')
```

And make the success regex specific to **explicit success markers**, not generic substring matches:

```bash
# BAD — matches 'polecat worktree' in --help text
sed -n 's/.*polecat \([a-z_-]*\).*/\1/p'

# GOOD — requires the explicit success line
sed -n 's/.*Created polecat:[[:space:]]*\([a-z0-9_-][a-z0-9_-]*\).*/\1/p'
```

If multiple success-line formats exist (because the wrapped CLI changed output over versions), chain them with `|| ` fallbacks rather than relaxing the regex:

```bash
name=$(echo "$output" | sed -n 's/.*Created polecat:[[:space:]]*\([a-z0-9_-]*\).*/\1/p' | head -1)
[[ -z "$name" ]] && name=$(echo "$output" | sed -n 's/.*Polecat[[:space:]]\([a-z0-9_-]*\)[[:space:]]spawned.*/\1/p' | head -1)
[[ -z "$name" ]] && name=$(echo "$output" | sed -n 's/.*Allocated polecat:[[:space:]]*\([a-z0-9_-]*\).*/\1/p' | head -1)
if [[ -z "$name" ]]; then
    log "ERROR" "Could not parse name from $tool output; treating as failure"
    return 1
fi
```

The final "if still empty → fail" guard catches CLI output format changes immediately rather than silently passing `unknown` (or whatever empty string handling does) downstream.

## When This Applies

- Any shell wrapper that parses CLI stdout/stderr to extract structured data
- Polling loops that gate follow-up actions on parsing results
- Watchdog scripts that monitor tool invocations and expect specific output shapes
- Cron jobs that delegate to CLIs and need to distinguish success from failure
- Scripts that chain multiple tool calls and propagate parsed results across the chain

## When This Does NOT Apply

- The wrapped CLI prints success content to stderr and treats it as fatal-but-recoverable — non-zero exit code with valid stdout is rare but exists (some tools use exit codes for "found nothing" vs "actually broken"). Read the docs for each tool.
- If the parsing target is a single well-defined header (e.g., HTTP status code from a separate `-w` template), the gating isn't needed because the field has a strict format.
- Performance-critical inner loops where the cost of a `[[ -z ]]` check matters — but if you're parsing CLI output in a hot loop you have bigger architecture issues.

## Grounding

Bug observed empirically: 228 failures over ~2 months on Mac Mini's `_idle_patrol`. The regex bug was masked because the cascading symptom (`gt polecat status` returns "not found") was indistinguishable from a real polecat-died-mid-execution scenario, which was the original intended trigger for that error path.

Fix shipped in `scripts/patrol-lib.sh` commit `3a0edfa` ([project] repo). Two changes:

1. `gt sling` exit code now checked explicitly; non-zero (and not the recoverable formula-instantiation case) bails immediately with the actual error head logged.
2. Polecat-name regex now requires explicit success markers (`Created polecat:` / `Polecat X spawned` / `Allocated polecat:`); the bare `polecat WORD` fallback that caused the bug is removed.

Verified end-to-end: `gt sling nm-itmw [project] --formula patrol-idle-review` now succeeds, polecat spawns, formula bonds, status=hooked.

## Related anti-patterns

- **Silent `|| true`** swallowing exit codes: a debugging cost in any context, but particularly destructive when paired with regex extraction.
- **Tee'ing stderr into stdout for parsing**: `2>&1` mixed with `sed` extraction means any warning line that happens to contain the regex shape will match. Capture stdout and stderr separately (`-o "$STDOUT" 2> "$STDERR"`), parse stdout for success, check stderr for warnings.
- **Greedy regex against CLI output in general**: prefer multiple specific patterns chained with fallbacks over one broad pattern.

## Source Context

Direct diagnostic from [project] morning-loop foundation session (2026-05-15). The patrol-lib.sh wrapper had been silently propagating help-text false-matches for two months due to missing exit-code gate; the bug was discovered during systematic failure-cascade analysis of the idle-patrol escalation surface.
