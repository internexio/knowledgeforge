---
title: stripe.Event does not support .get() — use [] access
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-18
tags: stripe-python, webhook, integration-pitfall, empirical, stable
related_entries: []
---

# stripe.Event does not support .get() — use [] access

## What this is

The Python stripe SDK exposes `stripe.Event` as a `StripeObject` instance,
not a plain dict. `StripeObject` supports `obj["key"]` and `obj.key` (via
`__getitem__` / `__getattr__`), but does NOT support `obj.get(key, default)`.

Calling `event.get("id")` raises `AttributeError: get` because Python first
looks up `"get"` as an attribute, falls through to `__getattr__` which
calls `__getitem__("get")`, which raises `KeyError` (no key called "get").
The error is then re-raised as AttributeError.

## When it bites you

Defensive code patterns like `event_id = event.get("id")` look reasonable
to a Python dev who's used to dicts. They fail the FIRST time a real
Stripe event reaches the handler. If your webhook is rarely exercised
(e.g. a single test customer hitting it monthly), the bug can mask for
months — every Stripe event 500s and Stripe retries silently exhaust.

## Real-world incident

A COS Stripe webhook had this pattern committed for ~4 months. Webhooks
for invoice.paid and customer.subscription.deleted events were ALL
500ing in production. Bug only caught when a manual subscription
cancellation needed to clear the local DB row — and the webhook never
fired. Investigation found the 500 was a pre-existing bug.

## The fix

```python
# Wrong:
event_id = event.get("id")

# Right:
event_id = event["id"]                   # raises KeyError on malformed events
# or if you really need a default:
event_id = event["id"] if "id" in event else None
```

## When this does NOT apply

- requests.Response, httpx.Response, plain dicts: .get() works fine.
- stripe.Charge, stripe.Invoice, stripe.Subscription: same StripeObject
  parent — same rule applies.
- After event.to_dict() or json.loads(event.json()): you have a plain
  dict; .get() works.

## Diagnostic signature

If you see this in prod logs:
```
File "/path/to/your/code.py", line N, in handler
    x = event.get("foo")
File ".../stripe/_stripe_object.py", line ~170, in __getattr__
    raise AttributeError(*err.args) from err
AttributeError: get
```
…you have this bug. Search the rest of your codebase for `<stripe_object_var>.get(` — likely more than one site.

## Source Context

COS production incident detected during billing-exemption e2e session
(2026-05-18). The webhook had been silently failing for ~4 months before
the bug was discovered during a manual subscription management flow that
required the webhook to emit an event to the local DB. Root cause: event
was a `stripe.Event` instance returned from the Stripe library, and the
handler used `.get()` to safely extract fields — a Python idiom that
does not apply to StripeObject. Grounding score reflects concrete
production detection and multi-month latency window (defensive pattern
masking the bug very effectively). Fix is straightforward but the pattern
is easy to repeat across any Stripe webhook codebase.
