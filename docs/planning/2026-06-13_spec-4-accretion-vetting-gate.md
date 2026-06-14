# SPEC 4 — Accretion vetting gate + Contract B + librarian promotion

**Status:** LOCKED (Phase 2 spec-commit complete, human-approved 2026-06-13)
**Date:** 2026-06-13
**Driver bead:** `knowledgeforge-core-f8a`
**Phase chain:** Probe → ERA → Strategist → Builder → Critic (1 revision cycle) → spec-commit
**Decision type:** novel (no precedent for provenance-derived vetting in KF)
**Risk tier (Module 20):** MEDIUM base; HIGH on cross-cutting (`~/.claude/wiki/`) decision path
**Reversibility:** gate-level revert restores pre-SPEC-4 step ordering; un-tagging unvetted entries is mechanical
**Phase 3 implementation:** gated separately

---

## Cross-spec dependencies

- **SPEC 1** (this session): SPEC 1 owns adversarial-critic promotion only. SPEC 4 owns librarian promotion independently and fully. Each spec deletes only its own `static_agents` entry.
- **Module 20** (new sub-policy required): accretion-candidate-tier policy — novel/predictive accretion candidates inherit HIGH tier and require human confirmation via `surface_for_human_review`. Cross-references the SPEC 1 `verifier_tool_tier_policy` work.
- **Module 03** (registry growth): Contract B entry added; registry count becomes 10 (post-SPEC-1 merge brings it to 9; SPEC 4 adds the 10th).
- **MemPalace integration** unchanged — gate sits between step_3c (profile cross-validate) and step_4a (taxonomy), upstream of mempalace-wiki-mine hook.

---

## Purpose

Stop accretion candidates derived from novel/predictive decisions from auto-filing into the cross-cutting wiki (`~/.claude/wiki/`) without an explicit vetting signal. Auto-accretion is an unsupervised knowledge loop — comprehension debt at the wiki layer. SPEC 4 inserts a provenance-aware gate at Module 21 `step_3d` BETWEEN scope classification and taxonomy validation. The gate consumes Contract B provenance ([project]-emitted), enforces a tier-boundary rule with explicit human-review surfacing for HIGH-tier risk, and decouples cleanly from the librarian agent (ERA Adversarial finding [3]).

---

## Design

### D1. Gate placement — Module 21 `step_3d_provenance_gate`

Insert between `step_3c_profile_cross_validate` and `step_4a_taxonomy_gate` (currently at `modules/21:552-580` and `modules/21:568-580`):

```yaml
step_3d_provenance_gate:
  # NEW SPEC 4. Runs after scope is known (step_3) and profile cross-cuts validated (step_3c),
  # before taxonomy gating (step_4a).
  description: |
    Cross-cutting wiki entries (~/.claude/wiki/) derived from novel or predictive
    decisions require an external vetting signal — separate-verifier sign-off OR
    human review. Project-scoped wiki entries ({project_root}/wiki/) derived from
    novel or predictive decisions also surface for human review before filing.
    Reckoning/evaluative candidates pass through unchanged.
  inputs:
    - provenance (per Contract B): {loop_id, run_id, decision_tag, source_mode, signals[]}
  gates:
    cross_cutting_novel_or_predictive:
      condition: |
        scope == global AND decision_tag ∈ {novel_judgment, predictive_judgment}
      require: |
        verifier_signoff OR human_review_signal in provenance.signals[]
      on_fail: surface_for_human_review
      log_to: compile_log_format with reason "cross_cutting_unvetted_surfaced"
    project_novel_or_predictive:
      condition: |
        scope == project AND decision_tag ∈ {novel_judgment, predictive_judgment}
      action: surface_for_human_review
      rationale: |
        Module 13 → Module 20 maps novel/predictive to HIGH risk tier. The
        `unvetted` tag is an annotation, not a checkpoint. Auto-file with
        annotation silently bypasses Module 20's HIGH-tier human-confirmation
        requirement. Surfacing for human review preserves the audit trail.
      log_to: compile_log_format with reason "project_unvetted_surfaced"
    cross_cutting_reckoning_or_evaluative:
      condition: |
        scope == global AND decision_tag ∈ {reckoning, evaluative_judgment}
      action: proceed (existing path)
    project_reckoning_or_evaluative:
      condition: |
        scope == project AND decision_tag ∈ {reckoning, evaluative_judgment}
      action: proceed (existing path)
  provenance_completeness_check:
    condition: |
      provenance missing OR provenance.decision_tag absent
    action: |
      surface_for_human_review with provenance_missing: true; user decides
      file destination (project unvetted | cross-cutting with override | discard)
    log_to: compile_log_format with reason "incomplete_provenance"
  surface_for_human_review_protocol:
    show_to_user:
      - candidate body (full)
      - provenance summary (loop_id, run_id, decision_tag, source_mode, signals)
      - proposed scope (global | project)
      - reason for surfacing
    user_options:
      - file_to_project (with `unvetted: true` frontmatter)
      - file_to_global_with_override (Module 20 HIGH-tier confirmation logged)
      - discard
  next: step_4a_taxonomy_gate
```

