---
title: Deprecating a target requires removing the shared infrastructure — the orphaned generic path becomes a leak vector
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.80
staleness_risk: stable
importance: 3
pinned: false
created: 2026-06-15
domain: diagnostics
topic: refactor-hygiene
tags: deprecation, multi-target-publish, dead-code, leak-surface, refactor-hygiene
related_entries:
  - wiki/patterns/2026-05-11_archival-retirement-not-relocation.md
  - wiki/architecture/2026-05-20_platform-deprecation-architectural-intent-preservation.md
  - wiki/strategy/2026-06-14_substrate-migration-triage.md
---

# Deprecating a Target Requires Removing the Shared Infrastructure — the Orphaned Generic Path Becomes a Leak Vector

## Core Principle

When a build/publish/compile system has N targets and one target is deprecated, **the shared/generic infrastructure that was written to accommodate all N targets is now over-general**. The deprecation must remove not just the target's binding/choice/route, but also the shared code paths that existed because target-N's needs differed from the others. Otherwise the over-general path stays in place and silently behaves as a leak vector between the surviving N−1 targets.

## The Pattern Shape

- Generic export path was written when target N still mattered (it needed special handling that targets A and B didn't share).
- The genericity made the path target-agnostic — it applied the same filter to all targets.
- Target N's deprecation closes the surface that justified the genericity, BUT
- the generic path persists, now applying target-N's defaults to A and B.
- The defaults are wrong for one of {A, B} but the leak is silent because the filter doesn't differentiate.

## When This Applies

- Any multi-target builder, compiler, publisher, or codegen system.
- A target is being deprecated, archived, or retired.
- The surviving targets have different content requirements.
- Especially when the deprecation is described as "drift" or "no longer maintained" rather than "removed" — partial removal preserves the surface.

## When This Does NOT Apply

- All targets had identical needs to begin with (shared path is correct).
- The deprecated target was the strictest (its defaults are conservative for everyone).
- The shared path is genuinely orthogonal to the deprecated target's existence.

## Refactor Checklist When Removing a Target

1. Remove the target's binding file / config entry.
2. Remove the target from the dispatch surface (argparse choices, target enum, route table).
3. **Audit every shared/generic code path that referenced "all targets"** — identify which targets actually need the shared behavior vs which were just along for the ride.
4. Either split the shared path into per-surviving-target paths, or narrow the shared default to match exactly what the survivors need (whichever is fewer lines).
5. Add a fail-closed guard (see `fail-closed-publish-guards-multi-target-compiler` once filed) for any property the formerly-shared filter was supposed to enforce.

## Concrete Grounding (KF compiler, 2026-06-15)

KF historically had three compile targets: **-CC** (Claude Code, filesystem + sub-agents), **-CP** (Claude Projects, docs-only), **-CW** (Cowork, "drifting" status). The `strip_cc_sections()` filter and the broader export path were target-agnostic — the strip logic applied to anything that wasn't -CC. When -CW was effectively dormant but not deprecated, the export path remained generic, and a separate `sync-cp-modules.py` (verbatim copy, no strip) was sometimes used in parallel to the canonical `kf-compile.py --target claude-projects` path. The two paths disagreed about what -CP should receive: kf-compile stripped, sync-cp didn't. Sessions that picked the wrong tool produced leaked CC sections into -CP — which a `kf-sync[bot]` automation reconciled invisibly via PR. The root cause traced back to the shared export path that originated when -CW was also a target requiring its own handling.

**Fix in core@c143865:** -CW formally deprecated:

- binding file `platform-bindings/cowork.yaml` deleted;
- `cowork` removed from `kf-compile.py --target` argparse choices;
- `kf.yaml` `variants.knowledgeforge-cw.status` flipped `drifting → deprecated` with explanatory note.

With -CW out of the target set, the export filter can be per-target and fail-closed (`assert_cp_clean()` + `assert_cc_invariants()`) without worrying about a third historical user.

## Reusable Diagnostic Move

When debugging a leak between surviving multi-target outputs: **look for a third target (current or historical) whose existence justified the generic shared path.** Removing that target — and the shared path along with it — often resolves the leak more cleanly than tightening the filter, because the genericity was the leak's enabling condition.

## Cross-Reference

- Related: **Archival is retirement, not relocation** (`wiki/patterns/2026-05-11_archival-retirement-not-relocation.md`) — operator-side semantics of moving to `archive/`; this entry is the structural analog for build/compile pipelines (the dispatch surface, not the file path).
- Related: **Platform deprecation — preserve architectural intent, replace syntactic constraint** (`wiki/architecture/2026-05-20_platform-deprecation-architectural-intent-preservation.md`) — third-party platform deprecation; this entry covers internal-target deprecation where the over-general code path is the residue.
- Related: **Substrate-migration triage** (`wiki/strategy/2026-06-14_substrate-migration-triage.md`) — when a dormant subsystem becomes a substrate-migration; this entry is the post-decision refactor hygiene.
- Cross-link target (file in parallel this session if accepted): `fail-closed-publish-guards-multi-target-compiler` — describes the per-target fail-closed assertions that should replace the formerly-shared filter.
