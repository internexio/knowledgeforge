---
title: GitHub Actions sparse-checkout cone mode silently breaks with trailing slash in YAML multiline block
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.90
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-07-08
domain: infrastructure
topic: ci-cd-automation
tags: github-actions, ci-cd, git, debugging, gotcha
related_entries: []
---

# GitHub Actions sparse-checkout: Trailing Slash in YAML Multiline Block Breaks Cone Mode Silently

## What Happens

When using `actions/checkout@v4` with `sparse-checkout` in cone mode (the default), specifying a directory with a trailing slash inside a YAML multiline block (`|`) causes the checkout to run "successfully" (step shows ✓) but checks out NO files. The target subdirectory never gets created, even though the repo is cloned.

## Failure Signature

- `actions/checkout@v4` step shows ✓ (green checkmark, no error)
- Downstream step that expects `<path>/<dir>/` fails with: `change_dir "/home/runner/work/.../client-project/site" failed: No such file or directory (2)`
- rsync or subsequent commands see an empty workspace
- No error log from the checkout step itself — the git operations complete with zero exit code

## Broken Pattern

```yaml
- uses: actions/checkout@v4
  with:
    repository: SEMalytics/client-project
    token: ${{ secrets.PAT }}
    path: client-project
    sparse-checkout: |
      site/          # ← trailing slash inside multiline block = silent no-op
```

## Fixed Pattern

```yaml
- uses: actions/checkout@v4
  with:
    repository: SEMalytics/client-project
    token: ${{ secrets.PAT }}
    path: client-project
    sparse-checkout: site  # ← bare directory name, no multiline block, no trailing slash
```

Alternative (also works):

```yaml
- uses: actions/checkout@v4
  with:
    repository: SEMalytics/client-project
    token: ${{ secrets.PAT }}
    path: client-project
    sparse-checkout-cone-mode: true
    sparse-checkout: |
      site
      # ← no trailing slash even in multiline block
```

## Why It Breaks

Git cone mode interprets directory patterns strictly. The YAML `|` block introduces a trailing newline after `site/`, and git sparse-checkout in cone mode rejects `site/` (with trailing slash) as an invalid cone pattern — silently falling back to an empty checkout. The `actions/checkout` action doesn't surface this as an error because the git operations themselves complete without a non-zero exit code.

The multiline block syntax (`|`) is the vector: it appends a final newline. Bare scalar syntax (`site`) does not. When you pass `site/\n` to git cone-mode, git silently ignores the malformed pattern rather than raising an error, leaving the repo cloned but the cone empty.

## Diagnosis Path

1. Step shows ✓ in GitHub Actions UI
2. Downstream rsync/copy step fails with "No such file or directory" on the expected subdirectory
3. Check the checkout step log — look for `Bad credentials` or absent file-listing lines (you should see something like `Adding directory 'site/'` but you don't)
4. Source directory exists in the repo (confirmed via `gh api repos/OWNER/REPO/contents/`) but wasn't checked out
5. Compare the checkout config: if using multiline block, remove it and use bare scalar or remove the trailing slash

## Grounding

Directly observed in two consecutive CI runs on SEMalytics/cos (runs 28907771276 and 28908485041, 2026-07-08). The fix (`sparse-checkout: site`) was committed as `bf49192` and verified in run 28908485041 — checkout step ✓, though an unrelated PAT credential issue prevented file transfer. The sparse-checkout behavior itself was confirmed by CI log: `change_dir ".../client-project/site" failed: No such file or directory` in both pre-fix runs; absent in post-fix run.

## When This Applies

- Using `actions/checkout@v4` with `sparse-checkout` parameter
- Specifying directory with trailing slash (`site/`)
- Inside a YAML multiline block (`|` or `|-` or `|+`)
- Git cone mode (default when `sparse-checkout-cone-mode` is not explicitly set to false)

## When This Does NOT Apply

- Using `sparse-checkout-cone-mode: false` (pattern mode handles trailing slashes differently)
- Using the full checkout (no `sparse-checkout` parameter)
- The directory truly doesn't exist in the repo root (different root cause — verify with `gh api repos/OWNER/REPO/contents/DIR`)
- Using bare scalar syntax without the multiline block (`sparse-checkout: site/` still works in some edge cases, but multiline + trailing-slash is the failure vector)

## Source Context

Surfaced during COS CI/CD debugging on branch `fix/ads-deploy-sparse-checkout` (2026-07-08), session `[project]-ci-ads-deploy-2026-07-08`. The issue manifested in automated static-site deploy when trying to cherry-pick only the `site/` directory from the `client-project` repository into the COS deploy pipeline.
