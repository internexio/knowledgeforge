---
title: macOS Gatekeeper rejects binaries SCP-copied from another Mac — build natively on target
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-11
domain: infrastructure
topic: deployment
tags: deployment, filesystem, scheduling
related_entries: []
---

# macOS Gatekeeper Rejects SCP-Copied Binaries — Build Natively on Target

## Problem

When you build a Go binary on Mac A and copy it to Mac B via `scp`, macOS Gatekeeper on Mac B will reject it with SIGKILL (exit 137). `spctl --assess --verbose <binary>` returns "rejected". The binary is unsigned and not from a notarized source.

**Observed 2026-07-11:** built `gt` binary on laptop (arm64/darwin), scoped it to Mini via scp, set executable bit — binary was killed immediately on every invocation. `spctl --assess` confirmed the rejection. Removing quarantine xattr did not help (there was no quarantine attribute; the rejection was policy-level).

## Fix

Build the binary natively on the target machine using its own Go toolchain.

In practice for gastown:

```bash
# On Mini:
cd ~/Mini/gastown
PATH=/opt/homebrew/bin:$PATH SKIP_UPDATE_CHECK=1 make safe-install
```

- `PATH=/opt/homebrew/bin:$PATH` — Mini's Go is Homebrew-installed; launchd PATH doesn't include it
- `SKIP_UPDATE_CHECK=1` — override the forward-check when on a branch ahead of origin

## When This Applies

- Deploying Go binaries cross-machine on macOS (even same-architecture arm64→arm64)
- Any unsigned binary scp'd from another machine
- Does NOT apply to: script files (.sh, .py), which are not subject to Gatekeeper binary checks

## When This Does NOT Apply

- Linux→Linux cross-host deployment (no Gatekeeper)
- Official Homebrew installs (signed by publisher)
- Binaries built AND installed in the same session on the same machine

## Build Gotchas (gastown-specific)

- `make safe-install` checks that local branch ≤ origin. Use `SKIP_UPDATE_CHECK=1` on custom branches.
- gastown needs ICU4C headers: `brew --prefix icu4c` must resolve, or the build fails with `unicode/regex.h not found`. The Makefile auto-detects this via `CGO_CPPFLAGS`.
- Install path: `~/.local/bin/gt`, NOT `~/go/bin/gt`. Makefile removes the go/bin copy and warns if `$PATH` resolves `gt` elsewhere.

## Source Context

Discovered during [project]-happy-orchestrator-toml-migration session on Mac Mini when gastown binary deployment via scp failed with exit 137 on every invocation.
