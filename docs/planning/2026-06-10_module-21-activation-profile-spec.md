# Module 21 Spec Patch — `activation_profile` on Accretion Candidate Metadata

**Bead:** `knowledgeforge-core-y4b`
**Phase:** 1 of 2 (Phase 2 = cc rules + hook emitter, separate bead on approval)
**Status:** SPEC — no implementation. Stop at human gate.
**Module target:** `modules/21_knowledge_accretion.md`
**Proposed version bump:** 7.3.1 → **7.4.0** (minor; see Section 5 for defense against breaking-change reading)
**KF system version:** `kf.yaml` bumps to match per project CLAUDE.md versioning rule
**Decision class:** evaluative (gate semantics) + novel (new field shape). Tagged inline below.

**Revision history:**
- 2026-06-10 r1: initial draft
- 2026-06-10 r2: revised per adversarial-critic findings [1]–[6]. Changes:
  - [1] split step_2c into step_2c (assignment) + step_3c (cross-validation after scope is known) — eliminates the lookahead
  - [2] added explicit expected-distribution note in Section 4 and Phase 2 carry-forward
  - [3] reframed `native` as a deferred-activation field — v1 default `false`, no auto-evaluation, gate clause is inert at v1 with the calibration path documented
  - [4] added Section 1b with explicit CC Doc patch text
  - [5] added backwards-compatibility defense for the minor-bump claim
  - [6] retitled Section 11 and bracketed steps as post-approval only

---

## 0. What this spec changes (1-sentence summary)

Add a substrate-agnostic `activation_profile` block to the `accretion_candidate` schema at `modules/21_knowledge_accretion.md:288`, and add a gate-level **non-native suppression clause** to the two-condition test. The profile attaches at metadata finalization (gate-passed candidates only) and is consumed by downstream dispatchers (Module 22, MemoryRouter, the future cc rules/hook emitters).

---

## 1. Schema patch (the proposed Module 21 edit)

**Decision tag:** novel — new field shape; no prior KF schema codified it. Confidence: **high** (substrate-grounded by docs.claude.com/en/memory and /en/claude-directory, fetched 2026-06-10).

Insert at line 331 (immediately after the `staleness_risk` definitions block, before `---` and `## Two Runtime Behaviors`):

```yaml
  # ---------------------------------------------------------------------------
  # Activation profile — added 7.4.0
  # ---------------------------------------------------------------------------
  #
  # Substrate-agnostic metadata describing HOW a downstream dispatcher should
  # surface this candidate. Computed in core, consumed by downstream routers.
  # The profile is dispatch-input only — except `native`, which is gate-input
  # (see Section 2 below). The profile NEVER references substrate concepts
  # like "is there a rules dir" or "settings.json exists" — those are
  # cc-target concerns, not core concerns.
  #
  activation_profile:
    trigger: invariant | path_bound | task_bound
      # invariant: applies regardless of which files the session touches
      # path_bound: applies only when files matching path_globs are read
      # task_bound: applies only when a specific mode/skill is invoked
      #
      # Trigger is descriptive metadata about WHEN this knowledge is relevant.
      # Downstream dispatchers map it onto substrate (e.g., cc maps
      # invariant→unscoped rule, path_bound→path-scoped rule, task_bound→skill).

    decidability: true | false
      # Does a mechanical predicate exist for "this rule was applied / violated"?
      # true  → eligible for hook-class enforcement downstream
      # false → advisory only; downstream may only render as guidance
      # Dispatch input. Not consulted at the gate.

    miss_cost: low | medium | high
      # If this knowledge is not surfaced when relevant, what is the cost?
      # low    → minor inefficiency, easy correction
      # medium → recurring rework, possible quality regression
      # high   → defect class, lost data, broken deploy, customer-visible bug
      # Dispatch input. Selects between tiers; not consulted at the gate.

    native: true | false
      # Does the model already exhibit this behavior natively?
      # true  → SUPPRESS at gate (do not persist; see Section 2)
      # false → proceed to filing protocol
      # Codifies the KF meta-principle: patch weaknesses, do not scaffold
      # strengths. See `~/.claude/rules/kf-meta.md` and Module 13 commentary.
      # Gate input. The one gate-clause field in this block.

    path_globs: [string]      # optional; required only when trigger == path_bound
      # Glob patterns identifying the files for which this knowledge is relevant.
      # Substrate-agnostic shape (string globs). Downstream cc target uses these
      # verbatim as the `paths:` frontmatter on a generated rule file.
      # Constraints:
      #   - Repo-specific by nature → travels ONLY with project-scoped candidates
      #     (scope=project per step_3 classification). Global-scoped candidates
      #     with trigger==path_bound are an error; reject at metadata finalization.
      #   - Empty list with trigger==path_bound is also an error.
      #   - Provenance: see Section 4 (ERA→path_globs handoff).
```

