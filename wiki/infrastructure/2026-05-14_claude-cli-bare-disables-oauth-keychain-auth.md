---
title: Claude CLI --bare disables OAuth/keychain — subscription-billed subprocess workers must omit it
source_mode: builder
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-05-14
domain: infrastructure
topic: ops
tags: claude-cli, anthropic-auth, subprocess-workers, oauth, subscription-billing, kf-chain
related_entries:
  - infrastructure/2026-05-14_self-identity-minting-cli-flag-cron-workers.md
  - infrastructure/2026-05-13_launchd-cwd-trap-relative-tool-lookups.md
  - infrastructure/2026-05-11_python-package-cli-under-cron.md
---

# Claude CLI `--bare` Disables OAuth/Keychain Auth

## The Problem

When invoking `claude --print` from a subprocess worker (cron-driven KF chain stage, headless audit, daemon background task), the `--bare` flag is tempting for performance: it skips hooks, MCP, plugin sync, CLAUDE.md auto-discovery, and keychain reads. The reduction is real — approximately 2-4 seconds of subprocess startup overhead avoided.

However, `--bare` mode's auth contract is strict and non-obvious:

> "Anthropic auth is strictly `ANTHROPIC_API_KEY` or apiKeyHelper via `--settings`. OAuth and keychain are never read in bare mode."

If your worker is intended to be billed against a Claude subscription (OAuth auth via keychain entry created by `claude login`), passing `--bare` **silently switches auth to env-var-required mode**. Without `ANTHROPIC_API_KEY` exported to the subprocess environment, the call returns:

```json
{"is_error": true, "result": "Not logged in · Please run /login"}
```

This surfaces as a subprocess failure but is actually an auth-model mismatch: the CLI did exactly what it was asked (check only env var + apiKeyHelper), found neither, and reported the expected error. The worker's caller sees a command failure, not a missing-key error.

## When This Applies

- You're building a subprocess wrapper around `claude --print` that runs unattended (cron, launchd, daemon, Kubernetes cronjob)
- You want subscription billing (one consolidated bucket on the user's Claude subscription plan), not per-stage API-key attribution
- You're seeing `"Not logged in"` errors despite the user being logged in interactively
- The worker uses `--bare` to optimize startup latency

## When This Does NOT Apply

- You explicitly want a dedicated API key per worker for dashboard attribution and cost tracking — then `--bare` + `ANTHROPIC_API_KEY` is the right path
- You're calling `claude` from within a parent Claude Code session (the Agent tool uses a different auth surface — this whole discussion is about subprocess invocation only)
- You're running on a third-party provider (Bedrock, Vertex, Foundry) — those have their own credential flows unaffected by `--bare`
- Your worker is short-lived and auth overhead is acceptable (< 1 second for a 10+ second LLM call amortizes the cost)

## The Fix

Two paths, with opt-in cutover:

### Path A: Default (Subscription Billing)

Omit `--bare` entirely. Pass `--no-session-persistence` (workers are one-shot, no session state needed) and `--output-format json`. The CLI reads the OAuth keychain entry the same way an interactive session does:

```bash
# In launchd plist or cron entry
claude --print \
  --no-session-persistence \
  --output-format json \
  -p "..." \
  --max-budget-usd 0.05 \
  --json-schema '{"type":"object",...}'
```

The worker environment inherits the user's keychain (on macOS, via login context). No extra configuration needed. Auth happens transparently.

### Path B: Cutover (Dedicated API Key)

Mint a dedicated API key via the Anthropic Console. Export `ANTHROPIC_API_KEY` into the worker environment (launchd `EnvironmentVariables` block — this does NOT inherit `~/.zshrc`), and pass `--bare`:

```bash
# In launchd plist EnvironmentVariables or in a wrapper script
export ANTHROPIC_API_KEY="sk_..."
claude --print --bare \
  --output-format json \
  -p "..." \
  --max-budget-usd 0.05 \
  --json-schema '{"type":"object",...}'
```

Billing appears per-key on the Anthropic dashboard, not consolidated to the user's subscription. Treat this as an **explicit opt-in** decision (via an `extra_args=["--bare"]` parameter), not as the default startup optimization.

### Launchd EnvironmentVariables Example

```xml
<key>EnvironmentVariables</key>
<dict>
  <key>ANTHROPIC_API_KEY</key>
  <string>sk_your_dedicated_key_here</string>
</dict>
```

Launchd does NOT source `~/.zshrc` or inherit the shell environment — the plist must list all env vars explicitly.

## Trade-Off Analysis

| Aspect | Path A (no --bare) | Path B (--bare + key) |
|---|---|---|
| Startup latency | +2-4 sec/call (hooks, MCP, plugin sync) | ~0.5 sec (minimal) |
| Auth source | OAuth keychain entry | Env var only |
| Billing model | Subscription bucket (consolidated) | Per-key dashboard line |
| Launchd setup | Inherits user keychain (no extra config) | Requires explicit EnvironmentVariables block + key rotation plan |
| Reverts | None — just drop the flag | None — remove env var, key still live in Anthropic Console |
| Applicable scenarios | Most unattended workers | High-frequency workers where 2-4 sec/call is unacceptable |

For v0 concurrency=1 with 10-30 seconds of LLM work per stage, subscription mode (Path A) amortizes startup latency acceptably. The 2-4 sec overhead is ~10-20% of the total stage time. Revisit for Path B if subprocess overhead becomes a measurable bottleneck at v1+ with concurrent workers or sub-second stage targets.

## Concrete Grounding

- **Verified live on 2026-05-14:**
  ```bash
  claude --print --bare --output-format json -p '...' \
    --max-budget-usd 0.05 --json-schema '{"type":"object",...}'
  ```
  Returned `"is_error":true, "result":"Not logged in"` despite interactive sessions working fine. The keychain entry was not consulted in bare mode.

- **After removing `--bare` from argv:** Same command succeeded, processing against the subscription-billed OAuth token.

- **Implementation reference:** `kf_chain_invocation_spec.md` § 2.3 and `docs/iteration-loop/api-key-setup.md` document the cutover decision and launchd EnvironmentVariables configuration.

- **Related shipping:** KnowledgeForge iteration-loop v0 ([project] 51cb843, 2026-05-14) uses Path A (no `--bare`) for all `claude --print` invocations in KF chain stages.

## Source Context

Extracted from [project] iteration-loop v0 implementation debugging (2026-05-14). Initial KF chain invocation spec used `--bare` as a performance optimization. Testing revealed the auth-model mismatch: interactive sessions use OAuth keychain, but subprocess workers with `--bare` silently require `ANTHROPIC_API_KEY`. This is not a bug in the Claude CLI — the behavior is documented in `--help` — but the silent switch from "logged in interactively" to "env var only" is a footgun for unattended workers. Documented in commit history and flagged as MUST-address in the iteration-loop v0 spec review. This is a reusable diagnostic: anyone running `claude --print` in a subprocess and seeing `"Not logged in"` should check (a) whether they passed `--bare`, and (b) whether the environment has `ANTHROPIC_API_KEY` or the worker inherits keychain access.
