---
title: Backup-in-enumerated-dir anti-pattern — plugin/skill install scripts must not back up in place
source_mode: critic
novelty_type: new_pattern
grounding_score: 0.85
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-11
domain: patterns
topic: plugin-systems
tags: install-scripts, plugin-systems, skill-management, anti-pattern, claude-code
related_entries: ["2026-07-05_claude-code-skills-durability-source-repo-install-script.md"]
---

# Backup-in-enumerated-dir anti-pattern — plugin/skill install scripts must not back up in place

## Pattern: Backup-in-Enumerated-Dir Anti-Pattern

### What was observed

A skill installer script (`install.sh` in the `leonardo-skills` repo) backed up existing skill directories in place before overwriting them:

```bash
if [ -d "$DEST/$s" ]; then
  ts=$(date +%Y%m%d-%H%M%S)
  mv "$DEST/$s" "$DEST/$s.bak.$ts"
fi
cp -R "$SRC/$s" "$DEST/$s"
```

`$DEST` is `~/.claude/skills/` — the directory Claude Code enumerates for available skill commands. Running the install 4 times in one day produced 15 `.bak` directories (4 skills × ~4 runs), all of which appeared as phantom commands in the skill list.

Example phantom commands visible to the user: `leonardo-infographic.bak.20260710-151031`, `svg-mobile-lint.bak.20260710-153404`, etc.

### Why it happens

The host system (Claude Code, a plugin loader, a package manager) enumerates the target directory to discover installable units. It uses directory name as command/skill identity. Backup dirs placed in the same directory pass the same discovery check as real skills, with names that look like valid (if odd) commands.

### When this applies

Any system where:

- A directory is enumerated by name to register commands, plugins, or skills
- An install script backs up prior versions of those directories
- The backup remains in the enumerated directory

Common surfaces: Claude Code `~/.claude/skills/`, VS Code extension dirs, npm global bin dirs, shell completion dirs, any `$PATH` directory where installers drop backups.

### Fix pattern

Three options, ranked by simplicity:

1. **No backup** (recommended when content is source-controlled): delete and replace.
   Git is the recovery path. `rm -rf "$DEST/$s" && cp -R "$SRC/$s" "$DEST/$s"`

2. **Backup outside the enumerated dir**: use a sibling or temp directory.
   ```bash
   BACKUP_DIR="$HOME/.claude/skills-bak"
   mkdir -p "$BACKUP_DIR"
   mv "$DEST/$s" "$BACKUP_DIR/$s.bak.$ts"
   ```

3. **Max-1 backup with auto-cleanup**: keep only the most recent backup, delete older ones.
   Most complex; only warranted when the install source is not version-controlled.

### When NOT to apply

- Backup dirs that live OUTSIDE the enumerated directory are safe — location is the only discriminator, not naming convention.
- Systems that filter by extension or metadata (e.g., only `.js` files) are immune if `.bak` dirs don't match the filter.

### Grounding

Directly observed in session: 15 `.bak` dirs in `~/.claude/skills/` confirmed by `ls ~/.claude/skills/ | grep "\.bak"`, all surfaced as phantom skills in the Claude Code system-reminder. User reported the symptom ("don't think the .bak files should be commands"); root cause traced to install.sh in one turn.

## When This Applies

Any install or deployment script that:
- Targets a system-enumerated directory (plugin registry, command loader, skill discovery, $PATH)
- Backs up prior state before overwriting
- Leaves the backup in the same enumeration zone

## When This Does NOT Apply

- Backup dirs that live outside the enumerated scope (e.g., `~/.skills-archive/` when the enumeration watches `~/.claude/skills/`)
- Systems with explicit exclusion patterns that ignore backup naming (e.g., "skip `*.bak`" or "skip dotfiles")
- One-off, non-repeated installs where the backup never re-runs

## Source Context

Directly observed in leonardo-skills repo install.sh during a commit-review session (2026-07-11). Install ran 4 times in one day; each run created a fresh `.bak.TIMESTAMP` directory. Claude Code's skill enumeration picked them up, surfacing them as phantom commands in the skill list. Candidate filed as a negative (anti-pattern) example to prevent the same mistake in future install script design.

**Extends:** 2026-07-05 entry on source-repo-based skill durability. That entry prescribes the right install.sh pattern; this entry documents the failure mode when that pattern is skipped.
