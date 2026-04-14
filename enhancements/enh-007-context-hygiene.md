# ENH-007: Context Hygiene Audit in Calibrator
**Mode:** Calibrator
**Priority:** P3
**Effort:** Low — checklist addition to Calibrator setup flow
**Status:** Proposed

## Problem

Calibrator configures AI coder setup: CLAUDE.md, guardrails, stack decisions, project
conventions. It optimizes what goes *in* — but doesn't audit what *shouldn't* be there.

Nate's formulation: "How do you make sure that there isn't dirty and polluting data that
confuses the AI agent in your context available to be searched?"

KF's four-tier memory and taxonomy enforcement prevent tag fragmentation and manage retrieval.
But Calibrator — which sets up the context environment a project runs in — doesn't explicitly
ask: what's in this context that will degrade agent performance over time?

"Dirty context" in practice:
- Outdated CLAUDE.md rules that contradict current behavior
- Stale memory entries that describe a past system state as current
- Conflicting instructions from multiple CLAUDE.md files (global vs. project)
- Dead skill references (skills that no longer exist or have changed)
- Wiki entries with low grounding scores that get surfaced as facts
- Verbose context that crowds out relevant signals (context utilization > 80%)

Without a hygiene audit, context degrades silently. Quality drops, agents start making
decisions based on stale data, and the failure looks like model quality regression — not
a context problem.

## Proposed Fix

Add a **Context Hygiene Audit** as a named step in Calibrator's setup and periodic review.

### When It Fires

1. **New project setup** — Calibrator is configuring a new project's CLAUDE.md
2. **Explicit request** — "review my context setup", "audit my CLAUDE.md", "context hygiene"
3. **Performance degradation signal** — user reports "the agent keeps making the same mistake"
   or "it keeps using the wrong pattern" (Debugger may route to Calibrator for this)

### Audit Checklist

**1. Instruction Conflict Scan**
- Are there CLAUDE.md files at multiple levels (global `~/.claude/CLAUDE.md` + project)?
- Do any rules in project CLAUDE.md contradict global rules?
- Are any rules duplicated (same instruction in two places = noise)?
- Surface conflicts: [rule A in global] vs. [rule B in project] — which wins?

**2. Staleness Check**
- Are any rules dated or referencing past system states? ("we use X" — do we still?)
- Are any skill references valid? (skill names, paths, commands)
- Are any server/URL references current? (endpoints, hostnames)
- Flag candidates: rules that haven't been touched in 30+ days on an active project

**3. Verbosity Assessment**
- Estimate context load from CLAUDE.md at session start
- Flag if > 4k tokens (high load, crowds signal)
- Identify candidates for compression: verbose explanations that could be one line

**4. Wiki Hygiene**
- Any entries with grounding score < 0.6 being surfaced as high-confidence?
- Any entries where the topic has been superseded by newer work?
- Entries that are duplicates or near-duplicates of each other?

**5. Memory Decay Check**
- Any Tier 3 history entries being treated as current fact?
- Any remembered patterns that the user has since explicitly changed?

### Output Format

```
Context Hygiene Audit

Instruction Conflicts: [N found / none]
  • [conflict description + resolution recommendation]

Stale Rules: [N candidates]
  • [rule text] — last relevant: [when] — recommendation: archive / update / keep

Verbosity: [LOW / MEDIUM / HIGH] ([estimated tokens])
  • High-verbosity candidates: [sections to compress]

Wiki Hygiene: [N issues / clean]
  • [entry] — [issue] — recommendation: [update / archive / flag for review]

Memory: [N stale entries / clean]
  • [entry] — [staleness signal]

Recommended actions: [ordered list]
```

## Acceptance Criteria
- Hygiene audit runs as part of new project Calibrator setup
- Audit covers all 5 checklist dimensions
- Output is structured and actionable (not a wall of observations)
- Recommendations are ordered by impact — most important first
- Does not auto-modify any files — surfaces findings only, user decides

## Anti-Patterns
- Auto-deleting stale entries — surface only, never delete without user confirmation
- Running hygiene audit on every session (expensive, noisy) — only on setup / explicit request / degradation signal
- Flagging everything as stale — use judgment; a rule that's still accurate isn't stale just because it's old
- Conflating "verbose" with "wrong" — some verbose rules exist for good reasons; flag, don't auto-compress
