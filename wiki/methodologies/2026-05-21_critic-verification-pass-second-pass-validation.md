---
title: Critic verification pass — run KF Critic AGAIN on the revisions, not just on the draft
source_mode: critic
novelty_type: new_pattern
grounding_score: 0.75
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-21
domain: strategy
topic: prioritization
tags: quality-gate, orchestration, adversarial, empirical
related_entries:
  - methodologies/2026-05-13_critic-triage-routing-strategist-vs-defer-doc.md
  - methodologies/2026-05-20_propagation-gap-addenda-propose-downstream-changes-that-dont-execute.md
  - methodologies/2026-05-18_polish-as-blocker-drift-explicit-ship-gate.md
---

# Critic verification pass — run KF Critic AGAIN on the revisions, not just on the draft

## What this is

A second KF Critic pass run AFTER the first pass's findings have been closed via revisions. Purpose: verify the closures actually closed substantively (not cosmetically), catch new issues introduced by the revisions, and validate cross-doc propagation.

Most critic-driven workflows treat closure as terminal: critic finds → builder fixes → done. The verification pass adds an explicit "did the fix work, and did it introduce anything new?" step before declaring the artifact founder/owner/stakeholder-approval-ready.

## When to run it

- Whenever a critic pass produced **3+ Critical or High findings** that required structural revisions (not just typo fixes)
- Whenever revisions touched **3+ files** or introduced new architectural patterns
- Whenever the artifact is **production-bound** (real spend, real users, real external commitments)
- Whenever the team's pattern history shows **prior-fix regression** (a previous fix later broke under load — verification catches the regression class proactively)

Skip it when:
- All critic findings were Low/cosmetic
- Revisions were single-file localized edits
- Artifact is exploratory / discussion-only / not committed to durable form

## How to structure the verification-pass brief

Spawn the verification critic with explicit instructions to check, per finding:

1. **Closure is real, not cosmetic.** Did the edit change the operational meaning, or just add a "see XYZ" cross-reference without substance?
2. **Closure is propagated everywhere it should be.** Half-closures (fix in one doc but not the others that mirror it) are common failure modes.
3. **Closure didn't introduce a NEW bug.** Did the rewording open a new gap, contradict an existing rule, or create a new ambiguity?
4. **Cross-references are valid.** If §X cites §Y, does §Y actually exist and contain what §X claims?
5. **Platform-behavior claims survive verification.** Apply the adversarial-testing lens HARD again — re-verify any claims introduced during revision.

Plus: scan for regression of prior critic fixes (in earlier artifacts touched by this session) and for new platform-behavior claims that need verification.

## Output structure (what to expect from the verification critic)

- Per finding: closed-substantively / closed-cosmetically / partial / regressed / new-issue-introduced
- New findings introduced by the revisions (typically Medium/Low, but sometimes Critical if a revision broke something)
- "If you fix only N things" prioritization for any new findings
- Closure-summary table: original-closed / original-deferred / new-introduced / regressions

## Grounding from the 5SB FB Ads session

The May 2026 5SB paid-ads project ran this on the FB strategy after closing 10 of 12 original critic findings in v0.2/v0.3/v0.4:

- **10/10 non-deferred original findings verified substantively closed** (not cosmetic)
- **4 new findings introduced** (2 Medium, 2 Low) — none regressions
- **The 4th new finding (F1) was the third recurrence** of an adversarial-testing failure pattern — the verification pass caught a precise-sounding claim ("Meta resets learning phase whenever budget changes exceed 20%") that wasn't in Meta's documentation as a fixed rule
- **All 4 new findings closed in a v0.5 pass** — total close-out cycle: critic → 3 revision passes → verification critic → 1 revision pass

Without the verification pass, the v0.4 state would have been declared "founder-approval-ready" with three minor flaws in the artifact that would have surfaced later as operational confusion.

## Why this is worth the cost

A verification pass costs ~60-80% of the original critic pass (less work because closures are usually cleaner than initial drafts). In exchange:

- Catches cosmetic vs substantive closures before the artifact goes live
- Catches new issues introduced by the revisions (regression class)
- Validates cross-doc propagation explicitly (the most common half-closure failure mode)
- Provides a clean go/no-go signal: "verified founder-approval-ready" vs "more work needed"

The alternative — declaring done after the first close-out cycle — defers the discovery of those issues to operational use, where the cost of finding them is much higher.

## When NOT to run a verification pass

- Single-file Low-severity fixes (overhead > value)
- Same-day re-revisions when the artifact is still in flux
- Pure-judgment artifacts where critic findings are taste-level, not bug-level

## Related wiki entries

- [[platform-behavior-verification-discipline]] — the adversarial-testing discipline this pass enforces hardest (not yet a wiki entry; treat as concept-tag)
- Any KF Orchestrator entries on mode chains (Strategist → Builder → Critic → Critic-verification → Builder is the validated 5-step chain for production-bound complex artifacts)

## When This Applies

- Multi-pass critic workflows where early passes produced structural findings
- Artifacts spanning multiple files or phases
- Artifacts with external commitments (spend, users, SLAs)
- Artifacts where regression history exists

## When This Does NOT Apply

- Single-pass cosmetic fixes
- Isolated single-file changes
- Low-stakes exploratory work

## Source Context

Extracted from the 5sb-paid-ads-2026-05-21-fb-workstream session, where a second critic pass on Facebook ads strategy revisions validated closure quality and caught platform-behavior claim drift that the first-pass closure had masked. Pattern emerged as distinct, reusable, and high-value for any multi-stage critic-driven workflow targeting production readiness.
