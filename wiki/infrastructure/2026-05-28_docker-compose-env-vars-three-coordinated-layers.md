---
title: Docker Compose env vars need 3 coordinated layers to reach a container and survive deploys
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-28
tags: docker-compose, deployment, environment-variables, infrastructure, ci-cd, debugging
related_entries: []
---

# Docker Compose env vars need 3 coordinated layers to reach a container and survive deploys

## The Trap

Getting a new environment variable to actually reach a running container — AND survive the next CI deploy — requires THREE separate, independently-failable changes. Doing one or two of them produces a silent no-op: the feature reads its config as empty/default and nobody sees an error.

### Layer 1 — the value in `.env`

`RATE_LIMIT_TRUSTED_IPS=1.2.3.4` in `/opt/app/.env`. Necessary but NOT sufficient.

### Layer 2 — the passthrough in `docker-compose.yml`

Compose only injects vars that are explicitly listed in the service's `environment:` block:

```yaml
services:
  backend:
    environment:
      - RATE_LIMIT_TRUSTED_IPS=${RATE_LIMIT_TRUSTED_IPS:-}
```

If a var is in `.env` but NOT referenced here, the container never sees it. This is the most commonly-missed layer — developers add the `.env` line, restart, and are baffled when `docker exec <c> env | grep VAR` shows nothing. (Note: `env_file:` directives pass the whole file through and avoid this, but many production composes use explicit `environment:` lists for clarity/security — check which style is in use.)

### Layer 3 — survival across redeploys

If the CI deploy step templates `.env` from scratch (e.g. `ssh host "cat > /opt/app/.env << EOF ... EOF"`), any manually-added `.env` line is WIPED on the next deploy. The durable pattern is a separate file the deploy appends:

```bash
# in the deploy workflow, after templating .env:
if [ -f /opt/app/.env.local ]; then
  cat /opt/app/.env.local >> /opt/app/.env
fi
```

Put the value in `.env.local` (or whatever the project's append-file is named) so it persists. The compose file (Layer 2) is itself usually scp'd from the repo on deploy, so the passthrough line must live in the repo's compose file — not just hot-patched on the host.

## Restart Semantics (a 4th subtlety)

`docker compose restart` does NOT re-read `.env` — env vars are bound at container CREATE time. Use `docker compose up -d --force-recreate <service>` to pick up new env values. A plain `up -d` may also no-op if compose decides nothing changed (it doesn't always detect `.env`-only changes), so `--force-recreate` is the reliable lever.

## Diagnostic Checklist

When a container isn't seeing an env var you "set":

1. `docker exec <c> env | grep VAR` — is it actually in the container? (If yes, you're done.)
2. `grep VAR /opt/app/.env` — is the value present on the host?
3. `grep VAR docker-compose.yml` — is there an `environment:` passthrough line?
4. Will it survive the next deploy? Check whether the deploy workflow rewrites `.env` and whether VAR is in the append-file.

## When It Does NOT Apply

- Composes using `env_file: .env` (whole-file passthrough) skip Layer 2.
- Local dev where you control `.env` and never run the CI deploy — Layer 3 is moot.
- Vars baked into the image at build time (ENV in Dockerfile) — different mechanism entirely.

## Concrete Grounding

[project] 2026-05-28 (cos-rig trusted-IP whitelist): adding `RATE_LIMIT_TRUSTED_IPS` to the prod `.env` and restarting did nothing — `docker exec` showed the var absent. Root cause cascade: (1) added to `.env` ✓ but (2) `docker-compose.yml` had no passthrough line, so even after `--force-recreate` the container env was empty; (3) once the passthrough was added on the host, the next CI deploy scp'd a fresh `docker-compose.production.yml` from the repo (overwriting the hotfix) AND templated `.env` from scratch (wiping the value). Permanent fix required: passthrough line committed to all 3 repo compose variants, value placed in the deploy-appended `.env.kf` file, and `--force-recreate` to apply. Each missing layer was an independent silent failure.

## Source Context

[project] variance-tuning session, 2026-05-28. Added trusted-IP rate limit exemption for internal monitoring, discovered the multi-layer coordination issue during validation of the feature reaching production. Diagnostic process: verified env var exists in `.env` file → checked if it reached container → confirmed Layer 2 and Layer 3 gaps → fixed all three layers → tested with full deploy cycle.
