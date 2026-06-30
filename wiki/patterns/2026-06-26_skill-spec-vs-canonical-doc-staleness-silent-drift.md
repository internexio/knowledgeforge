---
title: Skill-spec vs canonical-doc staleness as a recurring class of silent drift
source_mode: builder
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.7
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-26
domain: patterns
topic: skill-design
tags: skill-design, agent-workflow, drift-detection, positioning, version-sync, documentation-pattern
related_entries:
  - infrastructure/2026-05-12_vendoring-drift-detection.md
  - patterns/2026-05-18_markdown-binary-artifact-drift-independent-editing.md
  - infrastructure/2026-05-25_hook-installed-vs-source-drift-direct-edits.md
  - integration/2026-06-12_embedding-skill-intent-into-runtime-prompts.md
  - patterns/2026-05-22_spec-to-implementation-gap-distinct-review-pass.md
---

# Skill-spec vs canonical-doc staleness as a recurring class of silent drift

## Pattern

When a skill encodes domain knowledge that has its own versioned canonical source-of-truth (positioning locks, schemas, configs, branding manifestos, anti-pattern lists), the skill silently drifts when the canonical source updates and no propagation mechanism exists. The skill keeps running and producing output that contradicts the new canonical state.

## Diagnostic surface

The drift becomes visible when an agent invokes the skill live AND reads the canonical doc as part of the workflow. The discrepancy surfaces as contradictory guidance — text in the skill spec opposes text in the canonical doc.

Example (observed session 2026-06-26):
- Project-local skill `/social-post` at `.claude/skills/social-cross-post/SKILL.md` contained the line "COS is NOT a generator. Frame as measurement, not authoring."
- Positioning lock at `wiki/positioning/CURRENT.md` had advanced to v1.0.4 (ratified 2026-06-21), which establishes COS as **dual-surface**: a chat surface that GENERATES copy constrained by Big Five coverage, AND an analyzer surface that scores existing copy.
- The skill's anti-positioning guardrails would have refused legitimate v1.0.4 content if a future invocation generated content that mentioned the chat-generation surface.

## Why this drift is sticky

- The skill spec is read every invocation; the canonical doc may not be unless the skill spec mandates it.
- Versions of the canonical doc don't auto-trigger skill updates.
- The skill's anti-positioning / refusal logic becomes a **source of false positives** against now-valid content.
- Operators who didn't author the skill are unlikely to notice until the agent produces output that reads weirdly conservative or refuses valid requests.
- The longer the gap between canonical-doc revision and skill audit, the more the skill drift compounds with downstream artifacts (project CLAUDE.md, related skills, integration modules) that also encode the same canonical state.

## Mitigation pattern

1. **Make the skill READ the canonical doc as Step 1 of its workflow.** Don't bake canonical content into the skill spec. The skill becomes a workflow harness; the canonical doc remains the source of truth.

2. **Pin a version tag in the skill** (e.g., `synced_to: positioning_lock_v1.0.4`) in the skill's YAML frontmatter or top-of-file metadata. Future agents can compare the skill's pinned version against the canonical doc's current version and flag drift before invocation.

3. **Surface drift during live invocations.** When the agent reads BOTH the skill and the canonical doc, it should explicitly compare and flag mismatches to the operator BEFORE generating output. Don't silently prefer either source — let the operator decide.

4. **File a bead/issue for downstream artifacts.** When you discover a stale skill, the same canonical content likely appears in N other places (project CLAUDE.md, sibling skills, integration specs). Track downstream sync as a separate issue so it doesn't get lost.

## When it applies

- Any skill that encodes positioning, branding, schemas, anti-patterns, allowed values, taxonomies, or any versioned domain truth.
- Multi-artifact projects where the same canonical truth appears in multiple files.
- Long-lived skills that get re-invoked across many sessions and many canonical-doc revisions.

## When it does NOT apply

- Pure-mechanism skills ("how to format a URL slug", "validate a JSON file") that don't reference domain truth.
- Skills where the skill IS the canonical doc (no upstream version exists).
- One-shot or single-session skills that won't outlive the canonical state.

## Relationship to existing drift patterns

This pattern is a sibling to several existing drift entries — each isolates a different copy-vs-source-of-truth failure mode:

- [[infrastructure/2026-05-12_vendoring-drift-detection]] — vendored content (a literal copy of upstream) drifts when upstream evolves. The fix is CI diff against upstream or submodule pointer. The candidate pattern differs: the skill is NOT a copy of the canonical doc — it's an independently-authored harness that bakes in domain claims that HAPPEN to be sourced from a versioned canonical doc. There's no upstream to diff against; the drift is semantic, not textual.
- [[patterns/2026-05-18_markdown-binary-artifact-drift-independent-editing]] — markdown source and exported binary diverge when both are edited. The candidate differs: there's no derivation relationship — the skill was never "generated from" the canonical doc.
- [[infrastructure/2026-05-25_hook-installed-vs-source-drift-direct-edits]] — installed copy vs source-of-truth copy of the same file drift. The candidate differs: same conceptual structure (one copy goes stale relative to another), but in the candidate the two artifacts have DIFFERENT shapes (skill spec encodes domain claims as guardrails; canonical doc encodes them as positioning facts) — you can't just `cp` one over the other.
- [[integration/2026-06-12_embedding-skill-intent-into-runtime-prompts]] — uses prompt-version-pinning to make rule drift visible when CC-skill content is embedded into a non-CC runtime prompt. The candidate generalizes the same `synced_to: version` pinning technique to the in-CC case where the skill itself encodes domain claims from a versioned source.
- [[patterns/2026-05-22_spec-to-implementation-gap-distinct-review-pass]] — spec is consistent but code doesn't implement it. The candidate is the inverse: the canonical doc (spec-like) has advanced but the skill (implementation-like) still reflects an earlier version.

## Grounding

Observed during session 2026-06-26 when `/social-post` was first invoked live on a real source post in the client-project project. The skill spec referenced `kp-003` ("AI content optimizer / generator") as an active anti-position; that anti-position was retired in lock v1.0.4 (2026-06-21). The skill was synced in-session (4 edits to anti-positioning sections, dual-surface framing added). A downstream bead `gtm-3me` (P2) was filed for the project CLAUDE.md guardrail #1, which carries the same pre-v1.0.4 framing. Skill sync committed at `d41762b`.

## Source Context

Project-local skill `/social-post` in `~/Scripts/client-project/.claude/skills/social-cross-post/SKILL.md` had been authored before the positioning lock advanced from v1.0.3 to v1.0.4 on 2026-06-21 (commit retiring `kp-003`). The first live invocation of the skill in a subsequent session was the surface where drift became visible — the agent read both the skill spec and `wiki/positioning/CURRENT.md` as part of the standard workflow, and the contradiction became apparent. Without the workflow step that reads the canonical doc, the skill would have continued generating output under retired guardrails until something downstream broke (a refusal of valid content, an operator catching the inconsistency, or a public artifact that contradicted the current public positioning).

The fact that the project CLAUDE.md (a SEPARATE artifact in the same project) ALSO carries the pre-v1.0.4 framing in its guardrail #1 confirms the compounding-drift claim in the pattern body: a single canonical-doc revision creates an N-artifact propagation problem, and the further from the canonical doc you get, the longer the lag before correction.