---

## 1b. CC Doc patch (resolves Critic finding [4])

**Decision tag:** reckoning. Confidence: **high**.

The CC Doc section (M21:1025–1085) is a separately maintained verbatim block compiled into the cc agent's docs. It is NOT generated from the structured YAML in the main body — it is hand-written prose/markdown in the same file. The schema patch in Section 1 above modifies the main-body YAML at line 288; this Section 1b modifies the CC Doc block at line 1056.

### Patch 1b.1 — Two-condition test → three-condition test (replaces M21:1032–1038)

```markdown
## Three-Condition Test

Flag as `ACCRETION_CANDIDATE` when ALL THREE are met:
1. **Novelty:** Knowledge not already present in the existing knowledge base.
2. **Reuse value:** Would benefit future queries beyond the current session.
3. **Non-native:** The model does not already exhibit this behavior natively (v1: default false, see activation policy).

Novelty alone is not enough. A unique observation with no transferable value is not a candidate. A reusable observation that the model already exhibits without instruction is also not a candidate (suppressed at the gate; logged to compile.md for audit).
```

### Patch 1b.2 — Candidate Metadata block (replaces M21:1056–1066)

```markdown
## Candidate Metadata

```yaml
accretion_candidate:
  source_mode: [mode]
  grounding_score: [0.0–1.0]
  novelty_type: [see table above]
  knowledge_target: [specific wiki section]
  staleness_risk: stable | slow_decay | fast_decay
  created: [ISO date]
  activation_profile:
    trigger: invariant | path_bound | task_bound
    decidability: true | false
    miss_cost: low | medium | high
    native: true | false      # v1: always false (deferred-activation; see full schema in main body)
    path_globs: [string]      # required only when trigger == path_bound
```
```

### Patch 1b.3 — Add Activation Profile summary (insert after Candidate Metadata block, before Grounding Gate)

```markdown
## Activation Profile

Computed at `step_2c` after the three-condition gate. Carries dispatch-time signals for downstream routers; does not affect gate eligibility (except `native`, which is gate input). Full schema in main body. Common shapes:

| Mode | Default trigger | Default decidability | Default miss_cost |
|---|---|---|---|
| Synthesizer | invariant | varies | low |
| Strategist  | invariant | varies | medium |
| Builder / Calibrator | invariant | varies | low |
| Critic linter | invariant | true | high |
| Expert | invariant (path_bound if ERA + author globs) | varies | medium |
| Debugger | path_bound if filename in body else task_bound | true | medium |

At v1, `trigger: path_bound` is sparse (<1% expected) because the entity→path resolver is deferred to a follow-up bead. Designs that depend on a balanced trigger distribution should wait.
```

### Patch 1b.4 — Filing Protocol Gates (append to M21:1077–1081)

After the existing Gate 4a / Gate 4b prose, append:

```markdown
**Step 2c (Activation profile assignment):** Between gate and step_3, assign `trigger / decidability / miss_cost / native` per mode lookup tables. Populate `path_globs` only when mode authors them. Partial validation only (no scope cross-cut yet).

**Step 3c (Profile cross-validation):** After step_3 scope is known, reject `trigger: path_bound + scope: global` candidates (path_globs are repo-local). Log rejection to compile.md.
```

---

## 2. Gate clause — `native: true` suppression (deferred-activation at v1)

**Decision tag:** evaluative. Confidence: **high** on shape and seam; **medium** on v1 behavioral impact (intentionally minimal).

The KF meta-principle ("modes patch weaknesses, not scaffold strengths" — `~/.claude/rules/kf-meta.md`) already governs runtime mode invocation. Extending it to the persistence layer is consistent: persistent knowledge that codifies a native behavior is dead weight that pollutes the KB.

The current two-condition test (Module 21:1032–1038, CC Doc verbatim) becomes a three-condition test:

```
Flag as ACCRETION_CANDIDATE when ALL THREE are met:
  1. Novelty:      Knowledge not already present in the existing knowledge base.
  2. Reuse value:  Would benefit future queries beyond the current session.
  3. Non-native:   The model does not already exhibit this behavior natively.

Failing any condition → not a candidate. Drop silently (no surfacing,
no metadata generation, no filing).
```

**Why `native` is a gate concern, not a dispatch concern** (the question the handoff asked us to resolve):

- The Dispatcher Boundary (Module 21:936) assigns the downstream router **physical write path** and **tier selection** — but NOT eligibility-to-persist. Eligibility is gate-side.
- `native: true` means "this should not persist at all." That decision must happen before metadata finalization to avoid wasted candidate construction and to keep the dispatcher pure (rendering, not eligibility).
- Structurally, `native: true` is symmetric with `novelty: false` and `reuse_value: false` — all three are pre-conditions on persistence. They belong together at the gate.

**Suppression behavior:** Identical to a novelty-fail today — no surface to the user, no filing — EXCEPT a suppression event MUST be appended to `compile.md` with the candidate body and `suppressed_by: native` reason. Rationale: over-suppression produces invisible false negatives (Critic finding [3]); the compile log is the audit trail that makes over-suppression detectable in linter health checks.

### v1 activation policy — deferred-activation (resolves Critic finding [3])

**The `native` field ships at v1 in inert-default mode:**

- **Default value:** `false`. Absence-equals-false. No mode auto-emits `native: true` at v1.
- **No mode self-evaluation at v1.** The Critic finding correctly identifies that a mode evaluating "is this thing I just produced something I produce natively?" is circular and unfalsifiable. We do not attempt this at v1.
- **Only assignment source at v1:** human review via the existing `importance_source: inferred → human_set` lifecycle (Module 21:302). A human reviewing wiki entries may set `native: true` retroactively; future candidates matching the same content shape are then suppressed at the gate by the linter's duplicate-check (Module 21:477+).
- **Effect at v1:** the gate's behavioral impact is zero on existing modes. The gate clause is *structurally* present (third condition) but *practically* inert because no candidate gets `native: true` at production time without human action.

**Activation path (out of scope for this bead):** A future calibration bead defines mode-side auto-evaluation criteria. Probable shape:

- An accretion candidate is `native: true` if the proposed knowledge text is generated by the model with zero KF context in a clean session at temperature 0 with high probability. This is observable, falsifiable, and calibratable via Module 12.
- The calibration bead also defines the false-negative detection protocol: suppression events in `compile.md` are periodically reviewed; any suppression that downstream sessions would have benefitted from is a false negative, threshold-tunable like novelty.

Without these criteria specified, v1 ships with `native` as a future-extensible field whose schema is locked but whose population logic is deferred.

**Why ship the field now instead of waiting:** The schema lock-in cost of adding the field later (after Phase 2 emitters ship) is higher than the cost of a temporarily-inert field. The field shape is the contract; the activation rules are an implementation detail.

