---
title: Platform-behavior verification discipline — verify-with-date / heuristic-framed / cited
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 5
pinned: false
created: 2026-05-21
domain: methodologies
topic: validation
tags: methodology, validation, verification, quality-gate, platform-behavior, commitment-discipline
related_entries:
  - methodologies/2026-05-20_primary-source-vendor-guidance-reanchor.md
  - architecture/2026-05-20_platform-deprecation-architectural-intent-preservation.md
  - methodologies/2026-05-13_verify-audit-claims-before-designing-fix.md
---

# Platform-Behavior Verification Discipline

## What this is

A discipline for committing claims about external-platform behavior (paid-ad platforms, cloud APIs, ML infra, SaaS UIs, anything that changes outside our control) to durable artifacts. The rule: any quoted threshold, named feature, UI label, API endpoint, or deprecation-status claim in a committed doc must be EITHER:

1. **Verified** against current platform documentation with a verification date noted in-doc, OR
2. **Framed as industry heuristic** rather than platform-stated rule, OR
3. **Cited** from a source the reader can reach

If none applies, the claim is not safe to commit. Drafts and discussion notes can carry unverified claims; strategy docs, checklists, briefs, and anything an agent or partner may execute against must clear this bar.

## Three documented recurrences (the grounding)

In a single ~48-hour window in May 2026, a single project (5SB paid-ads) hit this failure mode three times:

| Instance | Date | Claim | What was wrong | How caught |
|----------|---|---|---|---|
| 1 | 2026-05-20 | Google Ads Catch-All + Conquest used `+keyword +keyword` Broad Match Modifier syntax | BMM was deprecated by Google in Feb 2021 and rolled into Phrase match — 5 years dead when the architecture was written | Founder caught during review |
| 2 | 2026-05-21 | Meta FB strategy Pillar 3 routed offline lead-quality signal through Meta's standalone Offline Conversions API | Meta retired the standalone Offline Conversions API on 2025-05-14, one year before the doc was drafted. UI still shows legacy upload paths in degraded mode (uploads visually succeed; signal doesn't reach optimizer) | KF Critic CC1 finding |
| 3 | 2026-05-21 | Same Meta FB strategy anti-list claimed "Meta resets learning phase whenever budget changes exceed 20%" | Widely cited in 2022–2024 vendor blogs but NOT Meta's stated policy — Meta documents "significant edits" without a fixed threshold | KF Critic verification pass (F1) |

Instance 1 explicitly committed the team to "verify platform claims before doc commit." Instance 2 appeared the next day. Instance 3 appeared hours after Instance 2 closed. The discipline reliably slipped under revision-workload pressure when verification felt optional.

## The rule (durable form)

For each platform-behavior claim entering a committed artifact, pick exactly one path:

### 1. Verified with date

Run a search against current platform docs (Meta Business Help Center, Google Ads Help, official changelogs/release notes) **AT TIME OF WRITING**. Note the verification date inline:

```
(verified against Meta CAPI docs 2026-05-21)
(verified against Google Ads Help — Broad Match Modifier section, 2026-05-21)
```

For cloud APIs, check:
- Official API reference or SDK docs
- Changelog or "Latest updates" section
- Provider's official blog (not third-party CDNs of docs)

### 2. Industry heuristic framing

If no platform documentation supports a precise claim but the directional advice is sound, frame as:

```
Industry heuristic is ~X — [Platform] does not publish a fixed number.
```

Keep the directional rule; drop the false precision. Example:

**Bad (unverified):** "Meta resets learning phase whenever budget changes exceed 20%"

**Good (heuristic-framed):** "Industry heuristic is that large budget swings (>20%) may reset learning — Meta documents 'significant edits' without a fixed threshold."

### 3. Cited

Link or name the source the reader can verify:

```
(Per Vendor Blog Post: [title], [URL], published [date])
(Per Meta for Developers changelog: [section], [date])
(Per conference talk: [speaker], [event], [date])
```

