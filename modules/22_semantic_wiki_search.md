# Semantic Wiki Search

## Module Metadata

```yaml
module:
  title: Semantic Wiki Search
  version: 6.5.0
  purpose: Metadata-gated two-phase retrieval over the Tier 0 wiki — domain/topic/tag pre-filter followed by vector similarity scoring — closing the 35-point recall gap between keyword search (~60% R@10) and filtered semantic search (~95% R@10)
  topics: [retrieval, semantic-search, metadata-filter, embedding, vector-index, wiki-search]
  contexts: [knowledge-retrieval, accretion-check, linter-runs, cross-session-queries]
  difficulty: advanced
  related: [19_Memory_Architecture, 21_Knowledge_Accretion, 23_Taxonomy_Enforcement, 24_Verbatim_History_Mining, 17_Temporal_Knowledge]
  added_in: "6.5"
  changelog:
    6.5.0: |
      - Initial module — closes the retrieval half of the compile-query-enhance loop
      - Two-phase retrieval: metadata pre-filter + semantic re-rank
      - Score fusion: 0.65 semantic + 0.20 importance + 0.15 recency
      - ChromaDB/LanceDB embedded backends
      - Grep fallback with mandatory logging
      - Benchmarks from LongMemEval: 60% R@10 (no filter) → 95% R@10 (hierarchical filter)
```

---

## Core Approach

Keyword search fails on paraphrase, synonym, and conceptual queries. Pure semantic search without metadata pre-filtering achieves ~60% R@10 on a heterogeneous wiki — the unrelated-domain noise drowns the relevant signal. Hierarchical metadata pre-filtering raises this to ~95% R@10. The 35-point gain costs nothing at query time; it requires only that entries carry structured taxonomy fields at write time (Module 23) and pre-computed embeddings (Module 21).

**Two-phase retrieval. Order is not interchangeable.**

Phase 1 — Metadata pre-filter: narrow the candidate set using YAML frontmatter before any semantic scoring. Domain filtering eliminates the largest mass of irrelevant entries. Topic narrows further. Tag overlap catches edge cases.

Phase 2 — Semantic re-rank: compute vector similarity over the filtered candidate set only. Operating on a small, already-domain-relevant set is what produces the 95% recall figure.

```
query
  → extract domain / topic / tag signals from query text
  → candidates = entries where domain matches ∩ topic matches
                 UNION entries with ≥ 2 tag overlaps
  → embed query (cached for session duration)
  → semantic score each candidate: cosine_sim(query_emb, entry_emb)
  → fuse scores
  → return top-K
```

### Score Fusion

```
final_score(entry) =
  0.65 · cosine_similarity(query_embedding, entry_embedding)
  + 0.20 · normalize(entry.importance, range=[1,5])
  + 0.15 · recency_boost(entry.last_accessed, entry.staleness_risk)
```

Weights are defaults. Importance and recency prevent stale low-signal entries from ranking above fresh relevant ones.

`recency_boost` formula:

```
recency_boost(last_accessed, staleness_risk) =
  exp(-λ · days_since_access)
  where λ = 0.01 for staleness_risk = stable
            0.05 for staleness_risk = slow_decay
            0.15 for staleness_risk = volatile
```

Volatile entries decay faster from the recency component, ensuring stale volatile knowledge does not surface above fresh stable knowledge.

---

## Implementation

### Backend Options

| Backend | Deployment | Best Fit |
|---------|-----------|----------|
| ChromaDB | Embedded (no server) | Small–medium wiki (< 50K entries) |
| LanceDB | Embedded (no server) | Large wiki, columnar analytics queries |
| Qdrant | Server | Multi-user or production deployment |

**Default:** ChromaDB embedded. Zero extra dependencies, native metadata filter support, persistent on disk, Python package install.

### Embedding Model

- **Default:** `text-embedding-3-small` — 1536-dim, fast, ~$0.02/1M tokens
- **Local fallback:** `nomic-embed-text` via Ollama — no API cost, comparable quality on technical content
- **Floor:** 768-dim minimum. Below 512-dim, precision on technical distinctions degrades unacceptably.

Embeddings are computed at **write time** (Module 21 pipeline) and stored in the vector index. Module 22 never re-embeds at query time. Query embedding is computed once per query and cached for the session.

### Required YAML Fields for Search

Every wiki entry must carry these fields for the filter to function:

```yaml
domain: "architecture"          # top-level taxonomy node (Module 23 vocabulary)
topic: "memory-systems"         # mid-level node (Module 23 vocabulary)
tags: ["retrieval", "decay"]    # leaf tags (Module 23 vocabulary)
importance: 4                   # integer 1–5 (assigned by Module 21)
created_at: "2026-04-05"
last_accessed: "2026-04-05"
grounding_score: 0.85           # from Module 21 grounding gate
staleness_risk: "stable"        # from Module 17 vocabulary
```

Entries missing `domain` are excluded from filtered search and fall back to full-corpus semantic search for that entry. Module 22 logs a warning for each such entry.

