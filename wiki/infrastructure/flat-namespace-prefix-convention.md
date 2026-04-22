# Flat-Namespace Prefix Convention for Subdirectory-Free Environments

```yaml
metadata:
  source_mode: synthesizer
  source_session: redacted
  created: "2026-04-21T00:00:00Z"
  date: "2026-04-21"
  confidence: 0.92
  grounding_score: 0.92
  grounding_source: "VisionForge Unified composition chain. 13 wrong Leonardo filenames in CLAUDE.md (Sev 1 finding [4]) and doubled-prefix typo brand-brand-schema.md (Sev 1 finding [1]) both traced directly to retroactive renaming under flat-file constraint discovered late. VisionForge CLAUDE.md carries bolded warning added reactively."
  novelty_type: transferable_framework
  staleness_risk: stable
  importance: 4
  pinned: false
  accreted_in: "6.5"
  related:
    - wiki/orchestration/adversarial-filename-audit.md
    - wiki/orchestration/multi-framework-cp-composition.md
    - modules/02_builder.md
```

---

## Pattern

When deploying a multi-framework knowledge bundle to an environment that does not support subdirectories (Claude Projects, flat vector stores, S3-backed knowledge bases) with 50+ files from 3+ source namespaces:

**Establish the full prefix table before any files are named, at project inception. Lock it in the project instructions. Apply without exception.**

Recommended structure:
- One prefix per source framework: `kf-`, `cos-`, `leo-`
- One prefix per functional category: `wf-`, `plat-`, `brand-`, `ref-`
- Apply category prefix to net-new gap modules (no single source framework owns them)
- Never nest prefixes: `brand-schema.md`, not `brand-kf-schema.md`

**Lint rule:** Search all file references for filenames starting with the same prefix token twice (`brand-brand-`, `kf-kf-`). This catches the doubled-prefix typo class. Add this to the Adversarial Critic checklist.

**Convention rule:** Enforce lowercase-hyphenated filenames from day one. Mixed conventions (underscore/PascalCase in some files) guarantee orchestrator references will drift. When files are renamed retroactively, orchestrator references miss the rename.

---

## Anti-Pattern — "Natural Naming, Subdirectories Later"

Name files naturally and plan to organize via subdirectories in a future deployment.

**What breaks:** VisionForge designed around subdirectories (`kf/`, `cos/`, `leo/`, `workflows/`) before the flat-file CP constraint was discovered. Retroactive renaming under time pressure produced:
- 13 wrong Leonardo filenames in the orchestrator: `leo-L01_Campaign_Context.md` (underscore/PascalCase) instead of `leo-L01-campaign-context.md` (Sev 1 finding [4])
- Doubled-prefix typo: `brand-brand-schema.md` (Sev 1 finding [1])

Both are syntactically valid strings invisible to narrative review. Both require filesystem verification to catch. Both silently prevent entire framework modules from loading — no error raised, pipeline appears to run.

**Evidence of reactive addition:** VisionForge CLAUDE.md carries the constraint as a bolded warning (`⚠️ FLAT FILE ARCHITECTURE:`) — evidence it was added after naming had already begun.

---

## Evidence from VisionForge

- Sev 1 findings [1] and [4] are both phantom/wrong-convention filename failures
- Combined: two of three framework contributions silently absent from every session
- Both caught only by the Adversarial Critic's explicit filesystem glob verification
- The `⚠️ FLAT FILE ARCHITECTURE:` warning in CLAUDE.md is a post-hoc addition — the convention was not established at project inception

---

## Reuse Context

Reference this entry when:
- Starting any CP bundle project with 3+ source frameworks
- Evaluating whether to "just use subdirectories and rename later" — the answer is no
- Adding the doubled-prefix lint check to an Adversarial Critic checklist
- Claude Projects specifically: flat-file constraint is a stable platform characteristic, guaranteed to apply to every CP bundle deployment
