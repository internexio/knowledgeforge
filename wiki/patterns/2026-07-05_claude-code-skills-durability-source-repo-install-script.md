---
title: Claude Code skills durability — source repo + install.sh pattern
source_mode: direct
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-07-05
tags: quality-gate, empirical, stable
related_entries: []
domain: patterns
topic: engineering-craft
---

# Claude Code skills durability — source repo + install.sh pattern

## The gap

Skills authored directly at `~/.claude/skills/<name>/SKILL.md` have **no durability**. The `~/.claude` global config repo (`internexio/claude-global` on this operator's fleet) explicitly gitignores `skills/`:

```
# in ~/.claude/.gitignore
# Skills source: ~/Scripts/cos-skills + others — install via their scripts.
skills/
```

So a skill created in place has:

- No git tracking → any `rm -rf ~/.claude/skills/<name>/` deletes it irrecoverably
- No cross-host propagation → Mac Mini never sees a skill authored on the laptop
- No update audit trail → editing SKILL.md leaves no history

The convention is: **skills are sourced from external repos and installed into `~/.claude/skills/` via install scripts.** Skills that skip this step are one accidental delete away from oblivion.

## The pattern (transferable)

For any custom Claude Code skill or skill family, create a companion source repo:

```
~/Scripts/<name>-skills/
├── README.md            # what this is + how to install/update
├── install.sh           # idempotent copy into ~/.claude/skills/
├── <skill-1>/
│   ├── SKILL.md
│   └── <prompt-template>.md
├── <skill-2>/
│   └── SKILL.md
└── .gitignore           # excludes .bead-backup-*/ etc.
```

**install.sh contract:**

- Idempotent — re-running with identical source is a silent no-op
- Backs up target dirs to `~/.claude/skills/.bead-backup-<ts>/` when contents differ, before overwriting
- Supports `--dry-run` (show plan, no writes) and `--no-backup` (skip snapshot)
- Uses `diff -r` per skill dir to decide "no change" vs "update," so partial edits don't silently trigger a full backup churn

**GitHub topology:** private repo under the operator's org (e.g., `internexio/<name>-skills`), matches the cos-skills pattern.

**Cross-host propagation:**

```bash
# Fresh install on a new host
git clone git@github.com:internexio/<name>-skills.git ~/Scripts/<name>-skills
cd ~/Scripts/<name>-skills && ./install.sh

# Update after an edit on any host
cd ~/Scripts/<name>-skills && git pull && ./install.sh
```

**Verify parity** by comparing SHA256 of prompt template files across hosts:

```bash
shasum ~/.claude/skills/<name>/*prompt*.md   # laptop
ssh mac-mini 'shasum ~/.claude/skills/<name>/*prompt*.md'   # Mini
```

Hashes match ⇒ hosts are in sync.

## When This Applies

- Any custom Claude Code skill or skill family that survives long enough to be worth backing up
- Cross-host operator setups (laptop + Mini + iPad, etc.) where a skill edited on one machine needs to reach the others
- Skills whose behavior other skills depend on (e.g., `/bead-triage` templates that `/bead-pipeline` reads)

## When This Does NOT Apply

- Throwaway one-off skills authored for a single session
- Skills that live inside a project repo (`.claude/commands/<name>.md`) — those are already versioned with the project
- COS skills (already tracked in `~/Scripts/cos-skills/`, `internexio/cos-cc` — the pattern this generalizes from)

## Source Context

[project] session 2026-07-04: after wiring KF meta-principles into `~/.claude/skills/bead-triage/triage-prompt.md` and `bead-build/builder-prompt.md`, the user asked "have we installed this on laptop and mini?" — surfacing the gap: laptop edits were live but not tracked, Mini didn't have the `bead-*` skills at all. Resolution: created `~/Scripts/bead-skills/` (private repo `internexio/bead-skills`), wrote idempotent `install.sh` with backup snapshots, pushed initial commit `44742b6`, cloned + installed on Mini, verified SHA parity on both prompt files. Full recipe generalizes to any custom skill family; matches the pre-existing `cos-skills` pattern noted in `~/.claude/CLAUDE.md § COS Skills`.
