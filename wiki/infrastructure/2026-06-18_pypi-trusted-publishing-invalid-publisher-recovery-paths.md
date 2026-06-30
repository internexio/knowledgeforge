---
title: PyPI trusted-publishing fails silently with `invalid-publisher` — three recovery paths (configure publisher, convert to token, manual twine)
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.85
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-06-18
domain: infrastructure
topic: ci-cd
tags: github-actions, pypi, python-packaging, oidc, trusted-publishing, deployment
related_entries: ["infrastructure/2026-05-25_github-pat-rotation-hygiene-verify-via-rerun.md", "infrastructure/2026-05-25_ci-auth-failure-workflow-diagnosis-before-chasing-local-state.md"]
---

# PyPI Trusted-Publishing Fails Silently with `invalid-publisher`

## Symptom

A GitHub Actions workflow using `pypa/gh-action-pypi-publish@release/v1` with `permissions: id-token: write` + `environment: pypi` fails at the OIDC exchange step (~20s into the run, fast failure) with:

```
##[error]Trusted publishing exchange failure:
Token request failed: the server refused the request:
* `invalid-publisher`: valid token, but no corresponding publisher
  (Publisher with matching claims was not found)
```

The error payload includes a debug dump of the OIDC claims (`sub`, `repository`, `workflow_ref`, `environment`, `repository_owner`). **These are NOT what to configure — they are what was *presented* and didn't match** an entry on the PyPI side.

## Root Cause

PyPI's trusted publisher is configured **per-project at `https://pypi.org/manage/project/<NAME>/settings/publishing/`**, NOT in the GitHub repo or workflow file. The workflow can be wired correctly for trusted publishing while PyPI side has no matching entry. Common ways this happens:

- Workflow was written aspirationally but PyPI was never actually configured
- Project was forked or migrated between orgs (claims now name a different `repository` than the publisher entry)
- Trusted publisher was deleted or expired

**The same tag pushed to a different remote/repo will fail too**, since each repo presents a different `repository` claim. Pushing `mcp-v0.3.1` to `internexio/cos` after it failed on `SEMalytics/cos` produced an identical failure with the only difference being `repository: internexio/cos` vs `SEMalytics/cos`.

## Three Recovery Paths

### Path 1: Configure trusted publisher on PyPI (sustainable, OIDC stays)

Matches workflow as-written; no long-lived token in repo secrets.

1. Sign in to PyPI as project maintainer
2. Project settings → Publishing → Add a Trusted Publisher
3. Fill in **using the claims dumped by the failed run**:
   - Owner: `<GitHub org>` (matches `repository_owner`)
   - Repository: `<repo>` (matches `repository`)
   - Workflow filename: `<workflow.yml>` (matches the basename of `workflow_ref`)
   - Environment: `<env name>` (matches the environment in `sub`)
4. Re-run the failed workflow (`gh run rerun <id>` — no new commit needed)

### Path 2: Convert workflow back to token-based publish (durable fix without PyPI access)

Matches historical pattern. Use when you can't reach PyPI settings, or when the workflow is one of many and you don't want per-project OIDC bookkeeping.

- Remove `permissions: id-token: write` and the `environment: pypi` block
- Add `twine` to the pip install step
- Replace the `pypa/gh-action-pypi-publish` step with:

  ```yaml
  - name: Publish to PyPI
    env:
      TWINE_USERNAME: __token__
      TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
    working-directory: <package-dir>
    run: twine upload dist/*
  ```

- Add `PYPI_API_TOKEN` to repo Settings → Secrets → Actions. Value = a **project-scoped** PyPI API token in `pypi-...` format (200+ chars). CLI add (keeps token out of shell history):

  ```bash
  gh secret set PYPI_API_TOKEN --repo <owner>/<repo>
  # paste token, press Ctrl-D
  ```

### Path 3: Ship the current release manually (escape hatch)

Useful when the failure surfaces mid-deploy and you need the release out NOW. Workflow conversion can follow.

```bash
cd <package-dir>
python -m build
twine upload dist/*  # uses ~/.pypirc token
```

Requires a working `~/.pypirc` with a project-scoped token. After the release is out, apply Path 1 or Path 2 as the durable fix.

## When to Apply Which Path

- **Path 1** — default. OIDC is more secure than long-lived tokens. Use this unless you have a specific reason to avoid PyPI settings access.
- **Path 2** — when you can't access PyPI settings, OR when you're standardizing many projects on the same secret-based pattern and want one rotation point.
- **Path 3** — escape hatch only. Combine with Path 1 or Path 2 for the durable fix.

## When NOT to Apply

- Trusted publishing IS correctly configured (claims in error dump match a publisher entry exactly) — the failure is somewhere else (network, PyPI outage, malformed dist artifacts). Check `gh run view --log-failed` for context AFTER the OIDC exchange step.
- Test-PyPI vs production PyPI mismatch — `test.pypi.org` and `pypi.org` are separate publisher registries. A test-PyPI publisher does not authorize a prod-PyPI push.

## Anti-Patterns

- **Reading the OIDC claim dump as configuration to apply on GitHub.** The dump is what was presented, not what's missing. The missing piece is the PyPI-side publisher entry. New users routinely try to "fix" the `sub` claim in the workflow — there's nothing to fix.
- **Repeatedly pushing the same tag to different remotes hoping one works.** Each repo presents a different `repository` claim; if PyPI doesn't know about any of them, all fail identically.
- **Recommending Path 2 over Path 1 by default.** Long-lived tokens are weaker than OIDC. Prefer Path 1 unless context says otherwise.

## Related

- `infrastructure/2026-05-25_github-pat-rotation-hygiene-verify-via-rerun.md` — the rotation procedure for the `PYPI_API_TOKEN` secret introduced in Path 2
- `infrastructure/2026-05-25_ci-auth-failure-workflow-diagnosis-before-chasing-local-state.md` — diagnostic for "deploy keeps failing" symptoms that masquerade as code drift

## Source Context

Lived through this exact failure on `SEMalytics/cos`'s `publish-pypi.yml` for `cos-mcp` v0.3.1 in June 2026. OIDC claims dumped by the failed run: `sub=repo:SEMalytics/cos:environment:pypi`, `workflow_ref=SEMalytics/cos/.github/workflows/publish-pypi.yml@refs/tags/mcp-v0.3.1`. Pushing the same tag to `internexio/cos` reproduced the failure with `repository=internexio/cos` — proving the failure is PyPI-side, not GitHub-side. Recovery via Path 3 (local twine, `~/.pypirc` token) succeeded immediately; Path 2 (workflow conversion + repo-secret) was applied as the durable fix for next release.
