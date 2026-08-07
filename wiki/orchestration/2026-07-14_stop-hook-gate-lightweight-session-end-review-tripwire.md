---
title: Stop Hook Gate — Lightweight Session-End Review Tripwire
source_mode: synthesizer
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-07-14
domain: orchestration
topic: agent-coordination
tags: claude-code, hooks, stop-hook, review-gate, session-lifecycle
related_entries: [architecture/hook-consequence-asymmetry.md, diagnostics/2026-05-23_live-smoke-as-verification-gate-mocks-pass-prod-breaks.md, patterns/2026-06-20_pre-commit-hook-three-piece-structure.md]
---

# Stop Hook Gate — Lightweight Session-End Review Tripwire

## Pattern Summary

A "stop hook gate" is architecturally distinct from an on-demand review command. It provides always-on (opt-in), lightweight review that triggers at session end rather than on explicit invocation. The key design insight is that the heavy on-demand review and the lightweight stop gate serve **different failure modes** and should have different properties.

## Design Space

| Property | On-demand review | Stop hook gate |
|---|---|---|
| Trigger | Explicit `/adversarial-review` | Every session end (if enabled) |
| Output format | Full JSON schema (verdict, findings[], confidence) | Binary: `ALLOW: reason` or `BLOCK: reason` |
| Scope | Full diff (configurable: working tree, branch) | Last Claude turn only |
| Failure mode caught | "This specific code change has a bug" | "Claude declared done and was wrong" |
| Cost | High (full review) | Low (targeted check) |

## Concrete Implementation

Reference: `duncanschouten/gemini-plugin-cc` — `plugins/gemini/hooks/hooks.json` registers `stop-review-gate-hook.mjs` on the `Stop` event with a 900s timeout.

### Hook registration

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "node scripts/stop-review-gate-hook.mjs",
        "timeout": 900
      }]
    }]
  }
}
```

### Gate logic (pseudocode)

1. Read `last_assistant_message` from hook input
2. Check `config.stopReviewGate` — if disabled, pass-through silently
3. Check reviewer availability/auth — if not ready, pass-through with warning (no hard block)
4. If `last_assistant_message` empty → pass-through (nothing to review)
5. Spawn external reviewer with the stop-gate prompt
6. Parse `ALLOW: <reason>` or `BLOCK: <reason>` from first line
7. If BLOCK → `emitDecision({ decision: "block", reason })` → session end blocked

### Gate prompt instructions

The stop-gate prompt instructs the reviewer to:
- Return ALLOW immediately if the previous turn didn't make code changes (status, setup, reporting turns are free)
- Verify from repo state that edits happened — **don't trust Claude's text as proof**
- Use BLOCK only if there's a substantive issue that still needs fixing before stopping
- Grounding rule: "Do not treat the previous Claude response as proof that code changes happened; verify that from the repository state before you block."

The grounding rule prevents false positives: a Claude turn that claims "I've updated X" but didn't actually modify X should only block after repo verification.

## When This Applies

- Any agentic workflow where an agent declares completion (polecat `gt done`, PR submission, deploy trigger)
- When you want a lightweight always-on review without the cost of a full adversarial review on every turn
- When the failure mode is specifically "agent incorrectly self-assessed completion"
- Opt-in via a config flag (not on by default) — appropriate given the added friction

## When This Does NOT Apply

- When cost is no concern and you want full review on every turn
- When the insertion point should be pre-turn (PreToolUse hook) rather than session-end
- When the workflow has its own completion verification (e.g., Refinery does its own diff review before merging)
- When the reviewer availability is unpredictable (the hook should gracefully degrade to pass-through)

## Distinction from Related Patterns

**vs. Hook Consequence Asymmetry:** The stop-hook-gate is a specific application of the asymmetry principle. It's a *productivity hook* (opt-in, lightweight, exit 0 on indecision) that fires on a security-adjacent failure mode (agent didn't actually complete work). The hook must be fast enough not to frustrate session-end UX — typically <2 seconds for the gate decision.

**vs. Live-smoke verification gate:** Live-smoke verifies integrations work before *deployment*. Stop-hook-gate verifies the agent's self-assessment before *session completion*. Both are pre-transition gates, but they guard different boundaries and operate on different timescales.

**vs. Pre-commit hooks:** Pre-commit hooks fire on every commit attempt. Stop-hook-gate fires once at session end (or on explicit completion command). Pre-commit hooks can afford more friction (developers expect git operations to validate); stop gates must stay out of the way (developers expect sessions to end smoothly).

## Implementation Notes for Claude Code Hooks

The hook receives `last_assistant_message` in stdin JSON. It should:
- Emit `emitDecision({ decision: "block", reason })` on stdout to block the session end
- No output (or non-`decision` output) on stdout = pass-through
- Return exit code 0 on successful gate logic (pass or block decision made)
- Timeout behavior: if the reviewer takes >900s, the session end proceeds anyway (graceful degradation)

## Application to Agentic Workflows: Polecat Contract

The polecat `gt done` command is a natural insertion point for a similar gate: before `gt done` fires, verify the assigned bead is actually in a closeable state (not still in-progress, not missing required test runs). This catches exactly the "agent declared done but wasn't" failure mode.

Polecat contract adaptation:

```bash
# Before gt done, run a lightweight completion check
bd show <issue-id> | jq -r '.status'  # must be "in_progress", not "open"
# Check test harness state (project-specific)
# If any check fails: return non-zero exit, block the session end
# If all pass: return 0, allow gt done to proceed
```

## Verification

After enabling the stop-hook-gate on a Claude Code plugin:

1. Test it with a session that correctly completes work → gate should return ALLOW
2. Test it with a session where Claude claims completion but didn't commit → gate should return BLOCK
3. Test it with a session that's just status reporting → gate should return ALLOW (no friction on non-work turns)
4. Verify the gate exits within 30s for normal sessions (no >900s timeouts breaking UX)

## Source Context

Learned during deep-dive into `duncanschouten/gemini-plugin-cc` plugin architecture (2026-07-13). The stop-hook-gate is a mature pattern within the Gemini plugin ecosystem for agent self-assessment verification. The pattern generalizes to any Claude Code hook system: lightweight gates that fire at high-friction points (session end, completion declaration) need to be fast, gracefully degrade on unavailability, and focus on a single verifiable claim ("did the agent actually do what it said?") rather than full-diff review. The grounding rule (verify from repo state, not from Claude's claims) prevents the gate from blocking legitimate sessions due to false claims in Claude's narration.
