---
title: Bead-as-context-anchor — convert in-session deferrals into persistent runbooks before session end
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.7
staleness_risk: stable
importance: 4
domain: architecture
topic: memory-systems
tags: tier-1, accretion, empirical, stable
related_entries: []
---

# Bead-as-context-anchor — convert in-session deferrals into persistent runbooks before session end

## Pattern

When work splits into "do now" and "do later under condition X", create a persistent bead (or equivalent issue) **immediately** with the full runbook + trigger condition. Do not rely on session-local task lists or working memory to remember the deferred half. The bead is the context anchor — it survives session end, context compaction, machine restart, and weeks of intervening work.

## The Structure That Works

| Field | Content |
|-------|---------|
| **Title** | Verb-first imperative naming the deferred action ("Upload cos-mcp 0.2.0 to PyPI") |
| **Description** | Why this is deferred + what the trigger condition is (e.g. "wait until dogfood-verified") |
| **Acceptance criteria** | Exact commands to run when the trigger fires. Verbatim. Copy-pasteable. |
| **Context** | What was already done leading up to the deferral (commit hashes, env state, dependencies) |
| **Labels** | At minimum: `follow-up`, plus topical labels (`pypi`, `release`, etc.) |
| **Priority** | Match the trigger urgency. Most held actions are P3 (follow-up, not urgent). |

## Why This Beats Session-Local Tracking

1. **Task lists are ephemeral.** TaskCreate/TodoWrite track in-session state and don't survive context compaction or session end.

2. **Working memory is unreliable.** The agent will not remember a P3 follow-up across 3 weeks of sessions in other projects.

3. **The trigger condition lives with the action.** "When dogfood-verified, run X" is one atom of information. Splitting trigger and action across human memory + agent memory loses both halves.

4. **Beads are queryable.** `bd ready` surfaces the follow-up when the agent is back in the project. The right moment to revisit becomes a routine check, not a recall feat.

## When This Applies

- Multi-track work where one track ships now and another is held (e.g. "commit metadata, hold upload")
- "Prep but don't trigger" workflows (feature flags, scheduled releases, manual approval gates)
- Any deferred action with a non-trivial runbook (>3 commands)
- Cross-session continuity needs (the agent or user expects to revisit this later)

## When This Does NOT Apply

- Trivial follow-ups expressible in 1 sentence ("also run lint next time")
- Strictly in-session tracking (TaskCreate is fine for "during this conversation")
- Actions that are obviously single-use and won't be forgotten (just-shipped commits being verified within minutes)

## Counterexample / Failure Modes to Watch

**Don't over-bead.** Beads for everything = bead-list bloat, just like task-list bloat. The threshold: would this be lost without the bead? If no, skip.

**Don't write thin beads.** A bead with just a title ("publish package") is worse than no bead — it triggers later but provides no help executing. The acceptance criteria + context fields are the value.

**Don't bead in-session iterations.** If the deferral is "fix this in 5 minutes after lunch", use TaskCreate. Beads are for cross-session.

## Grounding From Session

User authorized "Both — A now, prep B as a follow-up commit (hold the upload)." The split:

- **Track A:** install + register cos-mcp locally (irreversible-but-low-stakes, do now)
- **Track B1:** commit metadata bump (URL fix + version 0.1.0→0.2.0, reversible, do now)
- **Track B2:** PyPI upload (visible, hard-to-reverse, hold until dogfood-verified)

After A and B1 completed, user directive: "Add the meta commit to a bead so we don't forget it."

**Result:** bead `cos-c10` created in `[project]/cos/.beads` with:
- Title: "Upload cos-mcp 0.2.0 to PyPI"
- Description: trigger condition (dogfood-verified), reference to commit 64db561
- Acceptance criteria: 4 exact commands (build, upload, verify, smoke-install)
- Context: prod state, ENV vars, commit hashes
- Labels: cos-mcp, release, pypi, follow-up
- Priority: P3

The bead now contains the full runbook. Future sessions don't need this conversation's context to execute the upload — the bead is self-sufficient.

## Cross-References

Tier 1 routing entries (Module 19) carry similar in-session persistence. Beads extend that to cross-session persistence by externalizing the state outside the conversation. The bead is the Tier 0 layer for deferred work.

Related file-based patterns (Module 15):
- File-based stub for deferred dispatch surfaces — addresses "what to do when external integration is deferred"
- File-based timer-poll pattern — addresses "how to track async acknowledgements without callback infrastructure"

Bead-as-anchor addresses the complementary problem: "how to persist a multi-part decision across session boundaries without losing the runbook."

## Source Context

Discovered during cos-mcp integration Phase 2/3 (prod-push session, 2026-05-18). Feature split into immediate installs + metadata commits vs. deferred PyPI upload pending dogfood verification. Rather than track the upload runbook in session-local working memory, the pattern emerged from externalizing the full acceptance criteria + trigger into a persistent bead. The bead survives session end and context resets; future revisits to the [project] project surface it via `bd ready`.
