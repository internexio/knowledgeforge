---
title: Fleet repo audit: 4-tier classification methodology for multi-repo codebases
source_mode: strategist
novelty_type: reusable_diagnostic
grounding_score: 0.80
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-07
domain: methodologies
topic: decision-framework
tags: taxonomy, quality-gate, deployment
related_entries: []
---

# Fleet Repo Audit: 4-Tier Classification Methodology for Multi-Repo Codebases

## Problem

When a project grows to 10+ repos, it becomes unclear which repos are active, which are dormant, which are duplicates, and which can be safely archived. Ad-hoc decisions made per-repo lead to inconsistent standards and missed cleanup opportunities.

## The 4-Tier System

**Tier 1 — Monitor** (active, in-scope, include in automated sweeps)
Criteria: committed within last 4 weeks AND serves a current product/integration function

**Tier 2 — Active but peripheral** (alive but not in main coordination loop)
Criteria: committed within last 4 weeks BUT either local-only, dependency-only role, or scope outside current focus

**Tier 3 — Clarify** (ambiguous — need one question answered before classifying)
Criteria: unclear purpose from name/README alone, or anomalous signals (wrong remote, unexpected commit content)

**Tier 4 — Archive** (safe to move out of active workspace)
Criteria: last commit > 3 months AND (no beads OR beads all closed) AND no active cross-repo dependency

## Signal Stack (Run in Order, Fast to Slow)

1. **Does the repo have its own `.git` directory?** (not inheriting from a parent Scripts repo)
   — False positives if you run `git log` on a dir without its own `.git`
2. **Last commit date** — `git log -1 --format="%cr"` — under 4 weeks = active signal
3. **Remote presence** — `git remote get-url origin` — local-only = higher archival risk
4. **Beads presence** — `ls .beads/` — no beads often = prototype or abandoned
5. **README first 5 lines** — purpose and scope; catches duplicate clones (same remote = same repo)
6. **Cross-repo dependency check** — grep SURFACE_MAP or coordination docs for references

## Duplicate Clone Detection

Two repos with identical `origin` remotes are duplicate clones. Keep the one with more recent commits; archive the other. In the 2026-07-07 audit, cos-skills and cos-cc both pointed to `git@github.com:internexio/cos-cc.git` — cos-skills was kept (3 weeks ago), cos-cc archived (3 months ago).

## Anomaly Signals Warranting Tier 3 (Clarify) Rather Than Tier 4 (Archive)

- Commit message references a different project's bead ID (cross-contamination)
- Remote URL doesn't match what the repo name implies
- README describes something incompatible with last commit message
- Is a path dependency for an active Tier 1 repo (even if stale itself)

## Archive Mechanics

`mv ~/Scripts/{repo} ~/Scripts/archive/{repo}` — preserves full git history, keeps code accessible without cluttering the active workspace. Preferable to deletion unless the repo is a confirmed exact duplicate with a live identical clone.

## Applied Example (2026-07-07 Audit, 13 Repos)

- **Tier 1 (7):** [project]/cos, client-project, semalytics-gtm, cos-grounding, cos-skills, cos-browser-analyzer, keywordplannertools
- **Tier 2 (2):** cos-manager (self), [project] (path dep only)
- **Tier 3 → resolved (4):** cos-cc (duplicate of cos-skills), cos-cw (KF-CW plugin), cos-research (predecessor app), cos-score (stale CLI)
- **Tier 4 (1):** semalytics-update (10 months, PAIRED branding dead)
- **Result:** 5 archived, 1 duplicate moved to archive; active workspace reduced from 13 to 8 repos

## Anti-Patterns

- Classifying on commit count rather than commit recency (old active repos look stale by count)
- Archiving a Tier 2 dependency before checking if anything in Tier 1 depends on it at build time
- Deleting rather than archiving (loses git history; archive is reversible)
- Running git commands on parent directories without verifying `.git` presence first

## When This Applies

- Multi-repo projects (10+ repos) where manual per-repo classification has become error-prone
- Quarterly or semi-annual fleet hygiene sweeps
- Preparation for cross-project coordination work (identifying which repos must stay synchronized)
- Workspace-cleanup initiatives where clarity on "what's actually being used" is a prerequisite

## When This Does NOT Apply

- Small codebases (< 5 repos) — overhead exceeds benefit
- Automated fleet management systems that already have repo provenance tracking
- Teams with explicit documented repository lifecycle policies and tooling (e.g., Renovate, dependabot fleet config)

## Key Insight

The 4-tier system transforms subjective "is this repo dead?" conversations into a deterministic checklist with clear signal ordering. The recency-based thresholds (4 weeks active, 3+ months archive candidate) are defaults — they should be calibrated to your project's actual velocity and commit patterns.

## Source Context

Derived from the 2026-07-07 cos-fleet-cleanup session. Applied to 13 repos (cos-manager, [project] ecosystem, semalytics suite, related tools) to establish a baseline classification and execute archival decisions for 5 repositories and 1 duplicate.

