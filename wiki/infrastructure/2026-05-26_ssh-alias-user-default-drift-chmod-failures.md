---
title: SSH alias without User= defaults to current local user — operations land as root, breaking ownership
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 1.0
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-26
domain: infrastructure
topic: server-configuration
tags: [empirical, deployment, configuration, quality-gate]
related_entries:
  - infrastructure/2026-05-25_ssh-alias-drift-verify-destination-hostname.md
---

# SSH alias without User= defaults to current local user — operations land as root, breaking ownership

## The trap

When `~/.ssh/config` defines a Host alias WITHOUT a `User` directive, the default user comes from the LOCAL user running the ssh command. On macOS with sudo-enabled accounts, or any environment where you've added an SSH key for root on the remote, this can silently authenticate you as `root` on the destination — not as the application user (e.g., `forge`, `www-data`) that documentation might suggest.

The trap fires when:

1. The ssh config alias is set up "for convenience" (no User specified)
2. Both root and an application user have your SSH key authorized on the remote
3. You run commands via the alias, treating them as application-user operations
4. The commands create files/dirs that need to be readable/writable by the application user later

Files created under `ssh staging "..."` end up `root:root` — but the application user is what later needs to chmod, rename, or rm them. Bug surfaces during automated deploys (CI/CD chmod runs as application user, fails on root-owned subtree).

## When this applies

- Any project where SSH aliases are used for ops/deploy and the developer doesn't explicitly set User=
- Multi-user destination servers (Forge, traditional Linux hosts with app+root accounts)
- Setups where the SSH key is added to both root AND application user's `authorized_keys` (common for convenience)
- Automated deploy workflows where a manual SSH operation (via alias) creates state that a CI/CD process later tries to modify

## When this does NOT apply

- ssh config aliases with explicit `User=app-user` directive — no ambiguity
- Single-user destination servers
- Environments enforcing keys per user via certificate-based auth

## The diagnostic

When a deploy fails on `chmod` or `chown` of files that "shouldn't have been created by root":

```bash
# Verify on the remote what user a recent file was created by
ls -la /path/to/suspect/file
# If owner is root:root but you expected forge:forge,
# AND you recently created the file via `ssh alias "command"`,
# AND the alias has no `User=` directive,
# you've hit this trap.
```

Verify your own ssh config:

```bash
grep -A 5 'Host alias-name' ~/.ssh/config
# Look for missing `User` line — that's the bug
```

Verify which user the alias actually connects as:

```bash
ssh alias-name whoami
# If it returns 'root' but you expected 'forge', confirmed.
```

## The fix

Two options:

### Option 1: explicit User in ssh config (safer for ops aliases)

```sshconfig
Host staging
  HostName 1.2.3.4
  User forge
  IdentityFile ~/.ssh/id_ed25519
```

### Option 2: separate aliases per user (safer for dual-purpose access)

```sshconfig
Host staging-forge
  HostName 1.2.3.4
  User forge
  IdentityFile ~/.ssh/id_ed25519

Host staging-root
  HostName 1.2.3.4
  User root
  IdentityFile ~/.ssh/id_ed25519
```

Option 2 forces explicit choice of privilege level per operation. Recommended when both users are legitimate ops targets.

## Recovery after the trap fires

If files have already been created under wrong ownership:

```bash
# On the remote, as root (or via sudo):
chown -R forge:forge /path/to/affected/tree
```

Then audit recent operations and adjust the alias before re-running.

## Concrete grounding

On 2026-05-26 during a Phase 1 SEO dashboard deploy, an automated GitHub Actions chmod step failed with "Operation not permitted" on `storage/app/snapshots/processed/`. Investigation showed:

- The directory had been created earlier in the session by `ssh staging "php artisan snapshots:import-seo"` (artisan's `mkdir($processedDir, 0755, true)` ran as the connection user)
- `ls -la` on the remote showed `drwxr-xr-x 2 root  root  4096 May 26 16:09 processed`
- The forge user couldn't chmod root-owned files during the subsequent deploy
- `~/.ssh/config` had `Host staging` mapped to `HostName 143.198.150.190` with NO `User` directive
- `ssh staging whoami` returned `root` (confirming the trap)

Fix: `ssh staging "chown -R forge:forge /path/to/snapshots"` then continued the deploy. The resolution required adding `User forge` to the `Host staging` section in `~/.ssh/config` to prevent recurrence.

## Related entries

This entry pairs with `infrastructure/2026-05-25_ssh-alias-drift-verify-destination-hostname.md` which covers a different SSH alias trap (alias name drifting from destination IP). Both are facets of "treat SSH aliases as cosmetic conveniences — verify what's behind them before state-changing operations."

The broader pattern family includes any configuration/documentation/runtime mismatch where the wrong state-change target is selected silently (see `diagnostics/2026-05-23_live-smoke-as-verification-gate-mocks-pass-prod-breaks.md`).

## Source Context

Discovered during staging-deploy-chmod-fail-2026-05-26 session. A manual artisan command run via SSH alias created files as root instead of the application user, causing automated deploy chmod to fail. The diagnosis required verifying the ssh config alias and testing which user it connected as. Both the hostname-drift entry (2026-05-25) and this entry (2026-05-26) address silent SSH configuration mismatches that break state-changing operations.