- **Decision type:** novel — new gate semantics with no precedent in Module 21.
- **Confidence:** 0.75 on the surface-vs-auto-tag balance; quantitative impact on accretion velocity is unknown and calibrated post-deployment.

### D2. Schema additions to `accretion_candidate` — provenance sub-object

`accretion_candidate` schema at `modules/21:354-461` gains:

```yaml
provenance:
  loop_id: string         # required when emitted by [project]; null when direct orchestrator
  run_id: string          # required when emitted by [project]; null when direct orchestrator
  decision_tag: string    # required; enum [reckoning, evaluative_judgment, predictive_judgment, novel_judgment]
  source_mode: string     # required; moved from top-level
  signals: array          # optional; entries: {type: verifier_signoff, ref: <pointer>}
                          #                    {type: human_review_signal, ref: <pointer>}
```

`source_mode` MOVES from top-level into `provenance.source_mode`. This is a breaking schema change on the top-level field.

- **Decision type:** evaluative — additive plus one breaking move.
- **Reversibility:** reversible by restoring `source_mode` to top level and demoting `provenance` to optional.
- **Confidence:** 0.85.

### D2b. Schema transition — accessor shim + grandfather rule

Top-level `source_mode` consumers MUST use the accessor shim during transition:

```
source_mode = candidate.provenance?.source_mode ?? candidate.source_mode
```

Affected sites within Module 21 (must be updated in Phase 3 implementation):
- `step_2c_activation_profile.compute.trigger` lookup table (`modules/21:482-490`) — trigger inference keyed on source_mode
- `default_importance.source_mode_boost` (`modules/21:377-378`) — Expert/Strategist +1 boost
- `compile_log_format` (`modules/21:629`) — `Source: [mode]` string interpolation

**Grandfather rule:** Wiki entries with top-level `source_mode` (not nested) AND `created < 2026-07-01` (or one month past SPEC 4 merge — actual cutover confirmed at merge time) are exempt from the gate's provenance completeness check. Critic linter raises Sev 3 finding "schema migration pending — provenance fields absent" but does not block.

**Sunset:** 90 days after cutover, the shim fallback path (`?? candidate.source_mode`) is removed; entries failing the new schema are rejected.

- **Decision type:** evaluative.
- **Confidence:** 0.85.

### D3. Contract B registry entry — Module 03

Add to `modules/03_coordination_patterns.md` `handoff_contract_registry`:

