---
title: Vendor-in decision framework for flat-script Python projects
source_mode: builder
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-21
domain: integration
topic: external-tools
tags: empirical, quality-gate, api
related_entries:
  - infrastructure/2026-05-12_vendoring-drift-detection.md
  - infrastructure/2026-05-13_default-extension-over-sibling-infrastructure.md
---

# Vendor-in decision framework for flat-script Python projects

## The Problem

You need to reuse code from another Python project that lives in the same workspace (sibling directory, same user). What's the right integration mechanism?

## The Three Options and How to Choose

| Option | When to pick it | Trade-off |
|---|---|---|
| **pip install -e ../sibling** | Source has a `pyproject.toml` or `setup.py` (i.e., it is a real Python package). | Tightest reuse, zero drift. Requires the source to be packaged. |
| **Subprocess (call source's CLI)** | Source is a CLI tool with a stable JSON or text output contract you control. | Preserves project boundary. Latency + parse cost + CLI brittleness; outputs become a coupling surface. |
| **Vendor-in the minimum files needed** | Source is a flat script project (no `setup.py`/`pyproject.toml`) AND your reuse surface is small (<50% of the source). | Ships immediately. Accepts drift risk; you re-sync manually if upstream improves. |
| **Refactor source into a real package first** | You expect to reuse >50% of the source's surface, or upstream evolves quickly enough that drift would burn you. | Cleanest long-term, biggest upfront cost. |

## Decision Gate

1. Does the source have `pyproject.toml` or `setup.py`? → If yes, pip install -e and stop here.
2. Is the source a script-only project? → Estimate reuse surface.
   - Small (one wrapper class + a few helpers): vendor the minimum. Note the drift risk in a comment.
   - Large: refactor source into a real package first, then pip install -e.
3. CLI surface tempting? → Almost always worse than vendoring because the JSON/text contract becomes an unwritten API.

## Grounding (sem-tools F10.2-shared, sem-tools-osd)

Source: `~/Scripts/reddit-scan/` (no `setup.py`/`pyproject.toml` — confirmed by `ls ~/Scripts/reddit-scan/{setup.py,pyproject.toml}` returning ENOENT for both).

Reuse surface needed: one read-only PRAW wrapper + ~5 heuristic functions for the F10.2b mention-farming detector. Well under 50% of reddit-scan's surface.

Decision: vendor the minimum into `sem/integrations/reddit/{client,heuristics}.py`.

Heavier reddit-scan analyzers (`coordination_detector.py`, `user_pattern_analyzer.py`) were explicitly NOT vendored because they expect a fully collected markdown corpus, which is not the F10.2b workload shape (live PRAW objects, ~5–30 commenters per thread). Vendoring them wholesale would have cost more than rewriting the small heuristic set we actually needed.

## Anti-Patterns

- Don't vendor heavy modules with peripheral dependencies — rewrite the small slice you need.
- Don't reach for subprocess when both projects live in the same workspace; it's almost always worse than vendoring.
- Don't pip install -e a "package" that's really a flat scripts dir with an `__init__.py` glued on — you'll fight import paths forever.

## When NOT to Apply

- If both projects share an org and a CI pipeline, the right answer is usually "refactor source into a package," not vendor-in. Vendor-in is for local-dev workspace integrations where ceremony is the enemy.

## When This Applies

- You have two Python projects in the same workspace (sibling directories, same user control)
- The source project is a flat-script repo (no `setup.py`/`pyproject.toml`)
- You need to reuse a subset of the source's functions or classes
- The reuse surface is estimable and <50% of the source
- You control both projects' evolution within a single workspace

## Source Context

Discovered during sem-tools F10.2b (spam-risk batch processing), 2026-05-21. The `reddit-scan` source was a flat-script project without package metadata; sem-tools needed a read-only PRAW wrapper and ~5 heuristic functions. The decision to vendor the minimum (rather than pip install -e or subprocess) was grounded in reuse-surface estimation: <50% of reddit-scan. Heavier components (`coordination_detector.py`, `user_pattern_analyzer.py`) were not vendored because they expect a corpus-based workflow incompatible with F10.2b's live-mention streaming. Opting for vendor-in preserved sem-tools' self-containment and avoided subprocessing latency.
