---
title: Split-by-blocking-axis — refactor monolithic tasks so framework parts ship while external blockers persist
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-12
domain: orchestration
topic: multi-stage-issue-workflow
tags: routing, classification, quality-gate, throughput
related_entries:
  - wiki/orchestration/2026-05-30_bead-tracker-workflow-pipeline-triage-decisions-build-deploy.md
  - wiki/orchestration/2026-05-30_preflight-cred-gap-detection-bead-build-halt-decompose.md
  - wiki/orchestration/2026-05-30_force-close-epic-deferred-child-pattern.md
  - wiki/infrastructure/2026-05-27_bd-cli-dependency-wiring-inversion-two-pass-pattern.md
  - wiki/methodologies/2026-05-18_reframe-stated-scope-to-actual-goal-strategist-heuristic.md
---

# Split-by-blocking-axis — refactor monolithic tasks so framework parts ship while external blockers persist

## The problem pattern

You have a task tracked as one bead/issue with multiple deliverables. Some deliverables are buildable today; others are blocked on an external dependency (API approval, vendor response, legal sign-off, partner integration). The whole bead reads as "blocked" until the external thing clears. Meanwhile, sibling beads that depend on the framework parts (not the external parts) are ALSO marked blocked — they wait for "the bead" to close, which can't close because of the external dep.

Net effect: a 2-week external wait blocks 6+ weeks of derivative work that could have moved in parallel.

## Concrete case from sem-tools-xcu

Before split:
- `sem-tools-svo` (monolithic): "Phase 1 review aggregator + LLM drafter + nightly sync"
  - Includes: schema migration, ReviewAdapter ABC, aggregator, drafter, CLI, cron — none of which need any external API
  - ALSO includes: `sem/reviews/gmb.py` real implementation against the v4 reviews API
  - Blocked by: `sem-tools-73z` (Google API allowlist reapply, 7-10 business day external review window)
- `sem-tools-1jw` (Facebook via Chrome MCP) — blocked by svo
- `sem-tools-9ay` (Yelp via Chrome MCP) — blocked by svo

The 1jw and 9ay beads have their OWN platform fetchers via Chrome MCP — they don't need any Google API. But they were blocked by svo because svo carried the framework they ride on.

## The split

1. Identify the BLOCKING AXIS: what's the external thing that's slow? (Google API approval = sem-tools-73z, 7-10 days)
2. Identify which deliverables in the monolithic bead actually need the external dep:
   - Real gmb.py impl → needs API approval, blocked
   - Schema, ABC, aggregator, drafter, CLI, cron, restaurant_facts seed, prompts → don't need it
3. Create two new beads along the axis:
   - "Bones": the unblocked deliverables + a STUB for the blocked part
   - "Adapter": the blocked deliverable, depending on the blocker AND the bones
4. Re-wire downstream deps from the old monolithic bead to the BONES bead (since downstream needed the framework, not the external thing).
5. Supersede the old bead with the bones bead.

After split:
- `sem-tools-xcu` (BONES): all the framework + stub gmb.py — buildable today, no external blockers
- `sem-tools-017` (gmb adapter): real v4 fetcher — blocked by 73z AND xcu
- `sem-tools-1jw` (FB Chrome MCP): re-wired to depend on xcu (not the old svo or 017)
- `sem-tools-9ay` (Yelp Chrome MCP): re-wired to depend on xcu

Result: xcu shipped in 7 commits during the 73z wait window. 1jw and 9ay unblocked the moment xcu landed. The Google review timeline became orthogonal to the rest of the work.

## When this pattern applies

- A monolithic task has multiple deliverables.
- AT LEAST ONE deliverable has an external/slow blocker (vendor, legal, partner, approval queue).
- AT LEAST ONE deliverable does NOT have that blocker.
- Sibling/downstream tasks depend on the un-blocked parts.

## When this pattern does NOT apply (or is overkill)

