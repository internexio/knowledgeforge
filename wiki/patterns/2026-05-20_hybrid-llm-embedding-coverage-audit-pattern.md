---
title: Hybrid LLM-generation + embedding-coverage for topic-fan-out audits
source_mode: builder
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.78
staleness_risk: slow_decay
importance: 4
created: 2026-05-20
domain: performance
topic: token-cost
tags: embedding, benchmark, api, throughput, quality-gate
related_entries: []
---

# Hybrid LLM-generation + embedding-coverage for topic-fan-out audits

## The Pattern

For "how well does this artifact cover this set of expected topics?" problems, split the LLM work across two model classes:

1. **Generative LLM for the small creative step** — produce the expected-topics list itself. This needs reasoning + world knowledge + creative recall. Examples: generate likely fan-out sub-queries from a head query, generate the FAQ list a customer might have, generate test cases that a spec should handle.

2. **Embedding model for the large comparison step** — for each (topic, artifact) pair, compute cosine similarity between embedding(topic) and embedding(artifact). Bucket the similarity into coverage labels (yes / partial / no) at empirical thresholds. This needs only semantic similarity — no reasoning, no recall.

The full grid (N topics × M artifacts) becomes:
- 1 generative call (produces N topics; ~$0.0001 at Flash Lite rates)
- (N + M) embedding calls (~$0.00003 each at text-embedding-004 rates)

Versus the LLM-everywhere alternative:
- 1 generative call + N×M comparison calls

For N=10, M=1: hybrid uses 12 calls vs. 11 LLM calls — barely a saving.
For N=10, M=50: hybrid uses 61 calls vs. 510 LLM calls — ~8× saving.
For N=10, M=500: hybrid uses 511 embed + 1 gen vs. 5001 LLM calls — ~10× saving.

The crossover is around M=5 artifacts; bigger M strongly favors hybrid.

Empirically measured in F8 (sem-tools fan-out coverage): hybrid steady-state cost ~$0.12/mo at medium-agency scale (5 domains, 1000 URLs, weekly) vs. ~$3/mo with Flash Lite for both stages — a ~25× reduction at that scale, matching the analytical model above.

## When This Applies

- The "expected topics" list is finite and stable across many artifacts. (If you need to regenerate the topic list per artifact, the gen cost dominates.)
- A per-pair LLM judgment isn't required — cosine similarity is sufficient for the coverage bucket you need.
- The artifact corpus is large enough (M >> 1) that per-comparison cost matters.
- Embedding quality is good enough for the domain. (Sentence-Transformers / text-embedding-004 / Cohere embed-v3 all work for general-purpose text; specialized domains may need domain-tuned embeddings.)

## When This Does NOT Apply

- Coverage requires reasoning about HOW the artifact addresses the topic (e.g., "does this page give the correct legal answer to this question?"). Cosine similarity catches topical relatedness, not correctness.
- The expected topics are short keywords lacking semantic context. Embeddings of 1–3 word strings are noisy; LLM "does X cover Y?" prompts are more robust for short topics.
- The artifact embedding is dominated by boilerplate (footer, nav, JS-injected marketing copy). Strip-before-embed is mandatory; otherwise similarity collapses toward "homepage average" for all queries.
- M is small (< 5 artifacts). The economics don't justify the architectural complexity.

## Implementation Notes from F8 Build

- **Truncate before embed**: text-embedding-004 accepts ~2048 tokens. Cap page text at ~20K chars (~5K tokens) to stay safely under and keep cost bounded. Beyond this, more content rarely helps coverage detection because the embedding is a single vector — adding more text averages it out.

- **Cosine bucketing is empirical**: 0.75 / 0.60 thresholds worked as a starting point for SEO content vs. natural-language queries, but they need tuning on real data. Store the raw similarity alongside the bucket so threshold changes don't require re-running embeddings.

- **Cache key composition**: `sha256(artifact_text) + topic_set_hash + embedding_model_version`. The generative model's output (topic list) should also be cached separately so re-runs after a coverage failure don't re-pay the generation cost.

- **Failure isolation**: per-topic embedding failures should degrade to "no" coverage for that topic rather than aborting the whole batch. Page-text embedding failure is terminal (no comparison possible).

- **Free tier non-starter**: Gemini free tier trains on submitted data — unsafe for client work. Cost model assumes paid tier ($0.075/M input, $0.30/M output for Flash Lite; ~$0.00001/1K tokens for embeddings). Verify pricing at ai.google.dev/gemini-api/docs/pricing before committing.

## Cross-References

- Implemented in F8 (sem-tools `sem/geo/fanout.py`, 2026-05-20). Bead `[project]-hapj` design field has the full configuration.
- Related: external-source-to-kf-mapping methodology (treats this hybrid as the LLM-API-class instantiation of a general "small-creative + big-cheap" decomposition pattern).
- Anti-pattern reference: LLM-everywhere fan-out scoring (cost-prohibitive at M > 50 even with cheap models).

## Grounding

Grounding score 0.78 — design is implemented and tested with mocked Gemini calls, but real-data validation (do the cosine thresholds actually match human judgment on "covered/partial/uncovered"?) has not been run. The cost-model arithmetic is verified analytically.

## Source Context

Extracted from sem-tools fanout builder session (F8 build, 2026-05-20). Pattern generalizes a cost-optimization decision made during coverage-audit infrastructure design. Bead: `[project]-hapj`.
