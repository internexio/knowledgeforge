---
title: launchd CWD-is-slash trap for CWD-relative CLIs
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-13
tags: diagnostics, infrastructure, debugging, empirical, stable
related_entries: ["infrastructure/2026-05-11_python-package-cli-under-cron.md", "diagnostics/2026-05-13_bd-search-idempotency-grep-trap.md"]
---

# launchd CWD Trap: Jobs Run with `cwd=/`, Breaking CWD-Relative Tool Lookups

## The Symptom

A shell script that works perfectly when run from an interactive terminal fails silently or cryptically when scheduled via launchd. Common cryptic forms:

- `bd create ...` → `Error: no beads database found`
- `git status` → `fatal: not a git repository`
- `python script.py` → `ModuleNotFoundError` on a sibling-directory import
- Relative paths in scripts (`./helper.sh`) → "No such file or directory"

## The Cause

Unless overridden via `WorkingDirectory` in the plist, **launchd starts jobs with CWD=`/`**. Any tool that resolves state via "walk up from CWD looking for X" — git's `.git`, bd's `.beads`, python's sys.path, plus most ad-hoc scripts — will not find that state.

This is different from cron (which uses `$HOME` as CWD on most systems) and different from interactive shells (which use wherever you cd'd). So even a script that's been "tested" via SSH-and-run will work; the same script under launchd will not.

## The Fix (Three Options, Preferred Order)

### 1. Set the tool's state directory via env var in the plist (RECOMMENDED)

Most explicit, doesn't affect other path resolution:

```xml
<key>EnvironmentVariables</key>
<dict>
    <key>BEADS_DIR</key>
    <string>/Users/<user>/<repo>/.beads</string>
    <key>GIT_DIR</key>
    <string>/Users/<user>/<repo>/.git</string>
</dict>
```

This is the cleanest approach because:
- Only affects the tools that need it
- Doesn't surprise other tools by changing their runtime cwd
- Easily auditable in the plist

### 2. Set `WorkingDirectory` in the plist

Sweeps all CWD-relative behaviors at once, but may surprise tools that expect a specific runtime location:

```xml
<key>WorkingDirectory</key>
<string>/Users/<user>/<repo></string>
```

Use this when your script and all its dependencies actually expect to be in that directory.

### 3. `cd` inside the script before invoking the CWD-relative tool

Works but easy to forget when adding new tools:

```bash
cd /Users/<user>/<repo> || exit 1
bd create ...
```

This approach makes the dependency implicit in the script body; prefer option 1 or 2 for clarity.

## Diagnostic Recipe

When a launchd-scheduled script "passes" interactively but fails under launchd:

1. **Verify what CWD launchd hands to the job:**
   Add `pwd` near the top of the script and let the next scheduled run write it to your log. Expect to see `/`.

2. **Verify environment variables:**
   ```bash
   launchctl print "gui/$(id -u)/<label>"
   ```
   Shows the full env passed in. Anything missing that your interactive shell has set (e.g., from `.zshrc`) won't be there.

3. **Reproduce in the same env:**
   ```bash
   sudo -u <user> -H bash -c 'cd / && WATCHDOG_ENABLED=1 PATH="<plist-path>" /path/to/script.sh'
   ```
   Approximates launchd's environment without scheduling.

## Detection Heuristic

The error path may swallow the actual stderr. If the error message says nothing about CWD or "not a repository / no database found," check whether the failing path could be CWD-relative:

**Strong indicators that this is the trap:**
- Manual run from interactive shell: succeeds
- Same command via launchd-scheduled wrapper: fails silently (stderr swallowed via `>/dev/null 2>&1`)
- Working with absolute paths in script BUT the underlying tool defaults to CWD-relative state

## When This Does NOT Apply

- Tools that take an explicit path argument and ignore CWD (e.g., `ls /etc`)
- launchd plists with `WorkingDirectory` already set
- Statically-loaded tools (no state file lookup, no `.git`, `.beads`, etc.)

## Grounding

Discovered 2026-05-13 in [project] project, Paperclip Pattern 2 silent-run watchdog. The scenario: a `bd create` call written into a launchd-scheduled script (`com.[project].healthcheck.plist`). Interactive runs worked perfectly. The first scheduled run failed with a FAILURE log message but no stderr (caller used `>/dev/null 2>&1`).

After improving the error path to capture combined output, the launchd run surfaced:
```
Error: no beads database found / Hint: run 'bd init' or set BEADS_DIR
```

The fix: added `<key>BEADS_DIR</key><string>~/Scripts/[project]/.beads</string>` to plist EnvironmentVariables. Subsequent launchd kickstart found the database, ran the idempotency check, and correctly no-op'd because the bead already existed.

**Commit reference:** 4dd42fa ([project] master, Paperclip Pattern 2 Phase B).

**Related diagnostics:**
- `bd-search-idempotency-grep-trap` — sibling tool-specific gotcha caught in the same watchdog code
- `python-package-cli-under-cron` — launchd shares the near-empty-env problem with cron (though cron defaults to `$HOME` not `/`)

## Source Context

[project] paperclip Pattern 2, deployment audit phase 2026-05-13. The health-check watchdog runs via launchd on a frequent cadence to detect when the main dreaming cycle stops firing. First implementation passed interactive testing but failed silently under launchd because it couldn't locate the beads database.
