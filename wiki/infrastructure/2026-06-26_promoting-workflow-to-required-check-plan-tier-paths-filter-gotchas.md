---
title: Promoting a GitHub workflow to a required status check (plan-tier + paths-filter gotchas)
source_mode: debugger
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-06-26
domain: infrastructure
topic: ci-cd
tags: github, ci-cd, branch-protection, workflows, required-status-check, debugging
related_entries: ["infrastructure/2026-06-20_github-actions-workflow-not-gate-without-required-status-check.md", "infrastructure/2026-05-25_ci-auth-failure-workflow-diagnosis-before-chasing-local-state.md", "infrastructure/2026-05-25_github-pat-rotation-hygiene-verify-via-rerun.md"]
---

# Promoting a GitHub workflow to a required status check

When making a CI workflow's check required for merge to a protected branch, there are two gotchas that bite in sequence. Both are easy to miss because GitHub's error messages are unhelpful.

This entry is the operational follow-up to `infrastructure/2026-06-20_github-actions-workflow-not-gate-without-required-status-check.md` — that one taught "shipping a workflow does not gate it." This one teaches "actually wiring the gate hits two more failure modes you will not see coming."

## Gotcha 1: Plan tier on private repos

Branch protection on PRIVATE repos requires a paid plan, but GitHub's response doesn't tell you which paid plan you need. Both legacy branch-protection API and the newer rulesets API return:

```
{"message":"Upgrade to GitHub Pro or make this repository public to enable this feature.","status":"403"}
```

...whether the repo is owned by a USER or an ORGANIZATION. The actual requirement differs:

| Owner type | Required plan |
|---|---|
| User account | **GitHub Pro** ($4/mo) — both legacy + rulesets APIs unlock |
| Organization | Lower tiers (e.g., Free Org) often have rulesets API enabled even without branch protection on legacy API. Free Team gets full features. |

**Diagnostic for the actual plan state:** `gh api user --jq '.plan.name'`
- Paid plans populate `plan.name` (e.g., `"pro"`).
- Free user accounts return `null` (not omitted — explicit null).
- Org plans are in `gh api orgs/<org>` similarly.

**Diagnostic for the actual capability:** just try the PUT. If it succeeds, you're on the right plan; if not, the response is authoritative even when the error is generic.

Verified 2026-06-26 against `internexio/cos` (user-owned private repo): Free user account returned `plan:null`, both branch-protection and rulesets APIs returned 403. After upgrade to GitHub Pro, both APIs accepted the protection PUT. `SEMalytics/cos` (org-owned) had rulesets API working even before any upgrade discussion — confirming the org-vs-user distinction.

## Gotcha 2: paths-filter + required-status-check deadlock

Once a workflow's job is required for merge, GitHub will not allow merge unless that status check has reported. If the workflow has an `on.pull_request.paths` filter, off-path PRs (touching only files not in the filter) will NEVER trigger the workflow → status never reports → PR is blocked from merge indefinitely.

Pages-that-would-deadlock when a typical site-canonicalization-check filter is in place:
- README-only changes
- `CLAUDE.md`, `.beads/*`, `.claude/rules/*`
- Workflow changes other than the one being protected
- New files at repo root
- Tests/scripts outside the filter path

GitHub does NOT auto-pass an unfired required check. The check is stuck in "Expected" state forever.

## Fix pattern: remove paths-filter, add in-job change detection

Modify the workflow to fire on EVERY PR but short-circuit to success when no relevant files changed:

```yaml
on:
  pull_request:
    branches: [master]
    # paths filter REMOVED — workflow now runs on every PR; checks gate
    # is satisfied via in-job change detection below.

jobs:
  pr-check:
    name: Pre-merge (file-system invariants only)
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0   # need both base and head in local history

      - name: Detect relevant changes
        id: changes
        run: |
          BASE_SHA="${{ github.event.pull_request.base.sha }}"
          HEAD_SHA="${{ github.event.pull_request.head.sha }}"
          CHANGED=$(git diff --name-only "$BASE_SHA" "$HEAD_SHA")
          if echo "$CHANGED" | grep -qE '^(site/|frontend/src/|backend/app/|docs/|nginx/)'; then
            echo "relevant=true" >> "$GITHUB_OUTPUT"
          else
            echo "relevant=false" >> "$GITHUB_OUTPUT"
          fi

      - uses: actions/setup-python@v5
        if: steps.changes.outputs.relevant == 'true'
        with:
          python-version: '3.11'

      - name: Run the real check
        if: steps.changes.outputs.relevant == 'true'
        run: python3 scripts/check_something.py
```

Off-path PRs report success in ~5-10 seconds. On-path PRs run the real check at full cost (~40+ seconds for a typical static-site canonicalization sweep). Required-status-check semantics satisfied either way.

## Verification before locking in

Before setting the required check live, open a deliberately off-path test PR (e.g., touch only README.md or CLAUDE.md) and confirm:
1. The workflow fires
2. The change-detection step prints "no relevant files changed"
3. The job reports success quickly (~5-10s)
4. The status check appears green on the PR

Verified 2026-06-26 via PR #37 against `internexio/cos`. Closed without merge after verification; branch deleted.

## Settings deliberately NOT enabled (operator call)

When applying the protection PUT, decide each:
- `strict: false` — don't require branch up-to-date with base (rebase friction otherwise)
- `enforce_admins: false` — admin override still allowed for emergency hotfixes
- `required_pull_request_reviews: null` — don't force PR review process
- `restrictions: null` — don't restrict who can push
- "Require linear history" / "Require a pull request before merging" — these change the entire workflow (direct master pushes blocked); only enable if PR-only is the policy

## When to use this guide

- Promoting any conditional workflow to required-check status
- Diagnosing "Pro upgrade" 403 errors on GitHub API calls about branch protection or rulesets
- Troubleshooting PRs stuck in "Expected" state on a required check

## When NOT to use

- Public repos (branch protection is free) — skip the plan-tier section
- Workflows that genuinely should run on every PR (no paths filter to begin with) — skip the workflow-restructure section

## Related Entries

- `infrastructure/2026-06-20_github-actions-workflow-not-gate-without-required-status-check.md` — predecessor; the lesson that triggered cos-9a54. Workflow shipped, gate not wired. This entry continues the story: actually wiring the gate.
- `infrastructure/2026-05-25_ci-auth-failure-workflow-diagnosis-before-chasing-local-state.md` — adjacent "workflow exists but doesn't do what you think" mode.
- `infrastructure/2026-05-25_github-pat-rotation-hygiene-verify-via-rerun.md` — companion CI hygiene pattern.

## Source Context

Extracted from `cos-9a54` (P2 operator-action follow-up bead opened by the 2026-06-20 cos-twsy validation). 2026-06-26 session resolved the bead by:

1. Diagnosing the legacy branch-protection 403 → discovering plan-tier issue
2. Trying the rulesets API (newer feature) → same 403 → confirming plan-tier rather than API-specific
3. Comparing `gh api user --jq '.plan.name'` (null) vs the org's `plan.name` (paid) → root-cause confirmed
4. Operator upgraded `internexio` user account to GitHub Pro
5. Branch protection PUT succeeded with `Pre-merge (file-system invariants only)` as the required check
6. Validation PR #37 (deliberate off-path: README-only change) revealed the paths-filter deadlock — workflow never fired, status stuck "Expected", merge blocked
7. Workflow restructured to remove `paths:` filter and add in-job change detection
8. PR #37 closed after green verification; bead `cos-9a54` closed
