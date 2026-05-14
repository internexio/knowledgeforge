---
title: Phased god-module split — facade-first, late-bound helpers, simplest-first sequencing
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-13
domain: patterns
topic: synthesis
tags: [quality-gate, deployment, empirical]
related_entries: [patterns/mode-variants-taxonomy.md, orchestration/spec-commit-before-impl-commit.md, architecture/scaffolding-vs-patching-pattern.md]
---

# Phased god-module split pattern

A repeatable strategy for breaking up files that have grown past 2,000 LOC and accumulated unrelated responsibilities. Validated this session across five independent applications:

| File | Before | After | Sub-files | Phases |
|---|---|---|---|---|
| `app/services/database.py` (Python/FastAPI) | 1,008 LOC | 165 LOC (facade) | 8 repos | 1 |
| `app/api/projects.py` (Python/FastAPI) | 2,748 LOC | 742 LOC (`__init__.py`) | 6 sub-resources | 6 |
| `app/api/admin.py` (Python/FastAPI) | 2,597 LOC | 2,485 LOC | 1 service (`TemplateRepo`) | 1 |
| `app/api/chat.py` (Python/FastAPI) | 2,144 LOC | 1,953 LOC | 1 pipeline service | 1 |
| `src/pages/Projects.tsx` (React/TypeScript) | 4,377 LOC | 528 LOC | 13 section/component files | 9 |

## Core moves

### 1. Facade-first for service classes

When the god module is a *class* with many methods, do **not** rename callers in the same commit. Instead:

1. Extract each domain into its own file with a class that takes the underlying client/state in `__init__`.
2. Rewrite the god class as a **facade** that holds instances of the new sub-classes as attributes (`db.conversations`, `db.messages`, …) AND keeps every legacy method as a 1-line delegate (`async def get_conversation(self, *a, **kw): return await self.conversations.get_conversation(*a, **kw)`).
3. Callers don't change. They migrate opportunistically to the attribute path (`db.conversations.get_conversation(...)`) over time. The delegate methods can be removed once the migration is complete.

This made it possible to ship the database.py split as a single zero-behavior-change commit despite 60+ call sites across 10 files.

### 2. Late-bound helper imports for package conversions

When the god module is a single *file* with many top-level functions/components, convert it to a package (e.g., `app/api/projects.py` → `app/api/projects/__init__.py`) and pull sub-resources into sibling files (e.g., `app/api/projects/files.py`, `pages.py`, …). The package `__init__.py` mounts each sub-router at the bottom:

```python
# At the END of __init__.py (after all helpers + the main router are defined):
from app.api.projects.files import router as _files_router
router.include_router(_files_router)
```

Sub-modules avoid the obvious circular import (they need shared helpers like `_get_owned_project` that live in `__init__`) by **late-binding inside function bodies**:

```python
def list_files(...):
    from app.api.projects import _get_owned_project  # late-bound
    _get_owned_project(project_id, user.id)
    ...
```

By the time a route handler runs, the package is fully loaded and the symbol resolves. Module-load-time imports would fail because `__init__.py` imports the sub-module to mount its router.

### 3. Simplest-first sequencing

For multi-phase splits, **phase 1 is always the most isolated sub-resource**. For projects.py the order was: files → pages → goals/decisions → campaigns → personas → bundle. For Projects.tsx: Files → Instructions → QuickLinks+CalendarLink → Platforms+CampaignNotes → AudienceSegments → Strategy → BrandVoice → Personas → ProjectsList chrome. This:

- Establishes the directory structure with low-risk first
- Lets the team validate the import pattern + test suite stability before bigger chunks land
- Reveals shared dependencies (e.g., `FetchErrorBanner` used by 3 sections → extracted to `components/` after phase 1)
- Builds a precedent the user can point at: "same pattern as previous phases" becomes a reviewable signal

## When this applies

- Single file > 1,500 LOC mixing 5+ unrelated responsibilities
- Tests already cover the public surface (so you can prove byte-equivalence)
- The function/class names are stable enough that 1-line delegates can preserve them indefinitely
- Multi-phase pacing is acceptable (i.e., not a one-shot rewrite)

## When this does NOT apply

- The god module's interior is genuinely incoherent — facade-style won't help, and you need a from-scratch redesign
- Public API needs to change as part of the split (then the facade is a lie; do the rename instead)
- File is < 1,000 LOC — overhead of multiple files isn't justified
- No test coverage on the public surface — split risks behavior drift you won't catch

## Concrete grounding

- `database.py` facade: 31 delegating methods, all 60+ call sites untouched. Backend 932/932 tests pass at the same commit that introduces the split.
- `projects.py` package: 6 phases over 6 commits. Each phase shipped independently, each at 951/951 passing.
- `Projects.tsx` package: 9 phases. Each shipped at 176/176 frontend tests + clean typecheck.
- The late-bound helper pattern was used 18 times across the projects.py split (6 sub-files × ~3 helpers each) without a single circular-import failure.

## Source Context

Validated across five independent god-module refactors in the COS platform and EI projects (Python/FastAPI backends + React/TypeScript frontends). Each application followed the same three moves: (1) extract with facade, (2) use late-bound helper imports to avoid circular dependencies, (3) phase by isolation level. The pattern produced 100% test pass rates at every phase boundary and enabled incremental shipping without behavior drift. Sourced from session `cos-week3-god-module-splits-2026-05`.
