---
title: Bash $? is clobbered by $(...) substitutions that run first in the same argument
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: stable
importance: 3
pinned: false
created: 2026-06-12
domain: diagnostics
topic: error-classification
tags: bash, shell-scripting, cron, error-handling, gotcha
related_entries: [diagnostics/2026-05-15_check-exit-code-before-cli-output-parsing.md, infrastructure/2026-05-13_bash-random-deterministic-command-substitution-subshells.md, patterns/2026-05-13_best-effort-bash-pipeline-runner.md]
---

# Bash $? is clobbered by $(...) substitutions that run first in the same argument

## The bug

In `scripts/daily-rank-check.sh` I wrote a per-step failure-isolation pattern for a cron job that runs a sequence of `sem reviews ...` commands. Each step logs its outcome:

```bash
if "$SEM" reviews $step >> "$LOG_FILE" 2>&1; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Reviews: $step OK" >> "$LOG_FILE"
else
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] WARN: reviews $step failed (exit $?) — continuing" >> "$LOG_FILE"
fi
```

End-to-end smoke test with a stub `sem` binary that exits 7 on a chosen pattern. The expected WARN line:

```
WARN: reviews draft --all-undrafted failed (exit 7) — continuing
```

Actually observed:

```
WARN: reviews draft --all-undrafted failed (exit 0) — continuing
```

## Root cause

When bash expands `echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] WARN: ... (exit $?)"`, the order of operations is:

1. `$(date -u +%Y-%m-%dT%H:%M:%SZ)` runs FIRST as a command substitution.
2. `date` succeeds and exits 0, setting `$?` to 0.
3. THEN `$?` is expanded — but now `$?` reflects the just-completed `date`, not the failed `sem` call that triggered the `else` branch.

So the WARN line dutifully reports `exit 0` for what was a real failure. Silent loss of diagnostic detail — the cron logs say "something failed but the exit code looks fine," masking the underlying signal.

## The fix

Capture `$?` into a local variable BEFORE any command substitution runs:

```bash
else
    rc=$?    # capture immediately while $? still holds the failed cmd's exit code
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] WARN: reviews $step failed (exit $rc) — continuing" >> "$LOG_FILE"
fi
```

Verified by re-running the same smoke test: WARN line now reads `exit 7` as expected.

## When this applies

Any shell script that:
- has an error-handling branch that logs an exit code via `$?`, AND
- the log line uses `$(command)` substitution somewhere in the same argument (timestamps, hostname, anything)

The pattern is silent — there's no syntax error, no warning. Only an end-to-end test that compares actual exit codes against logged ones catches it.

## When this does NOT apply

- Bare `echo "exit $?"` with no `$(...)` substitutions — `$?` survives until expansion.
- Using `trap ... ERR` for error reporting — different mechanism, not affected.
- Languages other than bash/zsh (POSIX shells have the same behavior, but fish/etc. work differently).

## Concrete grounding

- Reproduced and fixed in commit `ced40b9` of internexio/sem-tools (sem-tools-xcu).
- Validated via stubbed-binary smoke test: created a `sem` script that records args and exits 7 on a configurable pattern, ran the cron, grepped the log for "WARN" — before the fix showed "exit 0", after the fix showed "exit 7".
- Bash version: 5.x on macOS Darwin 25.5.0. Behavior is POSIX-standard; not version-specific.

## Why this is worth saving

This is a non-obvious, silently-failing bug that any future shell-script with timestamped error logging will hit. Easy to miss in code review because the code "reads correctly" — the bug is in the expansion order, not the syntax. The fix is one extra line (`rc=$?`) but you have to know to add it.

## Source Context

Discovered 2026-06-12 during sem-tools cron extension (sem-tools-xcu) while implementing failure-isolation logging for a rank-check multi-step pipeline. The bug was caught by end-to-end smoke test (stubbed `sem` binary exiting 7, grepped logs for the reported exit code). Related to [[check-exit-code-before-cli-output-parsing]] (another error-code handling gotcha) and [[best-effort-bash-pipeline-runner]] (the broader pattern that this diagnostic supports).
