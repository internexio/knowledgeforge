---
title: YAML plain-scalar list items with embedded colon-space fail safe_load silently
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 1.0
staleness_risk: slow_decay
importance: 4
created: 2026-06-14
domain: diagnostics
topic: data-validation
tags: [empirical]
related_entries:
  - compiler/2026-06-10_extract-section-cc-marker-stop-condition-over-extraction.md
pinned: false
---

# YAML Plain-Scalar List Items with Embedded Colon-Space Fail safe_load Silently

## Problem Shape

A YAML changelog entry written as a plain (unquoted) list item that contains `: ` (colon-space) inside parens or quotes will fail `yaml.safe_load()` with `"mapping values are not allowed here"` because the parser ambiguates the embedded `:` as a mapping key. Example:

```yaml
changes:
  - Module Reference table updated for M14 (6.6: vision principle drift detection), M17 (7.0.2: planning artifact staleness predicate)
```

`"6.6: vision"` triggers the parser. The fix is non-obvious because the human reader sees the item as one prose string.

## The Silent-Fail Compounding

If the calling code uses graceful YAML fallback (e.g., `try: yaml.safe_load(text); except YAMLError: return {}`), the parse error becomes silent: the caller gets `{}` and downstream code that reads `metadata["version"]` quietly gets `None`. Symptoms surface far from the cause — e.g., a plugin-bundle compile target silently skips entries because the version-gate `_semver_satisfies("", ">=7.3.0")` returns False.

## Detection

Scan all module metadata YAML blocks:

```python
import re, yaml
from pathlib import Path

for m in sorted(Path("modules").glob("*.md")):
    txt = m.read_text()
    h = re.search(r"^## Module Metadata\s*$", txt, re.M)
    if not h: continue
    o = re.search(r"^```yaml\s*$", txt[h.end():], re.M)
    if not o: continue
    o_pos = h.end() + o.end()
    c = re.search(r"^```\s*$", txt[o_pos:], re.M)
    if not c: continue
    yaml_text = txt[o_pos:o_pos + c.start()]
    try:
        yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        print(f"{m.name}: line {mark.line if mark else '?'} — {yaml_text.split(chr(10))[mark.line][:80] if mark else ''}")
```

## Fix Patterns

- **Single-line entry:** wrap with single quotes — `'text with : inside'`. Single quotes preserve everything except `'`.
- **Multi-line entry:** convert to a literal block scalar `|-`:
  ```yaml
  - |-
    Multi-line text that contains : inside
    and continues across lines : here too.
  ```

No prose changes are required for either fix.

## When This Applies

- Any Python project that loads YAML changelogs / metadata from human-edited files
- Compilers / linters that quietly degrade on YAML parse failure
- Codebases where many modules carry their own metadata blocks (KF, monorepos with per-package frontmatter)

## When This Does NOT Apply

- YAML emitted by tools (those tools quote correctly)
- Single-document configs where the parse error fails loudly (no `except YAMLError`)
- Strict-mode YAML loaders that refuse `: ` in plain scalars at write time

## Grounding

KF-core 2026-06-14 audit found 8 of 26 module metadata blocks failed parsing this way. `parse_module_metadata` returned `{}` in those cases, silently defeating the plugin-bundle version-gate and the bundle-stamp's `module_version` field. After applying single-quote / `|-` fixes across 7 modules (commit `bf42ded`), all 26 parsed cleanly; plugin-bundle target moved from 13 → 14 emitted entries.

## Source Context

The bug surfaced as a downstream consequence (plugin-bundle skipping the librarian) hours after the original parse error was emitted to stderr. The graceful fallback in `parse_module_metadata` was correct design — but it hid the upstream bug. Consider: any "graceful fallback returns empty dict" path should ALSO emit a counter or one-shot warning that downstream code can check.
