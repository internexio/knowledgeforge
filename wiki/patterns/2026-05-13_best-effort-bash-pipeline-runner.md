---
title: Best-effort bash pipeline runner — subshell + pipefail + sed-prefix + WARN-not-fail composition
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-13
domain: patterns
topic: composition
tags: routing, stable, reconciliation, bash, failure-isolation
related_entries: [infrastructure/2026-05-12_self-watchdog-autonomous-fix-cycles.md, orchestration/2026-05-13_one-reconciliation-pipeline-called-twice.md]
---

# Best-Effort Bash Pipeline Runner

## The Pattern

A bash runner that invokes N independent step scripts in glob order,
isolates failures so one bad step doesn't kill the rest, and prefixes
each step's output with its name for clean log inspection. Runner exit
code is always 0 — reconciliation is best-effort, not transactional.

## The Composition

```bash
#!/bin/bash
set -uo pipefail   # pipefail is critical — see "why each piece" below

STEPS_DIR="$(dirname "$0")/steps"
STEPS=( $(ls "$STEPS_DIR"/0*-*.sh 2>/dev/null) )

log() { echo "[runner] $1"; }
log "starting (${#STEPS[@]} steps)"

for step in "${STEPS[@]}"; do
    step_name=$(basename "$step" .sh)
    if ! ( bash "$step" ) 2>&1 | sed "s/^/[$step_name] /"; then
        log "WARN: step $step_name exited non-zero"
    fi
done

log "complete"
exit 0
```

## Why Each Piece

| Piece | Purpose |
|---|---|
| `set -uo pipefail` | `pipefail` makes the `if !` check see the step's exit code, not sed's. Without it, `bash step \| sed` always returns sed's 0 and failures are invisible. |
| Numbered glob `0*-*.sh` | Filename prefix (`01-`, `02-`, ...) controls run order without an explicit array. Adding/removing a step is a file operation. |
| `( bash "$step" )` subshell | Each step runs in a fresh shell. `set -e` inside a step can't propagate up. Variable exports don't leak across steps. |
| `bash "$step"` (not `"$step"`) | Doesn't require execute bit. Steps can ship in any state of chmod. |
| `2>&1 \| sed "s/^/[$step_name] /"` | Folds stderr into stdout, then prefixes every line. `[step] message` format makes log triage trivial. |
| `if ! (...); then log WARN` | Failures logged at WARN level. Loop continues. |
| `exit 0` at end | Even if every step failed, the runner returns success. Best-effort semantics. |

## When This Applies

- Reconciliation pipelines (cleanup, idempotent state-repair sequences)
- Multi-step audit/health-check scripts where partial completion is useful
- Plugin-style step directories where you can't trust step quality
- Any "run these in order, but don't let one bad apple stop the batch" pattern

## When This Does NOT Apply

- Transactional pipelines where step N depends on step N-1's success.
  Use plain `set -e` and let it abort instead.
- Steps that need to communicate via the shell's variable scope.
  Subshell isolation breaks that — use sourced functions inside one
  shell instead.
- Cases where the runner's caller cares about step failures. Either
  expose the WARN count via exit code (e.g., `exit $WARN_COUNT`) or
  switch to a structured success/fail report.

## Concrete Failure-Isolation Test

```bash
SANDBOX=$(mktemp -d)
cp runner.sh "$SANDBOX/"
mkdir "$SANDBOX/steps"
cp steps/*.sh "$SANDBOX/steps/"
# Replace exit 0 with exit 1 in the middle step
sed -i '' 's/^exit 0$/exit 1/' "$SANDBOX/steps/02-foo.sh"
bash "$SANDBOX/runner.sh"
# Expected: [02-foo] message, [runner] WARN: step 02-foo exited non-zero,
#           [03-...] message continues. Runner exit 0.
```

## Grounding

Validated end-to-end in [project] paperclip Pattern 5 Phase A ([project]-mn3), commit 588ba75. Sandbox copy + replace-exit-0-with-1 in step 02 confirmed: WARN logged, subsequent steps still ran, runner exit 0. Failure-isolation test included in the spec at `~/Scripts/[project]/docs/planning/2026-05-13-paperclip-steals/05-reconcile-pipeline/SPEC.md`.

## Why Staleness Risk Is "Stable"

Bash semantics for subshells, pipefail, and pipeline exit codes are POSIX and have been stable for decades. The pattern composes well-defined primitives — there's no proprietary CLI behavior or version-pinned tool in the recipe.

## Source Context

Extracted 2026-05-13 during [project] paperclip Pattern 5 implementation. The reconciliation pipeline (see [[one-reconciliation-pipeline-called-twice]]) runs idempotent state-repair steps in sequence. The runner pattern isolates step failures using subshells + pipefail + sed prefixing, allowing partial completion while maintaining visibility. Implementation spans multiple projects: the pattern itself is from [project] reconcile-pipeline spec, now reusable for any multi-step best-effort batch runner.