---

## 3. Where the profile is computed (filing protocol seam)

**Decision tag:** reckoning (placement) + evaluative (two-pass design). Confidence: **high**.

`activation_profile` is part of the candidate metadata block, so it is finalized when the candidate metadata is finalized. Per Critic finding [1], the cross-cut `path_bound + global = error` cannot be evaluated until `step_3` has determined scope. Resolving by splitting profile computation across two passes — assignment in `step_2c` (no scope dep), cross-validation in `step_3c` (after scope is known). No lookahead, no out-of-order step dependencies.

### Pass 1 — `step_2c_activation_profile` (between gate and step_3)

```yaml
    step_2c_activation_profile:
      # Runs after the three-condition gate, before step_3 scope classification.
      # Assigns trigger/decidability/miss_cost/native. Does NOT validate scope cross-cuts.
      compute:
        trigger:
          # Inferred from the mode that produced the candidate + the candidate's content shape.
          # Lookup table:
          #   Synthesizer (new_pattern), Strategist (transferable_framework) → default invariant
          #   Builder (template_candidate), Calibrator (template_candidate)  → default invariant
          #   Critic linter (contradiction)                                  → default invariant
          #   Expert (reusable_analysis)                                     → invariant unless ERA emitted entity-scoped filters → path_bound
          #   Debugger (reusable_diagnostic)                                 → path_bound if filename/path appears in candidate body; else task_bound
          # Modes may override the default by emitting trigger explicitly in their accretion_note.

        decidability:
          # Heuristic: does the candidate body include a mechanical predicate?
          #   true  if body contains imperative + observable predicate
          #         ("Run X before Y", "All Z must include W")
          #   false otherwise
          # Modes may override.

        miss_cost:
          # Heuristic: rough mapping from novelty_type + grounding.
          # Default table:
          #   contradiction             → high
          #   reusable_diagnostic       → medium
          #   reusable_analysis         → medium
          #   transferable_framework    → medium
          #   new_pattern               → low
          #   template_candidate        → low
          # Boost by one tier if grounding ≥ 0.85.
          # Modes may override.

        native:
          # v1: always false (see Section 2 deferred-activation policy). The gate clause
          # in Section 2 still fires when native==true; v1 has no auto-emission of native==true.

        path_globs:
          # Populated only when trigger == path_bound AND the producing mode authored explicit globs.
          # See Section 4 (ERA handoff) for provenance.

      partial_validate:
        - If trigger == path_bound AND path_globs is empty → downgrade trigger to task_bound; log downgrade in compile_log
        - If trigger != path_bound AND path_globs is non-empty → strip path_globs (log warning)
        # NOTE: path_bound+global cross-cut is NOT evaluated here — see step_3c below.

      next: step_3_scope_classification
```

### Pass 2 — `step_3c_profile_cross_validate` (between step_3 and step_4a)

```yaml
    step_3c_profile_cross_validate:
      # Runs after step_3 (scope known) and step_3b (bootstrap done), before step_4a (taxonomy).
      # Validates the cross-cuts between activation_profile and scope.
      validate:
        - If trigger == path_bound AND scope == global → reject candidate
          reason: "path_globs are repo-specific; cannot travel with a global-scoped wiki entry"
          log_to: compile_log_format with reason "scope_glob_cross_cut"
        # Future cross-cuts (when added in subsequent revisions) attach here.

      next: step_4a_taxonomy_gate
```

**Why split-pass and not merge into step_3:** Conceptually, profile computation and scope classification are independent concerns. Merging would couple them and make step_3 do double duty. Cross-validation as a discrete sub-step preserves single-responsibility per step and keeps the step graph linear.

**Why both passes belong to Module 21 (not to a downstream router):** Both passes operate on candidate-metadata correctness — they ensure the metadata block is internally consistent before disk write. Internal consistency of a candidate IS the gate's responsibility per Dispatcher Boundary line 944 ("Candidate metadata generation ✓ Module 21"). Cross-validation is a sub-step of metadata generation.

