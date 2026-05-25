---
title: CI auth failure presents as "compilation/deploy failing" — check workflows before chasing local state
source_mode: debugger
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-25
domain: infrastructure
topic: ci-cd
tags: deployment, quality-gate, grounding
related_entries: ["infrastructure/2026-05-19_git-dash-c-cwd-stability-claude-code-bash.md", "infrastructure/2026-05-14_claude-cli-bare-disables-oauth-keychain-auth.md", "infrastructure/2026-05-25_hook-installed-vs-source-drift-direct-edits.md"]
---

# CI Auth Failure Presents as "Compilation/Deploy Failing"

## The Pattern

User reports "compilation/deploy keeps failing" or "things keep getting out of sync." The intuitive hypothesis is code drift, repo desync, or a build break. The actual cause is often CI-side credential rot: an expired PAT, revoked token, deleted webhook, or rotated secret that wasn't propagated. Local compiles work fine; the failure is invisible until you look at the CI dashboard.

The symptoms look identical between "code drift" and "CI auth break" if you only look at the developer's local terminal. Both produce: "stuff that should be in sync isn't." But the diagnostic cost between the two hypotheses differs by 10×.

## Concrete Instance (knowledgeforge-core, 2026-05-25)

User reported "Compilation / deploy keeps failing, some agents have pushed updates so perhaps things are out of sync?"

First-pass investigation (~5 minutes): fetched origin on three repos (core, cc, cp), checked for divergence, checked working trees, compared installed hooks vs source. Found one real drift (hook source-vs-installed — a separate issue) but everything else aligned. The "deploy failing" symptom was not explained.

Pivot to CI inspection (~30 seconds): `gh run list --limit 10` showed every push since 2026-05-19 had failed at the `Checkout knowledgeforge-cc` step with `Bad credentials - https://docs.github.com/rest`. 6 days of red-X notifications. The PAT secret `CORE_SYNC_TOKEN` had been created 2026-04-15 (40 days prior) and was expired or revoked.

Rotation + workflow re-run via `gh run rerun <id>` → both workflows green within 30s.

## Diagnostic Order

When the user signal is vague ("X keeps failing"), check in cheap-first order:

1. **`gh run list --limit 10`** (~3 seconds) — surfaces CI failures with timestamps. If failures cluster around a specific date and the symptom is "X keeps failing since," this is almost certainly the cause.
2. **`gh run view <failed-id> --log-failed | tail -30`** (~5 seconds) — gives the actual failure text. Look for "Bad credentials," "token expired," "permission denied," or any auth-related noun.
3. **`git status` + `git log HEAD..origin/main`** (~5 seconds) — check local-vs-origin drift. Often clean when the cause is CI.
4. **Installed-vs-source artifact diff** (varies) — for projects with deploy/install steps. See the hook-drift entry for one variant.
5. **`gh secret list`** — shows secret names + last-updated timestamps. A secret created >30 days ago that fits the auth failure window is a strong tell.

The principle: CI auth state is cheap to check and high-prior-probability for "deploy failing" symptoms when local state looks clean. Don't burn 30 minutes inspecting local repos before spending 3 seconds on `gh run list`.

## Heuristic: When to Suspect CI Auth Specifically

- "Failing since" date matches roughly when a secret was created 30-90 days prior (PAT expiry windows are commonly 30, 60, 90 days, or 1 year)
- Local compiles / builds work; only CI fails
- The failing step is "checkout," "auth," "publish," "deploy," "push" — any step that crosses a repo or service boundary
- Multiple workflows fail simultaneously and they share a common secret reference
- The repo uses cross-repo automation (PR-creating workflows, sync workflows, deploy workflows)

## When NOT to Apply

- Local compile actually fails — that's a real code issue, not CI auth
- CI failure is in a step that doesn't touch external services (e.g., unit tests, linting against repo-local code)
- The failure is intermittent or flaky — auth failures are usually deterministic
- The failure post-dates a recent code change that's plausibly the cause — investigate the code change first

## Related

- `infrastructure/2026-05-25_hook-installed-vs-source-drift-direct-edits.md` — the OTHER common cause of "things out of sync" that's NOT CI; check both

## Source Context

Extracted from knowledgeforge-core session mn6 (2026-05-25), post-Phase 1 hook landing. User reported sync failures across three repos; investigation initially chased local state and found secondary drift (hook source-vs-deployed mismatch), but the primary cause was 6 days of CI auth failures from an expired PAT secret. Verified by `gh run list` and `gh run view --log-failed`, resolved by PAT rotation + workflow re-run. This is a reusable diagnostic for any situation where "deploy keeps failing" masquerades as code/repo issues.
