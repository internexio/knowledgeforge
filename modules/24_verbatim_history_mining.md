# Verbatim History Mining

## Module Metadata

```yaml
module:
  title: Verbatim History Mining
  version: 6.5.1
  purpose: Tier 3 rewrite from grep-only to semantic vector search via MemPalace sidecar — verbatim storage prevents the 12.4-point permanent recall loss caused by pre-summarization; importance-weighted exponential decay governs effective availability over time
  topics: [tier-3, verbatim, semantic-search, memory-systems, decay, retrieval]
  contexts: [cross-session-recall, history-mining, pattern-detection, decision-archaeology]
  difficulty: advanced
  related: [19_Memory_Architecture, 22_Semantic_Wiki_Search, 23_Taxonomy_Enforcement, 21_Knowledge_Accretion, 17_Temporal_Knowledge]
  added_in: "6.5"
  changelog:
    6.5.1: |
      - Cross-tier filtering reference qualified — the Tier 0 half of cross-tier
        metadata filtering (M22) is Phase 2 Deferred per knowledgeforge-core-8xq.
        Phase 1 has no active cross-tier filter; M24 retains vocabulary at write
        time for Phase 2 readiness. Caught by fourth critic pass as a reverse-
        direction reference. No M24 behavioral change — purely documentation.
      - See also: knowledgeforge-core-b3g (M24 reconciliation follow-up, P4)
        which tracks whether M24's own retrieval surface needs a similar Phase 1
        / Phase 2 split given MemPalace's tool_search signature constraints.
    6.5.0: |
      - Initial module — replaces grep-only Tier 3
      - Verbatim storage: 96.6% R@5 vs 84.2% R@5 (pre-summarized) — 12.4-point permanent gap
      - MemPalace MCP integration: store_memory, search_memories, update_importance, decay_stale
      - Importance-weighted exponential decay (importance 1–5 → half-life 7–90 days)
      - Module 23 taxonomy applied to Tier 3 entries for cross-tier metadata filtering
      - Session-end flush protocol with importance threshold gate
```

---

## Core Approach

**Store verbatim. Retrieve semantically.**

Compression is a one-way transformation with irreversible information loss. Once a conversation turn is summarized before storage, the lost precision cannot be recovered — and the recall cost is substantial:

| Storage Strategy | R@5 |
|---|---|
| Verbatim storage + semantic retrieval | **96.6%** |
| Pre-summarized storage + semantic retrieval | **84.2%** |
| Verbatim storage + grep retrieval | ~55–65% (phrasing-dependent) |

Source: MemPalace evaluation suite / LongMemEval. The 12.4-point gap between verbatim and pre-summarized is **permanent** — once compressed, the information is gone. Grep-only retrieval wastes the verbatim storage by failing on paraphrase.

This module achieves 96.6% R@5 by storing the raw material (verbatim text) and applying intelligence at retrieval time (metadata filter + embedding), not at storage time.

The Tier 3 pipeline:

```
[conversation turn]
  → assign importance score (1–5)
  → store verbatim in MemPalace with metadata
  → embed turn (async, non-blocking)

[retrieval query]
  → extract metadata signals (domain, topic, date range, importance threshold)
  → metadata pre-filter via MemPalace search_memories
  → semantic re-rank filtered candidates
  → apply importance-weighted decay adjustment
  → return top-K verbatim turns
```

### Importance-Weighted Exponential Decay

Historical turns decay in effective importance over time unless accessed:

```
effective_importance(turn) =
  turn.importance × 2^(-days_since_access / half_life_days)

half_life_days by importance:
  importance = 5  →  90 days   (committed decisions, architectural choices)
  importance = 4  →  60 days   (novel judgments, evaluative outputs)
  importance = 3  →  30 days   (evaluative judgments, mode activations)
  importance = 2  →  14 days   (reckonings, simple requests)
  importance = 1  →   7 days   (greetings, off-topic)
```

