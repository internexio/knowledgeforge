---
title: Automating Happy Claude sessions from external processes — tmux send-keys + C-m mechanism, E2E-encrypted API caveat
created: 2026-07-03
source_mode: builder
source_session: redacted
novelty_type: reusable_diagnostic + transferable_framework
grounding_score: 0.90
staleness_risk: slow_decay
importance: 4
domain: infrastructure
topic: ops
tags: [scheduling, api, empirical, sidecar, volatile]
---

# Automating Happy Claude sessions from external processes

## The problem
When you need an external process (launchd job, autopoll daemon, cron script) to inject a user prompt into a running Happy-managed Claude Code session, the naïve options fail:

1. **HTTP POST to Happy's session API (`/v3/sessions/{id}/messages`)** — DOES NOT WORK. Every message on that endpoint is end-to-end encrypted with a per-session key via `encrypt(session.encryptionKey, session.encryptionVariant, content)`. The Happy server cannot read plaintext; neither can any external process without the in-memory key of that specific session. This is a deliberate architectural moat (mobile ↔ server ↔ local session is E2E encrypted). Verified 2026-07-03 in `/opt/homebrew/lib/node_modules/happy-coder/dist/types-BtoZF_Bo.mjs` — see `RpcHandlerManager` class and `enqueueMessage()`.

2. **`tmux send-keys "prompt" Enter`** — FAILS SILENTLY in two ways:
   - **Remote mode**: if the Happy session shows the marker `📡 Remote Mode - Claude Messages` in its pane, typed input is captured by Happy's TUI (only Space, Ctrl-T, Ctrl-C are meaningful) and never forwarded to Claude Code below. Sessions are in remote mode whenever they're mobile-driven.
   - **Wrong submit key**: even in local mode, tmux's `Enter` keyword does not submit — Claude Code's Ink TUI input widget requires a literal CR (`C-m`). Sending `Enter` types text into the buffer without submitting; the prompt sits there until something else pushes CR.

## The working mechanism

For any Happy session running under `happy --yolo` in tmux:

1. **Detect mode** — capture the pane and look for the substring `Remote Mode - Claude Messages`:
   ```bash
   pane=$(tmux capture-pane -t "$SESSION" -p)
   if echo "$pane" | grep -qF "Remote Mode - Claude Messages"; then
       # session is in remote mode
   fi
   ```

2. **If remote mode, flip to local** — send Ctrl-T and poll for the transition:
   ```bash
   tmux send-keys -t "$SESSION" C-t
   for _ in $(seq 1 16); do
       sleep 0.5
       cur=$(tmux capture-pane -t "$SESSION" -p)
       if ! echo "$cur" | grep -qFE "Remote Mode - Claude Messages|Switching to local mode"; then
           break   # transitioned
       fi
   done
   ```
   Transition typically completes in 1–3 seconds. Ceiling at 8s; treat longer as a stuck state and skip the nudge.

3. **Send prompt + submit with C-m**:
   ```bash
   tmux send-keys -t "$SESSION" "your prompt text here"
   tmux send-keys -t "$SESSION" C-m
   ```

4. **Decide about switching back to remote** — a second `C-t` restores remote mode, but that briefly re-hides the just-sent prompt from mobile view. Per cos-manager operator decision (2026-07-03), STAY in local mode after nudge; do not switch back. Mobile driver can flip back manually.

## When this applies
- External scheduled nudges (launchd, cron) into a mobile-primary Claude fleet
- Cross-session coordination where one session needs to trigger work in another
- Reactive queue polling (autopoll) where an idle Claude needs to be told to check an inbox
- Any workflow that wants to inject user turns without going through Happy's mobile UI

## When this does NOT apply
- If the target Claude is a plain `claude` (not `happy`) — send-keys + `C-m` works directly, no mode handling needed
- If the Happy session has been paused (`happy-pause.sh`) — session process is dormant, tmux keys accumulate but do nothing
- If the session's tmux name differs from what watchdog boots — verify with `tmux ls` before nudging (`sem-tools` had a stuck watchdog on 2026-07-03 and its session was absent despite the plist being installed)

## Related patterns
- **Happy daemon HTTP API** — `happy daemon` exposes `/list`, `/spawn-session`, `/stop-session`, `/callback`, `/clear`, `/compact`, `/mcp`, `/skills`, `/tmp` on its randomly-chosen local port (see `happy daemon status` for the port). NONE of these inject prompts into existing sessions. Documented here for completeness so future readers don't re-investigate.
- **Autopoll debounce** — when nudging on pending-work, use a per-agent state file recording `last_nudge_ts` + `last_pending_count`. Skip re-nudge within cooldown UNLESS pending count grew (new work arrived). See `~/Scripts/[project]/scripts/orchestra-autopoll.py` for the reference implementation.

## Grounding
- Happy source inspection: `/opt/homebrew/lib/node_modules/happy-coder/dist/types-BtoZF_Bo.mjs` for encryption; `/dist/index-8VEfbn-K.mjs` for remote-mode UI + key bindings
- Empirical probe on cos-grounding session 2026-07-03: sent prompt via send-keys + C-m, Claude responded `⏺ ack`
- Live-fire on [project] 2026-07-03: mode-detect + C-t + prompt + C-m dispatched real work ([project] claimed art_dffab2c4 and began executing the b5-003 + fs-004 deployment plan)
- Reference implementation: `~/Scripts/[project]/scripts/orchestra-autopoll.py` (committed) and `~/Scripts/cos-manager/scripts/run-manager.sh` (Phase 3 commit)
