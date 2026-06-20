---
title: Linters scoped to git's tracked-file set miss filesystem state — false-positive and false-negative orphan claims
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-06-20
domain: diagnostics
topic: intent-vs-execution
tags: empirical, metadata-filter, filesystem
related_entries:
  - diagnostics/2026-05-23_compile-pipelines-complete-tracked-work-invisibly.md
  - methodologies/2026-05-23_beads-disk-reconciliation-discipline.md
  - methodologies/2026-05-29_deterministic-first-debugging.md
---

# Linters Scoped to Git's Tracked-File Set Miss Filesystem State

## The Anti-Pattern

A lint/audit tool whose input domain is git's index (staged + tracked files) cannot, by construction, see the live filesystem. When the operator's mental model is "audit the wiki" but the tool's actual scope is "audit the tracked subset of the wiki," the two diverge silently — and the divergence shows up as false-positive defects (claims a target is missing when it exists) and false-negative defects (misses real problems on untracked files). Confidence scores from the linter don't separate the two failure modes, because the linter has no signal about what it can't see.

## Pattern Description

Any linter reading from `git ls-files`, the staged index, or a committed snapshot operates on a **subset** of the working tree. Files created in the same session but not yet committed are invisible. Two distinct failure modes follow:

- **Target tracked + exact slug match but linter emits orphan.** Cause: linter is reading from a stale git index or a different working tree than the live filesystem the operator inspects. The "missing" target exists but is not in the index snapshot the linter consumed.
- **Target untracked, only on disk.** The link points to a real file that exists but is git-invisible. The linter correctly reports "not in tracked set" but the operator reads that as "doesn't exist," and the orphan claim is a snapshot artifact, not a real defect.

The general shape: the linter's input domain is narrower than the user's mental model of the audit, and the gap is silent.

## When It Applies

- Pre-commit hooks reading staged-only state
- CI-side linters reading committed-only state
- Baked-proposal generators running against a git snapshot
- Cross-reference / orphan-link detectors operating on `git ls-files`
- Any audit tool whose results are compared against `find` / live-filesystem state by the operator

## When It Does NOT Apply

Linters that are **intentionally** git-aware are correct to use git scope. Examples:
- "Find merge conflict markers in tracked files"
- "Warn on uncommitted secrets" (staged scope is the right scope)
- "Block commits with TODO in changed files"

The question being asked is itself git-scoped, so the tool's input domain matches the user's mental model.

## Concrete Grounding (knowledgeforge-core wiki-orphan sweep, 2026-06-20)

The [project] wiki-linter ran 2026-06-20 02:00 PDT and emitted 8 baked-proposal orphan beads against knowledgeforge-core wiki. Working through the beads revealed **5/8 (62%) were false positives**: the target file existed on disk with an exact filename-slug match to the `[[wikilink]]`. Linter confidence scores (0.74–0.80) did not distinguish false from true positives.

The 3 true orphans shared a distinct signature: the wikilink slug was missing the date prefix that the target filename carries (e.g. `[[autouse-fake-stages-fixture-subprocess-pipeline-tests]]` vs target `2026-05-14_autouse-fake-stages-fixture-subprocess-pipeline-tests.md`). That shape is a structural mismatch the linter could detect deterministically.

**Evidence:**
- False positives (closed without edits): wiki-orphan beads `8ig`, `b24`, `ytn`, `drr`, `yg8` — closed in commit `5b83f22`
- True date-prefix-missing orphans (fixed and closed): `edh`, `v8i`, `iwv` — same commit
- Linter-side fix tracked at: [project] `lx5o`

## Detection

For each "X does not resolve" claim from a git-scoped linter:

1. **Live-filesystem check.** Run `find <root> -name "<slug>*"` against the working tree. If a file exists with matching slug, the linter is wrong about that instance — its index view is stale or out-of-tree.
2. **Source tracked-ness check.** Look at whether the **source** file (the one containing the wikilink) is itself git-tracked. If the source is untracked, the orphan claim may be a snapshot artifact even when the target genuinely doesn't exist yet — premature defect.
3. **Slug-shape check.** For true orphans, compare against sibling filenames. If a sibling exists with name `<DATE>_<missing_link_slug>`, the defect is a missing date prefix, not a missing file.

## Fix (Linter Side)

Two viable changes; defense in depth = both:

- **Re-verify each orphan target against the live filesystem before baking a proposal.** Drop any whose target slug matches a sibling file on disk. Cheap deterministic check.
- **Restrict orphan detection to source files that are themselves git-tracked.** Premature orphan claims on untracked sources are deferred until the source itself is committed. Eliminates the snapshot-artifact class.

## Bonus Signal: Missing-Date-Prefix Subclass

When the linter finds a wikilink slug that doesn't resolve but a sibling file slug equals `<DATE>_<missing_link_slug>`, the right output is a **fix suggestion** ("did you mean `[[2026-05-14_<slug>]]`?"), not a generic orphan defect. That subclass converts a defect into an actionable correction and removes a known source of operator noise.

## Diagnostic Move

When a tool reports defects and your spot-checks find them spurious:

1. **State the tool's actual input domain.** Is it the index? The staged set? The committed HEAD? `find` output? Confirm — don't assume.
2. **State the operator's mental model.** What set did the operator think was being audited?
3. **The gap between those two sets is where false positives and false negatives live.** Diagnose the gap before re-tuning thresholds or confidence weights.

## Related Patterns

- **Compile pipelines complete tracked work invisibly:** Mirror failure mode at a different layer — a pipeline acts on the tracked set and the operator sees only the output, never the gap. Same root: tool scope ≠ operator scope.
- **Beads disk-reconciliation discipline:** When tracker state and disk state diverge, reconcile to disk as ground truth. Generalizes here: when the linter index and disk diverge, disk is the audit answer.
- **Deterministic-first debugging:** A deterministic filesystem check (`find <slug>*`) beats LLM-judgement re-ranking of confidence scores every time.

## Source Context

knowledgeforge-core bead-sweep session, 2026-06-20. [project] wiki-linter false-positive rate hit 62% on a single run, traceable to git-index scope vs filesystem scope mismatch — not a tuning problem, a scope problem. Fix lives in the linter's input contract, not its confidence model.
