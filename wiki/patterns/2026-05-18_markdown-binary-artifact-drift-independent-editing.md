---
title: Markdown-to-binary artifact drift when both are source-edited independently
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-18
domain: patterns
topic: validation
tags: quality-gate, deployment, grounding, accretion, source-of-truth
related_entries:
  - patterns/2026-05-18_python-pptx-in-place-editing-patterns.md
---

# Markdown-to-binary artifact drift when both are source-edited independently

## The Problem

When a project keeps a markdown source (e.g., `pitch-deck-keiretsu-2026-05.md`) AND a derived/exported binary artifact (e.g., `SEMalytics-Pitch-Keiretsu-2026-05.pptx`) in the same directory, and neither has a deterministic build script that regenerates the artifact from the source, edits applied to the markdown will not propagate to the artifact — and vice versa. Both files become independent sources of truth, and they will drift the moment the user makes a "small fix" in either one.

This happened in a real session: after careful COS-informed rewrites were applied to the markdown source, the user opened the .pptx and observed all the original (presumptuous, AI-fingerprinted) content was still there. Every COS improvement and named-reference strip had to be re-applied to the .pptx independently using python-pptx.

## Concrete Example

**Session: pitch-deck-cleanup-2026-05-18**

Starting state:
- `docs/pitch-deck-keiretsu-2026-05.md` — markdown source with full slide-by-slide content
- `docs/SEMalytics-Pitch-Keiretsu-2026-05.pptx` — PowerPoint export (last updated 2026-05-14)
- No `Makefile`, no `build-deck` script, no Marp config

Edits applied via COS-analysis (×2) + COS-copy (×1):
- Removed 15+ presumptuous claims and AI-voice markers
- Rewrote sections for named-reference accuracy
- Tightened copy across all slides

After applying all edits to the markdown, user opened the .pptx for a review pass and found **zero changes**. All the original content persisted. Required a follow-up python-pptx script to apply every text change a second time to the binary artifact.

## When This Applies

- Any project where a markdown/JSON/YAML source feeds an exported binary (.pptx, .docx, .pdf, .xlsx, image)
- No build script or pipeline that auto-regenerates the artifact on source change
- Source and artifact are stored side-by-side in version control or working dir
- Editors believe (or assume) they can edit the source and the artifact will catch up
- Team members may edit either the source or the artifact independently

## When This Does NOT Apply

- Sites with explicit build pipelines (Marp, Pandoc-driven slide gen, Hugo, etc.) where artifact is rebuilt from source on every change or on-demand
- Projects where only the binary is maintained (markdown source is one-time scaffolding)
- Projects where only the source is maintained (binary is regenerated on demand and treated as cache)
- Single-editor workflows where one person owns the artifact and strictly forbids source edits

## Mitigations (in preference order)

### 1. Build Script (Preferred)
Make the artifact a true derived artifact: add a `make deck` or `npm run build:deck` that regenerates the .pptx from the .md. Eliminates the drift problem at the root.

Approach:
- Use Marp for slide decks (markdown → PDF/PPTX)
- Use Pandoc for documents (markdown → DOCX/PDF)
- Use python-pptx for custom PowerPoint generation (python script reads markdown, populates template)
- Use openpyxl for spreadsheets (python script reads YAML, populates workbook)

Cost: One-time setup (1-2 hours). Payoff: eliminate drift forever.

### 2. Single Source of Truth
Pick one representation. If the .pptx is the artifact that ships, retire the .md or mark it as a one-shot draft. If the .md is the source, treat .pptx as ephemeral.

Cost: Minimal. Payoff: eliminates confusion about which file to edit.

### 3. Reconciliation Checklist
If both must exist independently (because the .pptx has visual design the markdown can't express), explicitly enumerate the changes to apply to each on every edit pass.

Example checklist:
```
[ ] Update slide 1 title in markdown
[ ] Update slide 1 title in .pptx
[ ] Update slide 3 table content in markdown
[ ] Update slide 3 table content in .pptx
...
```

Cost: Moderate (requires discipline). Payoff: prevents accidental single-source edits.

### 4. Programmatic Propagation
Use python-pptx (or equivalent) to read the markdown and apply targeted text replacements to specific slide shapes, preserving the .pptx's visual design. See related entry [[python-pptx-in-place-editing-patterns]] for technique.

Cost: Per-session effort (30-60 minutes per edit pass). Payoff: one-way propagation (markdown → binary) without losing design.

## Root Cause

The fundamental issue is **false locality**: editors interact with two files that *appear* independent because they're separate objects on disk. Without a build script, there's no mechanism to enforce coherence. The project has implicitly adopted a "optimistic" stance: "we'll keep them in sync manually." This almost always fails.

## Operational Checklist

Before shipping a project with both markdown and binary artifacts:

- [ ] Does a build script regenerate the binary from the markdown?
  - If YES: proceed. Binary is a derived artifact.
  - If NO: does the markdown say "DO NOT EDIT — this is generated"?
    - If YES: proceed. Binary is the source of truth.
    - If NO: conflict. Choose one, and mark the other as derived/ephemeral.

- [ ] Are both files in version control?
  - If YES: do they have different change frequencies?
    - If YES (e.g., .md changes weekly, .pptx monthly): they're independent sources. Risk of drift. Add mitigation.

- [ ] Does the team have a published policy about which file to edit?
  - If NO: add one. One-line statement in the README: "The **markdown is the source. The .pptx is generated. Edit the markdown, then run `make deck`.**"

## Source Context

Observed during pitch-deck-cleanup-2026-05-18 session. A 12-slide pitch deck (`docs/SEMalytics-Pitch-Keiretsu-2026-05.md` + `.pptx`) underwent 15+ targeted edits via COS multi-pass analysis (removing presumptuous claims, AI voice markers, adding named references). All changes were applied to the markdown. Upon review, the .pptx contained zero changes. Subsequent python-pptx pass was required to re-apply every change to the binary. Two backups created before destructive operations; both preserved.

This pattern is stable and widely applicable — any project mixing markdown/JSON sources with exported binaries faces this risk unless a build pipeline or explicit single-source-of-truth policy is in place.
