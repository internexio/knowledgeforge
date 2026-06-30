---
title: Static-site rsync excludes — internal-artifact leak prevention
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.95
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-20
tags: rsync, static-site, deploy, security, leak-prevention, infrastructure
related_entries:
  - infrastructure/2026-05-18_editable-venv-mcp-server-installation.md
  - diagnostics/2026-05-18_http-status-signatures-deploy-verification-smoke-test.md
  - methodologies/2026-05-20_propagation-gap-addenda-propose-downstream-changes-that-dont-execute.md
---

# Static-site rsync excludes — internal-artifact leak prevention

When a static-site source directory holds **both public content and internal-only artifacts** (drafts, audit scripts, keyword research, audit results, backup files), the canonical rsync deploy command must explicitly exclude each category. A minimal `--exclude='*.bak'` is not sufficient. Real-world leakage surfaces are broader than backup files.

## The leak signature (from 2026-05-20 cos/site deploy)

After a routine `rsync -avz --exclude='*.bak' --exclude='blog/' site/ host:/var/www/`, prod was publicly serving (all returned HTTP 200):

| Path on prod | Type | Sensitivity |
|---|---|---|
| `seo-research/seo-audit-page-draft-v1.md` → `v3.md` | Internal drafts with COS scores | High |
| `seo-research/kwp-seo-audit-page-2026-05-18.csv` | Paid Google Ads keyword data | High (vendor data) |
| `seo-research/check-keywords-seo-audit-page.py` | Internal script | Medium |
| `seo-research/site-audit-2026-03-29.md` | Site audit with internal findings | High |
| `dogfood-audit.py` + `dogfood-results.json` | Internal audit script + output | High |
| `seo-keywords.md` | Internal keyword tracking by page | High (competitive intel) |
| `*.html.bak` (3 files) | Backup snapshots | Low |
| `llms.txt.backup-2026-05-15` | Backup with non-`.bak` suffix | Low |

The `*.bak` exclude didn't catch `llms.txt.backup-2026-05-15` because the backup convention used a different suffix.

## The canonical pattern — broader rsync excludes

```bash
rsync -avz \
  --exclude='*.bak' \
  --exclude='blog/' \
  --exclude='seo-research/' \
  --exclude='dogfood-*.py' \
  --exclude='dogfood-*.json' \
  --exclude='seo-keywords.md' \
  --exclude='llms.txt.backup-*' \
  site/ host:/var/www/
```

## General principle (transferable to other static sites)

A static-site source tree has at least four distinct artifact classes — only the first should be deployed:

1. **Public content** (`*.html`, `css/`, `js/`, `images/`) — deploy
2. **Backups** (`*.bak`, `*.backup-*`, `*~`) — NEVER deploy
3. **Internal research** (`research/`, `drafts/`, `*.md` notes, CSV exports from paid APIs) — NEVER deploy
4. **Dev scripts** (`*.py` audit/dogfood scripts, `*.json` outputs) — NEVER deploy

Excludes need to cover all of classes 2-4. Naming conventions for backups should be standardized (`*.bak` only) to keep the exclude list short.

## Detection method (post-deploy audit)

After any bulk rsync, run a public-accessibility check on suspicious paths:

```bash
for path in <suspicious-paths>; do
  echo "$path: $(curl -sS -o /dev/null -w '%{http_code}' https://yoursite.com/$path)"
done
```

`200` = leaked. `404` = safe. The verbose output of rsync itself (`-v`) lists files transferred — scan for non-HTML/CSS/JS extensions.

## Cleanup pattern

When leakage is discovered, server-side removal is fast (`ssh host "rm -f /var/www/<path>"`) but the file remains in CDN caches (~24h) and search-engine indexes (~weeks). For high-sensitivity leaks (API tokens, internal financial data), assume content was harvested.

## When This Applies

- Static-site source directory contains mixed public content and internal artifacts
- Deployment is via rsync to a production web server
- Internal artifacts include research, drafts, scripts, or audit outputs
- Backup convention is variable (some files use `.bak`, others use `.backup-*` suffixes)
- Post-deploy public-accessibility audits are routine