The reader must be able to reach the source. A URL, blog post title, or changelog section is acceptable. "Everyone knows this" is not.

## When the discipline binds hardest

- **During heavy revision workloads** — verification feels like "nice-to-have" friction
- **When closing other critic findings** — focus on the immediate fix can crowd out verification of new claims introduced by the fix
- **When the writer has prior-knowledge confidence** — the false sense of expertise from "I know how X works" is precisely when verification is most needed (because platforms change continuously)
- **When drafting under time pressure** — verify-with-date adds ~60 seconds per claim but saves hours of critic-revision cycles

These are the exact conditions when slippage occurs. Knowing the rule ≠ applying it under workload.

## When this does NOT apply

- **Internal-only doc claims about internal systems** — different decay profile; we control the source-of-truth
- **Discussion notes and drafts not yet committed** to durable artifacts
- **Pure-judgment claims** that don't reference platform behavior (style guidance, taste calls, strategic recommendations without platform-fact dependency)
- **Claims framed explicitly** as "as of [date], assumption — verify before depending" or equivalent

## Operational application

### 1. Before drafting

For each platform claim about to land in the doc, run a 60-second documentation search. Cheaper than a critic-found regression.

### 2. During critic passes

When an artifact contains 3+ paid-platform claims, spawn an explicit "platform-behavior verification" sweep in the critic brief. The 5SB project's v0.4 verification pass succeeded at catching F1 because the brief explicitly asked for it.

### 3. When a stale claim is caught

Fix the artifact AND log the instance to a project-level recurring-pattern table so future agents see the pattern, not just the individual fix.

### 4. Mid-revision new claims

Flag in the commit message for second-pair-of-eyes verification before merge.

## Why this is harder than it sounds

The discipline slipped **TWO TIMES in 24 hours AFTER being committed to explicitly**. Reasons:

- **Knowing-the-rule ≠ applying-it** under workload pressure
- **Verification of NEW claims gets crowded out** by verification of the artifact-being-fixed
- **Platform changes accumulate silently** — prior-knowledge confidence is the trap

The fix: codify as a **project-level checkable rule** in a persistent process-rule artifact, not as session memory. When a new instance appears (it will), add to the recurring-pattern table. Don't just fix the doc and move on.

## Future-instance protocol

When a fourth instance lands, add the row to the project's recurring-pattern table, refresh the discipline review date, and update the operational-application list if the new instance suggests a new mitigation step.

## Companion entries

- **`wiki/architecture/2026-05-20_platform-deprecation-architectural-intent-preservation.md`** — focuses on recognizing and porting deprecated platform features. This entry is the *prevention discipline*; that entry is the *response pattern* once a deprecation is discovered.
- **`wiki/methodologies/2026-05-20_primary-source-vendor-guidance-reanchor.md`** — focuses on hierarchies of evidence when vendor docs contradict industry consensus. This entry is the *commitment discipline*; that entry is the *interpretation framework* for conflicting vendor signals.
- **`wiki/methodologies/2026-05-13_verify-audit-claims-before-designing-fix.md`** — focuses on structural claims in code audits drifting out of sync with current code. Same impulse (verify before designing); different scale (code snapshot vs. external platform state).

## Source Context

Grounded in 5SB paid-ads campaign strategy development (2026-05-20 to 2026-05-21). Three separate platform-behavior claims entered committed docs without verification in a 24-hour window: Google Ads Broad Match Modifier syntax (5 years deprecated), Meta Offline Conversions API (1 year retired), and an unverified Meta learning-phase heuristic. Each instance was caught by different verification paths (founder review, critic pass, explicit verification sweep). The pattern of repeated slippage despite explicit awareness suggests this needs to be a persistent process rule, not a one-off session directive. This entry codifies the discipline so the next project with multi-platform dependencies (paid-search + FB + Google Cloud, etc.) can integrate it into their artifact-review gates.
