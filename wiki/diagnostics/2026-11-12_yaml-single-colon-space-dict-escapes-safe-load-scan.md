---
title: Compiler warn-and-skip hides broken module metadata — a single colon-space item parses as a dict, so safe_load scans pass while the compiler stamps "unknown" versions and drops agent files
source_mode: direct
source_session: kf-completion-gate-metadata-yaml-2026-11-12
source_fingerprint: kf-module-metadata-yaml-folded-scalar-fix-2026-11-12
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-11-12
domain: diagnostics
topic: data-validation
tags: [empirical, quality-gate]
related_entries:
  - diagnostics/2026-06-14_yaml-plain-scalar-colon-space-safe-load-silent-fail.md
  - compiler/2026-06-10_extract-section-cc-marker-stop-condition-over-extraction.md
---

# Compiler Warn-and-Skip Hides Broken Module Metadata

This entry extends `diagnostics/2026-06-14_yaml-plain-scalar-colon-space-safe-load-silent-fail.md`. That entry covers the parse-error case (two or more `: ` in one plain scalar) and the all-modules `yaml.safe_load` scan. This entry adds three things it does not cover: a silent-parse case that the scan misses, the compiler-level symptom fingerprint, and a prevention rule for CI.

## Problem Shape

A compiler reads a YAML metadata block from each source module (here, a `## Module Metadata` fenced block in `modules/NN_*.md`). When that block fails to parse, the loader prints one warning line and falls back to defaults. The compile run succeeds. Output is produced for every target, but with wrong or missing content.

In the KnowledgeForge repo, `parse_module_metadata()` in `kf-compile.py` does this. On 2026-11-12, four of 31 modules (04, 07, 11, 26) had been unparseable for months, and no build failed. Symptoms were found only by accident while recompiling `platforms/`:

- The plugin-bundle target stamped `module_version=unknown` for the Critic and Calibrator, and `""` in `kf-plugin-bundle.json`.
- The plugin-bundle target silently omitted `agents/adversarial-critic.md`. The compile wrote 13 files. After the fix it wrote 14.
- Targets that copy metadata verbatim (Claude Projects, ChatGPT) looked fine, because the wrong values were never rendered from metadata into their output.

## Two Ways a Bad Item Breaks the Block

**Case A: parse error (loud at the YAML layer, silent at the compiler layer).** A changelog item contains two or more `: ` inside a plain scalar. Examples from the session:

```yaml
- capability_profiles: added grader (read: registration snapshot, ...)
- Gate: Wilson-CI class (deterministic). Stratify: rule-based ...
- Blocks: Step 3.5 (...) spanning a multi-line plain scalar
```

`yaml.safe_load` raises. The existing entry's scan catches this case.

**Case B: silent mis-parse (the case the existing scan misses).** A plain item contains exactly one `: ` and nothing else that trips the parser:

```yaml
changes:
  - Registry: added Contract F
  - Plain item with no colon
```

This parses without error. The first item becomes a one-key dict, `{"Registry": "added Contract F"}`, not a string. The `changes` list then mixes types (dict and string). A `safe_load` scan reports the file as clean. Any code that does `"\n".join(changes)` or renders items as text fails later, or renders the dict's repr.

## Why It Stays Hidden

1. The per-module scan uses `safe_load` only, so Case B passes it.
2. The loader's graceful fallback returns `{}` or defaults on Case A without raising. Downstream code reads `None` or `"unknown"`.
3. Metadata-copying targets never exercise the broken fields, so their output looks correct.
4. A new release line is the most likely trigger. The breakage here came from a new Module 20 changelog entry written the same day, and it surfaced only when the plugin-bundle target was recompiled.

## Detection

Run both checks. The first catches Case A, the second catches Case B.

```python
import re, yaml
from pathlib import Path

def metadata_block(txt):
    h = re.search(r"^## Module Metadata\s*$", txt, re.M)
    if not h: return None
    o = re.search(r"^```yaml\s*$", txt[h.end():], re.M)
    if not o: return None
    start = h.end() + o.end()
    c = re.search(r"^```\s*$", txt[start:], re.M)
    return txt[start:start + c.start()] if c else None