```yaml
- id: hc-runtime-to-accretion-gate
  source_mode: [project]_runtime
  source_variant: null
  target_mode: accretion_gate          # Module 21 step_3d
  target_variant: null
  trigger:
    type: automatic
    condition: "Loop run completes AND produces accretion candidate at evaluative+ depth"
    chain_pattern_reference: "runtime-accretion-emission"
  payload_schema:
    fields:
      - {name: candidate_body, type: object, required: true,
         description: "Per Module 21 accretion_candidate schema"}
      - {name: provenance, type: object, required: true}
      - {name: provenance.loop_id, type: string, required: true}
      - {name: provenance.run_id, type: string, required: true}
      - {name: provenance.decision_tag, type: string, required: true,
         validation: "enum: [reckoning, evaluative_judgment, predictive_judgment, novel_judgment]"}
      - {name: provenance.source_mode, type: string, required: true}
      - {name: provenance.signals, type: array, required: false}
  fallback_path:
    type: surface_for_human_review
    rationale: "Incomplete provenance → user decides destination. Never silent-promote
                to cross-cutting tier. Never silent-file to project tier when decision
                type is novel/predictive."
  validation_checks:
    - check_id: provenance_present
      assertion: "provenance is non-null AND provenance.decision_tag is non-null"
      check_type: deterministic
      failure_action: surface_for_human_review
      failure_severity: Sev1
    - check_id: provenance_decision_tag_enum
      assertion: "provenance.decision_tag matches enum"
      check_type: deterministic
      failure_action: surface_for_human_review
      failure_severity: Sev1
    - check_id: candidate_body_schema_conforms
      assertion: "candidate_body validates against Module 21 accretion_candidate schema"
      check_type: deterministic
      failure_action: surface_for_human_review
      failure_severity: Sev2
```

Registry entry count becomes 10 after both SPEC 1 (+1, to 9) and SPEC 4 (+1, to 10) merge. Module 03 changelog records both additions.

- **Decision type:** evaluative.
- **Confidence:** 0.85.

### D4. Librarian promotion — fully owned by SPEC 4

SPEC 4 owns librarian promotion atomically:

- `modules/21_knowledge_accretion.md` gains `## CC Agent (Knowledge Librarian)` section with current `cc/.claude/agents/knowledge-librarian.md` body byte-for-byte. **No clause additions** — librarian does not consume artifact bodies adversarially, so no untrusted-input clause needed.
- `platform-bindings/claude-code.yaml` — add module 21 output:
  ```yaml
  21:
    outputs:
      - type: doc
        path: ".claude/docs/knowledgeforge/21_knowledge_accretion.md"
        section: "CC Doc"
      - type: agent                                  # NEW
        path: ".claude/agents/knowledge-librarian.md"
        section: "CC Agent (Knowledge Librarian)"
  ```
- Delete `static_agents` entry for knowledge-librarian.

**Ownership boundary:** post-merge, `modules/21_knowledge_accretion.md` is canonical; `cc/.claude/agents/knowledge-librarian.md` is compile-output. `--check-divergence` is the tie-breaker for future hand-edit drift. SPEC 1 owns adversarial-critic only; SPEC 4 owns librarian only. No cross-spec piggyback.

Librarian's existing Step 1-4 protocol is unchanged. SPEC 4 gate logic at Module 21 step_3d fires upstream of librarian invocation; librarian trusts upstream gating.

- **Decision type:** evaluative.
- **Confidence:** 0.85.

### D5. `unvetted` tag lifecycle

Entries filed with `unvetted: true` (post-`surface_for_human_review` with `file_to_project` selection):

- Appear in `compile.md` log with reason flagged
- Skipped by Critic linter contradiction-detection unless invoked with `--include-unvetted`
- May be promoted to vetted by human review + explicit frontmatter flip
- Stale unvetted entries (age > 60 days, no promotion) surface as Critic linter Sev 3 finding: "Unvetted entry past review window — promote or archive."

- **Decision type:** evaluative.
- **Confidence:** 0.7. Threshold 60d is heuristic; may need calibration.

---

## Implementation (Phase 3 — out of scope)

### Pre-flight inventory

All of the following must land in the same squash-merge PR:

