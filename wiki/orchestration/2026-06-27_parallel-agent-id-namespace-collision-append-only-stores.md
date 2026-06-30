---
title: Parallel-agent ID-namespace collision in append-only claim/ticket stores
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.75
staleness_risk: stable
importance: 3
created: 2026-06-27
domain: orchestration
topic: parallel-workflow
tags: [multi-agent-orchestration, parallel-agents, append-only-store, claim-id, naming-collision, knowledge-aggregation]
related_entries:
  - orchestration/2026-05-30_parallel-agent-triage-backlog-reconciliation.md
  - orchestration/2026-06-12_parallel-spec-parallel-critic-pattern-independent-beads.md
  - orchestration/2026-05-29_append-only-queue-fingerprint-dedup-reconcile-gc.md
  - architecture/2026-05-15_schema-marker-multi-producer-jsonl-contract.md
pinned: false
---

# Parallel-Agent ID-Namespace Collision in Append-Only Claim/Ticket Stores

## What Was Observed

cos-grounding (Sat 2026-06-27 PM): two `discovery-scout` subagents were dispatched in parallel against different framework gaps. Both were authorized to write into the same numbered claim-ID namespace (the `qual-*` prefix). One sprint (F-PPE) wanted `qual-001` for Rosengren 2020; the other (F-SCQ) wanted `qual-001` for Tannenbaum 2015. They worked simultaneously, both created `claims/qual-001-*.md` + `evidence/qual-001.yaml` + a manifest entry, then the second-finishing sprint noticed the collision and self-corrected.

The self-correction pattern that worked:

1. The first sprint to commit a manifest entry "wins" — its claim slug + ID become canonical.
2. The losing sprint renames its artifacts to the next available number (`qual-001` → `qual-002`) and updates its own manifest entry to match.
3. The losing sprint's now-orphaned `claims/qual-001-<old-slug>.md` is **moved out of `claims/`** to a tombstone path (e.g. `findings/qual-001-tombstone-YYYY-MM-DD.md`), not deleted — preserves audit trail and signals the resolution to future scanners.
4. Tombstones outside `claims/` keep claim-directory listings clean and prevent future ID-resolution glob patterns from picking up stale slugs.

## When the Pattern Applies

Any time multiple agents are dispatched in parallel against an append-only store with sequentially-numbered IDs in a shared prefix space. Examples beyond cos-grounding:

- Issue trackers where multiple agents file tickets in the same project (`PROJ-001`, `PROJ-002`...)
- Aggregation stores where IDs are assigned by next-available-slot (claim DBs, citation managers, evidence libraries)
- Documentation systems with numbered RFC / ADR slots
- Test-fixture stores keyed by sequential IDs

## When the Pattern Does NOT Apply

- Hash-keyed stores (S2 IDs, content-addressed paths) — no collision risk by construction
- UUID-keyed stores — same
- Single-writer pipelines (one agent, sequential)
- Strongly-typed reservation systems (agent calls "reserve next ID" before generating content)

## What Goes Wrong If the Pattern Is Ignored

Without an active resolution step, the manifest ends up with two entries claiming the same ID, or one overwrites the other (silent loss of work), or both files coexist on disk and downstream consumers pick whichever they globbed first. cos-grounding's F-SCQ rollup explicitly flagged the issue with: *"a parallel F-PPE sprint had filed qual-001 without updating manifest; I clobbered then restored, shifted my filings to qual-002+."*

## Preferred Protocol Going Forward

Two paths:

**Reservation-first (preferred when possible):** before dispatching parallel agents, pre-allocate ID ranges per agent. E.g. Agent A gets `qual-001` to `qual-009`, Agent B gets `qual-010` to `qual-019`. Eliminates collision possibility. Requires upfront knowledge of how many claims each agent might file (over-allocate when uncertain).

**Tombstone-on-collision (always-safe fallback):** if reservation isn't feasible, document the protocol so any agent that detects a collision:
1. Renames its artifacts to the next available ID (not the colliding one).
2. Moves the old-ID artifacts to a tombstone path outside the canonical directory (NOT delete).
3. Updates the manifest entry to point at the new ID.
4. Logs the resolution in its discovery / rollup doc so the next session has audit trail.

## Why This Is Worth Remembering

It's the kind of orchestration bug that only surfaces under concurrency, costs little when handled inline, but can corrupt the audit trail of an aggregation store if missed. The fix (tombstone-on-collision) is cheap, reversible, and zero-data-loss — but it has to be a standing protocol, not an ad-hoc judgment call. Each subagent in a parallel dispatch should know the rule before it starts.

## Concrete Grounding from the Session

- Two subagents (discovery-scout for Platform/Personality/Engagement; discovery-scout for Strategic Clarity/Quality) ran concurrently against `~/Scripts/cos-grounding/`
- F-SCQ agent's rollup explicitly flagged the collision: tombstone left at `claims/qual-001-fear-appeals-meta.md`, rm permission denied, shifted filings to `qual-002+`
- Main thread resolved via `mv claims/qual-001-fear-appeals-meta.md findings/qual-001-tombstone-2026-06-27.md`
- Final state: 22 valid claim IDs in manifest, no duplicate qual-001, tombstone preserved in `findings/` for audit history
- Git commit `c317f0c` captures the resolution

## Related Entries

- `orchestration/2026-05-30_parallel-agent-triage-backlog-reconciliation.md` — parallel agents in read-only investigation mode (no write-conflict surface; this entry covers the write-conflict case).
- `orchestration/2026-06-12_parallel-spec-parallel-critic-pattern-independent-beads.md` — parallel critic chains where independence is enforced at the input layer; this entry covers parallel writers against a shared output namespace.
- `orchestration/2026-05-29_append-only-queue-fingerprint-dedup-reconcile-gc.md` — fingerprint-keyed dedup for re-running producers (content-keyed, single producer); this entry covers sequentially-keyed under multiple producers.
- `architecture/2026-05-15_schema-marker-multi-producer-jsonl-contract.md` — multi-producer JSONL where producers write different schemas to one file; this entry covers multi-producer where producers write the same schema into a shared sequential ID space.
