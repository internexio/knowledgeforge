---
title: launchd-spawned subprocess cannot resolve shell aliases — always invoke the underlying binary
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: stable
importance: 3
pinned: false
created: 2026-06-10
domain: infrastructure
topic: ops
tags: [scheduling, deployment, empirical, stable, quality-gate]
related_entries: ["infrastructure/2026-05-13_launchd-cwd-trap-relative-tool-lookups.md", "infrastructure/2026-05-11_python-package-cli-under-cron.md", "diagnostics/2026-05-15_subprocess-test-isolation-env-vars-sandbox-all-paths.md"]
---

# launchd-Spawned Subprocess Cannot Resolve Shell Aliases

## Pattern

Shell aliases (defined in `~/.zshrc`, `~/.bashrc`, etc.) are NOT resolvable from Python's `subprocess.run()` or any other `execvp()`-style spawn. `execvp` consults `$PATH` for literal filenames only; it does not source the user's interactive shell config. Code that works interactively ("just run `bd` in your terminal!") will fail with `FileNotFoundError: [Errno 2] No such file or directory: 'bd'` when the same code is run from a launchd-spawned daemon, a CI runner, or any non-interactive environment.

## Concrete Grounding

Verified 2026-06-10 during [project] jyku.4 loop-closed demo run.

Setup: `bd` is a zsh alias defined in `~/.zshrc` pointing at the actual binary `br` at `~/.local/bin/br`. The [project] `iteration_loop/bd_update.py` module calls `subprocess.run(["bd", "show", issue_id, "--json"], ...)`.

Under an interactive shell: works fine, alias resolves to br.

Under launchd-spawned Python (the exec-consumer daemon): every `subprocess.run(["bd", ...])` raised `FileNotFoundError`, which the module catches and reports as a `bd_update.BdUpdateResult(ok=False)`.

Symptom in the audit log: every task's audit envelope showed `bead_close_skipped_reason="bd_unreachable"` even for beads that existed and were closeable. The daemon was silently failing to close any bead under launchd, even though the unit tests (run from an interactive zsh shell) passed.

Reference: [project]-2quf bead filed for the fix.

## Distinct from Path-Related Gotchas

This is **not** the launchd CWD trap (2026-05-13, which defaults CWD to `/`), nor the PATH environment variable minimalism (launchd defaults to `/usr/bin:/bin:/usr/sbin:/sbin`). Those are about binary lookup by filename in `$PATH`. This pattern is about **aliases not being expanded before the subprocess even tries the path lookup**.

In launchd context:
- `$PATH` env var is minimal but can be extended via plist EnvironmentVariables
- `CWD` is `/` but can be set via plist WorkingDirectory
- **Aliases, however, live in the shell's interactive configuration — not in env vars, not in a directory**

When Python calls `subprocess.run(["bd", ...])`, the kernel's `execvp()` is trying to find a file named literally `bd`. The shell alias (which expands `bd` → `~/.local/bin/br` at parse time) never runs. The alias is metadata of the zsh process, not a file on disk.

## Fix

In any module that invokes a CLI via subprocess AND that module will run under launchd / cron / a non-interactive context:

1. **Resolve the underlying binary path explicitly.** Either:
   - Module-level constant: `BR_BIN = shutil.which("br") or "~/.local/bin/br"`
   - Discover at install time and bake into a config file
   - Read from an env var (e.g., `BR_BIN = os.environ.get("BR_PATH", "~/.local/bin/br")`)

2. **Invoke the resolved binary, never the alias name:**
   ```python
   # WRONG (will fail under launchd, pass interactively)
   subprocess.run(["bd", "show", issue_id, "--json"], ...)
   
   # RIGHT
   subprocess.run([BR_BIN, "show", issue_id, "--json"], ...)
   ```

3. **Add a startup check** that exits with a clear error if the binary isn't on the resolved PATH:
   ```python
   if not os.path.exists(BR_BIN):
       sys.exit(f"FATAL: br binary not found at {BR_BIN}")
   ```

### Counter-Temptation

Do NOT try to "source ~/.zshrc" from Python. Aliases live in the shell process, not in env vars; sourcing won't expose them to `execvp`.

## When This Applies

Any subprocess invocation from:
- A LaunchAgent / LaunchDaemon (macOS)
- A systemd unit (Linux)
- A cron job
- A CI pipeline
- A web request handler
- Any environment that is NOT an interactive login shell

Especially likely to bite when:
- The local dev cycle is interactive (alias works)
- The production cycle is daemonized (alias breaks)
- Tests are run interactively (passing)
- The daemon runs via launchd (failing)

## When This Does NOT Apply

- Pure interactive consumption (REPLs, terminal tools running as the user's logged-in shell)
- Subprocess invocations of binaries that don't have aliased names (no `bd` → `br` translation needed)
- Installed console_scripts entry points (e.g., via `pip install -e` with `setup.py`'s `entry_points.console_scripts`) — the installed wrapper is a real file on disk

## Diagnostic Signal

- Tests pass interactively
- Production silently fails with `FileNotFoundError` on a CLI name that you'd expect to "just work"
- Look for `subprocess.run([<short_name>, ...])` patterns where `<short_name>` is an alias you use at the prompt
- Re-verify with `which <short_name>` vs `type <short_name>`:
  - `which` reports the binary path (will be empty for aliases)
  - `type` reports "alias for ..." (confirming it's aliased, not a binary)

## Source Context

[project] jyku.4 loop-closed demo run, 2026-06-10. The exec-consumer daemon runs under launchd and processes execution envelopes by closing beads and updating state. The `bd_update` module was written with tests passing (interactive shell) but failed silently in production (launchd) because every `subprocess.run(["bd", ...])` raised `FileNotFoundError`. The alias `bd` → `br` is defined in the operator's `~/.zshrc` but is invisible to launchd-spawned Python subprocesses. Fixed by resolving the actual binary path at module init and invoking that instead.
