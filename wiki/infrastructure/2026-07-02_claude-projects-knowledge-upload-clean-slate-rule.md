---
title: Claude Projects appends on re-upload — clean-slate required before every upload cycle
source_mode: builder
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-07-02
domain: infrastructure
topic: deployment
tags: deployment, ops
related_entries: []
---

# Claude Projects Knowledge Upload — Append-Only Behavior and Clean-Slate Rule

## What Was Learned

Claude Projects does **not** replace existing knowledge files when you re-upload a file with the same name. It **appends** — creating a duplicate with a disambiguating suffix (e.g., `06_Quick_Reference__1_.md`). During retrieval, Claude cannot distinguish the canonical file from the stale duplicate, creating a live contradiction source.

**Discovered during:** KnowledgeForge v7.22.0 deployment planning (2026-07-02 audit remediation). The clean-reupload rule was added to both the core README and the CP variant README as a deployment prerequisite.

## The Problem

If you upload KnowledgeForge module files to a Claude Project, then re-upload after a version bump without deleting the old files first:

- `06_Quick_Reference.md` (old, stale) remains in the project
- `06_Quick_Reference__1_.md` (new, canonical) is added alongside it
- Retrieval can return either version — you get non-deterministic behavior where some queries hit the stale spec and others hit the current one
- This is silent: the UI shows both files, but there is no warning at query time that contradictory knowledge exists

The symptom: audit findings that Module N is deployed at version X while the core is at version Y, with no mechanism to resolve the collision. The platform's append-not-replace behavior silently allowed stale versions to persist undetected.

## The Fix

**Before every re-upload cycle:**
1. Open the Claude Project at claude.ai
2. Go to Project Knowledge
3. Delete **ALL** existing knowledge files
4. Upload the new version set from scratch

This is a clean-slate upgrade pattern — there is no "replace file" operation in Claude Projects.

## Upload Layout (KnowledgeForge-specific)

For KnowledgeForge specifically, the correct upload set is:

- `00_Project_Instructions-Claude.md` → **Project Instructions** field (not Knowledge)
- `01_Navigator_Agent.md` through `25_Entity_Relationship_Analysis.md` → **Project Knowledge** (25 files)
- README, CHANGELOG, EXPLORATION_PROMPTS — not uploaded (human reference only)

## When This Applies

Any knowledge-base update to a Claude Project where files are being replaced or updated. Applies regardless of whether you are updating 1 file or all 26 module specs.

## When This Does NOT Apply

- First-time setup (no existing files to conflict with)
- Adding genuinely new files that have no prior version in the project
- Claude Code deployments (compiled output goes to `~/.claude/`; overwrite behavior is normal at the filesystem level)

## Source Context

Grounding discovered through the 2026-07-02 audit finding during KF v7.22.0 deployment planning — Module 00 was observed at v7.9.0 in a deployed CP while the core was at v7.21.0. Investigation revealed that the append-not-replace platform behavior had silently allowed a stale version to persist undetected across multiple re-upload cycles. The clean-reupload instruction is now canonical in the KnowledgeForge README and CP variant README.

This is a stable operational constraint of the Claude Projects platform verified through direct experience.
