# Taxonomy Enforcement

## Module Metadata

```yaml
module:
  title: Taxonomy Enforcement
  version: 6.5.0
  purpose: Fixed controlled vocabulary for wiki entry domain/topic/tags, enforced at write time — prevents taxonomy drift, maintains Module 22 metadata filter reliability, and ensures cross-session consistency of knowledge classification
  topics: [taxonomy, controlled-vocabulary, knowledge-classification, write-time-validation, metadata-quality]
  contexts: [knowledge-accretion, wiki-filing, accretion-gate, linter-runs]
  difficulty: intermediate
  related: [21_Knowledge_Accretion, 22_Semantic_Wiki_Search, 19_Memory_Architecture, 17_Temporal_Knowledge]
  added_in: "6.5"
  changelog:
    6.5.0: |
      - Initial module — fixed vocabulary enforcement as accretion gate
      - Three-tier hierarchy: domain → topic → tags
      - 10 domains, ~40 topics, ~55 approved tags
      - Write-time rejection with nearest-match suggestion
      - Vocabulary extension protocol with version bump requirement
      - Anti-patterns: free-form tagging, query-time inference, synonym aliasing
```

---

## Core Approach

Free-form tagging produces synonymous but distinct tags — `retrieval`, `recall`, `lookup`, `search` — that fracture the filter set over time. By version 50 of a wiki, uncontrolled tagging produces ~40% tag fragmentation: entries about the same concept become unfindable via metadata filter because they carry different labels. Fixed vocabulary at write time costs nothing; remediation after fragmentation is expensive.

**Assignment at write, not at query.** The taxonomy is enforced once — when an entry is accreted (Module 21). At query time, the filter reads `domain`, `topic`, and `tags` as reliable. No inference, no normalization, no synonym expansion at query time.

**Three-tier hierarchy:**

```
domain (required, single value)
  └── topic (required, single value)
        └── tags (required, 1–5 values, all from approved list)
```

All three levels are required. An entry without all three is rejected at the Module 21 accretion gate.

---

## Controlled Vocabulary

### Domains and Topics

```yaml
taxonomy:
  architecture:
    topics:
      - memory-systems
      - routing
      - mode-design
      - chain-design
      - knowledge-accretion
      - decision-classification

  patterns:
    topics:
      - retrieval
      - decay
      - classification
      - synthesis
      - validation
      - orchestration

  anti-patterns:
    topics:
      - over-routing
      - context-bloat
      - compression-loss
      - hallucination
      - mode-collapse

  performance:
    topics:
      - latency
      - throughput
      - token-cost
      - cache
      - index-efficiency

  integration:
    topics:
      - mcp-protocol
      - vector-db
      - llm-api
      - external-tools
      - sidecar-services

  research:
    topics:
      - benchmarks
      - neuro-symbolic
      - memory-systems
      - agent-coordination
      - retrieval-augmented-generation

  strategy:
    topics:
      - prioritization
      - trade-off-analysis
      - risk-assessment
      - scope-management

  infrastructure:
    topics:
      - deployment
      - ops
      - ci-cd
      - observability
      - server-configuration

  debugging:
    topics:
      - root-cause-analysis
      - regression-detection
      - hypothesis-testing
      - error-classification

  security:
    topics:
      - threat-model
      - access-control
      - data-isolation
      - attack-surface
```

### Approved Tags

Tags are flat, domain-agnostic, and shared across all domains. Any approved tag may appear under any domain.

```yaml
approved_tags:
  # Retrieval and memory
  - retrieval
  - recall
  - decay
  - importance-weighting
  - temporal
  - verbatim
  - semantic-search
  - metadata-filter
  - embedding
  - vector-index

  # Modes and routing
  - routing
  - classification
  - mode-activation
  - chain
  - delegation

  # Quality and validation
  - grounding
  - confidence
  - adversarial
  - quality-gate
  - hallucination-risk

  # Architecture
  - tier-0
  - tier-1
  - tier-2
  - tier-3
  - accretion
  - taxonomy

  # Performance
  - latency
  - token-cost
  - throughput
  - benchmark

  # Integration
  - mcp
  - api
  - sidecar
  - vector-db

  # Infrastructure
  - deployment
  - gpu
  - compute
  - infrastructure

  # Research provenance
  - empirical
  - theoretical
  - experimental
  - peer-reviewed

  # Knowledge lifecycle
  - stable
  - volatile
  - pinned
  - archived
  - superseded
```

This list is version-controlled. Tags may be added only through the Vocabulary Extension Protocol (below). Current count: 55 approved tags.

---

## Validation Protocol

Enforced as Gate 4a in the Module 21 accretion pipeline (before grounding check, before embedding):

### Gate 1 — Domain Validation

```
IF entry.domain NOT IN taxonomy.keys():
  REJECT: "Unknown domain '{entry.domain}'.
           Valid domains: {taxonomy.keys()}
           Nearest: {suggest_nearest(entry.domain, taxonomy.keys())}"
```

### Gate 2 — Topic Validation

```
IF entry.topic NOT IN taxonomy[entry.domain].topics:
  REJECT: "Unknown topic '{entry.topic}' under domain '{entry.domain}'.
           Valid topics: {taxonomy[entry.domain].topics}
           Nearest: {suggest_nearest(entry.topic, taxonomy[entry.domain].topics)}"
```

### Gate 3 — Tag Validation

