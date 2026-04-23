# ERA Pass: User Education Layer

**Date:** 2026-04-23
**Scope:** 00_User_Quickstart.md + Module 01 v6.6.3 (Loop Detection + Fit Check Skill)
**Module reference:** 25_entity_relationship_analysis.md

---

## Entity Extraction

| Entity Name | Type | Which Deliverable | Notes |
|-------------|------|-------------------|-------|
| KF Orchestrator | Actor | Quickstart, M01 Spec | Routes requests; implicit throughout |
| User (new/first-contact) | Actor | Quickstart, Fit-Check Spec | Primary audience for education layer |
| Navigator (Mode) | System | All three deliverables | Fires on ambiguity; excluded from fit-check ranking |
| Builder, Debugger, Critic, Strategist, Synthesizer, Expert, Calibrator, Coordinator | System | Quickstart, Fit-Check Spec | 8 routable modes; targets of fit-check ranking and quickstart tree |
| Module 06 Quick Reference | Artifact | Quickstart, Quickstart Spec | Cross-linked at quickstart end; must exist at stable path |
| Module 13 Decision Classification | System | M01 (KF-5 integration section) | Quickstart implicitly assumes stable routing vocabulary |
| Module 16 Operational Bounds (circuit breaker) | System | M01 Loop Detection | Loop Detection Step 4 explicitly defers to M16 on third fire |
| Module 19 Memory Architecture | System | M01 Loop Detection | Loop Detection explicitly rejects routing index — referenced as non-dependency |
| 00_User_Quickstart.md | Artifact | Quickstart Spec / Deliverable | Lives at repo root; not a module |
| modules/01_navigator.md | Artifact | All specs | Home module for Loop Detection + Fit-Check Skill |
| CC Skill (Navigator) | Artifact | M01 Loop Detection | Existing compiled skill at .claude/skills/kf/navigator.md |
| CC Skill — KF Fit Check | Artifact | Fit-Check Spec / Deliverable | New titled CC Skill section; target .claude/skills/kf/fit-check.md |
| CC Agent (Navigator) | Artifact | M01 Loop Detection | Compiled agent at .claude/agents/navigator.md |
| Compiler (kf-compile.py) | System | Fit-Check Spec | Extracts CC Skill sections; exact-match section name lookup |
| Platform Binding (claude-code.yaml) | Artifact | Fit-Check Spec (implicit) | Defines section: "CC Skill" for module 01 — exact-match lookup |
| Loop Detection State | State | M01 Loop Detection | Ephemeral in-session; inferred from conversation context, no index fields |
| Second-consecutive-fire condition | State | M01 Loop Detection | Activation predicate for hint behavior |
| Ozymandias Check | Concept | Quickstart | Decision-type upgrade rule for yes/no questions |
| Decision Tree (9 modes) | Artifact | Quickstart | One-screen routing reference; assumes stable mode set |
| Mode-trigger vocabulary | Concept | M01 Loop Detection, Quickstart | Vocabulary taught in phrasing examples and loop detection hint |
| KF-5 / Decision Classification integration | Concept | M01 (unchanged) | Tags reckoning/evaluative/predictive/novel on every routed request |

---

## Relationship Map

