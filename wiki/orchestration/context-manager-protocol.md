---
title: Context-Manager Protocol
source_mode: synthesizer
source_session: redacted
created: '2026-04-29T00:00:00Z'
date: '2026-04-29'
confidence: 0.88
grounding_score: 0.88
grounding_source: 'Two independent implementations observed: CCT''s context-manager.md
  (repo-internal agent that opens with JSON state query before any output) and KF''s
  own context-manager protocol (MemPalace Tier 3 retrieval at session start). Both
  solve the same problem — agent context amnesia in multi-agent workflows — via the
  same pattern: state query precedes task execution.'
novelty_type: design_principle
staleness_risk: low
importance: 3
pinned: false
accreted_in: '6.5'
related:
- wiki/orchestration/schema-first-elicitation-order.md
- wiki/orchestration/multi-framework-cp-composition.md
- modules/01_kf_orchestrator.md
- modules/09_coordinator.md
domain: orchestration
topic: task-decomposition
---

# Context-Manager Protocol

## Pattern

In multi-agent workflows, agents lose session context between invocations. Without explicit state reconstruction, an agent receiving a handoff operates on incomplete information and produces output inconsistent with prior decisions.

**The protocol:** Every agent in a multi-agent system opens its response with a structured state query before generating any substantive output.

```
Agent receives task →
  1. Query: "What do I know about this session/project/prior decisions?"
  2. Reconstruct: retrieve state from session memory, beads, or context manager
  3. Validate: confirm the retrieved state is current (not stale)
  4. Then act
```

The state query is the first action, not an optional preflight. An agent that acts without querying state is amnesia-prone.

---

## Two Implementations, Same Protocol

**CCT implementation (simple):**
- `context-manager.md` agent opens with a hardcoded JSON query block
- Returns a state object with current tasks, decisions, and prior outputs
- Every sub-agent in the CCT multi-agent system is expected to call the context-manager before generating output
- Limitation: the context-manager is stateful (it holds session state in memory); if it dies, state is lost

**KF implementation (durable):**
- KF's Memory Architecture (Tier 3: verbatim conversation history) stores prior decisions durably via MemPalace
- At session start or after context compaction: `bd prime` (or `mempalace_search`) reconstructs the working context
- Tier 3 stores verbatim (not pre-summarized) — preserves recall fidelity at 96.6% R@5 vs 84.2% for pre-summarized
- Limitation: requires MemPalace to be available; grep fallback used when unavailable (reduced recall)

**The common structure:**
Both implementations follow: query → retrieve → validate → act. The storage backend differs; the protocol is the same.

---

## Anti-Pattern — Act-First Agent

Agent receives a task, immediately begins reasoning and producing output, treating the task as fully self-contained.

**What breaks:**
- The agent re-derives decisions that were already made in a prior session
- The agent contradicts prior decisions it would have honored if it had reconstructed context
- Two agents working in parallel make incompatible changes because neither queried shared state
- After context compaction (which this session experienced), the restored context is a summary — lower fidelity than the verbatim history that MemPalace provides

**Observed impact:** This session started from a compacted summary. Several prior tool results (the two `tool-results/*.txt` files flagged in system reminders) were not reconstructed, requiring the triage to re-derive CCT component analysis from scratch rather than building on prior work.

---

## Protocol Requirements

A compliant context-manager protocol implementation needs:

1. **Durable storage** — state survives agent death and session compaction (MemPalace, beads, or git-committed files; not in-memory only)
2. **Structured query** — the query returns a typed state object, not a free-text summary (allows downstream validation)
3. **Staleness detection** — the agent validates that retrieved state is current before acting on it (check timestamps, version numbers, or freshness markers)
4. **Conflict detection** — if the task conflicts with retrieved state, the agent surfaces the conflict rather than silently overriding
5. **Graceful degradation** — if state retrieval fails, the agent acknowledges it's operating without full context and flags its output accordingly

KF's implementation meets requirements 1-4 via MemPalace + verbatim storage + importance-weighted decay. Requirement 5 is handled by the Metacognitive Monitor.

---

## Implementation Guidance

**For new agents in multi-agent KF workflows:**
```markdown
## Context Reconstruction (always first)

Before responding:
1. Run `bd prime` or check `~/Scripts/knowledgeforge-core/wiki/` for relevant prior decisions
2. Check `bd list --status=in_progress` for active work context
3. If context is stale or absent, flag: "Operating without full session context — prior decisions not confirmed"
```

**For simple agents where MemPalace is unavailable:**
```markdown
## State Query (always first)

1. What task was I handed? (read the handoff artifact)
2. What decisions were already made? (check commit history or bead notes)
3. What is the current state of the artifact I'm working on? (read the file, don't assume)
```

**For context-manager as a skill (preferred over agent for stateless serialization):**
If the context-manager only reads/writes state without reasoning about it, implement it as a skill (see `skills-vs-agents-design-boundary`), not an agent. Deterministic state serialization is a skill; interpreting ambiguous state and making routing decisions is an agent.

---

## Reuse Context

Reference this entry when:
- Designing any multi-agent workflow: every sub-agent specification should include a context-reconstruction step
- Debugging inconsistent agent output in a multi-agent chain: the first diagnostic is whether the agent queried prior state
- After a context compaction event: the session-start protocol (bd prime + check in-progress beads) is the context-manager protocol applied at session level
- Building a new orchestration workflow: the coordinator agent's first action should always be a state query, not task decomposition
- Reviewing CCT or community multi-agent templates: check whether each agent includes a state-query step; those that don't are amnesia-prone under load