```
FOR each tag in entry.tags:
  IF tag NOT IN approved_tags:
    REJECT: "Unknown tag '{tag}'.
             Nearest approved tag: {suggest_nearest(tag, approved_tags)}
             To add '{tag}', follow the extension protocol."

IF len(entry.tags) < 1:
  REJECT: "At least 1 tag required."

IF len(entry.tags) > 5:
  REJECT: "Maximum 5 tags per entry. Current count: {len(entry.tags)}"
```

### Suggestion Function

`suggest_nearest(candidate, vocabulary)` uses Levenshtein distance (default) or semantic similarity if an LLM is available. Returns top-2 candidates.

```
suggest_nearest("recall-rate", approved_tags)
→ ["recall", "retrieval"]

suggest_nearest("vector-database", approved_tags)
→ ["vector-db", "vector-index"]
```

`suggest_nearest` is advisory only. It does not auto-assign. The caller must provide a valid term; the suggestion is a hint to assist selection.

---

## Vocabulary Extension Protocol

Adding a new term requires:

1. **Justification:** The new term must not be expressible as a combination of existing terms.
2. **Scope:** Specify whether it's a domain, topic under a specific domain, or a tag.
3. **Sample entries:** At least 2 wiki entries that would use it.
4. **Update:** Modify the vocabulary block in this module file.
5. **Version bump:** Module 23 version increments on every vocabulary change.
6. **Index rebuild:** Trigger Module 22 index rebuild after vocabulary extension to re-classify pending entries.

**Vocabulary contraction (deprecating a term):** Migrate all entries using the deprecated term before removing it. Never silently drop a term with active entries.

**Frequency cap:** Aim to keep approved tags ≤ 60. Above 60, the vocabulary becomes unwieldy — new contributors don't know which tags to use and fragmentation risk rises. Before adding a term, consider whether an existing term covers it.

---

## Anti-Patterns

| Anti-Pattern | Consequence | Correct Approach |
|---|---|---|
| Free-form tagging at write time | Tag fragmentation; `retrieval`, `recall`, `lookup` become three separate filter buckets within months | Fixed vocabulary, reject at write |
| Query-time taxonomy inference | Tags on entries become unreliable; filter results vary with model version | Assign once at write, treat as static |
| Synonym aliasing at query time (`recall` → also search `retrieval`) | Coupling between Module 23 and Module 22 query logic; breaks when vocabulary updates | Enforce vocabulary so synonyms never enter the index |
| Domain-specific tag namespacing (`architecture/retrieval` vs `patterns/retrieval`) | Tags become domain-scoped and lose cross-domain utility; filter complexity doubles | Tags are flat and shared across all domains |
| Growing vocabulary without pruning | Approved list grows unmanageable; cap at ~60 tags | Enforce vocabulary frequency cap; prune on major version |
| Accepting a near-match without confirmation | Silent taxonomy drift from automated "close enough" assignments | Suggest nearest, reject if candidate ≠ approved term. Never auto-assign. |

---

## Integration Points

### Module 21 (Knowledge Accretion)
Taxonomy validation runs as Gate 4a in the Module 21 filing protocol, before grounding check and before embedding. An entry that fails taxonomy validation is rejected — returned to the caller with specific rejection reason and nearest-match suggestions. Module 21 does not file entries with invalid taxonomy.

### Module 22 (Semantic Wiki Search)
Module 22's metadata pre-filter reads `domain`, `topic`, and `tags` and treats them as controlled vocabulary. The filter's reliability guarantee depends entirely on Module 23 enforcement at write time. If Module 23 is bypassed, Module 22 accuracy degrades toward the unfiltered ~60% R@10 baseline.

### Module 19 (Memory Architecture)
The taxonomy vocabulary is a Tier 0 artifact — it lives in `wiki/taxonomy/vocabulary.yaml` and is version-controlled alongside wiki entries.

### Module 24 (Verbatim History Mining)
Tier 3 entries (verbatim conversation turns stored in MemPalace) also use Module 23's domain/topic/tag vocabulary. This enables cross-tier metadata filters — a query scoped to `domain=architecture, topic=memory-systems` retrieves relevant wiki entries (Module 22) and relevant historical turns (Module 24) in a single coherent filter pass.

---

## Constraints

- Vocabulary file is the single source of truth. Validation logic reads from it, not hardcoded terms.
- Vocabulary changes require a module version bump and changelog entry.
- The module must reject unknown taxonomy values — not warn-and-continue. Soft validation is not validation.
- `suggest_nearest` is advisory only. It does not auto-assign.

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Tag fragmentation rate (synonymous terms in index) | 0% (prevented at write) |
| Entries with invalid taxonomy in active wiki | 0% |
| Rejection rate with actionable suggestion provided | 100% of rejections include nearest-match suggestion |
| Vocabulary extension events per major version | ≤ 5 (stability signal) |
| Approved tag count | ≤ 60 |

---

## Attribution

| Element | Source |
|---------|--------|
| Controlled vocabulary principle | Ranganathan's PMEST faceted classification (adapted) |
| Tag fragmentation risk | Hearst et al., "Tag Semantics and Retrieval" (adapted) |
| Three-tier hierarchy design | Our design |

---

## Related Modules

- `21_Knowledge_Accretion.md` — taxonomy validation is Gate 4a in the filing protocol
- `22_Semantic_Wiki_Search.md` — filter reliability depends on controlled vocabulary
- `19_Memory_Architecture.md` — vocabulary file is a Tier 0 artifact
- `24_Verbatim_History_Mining.md` — Tier 3 entries also use this vocabulary for cross-tier filtering
- `17_Temporal_Knowledge.md` — `staleness_risk` values are also a controlled vocabulary (same principle)