### Query Analysis

Extract domain/topic signals before embedding. LLM classification preferred; keyword heuristic acceptable for latency-sensitive paths.

```
Input: "how does KF handle memory decay for old entries?"
→ domain signal: "architecture"
→ topic signal: "memory-systems"
→ tag signals: ["decay", "temporal", "retrieval"]
→ clean query for embedding: "memory decay old entries KF"
```

### Candidate Size Limit

If the metadata filter returns > 200 candidates, tighten filter (require topic match in addition to domain, or require ≥ 2 tag overlaps). Semantic scoring over > 200 candidates is fine for embedded backends but signals an under-specified taxonomy.

### Fallback

When the vector DB is unavailable (cold start, missing dependency, index corruption):
1. Fall back to keyword grep over wiki/ files
2. Log: `[Module 22 FALLBACK] Vector DB unavailable — using grep. Expect reduced recall.`
3. Never fail silently. The recall regression must be visible.

---

## Anti-Patterns

| Anti-Pattern | Consequence | Correct Approach |
|---|---|---|
| Pure semantic search, no metadata filter | ~60% R@10; surfaces unrelated entries from different domains | Always pre-filter by domain at minimum |
| Post-hoc tag filtering (filter after semantic scoring) | Wastes compute on irrelevant candidates; still misses paraphrase cases | Filter before semantic scoring |
| Re-embedding all entries at query time | O(n) cost per query, unacceptable at scale | Pre-compute embeddings at write time (Module 21) |
| BM25/TF-IDF as primary ranker | Synonyms and paraphrases fall through | BM25 acceptable as optional diversity re-ranker only |
| Rebuilding index on every query | Latency unacceptable at scale | Index persists on disk; rebuild only on new entry, archive, importance delta > 1, or taxonomy reassignment |
| Treating domain mismatch as soft penalty | Off-domain entries contaminate top-K | Domain mismatch = hard exclude, not soft penalty |

---

## Integration Points

### Module 21 (Knowledge Accretion)
Accretion pipeline embeds entries at write time and upserts into the vector index. `entry.embedding`, `entry.importance`, `entry.last_accessed`, `entry.domain`, `entry.topic`, and `entry.tags` are all written at accretion time. Module 22 is read-only against this index.

### Module 23 (Taxonomy Enforcement)
Domain/topic/tag values used in metadata pre-filter come from Module 23's controlled vocabulary. An entry with invalid taxonomy values is excluded from filtered search and falls back to full-corpus semantic search. Module 23 prevents this at write time; Module 22 degrades gracefully if it happens anyway.

### Module 19 (Memory Architecture)
Tier 0 (wiki/) is the corpus. Module 22 provides the retrieval mechanism for Tier 0. The Tier 1 routing index is small enough to load fully; Module 22 is not applied there.

### Module 17 (Temporal Knowledge)
`staleness_risk` field drives the λ parameter in `recency_boost`. Volatile entries decay faster from the recency component.

### Module 24 (Verbatim History Mining)
Module 24 applies the same metadata-filter-first pattern to Tier 3 (verbatim conversation history). Module 22 is the wiki-specific instantiation; Module 24 is the history-specific instantiation. Both share Module 23's controlled vocabulary, enabling cross-tier queries that search wiki and history in a single coherent filter pass.

---

## Constraints

- Do not embed entries with `grounding_score < 0.6`. Low-grounding entries pollute the index.
- Index rebuild required on: new entry accreted, entry archived, importance delta > 1, taxonomy reassignment.
- Return at least 3 results unless fewer than 3 entries pass the metadata filter. Do not return zero results if any entries exist.
- Maximum K for default queries: 10. Caller may request up to 25 for synthesis tasks.

---

## Success Criteria

| Metric | Target | Baseline |
|--------|--------|----------|
| R@10 with hierarchical filter | ≥ 95% | ~60% (no filter) |
| Query latency, embedded backend | < 200ms P95 | — |
| Index rebuild time, 1K-entry wiki | < 30s full rebuild | — |
| Fallback rate | < 1% of queries | — |
| Entries missing required YAML fields | 0% (enforced by Module 23) | — |

---

## Attribution

| Element | Source |
|---------|--------|
| Metadata-gated retrieval, 60% → 95% R@10 | LongMemEval benchmark, Arora et al. 2025 |
| Score fusion design | Our design |
| ChromaDB | trychroma.com — Apache 2.0 |
| LanceDB | lancedb.com — Apache 2.0 |

---

## Related Modules

- `19_Memory_Architecture.md` — Tier 0 is the search corpus
- `21_Knowledge_Accretion.md` — write-time embedding pipeline feeds this module
- `23_Taxonomy_Enforcement.md` — controls vocabulary used in metadata filters
- `24_Verbatim_History_Mining.md` — same filter-first pattern applied to Tier 3
- `17_Temporal_Knowledge.md` — staleness signals used in recency boost
