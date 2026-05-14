---
title: docker compose down/up container-name race in deploy scripts
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.65
staleness_risk: slow_decay
importance: 2
pinned: false
created: 2026-05-13
tags: docker, deployment, race-condition, infrastructure, ci-cd, sre
related_entries: []
---

# docker compose down/up container-name race in deploy scripts

A real, intermittent failure mode in deploy scripts that run `docker compose down` followed immediately by `docker compose up -d`. The previous container's name doesn't always release in time for the new create, and `up` fails with:

```
Error response from daemon: Conflict. The container name "/cos-backend-1" is already in use by container "02be9bec...".
You have to remove (or rename) that container to be able to reuse that name.
```

## When it happens

Observed on a GitHub Actions deploy workflow targeting a DigitalOcean host (cos-prod) running `docker compose` v2.x. The deploy script:

```bash
docker compose down
docker compose pull
docker compose up -d
```

Out of ~6 rapid-fire deploys in a 20-minute window (each commit triggered a deploy, no concurrency control), one of them failed with the conflict error. The next deploy in the queue succeeded and brought the service back to healthy state.

## Why it self-heals

Each subsequent deploy starts with another `docker compose down` which DOES successfully remove the lingering container (because by then the previous run's stale container reference has fully cleared). So the failure mode is intermittent and recovery is automatic — as long as another deploy lands soon.

## Why it's nonetheless worth fixing

- Failed run shows red in CI which causes alert fatigue
- The conflict can leave the service in a half-down state for the duration of the gap until the next deploy
- If the failed deploy IS the last deploy (no queued retry), production stays degraded until manual intervention
- Concurrent deploys (multiple commits pushed in close succession) amplify the race window

## Fixes

In rough order of effort:

### 1. Add `--remove-orphans` to the down call

```bash
docker compose down --remove-orphans
```

Cleans up stale containers that escaped the compose project's tracking.

### 2. Explicit force-remove fallback

```bash
docker compose down --remove-orphans
docker rm -f $(docker ps -aq --filter "name=cos-") 2>/dev/null || true
docker compose up -d
```

Aggressive, but eliminates the race entirely.

### 3. Retry-on-conflict

Wrap `docker compose up -d` in a retry that sleeps 5s and re-tries once on conflict-class errors.

### 4. GitHub Actions concurrency group

Prevent overlapping deploys to the same environment by adding `concurrency: { group: production-deploy, cancel-in-progress: false }` to the workflow. Forces queueing and a clean state between deploys.

## When this applies

- Compose-based deploy scripts on Linux hosts
- High-churn periods (chained commits, hotfix flurries)
- Any orchestration that does `down → up` without intermediate cleanup
- Especially: deploys that share a `restart_policy` of `unless-stopped` or `always` — the policy can interfere with the down's cleanup timing

## When this does NOT apply

- `docker compose up -d` alone without prior `down` — uses recreate logic which is race-free
- Kubernetes-style deploys (different lifecycle model)
- Single-container `docker run` patterns

## Source Context

Observed during the semalytics.com/cos production deploy on 2026-05-13. Commit `6434481` (BrandVoiceSection extraction) failed in CI with the conflict error around 20:11 UTC. The next deploy (`ac3533b` Personas) succeeded and brought production back to healthy on its first attempt. Production was never down — the previous deploy's containers remained running during the failed deploy's `up` attempt — but the failure was real and shows as a red mark in the GitHub Actions deploy history.
