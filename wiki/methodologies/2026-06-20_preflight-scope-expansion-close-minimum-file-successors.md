---
title: Pre-flight scope expansion — close the in-scope minimum, file successors for the rest
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.75
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-20
domain: methodologies
topic: scope-management
tags: scope-management, accretion, classification, empirical, bead-tracking, project-management
related_entries:
  - methodologies/2026-05-15_pre-emptive-scope-sweep-downstream-verdict.md
  - methodologies/2026-05-18_reframe-stated-scope-to-actual-goal-strategist-heuristic.md
  - methodologies/2026-06-17_tracker-state-drift-at-session-boundary.md
  - methodologies/2026-06-09_read-bead-status-before-claiming-verify-explicit-deferral.md
---

# Pre-flight scope expansion — close the in-scope minimum, file successors for the rest

## The pattern
When a bead's pre-flight surfaces additional related work beyond the original framing, do NOT silently expand the bead. Instead:
1. Complete the in-scope minimum that the bead's framing actually closes.
2. File one or more successor beads for the additional surface area.
3. Record the predecessor → successor relationship in both bead descriptions and the closing commit message.

## Why this discipline
Silent scope expansion hides decision points from the operator. The original bead's framing reflects a priority decision; the expanded scope might have changed that priority. Splitting:
- Preserves the original bead's verifiable closure (closes what it actually said it would close).
- Gives the operator a chance to re-prioritize the expansion as its own bead with current information.
- Prevents one bead from accreting indefinite scope and becoming un-closeable.
- Produces clearer commit messages — "closes bead X; filed successors Y, Z for the discovered scope" is more honest than "closes bead X (also did Y, Z)."

## When this applies
- Bead pre-flight reveals additional related artifacts (files, vocab terms, modules) that share a domain with the bead's stated scope.
- Discovered surface area changes a priority, sequencing, or destination decision (cross-repo move, version bump rules, vocab churn).
- Operator was not in the room when the discovery happened.

## When it does NOT apply
- Surfaced work is trivially additive within the same execution pass and does NOT change any operator-visible decision (no priority change, no destination change, no sequence change).
- The bead's framing was explicitly placeholder/exploratory and the operator expected scope discovery.

## Concrete grounding
Session 2026-06-20, bead `knowledgeforge-core-a05`:
- Original framing: prune 5 SEO-flagged vocab topics from M23; ~5 entries affected.
- Pre-flight via kf-strategist mode discovered: (a) 7 entries (not 4) under the orphan `seo-strategy` domain, (b) 4 cross-domain referrers needing bridge pointers, (c) the destination repo (sem-tools) had uncommitted in-flight work.
- Decoupling: closed a05 with M23 vocab cleanup (the gating action that prevents new SEO accretion) in commit `b7108e5`; filed successor `-56c` for the file-relocation half (paused until destination is clean); filed successor `-sd3` for the EXPAND-side vocab additions (independent decision).
- Closing commit message referenced both successors explicitly.

## Useful indicator that you should split
Ask: "Does the discovered scope change any decision the operator already made?" If yes, split. If no, fold in.

## Relationship to neighboring patterns

- [[2026-05-15_pre-emptive-scope-sweep-downstream-verdict]] — covers the **multi-bead post-verdict** case (a locked strategic decision rescopes a queue of dependent beads). This entry covers the **single-bead pre-flight** case (one bead's discovery surfaces adjacent surface area). Both share the principle of not silently mutating tracker scope, but operate at different boundaries.
- [[2026-05-18_reframe-stated-scope-to-actual-goal-strategist-heuristic]] — reframes the goal upstream of execution; this entry handles the reverse, when goal is solid but scope inflates during pre-flight.
- [[2026-06-17_tracker-state-drift-at-session-boundary]] — about syncing artifacts back to the tracker. The successor-filing step here is one instance of that discipline applied at the point of discovery rather than session-end.