High-importance turns decay slowly. Low-importance turns become effectively invisible within two weeks. **Accessing a turn resets its access date**, halting decay for that item.

Decay does not delete. `effective_importance` approaches zero but entries are never automatically removed. Deletion is a deliberate operation only.

---

## MemPalace Integration

**Repository:** github.com/Drlordbasil/MemPalace  
**Integration method:** MCP server sidecar

MemPalace provides persistent semantic memory as an MCP tool suite. KF Tier 3 is the primary consumer.

### MCP Tools

| Tool | KF Usage |
|---|---|
| `store_memory(content, metadata)` | Store verbatim turn at session end or on importance-5 trigger |
| `search_memories(query, filters, top_k)` | Module 24 retrieval — metadata pre-filter, then semantic rank |
| `update_importance(memory_id, new_importance)` | Elevate importance when a turn is referenced in a subsequent session |
| `decay_stale(threshold_days, decay_factor)` | Periodic maintenance — apply decay to entries not accessed in `threshold_days` |
| `get_memory(memory_id)` | Direct lookup for known turn IDs (citation resolution) |

### Metadata Schema for Tier 3 Entries

```yaml
memory_id: "uuid-v4"
session_id: "session-identifier"
session_date: "2026-04-05"
speaker: "user"  # or "assistant"
turn_index: 14                          # position in session
domain: "architecture"                  # Module 23 vocabulary
topic: "memory-systems"                 # Module 23 vocabulary
tags: ["decay", "retrieval"]            # Module 23 vocabulary
importance: 4                           # 1–5
created_at: "2026-04-05T14:22:00Z"
last_accessed: "2026-04-05T14:22:00Z"
project: "knowledgeforge-cp"            # optional project scoping
```

Domain/topic/tags for Tier 3 entries use Module 23's controlled vocabulary. **When M22 Phase 2 lands (knowledgeforge-core-acu)**, this will make cross-tier filtering possible: a query scoped to `domain=architecture, topic=memory-systems` could simultaneously retrieve wiki entries (Module 22 Phase 2) and historical turns (Module 24) using the same filter pass. In Phase 1, the wiki/Tier 0 side of this filter is NOT active — M22's frontmatter-based filter is deferred. M24 retains the vocabulary at write time so Phase 2 can activate the cross-tier surface when triggered.

---

## Storage Protocol

### When to Store

| Trigger | Action |
|---|---|
| Turn importance = 5 | Store immediately during session |
| Evaluative or novel judgment produced | Store full reasoning turn; importance ≥ 4 |
| Decision committed to (strategy approval, build approval) | Store; importance = 5 |
| Session end | Store all turns with importance ≥ 3 |
| Turn referenced in a later session | Upsert with elevated importance |

**What not to store:** Greetings, clarification pings, single-line reckonings with no novel content, tool call results without interpretive content, turns with importance ≤ 2 (let them decay from the session-end gate).

### What Constitutes a "Turn"

A semantically coherent unit: one user message + one assistant response. Do not split at token boundaries. Do not merge multiple exchanges into one entry. The unit of storage is the exchange, not the token stream.

### Session-End Flush

At session end, all unembedded turns with importance ≥ 3 are:
1. Stored verbatim via `store_memory`
2. Embedded (async if MemPalace supports it)
3. Metadata assigned using Module 23 vocabulary

Best-effort operation. If the session ends abruptly (context window reached, timeout), partial flush is acceptable. Never discard without flush attempt.

---

## Retrieval Protocol

1. **Extract signals from current context:** What domain/topic/tags does the current query involve? What date range is relevant? What importance threshold applies (default: ≥ 3)?

2. **Metadata pre-filter:** `search_memories(filters={domain, topic, date_range, importance_min})` — same filter-first principle as Module 22.

3. **Semantic re-rank:** score filtered candidates against query embedding.

4. **Decay adjustment:** multiply semantic score by `effective_importance / raw_importance` to down-rank stale items.