## When This Does NOT Apply

- Pure-public static sites (e.g., a blog with no internal artifacts in the source tree) — `rsync --delete` with no excludes is fine.
- Build-output deploys (e.g., Vite/Webpack `dist/` directory) — the build step already filtered to public artifacts.
- Deployment via containerized image (Docker image build + push) — the build layer separation enforces isolation.

## Source Context

Discovered during 2026-05-20 COS static-site SEO audit cleanup. Post-deploy verification found internal research, audit scripts, and keyword data publicly accessible via HTTP 200 responses. Commit `8fcba05` — docs: expand rsync excludes to prevent internal-artifact deploy — records the remediation.

---

## Addendum 2026-06-18 — CI workflow drift + `--delete-excluded` self-healing (cos-yh03)

Two refinements from the June 2026 recurrence on the same `site/` tree, this time on the GitHub Actions deploy path rather than the manual rsync recipe.

### Refinement 1 — `--delete` alone does NOT clean previously-shipped excluded files

`rsync --delete --exclude='X'` removes destination files **not present in source**. Excluded files are out of scope from rsync's perspective entirely — not "missing from source." So if `X` already exists on the destination from a prior deploy, adding `X` to the exclude list on a later run will NOT remove it. The file persists until something explicitly deletes it.

The self-healing variant is `--delete-excluded`:

```bash
rsync -avz --delete --delete-excluded \
  --exclude='seo-research/' \
  --exclude='dogfood-*.py' \
  --exclude='*.backup-*' \
  site/ user@host:/var/www/example.com/
```

With this flag, the next deploy after adding a new exclude pattern cleans those files from the destination automatically. Subsequent deploys remain self-healing for any future exclude additions.

**Caveat.** `--delete-excluded` will also wipe manually-uploaded files matching the exclude pattern. If operators paste files directly into the destination for ad-hoc reasons, this is a behavior change worth flagging before flipping the switch.

**One-time cleanup of already-leaked files.** Once `--delete-excluded` is in the CI workflow, the next deploy removes them automatically. If immediate removal is required (sensitive URLs, credentials), SSH-delete first, then verify HTTP 404 — don't trust "next deploy will fix it" if content is active liability.

### Refinement 2 — Docs/CI workflow drift is the actual leak source

The 2026-05-20 fix expanded the **manual rsync recipe** in `site/DEPLOY.md` to include the broader exclude list above. But the CI workflows (`deploy-testing.yml`, `deploy-production.yml`) were never updated — they still rsync'd `site/` with minimal excludes (`cos/`, `blog/`, `.gitignore`, `*.bak`). So every CI deploy continued to ship the internal artifacts that the manual recipe explicitly excluded. The docs change became shelfware.

**Pattern.** When two surfaces describe "how to deploy" — a docs file and a CI workflow — the CI workflow IS the deployed behavior. The docs version is irrelevant if it's not the path that actually runs in production. Reconcile both, or single-source one from the other (e.g. docs reference the workflow's exclude list, or the workflow `source`s the docs version).

### Refinement 3 — Detection variant for CI-deployed surfaces

For projects where the source tree is large enough that manual review of `git ls-files` is impractical, narrow the search with naming-convention heuristics:

```bash
git ls-files <site-dir>/ | grep -iE '(internal|backup|audit|research|draft|keywords|dogfood)'
```

Then verify which are HTTP-reachable with the existing curl loop. Pair both — naming convention catches what excludes miss, HTTP probe catches what naming misses.

### Grounding (addendum)

June 2026 [project] recurrence. Both GitHub Actions workflows shipped 16+ tracked internal files (`llms.txt.backup-2026-05-15` — which leaked a URL the team had just removed from the canonical file — plus `seo-keywords.md`, `seo-research/*.{csv,md,py}`, `dogfood-*.py/json`). Fix shipped: expanded both workflow exclude lists to mirror the manual rsync recipe, added `--delete-excluded` to both, SSH-deleted the already-leaked files. Verified 7 sample URLs returned HTTP 404 post-cleanup while real content continued to serve HTTP 200.
