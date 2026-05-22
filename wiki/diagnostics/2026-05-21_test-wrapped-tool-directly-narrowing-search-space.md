---
title: Test the wrapped tool directly — narrowing pattern for wrapper bugs
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-21
domain: diagnostics
topic: root-cause-analysis
tags: diagnostics, debugging, wrappers, orchestrators, layered-systems
related_entries:
  - diagnostics/2026-05-19_cos-mcp-analyze-full-timeout-direct-curl-fallback.md
revises: null
superseded_by: null
---

# Test the Wrapped Tool Directly — Narrowing Pattern for Wrapper Bugs

## Pattern

When a wrapper or orchestrator fails (CLI shim, IDE plugin, agent framework, daemon supervisor), the bug is almost always in either (a) the wrapped tool, (b) the wrapper itself, or (c) the integration between them. Confirming (a) is healthy is the cheapest test in the diagnostic flow and instantly narrows the search space by ~2/3.

## When this applies

You're debugging anything where Layer A invokes Layer B, and Layer A is failing:
- CLI wrapper (Happy → Claude, codex → openai, gh → git)
- Orchestrator (LangGraph/CrewAI agent → LLM API)
- Daemon supervisor (systemd → app, launchd → script)
- Build wrapper (Bazel → compiler)
- IDE extension → language server

If the wrapper symptoms are vague ("it hangs", "wrong output", "auth fails"), invoke Layer B directly with the simplest possible request before going deeper into the wrapper.

## The test

The minimal test is whatever proves Layer B can handle a trivial request standalone, in the same working directory and environment Layer A would have set up. Examples:

- Happy wraps Claude → `claude --print "Reply with exactly 'pong'"` in the same workdir
- Codex wraps OpenAI → `curl -X POST https://api.openai.com/v1/chat/completions ...` with the same API key from env
- gh wraps git → `git log -1` in the same repo
- Agent framework wraps LLM → call the LLM provider's SDK directly with the same model + a one-shot prompt

If Layer B returns expected output, the bug is in the wrapper or the integration. If Layer B fails, the bug is in Layer B (or its config/auth/env, which the wrapper would have inherited).

## Cost of the test

Seconds. The simplest invocation of any well-designed Layer B is cheap to run. This is the highest-information-per-second diagnostic step available in any layered-system bug — do it first, not after exhausting wrapper-side hypotheses.

## Concrete grounding (2026-05-21, happy-coder + Claude Code)

Happy CLI was throwing "Error during execution / Completed 0 turns before error" on every prompt for one specific workdir (`client-project`). We'd already tried: kill+respawn, mode switch, reinstall, version upgrade — nothing helped.

Then ran `cd ~/Scripts/client-project && claude --print "Reply with exactly 'pong'"`. Returned `pong` cleanly. That single 2-second invocation eliminated Claude SDK, Claude auth, the working directory's config, and Claude's session store as suspects — leaving Happy itself or its backend as the only place the bug could live. Two hours of triage already-done had been thrashing in the wrong half of the search space.

If we'd run the direct-invocation test first, we'd have skipped: the local-mode switch attempt, the reinstall attempt, the v1.1.9 upgrade detour. The bug was always going to be in the wrapper or its server.

## When this does NOT apply

- Layer B is **the** thing that's broken in a way that's obvious from Layer A's error (e.g. "401 Unauthorized" from the LLM provider) → no narrowing needed.
- Layer B has no standalone invocation mode → some libraries can only run inside their framework.
- The integration layer is itself the thing under test (e.g. you're explicitly debugging the MCP server's translation logic) → bypassing it defeats the test.

## Anti-pattern

Spending more than 30 minutes assuming the bug is in Layer A without ever invoking Layer B directly. The cost-information ratio of the direct test is so favorable that skipping it is almost always a mistake.

## Related patterns

This is the cheap-narrowing analogue of the "encrypted server-side state can outlive every client-side fix" pattern. The direct-invocation test is what tells you "the bug is in the wrapper, not the wrapped tool"; the server-side-state pattern is what tells you "now check the wrapper's backend, not the wrapper's local files."

The COS MCP → curl fallback diagnostic is a concrete instance of this pattern: when MCP timeouts are vague, bypass the MCP transport layer entirely and test the backend API directly. Same principle, same 2/3 search-space narrowing.

## Source Context

Extracted from Happy CLI debugging session on 2026-05-21 (client-project resume-loop investigation). Two hours of wrapper-side hypotheses and fixes (reinstall, version update, mode switch) had been exhausted before testing `claude --print` directly in the same workdir. The direct test narrowed the root cause to Happy's backend in seconds. This diagnostic is highly reusable for any developer maintaining wrapper/shim/orchestrator layers; the principle generalizes across CLI wrappers, MCP servers, daemon supervisors, and agent frameworks. Grounding score reflects the concrete Happy CLI case and applicability to similar layered systems.
