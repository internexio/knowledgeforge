# Temporal Knowledge Accumulation

## Module Metadata

```yaml
module:
  title: Temporal Knowledge Accumulation
  version: 7.0.1
  purpose: Add temporal structure to KF's knowledge base — every entry gets versioning, relationships, and lifecycle management
  topics: [temporal-reasoning, knowledge-versioning, knowledge-lifecycle, temporal-relationships, accretion-temporality]
  contexts: [knowledge-management, version-tracking, historical-queries, knowledge-hygiene]
  difficulty: advanced
  related: [15_Grounding_Scores, 09_Debugger_Agent, 08_Synthesizer_Agent, 12_Calibration_Layer, 19_Memory_Architecture, 20_Permission_Model, 21_Knowledge_Accretion, 18_Salience_Allocation]
  changelog:
    7.0.1:
      date: 2026-04-29
      changes:
        - Research Staleness Gate completed — added trigger predicate (staleness_risk != stable), proportional severity based on staleness ratio (age/half-life), explicit do-not-block rule, and updated caveat format. 7.0.0 had binary gate; missing the proportionality and trigger condition. Source: plans/orchestra-integration.md ([project]-swd.7)
    7.0.0:
      date: 2026-04-14
      changes:
        - Add research staleness gate with domain half-life table; flags stale research before building on it
    6.3.1: |
      - Added importance-weighted exponential decay model, pinning, domain half-life table
      - Added decay-staleness_risk consistency check (linter finding if they conflict)
      - Extended temporal_entry schema with importance (int 1-5) and pinned (boolean)
      - Added tertiary fallback chain for days_since_access: access log → last_verified → created_at
    6.2.0: |
      - Accreted entries carry temporal metadata and staleness_risk (Module 21 integration)
      - Added accretion temporal metadata schema
      - Staleness windows drive linter scheduling
    6.1.0: |
      - Added Memory Architecture integration (Module 19) — routing index provides session-scoped temporal record
      - Standardized version numbering to KF release version
```

---

## Core Approach

LLMs treat knowledge as a flat, timeless collection. Temporal Knowledge adds the dimension of *when* — when knowledge was acquired, how it relates to prior knowledge, whether it's still valid, and what superseded it.

**Primary function:** Version and temporally structure all knowledge entries for historical queries, change tracking, and knowledge hygiene.

**Key insight:** Knowledge has a lifecycle. Ignoring it leads to acting on outdated information, missing contradictions between old and new knowledge, and inability to answer "what changed?" questions.

---

## Schema Per Knowledge Entry

Every knowledge entry in KF's knowledge base gains temporal metadata.

```yaml
temporal_entry:
  # Core content (unchanged)
  id: [unique_id]
  content: [the knowledge itself]
  
  # Temporal metadata (NEW)
  created_at: [iso_datetime]
  generation: [monotonic version counter — 1, 2, 3, ...]
  
  relationship:
    type: extends | revises | supersedes | contradicts
    references: [id of related entry]
    
  valid_from: [iso_datetime]  # When this knowledge became true
  valid_until: [iso_datetime | null]  # null = still valid (indefinite)
  
  # From KF-3 (Grounding Scores)
  grounding_score: [0.0-1.0]
  last_verified: [iso_datetime]
  
  # Lifecycle
  status: acquired | active | consolidated | reinforced | decayed | superseded | archived
  
  # Decay metadata (6.3.1)
  importance: [integer 1-5 — human-set at creation, represents base value independent of recency]
  pinned: [boolean, default false — exempts entry from decay-based pruning]
```

---

## Temporal Relationship Types

Simplified from Allen's 13 interval relations to 4 practical operations.

