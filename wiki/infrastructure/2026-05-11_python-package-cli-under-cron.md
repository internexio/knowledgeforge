---
title: Python package CLIs under cron — module form required for relative imports
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-11
tags: deployment, scheduling, quality-gate, adversarial, empirical
related_entries: []
---

# Python Package CLIs Under Cron — Module Form Required for Relative Imports

A Python package CLI invoked directly as a script (`python3 /abs/path/to/package/cli.py`) fails with `ImportError: attempted relative import with no known parent package` whenever `cli.py` contains a relative import like `from . import cycle, state`. The script lacks package context because Python's resolution of "what package does this file belong to?" is driven by `__init__.py` walk + `sys.path` — and a direct script invocation neither sees the parent package directory in `sys.path` nor knows the file's package identity.

This bites every cron-driven Python CLI inside a package. The cron daemon runs scripts with a near-empty environment and a cwd of `$HOME`. There is no implicit package context.

## Wrong (cron entry that fails at runtime)

```bash
0 6 * * * python3 ~/Scripts/myproject/mypkg/cli.py cycle
```

Output: `ImportError: attempted relative import with no known parent package`

## Right (module form with explicit cwd)

```bash
0 6 * * * cd ~/Scripts/myproject && python3 -m mypkg.cli cycle
```

The module form (`python3 -m mypkg.cli`) places `mypkg/cli.py` in package context: Python adds the cwd to `sys.path`, sees `mypkg/__init__.py`, and resolves `from . import cycle` correctly.

A thin shell wrapper around the cron entry should ALSO use the module form:

```bash
#!/bin/bash
PKG_ROOT="~/Scripts/myproject"
cd "$PKG_ROOT" && python3 -m mypkg.cli "$@"
```

## Failure Mode

Tests pass (`python -m pytest` runs from project root with correct cwd), local interactive invocations work (`python -m mypkg.cli` from the project dir), but the cron-driven cycle silently never runs because of the import error. Fail-open semantics make this even more invisible — the wrapper catches the non-zero exit and exits 0, leaving operator-visible logs but no actionable error.

## When This Applies

- Any Python package that exposes a CLI entry point via `cli.py` (or `__main__.py`) using `from . import ...` style relative imports.
- Cron, systemd timers, launchd, or any system scheduler that invokes a Python file directly.
- CI/CD scripts that paste an absolute script path into a job runner.
- Wrapper scripts for any of the above.

## When This Does NOT Apply

- Single-file scripts with no package siblings (no relative imports).
- Packages installed via `pip install -e` with a console_scripts entry point — the installed shim handles the package context automatically.
- Direct invocations from within an active virtualenv whose activation adds the package root to `sys.path` (this is fragile and not recommended for cron).

## Source Context

Discovered during [project] Dreaming Tier 1 implementation — Phase I8 entry script audit. The Phase I1 scaffold wrote `[project]-dream.sh` invoking `python3 "$[project]_DIR/dream/cli.py" cycle`. Phase I8 added relative imports to `cli.py` (`from . import cycle, findings, state, undo`). The next manual test of the wrapper produced `ImportError: attempted relative import with no known parent package`. Fixed in Phase I8 by changing the wrapper to `cd "$[project]_DIR" && python3 -m dream.cli`. The bug would have surfaced in production on the first cron-driven cycle if unaddressed.
