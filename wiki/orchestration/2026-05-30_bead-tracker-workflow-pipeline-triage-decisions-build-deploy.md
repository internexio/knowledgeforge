---
title: Bead-tracker workflow pipeline (triage → decisions → build → deploy)
source_mode: kf-coordinator + kf-builder
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: slow_decay
importance: 5
pinned: false
created: 2026-05-30
tags: orchestration, beads, bd-cli, parallel-agents, workflow-pipeline, autonomous-throughput
domain: orchestration
topic: multi-stage-issue-workflow
related_entries:
  - wiki/orchestration/2026-05-30_dry-run-first-validation-mutation-bearing-orchestration-skills.md
  - wiki/infrastructure/2026-05-27_bd-cli-dependency-wiring-inversion-two-pass-pattern.md
  - wiki/architecture/2026-05-18_bead-as-context-anchor-deferred-runbooks.md
  - wiki/methodologies/2026-05-27_supervise-first-real-data-run-autonomous-loops.md
  - wiki/patterns/2026-05-18_composite-vs-atomic-mcp-tool-design.md
---

# Bead-tracker workflow pipeline (triage → decisions → build → deploy)

A 4-stage pipeline that takes a batch of open `bd` (beads) issue-tracker items from raw backlog to shipped code, with exactly TWO human checkpoints. Built and validated 2026-05-30 in [project].

## The 4 stages

```
Stage 1: PARALLEL TRIAGE  (autonomous, ~1 orchestrator call)
  Input:  N open beads
  Work:   ⌈N/8⌉ general-purpose agents verify each bead vs codebase in parallel
  Output: per-bead classification with file:line evidence
            ├── SHIPPED       → auto-close with evidence-based reason
            ├── NEEDS-SPEC    → auto-draft proposal markdown
            ├── NEEDS-DECISION → queue worksheet
            └── READY-TO-BUILD → queue build

Stage 2: DECISION WORKSHEET  (one human pass)
  All NEEDS-DECISION items presented via AskUserQuestion in one focused session.
  User picks options; decisions recorded on beads; items move to build queue.

Stage 3: PARALLEL BUILD  (autonomous + final auth)
  Per READY-TO-BUILD bead, classify build complexity (SIMPLE/ISOLATED/INTERLEAVING).
  ISOLATED → spawn Agent with isolation: "worktree", agent commits on branch.
  SIMPLE → in-place edits.
  INTERLEAVING → serialize after parallel batch.
  Merge branches into master locally; run full test suite.

Stage 4: BATCHED DEPLOY  (one user authorization)
  origin/test → verify → ask before prod → push prod → close all bundled beads.
```

## Why it works on the friction points

- **Premise drift** (beads describing already-shipped work): parallel triage finds them and auto-closes with evidence. In one session at [project], this found 6 stale beads in 30, ~3 hours saved.
- **Decision serialization** (every multi-option bead pauses for human input): worksheet pattern batches all decisions into one pass — typically ~5 min/decision instead of 15–30 min/bead.
- **CI cost** (~13-min CI cycle per push): batched deploy ships N beads in one cycle instead of N cycles.
- **Browser-verify gap** (frontend beads need eyes-on): the pipeline explicitly does NOT route browser-only beads autonomously; they get queued for human pickup.

## Implementation

Four Claude Code skills installed at `~/.claude/skills/`:
- `/bead-triage` — Phase 1 (parallel-agent verification + classification).
- `/bead-decisions` — Phase 2 (worksheet via AskUserQuestion).
- `/bead-build` — Phase 3 (worktree-parallel builds + batched deploy).
- `/bead-pipeline` — umbrella chaining all three.

Plus two agent-prompt templates (triage-prompt.md, builder-prompt.md) that the skills fill in and pass to general-purpose agents.

State lives in `<project-root>/.bead-workflow/` (worksheet.md, build-queue.md, last-triage-*.md). Project root resolved by walking up from cwd looking for `.beads/` — handles [project]'s case where `.beads` is at a non-git-repo level with a symlink from the inner git repo.

## Key design decisions

1. **Project-local state.** State files go in the project, not in `~/.claude/state/`. Survives across machines via the project repo. Walk-up resolution handles multi-repo umbrella projects.
2. **Native bd dependency integration.** When a triage agent surfaces a dep (`**Depends on:** <id>`), the skill runs `bd dep add <bead> <dep>` so bd's native ready/blocked machinery enforces the ordering. The skill doesn't reimplement deps.
3. **Dry-run mode at every mutating stage.** `--dry-run` classifies + reports without mutating. Was the validation tool that surfaced the dep-tracking gap in v1 (the v2 enhancement closed it).
4. **Cap parallel agents at 4** to avoid runaway resource use; cap per-agent bead count at ~8 for tight reports.
5. **Worktree isolation for builds** uses the Agent tool's native `isolation: "worktree"`; the orchestrator merges branches locally before any push.
6. **Two human checkpoints only.** Decisions worksheet + final deploy authorization. Everything else is autonomous.

## When to use

- ≥10 open beads accumulated from prior sessions.
- After time away — to reconcile what's still open vs already done.
- End-of-week / end-of-sprint sweep.

## When NOT to use

- Beads requiring browser-only frontend verify (pipeline can't see them; skip).
- Sensitive DB migrations or auth/billing changes (use individual careful review).
- Beads with "to-review" labels (need spec first; triage's NEEDS-SPEC bucket catches them but the spec is autonomous-drafted, may want human review before build).
- Backlogs with <5 open beads (pipeline overhead exceeds benefit).

## Grounding (concrete uses this session)

- 30-bead reconciliation sweep (Stage 1 standalone): found 6 stale + 2 re-scoped, ~3 hours saved.
- cos-moh BC/EC parity semantic scan (Stage 1 single-agent): found 3 HIGH-severity drift candidates + filed 2 refactor beads.
- /bead-triage --dry-run on 3 beads (full Stage 1 validation): correctly classified 1 NEEDS-SPEC + 2 READY-TO-BUILD; surfaced an unstated dep (cos-372 → cos-12g) which prompted the v2 enhancement.
- Stage 3/4 not yet exercised end-to-end (built but not run); designed off the patterns of the per-bead deploy cycles this session validated repeatedly.

## Anti-patterns / failure modes

- Running pipeline without dry-run first when the skill is new → state mutations against an unvalidated classification. Mitigated by mandatory dry-run for new skills (separate accretion).
- Putting state in `~/.claude/state/`: tempting (global) but loses survivability when the project moves machines. Project-local won.
- Asking the user for permission per-bead: was the failure mode of pre-pipeline ad-hoc work — 13-min CI × N beads + per-bead decision turnaround. Solved by batching.

## Source Context

Built 2026-05-30 in [project] overnight pipeline-build session. Integrated with existing dry-run-first validation methodology (same day's entry `2026-05-30_dry-run-first-validation-mutation-bearing-orchestration-skills.md`). The framework covers 4 stages: parallel triage + single worksheet decision pass + parallel builds with worktree isolation + batched deploy. Two human checkpoints only (decisions + final auth). State management via project-local files, native bd dep integration, and explicit handling for browser-verify beads. Validated dry-run against real [project] beads (cos-12g, cos-372, cos-sxk) surfaced a dependency-tracking gap (v1 → v2 enhancement). Partial grounding: Stage 1 proven on 30-bead reconciliation; Stages 3/4 designed off prior per-bead patterns but not yet exercised end-to-end.
