# Taxonomy Enforcement

## Module Metadata

```yaml
module:
  title: Taxonomy Enforcement
  version: 6.8.0
  purpose: Fixed controlled vocabulary for wiki entry domain/topic/tags, enforced at write time — prevents taxonomy drift, maintains Module 22 metadata filter reliability, and ensures cross-session consistency of knowledge classification
  topics: [taxonomy, controlled-vocabulary, knowledge-classification, write-time-validation, metadata-quality]
  contexts: [knowledge-accretion, wiki-filing, accretion-gate, linter-runs]
  difficulty: intermediate
  related: [21_Knowledge_Accretion, 22_Semantic_Wiki_Search, 19_Memory_Architecture, 17_Temporal_Knowledge]
  added_in: "6.5"
  changelog:
    6.8.0:
      date: 2026-06-20
      driver: knowledgeforge-core-sd3
      changes:
        - |-
          Added schema-evolution topic to migrations domain. Migrated the one
          existing migrations entry (2026-06-12_schema-evolution-additive-
          optional-fields.md) off the self-referential migrations -> migrations
          topic to migrations -> schema-evolution. Same anti-pattern as the
          deprecated orchestration self-topic; this resolves it for the
          migrations domain.
        - |-
          Total migrations topic count 1 -> 2 (error-classification +
          schema-evolution). Summary table at end of doc updated to match.
        - Partial close of sd3 (migrations sub-task). Compiler + orchestration
          sub-tasks still open — they need operator decisions on re-topic vs
          re-domain (compiler) and minimum-vs-full new topic set (orchestration).
    6.7.1:
      date: 2026-06-20
      driver: knowledgeforge-core-a05
      changes:
        - Fix YAML parse warning surfaced during kf-cc compile — 6.7.0
          changelog had a bullet starting with a backtick (`` `seo-strategy`...``)
          which YAML rejects as a non-token. Rephrased to start with a word.
          No semantic change; vocab unchanged.
    6.7.0:
      date: 2026-06-20
      driver: knowledgeforge-core-a05
      changes:
        - Pruned 5 SEO-domain leakage topics flagged in 6.6.0 — `keyword-repositioning`,
          `keyword-research-methodology`, `keyword-selection` from methodologies;
          `google-ads`, `serp-ranking-diagnosis` from diagnostics. The four entries
          actually using these topics (plus 3 more under the orphan `seo-strategy`
          domain) belong in sem-tools/wiki/, not KF-core — relocation tracked by
          successor bead knowledgeforge-core-56c. M23 vocab cleanup lands now so
          new SEO entries can no longer accrete into KF-core under these topics.
        - Total methodologies topic count 21 → 18. Total diagnostics topic count
          28 → 26. Summary tables at end of doc updated to match.
        - The seo-strategy domain (never in vocab; grandfathered) and its 7
          entries remain in place until the move bead executes — see -56c for plan.
    6.6.0:
      date: 2026-06-10
      driver: knowledgeforge-core-e0x
      spec: docs/planning/2026-06-10_module-23-vocabulary-drift-reconciliation-spec.md
      changes:
        - Added 5 new domains (methodologies, diagnostics, orchestration, migrations, compiler)
          covering 51% of wiki entries previously in directories absent from v6.5.x vocab.
          Topic lists are empirical baselines extracted from on-disk frontmatter (55 topics
          observed across the 5 directories), not speculative derivations.
        - Total domain count 10 → 15. Tag cap unchanged at 57/60 approved tags.
        - Added Grandfathering section after Vocabulary Extension Protocol — entries with
          creation timestamp before 2026-06-10 are NOT retroactively required to carry
          domain/topic fields. New entries strict; existing entries lazy-migrate.
        - |-
          Creation timestamp resolution order — created: frontmatter → git first-commit date
          → file mtime. Git fallback covers the 3 entries identified during Phase 0 audit
          that lack created: entirely.
        - |-
          Forgery resistance — linter MEDIUM finding on ±1 day created: vs git first-commit
          divergence. Cultural norm, not cryptographic enforcement.
        - |-
          Deprecated patterns/orchestration topic (collision with new orchestration domain).
          DEPRECATED-not-deleted — still validates on grandfathered entries; new entries
          should use the new orchestration domain.
        - |-
          Extension event counting interpretation locked: one bead = one Vocabulary
          Extension Protocol invocation = one event (regardless of how many domains added).
          This bead consumes 1 of v6.x's 5-event budget; 4 remain.
    6.5.2: |
      - Updated Module 22 cross-reference to acknowledge Phase 1 vs Phase 2 split
        (knowledgeforge-core-8xq). Phase 1 of M22 does NOT consume Module 23's
        vocabulary at retrieval time — frontmatter is preserved at write time for
        Phase 2 readiness only. Write-time validation in this module remains
        mandatory: it is what makes Phase 2 deployable when triggered.
      - Module 24 cross-reference (Integration Points) updated to qualify
        cross-tier filtering as Phase 2 Deferred — the Tier 0 half of the
        cross-tier filter is M22 Phase 2 work. Caught by fourth critic pass
        as a reverse-direction reference.
      - No vocabulary changes.
    6.5.1: |
      - Vocabulary extension: added 3 tags (scheduling, packaging, filesystem)
        based on infrastructure-domain audit. scheduling distinguishes cron /
        systemd / launchd patterns from generic deployment; packaging
        distinguishes artifact preparation (wheel / npm / Docker image) from
        release; filesystem distinguishes file-layout / atomic-rename / perms
        from generic infrastructure.
      - Vocabulary contraction: removed the tag `infrastructure` (tautological
        with the `infrastructure` domain — added no filter discrimination).
        Migrated 3 active entries off the deprecated tag.
      - Net change: 55 → 57 approved tags. 3 slots below the 60-tag cap.
      - No domain or topic changes.
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
      - orchestration   # DEPRECATED 6.6.0 — new entries should use the orchestration domain. Still validates on grandfathered entries.

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

  # --- ADDED 6.6.0 (bead e0x) ---
  # Topic lists are empirical baselines from on-disk frontmatter, NOT speculative.
  # Sparse domains (migrations, compiler, orchestration) reflect undercoverage in
  # the existing wiki; future extensions add topics on as-needed basis via the
  # Vocabulary Extension Protocol (one-domain-per-topic micro-extension).

  methodologies:
    # Process patterns for doing work. Distinct from `patterns` (content-level
    # patterns) because methodologies describe WORK, not artifacts.
    topics:
      - acceptance-criteria
      - artifact-discipline
      - bead-triage-workflow
      - conflict-recovery
      - decision-framework
      - deployment-sequencing
      - experiment-design
      - gate-design
      - measurement-methodology
      - prioritization
      - propagation-discipline
      - quality-gate
      - risk-assessment
      - scope-management
      - staged-rollout
      - trade-off-analysis
      - validation

  diagnostics:
    # Concrete problem→fix patterns. Distinct from `debugging` (the act);
    # diagnostics is the documented residue.
    topics:
      - api-design
      - calibration
      - classification
      - data-integrity
      - data-quality
      - data-validation
      - error-classification
      - error-handling
      - hypothesis-testing
      - intent-vs-execution
      - issue-tracking
      - liveness
      - measurement-logic
      - multi-repo-workflows
      - ops
      - queue-observability-pitfall
      - refactoring
      - reporting
      - retrospective-analysis
      - root-cause-analysis
      - server-configuration
      - test-isolation
      - testing
      - threshold-tuning
      - watchdog
      - workflow-discipline

  orchestration:
    # Multi-agent / multi-process workflow coordination patterns.
    # Note: topic `orchestration` (self-referential) is preserved but DEPRECATED.
    # New entries should pick a more specific topic.
    topics:
      - epic-closure-workflow
      - multi-stage-issue-workflow
      - orchestration                    # DEPRECATED 6.6.0 — self-referential; pick a specific topic
      - recovery

  migrations:
    # State transitions, schema migrations, vendor swaps, data backfills.
    # Sparse — most existing entries are grandfathered without topic. Expand via
    # Vocabulary Extension Protocol when new topics are needed.
    topics:
      - error-classification
      - schema-evolution

  compiler:
    # KF-internal infrastructure — kf-compile.py and platform-binding shapes.
    topics:
      - ci-cd
      - version-incompatibility
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
  - scheduling      # added 6.5.1 — cron / systemd / launchd / APScheduler patterns
  - packaging       # added 6.5.1 — artifact preparation (wheel / npm / Docker image) distinct from deployment
  - filesystem      # added 6.5.1 — file-layout / atomic-rename / permissions / path semantics
  - gpu
  - compute
  # `infrastructure` tag removed in 6.5.1 — tautological with domain `infrastructure`; added no filter discrimination

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

This list is version-controlled. Tags may be added only through the Vocabulary Extension Protocol (below). Current count: 57 approved tags.

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

## Grandfathering — Pre-Gate Entries (Added 6.6.0)

The M23 write-time gate enforces vocabulary on entries CREATED AFTER its
introduction. Entries that pre-date the gate (or pre-date a vocabulary
extension that would have applied to them) are NOT retroactively required
to carry the full schema.

A wiki entry is `grandfathered` if its creation timestamp is before
2026-06-10 (M23 v6.6.0 release date). Creation timestamp is resolved in
this order:

1. **`created:` frontmatter field** if present AND not obviously hand-forged
   (see "Forgery resistance" below).
2. **First-commit date from git history** as a fallback for entries lacking
   `created:` (the 3 entries identified during Phase 0 audit of bead e0x).
3. **File mtime** as a last resort (only when git history is unavailable,
   e.g., entries created in a session before being committed).

**Grandfathered entry validity:**
- `title`, `source_mode`, `novelty_type`, `grounding_score`, `staleness_risk`,
  `importance` remain REQUIRED for all entries.
- `domain`, `topic` are OPTIONAL on grandfathered entries.
- `tags` remain REQUIRED, with all values from the approved list.

**New entries (post-v6.6.0)** MUST include `domain` and `topic` per the
expanded vocabulary. No grandfathering applies. New entries lacking
`created:` are NOT grandfathered — the gate adds the field at write time.

**Lazy migration:** When a contributor touches a grandfathered entry for
any other reason (content update, related-entries fix, supersession),
they SHOULD add `domain` and `topic` at that time. Lazy schema completion
without a forced sweep.

**Bulk migration** of grandfathered entries to full schema is OUT of scope
for this release. Tracked separately in bead `knowledgeforge-core-96p`
(P4 — triggered when M22 Phase 2 acu activates).

### Forgery resistance (acknowledged honor system)

The `created:` field is editable in the markdown frontmatter. A
contributor can backdate `created:` to bypass the gate. This is an
honor system, not a cryptographic enforcement. Mitigations:

1. **Linter check** (added in 6.6.0, see Module 21 linter protocol):
   compare `created:` against the entry's first-commit date in git
   history. Divergence beyond ±1 day raises a MEDIUM finding
   ("possible backdated entry").
2. **PR review surface:** the linter's MEDIUM finding surfaces in
   routine knowledge-base health checks, giving a human reviewer a
   signal to investigate.
3. **Cultural norm:** grandfathering is documented as a transitional
   mechanism, not a permanent escape hatch.

Cryptographic enforcement would require signed git commits + per-entry
commit-hash binding in frontmatter — out of scope. The lighter detection
mechanism is adequate given the threat model (no adversarial contributors;
the only risk is sloppy bypass-for-convenience).

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
**As of M22 v7.3.0, Phase 1 of Module 22 does not consume this module's vocabulary at retrieval time.** Phase 1 wires only the wing-less duplicate-check gate (`mempalace_check_duplicate`). Module 22's metadata pre-filter — which reads `domain`, `topic`, and `tags` as controlled vocabulary — is Phase 2 (Deferred), triggered by observed evidence (see M22's Phase 2 Upgrade Triggers). Write-time enforcement here remains mandatory: it is the prerequisite that lets Phase 2 deploy cleanly when triggered. If Module 23 is bypassed before Phase 2 lands, the Phase 2 filter — when activated — would degrade toward the unfiltered ~60% R@10 baseline.

### Module 19 (Memory Architecture)
The taxonomy vocabulary is a Tier 0 artifact — it lives in `wiki/taxonomy/vocabulary.yaml` and is version-controlled alongside wiki entries.

### Module 24 (Verbatim History Mining)
Tier 3 entries (verbatim conversation turns stored in MemPalace) also use Module 23's domain/topic/tag vocabulary. **When M22 Phase 2 lands (knowledgeforge-core-acu)**, this enables cross-tier metadata filters — a query scoped to `domain=architecture, topic=memory-systems` will simultaneously retrieve wiki entries (Module 22 Phase 2) and historical turns (Module 24) in a single coherent filter pass. In Phase 1, this cross-tier filter is NOT active on the Tier 0 side — M22's frontmatter-based filter is deferred. Write-time vocabulary enforcement here remains mandatory so Phase 2 can deploy cleanly when triggered.

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
- `24_Verbatim_History_Mining.md` — Tier 3 entries also use this vocabulary; cross-tier filtering activates when M22 Phase 2 lands (knowledgeforge-core-acu)
- `17_Temporal_Knowledge.md` — `staleness_risk` values are also a controlled vocabulary (same principle)

## CC Doc

# Module 23: Taxonomy Enforcement — Execution Protocol
**Apply when:** [KF-ROUTE] load list includes M23, or a wiki entry is being filed (Gate 4a in M21 pipeline)

Fixed controlled vocabulary for wiki entry domain/topic/tags, enforced at write time. Free-form tagging produces synonym fragmentation that degrades M22 filter reliability.

## Three-Tier Hierarchy

```
domain (required, single value)
  └── topic (required, single value)
        └── tags (required, 1–5 values, all from approved list)
