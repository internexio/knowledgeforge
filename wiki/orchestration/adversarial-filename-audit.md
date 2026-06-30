---
title: Adversarial Filename Audit as Mandatory Bundle Gate
source_mode: synthesizer
source_session: redacted
created: '2026-04-21T00:00:00Z'
date: '2026-04-21'
confidence: 0.95
grounding_score: 0.95
grounding_source: 'VisionForge Unified composition chain. Sev 1 findings [1] and [4]:
  13 wrong Leonardo filenames + 1 doubled prefix. Both phantom filename failures.
  Both caught only by filesystem glob verification in Adversarial Critic pass. Combined:
  two of three framework contributions silently absent from every session.'
novelty_type: transferable_framework
staleness_risk: stable
importance: 4
pinned: true
accreted_in: '6.5'
related:
- wiki/infrastructure/flat-namespace-prefix-convention.md
- wiki/orchestration/multi-framework-cp-composition.md
- modules/07_critic_agent.md
domain: orchestration
topic: parallel-workflow
---

# Adversarial Filename Audit as Mandatory Bundle Gate

## Pattern

As the final step before marking any knowledge bundle complete, run explicit filesystem verification of every filename referenced in the orchestrator against the actual bundle directory.

**Two failure classes to check:**
1. **Phantom filenames** — referenced name does not exist on disk (wrong prefix, typo, doubled prefix)
2. **Convention violations** — referenced name uses a different convention than files on disk (underscore vs. hyphen, PascalCase vs. lowercase)

**For each file reference in the orchestrator:** glob or exact match against the bundle directory. Zero matches = blocking failure.

**Doubled-prefix lint rule:** Search all file references for any filename beginning with the same prefix token twice (`brand-brand-`, `kf-kf-`).

**This check belongs in the Adversarial Critic pass, not optional review**, because:
- (a) Impact is total — the referenced module never loads
- (b) Failure is silent — no error raised, pipeline appears to run
- (c) Human review does not reliably catch it — wrong filenames are syntactically valid strings

**Time cost:** Under one minute to run. No reason to skip.

---

## Anti-Pattern — "I'll Remember the Filenames"

Trust that orchestrator filenames match disk state because both were authored in the same session.

**What breaks:** VisionForge's CLAUDE.md was updated with Leonardo module references after files were renamed to hyphen/lowercase. The update applied the convention inconsistently: `leo-L01_Campaign_Context.md` (underscore/PascalCase) instead of `leo-L01-campaign-context.md`. All 13 Leonardo references were wrong. A practitioner following the orchestrator's loading instructions loads nothing and generates FLUX prompts without any Leonardo modules — no DR/brand regime classification, no OCEAN-to-visual crosswalk, no anti-pattern filtering. Unconstrained generic AI imagery. No error raised.

**The failure class is guaranteed to recur whenever orchestrators and files are updated in separate steps.** This is the normal condition in any multi-session bundle build.

---

## Evidence from VisionForge

- Sev 1 findings [1] and [4] are both phantom/wrong-convention filename failures
- Finding [1]: `brand-brand-schema.md` — doubled prefix typo
- Finding [4]: all 13 Leonardo module references used underscore/PascalCase after files were renamed to hyphen/lowercase
- Combined effect: two of three framework contributions (COS and Leonardo) silently absent from every session
- Both caught only by the Adversarial Critic's explicit filesystem glob verification
- Both were syntactically valid strings — invisible to narrative review of the orchestrator

---

## Implementation Checklist

Add to Step 6 (Verification) checklist:

```
[ ] For every filename in CLAUDE.md / orchestrator:
    - Glob match against bundle/ directory
    - Zero matches = BLOCKING — fix before marking complete
[ ] Search all references for doubled-prefix pattern (e.g., brand-brand-, kf-kf-)
[ ] Confirm all referenced files use consistent convention (lowercase-hyphen)
```

---

## Reuse Context

Reference this entry when:
- Completing any bundle emit step before commit or upload
- Adding a verification checklist to a new composition project
- The check is fast enough (~1 minute) that skipping it is never justified
- Any environment where the orchestrator and bundle files may be authored in different sessions or chain steps — which is the normal condition, not the exception
