# Module 25 Spec Patch — Entity → Path-Glob Resolver

**Bead:** `knowledgeforge-core-8gp`
**Phase:** 1 of 1 (single-bead spec; impl tracked separately)
**Status:** SPEC — no implementation. Stop at human gate.
**Module target:** `modules/25_entity_relationship_analysis.md`
**Proposed bumps (versions verified 2026-06-12):**
- M25 module: 7.0.3 → **7.1.0** (minor — new behavior, additive)
- M21 module: 7.1.3 → **7.1.4** (patch — extends step_2c with new lookup path; backwards-compatible default)
- kf.yaml system: 7.7.1 → **7.8.0** (minor, follows M25)
**Decision class:** evaluative (resolver-shape selection) + reckoning (interface schema). Tagged inline.

**Revision history:**
- 2026-06-12 r1: initial draft
- 2026-06-12 r2: revised per adversarial-critic findings [1]–[5]. Changes:
  - [1] HIGH — added explicit step_3c interaction protocol: ERA-resolved globs on global-scope candidates downgrade trigger to `task_bound` (not rejection). Resolves the silent-rejection failure mode.
  - [2] HIGH — replaced "longest prefix wins" with a fully-specified comparison function: (a) literal-character-count of pre-wildcard prefix; (b) tiebreak by lexicographic order of full glob. Deterministic.
  - [3] HIGH — cache key changed from `entity_name` to `(entity_name, repo_root)` where repo_root resolves via `git rev-parse --show-toplevel`. Multi-repo sessions no longer contaminate.
  - [4] HIGH — demoted `resolver_source` to diagnostic metadata; explicit "no current consumer" note; drift detection deferred to a separate calibration bead.
  - [5] HIGH — M25 version read empirically (7.0.3); spec now states actual bump targets.

---

## 0. What this spec changes (1-sentence summary)

Adds an entity → path-glob resolver to ERA (Module 25) so that `memory_filter.entities` (which today contains entity NAMES like "API gateway") can also produce `entity_paths` (a dict of glob patterns keyed by entity), which M21 reads into `activation_profile.path_globs` when emitting path-bound accretion candidates. **Strategist-mode decision** on resolver shape: select GitNexus-first with session-cached grep fallback.

---

## 1. Why this work matters now

**Decision tag:** reckoning (gap is documented). Confidence: **high**.

From Phase 1 spec (`y4b` Section 4):

> ERA emits entity *names* ("API gateway"), not file paths. The translation step (entity → repo-specific path glob) is unspecified work.

From Phase 2 spec (`5fd` Section 4):

> Under Option A, expect ~90% invariant, ~10% task_bound, **<1% path_bound** (Debugger-only) until the resolver ships.

**The Phase 2 cc_rules emitter shipped with `<1% path_bound` baked in.** It works correctly, but the entire `trigger: path_bound` branch is sparse-at-best. Shipping this resolver moves the expected distribution toward a balanced shape (rough estimate ~60% invariant / ~25% task_bound / ~15% path_bound — to be measured post-ship). Without it, the Phase 2 emitter's `.claude/rules/kf/` directory will stay empty or near-empty in practice.

---

## 2. Constraints inherited from ERA

**Decision tag:** reckoning. Confidence: **high**. Direct quote from M25:

| Constraint | Source | Implication for resolver |
|---|---|---|
| **<5% routing overhead** | M25:201 | Resolver must be cheap; no per-call full-repo scan |
| **Entity NAMES, not file paths** | M25:87 ("Entities are named from the query itself, not inferred") | Resolver maps abstract concept → concrete file globs; entity types include Concepts and States which often aren't code symbols |
| **5 entity types** (System / Actor / Concept / State / Artifact) | M25:75 | Resolver must handle non-code-symbol entities (Concepts especially are unlikely to map to file paths) |
| **No internal-only inference** | M25:87 ("ERA does not add entities the user didn't mention") | Resolver is allowed to produce ZERO globs for an entity if no real files match — that's the correct behavior, not a failure |
| **ERA output is internal** | M25:201 | The resolver's output is consumed by M21, not surfaced to the user |
| **Per-repo specificity** | y4b Section 4 — "globs are repo-specific" | Resolver must be repo-aware; cross-repo globs are invalid |