- [ ] `modules/21_knowledge_accretion.md`:
  - Insert `step_3d_provenance_gate` between step_3c and step_4a
  - Add `provenance` sub-object to `accretion_candidate` schema (D2)
  - Update `step_2c`, `default_importance`, `compile_log_format` to use accessor shim (D2b)
  - Add `## CC Agent (Knowledge Librarian)` section with current body byte-for-byte (D4)
  - Update CC Doc section to reflect new gate
- [ ] `modules/03_coordination_patterns.md` gains `hc-runtime-to-accretion-gate` entry; registry validation comment updates to 10 entries (post-SPEC-1 merge).
- [ ] `platform-bindings/claude-code.yaml` — append librarian agent emission under module 21; delete `static_agents` entry for knowledge-librarian only.
- [ ] Module 21 changelog records:
  - step_3d_provenance_gate addition
  - provenance sub-object addition + shim transition + grandfather window
  - librarian section addition

### Verification gate

**(a) Gate firing test (manual):** Submit candidate with `decision_tag: novel_judgment` + `scope: global` + no `signals[]` → step_3d surfaces for human review with correct context. Repeat for all four (decision × scope) combinations; assert correct routing per D1 table.

**(b) Manifest-presence assertion:** `kf-compile --target claude-code --dry-run` manifest contains entry with:
```
output:  ".claude/agents/knowledge-librarian.md"
source:  "21_knowledge_accretion.md"
section: "CC Agent (Knowledge Librarian)"
status:  "would_write"
```
CI fails if absent.

**(c) Divergence assertion:** `kf-compile --target claude-code --check-divergence` reports zero divergences post-merge (librarian body is byte-identical to current cc copy by D4 design).

---

## Assessment (testability)

| Test | Pass criterion |
|---|---|
| Gate routes novel + global | Submit candidate → `surface_for_human_review` triggered; log entry with reason `cross_cutting_unvetted_surfaced` |
| Gate routes evaluative + global | Submit candidate → passes gate; proceeds to step_4a |
| Gate handles missing provenance | Submit candidate without provenance → `surface_for_human_review` with `provenance_missing: true` |
| Accessor shim works on legacy entries | Read pre-cutover entry with top-level `source_mode` → shim returns correct value |
| Grandfather rule | Entry with `created < 2026-07-01` and missing provenance → Sev 3 linter finding, not Sev 1+ block |
| Librarian byte-equality | `diff cc/.claude/agents/knowledge-librarian.md <(extract Module 21 CC Agent Knowledge Librarian section)` → zero output |
| Registry growth | `modules/03` registry has 10 unique IDs post-merge |

---

## Adversarial findings resolution (Phase 2 revision cycle 1)

| Critic finding | Resolution |
|---|---|
| Sev-1 [1] Dual-source librarian ownership ambiguity | D4 explicit ownership boundary: SPEC 4 owns librarian only; SPEC 1 owns adversarial-critic only; no piggyback; canonical = core, derived = cc |
| Sev-2 [2] provenance breaking schema, no migration | D2b accessor shim + grandfather rule + 90-day sunset window |
| Sev-2 [3] Reject-to-project bypasses Module 20 HIGH-tier confirmation | D1 fallback changed: `surface_for_human_review` (not auto-file). All novel/predictive paths route through human review checkpoint, regardless of scope. Contract B fallback_path updated to match. |

No findings persisting after revision cycle 1. Loop exit: `findings_resolved_on_revision`.

---

## Revision history

- 2026-06-13: SPEC 4 v1 drafted by Builder (decision_type_exercised=novel_judgment).
- 2026-06-13: Adversarial pass returned 3 Sev-2+ findings (1 CRITICAL, 2 HIGH).
- 2026-06-13: Revision cycle 1 — Patches 4A/4B/4C applied; all findings resolved.
- 2026-06-13: Human approval at Phase 2 spec-commit gate. Locked.
