---
title: KF semver lives on three surfaces — module version, kf.yaml system version, platform binding version — and they bump independently
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-10
tags: versioning, semver, spec-impl-discipline, kf-internal, change-management
related_entries:
  - methodologies/2026-05-20_propagation-gap-addenda-propose-downstream-changes-that-dont-execute.md
  - methodologies/2026-05-21_critic-verification-pass-second-pass-validation.md
domain: methodologies
topic: propagation-discipline
---

# KF Semver Lives on Three Surfaces — and They Bump Independently

## The Three Surfaces

KnowledgeForge maintains **three distinct version numbers**, and they bump independently. Conflating them in a spec produces confusion at implementation time.

| Surface | File | When it bumps |
|---|---|---|
| **Module version** | `modules/NN_*.md` — `module.version` field inside the YAML metadata block | When THAT specific module's content changes (patch / minor / major per project CLAUDE.md rule) |
| **KF system version** | `kf.yaml` — `version` field at top of file | When ANY module minor/major bump, or any compiler/binding change |
| **Platform binding version** | `platform-bindings/<target>.yaml` — `platform_version` field | When the platform binding contract changes (output_structure schema, special_outputs additions, etc.) |

These three numbers are NOT synchronized. M21 might be at 7.0.6 while kf.yaml is at 7.3.1 while the claude-code binding is at 7.0. A single spec implementation can bump all three by different amounts in a single cycle.

## Concrete grounding from Phase 1 + Phase 2 (2026-06-10)

### Phase 1 (bead `knowledgeforge-core-y4b` → impl `poz`)

The Phase 1 spec (`docs/planning/2026-06-10_module-21-activation-profile-spec.md`) said:

> **Proposed version bump:** 7.3.1 → **7.4.0** (minor — new field, new gate clause, additive)

At implementation time, M21 was actually at **version 7.0.6**, not 7.3.1. The 7.3.1 number was the SYSTEM version (kf.yaml), not the M21 module version. The spec author had conflated them.

Correct interpretation — spec intent was a "minor bump." Implementation applied:
- M21 module: 7.0.6 → **7.1.0** (minor; new behavior + additional rule)
- kf.yaml system: 7.3.1 → **7.4.0** (minor; follows M21)

The implementation commit reconciled the version-name confusion in its commit body so future readers can trace the discrepancy.

### Phase 2 (bead `knowledgeforge-core-5fd` → impl `261`)

Phase 2 produced **three** version bumps in a single implementation cycle:
- M21 module: 7.1.0 → **7.1.1** (patch-equivalent — added step_5b runtime emission)
- Platform binding (claude-code.yaml): 7.0 → **7.1** (cc_rules + cc_settings_fragment under special_outputs)
- kf.yaml system: 7.4.0 → **7.5.0** (minor; follows compiler + binding additions)

## Spec authoring rule

When proposing a version bump in a spec doc, ALWAYS name the surface explicitly.

**Bad:**
```
Proposed version bump: 7.3.1 → 7.4.0 (minor)
```

**Good:**
```
Proposed bumps:
  - Module 21 (modules/21_*.md): 7.0.6 → 7.1.0 (minor — new field + new gate clause)
  - kf.yaml system:                7.3.1 → 7.4.0 (minor — follows M21)
  - Platform binding:              no change
```

Without the surface name, the reader has to infer which `version: X.Y.Z` line the spec means — and the inference is wrong as often as it's right.

## Implementation rule

When implementing a spec, **verify the current version of each surface before applying the bump**. The numbers in the spec may have been written against an older snapshot. Take the spec's INTENT (patch / minor / major level) and apply it to the current numbers.

Practical check before any version-bump edit:

```bash
# Current module version
grep -A1 "^module:" modules/21_knowledge_accretion.md | grep "version:"

# Current system version
head -3 kf.yaml | grep "^version:"

# Current binding version
head -3 platform-bindings/claude-code.yaml | grep "^platform_version:"
```

Three commands, three numbers, three independent bump decisions.

## Versioning rules (per project CLAUDE.md, repeated here for self-containment)

| Level | When |
|---|---|
| **Patch** (X.Y.Z → X.Y.Z+1) | Typo fixes, clarifications, no behavior change |
| **Minor** (X.Y.Z → X.Y+1.0) | New behavior, additional rules, protocol extension |
| **Major** (X.Y.Z → X+1.0.0) | Protocol overhaul, breaking interface change |

The same rule applies to all three surfaces — but the decision is made per-surface, not globally.

## When this composes with other patterns

This pattern composes with the existing "verify the bead's premise before claiming" guardrail in `~/.claude/CLAUDE.md`. Both are forms of **verify-current-state-before-applying-planned-action**. The bead-premise check protects against stale problem descriptions; the version-surface check protects against stale version baselines.

## What this does NOT cover

- **Module ordering when multiple modules change in one commit.** If a single implementation pass edits M21 AND M22, each module's `module.version` field bumps independently. The kf.yaml changelog entry references both module bumps.
- **Pre-release labels.** KF doesn't use `-alpha` / `-beta` / `-rc` qualifiers on module versions today. If introduced later, the surface-distinction rule would still apply.
- **Variant repos (cc, cp, cw).** Variant repos' own commits don't bump these three surfaces; they're regenerated from core by the compiler. The compiler stamps the system version into compiled outputs.

## Failure mode this prevents

A spec author says "M21 7.3.1 → 7.4.0." The implementer reads the spec, opens `modules/21_*.md`, sees `version: 7.0.6`, gets confused. Either (a) the implementer bumps M21 to 7.4.0 to match the spec — wrong; loses the version-history continuity for M21 — or (b) the implementer pauses to ask the spec author what they meant — burns a clarification cycle. The fix is upstream: the spec author names the surface, so the implementer never has to disambiguate.