```yaml
relationship_types:
  extends:
    definition: New knowledge adds to existing without changing it
    example: "API also supports POST method" extends "API supports GET method"
    effect: Both entries remain valid; new entry linked as extension
    
  revises:
    definition: New knowledge corrects or updates existing
    example: "Rate limit is 100/min (was 50/min)" revises "Rate limit is 50/min"
    effect: Old entry marked valid_until; new entry becomes active
    
  supersedes:
    definition: New knowledge completely replaces existing
    example: "API v3 specification" supersedes "API v2 specification"
    effect: Old entry archived; new entry becomes canonical
    
  contradicts:
    definition: New knowledge conflicts with existing — both might be valid in different contexts
    example: "Service A says timeout is 30s" contradicts "Service B says timeout is 60s"
    effect: Both remain active; contradiction flagged for resolution
    resolution_required: true
```

---

## Knowledge Lifecycle

```
acquired → active → consolidated → (reinforced | decayed | superseded | archived)
```

```yaml
lifecycle_states:
  acquired:
    description: Just ingested, not yet integrated
    duration: Brief (seconds to minutes)
    transition: → active (after integration check)
    
  active:
    description: Current, valid, in use
    duration: Indefinite (until verified or decayed)
    transition: → consolidated | decayed | superseded
    
  consolidated:
    description: Active knowledge that has been verified and integrated with other knowledge
    duration: Indefinite
    transition: → reinforced | superseded | archived
    
  reinforced:
    description: Consolidated knowledge re-verified (grounding score refreshed)
    duration: Until next decay window
    transition: → consolidated (cycle continues)
    
  decayed:
    description: Knowledge not re-verified within decay window (from KF-3)
    duration: Until re-verified or archived
    transition: → reinforced (if re-verified) | archived (if abandoned)
    
  superseded:
    description: Replaced by newer knowledge (via supersedes relationship)
    duration: Retained for historical queries
    transition: → archived (eventually)
    
  archived:
    description: No longer active but retained for historical record
    duration: Permanent
    transition: None (terminal state)
```

---

## Query Capabilities

Temporal Knowledge enables three types of queries that flat knowledge bases cannot answer.

### 1. Temporal Query

*"What did I know about X as of date Y?"*

```yaml
temporal_query:
  input: { topic: "X", as_of: "2024-06-15" }
  process:
    - Find all entries matching topic X
    - Filter to entries with valid_from ≤ as_of AND (valid_until > as_of OR valid_until = null)
    - Return entries that were active on that date
  output: Knowledge state at specified point in time
```

### 2. Diff Query

*"What changed about X between date A and date B?"*

```yaml
diff_query:
  input: { topic: "X", from: "2024-06-01", to: "2024-07-01" }
  process:
    - Get knowledge state at date A
    - Get knowledge state at date B
    - Diff: what was added, revised, superseded, or contradicted
  output: Change log with relationship types
```

### 3. Hygiene Query

*"What knowledge has been superseded but not cleaned up?"*

```yaml
hygiene_query:
  input: { scope: "all" | topic_filter }
  process:
    - Find entries with status = superseded but still referenced by active entries
    - Find entries with status = decayed (past decay window, not re-verified)
    - Find unresolved contradictions
  output: Cleanup recommendations
```

---

## 8 Known LLM Temporal Failures

These are the specific temporal reasoning failures this module addresses.

```yaml
temporal_failures:
  1:
    failure: Treat time as tokens, not dimensions
    description: LLMs process timestamps as text strings, not temporal coordinates
    mitigation: Explicit temporal schema with computable datetime fields
    
  2:
    failure: Allen composition failures
    description: Cannot correctly compose temporal relations (if A before B and B during C, then...)
    mitigation: Explicit relationship types with defined composition rules
    
  3:
    failure: Relation confusion
    description: Collapse distinct temporal relations (e.g., "overlaps" with "during")
    mitigation: Four simplified, unambiguous relationship types (extends/revises/supersedes/contradicts)
    
  4:
    failure: Temporal closure incompleteness
    description: Cannot derive implied temporal relations from stated ones
    mitigation: Explicit relationship graph — don't rely on inference
    
  5:
    failure: Asymmetric performance
    description: Handle "before/after" well but fail on "overlaps/during"
    mitigation: All relationships are directional and explicit; no need for complex interval reasoning
    
  6:
    failure: Force-assign values when info is underspecified
    description: Guess at dates/times rather than acknowledging uncertainty
    mitigation: valid_from and valid_until allow null; uncertain timestamps flagged
    
  7:
    failure: No temporal grounding
    description: Timestamps in training data are not connected to real time
    mitigation: Grounding scores (KF-3) track when knowledge was verified against reality
    
  8:
    failure: No time-binding
    description: Trained once, frozen — cannot update knowledge over time
    mitigation: Knowledge lifecycle with explicit versioning and supersession
```

