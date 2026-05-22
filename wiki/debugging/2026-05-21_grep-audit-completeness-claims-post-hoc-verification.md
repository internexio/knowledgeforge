---
title: Verify fix-commit completeness claims with a post-hoc grep audit
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-21
domain: debugging
topic: regression-detection
tags: quality-gate, adversarial, empirical, grounding
related_entries: []
---

# Verify Fix-Commit Completeness Claims With a Post-Hoc Grep Audit

## The Problem

When a commit fixes a pattern across multiple call sites (e.g., "guard all `maybe_single()` against None"), the commit message often claims completeness — "this was the only missed site" or "all other call sites already include the guard." That claim is unverified at commit time and frequently wrong.

## Concrete Incident

Commit `1ed30b5` (COS repo, 2026-05-18) patched `_get_owned_project` to guard against `supabase-py 2.30` returning None from `maybe_single().execute()`. The commit message stated:

> "All other maybe_single() call sites in the codebase already include the `if result and result.data` guard — this was the only missed site."

A grep audit on 2026-05-21 (during cos-9m3 triage) found the claim was wrong. Twenty-two unguarded sites remained:
- 9 in `backend/app/api/projects/` (campaigns, files, goals_decisions, pages, personas)
- 4 in `backend/app/api/admin_kf.py`
- 1 in `backend/app/api/tier0_viewer.py`
- 5 in `backend/app/services/credit_service.py`
- 3 in `backend/app/services/project_context/`

Each was a latent 500-instead-of-404 surface. `credit_service.py` specifically runs on every analyze request — a None balance row from the supabase-py quirk would 500 the entire analysis path.

## The Pattern

After any commit that patches a code pattern across multiple sites, run a grep audit AGAINST THE REPO STATE (not against memory or commit-message claims) to verify completeness:

```bash
# After patching: grep for the pre-fix anti-pattern
git grep -n "if not <var>.data:" -- 'backend/app/**/*.py' \
  | grep -B2 "maybe_single"  # filter to maybe_single-adjacent sites
```

Or, more robustly, write a quick AST-based audit script that looks for the structural anti-pattern in context. The script searches for `.maybe_single().execute()` followed by an unguarded `.data` access.

## When This Applies

- Pattern-cleanup commits (regex replace, structural fix across files)
- Defensive-guard additions (None guards, type guards, auth guards)
- Library-quirk fixes that have predictable call-site signatures
- Multi-file refactors where the commit message claims "all sites done"

## When This Does NOT Apply

- One-off bug fixes where there is no "pattern" of sites
- Refactors where the pattern is being eliminated entirely (rather than fixed in place)
- Single-file changes with a clear scope boundary

## Operational Rule

The commit message can SAY anything. The code state is what matters. If a commit message asserts "X is the only site" or "all other sites are fine," that assertion should be backed by a grep result reproducible by a future maintainer.

**Ideal:** Include the audit command in the commit body or land the audit as an automated CI check (e.g., a pre-commit hook that fails when the anti-pattern reappears after the commit claims it's fixed).

**Minimal:** At code-review time, reviewer runs the same grep on the patched version and confirms the claim.

**Never:** Trust the claim without verification — patterns spread faster than fixes, and "I fixed the only one" is a high-confidence failure mode.

## Related Concepts

- See also entry on "verify-audit-claims-before-designing-fix" — similar principle applied to tech-debt audits before implementation. That's about audit documents going stale; this is about commit-time claims.
- See also "adversarial-filename-audit" — both involve explicit filesystem/content verification against claims in documentation.

## Source Context

Discovered during COS triage session cos-9m3-triage-cos-ect-shipped-2026-05-21. Commit `1ed30b5` claimed it was "the only missed site" for a supabase-py None-guard pattern. Post-hoc grep audit found 22 additional unguarded call sites across 5 files, creating latent 500 surfaces on production traffic. The audit-after-commit surfaced a regression that shipped despite the fix commit's completeness claim.