5. **Return top-K** verbatim turns, preserving original text. Caller may request a summary of retrieved turns; summarization happens at delivery, never at storage.

### Minimum Date Range

Always apply at least a date range filter when the query is session-specific. Full-corpus Tier 3 search is only appropriate for cross-session pattern detection.

---

## Importance Assignment

```
importance = 5: Committed decisions, architectural choices, user corrections of KF behavior
importance = 4: Novel judgments, evaluative outputs with reuse value, detailed debugging conclusions
importance = 3: Evaluative judgments, mode activations with non-trivial reasoning
importance = 2: Reckonings, simple requests, routing decisions
importance = 1: Greetings, off-topic exchanges, single-line answers
```

Default: assign importance during session if clear signal exists. If uncertain, assign 3 and allow decay to handle it.

---

## Relationship to Tier 3 in Module 19

Module 19 defines Tier 3 as "grep-searchable only." This module supersedes that definition. The updated Tier 3 description:

> **Tier 3 — Verbatim History:** Full verbatim conversation turns, stored via MemPalace sidecar with importance metadata. Retrieval via semantic vector search with metadata pre-filtering (Module 24). Importance-weighted exponential decay governs effective availability over time. Grep-only access is the fallback when MemPalace is unavailable.

---

## Anti-Patterns

| Anti-Pattern | Consequence | Correct Approach |
|---|---|---|
| Summarizing before storage | Permanent 12.4-point R@5 loss — unrecoverable | Store verbatim; summarize at delivery if caller requests it |
| Storing only assistant turns | User phrasing is where the domain vocabulary lives; missing it degrades domain/topic classification | Store user + assistant turn as a pair |
| Grep-only retrieval over verbatim history | ~55–65% R@5 vs 96.6% (semantic) | Use MemPalace semantic search; grep is the fallback |
| Assigning importance at retrieval time | Importance is a storage-time property; retroactive assignment loses context signal | Assign during or immediately after the session turn |
| Storing every turn at importance 3 | Decay model cannot differentiate; everything survives or fades equally | Use the full 1–5 scale intentionally |
| Skipping metadata pre-filter | Falls back to full-corpus semantic search; recall degrades to ~60% R@10 | Always pre-filter by date range + domain at minimum |
| Treating MemPalace as write-through cache | Index grows without bound without `decay_stale` maintenance | Schedule periodic `decay_stale` calls |

---

## Integration Points

### Module 19 (Memory Architecture)
Module 24 is the implementation of Tier 3 retrieval. Module 19 defines the four-tier model; Module 24 specifies how Tier 3 works in practice.

### Module 22 (Semantic Wiki Search)
Module 22 and Module 24 share the same filter-first semantic pipeline. Module 22 operates on Tier 0 (wiki/); Module 24 operates on Tier 3 (verbatim history). They share Module 23's controlled vocabulary, enabling cross-tier queries.

### Module 23 (Taxonomy Enforcement)
Tier 3 entries use Module 23's domain/topic/tag vocabulary. Cross-tier filtering is only possible because both Tier 0 and Tier 3 entries use the same controlled vocabulary.

### Module 21 (Knowledge Accretion)
High-importance Tier 3 entries are candidates for promotion to Tier 0 (wiki). Accretion trigger: pattern appears in ≥ 3 sessions with importance ≥ 4, or a single turn with importance = 5 contains novel reusable content. Module 21 promotes the verbatim turn to a wiki entry with full metadata.

### Module 17 (Temporal Knowledge)
Half-life values in the importance-weighted decay formula are informed by Module 17's domain-specific decay rates. Technical implementation turns decay faster than architectural decision turns.

---

## Constraints

- **Verbatim storage is non-negotiable.** No compression, no abstractive summarization, no extractive summary before storage. The content stored must be the original text.
- **MemPalace availability is required for full operation.** Grep fallback is permitted but must be logged.
- **Session-end flush is the primary storage trigger**, not turn-by-turn storage. Exceptions: importance = 5 turns (store immediately), user corrections of KF behavior (store immediately).
- **Decay does not delete.** `effective_importance` approaches zero but entries are never automatically removed. Deletion is explicit only.