---

## Integration Points

### With Grounding Scores (15_Grounding_Scores)

Every temporal entry includes grounding metadata. Grounding decay uses temporal metadata for decay clock.

```yaml
grounding_integration:
  - created_at and last_verified drive the grounding decay clock
  - Superseded entries get grounding reduced (old info, even if once verified)
  - Re-verification resets both grounding score and temporal status (→ reinforced)
```

### With Debugger (09_Debugger_Agent)

Debugger traces reasoning errors temporally — when was incorrect knowledge introduced? What changed?

```yaml
debugger_integration:
  capabilities:
    - "When did this incorrect belief enter the knowledge base?" → temporal query
    - "What was known before the error was introduced?" → point-in-time snapshot
    - "What changed between working and broken?" → diff query
    - "Has this type of error occurred before?" → pattern query with temporal context
```

### With Synthesizer (08_Synthesizer_Agent)

Patterns get temporal context — when first observed, how they've evolved.

```yaml
synthesizer_integration:
  per_pattern:
    first_observed: [when pattern first appeared]
    evolution: [how pattern has changed — via revises/extends chain]
    stability: stable | evolving | emerging | declining
    evidence_timeline: [when each supporting example was observed]
```

### With Calibration Layer (12_Calibration_Layer)

Calibration results are temporally versioned — can track calibration drift over time.

```yaml
calibration_integration:
  temporal_tracking:
    - Each calibration result gets a temporal entry
    - Diff queries reveal calibration drift: "Are we more or less biased than last month?"
    - Trend analysis: is evaluation quality improving or degrading?
```

---

## Research Staleness Gate

**Trigger:** Before Builder or Expert mode operates on knowledge where `staleness_risk != stable`. Stable knowledge (academic foundations, general architecture) skips this gate.

Before building on externally researched material (web searches, retrieved documents, cited sources), check the research age against domain half-life:

| Domain | Half-life (approximate) | staleness_risk |
|--------|------------------------|----------------|
| AI/ML models and APIs | 3 months | fast_decay |
| Security advisories | 1 month | fast_decay |
| Cloud infrastructure pricing/features | 6 months | slow_decay |
| Framework versions and APIs | 6 months | slow_decay |
| General software architecture | 2 years | stable |
| Academic/theoretical foundations | 5+ years | stable |

**Gate behavior** — the gate never blocks; it flags:

- `staleness_ratio = age / half-life`
- `staleness_ratio < 1.0`: proceed normally
- `staleness_ratio 1.0–2.0`: flag LOW — "This research is [N] days old (domain half-life: [H] days). Findings may be outdated."
- `staleness_ratio > 2.0`: flag MEDIUM — "This research is significantly past its domain half-life. Verify before building on it."
- User decides whether to proceed in all cases — do not block

If the user proceeds with stale research: tag all outputs built on it with a caveat: `Built on unverified research from [date] — verify before acting.`

Research age is computed from the `retrieved_at` field if present, or estimated from content signals (model version numbers, API syntax, date references in text).

---

## Constraints

- Temporal metadata adds storage overhead — prioritize for consequential knowledge
- Relationship tracking requires discipline — entries without relationships lose temporal context
- Historical queries are only as good as the temporal metadata entered
- Lifecycle management requires periodic hygiene queries — automated if possible
- Allen's 13 relations simplified to 4 — some nuance lost in exchange for practicality
- Temporal reasoning about very long time spans (years) is less reliable than short spans (days/weeks)

---

