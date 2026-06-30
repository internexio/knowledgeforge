---
title: Deterministic scan before claiming refactor/audit-doc beads
source_mode: kf-strategist, direct
novelty_type: reusable_diagnostic, transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-26
tags: methodology, refactoring, code-review, audits, bead-management, verification, anti-rework
related_entries:
  - methodologies/2026-05-13_verify-audit-claims-before-designing-fix.md
  - methodologies/2026-05-23_beads-disk-reconciliation-discipline.md
  - architecture/2026-05-18_bead-as-context-anchor-deferred-runbooks.md
domain: methodologies
topic: verification
---

# Deterministic Scan Before Claiming Refactor/Audit-Doc Beads

## The Rule

Any bead, task, or work item filed against an audit document, code review, refactor backlog, or third-party recommendation that is **more than 7 days old** MUST begin with a 5-15 minute deterministic scan of current source code before claiming the work or starting implementation.

The scan tests one question: **does the structure described in the bead still need to be built, or has intervening work made it partially/fully obsolete?**

Trust the bead's *intent* (what the user wanted at filing time). Verify its *scope* against current reality.

## Why It Matters

Code-review docs, audit findings, and refactor backlogs all describe **the codebase at a moment in time**. When the codebase is actively refactored — security PRs landing, structural cleanup commits, parallel work — the doc starts decaying as soon as it's written. By 7-14 days out, items that were "high-priority TODO" at audit time may have shipped via unrelated work and the doc has no way to know.

Trusting a stale audit doc without verification produces two failure modes:
1. **Redundant refactor work** — building something that already exists. Wasted hours, churn in code-review.
2. **False-positive "done" closures** — closing a bead because surface evidence says "module exists" without verifying the duplication it was supposed to eliminate is actually gone.

The first failure is obvious and recoverable. The second is more subtle: it pollutes the bead queue with confidence the team hasn't earned, and the residual duplication keeps producing the bugs the audit was supposed to prevent.

## The Pattern in Practice

When a bead description says "extract X into shared module" or "build service Y" or "consolidate duplicated Z":

1. **Existence check first** — does the proposed target file/module already exist? (`find`, `ls`, `git log`)
2. **If it exists, verify it's actually used** — grep for imports/calls from the locations that were supposed to consume it
3. **Verify the original duplication is gone** — grep for the patterns the audit said were duplicated; count call sites
4. **Identify the smallest falsifying test per claim** (see subordinate technique below)

This takes 5-15 minutes per sub-bead. If the scan reveals the work is substantially done, the bead can close with a reason citing the verification. If partial work remains, the bead can be **rescoped to honest remaining work** — preserving the original intent while reflecting reality.

## Subordinate Technique: Smallest Falsifying Test Per Claim

When closing a "claimed done" bead, identify the smallest grep/wc/read operation that would falsify "done" if the claim is wrong. Examples that worked in the source session:

| Bead claim | Smallest falsifying test |
|--|--|
| "Frontend factory consolidates all BC/EC API calls" | `grep -cE 'fetch\(|axios\.' bc/api.ts ec/api.ts` — if either >0, factory is partial |
| "Analyzer base class owns Anthropic client; 8 analyzers inherit" | `grep -c 'self.client.messages' analyzers/*.py` — if any concrete analyzer >0, duplication remains |
| "Central rate-limit service replaces inline implementations" | Read the service file; grep for the old patterns the audit said were inline (`_check_rate_limit` definitions) across all consumer files |

The test must be **deterministic** (same input → same output), **cheap** (under 60s), and **falsifying** (a "fail" result definitively means the claim is wrong, not "maybe wrong").

## When It Does NOT Apply

- Beads filed **within the last 7 days** against a fresh audit — the doc is still current enough to trust at face value
- Beads filed against **stable specifications** (e.g., a public API contract, a regulatory requirement) — the spec doesn't drift the same way
- **First-build greenfield work** — there's nothing to scan against
- Beads where the user explicitly says "I want this even if something similar exists" — the goal isn't deduplication, it's a specific implementation

## When It Pays Off Most

- Multi-week security/structure audits that produce 30+ findings — high probability that intervening commits have shipped subsets
- Refactor backlogs that share scope with active feature work — features often incidentally close audit findings
- Sessions opening with "let's execute on [epic filed N days ago]" — N > 7 is the trigger

## Concrete Grounding (the source session)

[project] session 2026-05-26: User asked "execute on cos-0od" — an epic filed that same day, but referencing CODE_REVIEW_2026-05-12.md (14 days old). Before claiming work I scanned the 4 sub-beads:

- cos-cee (rate-limit central service): central service already existed at `app/core/rate_limit.py` (468 LOC + 471 LOC tests). 6 consumer endpoints migrated. The Theme B work was substantially done.
- cos-h0x (frontend factory): `lib/featureApi.ts` existed; BC/EC both imported and called it. 0 raw HTTP bypasses.
- cos-3gw (analyzer base): `services/analyzers/base.py` (340 LOC) existed; all 8 concrete analyzers inherited. 0 direct `self.client.messages` calls.
- cos-bzi (app/core extracts): 4/5 modules existed and were imported. One residual (DUP-M2) was honestly open.

Total scan time: ~20 min. Work avoided: estimated 3-5 days of redundant refactor. The single open straggler (cos-bzi DUP-M2) was correctly preserved and rescoped.

The reusable rule was codified at the top of the original audit doc as an annotation, so future sessions claiming Week 3/Week 4 epics from the same doc inherit the discipline.

## Cross-References

Pairs with [[verify-audit-claims-before-designing-fix]] (which focuses on pre-design verification of audit structural claims) and general [[beads-disk-reconciliation-discipline]] patterns. The "smallest falsifying test" technique is closely related to [[deterministic-first-debugging]] (verify before invoking LLM judgment).

## Source Context

Discovered during cos-week2-stale-audit-2026-05-26 session. User opened an epic (cos-0od) that referenced a 14-day-old code review document. Rather than immediately implement the prescribed refactors, I ran a deterministic scan on each sub-bead claim and found 3/4 were substantially complete via intervening work. The scan surfaced the 7-day rule as a reusable pattern and the "smallest falsifying test" technique as a subordinate diagnostic. Scope was rescoped from "full Week 2 epic" to "one residual straggler (DUP-M2)" after verification, saving 3-5 days of redundant refactor effort.
