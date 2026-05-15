---
title: Claude CLI structured-output vs result routing — json-schema callers must check structured_output first
source_mode: builder
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-05-14
domain: patterns
topic: subprocess-integration
tags: [claude-cli, json-schema, structured-output, subprocess-integration, envelope-routing]
related_entries:
  - infrastructure/2026-05-14_claude-cli-bare-disables-oauth-keychain-auth.md
  - patterns/2026-05-14_file-based-stub-deferred-dispatch-surfaces.md
---

# Claude CLI `--json-schema` Populates `structured_output`, Not `result`

## The Problem

When invoking `claude --print` with a `--json-schema` argument, the validated JSON payload is placed in `envelope.structured_output` (a dict), NOT in `envelope.result`. The `result` field becomes prose output or remains empty in schema mode.

Callers that read only `envelope.result` will reliably see an empty or unparseable value **on 100% of successful schema-validated responses**. This appears as a subprocess success (rc=0, no `is_error=true`) with an invalid or missing structured response — the classic "silent data loss" pattern.

### Measured Impact

In the [project] KF chain v0 hardening (2026-05-14), this routing mismatch caused **40 of 41 successful findings to surface as `empty_result_field` errors** before diagnosis. All 40 calls returned valid JSON in `structured_output`, but the caller was looking in the wrong envelope field.

## When This Applies

- You're invoking `claude --print --json-schema '<schema>'` from a subprocess wrapper (Python `subprocess.run`, shell script, etc.)
- You're parsing the `envelope.result` field to extract the validated JSON
- You see rc=0 and `is_error=false`, but the result is empty, `null`, or unparseable
- The call succeeded (LLM generated a response), but the structured data appears to have vanished

## When This Does NOT Apply

- You're calling `claude --print` without `--json-schema` — `result` is the correct field
- You're using the Claude API directly (REST or SDK) — the `content_block.text` and `content_block.input_json` fields are already correctly routed
- You're calling from within a Claude Code session (the Agent tool, `/raw`, etc.) — different envelope contract

## The Fix

Before parsing `result`, check `structured_output` first. Only fall back to parsing `result` if `structured_output` is absent (for backward compatibility with callers that don't pass a schema, or older CLI versions).

### Pattern

```python
def extract_response(envelope):
    """
    Route structured responses from claude --print.
    
    When --json-schema is passed, the validated JSON lands in structured_output.
    When --json-schema is NOT passed, the response is prose in result.
    """
    # Check structured_output first (schema mode)
    if isinstance(envelope.get("structured_output"), dict):
        # This is the validated payload from --json-schema
        return envelope["structured_output"]
    
    # Fall back to result (prose mode or older CLI)
    result_str = envelope.get("result", "")
    if not result_str:
        raise ValueError("Both structured_output and result are empty")
    
    # Try to parse result as JSON (for callers that don't use --json-schema)
    try:
        return json.loads(result_str)
    except json.JSONDecodeError:
        # Not JSON — return as prose
        return result_str
```

### Subprocess Wrapper Example

```python
import subprocess
import json

def invoke_claude_with_schema(prompt, schema):
    """Invoke claude --print with a schema and route the response."""
    result = subprocess.run(
        [
            "claude", "--print",
            "--output-format", "json",
            "--json-schema", json.dumps(schema),
            "-p", prompt,
        ],
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"claude failed: {result.stderr}")
    
    envelope = json.loads(result.stdout)
    
    # Correct routing: check structured_output first
    if isinstance(envelope.get("structured_output"), dict):
        return envelope["structured_output"]
    
    # This should not happen in schema mode, but handle it
    raise ValueError(
        f"No structured_output in response. "
        f"Envelope keys: {envelope.keys()}"
    )
```

## Root Cause

The Claude CLI's `--json-schema` mode operates in two stages:

1. **LLM generation:** Constrained to match the schema (via guided JSON generation)
2. **Validation:** The validated JSON is stored in `structured_output`
3. **Result field:** Contains only the prose preamble/explanation (if any), not the JSON payload

This is the intended behavior — `structured_output` is specifically for schema-validated payloads, and `result` is for natural-language responses. Callers familiar with the bare API (where structured content goes in `content_block.input_json`) need to re-route when using the CLI.

## Envelope Structure Reference

### With `--json-schema`
```json
{
  "result": "Here's the extracted data in JSON format.",
  "structured_output": {
    "field1": "value1",
    "field2": 42,
    ...
  },
  "stop_reason": "stop_sequence",
  "usage": { ... }
}
```

### Without `--json-schema`
```json
{
  "result": "Full prose response here...",
  "structured_output": null,
  "stop_reason": "stop_sequence",
  "usage": { ... }
}
```

## Trade-Offs

| Aspect | Benefit | Cost |
|---|---|---|
| Check `structured_output` first | Handles schema mode correctly, then falls back to prose | One extra `isinstance` check per response |
| Hardcoded field routing | Fast, predictable | Breaks if CLI changes field names (unlikely) |
| Dual-mode parsing | Supports both schema and prose invocations in one code path | Adds conditional logic |

For subprocess wrappers that **always** use `--json-schema`, just read `structured_output` directly and raise an error if it's missing. No fallback needed. For generic wrappers that accept an optional schema argument, use the dual-mode pattern above.

## Concrete Grounding

- **Live reproduction (2026-05-14):**
  ```bash
  schema='{"type":"object","properties":{"name":{"type":"string"},"count":{"type":"integer"}}}'
  claude --print --output-format json --json-schema "$schema" \
    -p "Extract: John has 5 apples" | jq .
  ```
  Output:
  ```json
  {
    "result": "Here's the extracted data:",
    "structured_output": {
      "name": "John",
      "count": 5
    }
  }
  ```
  Note: `result` is prose, `structured_output` is the actual payload.

- **Implementation reference:**
  `~/Scripts/[project]/iteration_loop/kf_chain.py` lines 218–253
  (commit `fad3877`). The KF chain's response envelope parser was updated to check `structured_output` first before attempting to parse `result`.

- **Test coverage:**
  Each KF stage that uses `--json-schema` now has a unit test verifying that `structured_output` is extracted correctly, and that `result` is ignored (unless `structured_output` is absent).

- **Related:** Infrastructure entry **"Claude CLI `--bare` Disables OAuth/Keychain Auth"** (infrastructure/2026-05-14_claude-cli-bare-disables-oauth-keychain-auth.md) documents another CLI routing footgun in the same subsystem.

## Source Context

Extracted during [project] iteration-loop v0 hardening (2026-05-14). The KF chain's response parser was invoked ~41 times in early testing, and all 41 calls returned valid JSON in `structured_output`. However, the caller was looking in `result`, which contained only prose preambles or was empty. This manifested as silent data loss: rc=0 success, but the structured data appeared to vanish mid-pipeline. Root-cause diagnosis: re-read the CLI docs for `--json-schema` mode and discovered the field routing difference. After fixing the envelope parser to check `structured_output` first, all 40 previously-failed calls succeeded. The pattern is reusable for any subprocess caller that uses the Claude CLI with `--json-schema`, making it a diagnostic entry for the next team member who hits the same footgun.
