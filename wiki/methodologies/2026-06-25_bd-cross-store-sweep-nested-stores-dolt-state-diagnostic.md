---
title: bd cross-store sweep — extend to nested .beads stores + Dolt-state diagnostic
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-06-25
domain: methodologies
topic: search-strategy
tags: beads, cross-scope-search, nested-stores, broaden-pattern, dolt-errors
related_entries:
  - methodologies/2026-06-18_cross-scope-search-blindness-operator-insistence-as-broaden-signal.md
  - diagnostics/2026-05-23_beads-multi-database-working-directory-gotcha.md
  - methodologies/2026-05-23_beads-disk-reconciliation-discipline.md
  - infrastructure/2026-05-27_bd-cli-dependency-wiring-inversion-two-pass-pattern.md
extends: methodologies/2026-06-18_cross-scope-search-blindness-operator-insistence-as-broaden-signal.md
---

# bd Cross-Store Sweep — Extend to Nested .beads Stores + Dolt-State Diagnostic

## Why this extends the parent entry

The parent pattern ([[2026-06-18_cross-scope-search-blindness-operator-insistence-as-broaden-signal]]) establishes the cross-project sweep rule: when the local `.beads/` returns nothing and the operator pushes back, BROADEN the search across all sibling project stores via `find ~/Scripts -name ".beads" -type d`. That rule assumes one `.beads/` per project. This entry covers the case where that assumption breaks: **some projects nest sub-repos that each have their own `.beads/` store**, and the default sweep depth (`-maxdepth 3`) misses them. It also captures a secondary diagnostic — nested stores can be in a Dolt server/database state-mismatch where "no bead found" is not the same as "no bead exists."

## Core extension — nested .beads stores at sub-repo depth

Some projects contain inner `.beads` directories at sub-repo level, not just at the project-root. Concrete example from the grounding session (`[project]/`):

- `~/Scripts/[project]/.beads`                    (outer, project-root)
- `~/Scripts/[project]/[project]/.beads`         (inner sub-repo)
- `~/Scripts/[project]/mcp_agent_mail/.beads`     (inner sub-repo)

A `find ~/Scripts -maxdepth 3 -name .beads -type d` sweep ENUMERATES the outer store only. Inner stores require `-maxdepth 4` (or deeper depending on layout). The parent entry's recipe step ("Run `find ~/Scripts -name "PATTERN" -type d` to enumerate ALL instances") works correctly only if depth is not capped — but many agents add a `-maxdepth` guard to avoid scanning into `node_modules/`, `.venv/`, build artifacts, etc. That guard is what creates the blindness.

## Symptom

Operator references a bead by project name ("the X bead in [project]"). Standard sweep returns nothing. Without the nested-depth extension, the agent concludes "no bead exists" — and is wrong, because the bead may live in an inner store one level deeper than the sweep reached.

## Remediation

1. **Default sweep depth should be `-maxdepth 4`, not 3.** The cost of one extra level is negligible; the cost of missing a real bead is operator trust + re-search rounds.
2. **After the deeper sweep, search each store individually.** Each `.beads/` has its own Dolt instance — `bd` commands honor cwd, so `cd <store-dir> && bd list` per store is the safe pattern.
3. **If a nested store returns a Dolt server error (e.g., "database not found"), that's its OWN signal — not "no bead."** The store may exist but be in a broken/partial state. Surface this as a separate condition.

## Bonus diagnostic — Dolt state mismatch on nested stores

Nested `.beads/` stores can carry independent Dolt server issues unrelated to the outer store. Concrete grounding: `[project]/[project]/.beads` reported `bd dolt status` → "Dolt server: running" with a live PID and port, BUT actual `bd list` queries returned `database not found: [project]`. The Dolt server log showed `unable to process ComInitDB: database not found` — the server process was alive, but the database it was supposed to serve wasn't present.

This is a partial-init or recovery state, not a "no bead" state. The diagnostic chain that confirms it:

1. `bd doctor` from inside the suspect store dir — surfaces "Unable to open database" + "Storage: Dolt"
2. `bd dolt status` — confirms server running, returns PID + port
3. Read `.beads/metadata.json` — reveals the `dolt_database` field (the database name bd is asking the server for)
4. Compare against the server's actual database list