---

## 4. ERA → `path_globs` provenance

**Decision tag:** evaluative + flagged gap. Confidence: **medium**. This is the one open seam in Phase 1.

**Current state** (Module 25 `ERA Output Format`, lines 209–226): ERA emits `memory_filter: {entities: [...], domain, topic}`. **Entities are names, not paths.** No path-glob resolver exists.

**Two viable shapes:**

| Option | Description | Cost | Risk |
|---|---|---|---|
| **A. Ship field, defer resolver** | M21 spec includes `path_globs` field. ERA continues to emit entity names. A future bead specifies the entity→path resolver (e.g., grep-based, ctags-based, or per-repo index). Until the resolver lands, `trigger: path_bound` is computable only when the producing mode emits explicit `path_globs` in its accretion_note. | Low | `path_bound` rare in practice until resolver ships; defaults absorb into `invariant` or `task_bound`. Survivable. |
| **B. Extend M25 to emit `entity_paths`** | M25 adds an `entity_paths: {entity_name: [glob]}` field to ERA output. M21 reads it and projects into `path_globs`. Requires a new entity→path resolver inside ERA. | Medium-high | Resolver design is its own sub-spec. Blocks Phase 1 on Module 25 changes. Violates "one change per submission." |

**Recommendation: Option A.** Ship the `path_globs` field shape in this spec; defer the resolver to a follow-up bead. Rationale:

- Aligns with the handoff's "one change per submission" discipline.
- Path-bound rules without a resolver are still useful when the producing mode authors the globs directly (Debugger frequently produces candidates that name specific files; Critic findings on file-path matches do too).
- A future resolver can be slotted in without re-spec'ing M21 — it's an upstream change to ERA, transparent to M21.

### Expected trigger distribution under Option A (resolves Critic finding [2])

Per Critic finding [2], the consequence of deferring the resolver must be stated explicitly so Phase 2 emitter authors are not building against an optimistic model:

| Trigger | Expected share at v1 (Option A) | Source |
|---|---|---|
| `invariant` | **~90%** | Default for Synthesizer / Strategist / Builder / Calibrator / Critic-linter / most Expert candidates |
| `task_bound` | **~10%** | Debugger candidates that don't name a file path; Expert when ERA emits entity filter but no glob authoring |
| `path_bound` | **<1%** | Debugger when filename/path appears in candidate body; any mode that explicitly emits path_globs |

**Phase 2 carry-forward note (mandatory):** The cc rules emitter spec must be written knowing that `trigger: path_bound` is a sparse case at v1. Designing the emitter against a balanced three-tier distribution would be dead-branching. The emitter's design should treat `invariant` as the common path, `task_bound` as the secondary path (routes to skill, not rule), and `path_bound` as the explicit-override case. This expectation graduates the moment the entity→path resolver bead lands.

**Follow-up bead to file on approval:** "M25: entity→path-glob resolver for ERA output (feeds M21 path_globs)." Open at P3, blocked-by `knowledgeforge-core-y4b`.

---

## 5. Module 21 changelog entry + semver defense

**Decision tag:** evaluative (semver level). Confidence: **high** with documented defense.

### Defense against breaking-change reading (resolves Critic finding [5])

The Critic argued that adding a third gate condition is a breaking change to the gate contract: any pre-existing candidate that previously met (novelty + reuse_value) but is `native: true` would have passed under 7.3.x and is rejected under 7.4.0. The argument is technically sound under a strict reading of "breaking interface change."

The minor-bump claim survives this reading because of the v1 deferred-activation policy in Section 2:

