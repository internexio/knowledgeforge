---
title: Green daemon, zero output — suspect a status field that silently excludes work
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-13
domain: diagnostics
topic: queue-observability-pitfall
tags: data-integrity, root-cause-analysis, watchdog, scheduling
related_entries:
  - diagnostics/2026-05-31_per-entity-status-classifier-unmeasured-vs-measured-null.md
  - infrastructure/2026-05-15_silent-success-scripts-state-artifact-freshness.md
  - methodologies/2026-05-29_dormant-subsystem-forensics-check-supervision-first.md
---

# Green Daemon, Zero Output — Suspect a Status Field That Silently Excludes Work

## The Anti-Pattern

A background pipeline reports healthy — daemon process alive, no errors in logs, rate/quota budget open — yet produces zero output for an extended period. The instinct is to inspect the infrastructure (is it running? is auth working?). That instinct is usually wrong. When infra is demonstrably green but throughput is zero, the cause is almost always a **status field, counter, or filter** that silently excludes work from being processed. It is a bookkeeping bug, not an infrastructure bug.

## Pattern Description

When two code paths disagree about what a record's state means:

- **Path A** marks a work item as "done" using one field (`submitted=True`)
- **Path B** filters eligible work by checking a different field (`status != 'draft_ready'`)
- Result: Path A's output counts as "still pending" in Path B's logic, capping throughput to zero because the queue looks full

The "green daemon" appearance masks a silent contradiction: monitoring shows "queue is idle, budget is open, daemon is running," but the actual eligibility logic says "queue is full, don't process anything."

## When It Applies

- Any producer/consumer or scan→queue→act pipeline where one stage decides what is "eligible" or "pending" based on a stored status, flag, or rolling count
- Systems with multiple code paths that read/write eligibility state
- Especially when status views filter on different fields than the intake/processing logic
- Daemons that report healthy via logs but mysteriously stop producing output

## When It Does NOT Apply

- If there ARE errors or exceptions in logs, or the process is actually dead or wedged, this is a normal infra failure — diagnose that directly
- The pattern is specifically for the deceptive "everything looks fine but nothing happens" case
- If the status field is working as designed (legitimately excluding work), this is not a bug but a feature — check the specification

## Concrete Grounding (Moltbot, 2026-06-13)

A Moltbook feed-scan daemon ran every 5 min, found 7–10 good candidates each cycle, and queued ZERO for days.

- Daemon was healthy: no burns in logs, no exceptions
- Quota was wide open: per-author intake cap still had headroom
- Status view read as: "empty queue, ready for work"

**Root cause:** A per-author intake cap counted draft-queue entries whose status was `"draft_ready"` as still-pending. But the submit path set `submitted=True` **without ever flipping status off `"draft_ready"`** — so 53 already-POSTED comments looked like live backlog to the cap tally, capping every prolific author and starving intake to zero.

Two code paths disagreed on what "done" meant:
- Submit logic: "if posted, set `submitted=True`" ✓
- Capacity check: "count entries where `status == 'draft_ready'` as pending" ✓ (independently correct)
- Disagreement: "a posted entry can still have `status='draft_ready'`" ✗ (reveals state-field mismatch)

The `--status` view read as "empty queue" because it filtered on `submitted=True`, masking the contradiction.

**Fix:** Two one-liners:
1. Set `status='submitted'` when marking an entry as posted
2. Exclude `submitted=True` rows from the pending-count tally

The **same project hit a sibling instance weeks earlier:** auto-engage posted 0 for days because the `claude` binary moved paths and the daemon silently fell back to a disabled local model — again, green daemon, zero output, non-infra cause (different root, same diagnosis pattern: check the eligibility logic, not the daemon).

## Diagnostic Move

1. **Dump the actual eligibility-determining state:**
   - Queue statuses by value (e.g., `SELECT status, COUNT(*) FROM queue GROUP BY status`)
   - The counter's live inputs (what rows is it actually counting?)
   - The filter's matched set (what does the processing logic actually see as "eligible"?)

2. **Compare against what each consuming code path believes that state means:**
   - Does the submit path mark items as done?
   - Does the intake cap read the same field?
   - If not, trace the disagreement back to the source.

3. **The bug lives in the disagreement.** Don't trust summary/status views — they often apply a different filter than the logic that's actually blocking.

## Related Patterns

- **Per-entity status classifiers (unmeasured vs measured-null):** When a status field is truly absent, the consuming code must distinguish "we haven't checked" from "we checked and found null." Similar state-semantics problem, different domain.
- **Silent-success scripts:** Distinguishes what artifact *actually signals success* (for monitoring) vs. which file *looks up-to-date* (mtime trap). Complementary problem: which file tells the truth about work completion?
- **Dormant-subsystem forensics:** Checks the supervision layer before the subsystem code. If a pipeline appears dead, check whether something upstream decided it's ineligible.

## Source Context

Moltbot operations, 2026-06-13. Auto-engage daemon posted 0 comments for days despite healthy daemon, open quota, and good candidates. Root cause: draft-queue capacity check counted already-posted entries because the submit path didn't flip the `status` field — a disagreement between two independent status-reading code paths. The diagnostic pattern (check what state each code path *thinks* it's reading) is reusable: whenever a daemon looks healthy but produces nothing, the cause is often not infra but state-field misalignment.
