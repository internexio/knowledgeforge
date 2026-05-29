---
title: SSH alias drift — verify destination hostname before treating "you're on X" as fact
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.82
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-25
domain: infrastructure
topic: server-configuration
tags: [deployment, empirical, quality-gate]
related_entries:
  - diagnostics/2026-05-23_live-smoke-as-verification-gate-mocks-pass-prod-breaks.md
---

# SSH alias drift — verify destination hostname before treating "you're on X" as fact

## Problem

When SSH connection aliases (in `~/.ssh/config`) and infrastructure documentation (e.g., a server-IP table in CLAUDE.md or a README) drift apart, you can SSH into the "wrong" host and operate on it under the assumption you're on the documented host. Configuration files don't tell you they're stale; commands silently succeed against the wrong target.

The failure mode is invisible at the SSH layer — you connect, you get a shell, commands run. But what you're modifying isn't what the docs say you're modifying. Then surprising things start happening: files you dropped don't appear at the URL you expected, services you reconfigured don't change behavior, etc.

## When This Applies

- Any time a multi-server environment has aliases that map server names to IPs.
- Before making any state-changing operations on what you THINK is server X.
- When investigating "why didn't the file I dropped get served?" — the answer might be "you dropped it on the wrong box."
- During incident response on cross-machine infrastructure.

## When This Does NOT Apply

- Single-server environments where SSH config is one-to-one with reality.
- When you've literally just confirmed the destination in the last command.

## Verification Pattern

The cheap-and-fast hostname check:

```bash
ssh <alias> "hostname; ip a | grep -E 'inet ' | head -3"
```

Compare the output to what your docs say. If they disagree, your docs are stale (or your SSH config is). One additional belt-and-suspenders test:

```bash
ssh <alias> "echo 'on:' \$(hostname) ; cat /etc/hostname"
```

## Grounding (sem-tools session 2026-05-24)

User's global CLAUDE.md documented:

> | Alias | Server | IP | Purpose |
> |-------|--------|-----|---------|
> | `ssh clickadtech` | clickadtech-legacy | 143.244.188.165 | Legacy Clickadtech |

User's actual `~/.ssh/config`:

```
Host clickadtech clickadtech-prod
  HostName 164.92.101.234
```

So `ssh clickadtech` landed on **clickadtech-prod (164.92.101.234)** — a different machine than the documented one. Investigation needed to set up IndexNow on the *legacy* server (143.244.188.165, which actually serves internexio.com) burned ~20 minutes operating against the wrong server, including dropping a key file at `/var/www/html/fffc542999f140caa6edf7dbb25d566b.txt` that never served internexio.com (cleanup required).

The diagnostic that finally surfaced the drift:

```bash
ssh clickadtech "echo 'hostname='\$(hostname); ip -4 -br addr show | head -10"
# hostname=clickadtech-prod
# eth0  UP  164.92.101.234/19  10.48.0.8/16
```

vs. the assumed `143.244.188.165` in CLAUDE.md.

## Anti-Patterns

- Trusting an alias name to identify the host without verification ("Host clickadtech" → must be clickadtech-legacy, right?).
- Treating documentation tables as truth without periodic spot-checks.
- Investigating "why isn't the file I dropped serving?" without first verifying you dropped it on the right box.
- Updating docs to match a stale config — fix whichever side is wrong, but verify which one is actually canonical first.

## Related Entry

`wiki/diagnostics/2026-05-23_live-smoke-as-verification-gate-mocks-pass-prod-breaks.md` — same family of pattern (trust live verification over assumed/documented state). This entry is the infrastructure-specific instance.

## Source Context

Discovered during sem-tools session 2026-05-24. SSH alias in ~/.ssh/config pointed to a different host (clickadtech-prod, 164.92.101.234) than the one documented in CLAUDE.md (clickadtech-legacy, 143.244.188.165). Investigation to set up IndexNow on the documented legacy server burned ~20 minutes operating against the wrong box. A quick hostname verification command revealed the drift immediately. The pattern generalizes: SSH aliases can become stale silently. A deterministic hostname check before state-changing operations prevents silent target mismatches. Grounding is 0.82 because it's a single incident with clear remediation but narrow scope (specific to SSH configuration drift).