def list_dict_items(node, trail=()):
    """Yield (path, item) for every single-key dict sitting inside a list."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from list_dict_items(v, trail + (k,))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            if isinstance(v, dict) and len(v) == 1:
                yield trail, v
            yield from list_dict_items(v, trail + (i,))

for m in sorted(Path("modules").glob("*.md")):
    block = metadata_block(m.read_text())
    if block is None:
        continue
    try:
        data = yaml.safe_load(block)  # Case A: raises here
    except yaml.YAMLError as e:
        print(f"{m.name}: PARSE ERROR {type(e).__name__}")
        continue
    for path, item in list_dict_items(data):  # Case B: flag mixed-type list items
        print(f"{m.name}: list item at {path} is a dict {item!r}")
```

Also grep the compile output for the fingerprint: `grep -n "module_version=unknown"`. Any hit means metadata did not load. The per-target file count is a second signal: compare the count before and after a metadata fix.

Note: this script was written from the session notes and was not executed in this filing. Run it once against the real `modules/` tree before relying on it.

## Fix Patterns

- **Case A, one item:** re-express only the failing item as a folded block scalar. Put `- >-` on the item line, then the original text indented beneath it. The text is preserved byte for byte, with no added `: ` escaping.
- **Case A, single-line item:** single quotes also work (`'text with : inside'`).
- **Case B:** the same folded-scalar fix applies. Verify by loading the repaired block and checking that the original text appears in the parsed list as a string, not a dict.
- **Going forward:** reword new changelog entries to avoid `: `. Write "Registry added Contract F" in place of "Registry: added Contract F". Patch-bump the module and add a changelog entry whose own text also avoids `: `.

## Prevention

- Add the all-modules `safe_load` scan **and** the list-item type check to the pre-commit identity-drift check, so both cases block the commit.
- In CI, treat any compiler warning line (`parse_module_metadata:` or similar) as a build failure. A loader warning that does not fail the build is not a check.
- Where a loader falls back to defaults, emit a counter or a summary line at the end of the run (for example, `metadata fallbacks: 4`), and fail when it is non-zero.

## When This Applies

- A compiler or generator reads per-source YAML metadata that humans edit by hand, and falls back to defaults on load failure.
- The fallback values (`unknown`, `""`, `{}`) reach generated output that other tools or humans consume.
- Changelog-style lists in metadata, where mixed item types are plausible.

## When This Does NOT Apply

- Metadata emitted by a tool (the tool quotes correctly).
- Loaders that raise on bad metadata. The failure is already loud and the compiler-level symptom does not arise.
- Lists where every item is intentionally a single-key mapping. In that case the Case B check will flag them, and the check must be scoped to the known list keys.

## Grounding

Observed on 2026-11-12 in the KnowledgeForge repo. Fixes were applied in knowledgeforge commits `5bd70d9` (module 20, the new release line that introduced the fifth breakage) and `214f1e1` (modules 04, 07, 11, 26). Before the fix, the plugin-bundle target wrote 13 files and stamped `unknown` for two modules. After the fix it writes 14, with versions populated. The Case B mechanism was reasoned from YAML plain-scalar rules and the observed mixed-type changelog. It was not re-executed in this filing, so the grounding score reflects the session evidence, not a fresh parse test.

## Source Context

Filed from the `kf-completion-gate-metadata-yaml-2026-11-12` session, where the compile-output symptoms were found during a recompile of `platforms/`. The candidate was checked for overlap against the 2026-06-14 entry before filing. That entry already covers the parse-error mechanism, the scan, and the single-quote and `|-` fixes, so this entry links to it and does not repeat them. Its claim that any `: ` fails parsing is incomplete, since Case B shows a single `: ` can parse silently. This entry does not edit that entry, per the cannot-modify-without-versioning rule.