```

All three levels required. Missing any → rejection.

## Controlled Vocabulary

### Domains and Topics

| Domain | Topics |
|--------|--------|
| `architecture` | memory-systems, routing, mode-design, chain-design, knowledge-accretion, decision-classification |
| `patterns` | retrieval, decay, classification, synthesis, validation, orchestration |
| `anti-patterns` | over-routing, context-bloat, compression-loss, hallucination, mode-collapse |
| `performance` | latency, throughput, token-cost, cache, index-efficiency |
| `integration` | mcp-protocol, vector-db, llm-api, external-tools, sidecar-services |
| `research` | benchmarks, neuro-symbolic, memory-systems, agent-coordination, retrieval-augmented-generation |
| `strategy` | prioritization, trade-off-analysis, risk-assessment, scope-management |
| `infrastructure` | deployment, ops, ci-cd, observability, server-configuration |
| `debugging` | root-cause-analysis, regression-detection, hypothesis-testing, error-classification |
| `security` | threat-model, access-control, data-isolation, attack-surface |
| `methodologies` | acceptance-criteria, artifact-discipline, bead-triage-workflow, conflict-recovery, decision-framework, deployment-sequencing, experiment-design, gate-design, measurement-methodology, prioritization, propagation-discipline, quality-gate, risk-assessment, scope-management, staged-rollout, trade-off-analysis, validation |
| `diagnostics` | api-design, calibration, classification, data-integrity, data-quality, data-validation, error-classification, error-handling, hypothesis-testing, intent-vs-execution, issue-tracking, liveness, measurement-logic, multi-repo-workflows, ops, queue-observability-pitfall, refactoring, reporting, retrospective-analysis, root-cause-analysis, server-configuration, test-isolation, testing, threshold-tuning, watchdog, workflow-discipline |
| `orchestration` | epic-closure-workflow, multi-stage-issue-workflow, orchestration (deprecated), recovery |
| `migrations` | error-classification, schema-evolution |
| `compiler` | ci-cd, version-incompatibility |

**Grandfathering (6.6.0):** Entries with creation timestamp before 2026-06-10 are exempt from `domain`/`topic` requirement. See main body for full grandfathering policy. The `patterns/orchestration` topic is DEPRECATED — new entries should use the `orchestration` domain instead.

### Approved Tags (57 total)

```
retrieval, recall, decay, importance-weighting, temporal, verbatim, semantic-search,
metadata-filter, embedding, vector-index,
routing, classification, mode-activation, chain, delegation,
grounding, confidence, adversarial, quality-gate, hallucination-risk,
tier-0, tier-1, tier-2, tier-3, accretion, taxonomy,
latency, token-cost, throughput, benchmark,
mcp, api, sidecar, vector-db,
deployment, scheduling, packaging, filesystem, gpu, compute,
empirical, theoretical, experimental, peer-reviewed,
stable, volatile, pinned, archived, superseded
```

## Validation Protocol (Gate 4a)

**Gate 1 — Domain:** `entry.domain` must be in taxonomy keys. On fail: reject with nearest-match.
**Gate 2 — Topic:** `entry.topic` must be in `taxonomy[domain].topics`. On fail: reject with nearest-match for that domain.
**Gate 3 — Tags:** Each tag must be in `approved_tags`. Count must be 1–5. On fail: reject with nearest-match. **Never auto-assign.** `suggest_nearest` is advisory only.

Nearest-match uses Levenshtein distance, returns top-2 candidates.

## Vocabulary Extension

New terms require: justification, scope, 2+ sample entries, update to this file, version bump, and M22 index rebuild. Tag count cap: 60. Before adding, verify no existing term covers it.
