# Semantic Wiki Search

## Module Metadata

```yaml
module:
  title: Semantic Wiki Search
  version: 7.4.1
  purpose: Retrieval contract over the Tier 0 wiki — KF's specification on top of MemPalace's tool surface, defining how the accretion pipeline gates against duplicates and how retrieval degrades gracefully when the vector backend is unavailable
  topics: [retrieval, semantic-search, mempalace, vector-index, wiki-search, duplicate-detection]
  contexts: [knowledge-retrieval, accretion-check, linter-runs, cross-session-queries]
  difficulty: intermediate
  related: [19_Memory_Architecture, 21_Knowledge_Accretion, 23_Taxonomy_Enforcement, 24_Verbatim_History_Mining, 17_Temporal_Knowledge]
  added_in: "6.5"
  changelog:
    7.4.1: |
      - Added Phase 2 success criteria section (knowledgeforge-core-acu work scope item 5).
        Defines R@10 target, off-domain noise threshold, injection hit rate, wrapper
        latency, and false-negative monitoring. Closes the bead.
    7.4.0: |
      - Phase 2 activated (knowledgeforge-core-acu, triggered 2026-07-07).
        Trigger #1 fired: wiki > 100 entries AND infrastructure query returned
        2/5 off-domain results in top-5.
      - Wing-derivation defect fixed in mempalace-wiki-mine.py:
        find_wiki_root() now derives per-subdomain wings
        (wiki/patterns/foo.md → wing=wiki-patterns).
        mempalace.yaml markers added to all 11 wiki subdirectories.
        Existing 315 entries remain in wiki-kf-core (MemPalace dedup prevents
        re-mining already-filed files; migration is optional per spec).
      - kf_wiki_search.py created at ~/.claude/hooks/: Phase 2 wrapper around
        tool_search implementing two-phase retrieval (metadata pre-filter +
        score fusion). Weights: 0.65 cosine + 0.20 importance + 0.15 recency.
        staleness_risk aliases handled (fast_decay→volatile, low→stable,
        medium→slow_decay). Falls back to created field when last_accessed
        absent (currently 0 entries have last_accessed populated).
      - kf-route.py extended: after Gemini routing fires, keyword-based domain
        inference runs on the user prompt; if domain is inferred,
        wiki_search(query, domain, k=3) is called and top-3 results are
        injected as [Wiki context — M22 §2] block in the updatedPrompt.
        Injection is skipped when domain cannot be inferred (avoids noise from
        empty-domain legacy entries in unfiltered results).
      - Transitional state: existing wiki entries are in wiki-kf-core; new
        entries added after 2026-07-07 are mined into wiki-{subdir} wings.
        Phase 2 wrapper searches wiki-kf-core (full coverage) with client-side
        domain filter (correctness). Wing-scoped search is a future optimization.
    7.3.1: |
      - Dup-check threshold recalibrated 0.9 → 0.85 based on empirical probing
        during knowledgeforge-core-rk4 hook implementation. MemPalace mines wiki
        files into smaller drawers (chunked storage); full-file queries against
        drawer fragments top out at ~0.889 cosine similarity for EXACT-content
        matches. The original 0.9 threshold was empirically unreachable — Phase 1
        would have shipped as a no-op.
      - Empirical anchors (knowledgeforge-core wiki collection, 2415 drawers,
        2026-05-25): exact-content top similarity = 0.889; novel content top
        similarity ≈ -0.04 (negative — far from any drawer). Threshold 0.85
        catches exact matches with margin to spare; novel content scores far
        below.
      - See wiki/diagnostics/2026-05-24_threshold-vs-empirical-calibration-gap-
        similarity-systems.md for the full diagnostic and calibration probe.
      - knowledgeforge-core-rk4 also closed in this pass — hook implementation
        landed in ~/.claude/hooks/mempalace-wiki-mine.py with the
        calibrated threshold. Implementation Status table flipped to ✅.
    7.3.0: |
      - Phase 1 reconciliation with MemPalace adoption (knowledgeforge-core-8xq)
      - Replaced direct ChromaDB prescription with MemPalace MCP / direct-import tool surface
      - Phase 1 scope narrowed (post adversarial review): dup-check gate only — no wing/room
        pre-filter, no score fusion, no orchestrator-context retrieval. Single-purpose,
        verifiable, shippable.
      - Score fusion, wing/room pre-filter, frontmatter metadata filter, and orchestrator-
        context retrieval all preserved under "Phase 2 (Deferred)" — workload-triggered
        not scheduled. Trigger bead: knowledgeforge-core-acu.
      - Phase 2 prerequisites enumerated explicitly — including the known wing-derivation
        defect in mempalace-wiki-mine.py (single-level wing collapses subdomains into
        repo-wing; must be fixed before Phase 2 can scope by subdomain)
      - Cross-references in M21 and M23 updated to acknowledge Phase 1 vs Phase 2 boundary
      - Anti-Patterns updated: added "bypassing mempalace_check_duplicate during accretion";
        relocated fusion / wing-filter / frontmatter-filter anti-patterns to Phase 2
      - Strategist trade-off analysis (Phased A→D) recorded in 8xq comments
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

KF retrieves from the Tier 0 wiki through MemPalace, which wraps a ChromaDB vector store. MemPalace's `mempalace mine` CLI is invoked by `mempalace-wiki-mine.py` (PostToolUse on Write/Edit/MultiEdit) on every wiki write, keeping the index current without explicit re-indexing. KF's contract with MemPalace lives in this module.

**Phase 1 (this spec):** narrow scope — `mempalace_check_duplicate` is wired into the accretion pipeline as a detect-and-warn gate. No semantic search, no orchestrator-context retrieval, no wing/room scoping. The dup-check is wing-less by design (MemPalace's `tool_check_duplicate` signature accepts only `(content, threshold)`), so Phase 1 has zero dependency on wing derivation. Grep fallback is the retrieval surface for everything else.

**Phase 2 (active as of v7.4.0):** wing/room pre-filter, frontmatter (`domain`/`topic`/`tags`/`importance`) filter, score fusion, and orchestrator-context retrieval are live. Implemented by: `kf_wiki_search.py` (Phase 2 wrapper), extended `kf-route.py` (context injection), fixed `mempalace-wiki-mine.py` (per-subdomain wing derivation). Wing-derivation defect fixed: new entries get per-subdomain wings (`wiki-patterns`, `wiki-infrastructure`, etc.). Existing 315 entries remain in `wiki-kf-core`; wrapper searches that wing with client-side domain filter for full coverage. Per-subdomain wing queries are a future optimization once new entries accumulate.

Phase 1 is intentionally minimum-viable. The original v6.5.0 95% R@10 design intent is preserved in the Phase 2 section, not deleted.

---

## Implementation Status

Phase 1 is **fully landed** as of v7.3.1 (knowledgeforge-core-rk4).

| Component | Status | Tracked in |
|---|---|---|
| M22 v7.3.0 spec rewrite | ✅ Landed | knowledgeforge-core-8xq |
| M21 / M23 / M00 / M06 / M25 / M24 cross-reference updates | ✅ Landed | knowledgeforge-core-8xq |
| `mempalace-wiki-mine.py` extension to call `tool_check_duplicate` | ✅ Landed (threshold=0.85, calibrated empirically) | knowledgeforge-core-rk4 |
| Threshold recalibration 0.9 → 0.85 + spec v7.3.1 | ✅ Landed | knowledgeforge-core-rk4 |
| Phase 2: kf_wiki_search.py wrapper (filter + fusion) | ✅ Landed (v7.4.0, 2026-07-07) | knowledgeforge-core-acu |
| Phase 2: kf-route.py wiki context injection | ✅ Landed (v7.4.0, 2026-07-07) | knowledgeforge-core-acu |
| Phase 2: find_wiki_root() per-subdomain wing derivation | ✅ Landed (v7.4.0, 2026-07-07) | knowledgeforge-core-acu |

The hook calls `tool_check_duplicate` via direct Python import (`from mempalace.mcp_server import tool_check_duplicate`), guarded by `except BaseException` to catch both `KnowledgeGraph()` SQLite errors and argparse `SystemExit` on `--help`. Detect-and-warn semantics — does NOT block the mine.

---

## Implementation (Phase 1)

### Dup-Check Gate (only Phase 1 integration)

When a wiki entry is filed, the accretion pipeline calls MemPalace's `tool_check_duplicate` to detect near-duplicates. The check is **detect-and-warn**, not block: the PostToolUse hook fires AFTER the file is on disk, so blocking is not possible at this layer. The contract: every near-duplicate that gets filed must produce a stderr WARNING that surfaces to the user.

**Integration interface (for hook implementation):**

```python
# Direct Python import — bypasses both the CLI (no check-duplicate subcommand exists)
# and the MCP runtime (hooks shouldn't depend on MCP being connected).
from mempalace.mcp_server import tool_check_duplicate, _get_collection

