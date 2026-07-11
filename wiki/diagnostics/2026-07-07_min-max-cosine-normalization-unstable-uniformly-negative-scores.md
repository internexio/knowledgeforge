---
title: Min-max cosine normalization is unstable when all scores are uniformly negative
source_mode: debugger
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-07
domain: diagnostics
topic: calibration
tags: semantic-search, empirical, vector-db, quality-gate
related_entries:
  - diagnostics/2026-05-24_threshold-vs-empirical-calibration-gap-similarity-systems.md
  - integration/2026-07-07_mempalace-search-frontmatter-drawer-pattern.md
revises: null
superseded_by: null
---

# Min-max Cosine Normalization is Unstable When All Scores are Uniformly Negative

## Pattern

When a vector store returns cosine similarity scores that are uniformly negative (e.g., all in [-0.4, -0.01]), min-max normalization maps that range to [0, 1]. The result: the semantically least-bad candidate scores ~0.9 and the worst scores ~0.0 — which can be higher than the absolute semantic relevance deserves. Importance and recency components then dominate the final fusion score.

## Concrete Verification (2026-07-07)

During Module 22 Phase 2 implementation, `tool_search` queries against the `wiki-kf-core` MemPalace collection (ChromaDB with all-MiniLM-L6-v2) returned results like:

```
nginx query → similarities: [-0.014, -0.268, -0.299, -0.301, -0.318, ...]
```

All scores negative. After min-max normalization with lo=-0.377, hi=-0.014:
- Score -0.014 → norm_cosine ≈ 0.98
- Score -0.377 → norm_cosine = 0.0

The entry with sim=-0.014 (`react-route-shadows-rsynced-static-html`) was not semantically related to the query but ranked highest after fusion because its normalized cosine was 0.98.

## Root Cause

MemPalace uses ChromaDB with all-MiniLM-L6-v2 or similar embedding models. Cosine similarities between text chunks in this embedding space are often slightly negative when the query and chunk are loosely related. The raw values carry ordinal meaning (higher = more similar), but their absolute scale is meaningless. Min-max normalization preserves the ordinal ranking correctly, but inflates the contribution of a marginally-better candidate when the entire pool is in negative territory.

## Consequence for Score Fusion

In score fusion `0.65·norm_cosine + 0.20·importance + 0.15·recency`:
- When cosine scores are all near zero (negative but close together), the 0.65 weight doesn't help much
- Importance and recency effectively determine ranking
- Entries with high importance (4-5) and recent creation dates float to the top regardless of semantic relevance
- **The metadata filter (domain/topic) becomes the primary correctness mechanism**, not the semantic ranking

## Mitigation Applied (Module 22 Phase 2)

In the Module 22 Phase 2 implementation, the solution was:

1. **Domain filter as correctness gate** — `_passes_filter(fm, domain, topic, tags)` excludes off-domain entries before score fusion runs. This is the real fix.
2. **Only inject wiki context when domain is inferred** — `_fetch_wiki_context` returns early when `domain=None`, preventing noise from empty-domain legacy entries

A threshold-based approach (skip injection if best raw cosine < X) was considered but rejected as fragile — the domain filter is more semantically meaningful.

## When This Applies

- Score fusion over MemPalace/ChromaDB wiki corpora with ~300-3000 entries
- Any vector search result set where all raw cosine scores are negative
- Retrieval-augmented generation where you need to decide whether to inject context
- Weighted multi-component scoring where semantic signal is weak and metadata dominates

## When This Does NOT Apply

- Large corpora with high-signal queries that produce positive cosine scores (e.g., exact phrasing match)
- BM25/lexical search (different scoring range)
- Re-ranking models that produce calibrated probability scores rather than raw cosine values
- Score fusion where domain/topic metadata are unavailable or unreliable

## Source Context

Module 22 Phase 2 implementation session (knowledgeforge-core-acu-phase2-2026-07-07). Discovery: semantic wiki search over ChromaDB-backed MemPalace revealed that min-max normalization of negative-only similarity pools inflates marginal differences, making metadata filters the primary correctness gate rather than semantic similarity. The entry documents the failure mode and the domain-first filtering mitigation.
