---
title: KF-MODE telemetry marker must land in first 20 lines of compiled agent files
source_mode: debugger
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: stable
importance: 3
created: 2026-07-11
domain: compiler
topic: bootstrap-divergence
tags: [quality-gate, empirical, packaging, delegation]
related_entries:
  - compiler/2026-07-06_claude-code-agent-loader-line-1-frontmatter-option-d-source-trace.md
  - diagnostics/2026-06-14_worktree-isolated-subagent-cannot-spawn-other-subagents.md
  - methodologies/2026-06-10_kf-semver-three-surfaces-module-system-binding.md
pinned: false
---

# KF-MODE Telemetry Marker Must Land in First 20 Lines of Compiled Agent Files

## Problem

The KF-MODE telemetry marker directive lives in `~/.claude/rules/kf-meta.md` — a rules file that auto-loads in regular Claude Code sessions. When the `kf` agent (or any compiled agent) is invoked as a **sub-agent**, rules files are NOT inherited into the sub-agent's context. The compiled agent file itself carries zero mention of the telemetry marker, so per-turn observability is silently dropped during agentic/tool-calling loops.

This was the root cause of ~20% per-turn marker coverage loss observed in τ²-bench Phase-1 tool-calling probes (verified 2026-07-11, bead kf-vo1).

## Root Cause

Rules file inheritance works in primary orchestrator sessions (rules auto-load at session startup). In sub-agent contexts:

1. The `Agent` tool spawns the compiled agent file (e.g., `~/.claude/agents/kf.md`)
2. Rules files are NOT loaded into the sub-agent's context — only the agent file itself is available
3. The compiled agent file lacks the telemetry marker directive (it exists only in `~/.claude/rules/kf-meta.md`)
4. The sub-agent's first turn has no knowledge of the telemetry requirement
5. All per-turn markers are omitted → coverage gap in observability pipeline

## Fix Pattern

Embed a hard-enforcement blockquote at the top of the compiled agent file — **after YAML frontmatter and compile-attribution comment, before any section TOC or substantive content.** Target: **line 8 or earlier** (well within the first 20 lines).

**Enforcement block format:**

```markdown
> **TELEMETRY REQUIRED — every turn, no exceptions:** Emit `<!-- KF-MODE: <mode> | DECISION: <class> -->` as the **last line** of every text-bearing turn. Tool-only turns accumulate marker debt — prepend one deferred marker per missed turn as the **first line** of the next text turn, then append the current turn's marker at the end.
```

This blockquote is:
- Visually prominent (rendered as callout in standard markdown viewers)
- Self-contained (no cross-reference needed — the rule is complete in the block)
- Placed high enough that it cannot be missed during context-window loading
- Phrased with "REQUIRED" and "no exceptions" to override any competing priorities

## Why First 20 Lines Specifically

Claude Code's agent loader reads the full file, but the model's attention on behavioral directives degrades as file length increases. Placing the enforcement at line 8 ensures it appears **before any routing tables, mode descriptions, chaining logic, or reference indexes** — all of which expand context length before alternative placements would appear.

**Layout typically:**
- Lines 1–2: YAML frontmatter opening
- Lines 3–6: YAML fields (name, description, tools, etc.)
- Line 7: YAML frontmatter closing `---`
- Line 8: **ENFORCEMENT BLOCK (this rule)**
- Lines 9+: Sections, TOC, content

## Verification Criteria

After applying the fix:

1. `grep -n "KF-MODE\|TELEMETRY" ~/.claude/agents/<mode>.md` returns a hit at line ≤ 20
2. The blockquote text includes both "REQUIRED" and "no exceptions" to assert priority
3. The blockquote mentions both single-line-at-end (normal) and prepend-deferred-debt (tool-only) patterns
4. Sub-agent invocations of the mode produce 100% per-turn marker coverage (tau²-bench re-run as validation)

## Grounding

- **Empirical discovery:** τ²-bench Phase-1 tool-calling probes against kf-cc (2026-07-11, kf-vo1) showed ~80–100% marker coverage in primary session, ~60–70% in sub-agent calls
- **Root-cause validation:** Verified that kf-cc `~/.claude/agents/kf.md` had zero telemetry directive; `~/.claude/rules/kf-meta.md` carried the directive
- **Fix applied:** Commit 44eb04c (kf-cc, 2026-07-11) adds the blockquote at line 8 of all compiled agent files
- **Post-fix result:** τ²-bench Phase-1 re-run pending (targeted for 2026-07-12); Orchestra handoff art_3f2540a4 to mini-claude requesting verification

## When This Applies

- Any compiled agent file (`.md` file under `~/.claude/agents/`) that relies on behavioral directives to fire in sub-agent contexts
- Directives that only matter in primary session context can stay in rules files
- Applies to all KF modes (builder, critic, expert, synthesizer, etc.)
- Applies to any non-KF agent that embeds observability or telemetry requirements

## When This Does NOT Apply

- Rules files are fine for directives that only fire in primary orchestrator sessions
- If an agent is never invoked as a sub-agent, rules inheritance works and the rule is moot
- Skills (`~/.claude/skills/kf/*.md`) — different loader, different inheritance model
- Docs and reference files — no behavioral expectations

## Implementation Notes

The blockquote placement is a compile-time responsibility. Build systems generating agent files should:

1. Write the YAML frontmatter and closing `---`
2. Write the blockquote with the telemetry directive before any other body content
3. Increment line-numbering tracking if any prior lines were added
4. Verify line ≤ 20 in the output before shipping the compiled artifact

## Related Entry

See `diagnostics/2026-06-14_worktree-isolated-subagent-cannot-spawn-other-subagents.md` for patterns when sub-agents cannot access sibling agents (e.g., adversarial-critic). Telemetry inheritance and agent spawning are distinct constraints; this rule addresses telemetry only.

## Source Context

Filed from bead kf-vo1 (P2 fix). Root cause: rules files do not inherit to sub-agents, compiled agent files need embedded directives. Fix lands in kf-cc commit 44eb04c; Aurora validation pending (tau²-bench Phase-1 re-run, 2026-07-12).