result = tool_check_duplicate(content=entry_text, threshold=0.85)
if result.get("is_duplicate"):
    matches = result.get("matches", [])
    sys.stderr.write(
        f"[Module 22] near-duplicate detected for {file_path}: "
        f"{len(matches)} match(es) at similarity ≥ 0.85. "
        f"Top match: {matches[0].get('id', '?')} ({matches[0].get('wing', '?')}/{matches[0].get('room', '?')})\n"
    )
```

**Where this lives:** extend `~/.claude/hooks/mempalace-wiki-mine.py` to call this BEFORE the existing `mempalace mine` subprocess, scoped only to wiki/ writes. The dup-check is best-effort: any exception in this code path must not block the mining or crash the hook.

### Fallback: Grep

When MemPalace is unavailable (cold start before MCP connects, broken install, ChromaDB index corruption):

1. Fall back to `grep -rli "<query terms>" wiki/` for any retrieval need
2. Log to stderr: `[Module 22 FALLBACK] MemPalace unavailable — using grep. Expect reduced recall.`
3. Never fail silently. The recall regression must be visible.

### Required YAML Fields

Frontmatter is preserved at write time for human readers and Phase 2 readiness. Phase 1 retrieval does not read it. Required fields per Module 21:

```yaml
domain:          # M23 controlled vocabulary — Phase 2 will filter on this
topic:           # M23 controlled vocabulary — Phase 2 will filter on this
tags:            # M23 vocabulary, 1–5 tags — Phase 2 will require ≥2 overlap
importance:      # integer 1–5 — Phase 2 fusion input
created_at:      # YYYY-MM-DD
last_accessed:   # YYYY-MM-DD — Phase 2 recency boost input
grounding_score: # 0.0–1.0 from Module 21 grounding gate
staleness_risk:  # M17 vocabulary — Phase 2 fusion decay parameter
```

These fields are written by Module 21's accretion pipeline. Phase 1 does not consume them; Module 23 enforces vocabulary validity at write time so Phase 2 can rely on them when triggered.

### Runtime Availability (NOT pre-loaded by hooks)

MemPalace's full MCP tool surface is available to the orchestrator agent at runtime (`mempalace_search`, `mempalace_traverse`, `mempalace_find_tunnels`, `mempalace_status`, etc.). The agent MAY call these tools when an information need arises in-conversation. Phase 1 does NOT pre-load any retrieval context via hooks — that is Phase 2 work.

---

## Anti-Patterns

| Anti-Pattern | Consequence | Correct Approach | Phase |
|---|---|---|---|
| Bypassing `mempalace_check_duplicate` during accretion | Duplicate wiki entries accumulate; threshold-0.9 near-dupes escape | Wire the dup-check into the accretion pipeline; emit WARNING for every detected duplicate | 1 |
| Treating PostToolUse dup-check as a hard block | Hook fires too late — the file is already on disk | Detect-and-warn; surface to user via stderr; do NOT block the mine | 1 |
| Calling ChromaDB directly, bypassing MemPalace | Two indexes drift; breaks MemPalace's wing/room organization | Go through MemPalace MCP tools or direct Python imports from `mempalace.mcp_server` | 1 |
| Calling `mempalace check-duplicate` via CLI | CLI does not expose this subcommand — only `init`, `mine`, `split`, `search`, `mcp`, `compress`, `wake-up`, `repair`, `migrate`, `status`, `hook`, `instructions` | Use direct Python import: `from mempalace.mcp_server import tool_check_duplicate` | 1 |
| Silently swallowing MemPalace failures | Hidden recall regression; users don't know retrieval is broken | Emit `[Module 22 FALLBACK]` or `[Module 22]` to stderr, fall through to grep where applicable | 1 |
| Wing-scoping a Phase 1 dup-check | `tool_check_duplicate` has no `wing` parameter; passing one is silently ignored | Don't pass wing in Phase 1; global similarity is correct here | 1 |
| Pre-loading retrieval context in any hook | Phase 1 intentionally has no read-side hook integration | If you need pre-loaded context, file a Phase 2 trigger | 1 |
| Post-hoc tag filtering (filter after semantic scoring) | Wastes compute on irrelevant candidates; misses paraphrase cases | Filter before scoring (Phase 2 wraps MemPalace results client-side) | 2 |
| Treating domain mismatch as soft penalty | Off-domain entries contaminate top-K even with low score | Domain mismatch = hard exclude in fusion layer | 2 |
| Re-embedding all entries at query time | O(n) cost per query, unacceptable at scale | Pre-compute embeddings at write time (MemPalace handles this) | 1 |

---

## Integration Points

### Module 21 (Knowledge Accretion)
Accretion pipeline writes entries to `wiki/`, triggering `mempalace-wiki-mine.py` (PostToolUse). The hook (Phase 1) must call `tool_check_duplicate(entry_content, threshold=0.85)` via direct Python import, emit a stderr WARNING on duplicates, and proceed with the `mempalace mine` subprocess regardless. **(Target state — pending `knowledgeforge-core-rk4`. See Implementation Status section.)** Module 21's note about ChromaDB/LanceDB at step 4b is superseded by this spec — embedding happens inside MemPalace's mine pipeline; Module 21 callers do not invoke ChromaDB directly.

### Module 23 (Taxonomy Enforcement)
Phase 1 retrieval does not consume Module 23's vocabulary. Module 23 still enforces frontmatter validation at write time so Phase 2 can rely on it. Module 23's "Module 22 integration" cross-reference should be qualified: "M22's metadata pre-filter is Phase 2 (Deferred); Phase 1 uses no frontmatter filter."

### Module 19 (Memory Architecture)
Tier 0 (wiki/) is the corpus. Module 22 provides the dup-detection mechanism for accretion-time gating into Tier 0. Tier 1 routing index is small enough to load fully — Module 22 is not applied there.

### Module 17 (Temporal Knowledge)
Phase 1: not consumed. Phase 2: `staleness_risk` drives the recency-decay parameter in score fusion.

### Module 24 (Verbatim History Mining)
Module 24 also uses MemPalace, but against Tier 3 (verbatim conversation history) rather than Tier 0 (wiki). The two are separate MemPalace wings (`conversation-*` vs `wiki-*`) sharing the same ChromaDB backend.

---

## Constraints

- Hooks calling MemPalace must wrap the call in `try/except` and emit `[Module 22]` or `[Module 22 FALLBACK]` to stderr on failure — never propagate to a hook crash. Graceful degradation is mandatory per CLAUDE.md.
- The dup-check is best-effort and post-write: it CANNOT prevent a duplicate from being filed; it can only surface that one was. Treat success as "every duplicate that got filed produced a warning," not "no duplicates were filed."
- Phase 1 hooks must not depend on MCP runtime connectivity. Use direct Python import (`from mempalace.mcp_server import tool_check_duplicate`) — this works without the MCP server running, BUT the import has TWO failure modes the hook guard must cover:
  1. **Side-effect instantiations.** `MempalaceConfig()` and `KnowledgeGraph()` run at module-load (mcp_server.py:59-63). `KnowledgeGraph()` opens a SQLite connection to the palace; if `MEMPALACE_PALACE_PATH` is misconfigured or the palace has never been initialized, this raises a normal `Exception`. Verify palace state once via `python -m mempalace status` before deploying.
  2. **argparse `SystemExit`.** `_parse_args()` calls `parse_known_args()` against `sys.argv` at module-load (mcp_server.py:41-54). If the hook is ever invoked with `-h` or `--help` in `sys.argv` (manual operator runs, test harnesses, hook wrappers), argparse calls `sys.exit(0)`. `SystemExit` inherits from `BaseException`, not `Exception` — a plain `except Exception` does NOT catch it.

  The hook guard MUST use `except BaseException as e` (or `except (Exception, SystemExit) as e`) to cover both failure modes, then emit `[Module 22 FALLBACK] import failed: <err>` to stderr. Plain `except Exception` is insufficient — silent dup-gate disablement on `--help` invocations would result.
- Don't call ChromaDB directly. Go through MemPalace tools.

---

## Success Criteria (Phase 1)

Criteria became live with v7.3.1 (knowledgeforge-core-rk4). Initial verification completed against an existing wiki entry: `[Module 22] near-duplicate detected` warning emitted correctly. Ongoing measurement per the table below.

| Metric | Target | Measurement |
|--------|--------|-------------|
| Dup-check wired into accretion path | `mempalace-wiki-mine.py` calls `tool_check_duplicate` BETWEEN the fingerprint check and `mine_wiki()` | grep the hook for `tool_check_duplicate` import + call; verify insertion point by reading the hook source |
| Import guard uses `except BaseException` (not `except Exception`) | covers both `KnowledgeGraph()` SQLite errors AND argparse `SystemExit` | grep the hook for `except BaseException` around the import line |
| Bead-state verification before rk4 implementation starts | `bd show knowledgeforge-core-rk4` confirms P2 priority and depends-on 8xq | runtime check before implementing the hook |
| Near-duplicate detection coverage | Every near-duplicate that gets filed emits a stderr WARNING | Inspect `~/.claude/logs/kf-events.jsonl` and stderr logs |
| Unflagged near-duplicates filed | 0 in one month post-deploy | Manual spot-check: pick a handful of recent entries; run `tool_check_duplicate` retroactively; verify warnings exist |
| Hook crash rate from MemPalace integration | 0 | stderr log inspection; check that all `mempalace-wiki-mine` invocations exit 0 |
| Grep-fallback engagement | < 5% of wiki-touching operations | Add counter in fallback branch; weekly review |

Phase 1 explicitly does NOT measure recall, precision, R@10, or any retrieval-quality metric. Those are Phase 2 targets, triggered by observed evidence.

---

## Implementation (Phase 2)

### Wing Derivation (mempalace-wiki-mine.py)

`find_wiki_root()` now derives per-subdomain wings:
- `wiki/patterns/foo.md` → `wing=wiki-patterns`
- `wiki/infrastructure/bar.md` → `wing=wiki-infrastructure`
- `wiki/index.md` (directly in wiki root) → `wing=wiki-kf-core` (legacy)

`mempalace.yaml` markers exist in all 11 wiki subdirectories. Existing entries remain in `wiki-kf-core` (MemPalace dedup skips re-mining already-filed files).

### Phase 2 Wrapper (kf_wiki_search.py)

**Location:** `~/.claude/hooks/kf_wiki_search.py`

**Entry point:** `wiki_search(query, domain, topic, tags, k, limit, wing)`

**Two-phase retrieval:**

```
query + domain hint
  → tool_search(query, limit=50, wing="wiki-kf-core")  # candidate pool
  → deduplicate by source_file (best cosine drawer per file)
  → Phase 2a: metadata pre-filter
      keep if: domain matches OR (domain+topic both match)
               OR ≥2 tag overlaps with query tags
  → Phase 2b: score fusion
      fusion = 0.65·norm_cosine + 0.20·norm_importance + 0.15·recency_boost
  → return top-K sorted by fusion_score