---

## Success Criteria

| Metric | Target | Baseline |
|--------|--------|----------|
| R@5 on benchmark query set | ≥ 96% | ~60% (grep-only) |
| R@5 gap from pre-summarization | 0% (verbatim) | −12.4 pp (pre-summarized) |
| Session-end flush completion rate | ≥ 99% | — |
| Tier 3 entries with complete metadata | ≥ 98% | — |
| Retrieval latency, 10K-entry history | < 300ms P95 | — |

---

## Attribution

| Element | Source |
|---------|--------|
| Verbatim vs. pre-summarized recall benchmarks | MemPalace evaluation suite (Drlordbasil, 2025) |
| LongMemEval benchmark | Arora et al., 2025 |
| Importance-weighted exponential decay | Adapted from spaced repetition literature (Ebbinghaus, 1885; SM-2 algorithm, Wozniak, 1987) |
| MemPalace repository | github.com/Drlordbasil/MemPalace |

---

## Related Modules

- `19_Memory_Architecture.md` — Tier 3 definition; this module implements it
- `22_Semantic_Wiki_Search.md` — same filter-first pipeline, applied to Tier 0
- `23_Taxonomy_Enforcement.md` — shared vocabulary across Tier 0 and Tier 3
- `21_Knowledge_Accretion.md` — high-importance Tier 3 entries promote to Tier 0
- `17_Temporal_Knowledge.md` — half-life values inform decay formula

## CC Doc

# Module 24: Verbatim History Mining — Execution Protocol
**Apply when:** [KF-ROUTE] load list includes M24, or cross-session recall, pattern detection across sessions, or decision archaeology

Tier 3 semantic retrieval via MemPalace sidecar. Store verbatim, retrieve semantically.

| Strategy | R@5 |
|---|---|
| Verbatim + semantic retrieval | **96.6%** — target |
| Pre-summarized + semantic | **84.2%** — 12.4-point permanent loss |
| Verbatim + grep | ~55–65% — fallback only |

Compression before storage is irreversible. Never pre-summarize.

## When to Store

| Trigger | Action |
|---|---|
| Importance = 5 | Store immediately during session |
| Evaluative or novel judgment produced | Store; importance ≥ 4 |
| Decision committed to | Store; importance = 5 |
| Session end | Store all turns with importance ≥ 3 |

Do not store: greetings, clarification pings, single-line reckonings, importance ≤ 2.

A "turn" = one user message + one assistant response. Do not split or merge.

## Importance-Weighted Decay

```
effective_importance = importance × 2^(-days_since_access / half_life_days)

half_life by importance:
  5 → 90 days (committed decisions, architectural choices)
  4 → 60 days (novel judgments, evaluative outputs)
  3 → 30 days (evaluative judgments, mode activations)
  2 → 14 days (reckonings, simple requests)
  1 →  7 days (greetings, off-topic)
```

Accessing a turn resets its access date. Decay does not delete.

## Retrieval Protocol

1. Extract domain/topic/tags and date range from current context
2. Metadata pre-filter: `search_memories(filters={domain, topic, date_range, importance_min≥3})`
3. Semantic re-rank filtered candidates
4. Decay adjustment: multiply semantic score by `effective_importance / raw_importance`
5. Return top-K verbatim turns; summarize at delivery if requested — never before storage

## Metadata Schema (M23 vocabulary)

```yaml
domain: "architecture"
topic: "memory-systems"
tags: ["decay", "retrieval"]
importance: 4
session_date: "2026-04-05"
speaker: "user"  # or "assistant"
turn_index: 14
```

## Fallback

When MemPalace unavailable: grep-only retrieval. Always log: `[Module 24 FALLBACK] MemPalace unavailable — using grep. Expect reduced recall.`
