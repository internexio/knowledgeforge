---
title: File-based stub for deferred external dispatch surfaces
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-05-14
domain: patterns
topic: integration
tags: dispatch, stub, integration-deferred, observability, telegram, webhook, outbox
related_entries:
  - patterns/2026-05-11_atomic-write-stubs-for-readwrite-pipelines.md
  - architecture/2026-05-14_identity-registry-append-only-event-log-separation.md
---

# File-Based Stub for Deferred External Dispatch Surfaces

When integrating with an external dispatch surface (Telegram bot, SMTP, Slack webhook, SMS, PagerDuty, etc.) is **deferred** — because credentials/auth aren't ready, the API isn't verified, the operator hasn't approved the connector, or the vendor-side bot still needs setup — ship a **file-based stub** module instead of an in-memory mock.

## The Pattern

1. Module exposes the same public interface the real impl will have:

```python
def send_alert(payload, decision) -> Path: ...
def send_watchdog_alarm(event, decision) -> Path: ...
```

2. Body writes the formatted alert to a timestamped file under an outbox dir:

```python
OUTBOX_DIR = Path.home() / ".[project]" / "telegram-outbox"

def send_alert(...):
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%f")
    path = OUTBOX_DIR / f"{ts}-{kind}.txt"
    path.write_text(formatted_body, encoding="utf-8")
    return path
```

3. Microsecond suffix in filename prevents collision on back-to-back alerts at the same wall-clock second (multi-tick races for separate findings).

4. Real impl swap is a **one-function-body swap** — callers don't change. When the real bot is ready, the body of `send_alert` becomes `bot.send_message(chat_id, formatted_body)`.

## Concrete Instance

`iteration_loop/telegram_stub.py` ([project] repo, 2026-05-14):

- `send_proposal_alert(proposal, decision)` — Tier 3/4 formats per spec §3.4 / §3.5
- `send_watchdog_alarm(event, decision)` — default §4.4 format + special `budget_breach` frame
- Outbox at `~/.[project]/telegram-outbox/<YYYYMMDDTHHMMSS_microseconds>-<kind>.txt`

Six watchdog producers + Path A Tier 3/4 routes write here. After deployment, the operator sees real alerts pile up in the outbox as evidence that the loop is detecting failure modes correctly, even though no Telegram messages have actually been sent.

## Why Files Over In-Memory Mocks

- **Persists across process boundaries.** Cron worker writes; operator reads later. In-memory mocks die with the process.
- **Tail-able like a real log.** `tail -f outbox/` works.
- **Tests inspect filesystem, not mock objects.** No `unittest.mock.call_args_list` brittleness — assert on file contents.
- **Free dead-letter queue if the real surface goes down later.** Once the real connector is wired, you can `cat outbox/*.txt | bot-resend.py` to replay.
- **Format matches the real surface.** Each file body IS what a real Telegram message would look like — visible audit of "what would have been sent."

## When This Applies

- External dispatch surface whose integration is genuinely deferred (not just stubbed-for-tests)
- Asynchronous one-way notifications (send-and-forget)
- The format is well-specified enough that you can render the message body without the API call
- You want operators / on-call to see the would-be alerts before the connector is live

## When This Does NOT Apply

- **Synchronous request/response surfaces** where the caller awaits a return value — stub the call, not the dispatch, since the file isn't a response.
- **Interactive callbacks** (Slack message → button click → handler) — the file captures the send but not the callback round-trip. Need a different testing harness.
- **High-volume real-time alerting** — filesystem writes become a bottleneck above ~thousands/sec.

## Related But Distinct

- Mocking libraries (`unittest.mock`) — useful for test isolation but not visible to operators between test runs
- Message queues (RabbitMQ, SQS) — heavier weight, more infrastructure; only worth it when consumption logic also needs deferring

## Source Context

Discovered during [project] iteration-loop v0 Phase 1 implementation (2026-05-14). The cost-meter + Tier 3/4 watchdog route detection needed a dispatch surface for alert notifications. Telegram bot setup was deferred pending operator auth configuration. Rather than mock in-memory or block on the real bot, a file-based stub shipped with the Phase 1 code. Operators can now observe real alerts being routed to `~/.[project]/telegram-outbox/` before live Telegram integration is ready.
