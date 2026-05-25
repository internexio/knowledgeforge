---
title: GitHub PAT rotation hygiene + verify-via-rerun
source_mode: builder
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-05-25
domain: infrastructure
topic: ci-cd
tags: deployment, api, quality-gate, grounding, scheduling
related_entries: ["infrastructure/2026-05-25_ci-auth-failure-workflow-diagnosis-before-chasing-local-state.md"]
---

# GitHub PAT Rotation Hygiene + Verify-via-Rerun

## The Procedure

When a GitHub PAT secret expires or is revoked, CI workflows that use it begin failing at the auth/checkout step. Restoring the system requires:

1. **Generate** a new token in GitHub UI (the `gh` CLI cannot create classic PATs for the authenticated user, and the user's `gh` auth may be broken anyway)
2. **Store** the new token as a repository secret
3. **Verify** by deterministically re-running a known-failed workflow

Steps 1 and 2 are mechanical; step 3 is where most people skip — they assume "the next push will exercise it" and end up debugging again when an unrelated push fails for a different reason hours later.

## Full Procedure (Verified 2026-05-25 in knowledgeforge-core)

### 1. Generate New PAT

GitHub → top-right avatar → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new (classic).

- **Name:** descriptive + date-stamped. Examples: `knowledgeforge-core-sync-2026-05`, `cos-prod-deploy-2026-Q2`. Future-you needs to know what it's for and when it was issued. "ci-token" is useless 6 months later.
- **Expiration:** 1 year is the common sweet spot. "No expiration" eliminates rotation burden but creates an audit/security risk. 30/60/90 days creates churn.
- **Scopes:** minimum needed. For cross-repo sync workflows, `repo` (full control of private repos) is usually right. Don't grant `admin:org` unless the workflow needs it.
- Click Generate. **COPY THE TOKEN IMMEDIATELY** — GitHub shows it once. If you lose the modal you regenerate from scratch.

### 2. Store as Repo Secret

Browser tab → target repo → Settings → Secrets and variables → Actions → find the secret name (or create new) → Update → paste → save.

`gh secret set <NAME>` from the CLI works if `gh` auth is clean, but in many setups the CLI auth is broken. Browser UI is the reliable path.

### 3. Verify via Rerun

```bash
# Find the most recent failed workflow
gh run list --status failure --limit 5

# Re-run by ID (no new push needed — uses existing git state)
gh run rerun <DATABASE_ID>

# Poll until completion
until [ "$(gh run list --limit 1 --json status -q '.[].status')" = "completed" ]; do sleep 5; done
gh run view <DATABASE_ID>
```

If conclusion is `success`, the secret is good. If still `failure`, the new token doesn't have the right scope OR you pasted the wrong value OR the secret name doesn't match what the workflow references.

Don't trust "next push will trigger it" — explicit re-run gives a clean test signal in 30–60 seconds without polluting commit history with a fake "test rotation" commit.

## When to Apply

- A CI workflow has been failing on auth ("Bad credentials," "401," "403") and you've identified an expired/revoked PAT as the cause
- Periodic rotation (every 6–12 months) even when nothing is broken
- Anytime a PAT may have been exposed (committed by accident, shared in a chat, etc.)

## Anti-Patterns

- **Naming tokens "test" or "github-actions"** — useless in 6 months. Name them with purpose + date.
- **Pasting the token into a commit comment or PR body** — public exposure, immediate revocation needed.
- **Skipping the verify step** — declares success based on "I think I did the steps right." Always re-run a failed workflow to confirm.
- **Generating tokens with broad scopes "just in case"** — increases blast radius if exposed. Audit scope when generating.
- **Letting a token expire without rotation calendar** — sets up the failure mode this entry exists to fix. Either use no-expiration tokens with strict scoping, OR set a calendar reminder 2 weeks before expiration.

## When NOT to Apply

- CI failure isn't auth-related (e.g., test failure, syntax error, network timeout to a non-GitHub service)
- The secret is a GitHub App credential, not a PAT (App credentials use different rotation procedures via the App settings page)
- The workflow uses `GITHUB_TOKEN` (the auto-provided per-job token) — that one is rotated automatically by GitHub and can't be manually rotated

## Related

- `wiki/infrastructure/2026-05-25_ci-auth-failure-workflow-diagnosis-before-chasing-local-state.md` — the diagnostic that identifies PAT auth as the cause in the first place

## Source Context

Extracted from knowledgeforge-core session mn6 (2026-05-25), post-Phase 1 hook landing. User experienced 6 days of CI auth failures caused by an expired PAT secret (`CORE_SYNC_TOKEN`). This entry captures the rotation + verification procedure applied to resolve it: generate new PAT with descriptive name, store via GitHub UI (not CLI), and deterministically verify via `gh run rerun` rather than assuming "next push will test it." Paired with the diagnostic entry (ci-auth-failure-workflow-diagnosis) to form a complete troubleshooting + remediation flow.
