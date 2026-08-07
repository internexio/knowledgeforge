---
title: Config source migration requires auditing all consumer scripts, not just the primary loader
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.80
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-11
domain: migrations
topic: config-migration-audit
tags: [migrations, configuration, scripts, audit, bash]
related_entries: ["infrastructure/2026-07-06_bash-orchestrator-config-array-loaded-at-startup-restart-required.md", "methodologies/2026-06-10_verify-premise-before-defensive-bead.md"]
---

# Config Source Migration Requires Auditing All Consumer Scripts, Not Just the Primary Loader

## Problem Pattern

When migrating a config source (e.g., hardcoded shell array → TOML file), the primary loader is updated but secondary consumer scripts that ALSO read the old config source are overlooked. They continue to silently use the old source, causing confusing failures or no-ops.

## Observed Instance (2026-07-11)

`happy-orchestrator.sh` was migrated to load sessions from `machine.toml` via `happy-sessions-toml.py` (replacing a hardcoded `SESSIONS=(...)` bash array).

**Consumer scripts updated:** happy-sessions.sh (add/remove/list), happy-orchestrator.sh

**Consumer scripts NOT updated:** happy-enable.sh

`happy-enable.sh` had its own independent awk-based parser that read the SESSIONS array directly from happy-orchestrator.sh. After the migration, the array was gone (replaced by dynamic TOML loading), so awk found nothing and every `/happy-enable` call failed with "not registered in SESSIONS block" — even for sessions that existed in machine.toml.

**Fix:** Updated `happy-enable.sh` to check machine.toml via `happy-sessions-toml.py get-sessions` first, fall back to the legacy awk parser.

**Secondary bug found in the same pass:** `happy-enable.sh` used `${SESSION_WORKDIR//\$HOME/$HOME}` to expand literals but didn't handle `~` expansion. The TOML helper returns `~/path` (not `$HOME/path`), so workdir validation failed with "workdir does not exist". Fix: add `${SESSION_WORKDIR/#\~/$HOME}` before the `$HOME` substitution.

## Audit Checklist for Config Source Migrations

Before declaring a config migration complete:

1. **Find all independent readers:**
   ```bash
   grep -rn "OLD_SOURCE_IDENTIFIER" scripts/
   ```
   Find all scripts that reference the old config source (file path, array name, config key, etc.)

2. **Classify each hit:** Does it READ the old source independently, or does it delegate to an already-updated loader?

3. **Update each independent reader** to use the new source. Prefer a **try-new-first/fallback-to-old** pattern if old source may still exist on some hosts during rollout:
   ```bash
   CONFIG_VALUE=""
   # 1. New source (preferred)
   if [[ -f "$NEW_SOURCE" ]]; then
       CONFIG_VALUE=$(get_from_new_source "$KEY") || true
   fi
   # 2. Legacy fallback
   if [[ -z "$CONFIG_VALUE" ]]; then
       CONFIG_VALUE=$(get_from_old_source "$KEY")
   fi
   ```

4. **Test each consumer with the new source only** — deliberately remove/rename the old source to catch stragglers

5. **Check for derived assumptions.** Example: `$HOME` vs `~` in path values differs between old shell arrays (which often used `$HOME`) and TOML files (which often use `~`). Path-expansion helpers must normalize both forms.

## When This Applies

- Any config format migration (INI → TOML, TOML → JSON, shell variable → file, hardcoded → file, etc.)
- When multiple scripts are each parsing the same config source independently (not delegating to a shared library)
- Especially in shell codebases where config parsing is often inlined rather than abstracted
- Multi-host deployments where some hosts may lag during rollout (prefer-fallback pattern required)

## When It Does NOT Apply

- Single-script systems where one script owns all config reads
- Migrations using a compatibility shim that transparently handles both old and new formats (shim handles all consumers at once)
- Config changes that are read via a single canonical loader function and all consumers call that function

## Prefer-Fallback Pattern for Gradual Rollout

When migrating across multiple hosts or environments, consumer scripts should check the new source first, fall back to the old. This allows mixed deployments (e.g., Mini hasn't been updated yet) and reduces the blast radius of a partial rollout:

```bash
SESSION_WORKDIR=""
# 1. New source (preferred)
if [[ -f "$MACHINE_TOML" && -f "$TOML_HELPER" ]]; then
    SESSION_WORKDIR=$(get_from_toml "$NAME") || true
fi
# 2. Legacy fallback
if [[ -z "$SESSION_WORKDIR" ]]; then
    SESSION_WORKDIR=$(awk_parse_old_shell_array "$NAME")
fi
```

This pattern:
- Allows new code to use new source immediately
- Allows old code to keep working with old source
- Supports gradual host-by-host migration
- Makes rollback trivial (just don't update a consumer; it falls back forever)

## Red Flags During Migration Testing

- A consumer runs but produces different behavior after migration (old: "not found", new: wrong value from TOML) — indicates the consumer is still reading old source in one code path
- Partial updates work on one host but not another — check for distributed consumers that you missed
- Path-expansion differences cause "does not exist" failures even when the config key exists — check for `$HOME` vs `~` normalization issues

## Related Patterns

- **Config-at-startup latching** (infrastructure/2026-07-06_bash-orchestrator-config-array-loaded-at-startup-restart-required.md) — long-running daemons cache config in memory; restart required to re-read updated files
- **Verify premise before defensive bead** (methodologies/2026-06-10_verify-premise-before-defensive-bead.md) — general pattern of reading full context before claiming a source is "missing"
- **Find-consumer-first before data migrations** (methodologies/2026-05-13_find-consumer-first-before-data-migration.md) — upstream audit discipline for any config/data change

## Source Context

[project] happy-orchestrator TOML migration, 2026-07-11. Migration of session config from bash SESSIONS array to machine.toml missed happy-enable.sh, which independently parsed the array via awk. The `/happy-enable` command failed for all sessions even though they existed in TOML. Secondary bug: path-expansion differences (`~` vs `$HOME`) between shell arrays and TOML caused workdir validation to fail. Audit checklist and prefer-fallback pattern documented to prevent similar misses in future migrations.
