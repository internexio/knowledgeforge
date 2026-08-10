# Entity Relationship Analysis

## Module Metadata

```yaml
module:
  title: Entity Relationship Analysis
  version: 7.1.0
  purpose: Extract entities and their relationships from queries and context to improve routing accuracy, multi-hop reasoning, and memory retrieval — single-entity analysis misses relational complexity that changes which mode and chain is correct
  topics: [entity-extraction, relationship-mapping, routing-signals, multi-hop, graph-analysis]
  contexts: [decision-classification, mode-routing, memory-retrieval, coordinator-planning]
  difficulty: intermediate
  related: [13_Decision_Classification, 19_Memory_Architecture, 22_Semantic_Wiki_Search, 03_Coordination_Patterns, 18_Salience_Allocation, 10_Strategist_Agent]
  added_in: "6.5"
  changelog:
    7.1.0:
      date: 2026-06-12
      driver: knowledgeforge-core-8gp
      spec: docs/planning/2026-06-12_module-25-entity-path-glob-resolver-spec.md
      changes:
        - Added entity_paths resolver — ERA now produces entity_paths dict (glob patterns keyed by entity) alongside the existing memory_filter.
        - Recommended resolver shape — GitNexus-primary with session-cached grep fallback. Cache key is (entity_name, repo_root) to prevent multi-repo session contamination.
        - Glob derivation rules — single-file, N-in-dir, N-across-dirs, max-5-cap. Comparison function specified deterministically (literal-character prefix count + lexicographic tiebreak).
        - Added resolver_source diagnostic metadata — records which resolver (gitnexus, grep, or none) produced the entity_paths. No current consumer; future drift-detection bead may read it.
        - Forward-compatible — existing ERA consumers (M22 Phase 2, M24, downstream modes) ignore the new field cleanly; M21 path_globs lookup is the only currently-active consumer.
        - Closes the <1% path_bound bottleneck identified in Phase 1 spec (y4b) Section 4.
    7.0.3:
      date: 2026-05-24
      driver: knowledgeforge-core-8xq
      changes:
        - Memory Retrieval Enhancement section qualified — entity-scoped metadata filter integration with M22 is Phase 2 (Deferred). `mempalace_check_duplicate` (Phase 1) has no metadata filter parameter; passing entity/relationship/domain filters in Phase 1 is silently dropped. ERA's other outputs (entity list, relationship map, graph shape) remain consumed by downstream modes.
        - Tier 3 (M24) integration unchanged.
    7.0.2:
      date: 2026-04-29
      changes:
        - Upstream ERA adversarial checklist from knowledgeforge-cw era-domain skill — compound failures (hidden join paths, blast radius, cardinality violations, brittleness test), blast radius probes, assumption inversions, design implications
        - Add KF-specific ERA applications — module dependency audit, mode chain contracts, routing index schema
        - Add adversarial probes to CC Doc section for Expert mode execution
    7.0.1:
      date: 2026-04-17
      changes:
        - Module is now fully standalone — Module 00 and Module 07 updated to reference this as a first-class cross-cutting module (not optional, not conditional on Module 05 ERA section size)
    6.6.0: |
      - Added ## CC Doc section for Claude Code compilation
      - Added to CC platform binding (25_entity_relationship_analysis.md)
      - Added M25 entry to kf_module_index.txt
    6.5.0: |
      - Initial module
      - Entity extraction + relationship mapping pipeline
      - Routing signal generation from relationship graph complexity
      - Multi-hop reasoning support via relationship chains
      - Memory retrieval enhancement via entity-scoped metadata filters
      - Inspiration: James Hutchinson (github.com/anjinMeili) — A-RAG hierarchical retrieval,
        multi-hop question answering, and modular agentic framework design patterns
```

---

## The Problem This Patches

Decision Classification (Module 13) classifies *request types*. It doesn't analyze the *entities involved* or *how they relate to each other*. This creates a routing blind spot:

A query containing three interconnected systems with cascading dependencies routes the same as a query about one system in isolation — even though the first genuinely needs Coordinator or Expert while the second needs Builder or Debugger.

ERA patches this. It runs alongside Decision Classification and adds a relational signal to the routing decision.

---

## Core Concept

**Every non-trivial query involves entities. Those entities have relationships. The structure of those relationships is a routing signal.**

