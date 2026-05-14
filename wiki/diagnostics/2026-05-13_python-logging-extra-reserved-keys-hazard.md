---
title: Python logging.extra= reserved-key hazard
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.80
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-13
tags: grounding, quality-gate, empirical, stable
related_entries: []
---

# Python logging `extra=` reserved-key hazard

Passing a key in `logger.warning(msg, extra={...})` that collides with a `LogRecord` attribute raises `KeyError: "Attempt to overwrite 'X' in LogRecord"`. The reserved attribute set is **larger than most developers expect** and includes `message` — the single most natural-looking key for a logging payload.

## The exact failure mode

```python
# THIS LOOKS FINE — IT IS NOT.
logger.warning(f"SECURITY ALERT: {message}", extra={
    "alert": True,
    "message": message,  # ← KeyError on the 5th-and-later call
})
```

The crash:
```
KeyError: "Attempt to overwrite 'message' in LogRecord"
  File ".../logging/__init__.py", line 1606, in makeRecord
```

In `logging/__init__.py::makeLogRecord`:
```python
if extra is not None:
    for key in extra:
        if (key in ["message", "asctime"]) or (key in rv.__dict__):
            raise KeyError("Attempt to overwrite %r in LogRecord" % key)
```

## Why "5th-and-later call" specifically

Discovered during the COS rate-limit refactor in a `SecurityMonitor._alert` method. The alert function only fires when the monitor's threshold (default 5) is reached. So the bug was **latent for the first 4 security events of any session** and only crashed once accumulated events crossed the alert threshold — meaning the bug was a time bomb in production: any user hitting rate-limit five times in an hour would crash the handler.

## The full reserved attribute set

Cannot be used as keys in `extra=`:

```
"message", "asctime"  # explicit hard-block
```

Plus anything in `LogRecord.__dict__` after init:
```
name, msg, args, levelname, levelno, pathname, filename, module, exc_info,
exc_text, stack_info, lineno, funcName, created, msecs, relativeCreated,
thread, threadName, processName, process
```

Of these, **`message`** is the most dangerous because it's the most likely to be picked by a developer naming a payload field. `module`, `filename`, and `pathname` are the next-most-dangerous.

## When this applies

- Any module-level logger call using `extra={...}` for structured fields
- Especially: alert/notification/event-emission patterns where a "message" field is conceptually natural
- Audit existing logger.* calls in security monitors, observability emitters, and any code that wants to enrich log lines with structured payload

## The fix

Rename the colliding key. Common safe alternatives:
- `message` → `alert_message`, `event_message`, `payload_message`
- `module` → `module_name`, `source_module`
- `filename` → `file_name`, `source_filename`

## When this does NOT apply

- You're using `logger.warning(msg)` without `extra=` — completely safe
- Your `extra=` dict only contains keys outside the reserved set — fine
- You're using a structured logger like `structlog` that doesn't go through `LogRecord.__init__` — different model, different rules

## Concrete grounding

Found and fixed in `cos/backend/app/services/security.py::SecurityMonitor._alert` (commit `db14d74`). The bug was 100% reproducible: pytest test exercising 5 rate-limit-exceeded events on the same session crashed with the KeyError. Fix was a single-word rename: `message` → `alert_message`. 13 new tests added at the central rate-limit service that surface the bug if it returns.

## Source Context

Discovered during COS week2 rate-limit debugging session (2026-05-13, source_session: redacted
