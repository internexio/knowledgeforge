---
title: A new GitHub Actions workflow runs but does not gate PR merges — branch protection must explicitly require the check
source_mode: direct
source_session: redacted
novelty_type: reusable_diagnostic + new_pattern
grounding_score: 0.9
staleness_risk: stable
importance: 5
pinned: false
created: 2026-06-20
domain: infrastructure
topic: ci-cd
tags: github-actions, branch-protection, ci-cd, code-review, automation, gotcha, status-checks, deployment, quality-gate
related_entries: ["infrastructure/2026-05-25_ci-auth-failure-workflow-diagnosis-before-chasing-local-state.md", "infrastructure/2026-05-25_github-pat-rotation-hygiene-verify-via-rerun.md", "infrastructure/2026-06-13_bundle-check-pre-commit-hook-ai-agents.md"]
---

# A new GitHub Actions workflow runs but does not gate PR merges — branch protection must explicitly require the check

## The Pattern (and how it fails silently)

You add a new GitHub Actions workflow as a quality gate — a regression check, lint enforcement, security scan, security audit, whatever. The workflow fires correctly on PR open, runs the check, exits with status 1 on failure. The PR shows a red X. You think the gate is in place. **It isn't.**

A PR that fails the check **can still be merged**. Branch protection rules — set separately under repo Settings → Branches — control which status checks actually BLOCK merge. A check that is not in that list shows red but does not gate. The merge button stays enabled. The PR can merge — manually by a reviewer, automatically via `gh pr merge --auto`, or instantly via web-UI bots / default-branch automation in the org.

The disconnect is structural: GitHub treats "workflow ran and reported a status" and "this status is required for merge" as two independent configurations. Adding the workflow YAML does the first. Only a branch-protection update does the second.

## Symptom — Concrete Instance (cos-twsy, 2026-06-20)

Lived through 2026-06-20 on internexio/cos. Exact trace:

1. Built `cos-twsy`: a `canonicalization-check.yml` workflow asserting 5 URL-canonicalization invariants. Two triggers: `pull_request` to master (file-system invariants only) and `workflow_run` post-deploy (full crawl).
2. Deployed to both internexio/cos (test remote) and SEMalytics/cos (prod remote) via standard `git push` to master.
3. Validated the `workflow_run` trigger end-to-end — fired correctly after Deploy-to-Production succeeded; ran in 60s; passed clean against live prod sitemap.
4. To validate the `pull_request` trigger, created `test/cos-twsy-pr-validation` branch with a deliberate violation (a flat `<name>.html` file in `site/`). Pushed. Opened PR #36 against master.
5. Workflow fired in 41s. Exited fail-status. PR check showed red X.
6. Tried to `gh pr close 36` → error: "Pull request internexio/cos#36 … can't be closed because it was already merged".
7. **Master now had the violation file** as commit `6911b66 Merge pull request #36 from internexio/test/cos-twsy-pr-validation` — a merge commit with parent links to the failing-check commit.

Auto-merge wasn't explicitly enabled in the `gh pr create` invocation. The merge happened because nothing prevented it. The failing check wasn't a *required* status check, so the merge button stayed live. Either a reviewer clicked it (unlikely — fresh PR, no comments) or some automation in the org executed the merge.

## The Fix

For each workflow you intend as a gate:

1. Open the repo's Settings → Branches
2. Add or edit the rule for the protected branch (e.g., `master`)
3. Enable "Require status checks to pass before merging"
4. **Add the workflow's job display name** to the required-checks list (e.g., `Pre-merge (file-system invariants only)` if that's the job's `name:` field — NOT the workflow filename)
5. Save

Workflow checks that don't appear in this list run but don't gate.

Concretely for cos-twsy this is bead `cos-9a54`:

```
location: https://github.com/internexio/cos/settings/branches
add to master rule:
  - Require status checks to pass before merging: ✓
  - Required checks: + "Pre-merge (file-system invariants only)"
```

Repeat on the production-side repo (SEMalytics/cos) for symmetry. Consider also enabling "Require linear history" or "Require a pull request before merging" if direct-to-master pushes could bypass the PR-trigger entirely.

## Detection Rule for Code Review

**When you create a new CI workflow as a quality gate, the deploy must include TWO things:**

1. The workflow YAML
2. The branch protection update making it a required status check

If you do only step 1, the gate exists in name only. The check runs, the check fails, and the PR merges anyway.

In a PR review of a new workflow, ask: "Is this also wired as a required status check?" If the PR author can't show the corresponding branch-protection change (or doesn't have the admin access to make it), surface that as a blocker before merge — or at minimum, file a follow-up bead pinned to the admin so it doesn't sit forgotten.

## Diagnostic — Did the workflow actually gate?

Cheap checks, in order:

1. **`gh api repos/{owner}/{repo}/branches/{branch}/protection/required_status_checks`** — returns the list of required check names. If empty / 404 / your workflow's job name not listed, the workflow does not gate.
2. **Open a deliberate-violation PR** — push a branch with a known failing case, open a PR, observe whether the merge button is enabled while the check is red. If you can merge with red X, no gate.
3. **Inspect a recent PR's merge timeline** — `gh pr view <num> --json statusCheckRollup,mergeable` — `mergeable: MERGEABLE` while a check has `conclusion: FAILURE` is the signature.

The validation trace from cos-twsy was actually a deliberate-violation PR (step 2) — and the auto-merge that resulted was itself the diagnostic signal that no gate existed.

## When This Doesn't Apply

- If the workflow's job already gates merges via some other mechanism (e.g., a GitHub App that explicitly auto-blocks failing checks, like Renovate's `automerge: false` enforcement), branch protection may be redundant.
- If the workflow is informational-only (lint hints, suggestions, code-coverage delta) you may WANT it to not block.
- Repos using ruleset-based protection (newer GitHub feature) follow the same model with a different UI: Rulesets → Required checks. The two-step "ship workflow + wire as required" structure is identical.

## Related Entries

- `infrastructure/2026-05-25_ci-auth-failure-workflow-diagnosis-before-chasing-local-state.md` — the OTHER mode of "workflow exists but doesn't do what you think" (auth failure invisibly red-Xing everything)
- `infrastructure/2026-05-25_github-pat-rotation-hygiene-verify-via-rerun.md` — companion CI hygiene pattern
- `infrastructure/2026-06-13_bundle-check-pre-commit-hook-ai-agents.md` — local-side guard analog (pre-commit hook), where the install step is also necessary or the hook is dead weight; mirrors the "ship the gate AND wire it" structural lesson

## Source Context

Extracted from cos-twsy PR-trigger validation on internexio/cos, 2026-06-20.

- Workflow file: `.github/workflows/canonicalization-check.yml` (shipped in commit 13c6878 → 0398cab fix)
- PR: https://github.com/internexio/cos/pull/36 ("test: cos-twsy PR-trigger validation (DO NOT MERGE)")
- Workflow run: 27883382696, conclusion `failure`, 41s
- PR result: auto-merged into master, merge commit `6911b66`
- Cleanup commit: `d18c2c2` (cherry-picked onto master, removed violation file)
- Followup bead: `cos-9a54` (P2) — operator action required to enable required-status-check at GitHub repo settings

The validation goal was to confirm the `pull_request` trigger fired correctly. It did — but in the process exposed that the trigger firing was never wired to actually block merge. Two-fix outcome: trigger works as designed, AND the structural lesson that "workflow ships" ≠ "workflow gates" must be encoded in every quality-gate deploy going forward.