### Dolt CLI flag-order gotcha

When you try to query the running Dolt server directly to enumerate its databases, the natural form fails:

```
# WRONG — -H/-P after `sql` are interpreted as sql-subcommand flags and rejected
dolt sql -H 127.0.0.1 -P <port> -q "SHOW DATABASES;"
```

`-H/-P` are **global** dolt CLI flags and must appear BEFORE the `sql` subcommand:

```
# RIGHT
dolt -H 127.0.0.1 -P <port> sql -q "SHOW DATABASES;"
```

If the server's `SHOW DATABASES` output doesn't include the name in `metadata.json`, the store is in a state-mismatch. Repair is out of scope for a cross-session sweep — surface the finding and recommend the operator handle it in a session scoped to that project.

## When to apply

- Operator references a bead by project name and the standard depth-3 sweep finds nothing
- Project is known to have a sub-repo structure (e.g., `[project]/`, monorepos with inner repos, vendored projects with their own `.beads/`)
- Any time the parent cross-scope-blindness rule fires on a project that contains sibling sub-repos

## When NOT to apply

- Simple single-store projects (most of them) — the extra depth wastes time. Use depth-3 by default.
- Operator is genuinely creating the bead now — there's no prior bead to find.
- Single-file `.beads/` references (i.e., the operator names a specific store path) — go directly to that path.

## Concrete grounding (2026-06-25)

- **Request:** "Close the [project] disc/mbti bead... I am working on it in [project]."
- **Initial sweep at `-maxdepth 3`:** only `~/Scripts/[project]/.beads` found. Searched across terms (DISC, MBTI, personality, feeder, de-emphasis, AEO, GEO) — no matches.
- **Broader find with `-maxdepth 4`:** discovered nested `[project]/[project]/.beads` + `[project]/mcp_agent_mail/.beads`.
- **`[project]/[project]/.beads`:** hit Dolt error (`database not found: [project]`); diagnosed via the chain above, did not attempt repair.
- **`[project]/mcp_agent_mail/.beads`:** no bd database initialized at all.
- **Net result:** no DISC/MBTI bead found anywhere; operator confirmed move on.
- **Cost of the depth-3 cap on round 1:** would have produced a false-negative "doesn't exist" before the deeper find ran.
- **Cost of the deeper sweep:** one extra `find` with `-maxdepth 4` + per-store `bd list` calls.

## Composes with

- **Parent: [[2026-06-18_cross-scope-search-blindness-operator-insistence-as-broaden-signal]]** — establishes the broaden-on-pushback rule and the cross-project sweep. This entry refines the sweep's depth parameter and adds the Dolt-state-mismatch diagnostic.
- **[[2026-05-23_beads-multi-database-working-directory-gotcha]]** — `bd` selects its DB by walking up from cwd. The nested-store topology is exactly the on-disk arrangement that triggers this gotcha; this entry adds the search-side dimension to that operations-side hazard.
- **[[2026-05-23_beads-disk-reconciliation-discipline]]** — session-start reconciliation. When a project has nested stores, reconciliation has to visit each one.
- **Global CLAUDE.md `### beads (bd CLI)` section** — already mentions "Multi-project bead stores — sweep ALL instances on first 'not found' claim." This entry adds the nested-stores depth requirement (`-maxdepth 4`) to that rule and introduces the Dolt-state-mismatch failure mode as a third condition distinct from "found" and "not found."

## Source context

Surfaced in a 2026-06-25 semalytics-gtm session where the operator asked the agent to close a DISC/MBTI bead "in [project]." Standard sweep at `-maxdepth 3` returned only the outer `[project]/.beads/` store and found no matching beads. Broadening to `-maxdepth 4` revealed two additional nested stores at the sub-repo level — one of which was in a Dolt server/database state-mismatch (server running, database missing) that would have read as "no bead" but was actually "store broken." The bead in question was ultimately not present in any store; the operator confirmed and moved on. The extension to the parent pattern: depth-3 sweeps miss sub-repo stores, and "Dolt server error" is a third condition that must be distinguished from "no bead found."
