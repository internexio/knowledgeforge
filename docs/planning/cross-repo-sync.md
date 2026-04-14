# Cross-Repo Sync Architecture

**Status:** Workflows committed, implementation deferred to post-Phase 6
**Decision date:** 2026-04-14
**Revisit:** After Phase 6 (compiler) is complete

---

## What Exists Now

Two GitHub Actions workflows are committed to `knowledgeforge-core`:

| Workflow | Trigger | Action |
|----------|---------|--------|
| `sync-hooks-cc.yml` | push to `main` touching `hooks/**` | Opens PR in `knowledgeforge-cc` with updated `.claude/hooks/` |
| `sync-modules-cp.yml` | push to `main` touching `modules/**` | Opens PR in `knowledgeforge-cp` with updated module files |

Both support `workflow_dispatch` for manual catch-up syncs.

A sync script `scripts/sync-cp-modules.py` handles the CP file matching — core uses `NN_snake_case.md`, CP uses `NN_PascalCase.md`. Matching is by two-digit prefix. Tested: 26/26 modules matched, 0 errors.

---

## What's Missing (Deferred)

**One setup step remaining:** Add `CORE_SYNC_TOKEN` secret to `knowledgeforge-core` → Settings → Secrets → Actions.

Token requirements:
- Fine-grained PAT, resource owner: `internexio`
- Repositories: `knowledgeforge-cc`, `knowledgeforge-cp`
- Permissions: Contents (read/write) + Pull requests (read/write)

**Do not activate until after Phase 6.** The current sync does a verbatim file copy, which is a stopgap. The real implementation should invoke the compiler.

---

## Phase 6 Upgrade Path

Once `kf-compile.py` exists, replace the file-copy steps in both workflows:

**sync-hooks-cc.yml** — hooks don't need compilation, keep as-is (direct copy is correct for hooks).

**sync-modules-cp.yml** — replace `sync-cp-modules.py` call with:
```yaml
- name: Compile CP variant
  run: |
    python3 compiler/kf-compile.py \
      --target claude-projects \
      --output cp-repo/
```

The compiler reads canonical modules → generates CP-formatted knowledge files → writes to CP repo. This replaces the current direct-copy approach and handles any format differences between core modules and CP files.

---

## Architecture Decision

**PR-based, not direct push.** Both workflows open PRs rather than committing directly to the target repos. Rationale:
- Pre-Phase 6: hand-crafted files in CC/CP may have local changes not yet reconciled back to core. Direct push could overwrite them.
- Post-Phase 6: compiler output should still be reviewed before it lands, at least until the compilation pipeline is trusted.

Downgrade to direct push once confidence is high and the compiler round-trip is validated.

---

## Local Deploy Step (Permanent)

GitHub Actions can't reach `~/.claude/hooks/` on local machines. After any hook PR merges to CC, the local deploy is always manual:

```bash
cd ~/Scripts/knowledgeforge-core
./scripts/deploy-hooks.sh
```

This is intentional — hooks affect live Claude behavior and shouldn't auto-deploy without awareness.
