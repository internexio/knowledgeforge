---
title: Cross-machine accretion routing — write candidates to the live-clone session, not the dirty-clone session that produced them
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
created: 2026-06-15
domain: methodologies
topic: handoff-protocol
tags: [multi-machine, knowledge-base, accretion, handoff-protocol, orchestra-mcp]
related_entries:
  - strategy/2026-06-14_substrate-migration-triage.md
  - diagnostics/2026-06-13_green-daemon-zero-output-status-field-silently-excludes-work.md
  - patterns/2026-06-14_cross-module-summary-row-count-drift.md
pinned: false
---

# Cross-Machine Accretion Routing

## Problem Shape

When a single canonical knowledge base is replicated across machines but only ONE machine owns the canonical clone, accretion candidates discovered on a non-owner machine must NOT be filed into that machine's local clone. The non-owner clone is typically dirty, behind, or about to be removed — writing there entangles the entry with unresolved local state and risks loss. Instead, **route the candidate as an artifact to the owner-machine session, including the fully-formed wiki entry body in the routing payload, and let the owner-session file it cleanly**.

## When This Applies

- Multi-machine setup with one machine designated as the canonical clone owner
- A non-owner machine session produces an accretion candidate (during work in an unrelated project)
- The non-owner machine has an Orchestra/inbox/queue mechanism to route artifacts cross-machine
- The owner clone is current (vs the non-owner clone, which may be dirty/stale/pending-removal)

## When This Does NOT Apply

- Single-machine setup
- The non-owner clone IS canonically synced (not dirty/behind)
- No cross-machine routing mechanism available (in which case file locally + reconcile via git)
- The candidate's grounding is in the non-owner machine's local state that the owner has no view of (rare — usually the body can be made self-contained)

## Protocol

1. **On the producing (non-owner) machine:** detect dirt/behindness BEFORE writing locally. `git status` + `git rev-list --count HEAD..origin/main` is sufficient.
2. If dirty or behind, switch to routing mode: do NOT write the entry locally. Compose the full canonical body (frontmatter + content) in the artifact payload.
3. Push via Orchestra `push_artifact` (or equivalent) with:
   - `destination`: the owner-machine agent ID (e.g., `laptop-claude`)
   - `artifact_type`: `research` or `handoff` (depending on whether owner-side action is needed)
   - `priority`: elevated if the producing clone is about to be discarded (the candidate is time-bound)
   - `content`: full proposed wiki path + index.md line + the verbatim entry body
4. **On the owner machine:** `pull_pending` → claim → file via knowledge-librarian → complete with confirmation back to the producer agent_id. The librarian runs all standard gates (search overlap, grounding, taxonomy) on the inbound body — the producer doesn't pre-judge.
5. **Acknowledge:** the completion artifact pushed back includes the on-disk path + index totals so the producer has confirmation the routing succeeded.

## Worked Instances (laptop-claude ↔ mini-claude, 2026-06-14/15)

- **substrate-migration-triage** — mini-claude routed via `art_03ec9480` because mini's `~/Mini/knowledgeforge-core` clone was dirty ([project]-0za4 green-daemon state) and 16 behind. Laptop-side librarian filed at `wiki/strategy/2026-06-14_substrate-migration-triage.md`; ack returned as `art_94662aea`.

- **green-daemon-zero-output (RECOVERY case)** — mini wrote the entry on the dirty clone, then realized the clone was about to be removed in an architecture change (Mini → -cc-only; -core stays laptop-side). Routed at P6 via `art_f576ecfc` for time-bound recovery. Laptop-side librarian filed at `wiki/diagnostics/2026-06-13_green-daemon-zero-output-status-field-silently-excludes-work.md`; ack returned as `art_39de871b`. Without routing, the entry would have been lost on `rm`.

- **Counterpoint (cross-module-summary-row-count-drift, same session)** — laptop-side librarian wrote directly into laptop's clean local clone. No cross-machine routing was needed because the producing machine WAS the owner.

## Why This Pattern Is Reusable

The mechanism (route candidates as artifacts when the local clone isn't suitable for write) generalises to any multi-machine knowledge base: docs, wikis, agent-corpus, decision logs. The trigger predicate (`git status` non-clean OR `behind > 0`) is deterministic. The acknowledgement-loop is what makes it a protocol rather than a one-shot — the producer knows whether the entry landed.

## Anti-pattern — silent local commit on dirty clone

Writing to a dirty/behind clone "to commit later" reliably produces orphaned entries because the local-state reconciliation gets prioritized over the unrelated accretion and the accretion gets lost. The 2026-06-13 green-daemon entry was almost lost to this exact pattern; recovery via Orchestra routing was the only thing that saved it.
