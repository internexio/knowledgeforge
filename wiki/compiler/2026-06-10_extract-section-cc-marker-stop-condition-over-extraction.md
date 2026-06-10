---
title: extract_section() in kf-compile.py stops only at CC markers — non-CC headings cause silent over-extraction
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.92
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-10
domain: infrastructure
topic: ci-cd
tags: compiler, accretion, quality-gate, empirical
related_entries: []
---

# extract_section() CC Marker Detection Bug: Silent Over-Extraction on Non-CC Headings

## What

The `compiler/kf-compile.py` function `extract_section(content, section_name)` (lines 70–90) detects section boundaries using a stop condition that fires ONLY when the next `##` heading matches one of the CC marker types:

```python
CC_SECTION_MARKERS = frozenset({"CC Skill", "CC Doc", "CC Agent", "CC Rules"})
```

The stop logic (lines 79–80) checks:
1. Does the next `##` heading exactly match a marker name?
2. OR does it start with a marker name followed by a space (titled variant)?

**Consequence:** Any `##` heading that does NOT match a CC marker is INVISIBLE to the stop condition. Extraction continues past that heading and runs until either (a) a CC marker is found later in the file, or (b) end-of-file.

## Symptom

When a module has `cc_rules` sections followed by non-CC `##` headings (e.g., `## Notes`, `## Footnotes`), the compiler silently extracts the rule body PLUS all text under the non-CC heading.

Example failure mode:
```markdown
## CC Rules — Debugger Wiki Conventions
[rule body content]

## Notes
[notes section content]
```

Result: `extract_section("CC Rules — Debugger Wiki Conventions")` returns the rule body concatenated with the entire Notes section.

## When This Applies

- Adding new cc_rules sections at the bottom of modules without ensuring they cluster with other CC markers
- Test fixtures that author cc_rules sections followed by non-CC heading sections
- Module authors who insert new `## Footnotes`, `## See Also`, or `## Further Reading` sections between CC blocks

## When This Does NOT Apply

- Sub-headings (`###`, `####`) inside the section body — those are not level-2 headings and don't trigger the stop condition (correctly handled)
- Code-fenced blocks inside the body — those are not treated as section starts

## Root Cause

The stop condition is too narrow. It only recognizes CC marker headings as boundaries. Any `##` heading outside that marker set is passed through.

```python
# Current logic (lines 79–80):
if line.startswith("## ") and any(marker in line for marker in CC_SECTION_MARKERS):
    # This fires only for CC markers.
    # Non-CC headings like "## Notes" pass through silently.
    break
```

## Empirical Grounding

**Context:** KnowledgeForge Phase 2, bead `knowledgeforge-core-261`, test-fixture construction for cc_rules emitters (2026-06-10).

**Setup:** First revision of `tests/fixtures/cc_hooks_smoke_module.md` had:
```markdown
## CC Rules — Debugger Wiki Conventions
[detailed rule body with multiple paragraphs]

## Notes
[supplementary notes about the rules]
```

**Expected:** `extract_section()` extracts the rule body only.

**Actual:** Returned rule body + entire Notes section concatenated.

**Detection:** Critic adversarial review (Module 15) flagged the missing boundary check in the spec. The empirical manifestation surfaced during fixture construction — the extracted content length exceeded expectations, and the full Notes section appeared in the parsed rule body.

**Root cause confirmation:** Lines 79–80 of `compiler/kf-compile.py` check for CC markers only. No fallback to generic `##` boundary recognition.

## Documented Convention

Per `platform-bindings/claude-code.yaml` under `special_outputs.cc_rules.section_naming_convention`:

> cc_rules sections (`## CC Rules — X`) must cluster at the bottom of the module with other CC markers (`## CC Skill`, `## CC Doc`, `## CC Agent`, `## CC Rules — Y`) and have NO intervening non-CC `##` headings.

This convention is a workaround for the narrow stop condition. It prevents over-extraction by requiring CC sections to be contiguous.

## Fix Paths

| Option | Approach | Cost | When |
|--------|----------|------|------|
| **Enforce convention** (current) | Document that CC sections must cluster at file end with no intervening `##` headings | None (documentation only) | While cc_rules usage is rare; acceptable short-term |
| **Extend marker set** | Add any new marker types to `CC_SECTION_MARKERS` as they're introduced | Low (additive) | Each new CC output type |
| **Generic boundary detection** | Add a fallback: if line starts with `##`, stop (regardless of marker match) | Medium (refactoring) | Eliminates convention burden; cleaner long-term |
| **extract_section_strict variant** | Create a strict variant that stops at ANY `##` heading, use it for cc_rules only | Medium (new function) | Cleanest long-term; allows flexible extraction elsewhere |

**Current status:** Convention-based (Option 1). No active issue filed; the convention is sufficient while cc_rules entries remain rare.

## Prevention

- **Module authors:** Ensure all CC marker sections (`## CC Skill`, `## CC Doc`, `## CC Agent`, `## CC Rules`) cluster together at the file end with no intervening non-CC `##` headings.
- **Fixture authors:** When creating test modules with cc_rules sections, verify the extracted content matches the intended rule body (no accidental trailing sections).
- **Compiler maintainers:** If new cc_rules variants are introduced, add their marker names to `CC_SECTION_MARKERS` in `kf-compile.py` line 50.

## Related Knowledge

- **Module 04 (Spec Templates):** Defines the cc_rules block format for module specs.
- **Module 22 (Semantic Wiki Search):** Consumes cc_rules content extracted by this function to populate the wiki index.
- **Platform binding (Claude Code):** Documents the section-naming convention in `platform-bindings/claude-code.yaml`.

---

## Source Context

Discovered during Phase 2 compiler implementation fixture construction (bead `knowledgeforge-core-261`, 2026-06-10). Critic adversarial review (Module 15 cross-check) caught the narrow stop condition in the extraction logic. The empirical manifestation appeared when the first cc_hooks smoke test fixture included a non-CC `## Notes` section after the `## CC Rules` block — the extracted content silently over-included the Notes section. Resolved by restructuring the fixture to cluster all CC sections at the end and documenting the naming convention in the claude-code platform binding.