- Monolithic task where the external blocker affects ALL deliverables (e.g., "build feature X that needs the new database schema" — if every deliverable needs the schema, splitting doesn't help).
- Small task where the framework parts are <0.5 day of work. Overhead of two new beads + dep re-wire exceeds the parallelism win.
- Strong coupling between the framework and the external piece — if you can't write a stub adapter without knowing the real API's shape, you don't have a clean split.

## Concrete execution (bd CLI commands)

```bash
# 1. Read the original so context isn't lost in the split
bd show sem-tools-svo > /tmp/svo-original.md

# 2. Create the two new beads
bd create --title="Phase 1 BONES: framework + stub adapter" \
  --description="..." --type=task --priority=2
# → sem-tools-xcu

bd create --title="Phase 1 GMB adapter: real v4 fetcher" \
  --description="..." --type=task --priority=2
# → sem-tools-017

# 3. Wire new deps
bd dep add sem-tools-017 sem-tools-xcu  # adapter needs bones framework
bd dep add sem-tools-017 sem-tools-73z  # adapter needs the external thing

# 4. Re-wire downstream from old → bones
bd dep add sem-tools-1jw sem-tools-xcu
bd dep add sem-tools-9ay sem-tools-xcu
bd dep remove sem-tools-1jw sem-tools-svo
bd dep remove sem-tools-9ay sem-tools-svo

# 5. Supersede the old monolithic bead
bd supersede sem-tools-svo --with=sem-tools-xcu
```

## Trap to avoid

The stub adapter (gmb.py returning []) needs to register as a proper adapter implementing the ABC, not just a placeholder file. If the stub doesn't honor the contract, the framework can't actually run end-to-end and you've shipped half-paths. In sem-tools-xcu the stub is a real `GmbReviewAdapter(ReviewAdapter)` class — it just returns 0 reviews. The full pipeline exercises every code path, just against an empty input.

## Concrete grounding

- Executed in this session (sem-tools repo, 2026-06-12) — old svo bead split into xcu (framework) + 017 (gmb adapter), 1jw/9ay re-wired to depend on xcu.
- 7 commits to xcu landed (b90c85c → ef9ead6) during the 73z external wait window — work that would otherwise have been idle.
- 1jw and 9ay automatically appeared in `bd ready` the moment `bd close sem-tools-xcu` ran.
- bd `--suggest-next` flag surfaced the newly-unblocked siblings without manual checking.

## Why this is worth saving

This is the "don't let external dependencies block your momentum" scoping pattern, made concrete with executable steps. Useful for any team using a dep-graph task tracker (beads, GitHub Projects, Linear, Jira) when waiting on vendors/partners. The specific bd command sequence works for beads; the conceptual steps transfer to any tracker.

## When This Applies

Specific conditions where this scoping strategy unblocks parallel work:
- Multiple deliverables in a single tracked issue
- External blockers on only SOME deliverables
- Downstream work depends on the un-blocked parts
- The framework-piece (unblocked) is substantial enough that waiting is costly (>2 business days)

## When This Does NOT Apply

- All deliverables are blocked by the same external dependency
- Framework vs. external-facing code are too tightly coupled to separate (stub would violate interface contract)
- Downstream work actually depends on integration with the external service (can't unblock it truly)

## Source Context

Pattern emerged 2026-06-12 during sem-tools Phase 1 review-aggregator work (sem-tools-xcu-svo-split session). The monolithic sem-tools-svo bead contained framework (schema, adapters ABC, aggregator, drafter, CLI, cron infrastructure) PLUS a real Google Reviews API v4 adapter, blocked by a 7-10 day API allowlist approval (sem-tools-73z). Downstream beads (sem-tools-1jw for Facebook, 9ay for Yelp) each had their own platform fetcher via Chrome MCP but were blocked waiting for svo. The split identified the blocking axis (external API approval), partitioned deliverables into "Bones" (framework + stub impl) and "Adapter" (real implementation), re-wired downstream dependencies from monolithic svo to the unblocked xcu bead, and superseded the original. Result: xcu shipped 7 commits during the 73z wait window; 1jw/9ay unblocked automatically on xcu close. Grounding verified through 7 commits (b90c85c → ef9ead6) and observation of downstream unblocking via `bd ready` and `bd close` automation.
