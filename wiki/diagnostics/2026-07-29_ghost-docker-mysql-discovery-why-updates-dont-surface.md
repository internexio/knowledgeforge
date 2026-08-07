---
title: Ghost CMS Docker MySQL discovery — diagnosing why MySQL updates don't surface
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-07-29
domain: diagnostics
topic: server-configuration
tags: [deployment, empirical, grounding]
related_entries: ["infrastructure/2026-05-28_docker-compose-env-vars-three-coordinated-layers.md", "diagnostics/2026-07-27_ghost-admin-api-key-discovery-sqlite-when-unknown.md", "infrastructure/2026-07-24_ghost-active-theme-verification-before-ssh-edits.md"]
---

# Ghost CMS Docker MySQL Discovery — Diagnosing Why MySQL Updates Don't Surface

## Symptom

You update a Ghost CMS setting (e.g., `codeinjection_head`) directly in MySQL, restart the Ghost service via systemd (`systemctl restart ghost_*`), and the change still doesn't appear in the Content API or live pages.

## Root Cause Pattern

Ghost may be running **inside a Docker container** that has its **own MySQL container** — completely separate from the host MySQL instance. Common setup:

```
Host machine
├── MySQL (PID on host, 127.0.0.1:3306)   ← you updated this — WRONG
└── Docker
    ├── ghost-ghost-1                       ← actual Ghost process
    │   └── connects to host: "mysql"
    └── ghost-mysql-1                       ← actual Ghost database
        └── 3306/tcp (internal Docker network only, NOT bound to host)
```

Systemd services like `ghost_test-semalytics-com` may be **unrelated orphan services** that crash-loop with `EADDRINUSE` because the Docker Ghost already owns the port.

## Discovery Procedure

```bash
# Step 1: Who is actually listening on Ghost's port?
lsof -i :2368 -P -n
# If output shows "docker-pr" (docker-proxy): Ghost is containerized.
# If output shows "node": Ghost is running natively.

# Step 2: Find the Ghost container
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}'
# Look for: ghost-ghost-1 (ghost:X-alpine), port 127.0.0.1:2368->2368/tcp

# Step 3: Find the actual database
docker inspect ghost-ghost-1 | python3 -c "
import json, sys
c = json.load(sys.stdin)[0]
env = c['Config']['Env']
[print(e) for e in env if any(k in e for k in ['database','DB','MYSQL','mysql','url'])]
"
# Output will show:
#   database__connection__host=mysql         ← container hostname, NOT localhost
#   database__connection__user=ghost
#   database__connection__password=<differs from host MySQL password>
#   database__connection__database=ghost_production
```

## Updating the Correct Database

Once you've confirmed Ghost uses `ghost-mysql-1`:

```bash
# Verify current value
docker cp /tmp/check.sql ghost-mysql-1:/tmp/check.sql
docker exec ghost-mysql-1 bash -c \
  "mysql -u ghost -p<password> ghost_production < /tmp/check.sql 2>&1"

# Apply update (use UNHEX for complex values — see companion pattern)
docker cp /tmp/update.sql ghost-mysql-1:/tmp/update.sql
docker exec ghost-mysql-1 bash -c \
  "mysql -u ghost -p<password> ghost_production < /tmp/update.sql 2>&1"

# Restart Ghost to load the new settings
docker restart ghost-ghost-1
sleep 10  # Ghost takes ~10s to fully initialize
```

## Verifying the Restart

Ghost's container port is only accessible via the host's localhost proxy. Verify via the **public URL** or check container logs:

```bash
docker logs ghost-ghost-1 --tail 20
# Look for: "URL Service ready" and 200 response log lines
# Ghost takes longer to initialize than systemd reports — wait for log activity
```

**Note:** After restart, Ghost may briefly return 404 on `http://localhost:2368/` because it redirects all traffic to its configured `url` (e.g., `https://semalytics.com/blog`). A 301 redirect is a sign Ghost is running — not an error.

## Ghost Theme Files — Same Trap

Ghost content themes are NOT served from `/var/www/ghost/content/themes/` on the host. The actual content volume is Docker-mounted:

```bash
docker inspect ghost-ghost-1 | python3 -c "
import json, sys
c = json.load(sys.stdin)[0]
[print(m['Source'], '->', m['Destination']) for m in c['Mounts']]
"
# Example: /opt/ghost/data/ghost -> /var/lib/ghost/content
```

Edits to `/var/www/ghost/` are dead — the running container never reads them.

## Key Differentiators

| Signal | Host Ghost | Containerized Ghost |
|--------|-----------|-------------------|
| `lsof -i :2368` shows | `node` process | `docker-proxy` process |
| Systemd service `ghost_*` | manages Ghost | crash-loops (EADDRINUSE) |
| MySQL password | in Ghost config file | in `docker inspect` env |
| MySQL host | `localhost` | `mysql` (container hostname) |
| Themes path | `/var/www/ghost/content/themes/` | `/opt/ghost/data/ghost/themes/` (or similar volume mount) |

## When This Applies

- Any Ghost installation where port 2368 is managed by docker-proxy (confirmed via `lsof -i :2368`)
- MySQL updates not reflected after systemd service restart
- Ghost configuration changes appearing to have no effect
- Theme or setting edits that don't surface on the live site
- Troubleshooting why a systemd `ghost_*` service crashes with `EADDRINUSE`

## When This Does NOT Apply

- Ghost running natively on the host (confirmed by `lsof -i :2368` showing `node` process)
- Ghost (Pro) managed hosting (no Docker container access)
- Settings changed through the Ghost Admin UI (UI handles database routing automatically)
- Theme edits applied through Ghost's admin theme editor (not filesystem-based)

## Source Context

Verified 2026-07-29 on cos-prod (64.23.248.230, Ubuntu, Ghost 6.22.0 in Docker, MySQL in separate container). Previous session spent hours updating host MySQL (`wMKEkMzyDMZUj8N0xMEY5Day` credentials) and restarting `ghost_test-semalytics-com` systemd service — both completely ineffective. Actual Ghost uses `ghost-mysql-1` container (password `fb9fd...`) and is managed by Docker Compose, not systemd. Discovered via `lsof -i :2368` showing `docker-proxy`, then `docker inspect ghost-ghost-1` to inspect environment and mounts. Fix took ~5 minutes once root cause found. Grounding: full discovery + fix cycle completed; verified database change reflected in live API responses immediately after Docker restart.
