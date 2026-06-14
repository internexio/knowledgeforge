---
title: Bootstrap divergence is INTENTIONAL on static-to-compiled promotions — document, don't fix
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: stable
importance: 4
created: 2026-06-14
domain: compiler
topic: ci-cd
tags: [empirical, deployment, packaging]
related_entries:
  - compiler/2026-06-10_extract-section-cc-marker-stop-condition-over-extraction.md
  - methodologies/2026-06-10_kf-semver-three-surfaces-module-system-binding.md
pinned: false
---

# Bootstrap Divergence is Intentional on Static-to-Compiled Promotion

## Problem Shape

When promoting a hand-authored artifact (e.g., `cc/.claude/agents/X.md`) into a compiler-emitted artifact (source body lives in `core/modules/`, compiler writes to cc), the FIRST `--check-divergence` after merge will report exactly one divergence — even when the team intended "byte-for-byte" body copy. This looks like a defect, but it's structural and correct.

## Why It Happens

The canonical body in core adds something the existing cc copy lacks:

1. A new clause the team deliberately included as part of the promotion (e.g., an untrusted-input boundary added to the canonical source as part of SPEC 1's hardening).
2. Compiler transformations the source didn't go through: `inject_toc` adds a section TOC, `add_compile_header` adds a sentinel comment.
3. The original hand-authored file may have minor formatting drift (trailing whitespace, line endings) that the compiler normalizes.

The cc copy was hand-curated; the compiled output is generated. They differ by the diff between "what the human wrote" and "what the compiler produces from canonical source". That diff is the deliberate change.

## Pattern (resolution)

1. In the promotion PR description, **explicitly call out the expected divergence**. Format:
   > Expected post-merge bootstrap divergence on `cc/.claude/agents/X.md` — canonical Module N body has Y; cc copy does not. One-time hand-back-port required: delete the cc file, re-compile, file regenerates with canonical body.
2. After merging the core promotion PR, run the one-time back-port: in the cc repo, delete the hand-authored file → re-run `kf-compile --target claude-code` → the file regenerates from canonical source → commit cc-side as "bootstrap completion". From that commit onward, `--check-divergence` reports zero divergences.
3. Add `check-divergence` to CI on cc so future hand-edits are caught fast.

## When This Applies

- Static artifacts (hand-maintained MD/YAML/JSON) being promoted to compiler-emitted artifacts
- The compiler applies any transformation (header injection, TOC, normalization) to the output
- The canonical source intentionally adds content the existing artifact lacks
- Multi-repo "source → derived" pipelines where the derived artifact pre-existed

## When This Does NOT Apply

- Pure code generation where no manual artifact pre-existed
- Compiler with no transformations (raw file copy + nothing else)
- Renaming-only promotion where body is unchanged
- Subsequent re-compiles after the one-time back-port (those should be zero-divergence)

## Grounding

KF-core SPEC 1 promotion (2026-06-14) anticipated this and documented it in the spec: SPEC 4's knowledge-librarian promotion saw the TOC-injection version of it (195 → 200 lines). SPEC 1's adversarial-critic promotion saw both clause-addition AND TOC-injection (106 → 120 lines). Both back-ports were absorbed by the cc compile-pipeline GH Actions workflow on the next core push.

## Source Context

Without explicit anticipation, the first `--check-divergence` failure after a promotion looks like a defect, and the team either (a) chases a non-existent bug or (b) papers over it by skipping divergence-checking. Naming the pattern lets the team treat it as a deliberate one-time step.
