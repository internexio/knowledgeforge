---
title: Telegram getUpdates exclusivity — single-bridge architecture for multi-consumer apps
source_mode: direct
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-29
tags: telegram, getUpdates, callback-routing, single-poller, multi-consumer, bot-token, architecture
related_entries: []
domain: infrastructure
topic: server-configuration
---

# Telegram getUpdates Exclusivity — Single-Bridge Architecture for Multi-Consumer Apps

## The Constraint

The Telegram Bot API's `getUpdates` long-poll endpoint allows **only one consumer per bot token** at any given time. A second `getUpdates` call against the same bot token receives `409 Conflict` (or steals updates from the first consumer in some configurations). This is a hard server-side guarantee — it cannot be worked around at the client.

## The Implication: Single Bridge, Namespace Routing

Any non-trivial system that wants multiple internal services to participate in Telegram interaction (push notifications + inline-button approval callbacks) cannot have each service run its own `getUpdates` loop on the shared bot token. The correct architecture is:

1. **One bridge daemon** owns the bot connection and long-polls `getUpdates`.
2. Inbound `callback_data` payloads carry a **namespace prefix** (e.g., `orchestra:`, `ceo:`, `lookout:`, `approve:`) discriminating which internal service the callback belongs to.
3. The bridge **routes** callbacks to the owning service's handler — either by direct in-process dispatch (if the bridge embeds the handlers) or by registering callback→action mappings in a shared table (e.g., a SQLite/Postgres `telegram_callbacks` row keyed by `callback_data`, the dispatch reading that mapping at receive time).
4. Each producer becomes a **client** of the bridge — it sends through the bridge's `send_telegram` API and registers a callback→handler mapping; it does not poll Telegram directly.

## Why It Matters

The footgun is silent and slow to diagnose: build N services that each call `getUpdates`, deploy them, find that some button presses succeed and others vanish — or that the whole system works in test (when only one happens to run) and fails in prod (when both run concurrently). The conflict is intermittent because Telegram's behavior depends on long-poll timing and which process wins the race to claim the connection.

## When This Applies

- Multi-service systems sharing one Telegram bot token where multiple services need to **receive** callbacks or status updates (approval workflows, notifications, interactive responses)
- Integration workflows where decision-making spans multiple agents or domains (e.g., iteration-loop + CEO pipeline both need to respond to Telegram events)
- Long-lived daemon systems that must handle both send and receive patterns durably (business-critical approval flows cannot tolerate dropped messages)

## When This Does NOT Apply

- **Send-only systems** — one-way push, no inline buttons, no replies. Multiple services can `sendMessage` on the same token without any `getUpdates` conflict.
- **Webhook-based architectures** — Telegram pushes updates to a single configured URL, so there's a single consumer by construction. The same routing-by-namespace logic still applies at the webhook receiver, but the long-poll constraint is moot.
- **Truly per-bot isolation** — if each service owns a *separate* bot token (separate `@bot` accounts), they don't share the constraint. This is usually undesirable (multiple bots in one chat is confusing) but valid.

## Concrete Grounding

Discovered 2026-05-29 during the Step 3 (Telegram approval loop) reuse-vs-build spike for the [project] loop-closing work (`[project]-jyku.1` / `[project]-jyku.2`).

The investigation found three Python scripts in [project] each implementing a `getUpdates` long-poll loop and all reading `TELEGRAM_BOT_TOKEN` from the same shared `[project]/.env`:

- `scripts/orchestra-telegram-bridge.py` (440+ lines, established daemon)
- `scripts/ceo-pipeline-agent.py` (polling loop)
- `scripts/lookout-telegram-bot.py` (polling loop)

None were currently running together (which is why no operator-visible conflict had surfaced), but had any two been loaded into launchd as KeepAlive daemons simultaneously, `getUpdates` 409s would have been guaranteed.

The architectural decision was decisive: **do NOT add a fourth iteration-loop poller for the approval callback**. Instead:

1. Extend the existing `orchestra-telegram-bridge.py` (already has a clean `execute_action(action_type, payload)` dispatch backed by `orchestra.db`'s `telegram_callbacks` table keyed by `callback_data` + `source_agent`)
2. Add a new `_action_resume_pending_question` handler for iteration-loop's approval namespace
3. Ensure ceo-pipeline and lookout-bot become send-only clients or have their callback handlers consolidated into the bridge

## Source Context

Session: `2026-05-29-[project]-comms-hub-spike-jyku.1`

Recorded on beads:
- `[project]-jyku.1` — Spike investigation (closed)
- `[project]-jyku.2` — Implementation of consolidated bridge

The pattern generalizes to any system needing multi-consumer event dispatch over a single-connection API (Slack app API, Discord bot, etc.).

## Cross-References

- **Supervision-layer forensics:** General principle "verify the supervision/connection layer before the service code" — see existing entry on dormant-subsystem diagnostics
- **Namespace routing by discriminator:** Structurally similar to `iteration_loop/pending-suggestions.jsonl` using a `kind` field to route envelopes to different handlers ([project] CLAUDE.md pattern: "Kind-discriminator over parallel-file design")
