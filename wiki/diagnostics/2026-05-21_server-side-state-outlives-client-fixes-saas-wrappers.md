---
title: Encrypted server-side state can outlive every client-side fix
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-21
domain: debugging
topic: root-cause-analysis
tags: empirical, stable, api
related_entries:
  - diagnostics/2026-05-21_happy-filewatcher-absolute-path-symlink-fix.md
  - diagnostics/2026-05-18_happy-cli-filewatcher-ghost-session-mismatch.md
  - infrastructure/2026-05-14_claude-cli-bare-disables-oauth-keychain-auth.md
revises: null
superseded_by: null
---

# Encrypted Server-Side State Can Outlive Every Client-Side Fix

## Problem

When a SaaS-style CLI wrapper exhibits a persistent bug that survives every client-side intervention (reinstall, cache wipe, restart, mode switch, version upgrade), the broken state probably lives in the backend database, not on the client. Local fixes are no-ops because the client re-fetches the broken state from the server on every boot.

## When This Applies

- A CLI tool with a self-hosted or cloud backend (Happy, Linear, Notion CLI, GitHub CLI in some scenarios, custom internal wrappers).
- Bug manifests as a deterministic failure on every fresh launch — never intermittent, never different from one boot to the next.
- Local debugging steps that *should* have worked don't:
  - reinstall the CLI → bug persists
  - clear local cache / state dir → bug persists
  - kill + respawn the process → bug persists
  - switch modes (e.g. local vs remote) → bug persists
  - test the underlying tool directly → underlying tool is fine

If three of those don't help, the assumption "this is a client-side bug" is wrong. Move to server-side diagnosis.

## Diagnostic Flow

1. **Identify the backend.** DNS-resolve the API hostname against your known infrastructure (CLAUDE.md host table, Tailscale registry, etc.). If you can SSH to it, you can inspect it.

2. **Find the persistence layer.** `docker ps` on the host. Look for the database container (Postgres, Redis, Mongo). The schema usually tells you which table holds session/state binding.

3. **Locate the broken row.** From CLI logs, grab any stable identifier — session id, machine id, tenant id, tag — and search the schema for a column that holds it. Many CLI/SaaS backends use a `(account, workdir_or_tag)` UNIQUE constraint, meaning each workdir gets exactly one row that's reused across boots.

4. **Inspect the broken row.** Even if the body is encrypted (`metadata`, `state`, `agentState`), the row itself usually has plaintext columns: `active`, `version`, `updatedAt`, `tag`. These tell you which row to target.

5. **Backup before writing.** `COPY ... TO STDOUT > /tmp/backup-$(date +%s).tsv` is reversible. A `UPDATE` without backup on shared infrastructure is not.

6. **Clear the corrupted state.** Set the broken blob columns to empty/null, bump any monotonic version columns, and update the timestamp. Do NOT delete the row unless you're sure cascading dependents won't bite.

7. **Force the client to re-fetch.** Kill the local process / tmux session / browser tab. The watchdog or natural reconnect re-pulls clean state.

## Concrete Grounding (2026-05-21, happy-coder + happy.semalytics.io)

Symptom: every fresh Happy launch for `~/Scripts/client-project` errored with "No conversation found with session ID: d16de6cc-…", same ID across every boot, after dozens of restart attempts and a major-version upgrade (0.13.0 → 1.1.9). `claude --print` worked fine in the same workdir, ruling out Claude SDK itself.

The bad state lived in `Session.metadata` (encrypted blob) on the Happy server's Postgres (staging host, `happy-postgres` container). The Session row was keyed by `(accountId, tag)` UNIQUE — the tag was a stable UUID derived from workdir, so every Happy boot fetched the same row. Despite `active=false`, the server was reusing the row's metadata, which referenced a Claude session_id that had no `.jsonl` on disk (Claude minted the ID, the hook reported it, Claude died before writing transcript).

Fix:
```sql
UPDATE "Session"
SET metadata = '',
    "agentState" = NULL,
    "metadataVersion" = "metadataVersion" + 1,
    "agentStateVersion" = "agentStateVersion" + 1,
    "updatedAt" = NOW()
WHERE id = 'cmpfi62g96lpnjm14o43zt5d0';
```

Took ~30 seconds. Killed the tmux session, watchdog respawned, first prompt processed normally.

## When This Does NOT Apply

- Bug is intermittent or differs across boots → likely a race, network, or local-state issue, not server-side corruption.
- Bug only affects ONE specific client install → reinstall actually does fix it.
- Backend is opaque/managed (you have no DB access) → diagnostic flow stops at step 1; escalate to vendor support with the diagnostic narrative.
- Bug is in the local file watcher / file-system layer (e.g. ENOENT loops, symlink resolution) → different family of bug, requires different fix.

## Anti-Pattern

Reinstalling the CLI more than once when the first reinstall didn't help. If the first reinstall didn't fix it, the second won't either — the state isn't local. Escalate to backend inspection instead.

## Source Context

Extracted from debugging session 2026-05-21 (happy-gtm-resume-loop). The diagnostic flow above was articulated post-facto because the pattern wasn't yet documented. This is a **meta-diagnostic** — not a fix for a specific tool, but a reasoning method for triaging which layer a bug lives in. High reusability for any developer running SaaS CLI wrappers with self-hosted or cloud backends and SSH access to those backends. The concrete SQL query is specific to Happy's schema, but the flow generalizes across CLI/SaaS tools with deterministic failures and persistent backend state.