ERA extracts that structure in three steps:

```
[query + context]
  → Entity Extraction   — identify discrete named things
  → Relationship Mapping — identify how entities connect
  → Routing Signal       — derive mode/chain implications from graph shape
```

This is not a heavyweight graph database operation. It is a lightweight classification pass: ~3–5 entities max in most queries, ~5–10 relationships max. If a query contains more than that, ERA surfaces it as a complexity signal and routes to Expert.

---

## Entity Types

ERA recognizes five entity categories:

| Category | Examples |
|----------|----------|
| **System** | database, API gateway, auth service, Redis, caching layer |
| **Actor** | user, agent, team, role, external service, scheduler |
| **Concept** | policy, rule, rate limit, SLA, constraint, invariant |
| **State** | session, transaction, health score, queue depth, build status |
| **Artifact** | spec, config file, schema, migration, deployment package |

Entities are named from the query itself, not inferred. ERA does not add entities the user didn't mention.

---

## Relationship Types

| Relationship | Description | Example |
|-------------|-------------|---------|
| `depends_on` | Entity A cannot function without Entity B | payment service depends_on auth service |
| `produces` | Entity A generates Entity B | ingestion pipeline produces feature vectors |
| `consumes` | Entity A takes input from Entity B | ML model consumes feature vectors |
| `modifies` | Entity A changes state of Entity B | migration modifies database schema |
| `routes_to` | Entity A dispatches requests to Entity B | API gateway routes_to payment service |
| `monitors` | Entity A observes Entity B | alert system monitors health score |
| `conflicts_with` | Entity A and Entity B cannot both be true/active | new schema conflicts_with old schema |
| `co_changes_with` | Entity A and Entity B change together | auth service co_changes_with session store |

---

## Routing Signal Generation

The relationship graph shape maps to routing implications:

### Graph Shapes → Routing Signals

```
Linear chain (A → B → C)
  Complexity: LOW
  Signal: single-path dependency, Builder or Debugger sufficient

Branching fan-out (A → B, A → C, A → D)
  Complexity: MEDIUM
  Signal: parallel dependencies, consider Coordinator

Diamond (A → B, A → C, B → D, C → D)
  Complexity: MEDIUM-HIGH
  Signal: merge point creates ordering constraint, Coordinator required

Full mesh (A ↔ B ↔ C ↔ A)
  Complexity: HIGH
  Signal: circular dependency or tight coupling, Expert review warranted

Conflict edges present (X conflicts_with Y)
  Complexity: escalate one tier regardless of shape
  Signal: mutual exclusion requires explicit resolution before build

Isolated cluster + connected cluster
  Complexity: varies by each cluster
  Signal: decompose into separate tasks; different modes may apply to each cluster
```

### Routing Adjustments

ERA adjusts routing decisions, it does not override them. Decision Classification (M13) sets the base mode; ERA may *escalate* it:

| ERA Finding | Routing Adjustment |
|-------------|-------------------|
| > 5 entities, > 8 relationships | Escalate to Expert if not already; declare HIGH risk tier |
| Conflict edge detected | Add Critic pass before Builder; surface conflict explicitly |
| Diamond or mesh shape | Route to or add Coordinator |
| `co_changes_with` edge | Add Calibrator pass — configuration drift risk |
| Cross-system `modifies` | Add adversarial verification step |
| Isolated clusters | Decompose into separate mode calls per cluster |

ERA never *downgrades* a routing decision.

---

## Multi-Hop Reasoning Support

For queries that require reasoning across a chain of entity relationships (e.g., "how does a rate limit change on the API gateway affect downstream session expiry?"), ERA builds the traversal path before reasoning begins:

```
1. Extract: rate_limit_policy, API_gateway, session_store, session_expiry_logic
2. Map: rate_limit_policy modifies API_gateway → API_gateway routes_to session_store
         → session_store produces session_expiry_logic
3. Traversal path: rate_limit_policy → API_gateway → session_store → session_expiry_logic
4. Hand to reasoning: walk path, evaluating effects at each hop
```

Without an explicit path, multi-hop queries collapse into single-hop answers. ERA prevents that collapse by making the path explicit before reasoning starts.

