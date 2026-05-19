---
title: bd validates issue title length in UTF-8 bytes, not codepoints — error message says "characters"
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-18
tags: beads, bd, gastown, validation, unicode, gotcha, ai-tool-integration
related_entries: [diagnostics/2026-05-15_bd-validator-cache-requires-unset-reset-refresh.md, diagnostics/2026-05-13_bd-search-idempotency-grep-trap.md]
domain: infrastructure
topic: data-validation
---

# bd validates issue title length in UTF-8 bytes, not codepoints

## The gotcha

The `bd` (beads_rust) CLI rejects titles over a byte-length limit (500 UTF-8 bytes), but the error message uses the word "characters":

```
validation failed for issue : title must be 500 characters or less (got 506)
```

The integer it reports (506) is the **UTF-8 byte count**, not the Unicode code point count. Any caller that truncates by `len(title)` (Python), `.length` (JavaScript), or `str.len()` (Rust) is truncating by code points, not bytes. When the title contains multibyte characters (em-dash `—` is 3 bytes, smart quotes `"` or `"` are 3 bytes each, accented letters 2 bytes, emoji 4 bytes), the truncated string can still exceed 500 bytes and fail validation.

## Concrete failure pattern observed

On 2026-05-17 cron run of `scripts/gastown-router.py`:
- Script truncated title to 499 Python `len()` codepoints + `…` (3-byte ellipsis)
- Resulting string: 500 codepoints / 506 UTF-8 bytes
- `bd create` rejected with `got 506`
- Impact: 10 of 85 site-monitor suggestions failed for this reason alone

## Correct truncation pattern

```python
def truncate_title_to_bytes(text: str, max_bytes: int = 500) -> str:
    """Truncate text to max_bytes UTF-8 encoded, appending ellipsis if truncated."""
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    
    ellipsis = "…"  # 3 bytes in UTF-8
    budget = max_bytes - len(ellipsis.encode("utf-8"))
    
    # Slice at byte boundary, then decode with errors="ignore" to drop
    # any partial codepoint at the slice point.
    head = encoded[:budget].decode("utf-8", errors="ignore").rstrip()
    return head + ellipsis
```

The `errors="ignore"` clause is load-bearing: slicing arbitrary byte offsets can land mid-codepoint, which raises `UnicodeDecodeError` without error handling. With `errors="ignore"`, the trailing partial sequence is silently discarded and the result is valid UTF-8.

## Why this happens

`bd` validates byte length because the underlying database schema imposes a byte limit (common in PostgreSQL and similar systems for VARCHAR columns with explicit byte width). The error message wording is misleading — it says "characters" but means "bytes". Any tool consuming natural-language text (SEO copy, dream summaries, LLM output, user input) sees em-dashes and smart quotes routinely and will hit this boundary.

## When this applies

- Any tool feeding natural-language sources into `bd create --title`
- Long-running automation pipelines where the first 499 code points look fine but the tail (e.g., ellipsis) tips byte length over 500
- Scripts or agents truncating titles from LLM outputs or user copy
- Any multilingual content with accents or non-ASCII punctuation

## When this does NOT apply

- ASCII-only text sources where byte count == code point count
- Tools that already enforce byte-length limits at the input layer (most JSON-schema validators use byte counts)
- Direct `bd` command invocation from user shell (user is responsible for title length)
- Manual issue creation via UI (UI typically enforces the limit client-side)

## Grounding evidence

- **2026-05-17 06:00 cron run:** `scripts/scan-and-route.sh` produced 10 failures with exact `got 506` error
- All 10 involved titles containing em-dashes (`—`, U+2014) from [project] dream summaries
- Hypothesis verified: Python `len("...—...")` returned 500 codepoints but `len("...—...".encode("utf-8"))` returned 506 bytes
- Fix shipped in commit `79d8de9` (`scripts/gastown-router.py`)
- Unit test coverage: 10 tests in `scripts/test_gastown_router.py` cover ASCII threshold, em-dash regression at exact 506-byte boundary, and safe codepoint-boundary handling

## Related tracking

- Bead: [project]-5et5 (P1 bug, in_progress, pending cron verification 2026-05-19)
- Repository: https://github.com/steveasleep/beads
- CLI binary: `~/.local/bin/br` (aliased `bd`)

## Source Context

Direct diagnostic from happy-and-kf-decomp session (2026-05-18). Pattern emerged during gastown-router automation testing with LLM-generated titles containing smart punctuation. Reproduction is deterministic with any em-dash or other 3-byte character at the truncation boundary.
