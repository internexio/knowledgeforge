---
title: MemPalace mine skips already-filed files — wing migration via re-mine is impossible
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 4
pinned: false
created: 2026-07-07
domain: integration
topic: external-tools
tags: semantic-search, empirical, accretion
related_entries: []
---

# MemPalace mine skips already-filed files — wing migration via re-mine is impossible

## Pattern

`mempalace mine <dir> --wing <wing>` skips files that were already filed anywhere in the central palace (`~/.mempalace/palace`), regardless of which wing they were filed into. Re-mining a directory into a new wing produces "Files skipped (already filed): N" with zero drawers filed.

## Concrete verification (2026-07-07)

During Module 22 Phase 2 implementation, all 11 wiki subdirectories were inited with `mempalace.yaml` and mined individually to move entries from the flat `wiki-kf-core` wing into per-subdomain wings (`wiki-patterns`, `wiki-infrastructure`, etc.). Every mine returned:

```
Files processed: 0
Files skipped (already filed): 73
Drawers filed: 0
```

The central palace tracks filed files by identity (path and/or content fingerprint). The `--wing` override has no effect on dedup — the palace considers the file "already done" and skips it.

## Root cause

MemPalace's deduplication is global across wings, not per-wing. This prevents duplicate drawer accumulation (the design intent), but it also makes it impossible to reassign an existing file to a different wing via the standard `mine` workflow.

## Consequence for architecture

Wing migration for existing entries requires one of:

1. `tool_add_drawer` calls directly (bypasses mine dedup), adding new drawers with the target wing label — leaves old drawers in the original wing as orphans
2. Delete old drawers manually + re-mine into new wing (requires MemPalace drawer deletion API)
3. Accept the transitional state: existing entries stay in the original wing, client-side metadata filters (domain/topic) provide correctness, per-subdomain wings accumulate naturally as new entries are added

Module 22 Phase 2 chose option 3 — the wrapper searches the legacy `wiki-kf-core` wing globally and applies frontmatter-based domain filter for correctness.

## When This Applies

- Any MemPalace project that adopted a flat-wing scheme early and later needs per-subdomain wing scoping
- Any attempt to re-organize MemPalace content across wings after initial mining
- Planning wiki taxonomy changes that depend on wing-level search scoping
- Designing semantic search systems where wing organization is expected to reflect schema evolution

## When This Does NOT Apply

- First-time mining (no prior drawers → dedup doesn't skip anything)
- Content that was never mined (new files added after the wing scheme changed)
- Projects using MemPalace's knowledge graph (`kg_add`) rather than `mine` — kg_add has different dedup semantics
- Static wing assignments without schema-driven reorganization

## Source Context

Module 22 Phase 2 implementation session (knowledgeforge-core-acu-phase2-2026-07-07). Discovery: schema migration from flat `wiki-kf-core` wing to per-domain wings (`wiki-patterns`, `wiki-infrastructure`, etc.) hit a hard blocker when re-mining existing entries.
