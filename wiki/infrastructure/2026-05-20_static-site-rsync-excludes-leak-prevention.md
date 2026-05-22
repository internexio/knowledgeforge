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
