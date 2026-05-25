---
title: Threshold-vs-empirical calibration gap in similarity-based systems
source_mode: builder
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-05-24
domain: debugging
topic: hypothesis-testing
tags: empirical, semantic-search, vector-db, quality-gate, confidence
related_entries:
  - methodologies/2026-05-14_healthy-system-gate-trap-empirical-thresholds.md
  - diagnostics/2026-05-23_threshold-tune-illusion-data-caps-flatline-sensitivity.md
  - strategy/2026-05-21_vendor-selection-calibration-uncertainty-dominance.md
revises: null
superseded_by: null
---

# Threshold-vs-Empirical Calibration Gap in Similarity-Based Systems

## The Diagnostic

Specifications that pick round-number thresholds for similarity systems ("very similar = 0.9 cosine similarity") may be empirically unreachable when the underlying system chunks content at different granularity than the query. Always probe empirical scores against representative data BEFORE locking thresholds in spec — and especially before treating a threshold as functional for production behavior.

## Concrete Instance (knowledgeforge-core-rk4, 2026-05-25)

Module 22 Phase 1 spec mandated `tool_check_duplicate(content, threshold=0.9)` as the accretion gate for near-duplicate detection in MemPalace (ChromaDB-backed).

Empirical probe against MemPalace's 2415-drawer wiki collection:

| Test content | Top-5 raw similarities |
|---|---|
| Exact-match wiki file (6889 chars, already mined) | 0.889, 0.414, 0.385, 0.340, 0.340 |
| Synthetic novel content with unique tag marker | -0.036, -0.073, -0.075, -0.136, -0.146 |
| Near-domain novel (different topic, related tech) | -0.179, -0.204, -0.215, -0.224, -0.236 |

**Key finding:** The exact-content match scored 0.889 — just below the 0.9 threshold. At threshold 0.9, even re-filing identical content would not trigger the dup-check. Phase 1 would ship as effectively a no-op.

## Why This Happens

MemPalace mines wiki files into smaller drawers (chunked storage). Each drawer in the collection is a fragment of an original file. When `tool_check_duplicate` is called with the full file content, ChromaDB embeds the full file as a single query vector and compares against drawer-fragment vectors. The granularity mismatch (long query vector vs short drawer vector) loses semantic precision: even exact-content queries cap at ~0.85-0.89 similarity to any single drawer.

The 0.9 threshold was specified in good faith based on the intuition "near-duplicate = 0.9 cosine." Empirical reality with chunked storage is "exact match maxes at 0.89."

## When to Apply

- ANY similarity-based gating with a threshold (dup-check, near-match retrieval, semantic search filtering)
- When the spec mentions a round-number threshold (0.9, 0.95, 0.8) without empirical grounding
- When the underlying storage chunks/fragments content (RAG systems, vector DBs with auto-chunking)
- Before declaring a similarity-based gate "ready to ship"

## How to Run the Calibration Probe

```python
from <similarity_tool> import <query_fn>
from <vector_store> import <get_collection>

col = get_collection()
print(f"Collection size: {col.count()}")

# Test 1: query content known to be in the collection
known_content = <read a file already indexed>
results = col.query(query_texts=[known_content], n_results=5)
print("Exact-match top-5:", [round(1 - d, 3) for d in results['distances'][0]])

# Test 2: query novel content
novel = "<deliberately novel text>"
results = col.query(query_texts=[novel], n_results=5)
print("Novel top-5:", [round(1 - d, 3) for d in results['distances'][0]])

# Test 3: near-domain content (related topic, new wording)
near = "<plausible new content in same domain>"
results = col.query(query_texts=[near], n_results=5)
print("Near-domain top-5:", [round(1 - d, 3) for d in results['distances'][0]])
```

Set threshold = (exact-match-floor - 0.04). Below novel-noise-ceiling. Margin between them indicates how robust the threshold is.

## Calibration Rule

- **Threshold below exact-match floor by ~0.04**: catches exact and near-exact dupes; safe margin
- **Threshold above novel-noise ceiling by ~0.3**: avoids false positives on unrelated content
- **Threshold in between**: warn at this level; tune up or down based on tolerance for false pos vs false neg

For the MemPalace case: exact floor = 0.889, novel ceiling = -0.04. Threshold 0.85 catches exact-content while having 0.89 margin to noise. That's the calibrated value.

## Anti-Pattern: Spec-Literal Compliance with Empirically Broken Values

If empirical data shows a spec'd threshold is unreachable, "ship at the spec value" delivers a non-functional implementation. Better: report the calibration finding, surface to decision-maker, recalibrate spec OR document the empirical exception.

In rk4 the resolution was: ship at 0.85 (calibrated), bump M22 to v7.3.1, update spec with the empirical rationale, preserve the original 0.9 in changelog as the pre-calibration assumption.

## When NOT to Apply

- Threshold systems where the spec value comes from VALIDATED experiment (not a guess) — trust the experiment
- One-shot decision threshold where exact value doesn't matter (e.g., "fire any warning if > 0") — calibration adds no value
- Systems where chunking granularity matches query granularity (e.g., per-paragraph stores queried by paragraph) — granularity mismatch isn't a factor

## Related

- See knowledgeforge-core-rk4 commit notes for the threshold recalibration
- The spec-to-implementation gap pattern (filed separately) explains why this wasn't caught in 6 prior critic passes — they reviewed spec values, not empirical behavior