- **Backwards compatibility for existing modes:** No mode auto-emits `native: true` at v1. Therefore no candidate generated by existing modes can be affected by the new gate clause.
- **Backwards compatibility for existing wiki entries:** The gate runs on new candidates only. Existing wiki entries are not re-evaluated.
- **Backwards compatibility for consumers reasoning about gate behavior:** With v1 default `native: false` and no auto-emission, the gate's behavioral envelope is identical to 7.3.x. The contract gains a new optional clause; it does not change the existing behavior surface.
- **When activation is enabled (future bead):** That bead is responsible for its own semver classification. If auto-emission criteria are added in a way that changes gate yield, that bead's M21 bump is the right place to argue major.

**Conclusion:** 7.4.0 is correct at v1 under project CLAUDE.md rules because v1 is purely additive in its observable behavior. The schema lock-in (the new field) is minor-bump-worthy; the gate clause is inert at v1 and therefore not breaking. The future activation bead bears the semver re-evaluation if it ever moves yield.

### Changelog entry

Append to changelog at top of file (after the 7.3.1 entry, before older entries):

```markdown
- 7.4.0 (2026-06-10): Added `activation_profile` to accretion_candidate metadata
  (trigger, decidability, miss_cost, native, path_globs). Added `native: true`
  as a third gate clause alongside novelty + reuse value. v1 ships native in
  deferred-activation mode: default false, no auto-emission, human-review only —
  so the v1 gate envelope is unchanged. Added step_2c_activation_profile
  (assignment) and step_3c_profile_cross_validate (scope cross-cut) to the
  claude_code_runtime filing protocol. Profile is substrate-agnostic; downstream
  dispatchers consume it. See docs/planning/2026-06-10_module-21-activation-profile-spec.md.
```

---

## 6. Downstream consumers (who reads the new field)

**Decision tag:** reckoning. Confidence: **high** for known consumers, **medium** for forward references.

| Consumer | Module | What it reads | Status |
|---|---|---|---|
| Downstream dispatcher (MemoryRouter, etc.) | M21 Dispatcher Boundary (line 936) | `trigger`, `decidability`, `miss_cost` for tier selection | Existing seam, no edit needed |
| cc rules emitter (Phase 2 of this work) | `platform-bindings/claude-code.yaml` + `compiler/kf-compile.py` | `trigger: path_bound` + `path_globs` → `.claude/rules/*.md` with `paths:` frontmatter | Future bead |
| cc hook emitter (Phase 2 of this work) | same as above | `decidability: true` + `miss_cost: high` → `settings.json` hook fragment | Future bead |
| Module 22 (Semantic Wiki Search) | when `path_globs` reaches Phase 2 frontmatter filter | `path_globs` as a retrieval-time filter | Indirect, P4-deferred per `knowledgeforge-core-acu` |

---

## 7. Adjacent dependency — Module 19 (flagged, NOT absorbed)

**Decision tag:** evaluative (boundary call). Confidence: **high**.

This work touches the memory tier model. Per Module 19's four-tier scheme (Tier 0 / 1 / 2 / 3, lines 65–500):

- Auto-memory (`~/.claude/projects/<proj>/memory/MEMORY.md`) is **L1 scratch** in Claude Code's native model.
- KF wiki entries written by the M21 filing protocol are **Tier 0** persistent domain knowledge.
- `.claude/rules/` (target of Phase 2 emitter) is a NEW substrate that does not yet have a tier assignment in Module 19. It sits between auto-memory (Claude-authored, scratch) and wiki (KF-authored, consolidated).

**Reconciliation needed (out of scope for this bead, flag only):** Module 19 should add a tier-mapping note for `.claude/rules/` — likely as a *projection* of Tier 0 onto the cc substrate, not a new tier. The activation_profile's `trigger` field is the natural promotion signal between auto-memory (transient) and `.claude/rules/` (substrate-promoted).

**Action:** File a separate bead — "M19: reconcile four-tier model with .claude/rules/ substrate and auto-memory." Do NOT block Phase 1 or Phase 2 on it; the rule-emitter design works without the tier-model edit.

