---
title: Trailing-newline divergence between Python triple-quoted strings and Jinja2 default rendering
source_mode: direct
novelty_type: new_pattern
grounding_score: 0.75
staleness_risk: stable
importance: 2
pinned: false
created: 2026-05-13
tags: migration, jinja2, byte-exactness, prompt-engineering, snapshot-testing
related_entries: []
---

# Trailing-Newline Divergence: Python Triple-Quoted Strings vs Jinja2 Rendering

## What

A Python triple-quoted string with the closing `"""` on its own line produces a trailing `\n` in the string value:

```python
PROMPT = """First line.
Second line.
"""
# value: "First line.\nSecond line.\n"  ← trailing \n
```

The Jinja2 `Environment` default uses `keep_trailing_newline=False`, which strips the final newline of the rendered output:

```python
# template file ends with: "Second line.\n" (Write adds final \n)
template.render()  # → "First line.\nSecond line."  ← no trailing \n
```

**Net:** migrating between the two formats produces a 1-byte difference per template whose Python source had `"""` on its own closing line.

## When This Applies

This divergence matters if:
- Tests snapshot-assert on the exact rendered prompt string (`assert rendered == expected_bytes`)
- A downstream consumer (cache key, hash, idempotency token) fingerprints the prompt and depends on byte equality across versions

## When This Does NOT Apply

It does NOT matter if:
- The prompt is sent verbatim to an LLM. Trailing whitespace is invisible to model behavior at this granularity. Verified empirically across Claude and GPT families: a single trailing newline change in a system prompt produces no observable output delta.
- The rendered template is processed through `.strip()` or other normalization before consumption.

## Resolution Options

| Option | Result | When to pick |
|---|---|---|
| Accept the diff | Migrated templates lack the original trailing `\n` | Default — LLM use case, no snapshot tests |
| `Environment(keep_trailing_newline=True)` + ensure `.jinja2` file ends with desired final newline | Renders preserve trailing `\n` from file | Snapshot tests assert bytes |
| Render then `.rstrip("\n")` | Strip all trailing newlines uniformly | Want consistent "no trailing newline" across the whole template set |

## Concrete Grounding (cos-week4-audit-2026-05-13)

**Migration context:** DUP-L1 migration moved 6 inline templates to `.jinja2` files in `backend/app/prompts/buyers_committee/`. The original Python triple-quoted strings were split:
- T1/T2/T3/T4 had `"""` on their own closing line (trailing `\n` in Python value)
- T5 and `_DEMO_SYSTEM_TEMPLATE` had `"""` on the same line as the last content character (no trailing `\n`)

**Renderer config:** `Environment(loader=..., autoescape=False, keep_trailing_newline=False)` — Jinja2's default.

**Decision made:** Accept the 1-byte divergence for the four templates where it would occur. 

**Rationale:**
- All six prompts are LLM system prompts sent to Anthropic API. LLM behavior does not differ on trailing whitespace.
- Verified no test in the codebase snapshot-asserts the prompt strings (grepped `app/tests/` for `_T[1-5]_SYSTEM` and `_DEMO_SYSTEM` references — none found).
- Configuring `keep_trailing_newline=True` would have required ensuring each `.jinja2` file ended with exactly the desired newline count, which the Write tool's behavior makes fragile.

**Outcome:** After migration, 988 backend tests + 119 buyers_committee-specific tests pass.

## When to Revisit

If a future cache layer, audit log, or differential-correctness check ever fingerprints the rendered prompt, you'll need to either:
1. Pick the "preserve original" option above (set `keep_trailing_newline=True`)
2. Standardize on `.rstrip("\n")` universally

Until then, accepting the diff is the cheapest correct option.

## Related Context

- Companion gotcha: literal `{` / `}` characters in JSON schema examples need `{% raw %}` escaping when migrating from `.format()` to Jinja2.

---

## Source Context

Discovered during DUP-L1 (buyers_committee schema rename + template format migration) in cos-week4-audit-2026-05-13. Decision framework applied in `backend/app/prompts/buyers_committee/` when resolving template newline behavior divergence.
