---
title: Probe-before-chain — verify handoff brief inputs before running multi-mode chains
source_mode: direct
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-24
tags: orchestration, reconciliation, handoff, kf-chain, methodology, probe
related_entries:
  - methodologies/2026-05-13_critic-triage-routing-strategist-vs-defer-doc.md
  - methodologies/2026-05-13_verify-audit-claims-before-designing-fix.md
domain: methodologies
topic: validation
---

# Probe-Before-Chain: Verify Handoff Inputs Before Running Multi-Mode Chains

## The Pattern

When a handoff brief asks you to reconcile two artifacts — research vs spec, recommendation vs in-flight work, brief vs current state — **probe both artifacts for existence and current state before running any KF mode chain.** Handoff briefs are often authored against a stale mental model. The brief's assumptions about file names, file locations, version numbers, and implementation status can be wrong without the author knowing it.

The probe pass is read-only and tightly scoped: locate the referenced artifacts, sample-read enough to confirm shape and version, surface mismatches to the user *before* committing tokens to ERA / Strategist / Builder / Critic passes.

## When to apply

- A handoff brief instructs a multi-mode chain (typically 3+ modes: ERA → Strategist → Builder → Critic).
- The brief references specific file names, paths, versions, or implementation phases.
- The brief asserts current state ("v0.3 is pending implementation", "the four contract files exist at X").
- The brief originated in a different conversation, from a different mental model, or after the working tree may have advanced.

## When NOT to apply

- Single-mode invocations (kf-builder for new spec from scratch; kf-debugger on a fresh error trace). No reconciliation surface to verify.
- The brief explicitly says "ignore current state; design clean-room."
- The artifacts under reconciliation are entirely under your authorship in the current session.

## The Method

**Step 1 — Enumerate referenced artifacts.** Pull out every file path, version number, named entity, and implementation-phase assertion the brief makes. Build a checklist.

**Step 2 — Locate each artifact deterministically.** Use `find`, `ls`, `grep` — not LLM judgment. The artifact either exists at the named path or doesn't. If multiple candidate paths exist (case-insensitivity, relocated files), enumerate all of them.

**Step 3 — Sample-read to confirm shape + version.** For each located artifact: read the header (first 30-50 lines) to verify schema_version, status, last_updated, and section structure match the brief's assumptions.

**Step 4 — Detect mismatches.** Compare brief assertions to ground truth:
- Files named differently than the brief claims? (e.g., brief says `proposal_schema.toml` exists at planning/iteration-loop/; reality: it's at `~/.claude/wiki/operations/iteration-loop/`)
- Files don't exist at all?
- Versions advanced beyond what the brief assumes?
- Implementation status diverged ("spec-pending-implementation" → "shipped this week")?
- Module / agent / skill references match what's installed?

**Step 5 — Surface findings to user BEFORE running the chain.** Halt with a tight summary of mismatches and options:
- Proceed with corrections (brief's intent preserved against ground truth)
- Pivot to a different scope
- Wait for the user to provide missing inputs

**Step 6 — Then run the chain** with corrected baseline.

## Why this works

LLM chains compound assumptions. If ERA runs on the wrong entity set, Strategist's trade-offs are non-comparable, Builder produces deliverables citing wrong files, Critic flags the deliverables as wrong but can't see that the upstream baseline was the actual problem. Total burn: 30-50k tokens producing a reconciliation that needs to be redone.

The probe is ~5-10k tokens of deterministic file reads. The savings dominate every time the brief turns out to have stale inputs.

Empirically (observed multiple times in this codebase): briefs from prior conversations carry mental-model drift. The 5-file `~/.claude/wiki/operations/iteration-loop/` relocation, for example, was a v0.3 README §0.1 bootstrap step that brief authors a week later didn't know had happened. Without the probe, the entire reconciliation would have been built on substitute files at wrong paths.

## Case study (2026-05-24)

Reconciliation: "Iteration Loop v0.3 ↔ 24/7 Worker Fleet Research" handoff. Brief asserted:

1. Research report at `~/Scripts/[project]/docs/research/24-7-worker-fleet-research.md` (didn't exist).
2. Four contract artifacts at planning dir: `proposal_schema.toml`, `heartbeat_schema.toml`, `baking_pipeline_contract.md`, `surface_routing_rules.md` (existed, but at `~/.claude/wiki/operations/iteration-loop/` per v0.3 README §0.1 bootstrap relocation).
3. v0.3 is "spec-pending-implementation" (false; Phase A shipped earlier the same week with two live workers).
4. KF version 7.2.1 (false; installed 6.3 per global CLAUDE.md — but the "v7.2" references the brief read turned out to be intra-module schema versions, not the KF system version).

Probe (~10k tokens) caught all four. Without it, the chain would have run ERA on substitute files (the runtime `.py` schemas instead of the wiki TOML contracts) and produced wrong delta analysis. Builder would have cited non-existent paths in the deliverables.

After probe: brief intent preserved, artifacts re-baselined, chain ran cleanly, deliverables shipped against actual ground truth. See: `docs/planning/iteration-loop/handoff/reconciliation-report.md` §7 "What's Different from the Original Handoff Brief".

## Anti-patterns

- **Trust the brief's file names.** Names are the most drift-prone surface — relocations, renames, and refactors happen between conversations.
- **Run ERA "to see what's there."** ERA is for entity reconciliation across known artifacts, not for discovery. Use deterministic `find`/`grep` for discovery.
- **Probe-and-proceed without user confirmation.** If mismatches are found, the brief's mental model has drifted from reality. The user needs to confirm the corrected baseline; auto-correcting silently produces deliverables the user doesn't trust.
- **Skip probe for "small" reconciliations.** Brief authoring drift correlates with elapsed time between conversations, not with reconciliation size. A 2-week-old brief on a single contract file may be just as wrong as a multi-week-old brief on a system architecture.

## Related patterns

- [[verify-audit-claims-before-designing-fix]] — same family: verify the failure-mode-as-described matches the actual code before designing remediation. Probe-before-chain is the brief-level analog.
- [[critic-triage-routing-strategist-vs-defer-doc]] — once probe surfaces mismatches, the triage decision (run chain corrected vs halt for user input) is itself a Strategist call.