## Success Criteria

- Every consequential knowledge entry has temporal metadata
- Temporal queries correctly return point-in-time knowledge state
- Diff queries accurately identify what changed between two points
- Hygiene queries find and flag superseded/decayed entries
- Debugger can trace when incorrect knowledge was introduced
- Synthesizer can track pattern evolution over time

---

## Attribution

| Element | Source |
|---------|--------|
| Temporal relationship types | NARS-influenced, our formalization |
| Allen's 13 interval relations | Actively proposed in PNW AGI archive |
| 8 LLM temporal failures | 36-paper survey in PNW AGI archive |
| Knowledge lifecycle states | Our design |
| Simplified 4-relation model | Our practical reduction from Allen's 13 |

---

## Related Modules

- `15_Grounding_Scores.md` — Grounding-aware versioning and decay
- `09_Debugger_Agent.md` — Temporal trace for debugging
- `08_Synthesizer_Agent.md` — Pattern evolution tracking
- `12_Calibration_Layer.md` — Calibration drift analysis
- `19_Memory_Architecture.md` — (6.1) Routing index provides session-scoped temporal record; index entries carry implicit temporal ordering
- `21_Knowledge_Accretion.md` — (6.2) Accreted entries carry temporal metadata; staleness_risk drives linter scheduling
- `18_Salience_Allocation.md` — (6.3.1) Access-driven salience signal consumes `days_since_access` data that feeds the decay model

## Accretion Temporal Metadata (6.2 — Module 21 Integration)

Every entry filed through the accretion system carries temporal metadata that integrates with the existing knowledge lifecycle model.

```yaml
accretion_temporal_schema:
  created: [ISO datetime — when the knowledge was produced]
  source_session: redacted
  staleness_risk: [stable | slow_decay | fast_decay]
  
  staleness_windows:
    stable: null  # No automatic expiry — checked on extended linter schedule
    slow_decay: 180 days  # Re-validate every 6 months
    fast_decay: 30 days   # Re-validate monthly
    
  lifecycle_mapping:
    # Maps to existing knowledge lifecycle states in this module
    new_accretion: ACTIVE  # All accreted entries start active
    past_staleness_window: REVIEW  # Linter flags for re-validation
    confirmed_valid: ACTIVE  # Back to active with reset timer
    confirmed_stale: SUPERSEDED | ARCHIVED  # Human or Critic decides
    
  temporal_relationships:
    # Accreted entries can carry the same temporal relationships as any knowledge entry
    extends: "New accretion adds to existing entry without replacing it"
    revises: "New accretion updates specific claims in existing entry"
    supersedes: "New accretion replaces existing entry entirely"
    contradicts: "New accretion conflicts with existing entry — both flagged for resolution"
    
  linter_scheduling:
    # Staleness_risk determines how often the Critic linter checks this entry
    stable: "Check during quarterly health checks"
    slow_decay: "Check during monthly health checks"
    fast_decay: "Check during weekly health checks or on every linter pass"
```

---

## Importance-Weighted Decay Model (6.3.1)

Qualitative staleness categories (`staleness_risk`) tell you *how fast* knowledge decays. The decay model makes this quantitative — every entry has a computable effective importance that decreases over time unless accessed or pinned.

### Formula

```
effective_importance = importance * 2^(-days_since_access / half_life_days)
```

- `importance` (int 1-5): Human-set at creation. Represents base value independent of recency. A critical architectural decision is importance 5 whether accessed yesterday or 6 months ago.
- `pinned` (boolean, default false): Exempts entry from decay-based pruning. Use for critical infrastructure knowledge that's rarely accessed but essential — the kind of knowledge that "just works" until it doesn't.
- `days_since_access`: Days since the entry was last retrieved during a session. Populated by access logging (Module 21, 6.3.1). Falls back to `last_verified` if no access log exists, then to `created_at` if neither exists (prevents new or backdated imports from immediately tripping the archival threshold).

### Domain Half-Life Table