---

## 3. Resolver design space (Strategist analysis)

**Decision tag:** evaluative (option selection with explicit trade-offs). Confidence: **medium-high** on recommendation; **low-medium** on quantitative overhead estimates (calibration cycle will measure).

Four resolver shapes are viable. The matrix:

| Shape | Overhead | False-positive risk | Maintenance | Repo coverage |
|---|---|---|---|---|
| **A. Grep-per-query** | High (>5% at scale) | High — generic names ("session") match wildly | None | All repos |
| **B. Session-cached grep** | Low after first call | Medium — first-call accuracy depends on grep regex craft | None (session-scoped) | All repos |
| **C. Pre-built repo index** | Low (file read) | Low (offline-curated) | High — index drift; needs maintenance pass | Per-repo manual setup |
| **D. GitNexus integration** | Low (MCP call) | Low (production-quality resolver) | None (GitNexus owns) | Only GitNexus-indexed repos |

### Recommendation: **D-primary with B-fallback**

**Primary path: GitNexus.** When `gitnexus_context` or `gitnexus_query` is available in the session (KF's global CLAUDE.md already mandates GitNexus usage when indexed), ERA delegates entity-name lookup to GitNexus. GitNexus already returns file paths for symbols; ERA wraps those paths as globs (file-path → containing-directory glob + extension pattern). This gives near-zero KF maintenance cost.

**Fallback path: session-cached grep.** When GitNexus is unavailable (e.g., a fresh repo not yet `npx gitnexus analyze`-d), ERA falls back to a session-cached grep approach:

1. On first ERA call against a given repo in a session, scan the repo for entity-candidate paths using `git grep -l` against the entity name plus common variations (kebab-case, snake_case, camelCase, PascalCase).
2. Cache the result keyed by `(entity_name, repo_root)` where `repo_root` resolves via `git rev-parse --show-toplevel` at cache-write time (resolves Critic finding [3] — repo-switching contamination). Cache is in session memory (Tier 2 per Module 19).
3. On subsequent ERA calls in the same session-and-same-repo, read from cache.
4. When the session's cwd changes to a different repo_root, a fresh cache scope is created — entries from the previous repo are not returned for the new repo even if entity names collide.
5. Cache invalidates at session end (auto-memory clears it; Module 19 owns the lifecycle).

**Hybrid strategy** (recommended): try GitNexus FIRST; on failure (tool unavailable OR returns empty), fall back to grep cache. Both paths feed the same `entity_paths` output shape.

### Why not C (pre-built repo index)?

C is technically the lowest-overhead option per-call (just file read), but the maintenance burden is real — index files drift, require commit hooks or periodic regen, and the user has to opt-in per-repo. GitNexus already solves the "production-quality resolver" problem for the repos that have it, and the grep fallback is acceptable for repos that don't. C adds a second moving part for a marginal gain.

### Why not A (grep-per-query)?

A blows the 5% overhead budget at any repo of meaningful size. ERA is a lightweight pass; spending 30%+ of its budget on grep would change ERA's character.

---

## 4. Resolver output schema

**Decision tag:** reckoning + novel. Confidence: **high**.

Extend the ERA output format (M25:209) with a new `entity_paths` field alongside the existing `memory_filter`:

```yaml
era:
  entities:
    - {name: "API gateway", type: system}
    - {name: "session store", type: system}
    - {name: "rate limit policy", type: concept}
  # ... existing fields ...
  memory_filter:
    entities: [API gateway, session store, rate limit policy]
    domain: architecture
    topic: distributed-systems
  # NEW — added in this spec
  entity_paths:
    # Map of entity-name → list of glob patterns. Empty list = resolver
    # found no matching files (valid outcome; not an error).
    "API gateway": ["src/api/**/*.ts", "src/gateway/**/*.ts"]
    "session store": ["src/storage/session*.ts", "config/redis.yaml"]
    "rate limit policy": []  # concept — no concrete files match; correct empty result
  resolver_source:
    # DIAGNOSTIC METADATA only — no current consumer module reads this.
    # Records which resolver produced the entity_paths above. Useful in
    # post-hoc debugging if path_globs look wrong, but NO module currently
    # acts on this field. Drift-detection use case is deferred to a
    # separate calibration bead (per Critic finding [4]).
    # When that bead lands, this comment block updates to name the consumer.
    primary: gitnexus | grep | none
    gitnexus_attempted: true | false
    grep_attempted: true | false
```

### Glob derivation rules

When the resolver returns a list of file paths (from GitNexus or grep), it converts paths to globs:

- **Single file:** the path itself becomes the glob.
- **N files in a single directory:** `dirname/*.ext` if all share an extension; `dirname/**/*` otherwise.
- **N files across directories:** `**/*.ext` only if all share an extension AND span enough directories to be a wildcard win; otherwise keep individual paths.
- **Maximum 5 globs per entity** — anything beyond suggests the entity is too generic to path-bind (e.g., "config" matches everywhere); cap to 5 most-specific globs (per the comparison function below); emit a LOW finding via the Knowledge Base Linter for the over-match.

### Glob comparison function (deterministic — resolves Critic finding [2])

When ranking globs for the "5 most-specific" cap (applied at both per-entity derivation and at M21's join step), specificity is defined by this comparison:

1. **Primary key — literal-character count of the pre-wildcard prefix.** For each glob, extract the prefix up to the first wildcard character (`*`, `?`, `[`). The character count of that prefix is the score. Examples:
   - `src/api/auth.ts` → prefix `src/api/auth.ts`, score = 15
   - `src/api/**/*.ts` → prefix `src/api/`, score = 8
   - `**/*.ts` → prefix `` (empty), score = 0
   - `src/` vs `tests/` — score 4 vs score 6; `tests/` ranks more-specific despite equal directory-tree depth (this is a quirk of the rule — accepted because real-world prefixes rarely tie in practice and the rule is deterministic)
2. **Tiebreak — lexicographic order of the full glob.** Same prefix score → alphabetical, ascending.
3. **No semantic prefix interpretation.** The function does NOT distinguish `src/` from `tests/` by meaning; both are literal-character prefixes. Designers wanting semantic ranking should embed it in the resolver path (e.g., grep filter to exclude `tests/` paths before glob derivation), not in the comparison function.

---

## 5. M21 + Phase 2 emitter integration

**Decision tag:** evaluative. Confidence: **high**.

### M21 reads `entity_paths` at step_2c — with step_3c interaction protocol

M21's `step_2c_activation_profile.compute.path_globs` (Phase 1 spec Section 3) gets a new lookup path:

```yaml
path_globs:
  # 7.1.4 (added in this spec): for modes that consume ERA output (Builder,
  # Coordinator, Expert, Strategist, Critic), join all era.entity_paths
  # values into a single flat list (deduplicated). If the join produces
  # >5 globs, keep the 5 most-specific (per the comparison function in
  # M25 7.1.0 — Glob comparison function section).
  #
  # If era is absent (Debugger which falls back to filename-in-body
  # heuristic, or modes not consuming ERA), the existing Phase 1 logic
  # applies unchanged.
```

### Step_3c interaction protocol (resolves Critic finding [1])

The Phase 1 spec's step_3c cross-validation rejects any candidate where `trigger == path_bound AND scope == global` because globs are repo-local. With the resolver active, ERA-driven globs commonly appear on globally-scoped candidates (architectural patterns that span multiple repos). Silent rejection would make the resolver invisible — exactly the failure the resolver is supposed to fix.

**New rule (M21 7.1.4 patch):** When step_3c encounters `trigger == path_bound AND scope == global AND path_globs[].source == ERA`, instead of rejecting, **downgrade the trigger to `task_bound`** and clear `path_globs`. Log the downgrade to `compile_log_format` with reason `era_global_glob_downgrade`. Rationale: the candidate is still valid (knowledge has reuse value), and `task_bound` (mode-on-demand) is the correct semantic for cross-repo knowledge that touches specific entities — it surfaces when those entities are mentioned, regardless of file paths.

Manually-authored `path_globs` (where the producing mode explicitly emitted them in `accretion_note` per Phase 1) still trigger rejection on global scope — only ERA-resolver-produced globs get the downgrade. Distinguishing source requires a small additional field on `path_globs`:

```yaml
path_globs: [string]      # backwards-compatible — strings work
path_globs_meta:          # NEW 7.1.4 — optional sidecar, only ERA-populated globs get an entry
  - {glob: "src/api/**/*.ts", source: era}
  - {glob: "src/gateway/**/*.ts", source: era}
```

step_3c reads `path_globs_meta` if present; entries with `source: era` downgrade-on-global, entries without metadata (manual) reject-on-global per existing Phase 1 rule.

**Bumps M21 7.1.3 → 7.1.4** (patch — new lookup path + step_3c downgrade rule; backwards-compatible default when ERA absent).

### Phase 2 emitter benefits without change

The cc_rules emitter (Phase 2) reads `activation_profile.path_globs` and produces `.claude/rules/kf/*.md` with `paths:` frontmatter. No emitter change needed; the resolver just populates a field the emitter already consumes.

---

## 6. M25 changelog

**Decision tag:** reckoning. Confidence: **high**.

```yaml
- date: 2026-06-12
  driver: knowledgeforge-core-8gp
  spec: docs/planning/2026-06-12_module-25-entity-path-glob-resolver-spec.md
  changes:
    - Added entity-path resolver to ERA output. Two-source strategy — GitNexus primary, session-cached grep fallback. Produces entity_paths dict alongside existing memory_filter.
    - Glob derivation rules (single-file, N-in-dir, N-across-dirs, max-5-cap with linter flag).
    - Forward-compatible — existing ERA consumers (M22 Phase 2, Module 24, downstream modes) ignore the new field cleanly; M21 path_globs lookup is the only currently-active consumer.
    - Overhead budget — primary path (GitNexus) adds <2% to ERA's existing <5%. Fallback path (grep on first call, cache afterward) target <3% on first call, ~0% on subsequent. Calibration via M12 in post-ship cycle.
```

---

## 7. Adversarial probes (Critic prep)

| Probe | Response |
|---|---|
| **"GitNexus availability varies — fallback is the common case for new repos."** | Acknowledged. Fallback path (grep cache) is designed for full functionality; GitNexus is an optimization for repos that have it. Fallback overhead is bounded by cache (only first call pays full cost). |
| **"Concept-type entities (Concept, State) often have no matching files. Empty `entity_paths` shouldn't break downstream."** | Section 4 explicitly says empty list is valid outcome. M21's path_globs join treats empty input as "no path-bound trigger" — falls back to invariant or task_bound. Designed for this. |
| **"Glob derivation rules are heuristics. What if all 5 most-specific globs are still wrong?"** | LOW Critic linter finding on over-match. Doesn't block filing. Subsequent calibration can tune the cap or derivation rules. Same pattern as M21's existing default_importance inference (M21:306) — heuristic with linter feedback. |
| **"Resolver caches won't survive session boundaries — every fresh session re-grep'd."** | True. Tier 2 (per Module 19) is session-scoped by design. Cross-session resolver state would conflict with M19's scoping rules. A cross-session shape (Tier 0 or 2B) is a separate calibration bead if it becomes needed. |
| **"GitNexus dependence is a soft-coupling — what if GitNexus removes the relevant tools?"** | Fallback path is fully functional standalone. GitNexus is upside, not requirement. Spec doesn't propose making GitNexus mandatory. |
| **"Naming collisions: two entities resolve to overlapping globs (`src/api/auth.ts` matches both 'API' and 'auth')."** | Each entity gets its own `entity_paths[name]` list. Overlaps at the M21 join step are deduplicated. The dedup loses the entity→glob attribution but Phase 2 emitter only cares about the joined glob list, not which entity contributed which path. |
| **"The 5% overhead budget is for ERA as a whole. Resolver adds to it. Where's the headroom?"** | M25:201 says "<5% overhead." Resolver's primary path is <2% (GitNexus MCP call latency). Fallback's first call may briefly exceed 5% on first-call-of-session; subsequent calls return to <5%. Calibration bead will measure and tune. |

---

## 8. What this spec does NOT change

- Does not change the 5-entity-type taxonomy (M25:75) or 8-relationship taxonomy (M25:91).
- Does not change ERA's triggering rules (M25:193) — still Builder/Coordinator/Expert/Strategist/Critic always; Debugger conditional; never reckonings/Navigator.
- Does not propagate to M24 Verbatim History Mining (separate deferred bead).
- Does not change M22 Phase 2 (which is acu-deferred and independent).
- Does not introduce a Tier 0 entity index (deferred to a separate calibration bead if needed).
- Does not make GitNexus a hard dependency for ERA — fallback path is fully functional.

---

## 9. Post-approval implementation sequence — DO NOT EXECUTE during spec review

1. **Verify gate:** confirm M25's current version (currently unread; possibly 7.x.y).
2. **Edit M25:** bump version, append changelog entry, extend ERA Output Format with `entity_paths` + `resolver_source`, add Glob Derivation Rules subsection, add Resolver Implementation subsection (with GitNexus-primary + grep-fallback shape).
3. **Edit M21:** bump 7.1.3 → 7.1.4, append changelog entry, extend `step_2c_activation_profile.compute.path_globs` with the `entity_paths` join rule.
4. **Edit kf.yaml:** bump 7.7.1 → 7.8.0, changelog entry.
5. **Verify compile** — `python3 compiler/kf-compile.py --target claude-code --output /tmp/kf-cc-dryrun --dry-run` — 33 clean outputs expected.
6. **Open follow-up beads:**
   - **"Cross-session resolver state (Tier 0 entity index)."** P4 — only if calibration shows it's needed; deferred today.
   - **"Resolver calibration cycle"** — P3 follow-up to measure GitNexus-vs-grep distribution + first-call overhead + glob over-match rate. Integrates with M12.

---

## 10. Confidence summary

| Component | Confidence | Why |
|---|---|---|
| Resolver shape selection (D-primary + B-fallback) | **High** | Matrix-grounded; aligns with KF's existing GitNexus integration |
| Output schema (`entity_paths` + `resolver_source`) | **High** | Forward-compatible additive; no breaking change to existing ERA consumers |
| Glob derivation rules | **Medium** | Heuristic; over-match cap protects worst case; calibrate post-ship |
| M21 integration (step_2c join) | **High** | Small additive patch; backwards-compatible default |
| Overhead budget claim | **Medium-low** | Quantitative estimates not yet measured; calibration cycle scheduled |
| Resolver source telemetry (for drift detection) | **High** | Useful operational data; cheap to record |
| GitNexus fallback strategy | **High** | Both paths designed for full functionality; no hard dependency |

---

## HUMAN GATE — 8gp approval

- **Approve** → proceed to implementation pass (Section 9), file 2 follow-up beads
- **Approve with conditions** → state conditions; revise; re-gate
- **Reject** → state reason; revise or abandon

---

## Cross-references

- Bead `8gp`: this work
- Bead `y4b` (Phase 1 spec): `docs/planning/2026-06-10_module-21-activation-profile-spec.md` Section 4 surfaces the gap this resolves
- Bead `5fd` (Phase 2 spec): `docs/planning/2026-06-10_cc-rules-and-hook-emitter-spec.md` Section 4 documents the <1% path_bound expectation pre-resolver
- Phase 1 impl (commit `1fc709e`): M21 v7.1.0 ships `activation_profile.path_globs` field this resolver populates