This mirrors the A-RAG hierarchical retrieval pattern (Hutchinson, 2025): keyword tools for entity anchoring, semantic tools for relationship inference, chunk tools for hop-level evidence retrieval. ERA adapts that pattern to query analysis rather than document retrieval.

---

## Memory Retrieval Enhancement

**M22 Phase 1 limitation (as of v7.3.0):** `tool_check_duplicate` and the Phase 1 hook integration do NOT accept metadata filter parameters. Entity-scoped metadata filtering against Module 22 (Semantic Wiki Search) is Phase 2 (Deferred) work — tracked in `knowledgeforge-core-acu`. ERA's entity list and relationship map continue to inform downstream modes (Coordinator, Builder, Expert, Strategist, Critic) and Module 24 (Verbatim History Mining) integration is unchanged. The schema below documents the intended Phase 2 surface; in Phase 1, the `domain` / `entities` / `relationships` fields are ignored by M22.

ERA's entity list and relationship map are passed as metadata filters to Module 22 (Semantic Wiki Search) [Phase 2] and Module 24 (Verbatim History Mining) [active]:

```yaml
# ERA output metadata filter example
entities: [API_gateway, session_store, rate_limit_policy]
relationships: [modifies, routes_to]
domain: "architecture"          # Module 23 vocabulary
topic: "distributed-systems"    # Module 23 vocabulary
```

This enables **entity-scoped retrieval**: instead of semantic search against the full query string, the search anchors on specific named entities and their relationship types. Precision improves; false-positive recall drops.

Entity-scoped retrieval is particularly effective for multi-session pattern detection: prior decisions about the same entity cluster surface even when the phrasing differs across sessions.

---

## When ERA Runs

ERA is a lightweight pass, not a full mode. It runs:

- **Always**: On requests routed to Builder, Coordinator, Expert, Strategist, or Critic
- **Conditionally**: On Debugger requests when > 2 systems are mentioned
- **Never**: On reckonings, Navigator clarification exchanges, or single-entity requests

ERA adds < 5% overhead to routing. It does not generate user-visible output. Its output is the adjusted routing decision and the entity-scoped memory filter.

---

## ERA Output Format (Internal)

ERA produces a compact internal record, not displayed to the user:

```yaml
era:
  entities:
    - {name: "API gateway", type: system}
    - {name: "session store", type: system}
    - {name: "rate limit policy", type: concept}
  relationships:
    - {from: "rate limit policy", to: "API gateway", type: modifies}
    - {from: "API gateway", to: "session store", type: routes_to}
  graph_shape: linear_chain
  complexity: LOW
  conflict_edges: []
  routing_adjustments: []
  memory_filter:
    entities: [API gateway, session store, rate limit policy]
    domain: architecture
    topic: distributed-systems
  # Added 7.1.0 (bead 8gp). Maps entity name → list of glob patterns
  # identifying files where that entity is relevant. Empty list = resolver
  # found no matching files; this is a valid outcome (correct behavior
  # for Concept and State entities that often have no concrete file home).
  # Consumed by M21 step_2c_activation_profile.compute.path_globs.
  entity_paths:
    "API gateway": ["src/api/**/*.ts", "src/gateway/**/*.ts"]
    "session store": ["src/storage/session*.ts", "config/redis.yaml"]
    "rate limit policy": []
  resolver_source:
    # DIAGNOSTIC METADATA only — no current consumer module reads this.
    # When a future drift-detection bead lands, this comment updates to
    # name the consumer. Useful for post-hoc debugging in the meantime.
    primary: gitnexus  # one of: gitnexus | grep | none
    gitnexus_attempted: true
    grep_attempted: false
```

### Resolver shape (added 7.1.0)

ERA's entity → path-glob resolver uses a two-source strategy:

