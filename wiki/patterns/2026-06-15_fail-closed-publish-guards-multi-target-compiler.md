---
title: Fail-closed publish guards for multi-target compilers — invariants enforced at emit-time
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-15
domain: patterns
topic: compiler-hardening
tags: compiler, multi-target-publish, invariant-checking, fail-closed-design
related_entries:
  - compiler/2026-06-10_extract-section-cc-marker-stop-condition-over-extraction.md
  - methodologies/2026-05-14_structural-invariant-acceptance-over-wall-clock-stubbed-paths.md
  - patterns/2026-05-12_pin-tests-declarative-policy-manifests.md
  - patterns/2026-05-12_fastapi-streaming-preflight-gates.md
---

# Fail-Closed Publish Guards for Multi-Target Compilers

## The Pattern

When one canonical source compiles to multiple target artifacts (different repos, different shapes), the compiler's STRIP/EXTRACT logic is the only thing keeping target-A content out of target-B output. Strip filters are silent on failure — if the filter misses a new section variant, that content leaks. Add **post-emit fail-closed guards** that scan the on-disk output for the leak's signature and raise an exception naming the offending file + line. The guard is a backstop for the strip filter, not a replacement: it makes silent leaks impossible without the publish step rejecting itself.

## When This Applies

- A compiler/publisher has multiple targets sharing one source.
- Section-based extraction or stripping is used to differentiate targets.
- Leak between targets has been observed historically OR is plausible from the filter's structure.
- The compiler runs unattended (e.g., bot-triggered PRs) and silent failure modes are unacceptable.
- You have an invariant per target that can be expressed as a deterministic post-write check.

## When This Does NOT Apply

- Single-target publish — no cross-target leak surface.
- Target outputs are byte-identical and shared content is intentional.
- The invariants are evaluative (require human judgment) rather than deterministic.
- You have no concrete failure mode worth guarding against (premature hardening).

## Pattern Shape

1. **Enumerate forbidden content for each target.** For -CP it's compilation-section headings; for -CC it's the set of routable agent bodies minus self+utility specials.
2. **Implement an `assert_<target>_<property>()` function** that takes the output path + content (or directory) and raises:
   ```python
   RuntimeError(
       f"[publisher][-X guard] FORBIDDEN ... in {file} at line {n}: '{text}'. "
       f"Fix Y before re-publishing."
   )
   ```
   on violation.
3. **Wire each guard into the target's compile entrypoint at the moment of write** — per-file for content guards; once at end-of-run for cross-file invariants like body-set bijection.
4. **Run guards on real writes only** — skip on dry-run/diff-mode where there's nothing on disk to inspect.
5. **The error message must name the artifact AND the fix surface** (which filter, which spec) so the operator can act without re-deriving the diagnosis.

## Worked Instance — KF Compiler (core@c143865, 2026-06-15)

KF's `strip_cc_sections()` removes `## CC Skill / Doc / Agent / Rules` from -CP output. A historical session had leaked CC sections into -CP — the strip filter was target-agnostic, originally shared with the deprecated -CW target. After making the filter per-target, two guards were added:

### -CP guard: `assert_cp_clean(out_path, content)`

Scans each emitted -CP file for any forbidden heading (including titled variants like `CC Agent (Adversarial Variant)` and `CC Skill — KF Fit Check`) and raises `RuntimeError` naming the file + line. Wired into `compile_claude_projects()` after each file's `strip_cc_sections()` call. Verified PASS: 0 forbidden markers across 30 -CP files.

### -CC guard: `assert_cc_invariants(binding, output_root)`

Enforces three deterministic invariants at end-of-run:

(a) Every declared agent output in `module_outputs` produced `.claude/agents/<name>.md`.

(b) `adversarial-critic.md` contains the literal string `Untrusted Input Boundary` (the SPEC-1 prompt-level defense clause).

(c) The set of `@delegate` tokens parsed from M00's body equals the set of agent bodies on disk minus a frozen `CC_NON_ROUTABLE_AGENTS = {kf, knowledge-librarian}` (self + utility).

Each violation raises a named error. Wired into `compile_claude_code()` post-write; skipped on dry-run/diff-mode.

## Why This Is Reusable

The specific invariants are domain-specific; the pattern is not. Any multi-target compiler can encode "what must NOT appear in output X" as a regex/scan and "what bijections must hold among artifacts" as a set comparison. The guards' error messages double as the operator's runbook on miss — they name both the symptom and the fix surface, which is what makes them load-bearing rather than ornamental.

## Counterpoint — When to Skip

Don't add a guard for an invariant that hasn't been violated AND has no concrete mechanism to fail. KF's `Section-Load Map` heading is currently always inside CC blocks; adding it to the `CP_STRIP_MARKERS` frozenset was justifiable defense-in-depth (cheap text-match), but a guard would have been overkill since there's no failure mode to detect. The B3 guard exists because the -CW shared-path leak was real history; the C3 guard exists because the prior pass's `## CC Agent` orphan-vs-delegate mismatch was a near-miss.

## Trade-Offs

### Benefit
Silent leak becomes loud, named, and actionable. The publish step rejects itself on violation, so unattended runs can't push broken artifacts. Cost is one regex scan + one set comparison per target — negligible vs. the cost of a downstream consumer discovering the leak.

### Risk
A guard that doesn't keep pace with new content variants becomes stale and produces false confidence. The `CP_STRIP_MARKERS` frozenset and `CC_NON_ROUTABLE_AGENTS` set are governance surfaces — they must be revisited whenever a new section type or special-case agent is introduced.

### Mitigation
Pair guards with the originating filter so they live in the same file/module — when someone touches the filter, the guard is next to it. Frozen sets get explicit comments naming the justification for each member.

## Relationship to Adjacent Patterns

- `compiler/2026-06-10_extract-section-cc-marker-stop-condition-over-extraction.md` — documents the precise bug the guards exist to backstop. The guards are the deterministic ceiling for the silent-over-extraction failure mode.
- `methodologies/2026-05-14_structural-invariant-acceptance-over-wall-clock-stubbed-paths.md` — same family of reasoning (express the invariant deterministically, verify in CI), applied to acceptance testing rather than publish gating.
- `patterns/2026-05-12_pin-tests-declarative-policy-manifests.md` — pin-tests guard a manifest against accidental entry deletion; publish guards guard a target output against accidental entry inclusion. Mirror images.
- `patterns/2026-05-12_fastapi-streaming-preflight-gates.md` — same principle of "raise before commit-point" applied to HTTP streaming. Headers-sent vs. bytes-written are both irreversible publish events.

## Source Context

Discovered during KF Core export-filter hardening session (2026-06-15, commit `c143865`). After a historical -CW shared-path leak and a near-miss `## CC Agent` orphan-vs-delegate mismatch, the strip filters were made per-target and post-emit guards were added to make silent leaks structurally impossible. The pattern generalizes to any compiler/publisher where one source produces multiple shapes and the differentiation logic is silent on failure.