---

## 8. Adversarial probes (Critic prep — for the auto-Critic gate)

These are the failure modes the spec must survive review on:

| Probe | Response |
|---|---|
| **"`native: true` is a dispatch concern; suppression there leaks gate state."** | No — gate owns persistence eligibility (line 938). Dispatch owns physical-write decisions on persisted candidates. Suppression-before-persist is gate. |
| **"`miss_cost: high + decidability: true` collapses the hook tier into the rule tier; no real distinction."** | Rule tier loads guidance into context for Claude to interpret. Hook tier executes a shell command regardless of Claude's decision. Two failure modes: rule fails when Claude reads but doesn't follow; hook fails only if the shell command itself errors. The miss-cost ceiling for rules is "Claude ignored it." For hooks, "command didn't run." Different. |
| **"`trigger: task_bound` overlaps with `.claude/skills/` already-on-demand semantics."** | Yes — that overlap is intentional. `task_bound` candidates dispatch to skills (Phase 2), not rules. The profile distinguishes them at the gate; the emitter routes them. |
| **"`path_globs` provenance gap (Section 4) leaves `trigger: path_bound` underspecified."** | Acknowledged. Defaults route to `invariant` or `task_bound` when no glob source is available. Path-bound is an explicit override that requires either ERA emission or producer-mode emission. Safe default behavior. |
| **"Three-condition gate breaks existing accretion_calibration yields (M21:230, 'tighten novelty')."** | Calibration counts suppression events (native-fail) as part of yield denominator alongside novelty-fail and grounding-fail. Yield ratio definitions in M21 stay; numerator unchanged; denominator gains a new failure mode. Note this in the 7.4.0 changelog under calibration. |
| **"What if a future model becomes 'native' at something currently persisted? The KB rots."** | The linter health check (M21:477, `Knowledge Base Linter`) re-evaluates entries against `native` periodically. Add a linter rule: any entry whose original `activation_profile.native: false` claim is now `native: true` is flagged for archival. Tracked in the follow-up M19/linter reconciliation bead. |

---

## 9. What this spec does NOT change

Stated explicitly to prevent scope creep on review:

- **Does not touch persist / don't-persist logic** — the two-condition test is extended to three (native added), not redefined. The gate stays gate.
- **Does not touch Module 23 taxonomy validation** (step_4a).
- **Does not touch Module 22 (Semantic Wiki Search)** — `path_globs` is consumed by future Phase 2 frontmatter filter (bead `acu`), not by Phase 1 retrieval.
- **Does not specify cc emitters** — that is Phase 2, a separate bead with its own spec.
- **Does not touch knowledgeforge-cw** — explicitly out of scope per handoff constraint #5.
- **Does not specify the entity→path resolver** — deferred to a follow-up bead per Section 4.

---

## 10. Confidence summary (revised after Critic pass)

| Component | Confidence | Why |
|---|---|---|
| Field shape (`trigger`, `decidability`, `miss_cost`, `native`, `path_globs`) | **High** | Substrate-grounded; Dispatcher Boundary compatible; substrate-agnostic per handoff constraint |
| `native` as gate clause (not dispatch) | **High** | Symmetric with novelty/reuse-value; persistence-eligibility belongs to gate |
| `native` v1 deferred-activation (Section 2) | **High** | Resolves circularity in Critic finding [3]; preserves backwards compatibility; gate envelope unchanged at v1 |
| Computation site (step_2c assignment + step_3c cross-validate) | **High** | Resolves Critic finding [1] step-ordering issue; no lookahead; linear |
| `path_globs` provenance — Option A (defer resolver) | **Medium** | Pragmatic; acknowledged gap; expected-distribution table per Critic finding [2] |
| CC Doc patch text (Section 1b) | **High** | Resolves Critic finding [4]; explicit patch text now in spec |
| M21 changelog + version bump (7.4.0) | **High** | Resolves Critic finding [5] with explicit backwards-compatibility defense |
| Section 11 framing as "post-approval only" | **High** | Resolves Critic finding [6]; SPEC/IMPL boundary now explicit |
| M19 tier-model dependency flagged, not absorbed | **High** | Phase 1/2 do not require the reconciliation; clean separation |
| Adversarial probe responses (Section 8 + Critic-r2 findings absorbed) | **High** | Six in-spec probes + six Critic findings absorbed; spec is hardened |

