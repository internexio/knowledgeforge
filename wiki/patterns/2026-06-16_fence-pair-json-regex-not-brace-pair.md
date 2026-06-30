---
title: Markdown-fence JSON regex must match between fences, not between braces
date: 2026-06-16
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.95
staleness_risk: stable
importance: 4
tags: [regex, json-parsing, llm-output, anthropic, python]
domain: patterns
topic: synthesis
---

# Markdown-fence JSON regex must match between fences, not between braces

When extracting JSON from a markdown-fenced LLM response, the regex pattern
matters more than it looks. A `\{[\s\S]*?\}` non-greedy brace pattern is
nested-brace-unsafe and silently truncates the captured JSON.

## The bug

Common existing pattern, looks reasonable:
```python
json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
```

Failure case — LLM returns nested objects:
```
```json
{
  "wrapper": {
    "inner": {"score": 7}
  },
  "overall": 8
}
```
```

The `\{[\s\S]*?\}` is non-greedy on `{...}` pairs, so it matches the
SHORTEST balanced segment. With nested objects, that's the FIRST inner
`{}` pair (`{"score": 7}` or even just `{}` if `score` was empty). The
captured text is a JSON fragment that fails to parse.

Worse: when `re.search` fails its first pattern, downstream fallback code
often tries `json.loads(text)` directly. That fails too (the markdown
fences aren't valid JSON). Result: parsing returns `None`, caller defaults
to 7.0/null/empty. Silent corruption.

## The fix

Match between FENCE pairs, not between brace pairs. Fences nest predictably
(LLMs don't nest code blocks inside code blocks for JSON output), so
non-greedy fence matching IS safe even when the JSON content has arbitrary
nesting.

```python
def _extract_json(self, text: str) -> dict | None:
    if not text:
        return None

    # Capture between fence pairs — nested-brace-safe.
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Fallback for truncated responses (no closing fence — max_tokens hit).
    # Capture from after opening fence to end-of-text, try parsing what
    # we have.
    open_fence = re.search(r"```(?:json)?\s*", text)
    if open_fence:
        candidate = text[open_fence.end():].rstrip("`").strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Try raw JSON (no fences).
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Last resort: GREEDY outermost {...} match (handles nested braces
    # because greedy goes furthest-right, finding the true outer pair).
    json_match = re.search(r"(\{[\s\S]*\})", text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    return None
```

Four fallbacks in order of likelihood:
1. **Closed fenced block** (most common with claude-sonnet-4-5+)
2. **Truncated response, opening fence only** (max_tokens hit mid-stream)
3. **Raw JSON, no fences** (older Claude models, structured-output mode)
4. **Greedy brace match** (defensive — handles unusual prefixes)

## Why greedy `\{[\s\S]*\}` works as the last-resort fallback

Counter-intuitively, the greedy version is MORE robust on nested objects
than the non-greedy one. `\{[\s\S]*\}` matches from the first `{` to the
LAST `}` in the text — which is the closing brace of the outer object
when there's only one top-level object. The trailing whitespace / prose
after the JSON is fine because `json.loads` parses successfully if the
content is valid up to a delimiter (and `re.search` returns just the
matched span).

Greedy match fails when there are multiple top-level JSON objects in the
text (would match from the first `{` to the last `}` across all of them,
producing invalid JSON). That's rare for analyzer responses where prompts
ask for one object — but worth noting if you see weird parse failures
where the outer-most match clearly spans multiple objects.

## Why this matters

Silent corruption. The parser returning `None` triggers caller defaults
(7.0 scores, empty arrays, "Unknown" labels). The user sees a green CI
build and a working 200-response endpoint that produces useless output.

In COS, this exact bug shipped to production until manual hot-patch
inspection of the raw LLM response revealed the truncated fragment in the
match group.

## Verified grounding

Rewrote `cos/backend/app/services/analyzers/base.py::_extract_json` 2026-06-15
(commit `c769cbd`). Before: all 4 framework analyzers returned `null`
because `_extract_json` returned `None` on every claude-sonnet-4-5
response. After: parser successfully extracted JSON from fenced responses;
exposed a downstream shape-drift bug (the JSON parsed but the keys
inside didn't match parser expectations) — handled separately by
[[lock-llm-json-output-with-explicit-schema-example]].

## Related

- [[anthropic-model-eol-incident-response-three-phase-fix]] — the
  umbrella context (this is Phase 2 of the 3-phase response)
- [[lock-llm-json-output-with-explicit-schema-example]] — the better
  long-term fix (tell the LLM NOT to use fences); this regex pattern is
  defense-in-depth for when the LLM ignores the instruction anyway