| Domain | Half-Life | Rationale |
|--------|-----------|-----------|
| Architecture / integration patterns | 365 days | Slow-moving; architectural decisions outlast implementations |
| Audience insights / COS profiles | 90 days | Behavioral data shifts with market conditions |
| Campaign observations | 30 days | Campaign-specific; stale within weeks of campaign end |
| AI/ML techniques | 60 days | Field moves fast; best practices shift quarterly |
| Mathematical / algorithmic patterns | Pinned (no decay) | Timeless; no expiry unless proven incorrect |

### Decay Threshold

Entries below **0.2 effective importance** get flagged for archival regardless of explicit staleness tags. This catches entries that have both low base importance and haven't been accessed in a long time — the "nobody needs this anymore" signal.

### Consistency with staleness_risk

The decay model provides quantitative backing for what `staleness_risk` categorizes qualitatively. These should be consistent:

| staleness_risk | Expected half-life | Expected pinned |
|----------------|-------------------|-----------------|
| `fast_decay` | 30-60 days | false |
| `slow_decay` | 90-365 days | false |
| `stable` | 365+ days or pinned | true or long half-life |

**If they conflict** (e.g., an entry marked `stable` with a 30-day half-life, or `fast_decay` that's pinned), flag as a linter finding at MEDIUM severity. The human resolves which is correct.

### Anti-Pattern: Decay Without Pinning

**Looks like:** Critical infrastructure knowledge that's rarely accessed gets pruned because nobody thought to pin it.

**Failure example:** A Stripe webhook routing pattern that "just works" and hasn't been accessed in 90 days. Effective importance decays below 0.2. Archival flag fires. The entry gets removed. Three months later, someone needs to debug webhook routing and the knowledge is gone.

**Fix:** Explicit `pinned: true` for infrastructure knowledge at creation time. The linter should flag high-importance (4-5) entries that aren't pinned as a LOW severity finding — a nudge to consider whether pinning is appropriate.

## CC Doc

# Module 17: Temporal Knowledge — Execution Protocol
**Apply when:** [KF-ROUTE] load list includes M17, or request involves temporal reasoning, versioning, or staleness assessment

Add temporal structure to knowledge entries. Track what changed, when, and whether it is still valid.

## Temporal Entry Schema

Every knowledge entry gains:

```yaml
temporal_metadata:
  created_at: [ISO datetime]
  generation: [monotonic version counter]
  relationship:
    type: extends | revises | supersedes | contradicts
    references: [id of related entry]
  valid_from: [ISO datetime]
  valid_until: [ISO datetime | null]  # null = still valid
  last_verified: [ISO datetime]
  status: acquired | active | consolidated | reinforced | decayed | superseded | archived
```

## Temporal Relationship Types

| Type | Definition |
|------|-----------|
| `extends` | Adds to existing without changing it — both remain valid |
| `revises` | Corrects or updates — old entry marked valid_until |
| `supersedes` | Completely replaces — old entry archived |
| `contradicts` | Conflicts with existing — both active, flag for resolution |

## Staleness Risk Windows

- `stable`: No automatic expiry. Check quarterly.
- `slow_decay`: Re-validate within 180 days.
- `fast_decay`: Re-validate within 30 days.

Domain half-lives: API docs 30 days, user preferences 60 days, architecture 90 days, regulatory 180 days, math proofs pinned.

## Staleness Flag Triggers

Flag before using when: `last_verified` exceeds domain half-life, status is `decayed` or `superseded`, `staleness_risk` is `fast_decay` and entry is more than 30 days old.

When flagging: "This knowledge entry has not been verified since [date]. Domain decay rate is [fast/moderate/slow]. Verify before relying on it for [consequential decision]."

## Importance-Weighted Decay

```
effective_importance = importance × 2^(-days_since_access / half_life_days)
```

Entries below 0.2 effective importance flagged for archival. High-importance (4-5) entries that aren't pinned get a nudge to consider pinning.

## Uncertainty Rule

Use `null` for `valid_until` and timestamps when information is underspecified — never guess dates.