| Entity A | Relationship | Entity B | Deliverable | Notes |
|----------|-------------|----------|-------------|-------|
| Navigator | routes_to | Builder, Debugger, Critic, Strategist, Synthesizer, Expert, Calibrator, Coordinator | M01 / Quickstart | Core routing contract |
| Quickstart Decision Tree | produces | User routing expectation | Quickstart | User infers Navigator fires automatically from tree |
| Quickstart Decision Tree | depends_on | Module 13 vocabulary (reckoning/evaluative/novel) | Quickstart | Ozymandias Check uses M13 terms without naming M13; assumed stable |
| Quickstart Decision Tree | depends_on | Module 06 Quick Reference | Quickstart | Cross-link at doc end; M06 must be at modules/06_quick_reference.md |
| Loop Detection (Step 4) | modifies | Navigator CC Skill (Step numbering) | M01 Loop Detection | Renames Route from Step 4 to Step 5; inserts new Step 4 |
| Loop Detection (Step 4) | modifies | Navigator CC Agent (Step numbering + Rules) | M01 Loop Detection | Same renumbering; adds Rules line |
| Loop Detection (Step 4) | depends_on | Module 16 circuit breaker | M01 Loop Detection | Explicit: third consecutive fire defers to M16 |
| Loop Detection (Step 4) | conflicts_with (negated) | Module 19 routing index | M01 Loop Detection | Spec explicitly rejects M19 session state; no new fields |
| Loop Detection (Step 4) | monitors | Session conversation context | M01 Loop Detection | State tracking via prior turn inference |
| Fit-Check Skill | depends_on | modules/01_navigator.md (home module) | Fit-Check Spec | Authored as ## CC Skill — KF Fit Check in M01 |
| Fit-Check Skill | produces | Mode ranking (2-3 items) | Fit-Check Spec | Terminal output; no downstream mode invoked |
| Fit-Check Skill | conflicts_with | Navigator ambiguity detection trigger | Fit-Check Spec | Fit-check is NOT triggered by Navigator — user-initiated only |
| Fit-Check Skill | co_changes_with | Navigator CC Skill section | Fit-Check Spec | Both in 01_navigator.md; compiler changes to M01 skill extraction affect both |
| ## CC Skill — KF Fit Check (titled header) | conflicts_with | Compiler extract_section("CC Skill") | Fit-Check Spec | CRITICAL: exact-match check fails on titled variant; see Violation Checks |
| ## CC Skill (existing) | co_changes_with | ## CC Skill — KF Fit Check | M01 compiled | Both in same file; extractor bleeds from first into second if stop-detection misses titled header |
| Platform Binding module 01 | produces | section: "CC Skill" lookup | Platform Binding | Exact section name CC Skill; titled variant not registered |
| Ozymandias Check | depends_on | Module 13 (reckoning/evaluative/novel) | Quickstart | Implicit coupling; vocabulary used without attribution |
| Fit-Check Skill ranking table | depends_on | Stable mode set (8 routable modes) | Fit-Check Spec | New mode addition would silently leave ranking table incomplete |

---

## Graph Shape

**Shape:** Branching fan-out with two isolated sub-clusters and one conflict edge.

```
User Education Layer
+-- Quickstart [linear: User -> Decision Tree -> M06]
|     +-- implicit depends_on: M13 vocabulary (hidden edge)
+-- Loop Detection [linear: Step4 -> M16 deference, negated M19 edge]
|     +-- modifies: CC Skill step numbering, CC Agent step numbering
+-- Fit-Check Skill [branching: triggers -> 8 mode ranking signals]
      +-- CONFLICT EDGE: titled CC Skill header <-> compiler exact-match extractor
```

**Complexity:** LOW-MEDIUM for Quickstart and Loop Detection clusters. MEDIUM with one confirmed conflict edge on the Fit-Check / compiler interface.

Per Module 25: conflict edges present -> escalate one tier regardless of shape.

---

## Violation Checks

### Cardinality

**Finding C1 — Two CC Skill sections in one module file (Sev 2)**

Module 01 now contains two CC-Skill-level sections:
1. `## CC Skill` (existing Navigator skill, line 430)
2. `## CC Skill — KF Fit Check` (new fit-check skill, line 583)

The platform binding for module 01 registers one skill output with `section: "CC Skill"`. The `extract_section` function at compiler line 69 performs an exact string match:

```python
if stripped == f"## {section_name}":
```

Then stop-detection at line 74 checks:

```python
if line.startswith("## ") and line[3:].strip() in CC_SECTION_MARKERS:
```

where `CC_SECTION_MARKERS = frozenset({"CC Skill", "CC Doc", "CC Agent", "CC Rules"})`.

`"CC Skill — KF Fit Check"` is NOT in `CC_SECTION_MARKERS`.

**Effect 1 (bleed):** The existing `## CC Skill` extractor does not stop at `## CC Skill — KF Fit Check`. It consumes all fit-check content and includes it in `.claude/skills/kf/navigator.md`. The navigator skill file will be approximately 300 lines instead of 150, exceeding the `skill_token_budget: 2000` constraint in the platform binding.

**Effect 2 (missing output):** The fit-check skill is never extracted to `.claude/skills/kf/fit-check.md` because no binding entry with `section: "CC Skill — KF Fit Check"` exists. The spec target path is dead.

**Root cause:** The fit-check spec explicitly flags this as a dependency: "Compiler must extract `## CC Skill — KF Fit Check` and write it to `.claude/skills/kf/fit-check.md` — verify compiler skill-extraction regex handles titled CC Skill sections." This verification was deferred rather than resolved as a commit-blocking prerequisite.

**Required fix before next compile run (3 edits):**

1. `compiler/kf-compile.py` line 50: add `"CC Skill — KF Fit Check"` to `CC_SECTION_MARKERS`
2. `compiler/kf-compile.py` line 74: the updated frozenset will now match the full titled string correctly (the `in` check operates on the full string)
3. `platform-bindings/claude-code.yaml` module 01 outputs: add new binding entry:
   ```yaml
   - type: skill
     path: ".claude/skills/kf/fit-check.md"
     section: "CC Skill — KF Fit Check"
   ```

