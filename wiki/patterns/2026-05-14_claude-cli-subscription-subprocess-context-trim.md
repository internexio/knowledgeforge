---
title: Claude CLI Subscription Subprocess Context Trim — cwd + --setting-sources
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.92
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-14
tags: claude-cli,subprocess,context-bloat,cost-optimization,subscription-auth,cache-tokens
related_entries: [infrastructure/2026-05-14_claude-cli-bare-disables-oauth-keychain-auth.md]
domain: patterns
topic: retrieval
---

# Claude CLI Subscription Subprocess Context Trim

When `claude --print` (or other Claude CLI calls) runs via subscription authentication (OAuth/keychain), the CLI auto-discovers and hydrates two sources of context that may inflate token counts unnecessarily for focused single-shot calls:

1. **User-level settings** — `~/.claude/settings.json` (MCP servers, hooks, plugins, global configuration)
2. **Project-level settings** — Nearest `CLAUDE.md` in the current working directory parent walk

For a targeted Critic/Strategist/Calibrator subprocess probe against an agent definition, prompt, and schema, this user and project context is **irrelevant**. It still gets serialized and included in the request, inflating cache-creation tokens significantly.

## Symptom

- Subprocess KF stage calls timeout unexpectedly or run at high cost ($0.20–0.30 per trivial probe)
- Cache-creation tokens dominate the cost breakdown
- Calls succeed eventually but consume excessive budget and wall-clock time

## Solution: Two-pronged Trim

**1. Skip user settings with `--setting-sources local`**

Disable discovery and hydration of `~/.claude/settings.json`. Local-only settings from environment or config still load normally.

```bash
claude --print --setting-sources local "your prompt here"
```

**2. Escape project settings discovery with `cwd="/tmp"`**

Run the subprocess with `cwd="/tmp"` to place execution outside any project tree. The CLI's parent-walk for `CLAUDE.md` will hit `/tmp` (no `.md` file) and stop, avoiding project context hydration.

```python
import subprocess

result = subprocess.run(
    ["claude", "--print", "--setting-sources", "local", "prompt"],
    cwd="/tmp",
    capture_output=True,
    text=True
)
```

**Combined pattern (both trims):**

```python
subprocess.run(
    ["claude", "--print", "--setting-sources", "local", prompt_or_file],
    cwd="/tmp",
    capture_output=True,
    text=True,
    env={...}  # pass explicit env, or inherit
)
```

## Measured Impact

**Before trim** (2026-05-14, KF Critic probe):
- Cost: $0.27
- Cache-creation tokens: 41,000

**After trim** (same probe, both trims applied):
- Cost: $0.06
- Cache-creation tokens: 8,000

**Result:** 77% cost reduction, 80% cache-token reduction.

## Critical Constraint: Do NOT Use `--bare`

**WRONG:**
```bash
claude --print --bare "prompt"  # Disables OAuth/keychain entirely
```

`--bare` disables subscription authentication entirely and requires `ANTHROPIC_API_KEY` env var for API-key billing. This shifts cost tracking and breaks subscription-backed workflows.

**RIGHT:** Use the cwd + `--setting-sources local` pattern above. It achieves the same context cleanup while preserving subscription authentication and billing.

## Applicability

- **When to use:** Subprocess calls from orchestration layers, KF stage runners, batch probe workflows where context-trimming won't break the call
- **When NOT to use:** Interactive CLI calls where user settings (hooks, MCP servers, plugins) are expected; calls that need project-specific CLAUDE.md configuration
- **Auth preservation:** Works with both OAuth/subscription and `ANTHROPIC_API_KEY` billing; does not require either specifically

## Code Reference

- **Discovered:** 2026-05-14 during [project]-msey diagnosis (Critic timeouts under load)
- **Implementation:** `~/Scripts/[project]/iteration_loop/kf_chain.py`, lines 54–91 (subprocess invocation) + lines 155–165 (setting-sources flag construction)
- **Commit:** `d9d85f1` ("perf: kf_chain — slash subscription-auth context bloat 77%")

## When This Does NOT Apply

- Interactive `claude` CLI sessions where MCP servers or project hooks are needed
- Calls that rely on `CLAUDE.md` project instructions (agent definitions, skill routing, etc.)
- One-off commands where the 40k-token overhead is acceptable
