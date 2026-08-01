---
title: happy-coder bundled claude binary silent failure on -p flag
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: fast_decay
importance: 3
pinned: false
created: 2026-08-01
domain: infrastructure
topic: tool-selection
tags: claude-code, happy-coder, debugging, automation, gotcha
related_entries:
  - infrastructure/2026-08-01_mac-mini-launchd-claude-p-operational-pattern.md
  - infrastructure/2026-05-14_claude-cli-bare-disables-oauth-keychain-auth.md
  - infrastructure/2026-06-10_launchd-subprocess-shell-alias-resolution-gotcha.md
---

# happy-coder Bundled claude Binary: Silent Failure on `-p` Flag

## What was learned

The `claude` binary bundled inside the happy-coder npm package is NOT the standalone Claude Code CLI and does NOT support the `-p` (headless prompt) flag. Invoking it with `-p` exits with status 0 and produces no output — no error message, no response, complete silence. This silent failure makes diagnosis difficult and leads to automation workflows breaking silently.

## The Problem

**Version observed:** happy-coder bundled binary = `@anthropic-ai/claude-agent-sdk-darwin-arm64/claude` v2.1.141.  
**Standalone CLI (correct):** `@anthropic-ai/claude-code` v2.1.220+.

**Broken path:** `/opt/homebrew/lib/node_modules/happy-coder/node_modules/@anthropic-ai/claude-agent-sdk-darwin-arm64/claude`  
**Correct path:** `/opt/homebrew/bin/claude` (installed via `npm install -g @anthropic-ai/claude-code`)

When `which claude` resolves to the bundled binary, any invocation with `-p` (headless mode):
- Exits with status 0 (success)
- Produces no stdout
- Produces no stderr
- Returns no error code to distinguish failure from success

## Diagnostic

```bash
which claude          # reveals which version is active
claude --version      # compare versions (bundled is older)
claude -p "say hi"    # bundled: exits 0 with no output; standalone: outputs response
```

**Expected behavior (standalone):** Outputs the AI response.  
**Actual behavior (bundled):** Silently exits with no output.

## Fix

```bash
npm install -g @anthropic-ai/claude-code
which claude          # verify points to /opt/homebrew/bin/claude
claude --version      # should show v2.1.220 or later
```

After installing the standalone CLI, verify it takes precedence in your PATH:

```bash
echo $PATH | tr ':' '\n' | head -5
# /opt/homebrew/bin should come before any node_modules path
```

## When This Applies

- Any context where happy-coder is installed globally and `claude` resolves to the happy-coder bundled binary
- Automated workflows (launchd, cron, scripts) invoking `claude -p` fail silently
- Common on Mac Mini setups where happy-coder is the primary or first install method
- Diagnosis shows "job runs but produces no output" — suggests the -p flag is unsupported

## When This Does NOT Apply

- If `which claude` already points to `/opt/homebrew/bin/claude` from `@anthropic-ai/claude-code`, this is not the issue
- Interactive Claude Code sessions via Happy CLI (those use the happy-coder runtime correctly)
- Non-headless usage where interactive terminal modes are available

## Staleness Note

**Version-specific and time-sensitive.** happy-coder may update its bundled binary in future releases to add `-p` support or deprecate the bundled version entirely. Verify the failure on the installed version before assuming this diagnostic applies to newer releases.

## Related Diagnostics

The companion entry "[Mac Mini launchd + claude -p operational pattern](infrastructure/2026-08-01_mac-mini-launchd-claude-p-operational-pattern.md)" documents the correct setup for running `claude -p` from launchd. That entry assumes the standalone CLI is installed; this diagnostic helps identify and fix the case where the bundled binary is blocking it.

## Source Context

Discovered during cos-manager session 2026-08-01 while debugging why automated launchd tasks using `claude -p` were producing no output and no errors. Verified on Mac Mini M4, macOS 15. Initial `which claude` pointed to `/opt/homebrew/lib/node_modules/happy-coder/node_modules/@anthropic-ai/claude-agent-sdk-darwin-arm64/claude` (v2.1.141). The `-p` flag is simply not recognized by that binary — it silently exits without complaining. After installing `@anthropic-ai/claude-code` globally, `which claude` resolved correctly and `-p` mode worked as expected. The silent failure is the key diagnostic insight: there is no error to investigate, only absence of output, which initially suggested a different class of problem (authentication, script logic, environment) before the binary mismatch was discovered.