---

### Hidden Couplings

**Finding H1 — Quickstart implicit dependency on Module 13 vocabulary (Sev 1)**

The Ozymandias Check section uses "reckoning," "evaluative judgment," and "novel judgment" without naming Module 13 as the source. The quickstart spec lists no M13 dependency and explicitly excludes infrastructure modules. The coupling is read-only: quickstart reads M13 vocabulary, does not depend on M13 routing behavior. If M13 major-bumps and renames these categories, the Ozymandias Check language silently drifts.

Severity: Sev 1. M13 vocabulary has been stable across multiple versions. No immediate action. Flag as a review gate if M13 takes a major version bump.

**Finding H2 — Fit-check ranking table hidden dependency on stable mode set (Sev 1)**

The ranking signal table covers all 8 currently routable modes with no versioning pin on the mode set. If a new user-facing mode is added, the ranking table silently becomes incomplete — it will never surface the new mode.

Severity: Sev 1. Affects future correctness only. Document as a review gate: when a new user-facing mode is added, the fit-check ranking table must be updated.

---

### Contract Drift

**Finding D1 — Module 01 exposes two CC Skill sections; compilation contract covers one (Sev 2, same root as C1)**

The module compiled contract (as registered in the platform binding) is one skill output. The fit-check addition extends that to two outputs but the binding was not updated. Same defect as C1 viewed from the contract perspective. Fix is the same 3-edit patch.

**Finding D2 — Loop Detection does not drift the activation predicate (clean)**

The spec and delivered module are explicit: "Loop detection does not alter the primary activation predicate." The 6.6.1 SPEC-3 predicate is preserved verbatim. No contract drift on firing conditions.

**Finding D3 — Navigator agent contract unchanged (clean)**

The `agent.integration.sends_to` list and `agent.outputs` contract are unchanged. Loop Detection adds behavior within an existing step. Fit-Check is a separately invoked skill, not a Navigator output. No drift on the Navigator agent interface.

**Finding D4 — Module 06 step-count references: none found (clean)**

Search of `modules/06_quick_reference.md` found zero references to Navigator internal step numbers. Loop Detection renumbering does not break any Module 06 cross-reference.

---

### Interface Breakage

**Finding I1 — Fit-check skill will not compile to its target path (Sev 2)**

Same root as C1/D1. The next `kf-compile.py --target claude-code` run will:
- Produce an oversized `.claude/skills/kf/navigator.md` (fit-check content included via bleed)
- Produce NO `.claude/skills/kf/fit-check.md`
- Any wired `/kf-fit-check` command referencing the missing skill path will silently fail at load time

Blast radius is contained: no currently compiled variant depends on `fit-check.md` (it is a new file). No existing CC workflows break today. The breakage is prospective — the first compile run after this commit produces wrong output. Fix must land before that compile run.

---

## Routing Adjustment Required

Yes — confined to the compiler interface, not the module content.

ERA finding C1/D1/I1 is a conflict edge between the fit-check skill section header and the compiler section extraction logic. Per Module 25: conflict edges present -> escalate one tier regardless of shape.

The escalation applies to the compiler fix, not the content deliverables. The fix is a targeted Builder task (3 lines across 2 files). No Expert or Coordinator routing needed for the content itself.

Required actions are listed in Finding C1 above.

---

## ERA Verdict

**ESCALATED — Sev 2: Compiler interface breakage on titled CC Skill section**

Three deliverables are content-clean. One cross-cutting defect (C1/D1/I1) blocks correct compilation of the fit-check skill. The defect does not corrupt existing functionality but will produce wrong output on the next compile run.

**Sev 2 findings — action required before compile:**
- C1 / D1 / I1: `## CC Skill — KF Fit Check` section header not registered in `CC_SECTION_MARKERS` or the platform binding. Navigator skill bleeds into fit-check content; fit-check never produces its compiled output file. Fix: 3 targeted edits to `compiler/kf-compile.py` and `platform-bindings/claude-code.yaml`.

**Sev 1 findings — monitor, no immediate action:**
- H1: Quickstart implicit coupling to M13 vocabulary — read-only dependency, flag on M13 major bump
- H2: Fit-check ranking table has no mode-set version pin — flag as review gate when new user-facing modes are added

**Content verdict:** Quickstart decision tree, Loop Detection protocol, and Fit-Check skill behavior are internally consistent, correctly cross-referenced, and do not conflict with each other or with their stated module contracts. The education layer content is correct; its compilation pipeline needs one patch before the first compile run.
