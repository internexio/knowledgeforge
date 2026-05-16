---
title: KF Version-Gap Bridging via Adapter Classification
source_mode: synthesizer
source_session: redacted
created: '2026-04-21T00:00:00Z'
date: '2026-04-21'
confidence: 0.9
grounding_score: 0.9
grounding_source: VisionForge Unified composition chain. COS Batch 8 (6 modules) initially
  flagged as high-probability duplicates. ERA revealed all 6 carry domain-specific
  additions. Module census reclassified all 6 as adapter. Adversarial Critic Sev 2
  finding [7] confirmed the rescue.
novelty_type: transferable_framework
staleness_risk: low
importance: 3
pinned: false
accreted_in: '6.5'
related:
- wiki/orchestration/multi-framework-cp-composition.md
- modules/25_era.md
- modules/07_critic_agent.md
---

# KF Version-Gap Bridging via Adapter Classification

## Pattern

When a downstream framework was built against an older major KF version and includes domain-adapted copies of KF infrastructure modules (decision classification, grounding scores, calibration layer):

**Trigger signal:** Any source file declaring `architecture_compliance: "KnowledgeForge 3.x"` or `kf3_version: 3.x` — this is a version-gap tombstone.

**Steps:**
1. Identify the version at which the downstream framework was built (look for tombstone headers in integration notes files)
2. Identify which KF modules the downstream framework adapted
3. For each adapted module: enumerate only the additions/changes between the declared version and current KF — do not compare full content, only the delta
4. Classify as `adapter` if it carries domain-specific logic on top of the KF baseline; classify as `duplicate` only if it is a verbatim copy with zero domain additions
5. Keep all `adapter` modules in the bundle under their domain namespace; do not replace with current KF version
6. For each `adapter` missing KF additions: produce a targeted patch documenting only the specific missing additions; integrate into the adapter's body or ship as a small companion file

---

## Anti-Pattern — "Latest Wins, Drop the Fork"

Classify all downstream adapted modules as duplicates and drop them in favor of the current KF version.

**What breaks:** COS `08_Metacognitive_Monitor` adds a comms-specific confidence degradation floor lower than the general KF floor (copy decisions tolerate more uncertainty than infrastructure decisions) and stale-state contradiction detection (referencing outdated platform trends in copy). Dropping it in favor of KF 7.0.0 Module 14 silently uses the wrong confidence threshold for every COS copy session. The module loads, routing works, the threshold is just wrong for the domain.

**Never drop an adapted module without verifying it carries no domain-specific logic the backbone version lacks.**

---

## Evidence from VisionForge

- COS Batch 8 (6 modules) initially flagged as high-probability duplicates
- ERA analysis revealed all 6 carry domain-specific additions
- Module census reclassified all 6 as `adapter`, zero as `duplicate`
- For `08_Decision_Classification`: a specific 4-item delta was enumerated (Ozymandias Test, bias-toward-upgrading rule, `decision_type_exercised` field, Navigator predicate) and a patch (G9) scoped — then found redundant because the base adapter already incorporated the delta
- Caught by Adversarial Critic as Sev 2 finding [7]

---

## Reuse Context

Reference this entry when:
- Composing any bundle that includes COS (KF 3.2 lineage) against a future KF version
- Evaluating any source framework that declares a version header against the backbone
- Deciding whether to `duplicate` or `adapter` classify a module that "looks like" an existing backbone module
- The pattern recurs predictably: COS retains this gap until re-baselined against current KF
