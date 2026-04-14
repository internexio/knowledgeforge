# Cross-Repo Sync Architecture

**Status:** Workflows committed, implementation deferred to post-Phase 6
**Decision date:** 2026-04-14
**Revisit:** After Phase 6 (compiler) is complete

---

## What Exists Now (Phase 6 complete)

Three GitHub Actions workflows are committed to `knowledgeforge-core`:

| Workflow | Trigger | Action |
|----------|---------|--------|
| `sync-hooks-cc.yml` | push to `main` touching `hooks/**` | Direct copy: opens PR in `knowledgeforge-cc` with updated `.claude/hooks/` |
| `compile-cc.yml` | push to `main` touching `modules/**` | Compiler: opens PR in `knowledgeforge-cc` with compiled skill/doc/agent files |
| `sync-modules-cp.yml` | push to `main` touching `modules/**` | Compiler: opens PR in `knowledgeforge-cp` with compiled module files |

All three support `workflow_dispatch` for manual catch-up syncs.
Both compile workflows use `kf-compile.py` (Phase 6). No direct file copy stopgap.

---

## What's Missing

**One setup step remaining:** Add `CORE_SYNC_TOKEN` secret to `knowledgeforge-core` → Settings → Secrets → Actions.

Token requirements:
- Fine-grained PAT, resource owner: `internexio`
- Repositories: `knowledgeforge-cc`, `knowledgeforge-cp`
- Permissions: Contents (read/write) + Pull requests (read/write)

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