**Primary path: GitNexus.** When `gitnexus_context` or `gitnexus_query` is available in the session (KF's global CLAUDE.md mandates GitNexus usage when indexed), ERA delegates entity-name lookup to GitNexus. GitNexus returns file paths for symbols; ERA wraps those paths as globs (per the Glob Derivation Rules below).

**Fallback path: session-cached grep.** When GitNexus is unavailable (e.g., fresh repo not yet `npx gitnexus analyze`-d):

1. On first ERA call against a given repo in a session, scan the repo for entity-candidate paths using `git grep -l` against the entity name plus common variations (kebab-case, snake_case, camelCase, PascalCase).
2. Cache the result keyed by `(entity_name, repo_root)` where `repo_root = git rev-parse --show-toplevel`. Multi-repo sessions get separate cache scopes.
3. Subsequent ERA calls in the same session-and-same-repo read from cache.
4. Cache invalidates at session end (M19 Tier 2 lifecycle).

**Hybrid strategy:** try GitNexus first; on failure (tool unavailable OR returns empty), fall back to grep cache. Both paths feed the same `entity_paths` output shape.

### Glob derivation rules (added 7.1.0)

When the resolver returns a list of file paths, it converts them to globs:

- **Single file:** the path itself becomes the glob.
- **N files in a single directory:** `dirname/*.ext` if all share an extension; `dirname/**/*` otherwise.
- **N files across directories:** `**/*.ext` only if all share an extension AND span enough directories to be a wildcard win; otherwise keep individual paths.
- **Max 5 globs per entity** — cap to the 5 most-specific globs per the comparison function below; emit a LOW finding via the Knowledge Base Linter (M21) for the over-match.

### Glob comparison function (deterministic — added 7.1.0)

When ranking globs for the "5 most-specific" cap:

1. **Primary key — literal-character count of the pre-wildcard prefix.** Extract the prefix up to the first wildcard character (`*`, `?`, `[`). The character count of that prefix is the score. Examples: `src/api/auth.ts` → 15; `src/api/**/*.ts` → 8; `**/*.ts` → 0.
2. **Tiebreak — lexicographic order of the full glob.** Same prefix score → alphabetical, ascending.
3. **No semantic prefix interpretation.** The function does NOT distinguish `src/` from `tests/` by meaning; both are literal-character prefixes. Designers wanting semantic ranking should embed it in the resolver path (e.g., grep filter to exclude `tests/` paths before glob derivation), not in the comparison function.

---

## Anti-Patterns

| Anti-Pattern | Consequence | Correct Approach |
|---|---|---|
| Running ERA on every request | Overhead exceeds benefit on reckonings and simple requests | Apply ERA only on multi-entity, multi-system, or complex queries |
| Inferring entities not in the query | Hallucinated entities produce wrong relationship maps | Extract only what the user mentioned; do not infer |
| Treating ERA output as user-visible content | ERA is an internal routing pass, not an explanation | Never surface the ERA record directly; surface only routing decisions |
| Overriding Decision Classification with ERA alone | ERA adjusts but does not replace M13 | ERA escalates; it never downgrades |
| Building deep entity graphs on speculative relationships | Speculative edges corrupt the routing signal | Map only explicit or clearly implied relationships; mark uncertain edges |
| Skipping ERA on Coordinator requests | Coordinator without entity analysis misses merge-point constraints | ERA is mandatory on all Coordinator-routed requests |

---

## Adversarial Checklist

When ERA is running in Expert mode or on high-stakes requests, apply these probes beyond standard entity/relationship mapping. Standard extraction (entity identification, attribute listing, cardinality labeling) is what Sonnet does natively — document it, do not reproduce it. The adversarial checklist targets what gets missed.

### Compound Failures

```yaml
- "Two apparently independent entities — implicit dependency through a third? (Hidden join path)"
- "Relationship removed or renamed — which consumers break silently vs. loudly? (Blast radius)"
- "Cardinality assumption violated at runtime? (1:1 becoming 1:N under load)"
- "Which entity boundaries force re-analysis if a new requirement is added? (Brittleness test)"
```

### Blast Radius

```yaml
- "Entity renamed — full propagation across modules, templates, routing index, accretion candidates?"
- "Cardinality changes (1:N → M:N) — which consumers require schema migrations vs. cardinality-agnostic?"
- "Implicit contract made explicit — what hidden coupling is revealed?"
```

### Assumption Inversions

```yaml
- "'Entities are independent' → What shared mutable state couples them at runtime?"
- "'Relationship is 1:1' → What production scenario makes it 1:N?"
- "'Entity boundary is stable' → What new requirement forces split or merge?"
- "'Relationship is directional' → Is there a reverse dependency the model omits?"
- "'All entities explicitly modeled' → What implicit entities (sessions, locks, queues, caches) are missing?"
```

### Design Implications

```yaml
- "Entity model reflects domain or implementation? (Implementation-leaking entities = premature coupling)"
- "Relationship names are verb phrases describing behavior, not nouns describing co-location?"
- "Clear aggregate root, or competing entry points? (Competing roots = unclear bounded contexts)"
- "M:N relationships mediated by junction entity, or implicit? (Implicit M:N → unmaintainable)"
```

---

## KF-Specific ERA Applications

ERA applies to KF's own internal structure — not just external systems. Three recurring applications:

### Module Dependency Audit

```yaml
entities: [KF_Module, Activation_Condition, Cross_Reference, Data_Flow]
adversarial_focus:
  - Orphan cross-references (Module A references Module B; B does not reference A)
  - Load-coupled vs. reference-only relationships (misclassified in related: fields)
  - Missing handoff field contracts between chained modes
```

### Mode Chain Contracts

```yaml
entities: [Mode, Input_Field, Output_Field, Handoff_Contract]
relationships:
  - Mode --requires--> Input_Field (N:M via Handoff_Contract)
  - Mode --produces--> Output_Field (N:M via Handoff_Contract)
  - Output_Field --satisfies--> Input_Field (1:1 or 1:N)
adversarial_focus:
  - Output fields no downstream mode consumes (dead outputs)
  - Input fields no upstream mode produces (unsatisfied requirements)
  - Implicit type coercions between output and input field formats
```

### Routing Index Schema

```yaml
entities: [Session, Mode_Engagement, Decision, Artifact, Open_Item]
relationships:
  - Session --contains--> Mode_Engagement (1:N)
  - Decision --produces--> Artifact (1:N)
  - Mode_Engagement --classifies--> Decision (1:1)
adversarial_focus:
  - Decisions without decision_type classification
  - Artifacts with no producing mode (orphaned)
  - Open items referencing closed decisions (stale pointers)
```

ERA analyses of KF's own module structure are high-value accretion candidates. Novel undocumented couplings → flag as ACCRETION_CANDIDATE (novelty_type: new_pattern).

---

## Integration Points

### Module 13 (Decision Classification)
ERA runs after M13 classifies the decision type. M13 sets the mode; ERA may escalate it. The two passes together produce the final routing decision.

### Module 03 (Coordination Patterns)
ERA's graph output feeds directly into Coordinator's dependency mapping step. ERA does not replace Coordinator's dependency analysis — it provides the initial entity graph that Coordinator refines.

### Module 18 (Salience Allocation)
ERA's entity list informs salience weights: entities with more relationships receive higher salience allocation. The most-connected entity in the graph is the highest-priority reasoning anchor.

### Module 19 / 22 / 24 (Memory Architecture / Semantic Wiki Search / Verbatim History Mining)
ERA's entity-scoped metadata filter is passed directly to Tier 0 (wiki) and Tier 3 (history) retrieval. Entities become first-class retrieval signals alongside semantic embeddings.

### Module 20 (Permission Model)
ERA's complexity signal feeds the risk tier. Graph complexity HIGH → escalate toward HIGH risk framing. Conflict edges detected → always HIGH risk tier regardless of other signals.

---

## Attribution

| Element | Source |
|---------|--------|
| Hierarchical retrieval pattern (keyword → semantic → chunk) | James Hutchinson, A-RAG (github.com/anjinMeili, 2025) |
| Modular agentic framework design | James Hutchinson, AllOfUs framework (github.com/anjinMeili, 2025) |
| Multi-hop question answering over entity chains | James Hutchinson, A-RAG (github.com/anjinMeili, 2025) |
| Relationship type taxonomy | Adapted from RDF/OWL object property conventions |

---

## Related Modules

- `13_Decision_Classification.md` — sets base mode; ERA may escalate it
- `03_Coordination_Patterns.md` — Coordinator receives ERA's entity graph as its dependency input
- `18_Salience_Allocation.md` — entity connection count drives salience weights
- `19_Memory_Architecture.md` — ERA metadata filter applies across all four tiers
- `22_Semantic_Wiki_Search.md` — entity-scoped filter for Tier 0 retrieval
- `24_Verbatim_History_Mining.md` — entity-scoped filter for Tier 3 retrieval
- `20_Permission_Model.md` — graph complexity and conflict edges escalate risk tier

---
