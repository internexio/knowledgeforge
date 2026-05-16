---
title: 'Spec-Commit-Before-Impl-Commit: Decoupling Plan from Application'
source_mode: coordinator
source_session: redacted
created: '2026-05-05T00:00:00Z'
date: '2026-05-05'
confidence: 0.8
grounding_score: 0.8
grounding_source: 'Empirical: cos-bfm migration sequencing. First Studio apply of
  migration 071 failed; root cause diagnosed and migration revised. Because the codemod
  (impl) commit was already in the tree but had not yet been deployed, the revised
  migration could be re-applied without rewriting or re-running the codemod. The decoupling
  is what made just-in-time recovery possible.'
novelty_type: process_pattern
staleness_risk: low
importance: 2
pinned: false
accreted_in: 6.x
related:
- wiki/orchestration/codemod-driven-big-bang-rename.md
- modules/02_builder.md
- modules/05_debugger.md
---

# Spec-Commit-Before-Impl-Commit: Decoupling Plan from Application

## Pattern

When a change consists of (a) a script or migration that prepares state and (b) the application of that script to a real environment, **commit (a) and apply (b) as separate operations**.

The script lives in the repo as a reviewable, re-runnable artifact. Application happens against an environment, leaves no commit, and can be re-tried without history rewrites.

The instinct in many workflows is to fuse the two — "the migration ran, mark the migration as `applied: true` in a tracking commit." Don't. The script's purpose is to *describe a state transition*; whether it has run against a particular database is environment metadata, not script metadata.

---

## Sequence

```
[script commit]  →  [apply to staging]  →  [retry/recover loop if needed]  →  [apply to production]
       │                  │                          │                              │
   in git history    leaves no commit          leaves no commit                leaves no commit
   reviewable        Studio / CLI / runner    fix script in tree if needed   same script, different env
```

The script commit is permanent and reviewable. The application is environmental and re-runnable. If the application fails, the recovery path is:

1. Diagnose against the environment
2. If the script was wrong: revise it in the tree, commit the revision, re-apply
3. If the script was right but the environment was wrong: fix the environment, re-apply the same script
4. The history shows only the canonical script, not the recovery flailing

---

## Why This Survives

- **Recovery doesn't rewrite history.** A failed apply does not corrupt the commit log. The script either passes review or it gets a follow-up commit that revises it cleanly.
- **The same script applies across environments.** Staging apply and production apply use the identical artifact. No "staging variant" or "prod variant" of the migration exists.
- **Just-in-time application is safe.** The script can sit in the tree for hours or days before being applied to any environment. There's no implicit ordering between commit and apply that the next contributor needs to discover.
- **Forensics are easy.** "Why did this fail in prod?" → read the script as committed, read the environment as it stood, compare. Both are recoverable independently.

---

## Anti-Patterns

**Tracking-commit-after-apply.** Pattern: apply the migration, then commit `migrations_applied.json` with a new entry. Breaks if two engineers apply different migrations in parallel; breaks if a tracking commit is forgotten; breaks under rollback because you also have to revert the tracking file.

**Apply-from-CI-on-commit.** "When the migration commits, CI applies it to staging." Couples the commit moment to a deploy moment. The commit can no longer be reviewed before its effects appear. Recovery requires reverting the commit, which doesn't unapply the migration — now you have a divergent state with no script in the tree describing it.

**Script-revision-by-amend.** "First apply failed; let me amend the migration commit and re-apply." The amend forces a force-push if anything else has been pushed; downstream branches get rewritten; reviewers see a different artifact than the one they originally approved. Always make a follow-up commit instead.

---

## Reuse Heuristics

Apply this pattern whenever:

- A change has a "describe" half (migration, codemod, seed script, infra-as-code plan) and an "execute" half (apply to DB, run codemod, terraform apply)
- The execute half can fail for environmental reasons unrelated to the artifact
- Recovery should not require rewriting commit history

Skip when:

- The change has no describe-half — e.g., manual env-var edit on a single host (still log it elsewhere, but no commit pattern applies)
- The describe and execute halves are inseparable by design — e.g., a deploy where the artifact and the act of deploying are the same operation (and even then, separating image-build from image-deploy usually surfaces the same pattern at a different granularity)

---

## Evidence

cos-bfm migration 071 (May 2026):

1. Migration `071_rename_decision_ensemble_to_buyers_committee.sql` committed to tree (commit `[earlier]`)
2. Codemod applied across worktrees, committed (separate commit)
3. Migration applied to staging via Supabase Studio — failed (42P01 on CREATE POLICY)
4. Diagnosed: constraint-rename DO block was fragile and cosmetic
5. Revised migration as commit `c4a15b9` — DO block removed
6. Re-applied via Studio — succeeded
7. The codemod commit was untouched throughout the recovery
8. Validation queries confirmed renamed schema; 8/8 gates passed

The recovery loop was contained to a single follow-up commit. No history rewrite, no force-push, no `migrations_applied` tracking file. The codemod commit's review status was unaffected by the migration's apply-failure-and-recovery cycle. Production replication will use the same revised migration script — no staging-vs-production divergence in the artifact.
