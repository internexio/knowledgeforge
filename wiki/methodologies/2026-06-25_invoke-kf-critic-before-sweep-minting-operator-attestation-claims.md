---
title: Invoke kf-critic before any sweep work that mints operator-attestation claims at scale
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.75
staleness_risk: stable
importance: 3
pinned: false
created: 2026-06-25
domain: methodologies
topic: quality-gate
tags: [adversarial, quality-gate, mode-activation, chain, empirical]
provenance:
  source_mode: critic
related_entries:
  - methodologies/2026-05-21_critic-verification-pass-second-pass-validation.md
  - methodologies/2026-05-13_critic-triage-routing-strategist-vs-defer-doc.md
  - methodologies/2026-05-15_pre-emptive-scope-sweep-downstream-verdict.md
  - methodologies/2026-05-22_adversarial-critic-convergence-trajectory-category-per-pass.md
---

# Invoke kf-critic before any sweep work that mints operator-attestation claims at scale

## The heuristic

Before launching a sweep that will **mint, modify, or distribute claims the operator owns the truth of**, across N items (typically N ≥ 10), proactively invoke `kf-critic` on the planned framing — BEFORE the sweep script runs and BEFORE the commit. This is distinct from end-of-work critic review (the existing pattern). The trigger is the *type* of claim being minted, not the size of the diff.

## What counts as "operator-truth"

Claims that map to a verifiable real-world fact only the operator can confirm:

- **Authorship** — `Article.author`, editor, reviewer
- **Provenance** — creator, contributor, hasPart-author
- **Attribution** — E-E-A-T credentials, byline
- **Affiliation** — `worksFor`, `affiliation`, `memberOf`
- **Endorsement** — `Review.author`, citation, rated-by
- **Identity** — `sameAs` links — claiming X is the same entity as Y
- Any schema field that maps to a verifiable real-world fact

These are distinct from mechanical sweeps (rename a field, reformat blocks) which carry no attestation surface — pre-sweep critic adds no signal there.

## Cost asymmetry that makes pre-sweep critic high-leverage

| Side | Cost |
|---|---|
| Pre-sweep critic review | **Bounded.** ~3–5 min reading the framing, 10 findings written down. |
| Wrong-attestation cleanup after sweep ships | **Unbounded.** Every affected page may need surgical revision. Validators flag the error. Google's E-E-A-T validation downgrades the site for the rotation cycle (days-to-weeks of signal recovery even after fix). For attestations that already trained AI engines, the wrong claim persists in their next crawl/index. |

## How to invoke

Surface the planned scope + framing to `kf-critic` with the question form:

> "Review the proposed audit/sweep framing for [scope description]. The planned schema/attestation pattern is [X]. Critique:
> - Is the audit method extracting the operator-private data the bead specifies?
> - Are the schema options the full set, or is a real pattern missing?
> - Are the risk asymmetries surfaced explicitly to the operator before they choose?
> - Is the agent doing the operator's job?"

## What kf-critic catches well (vs. solo)

- **Spec deviation** — the bead said X per-item; the agent is doing X per-cluster.
- **Missing schema options** — the 3 options offered exclude a 4th that's actually the right call (e.g., `editor=` for AI-drafted-then-edited content).
- **Coarseness that defeats the bead's intent** — binary where the bead said gradient.
- **Self-shadowing** — the agent inferring data the operator was supposed to provide.

## When NOT to invoke pre-sweep critic

- **Mechanical refactor sweeps with no attestation surface** — rename a field, reformat blocks. Critic adds no signal.
- **Sweeps where the operator has already specified per-item truth** — e.g., "ship to these 22 pages I listed." Operator private knowledge is already extracted.
- **Single-item changes.** The cost-asymmetry math doesn't apply at N=1.

## Practical workflow

1. Draft sweep framing.
2. Surface to operator: "About to launch sweep. Before I do, want me to invoke `/kf-critic` on the framing?" (Operator can accept or decline.)
3. If accepted, run `kf-critic` with explicit context (planned scope, planned schema options, planned UX).
4. Apply critic findings: revise framing where needed.
5. Re-surface to operator with revised framing.
6. Execute.

## Grounding

`[project] 2026-06-25 cos-mk2l`. Operator invoked `/kf-5.1-backup` review this step at the threshold of a 74-page schema attestation sweep. Critic surfaced 10 findings; #1, #2, and #3 were structural enough to require **restart** (not adjustment) of the audit framing. Restart yielded a per-page checklist UX that preserved the bead's intent.

Estimated downstream cost averted:

- Re-applying 74 page-level schema changes
- Re-pushing through two CI cycles (~26 min CI alone)
- Re-verification on prod
- Total: ~1–2 hours engineering + reputation-risk reduction from not shipping wrong attestations to AI engines that train on them

## Adoption signal

When a future bead/sweep has BOTH

- (a) N ≥ 10 attestation-surface items, AND
- (b) operator-private knowledge as the truth source,

the agent should **proactively offer a kf-critic invocation BEFORE scripting the sweep** — not just at end-of-work review.

## Distinct from related entries

- `methodologies/2026-05-21_critic-verification-pass-second-pass-validation.md` — that pattern runs Critic AGAIN on the revisions (post-revision verification). This pattern runs Critic BEFORE the sweep launches, gating mutation at all (pre-mutation gate).
- `methodologies/2026-05-15_pre-emptive-scope-sweep-downstream-verdict.md` — that sweep reclassifies downstream work after a verdict. This entry is about preventing the sweep itself from minting wrong claims.
- `methodologies/2026-05-22_adversarial-critic-convergence-trajectory-category-per-pass.md` — that describes what critic catches across multiple passes. This entry specifies a single trigger heuristic for *when* to invoke a pre-mutation pass.
