---
title: Stable Error-Class Enum Alongside Freeform Reason String in Subprocess Result Types
source_mode: builder
novelty_type: reusable_pattern
grounding_score: 0.95
staleness_risk: stable
importance: 4
pinned: false
created: 2026-07-14
domain: patterns
topic: error-handling
tags: [error-handling, enums, subprocess, result-types, python, api-design]
related_entries: [patterns/2026-05-16_discriminated-enum-extension-7-point-checklist.md, patterns/2026-05-14_collapse-usestate-discriminated-union-reducer.md]
---

# Stable Error-Class Enum Alongside Freeform Reason String in Subprocess Result Types

## Pattern: Error-Class Enum + Reason String in Subprocess Result Types

### What was learned

Subprocess wrappers that return a freeform `reason: str` on failure have a callsite problem: callers must parse strings to branch on failure type. This creates fragile coupling (callers break when reason strings change) and makes aggregation impossible without regex.

The fix is to add a stable `error_class: ErrorClassEnum | None` field alongside the existing `reason: str | None`. The fields serve different audiences:

- `error_class` — for programmatic branching by callers (switch/match, routing log aggregation, retry strategy selection)
- `reason` — for human-readable audit trail (includes dynamic content: rc codes, stderr snippets, field paths)

### Implementation pattern (Python dataclass)

```python
import enum
from dataclasses import dataclass
from typing import Any

class KFChainErrorClass(enum.Enum):
    """Stable error category. None when ok=True."""
    BIN_NOT_FOUND    = "bin_not_found"     # binary missing from PATH
    TIMEOUT          = "timeout"            # subprocess.TimeoutExpired (retryable)
    SUBPROCESS_ERROR = "subprocess_error"   # OSError/FileNotFoundError (retryable)
    INVALID_ENVELOPE = "invalid_envelope"   # stdout not parseable as JSON
    BUDGET_EXCEEDED  = "budget_exceeded"    # cost cap hit
    CLI_ERROR        = "cli_error"          # non-zero rc (not budget) / is_error
    SCHEMA_VIOLATION = "schema_violation"   # payload fails json-schema validation
    EMPTY_RESULT     = "empty_result"       # result field empty or non-string
    INVALID_JSON     = "invalid_json"       # result field not parseable as JSON

@dataclass(frozen=True)
class SubprocessResult:
    ok: bool
    payload: dict[str, Any] | None
    cost_usd: float
    reason: str | None = None           # human-readable, may include dynamic content
    error_class: KFChainErrorClass | None = None  # stable enum, None when ok=True
```

### Key design properties

1. **Backward compatible** — `error_class` has a default of `None`, so existing callers that construct `SubprocessResult(ok=True, payload=p, cost_usd=c)` continue to work unmodified.

2. **Never parse strings** — callers branch on `result.error_class == KFChainErrorClass.TIMEOUT` not `"timeout" in result.reason`. The enum is the stable contract; the reason string is informational.

3. **Reason strings stay unchanged** — existing tests that check `assert result.reason == "timeout"` or `assert "schema_violation" in result.reason` continue to pass. The string format is NOT changed when adding the enum — both are maintained independently.

4. **Retry policy uses the enum** — the retry wrapper surfaces the second attempt's `error_class` on double-fail (most-recent failure mode). The reason string captures both attempts via concatenation: `"retried: 1st=timeout; 2nd=schema_violation"`.

5. **Retryable vs. non-retryable is readable from the enum** — callers can check `result.error_class in (ErrorClass.TIMEOUT, ErrorClass.SUBPROCESS_ERROR)` for transient failures worth retrying vs. `ErrorClass.SCHEMA_VIOLATION` which is deterministic and retrying is pointless.

### Concrete source

`[project]/iteration_loop/kf_chain.py` — `KFChainErrorClass` enum + `KFChainResult` dataclass. Implemented 2026-07-13. 50 tests, 0 failures. The stages that previously checked `result.reason` as a string (`calibrator_confidence.py`, `critic_adversarial.py`, `strategist_priority.py`) can now switch to `result.error_class` for routing-log aggregation.

### When this applies

- Any subprocess wrapper that returns a result type with a freeform failure reason
- When callers branch on failure type (retry strategy, routing log categorization, error reporting)
- Python 3.11+ with frozen dataclasses (the `object.__setattr__` workaround not needed — just add the field with a default)

### When this does NOT apply

- Simple one-shot calls that only care about ok/fail, not failure category
- When the existing codebase has only one caller and there's no aggregation need
- Go codebases: use sentinel error types or error wrapping instead of a parallel enum field

### Anti-patterns

- **Don't replace the reason string with the enum** — the enum loses dynamic context (actual rc code, stderr snippet, field path). Keep both.
- **Don't make error_class required** — adding it as optional with default=None is the backward-compatible path; making it required breaks all existing call sites.
- **Don't parse error_class from reason** — the enum should be set at the source (the specific return statement), not derived by regex from the reason string at read time.

## When This Applies

Subprocess wrappers where:
- Callers need to branch on error category (retry vs. fail-closed, log aggregation, metrics)
- Existing code already returns a reason string
- Multiple call sites need independent decision logic per error type

## When This Does NOT Apply

- Simple CLI wrappers with a single caller
- One-off scripts where the reason string is only for logging
- Systems that already use exception types or result enums at the call boundary

## Source Context

Sourced from [project] KF-chain work (session [project]-kf-chain-error-enum-2026-07-13). The KFChainResult type carries results from subprocess invocations of Claude CLI. Earlier design had only `reason: str` on failure; callers had to parse strings to decide retry strategy or route errors to logs. The enum+string dual design enables both stable programmatic routing and human-readable audit trails without changing existing reason-string formats or breaking backward compatibility.
