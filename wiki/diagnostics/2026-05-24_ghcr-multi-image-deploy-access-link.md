---
title: GHCR multi-image deploy — package-to-repo Actions access link
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-24
tags: ghcr, github-actions, devops, deployment, ci-cd, docker, permissions
related_entries: []
domain: diagnostics
topic: ops
---

# GHCR Multi-Image Deploy — Package-to-Repo Actions Access Link

## Problem Signature

A GitHub Actions workflow pulls multiple private GHCR images from the same owner namespace (e.g. `ghcr.io/internexio/cos/frontend`, `ghcr.io/internexio/cos/backend`, `ghcr.io/internexio/cos/mcp`) and one image — typically the most recently added — fails with `error from registry: denied` while the others pull cleanly. The Build job that pushed the image succeeded; the Deploy job using the same `GITHUB_TOKEN` and same registry login pulls the older images but not the new one.

## Root Cause

GHCR packages created by a workflow's first push are **private and user-scoped** (owned by the repo OWNER user, not the repo itself). The repo's `GITHUB_TOKEN` only has read access to packages that have been explicitly **linked to that repository** via the package's "Manage Actions access" setting.

Older images in the same namespace were linked when first created (or while the package settings UI was simpler); newer images get the GitHub default of "no repo links", and inherit no access.

**Critical:** Repo admin permissions do **not** grant package access. A user with admin on the consuming repo still cannot pull a user-owned private package unless the package is explicitly linked. The repo and the user namespace are separate authorization boundaries on GitHub.

## Diagnostic Chain

1. **Confirm the symptom:** One specific image denies, others in same registry/owner work.

2. **Probe image visibility anonymously:**
   ```bash
   for pkg in frontend backend mcp; do
     printf "%-10s " "$pkg"
     curl -sI "https://ghcr.io/v2/$OWNER/$REPO/$pkg/manifests/$TAG" | head -1
   done
   ```
   If all return `HTTP/2 401`, visibility is private across all — that rules out a visibility-only difference.

3. **Check Actions-access linkage:** Visit the package settings:
   ```
   https://github.com/users/$OWNER/packages/container/$REPO%2F$PKG/settings
   ```
   Compare "Manage Actions access" section across the working and broken packages. Missing entries on the broken one confirm the diagnosis.

## Fix

1. Open the package settings URL above for the failing package.
2. Scroll to "Manage Actions access" → click "Add Repository".
3. Select the consuming repo with role **Write** (Write lets the Build job push and supersedes Read, which only lets Deploy pull).
4. Save.
5. Re-trigger the failed workflow run. **No code change required.**

## When This Applies

- Multi-image GHCR deploys from a single repo, especially when a new image is added late.
- Migrations from "all images public" to mixed visibility (new image inherits private default).
- Cross-repo setups where Repo A builds an image and Repo B consumes it.
- Token rotation or permission audit producing different access per image (a leading indicator of unlinked packages).

## When This Does NOT Apply

- Single-image deploys (the original push from the consuming repo always has access).
- Org-owned packages with org-level permission grants (different authorization model).
- Public packages (anonymous pulls work regardless of repo linkage).

## Recognition Signal for Future Sessions

If a workflow log shows:
- "Build: success" for all images
- "Deploy: success" for some images
- "denied" for only the newest image

...the diagnosis is **package-link config**, not workflow code. Do not modify the workflow YAML. Do not rotate tokens. Do not chase repo permission changes.

## Source Context

[project] session 2026-05-23 (cos-fby). Verified by:
- Anonymous HTTP HEAD probe on all 3 images returned HTTP 401 (visibility not the cause).
- After Write access grant via the package settings UI, the previously-failing run rerun succeeded with no other change.