```

**Score fusion details:**
- `norm_cosine`: cosine similarity normalized within the candidate set [0,1]
- `norm_importance`: `(importance - 1) / 4` maps [1,5] → [0,1]
- `recency_boost`: `exp(-λ · days_since)` using `last_accessed` (falls back to `created`); λ from staleness_risk
- staleness_risk aliases: `fast_decay`→`volatile`, `low`→`stable`, `medium`→`slow_decay`

### Orchestrator Context Injection (kf-route.py)

When kf-route.py's Gemini routing activates a mode (non-reckoning), it:
1. Runs keyword-based domain inference on the user prompt
2. If a domain is inferred (ambiguous queries return None — injection is skipped):
   - Calls `wiki_search(prompt, domain, k=3, limit=50)`
   - Formats top-3 results as a `[Wiki context — M22 §2 | domain=X]` block
   - Injects the block into `updatedPrompt` between the skill-load hints and `---`

Domain keywords mapped: infrastructure, patterns, diagnostics, methodologies, orchestration, migrations, architecture, compiler, strategy, integration.

**Injection format:**
```
[KF-ROUTE: mode=builder | decision=evaluative | load=[M21]]
Load skill: .claude/skills/kf/builder.md
[Wiki context — M22 §2 | domain=infrastructure]
1. "Nginx rate-limit zones must distinguish credential-bearing vs read-only auth endpoints" (infrastructure/server-configuration, imp:5) — Rate limits must differ between login...
2. ...
---
[user prompt]
```

**Graceful degradation:** Any failure in the wiki search path emits `[M22 Phase 2 FALLBACK]` to stderr and falls through to the existing routing-only behavior. Tool search unavailability, import failures, and individual query failures are all caught.

---

## Success Criteria (Phase 2)

Phase 2 became active with v7.4.0 (2026-07-07). Metrics below are the operative targets for ongoing measurement.

| Metric | Target | Measurement method |
|--------|--------|-------------------|
| Domain-relevant results in top-10 (R@10) | ≥ 95% of top-10 results from `wiki_search` are domain-relevant | Monthly: sample 10 queries across 3 domains; count domain-relevant results in returned top-10 |
| Off-domain noise in top-5 | ≤ 1/5 off-domain results (down from 2/5 that triggered Phase 2) | Same sampling pass; count off-domain in position 1–5 |
| Injection hit rate | ≥ 50% of non-reckoning routed turns get wiki context injected | Review `~/.claude/logs/kf-events.jsonl` for M22 injection entries vs total mode-routed turns per week |
| Wrapper latency (P95) | < 2 s added to routing latency | stderr timestamps in `[kf-route] M22 Phase 2` log lines; compute delta over a session |
| Phase 2 fallback engagement | < 5% of wiki-search calls fall back | Count `[M22 Phase 2 FALLBACK]` entries in stderr logs per week |
| False-negative monitoring | 0 new `wiki/diagnostics/*module22-false-negative*` entries per month | File inspection: `ls wiki/diagnostics/ | grep module22-false-negative` |

**Measurement cadence:** Monthly manual review is sufficient. Trigger immediate re-review if off-domain noise climbs back to 2/5, or if David reports "search isn't finding things" (Phase 2 upgrade trigger #4 restated — a single subjective report is the highest-priority signal).

**95% R@10 provenance:** LongMemEval benchmark (Arora et al. 2025) measured 60% R@10 without hierarchical filter → 95% R@10 with metadata-gated retrieval. The Phase 2 design follows the same filter structure; the 95% target is aspirational calibration, not a guaranteed outcome on the KF wiki corpus. Treat 80%+ as operationally acceptable; 95%+ as the design target.

---

## Phase 2 Design Reference

This section preserves the v6.5.0 design intent. Phase 2 is now active (v7.4.0). The design below was implemented in `kf_wiki_search.py` and the extended `kf-route.py`.

### Prerequisites

Phase 2 cannot be cleanly implemented until these are addressed (folded into knowledgeforge-core-acu):

1. **Wing-derivation defect in `mempalace-wiki-mine.py`.** Current code collapses every wiki subdirectory under `knowledgeforge-core/wiki/` into the single wing `wiki-kf-core` (hardcoded in WIKI_WING_MAP). For per-subdomain wing scoping (architecture/diagnostics/methodologies/patterns/etc.), the hook must derive wing from the first subdirectory under `wiki/`, e.g., `wiki/architecture/foo.md` → `wing=wiki-architecture`. Existing drawers under the legacy `wiki-kf-core` wing remain queryable via that wing name — migration is optional.

2. **Wing-inference path for queries.** If Phase 2 wires `mempalace_search` into any hook, that hook needs a deterministic way to infer the right wing from a query. Options: extend `kf-route.py`'s Gemini classifier to return a `wiki_wing` field, OR use a static mapping from `cross_cutting` module IDs to wings, OR omit wing scoping and accept noisier results.

3. **Hook output schema.** `kf-route.py`'s UserPromptSubmit output uses `updatedPrompt`, not `additionalContext`. Any context-injection design in Phase 2 must conform to the actual UserPromptSubmit output schema, not an imagined one.

### Two-Phase Retrieval (Hierarchical Filter)

```
query
  → extract domain / topic / tag signals from query text
  → Phase 2a (metadata pre-filter):
      candidates = entries where domain matches ∩ topic matches
                   UNION entries with ≥ 2 tag overlaps
  → call mempalace_search(query, wing=inferred_wing, limit=50)
  → intersect MemPalace results with frontmatter-filter results
  → Phase 2b (score fusion re-rank)
  → return top-K
```

Implementation pattern: client-side wrapper around `mempalace_search` that pulls a broad candidate set, reads each result's source MD file, parses frontmatter, applies metadata filter + fusion math in Python.

### Score Fusion

```
final_score(entry) =
  0.65 · cosine_similarity(query_emb, entry_emb)   // from MemPalace
  + 0.20 · normalize(entry.importance, range=[1,5]) // from frontmatter
  + 0.15 · recency_boost(entry.last_accessed, entry.staleness_risk)
```

`recency_boost`:

```
recency_boost(last_accessed, staleness_risk) =
  exp(-λ · days_since_access)
  where λ = 0.01 for staleness_risk = stable
            0.05 for staleness_risk = slow_decay
            0.15 for staleness_risk = volatile
```

Cosine similarity is supplied by MemPalace; importance and recency are computed client-side from frontmatter.

---

## Phase 2 Upgrade Triggers

Phase 2 work is gated by observed evidence. Any one of these signals — when reproducibly observed — escalates `knowledgeforge-core-acu` from P4 to P2.

1. **Scale + off-domain noise.** Wiki crosses 100 entries AND a sample of `mempalace_search` queries returns ≥ 2/5 off-domain results in the top-5. Measure by manual sampling once per month or whenever wiki grows by ≥ 25 entries.

2. **Observed false negative.** Orchestrator fails to surface an obviously-relevant wiki entry that exists, in a session where it should have. File a `wiki/diagnostics/YYYY-MM-DD_module22-false-negative-*.md` entry when observed. Two such reports = trigger.

3. **Duplicate creep past threshold.** `mempalace_check_duplicate` at threshold 0.85 misses a near-duplicate and a duplicate gets filed. File `wiki/diagnostics/YYYY-MM-DD_module22-duplicate-miss-*.md`. One report = investigate; two = trigger.

4. **User-reported "search isn't finding things."** Subjective report from David. Single report = trigger immediately (priority overrides quantitative signals).

When triggered: open `bd show knowledgeforge-core-acu`, escalate priority from P4 to P2, and begin the Phase 2 implementation pass (which starts with fixing the wing-derivation defect listed under Prerequisites above).

---

## Attribution

| Element | Source |
|---------|--------|
| Hierarchical metadata-gated retrieval, 60% → 95% R@10 (Phase 2 target) | LongMemEval benchmark, Arora et al. 2025 |
| Score fusion design (Phase 2) | KF original (v6.5.0) |
| MemPalace | github.com/milla-jovovich/mempalace — MIT |
| ChromaDB (under MemPalace) | trychroma.com — Apache 2.0 |
| Phased A→D architectural decision | knowledgeforge-core-8xq Strategist analysis (2026-05-24) |
| Phase 1 scope reduction post-critic | knowledgeforge-core-8xq adversarial-critic findings (2026-05-24) |

---

## Related Modules

- `19_Memory_Architecture.md` — Tier 0 is the search corpus
- `21_Knowledge_Accretion.md` — write-time pipeline triggers `mempalace-wiki-mine`
- `23_Taxonomy_Enforcement.md` — frontmatter vocabulary (Phase 2 input)
- `24_Verbatim_History_Mining.md` — same MemPalace backend, different wings
- `17_Temporal_Knowledge.md` — staleness vocabulary (Phase 2 input)

## CC Doc

# Module 22: Semantic Wiki Search — Execution Protocol (Phase 1)
**Apply when:** [KF-ROUTE] load list includes M22, or filing a new wiki entry (accretion-check)

Phase 1: KF wires `mempalace_check_duplicate` into accretion as a detect-and-warn gate. No pre-loaded retrieval context, no wing/room scoping, no score fusion — all deferred to Phase 2 (workload-triggered, not scheduled). MemPalace's full MCP surface remains available to the orchestrator at runtime for ad-hoc queries.

## Phase 1 Required Behavior

**Accretion-check dup gate (the only Phase 1 hook integration — target state, pending `knowledgeforge-core-rk4`).** In `mempalace-wiki-mine.py`, BEFORE the existing `mempalace mine` subprocess (i.e., between the fingerprint-idempotency check and the `mine_wiki()` call), call:

```python
try:
    from mempalace.mcp_server import tool_check_duplicate
except BaseException as e:  # BaseException, not Exception — argparse may raise SystemExit
    sys.stderr.write(f"[Module 22 FALLBACK] import failed: {e}\n")
else:
    try:
        result = tool_check_duplicate(content=entry_text, threshold=0.85)
        if result.get("is_duplicate"):
            sys.stderr.write(f"[Module 22] near-duplicate detected for {file_path}: ...\n")
    except Exception as e:
        sys.stderr.write(f"[Module 22 FALLBACK] dup-check failed: {e}\n")
```

Use direct Python import — there is no `mempalace check-duplicate` CLI subcommand. Two failure modes to guard:

1. The import runs `MempalaceConfig()` + `KnowledgeGraph()` at module-load (mcp_server.py:59-63). `KnowledgeGraph()` opens a SQLite connection; misconfigured palace state raises `Exception`. Verify with `python -m mempalace status` once before deploying.

2. The import also runs `_parse_args()` against `sys.argv` (mcp_server.py:41-54). If `sys.argv` contains `-h`/`--help`, argparse raises `SystemExit` — which `except Exception` does NOT catch (SystemExit inherits from BaseException). Use `except BaseException` for the import guard.

Detect-and-warn; do NOT block the mine (the file is already on disk).

**Fallback.** Wrap every MemPalace call in try/except. On failure, emit `[Module 22 FALLBACK]` to stderr and continue. Use `grep -rli` against `wiki/` if any retrieval is needed (Phase 1 doesn't pre-load retrieval; this is the last-resort surface for ad-hoc orchestrator queries).

## Phase 1 Anti-Patterns

- Calling `python -m mempalace check-duplicate` (CLI subcommand doesn't exist)
- Calling ChromaDB directly (go through MemPalace)
- Passing `wing` to `tool_check_duplicate` (it ignores the arg silently)
- Pre-loading retrieval context from any hook (Phase 2 only)
- Treating the dup-check as a write-block (PostToolUse is too late)

## Phase 2 Triggers (escalate the Phase 2 bead `knowledgeforge-core-acu` when observed)

- Wiki > 100 entries + sampled queries return ≥2/5 off-domain results in top-5
- Two filed `wiki/diagnostics/*module22-false-negative*` entries
- Two filed `wiki/diagnostics/*module22-duplicate-miss*` entries
- David reports "search isn't finding things"

## Success Criteria (Phase 1)

`mempalace-wiki-mine.py` calls `tool_check_duplicate` before mining. Every near-duplicate filed has a stderr WARNING. Hook crash rate = 0. Grep-fallback engagement < 5%. Recall/precision metrics are deferred to Phase 2.