---

## 11. Post-approval implementation sequence — DO NOT EXECUTE during spec review

**Resolves Critic finding [6].** Section 11 was previously titled "Stop here" but contained imperative steps including a compiler invocation. The compiler invocation IS an implementation action. The clarified framing below makes the SPEC vs IMPL boundary explicit.

This is the Phase 1 deliverable. **No M21 edit, no compiler run, no kf.yaml bump until human gate approval at the bottom of this document.**

The steps below describe what an implementation pass will look like AFTER approval. They are documentation of intent, not instructions to the reviewer. A reviewer who runs them is performing the implementation.

### Steps that an approved implementation pass will execute

1. **Edit M21:** Apply Section 1 schema patch to `modules/21_knowledge_accretion.md` at the insertion point in Section 1 (after line 331).
2. **Edit M21:** Apply Section 1b CC Doc patch to the CC Doc section of `modules/21_knowledge_accretion.md` (~line 1056 region; full patch text is in Section 1b).
3. **Edit M21:** Apply Section 2 gate clause to the two-condition test in BOTH the main-body conceptual section AND the CC Doc verbatim block.
4. **Edit M21:** Apply Section 3 step_2c + step_3c additions to the `claude_code_runtime.filing` block (line 347).
5. **Edit M21:** Apply Section 5 changelog entry to the top of the file.
6. **Edit kf.yaml:** Bump system version to 7.4.0; add corresponding changelog entry.
7. **Verify compilation (post-edit verification, not spec review):** After all edits land, run:
   ```
   python3 compiler/kf-compile.py --target claude-code --output ~/Scripts/knowledgeforge-cc --dry-run
   ```
   Expected: CC Doc section regenerates with the three-condition test text and the `activation_profile` block visible in the compiled output. Failure modes to watch: section markers misplaced, YAML indentation drift, anchor changes.
8. **Open Phase 2 bead:** "Phase 2 — cc rules + hook emitter spec (consumes M21 activation_profile from y4b)." Carry forward the Section 4 trigger-distribution note.
9. **Open follow-up beads:**
   - "M25: entity→path-glob resolver for ERA output (feeds M21 path_globs)." P3, blocked-by y4b.
   - "M21: define native auto-evaluation criteria + calibration cycle." P3, blocked-by y4b.
   - "M19: reconcile four-tier model with .claude/rules/ substrate and auto-memory." P4, independent.

### Implementation-pass commit message template (use when approved)

```
feat(module-21): add activation_profile to accretion candidate metadata (7.4.0)

Adds trigger/decidability/miss_cost/native/path_globs to candidate metadata.
Adds native:true as a third gate clause alongside novelty + reuse value.
v1 ships native in deferred-activation mode (default false, no auto-emission)
so the v1 gate envelope is unchanged. Adds step_2c (assignment) and step_3c
(scope cross-validation) to the claude_code_runtime filing protocol.

Spec: docs/planning/2026-06-10_module-21-activation-profile-spec.md
Bead: knowledgeforge-core-y4b
```

---

## HUMAN GATE — Phase 1 approval

**This is where the chain stops.** Reviewer options:

- **Approve as-revised** → proceed to implementation pass (Section 11 above) and Phase 2 spec bead
- **Approve with conditions** → state conditions; revise in-doc; re-gate
- **Reject** → state reason; revise or abandon

Until one of these is recorded, no implementation occurs.
