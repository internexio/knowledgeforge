---
title: GitHub Actions PAT authentication failure modes — three distinct error signatures + continue-on-error UI masking
source_mode: debugger
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.88
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-07-08
domain: infrastructure
topic: ci-cd-automation
tags: github-actions, ci-cd, authentication, debugging, secrets, gotcha
related_entries: ["infrastructure/2026-05-25_github-pat-rotation-hygiene-verify-via-rerun.md", "infrastructure/2026-05-25_ci-auth-failure-workflow-diagnosis-before-chasing-local-state.md"]
---

# GitHub Actions PAT Authentication Failure Modes: Three Distinct Error Signatures

When a GitHub Actions workflow uses a PAT (Personal Access Token) via `actions/checkout@v4` or direct API calls, authentication failures produce three distinct error messages. Each points to a different root cause and fix.

## Error 1: Headers.append: "token ***" is an invalid header value

**Cause:** The PAT value in GitHub Secrets contains embedded whitespace (spaces, tabs, or newlines). GitHub Actions masks the value as `***` but the whitespace passes through to the HTTP header, which is invalid.

**Common source:** `pbpaste` on macOS copies with a trailing newline. Using `echo "token" | gh secret set` similarly appends `\n`.

**Fix:**
```bash
pbpaste | tr -d '[:space:]' | gh secret set PAT_SECRET --repo OWNER/REPO
# or
echo -n "ghp_actualtoken" | gh secret set PAT_SECRET --repo OWNER/REPO
```

**Grounding:** Observed in CI run 28905611186 (SEMalytics/cos). Fixed by re-setting the secret with whitespace stripped.

## Error 2: Bad credentials - https://docs.github.com/rest

**Cause:** The token value is syntactically valid (no whitespace, correct format) but GitHub's API rejects it. Typical reasons:
- Token was revoked or expired since it was created
- Wrong token was copied to clipboard and set as the secret
- Fine-grained PAT was created under the wrong organization/owner (e.g., personal account instead of org)
- Token doesn't have sufficient permissions for the target repo

**Distinguishing feature:** The checkout step may still show ✓ in the GitHub Actions UI (see masking behavior below) but the repo is empty.

**Fix:** Create a new fine-grained PAT with correct owner + repo + read permission, set cleanly.

**Grounding:** Observed in CI runs 28907771276 and 28908485041 (SEMalytics/cos) after whitespace was fixed.

## Error 3: Input required and not supplied: token

**Cause:** The secret referenced by `${{ secrets.SECRET_NAME }}` doesn't exist in that repo's secret store. Secrets are repo-scoped — adding to `repo-A` does NOT make it available in `repo-B`.

**Fix:** Add the secret to the correct repository. For multi-repo setups (e.g., `internexio/cos` test repo and `SEMalytics/cos` prod repo), secrets must be added to EACH repo that needs them.

**Grounding:** Observed in an earlier CI run when SEMALYTICS_ADS_PAT was set on internexio/cos but the workflow ran from SEMalytics/cos.

## continue-on-error: true UI Masking Behavior

When a step has `continue-on-error: true`, GitHub Actions displays the step with a **green ✓ checkmark** even when it fails (exits non-zero). The failure is only visible in:
- The "Annotations" section at the bottom of the run view (shows `X Process completed with exit code N`)
- The raw step logs (`gh run view --log --job=ID`)

**Diagnostic implication:** A step showing ✓ in the GitHub Actions web UI does NOT guarantee it succeeded when `continue-on-error: true` is present. Always check annotations and logs for these steps when debugging downstream failures.

**Grounding:** Observed in runs 28907771276 and 28908485041 where "Checkout client-project ✓" appeared in the UI but the checkout had failed with "Bad credentials."

## Decision Tree for Diagnosing PAT Failures

```
Checkout step fails or shows anomaly?
├─ Step shows ✗ (red X)?
│   ├─ "Input required and not supplied" → secret missing from this repo
│   ├─ "Headers.append: invalid header value" → whitespace in secret value
│   └─ "Bad credentials" → token wrong/expired/wrong-org
└─ Step shows ✓ but downstream fails with "No such file or directory"?
    ├─ Check annotations for "Process completed with exit code 23" → continue-on-error masked failure
    └─ Check step logs for "Bad credentials" → PAT auth failed silently
```

## When This Applies

- Using `actions/checkout@v4` with a PAT via `token:` parameter
- Using `actions/checkout@v3` or earlier versions (similar behavior)
- Any GitHub Actions step making direct API calls with a PAT (REST API auth, GraphQL queries)
- Cross-repo workflows that reference secrets from a different repository's secret store
- Workflows using `continue-on-error: true` on steps that rely on PAT authentication

## When This Does NOT Apply

- Using `GITHUB_TOKEN` (auto-generated per-run, never has these issues)
- Using SSH deploy keys (different auth path entirely)
- The error is in a `run:` step making direct API calls with a PAT (similar signatures, but different tooling)
- The checkout step shows ✗ and the error message is clearly non-auth (e.g., "Repository not found" when the repo definitely exists and is private)

## Source Context

Surfaced during COS CI/CD debugging on 2026-07-08 (session `[project]-ci-ads-deploy-2026-07-08`). Multi-step troubleshooting of checkout failures across internexio/cos (test) and SEMalytics/cos (prod) repositories revealed three distinct failure modes and the UI masking behavior when `continue-on-error: true` was present. Related to but distinct from the PAT rotation procedure and CI auth failure diagnosis entries — this entry focuses on the granular error taxonomy and masking behavior.
