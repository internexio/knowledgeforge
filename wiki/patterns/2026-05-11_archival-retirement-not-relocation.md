---
title: Archival is retirement, not relocation — autonomous fix systems must honor the difference
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-11
domain: patterns
topic: validation
tags: adversarial, quality-gate, scheduling
related_entries: []
---

# Archival is Retirement, Not Relocation — Autonomous Fix Systems Must Honor the Difference

## The Principle

When an autonomous remediation system encounters a reference to a missing resource and finds a candidate replacement, the temptation is to *redirect* the reference to the replacement. This is correct when the replacement is functionally equivalent (e.g., a moved file). It is **wrong** when the replacement is in a directory whose name encodes retirement (`archive/`, `deprecated/`, `legacy/`, `old/`, `retired/`). Redirecting silently keeps the retired thing running.

The operator-side semantics of moving a file to `archive/` is almost always "stop using this." Auto-rewriting a cron entry, config file, or import path to point at the archive copy violates that semantic silently. The correct auto-fix is to *disable* the reference, not relocate it.

## Concrete Failure

[project] Dreaming Tier 1 (autonomous remediation system for cron hygiene) initially had this policy for cron orphans:

- Cron line references `/scripts/foo.sh` which is missing
- Archive copy exists at `/scripts/archive/foo.sh`
- Auto-fix: `crontab_rewrite` — rewrite the cron line to point at `/scripts/archive/foo.sh`

On first deployment to a laptop with 4 archived scripts, the system "helpfully" re-pointed all 4 cron entries to their archive copies. The result: 4 scripts that had been intentionally retired months prior resumed running on schedule, including a `death-loop-detector` that fired every 15 minutes and a `daily-security-summary` script whose downstream consumers had been turned off.

The operator (during post-deployment review) caught it and asked: "we shouldn't have orphaned scripts in archives." The fix was a policy reversal:

- Cron line references missing script
- Archive copy exists OR not — doesn't matter
- Auto-fix: `crontab_disable` — comment out the line with a `DREAMING-DISABLED:` prefix
- The archive path is surfaced in the finding's evidence as `archive_path_hint` so the operator can manually revive if intended
- New detector rule: if a cron line already points into a path with `archive/` segment, it's a finding too — disable it

## When This Applies

- Any autonomous remediation system that detects "missing reference" and considers auto-replacement candidates
- Cron-orphan detectors, broken-symlink fixers, dead-import resolvers, missing-config-file repairers
- Any system where directory naming conveys lifecycle state (`active/` vs `archive/`, `current/` vs `legacy/`)
- Auto-fix systems with a "preserve execution if possible" bias — this bias is wrong for retirement signals

## When This Does NOT Apply

- Systems where archived items are still considered functional and the move was purely organizational (rare; verify by reading the archival convention in the repo's docs or CLAUDE.md)
- Systems with explicit version pinning where pointing at an older copy is a legitimate operation (rollbacks, blue-green deploys)
- Cases where the archive path is the canonical location for long-term scheduled jobs (some legacy systems do this; check for an opt-in marker in the path before applying the principle)

## Detection Heuristic

Path-segment match (not substring match):

```python
def path_references_archive(p: Path) -> bool:
    # Matches /scripts/archive/foo.sh
    # Does NOT match /scripts/my-archive-tool.sh
    return any(part.lower() == "archive" for part in p.parts)
```

Similarly for `deprecated/`, `legacy/`, `retired/`, `_old/`. Pick the words your codebase uses.

## Two Findings Are Better Than One Auto-Rewrite

When the detector finds a missing script with an archive copy:

1. **Disable the cron entry** — primary fix (auto-applied)
2. **Surface the archive path in evidence** — informational, lets the operator manually revive by editing the disabled line back

This preserves "execution if intended" via operator action without the autonomous system silently making the wrong default choice.

## Key Insight

Lifecycle signals encoded in directory names (`archive/`, `deprecated/`, etc.) are semantic markers. An autonomous system that converts a semantic signal (retirement) into an operational action (relocation) violates the operator's intent. The correct behavior is to surface the finding and let the operator decide.

## Source Context

Discovered during [project] Dreaming Tier 1 deployment, 2026-05-12. The first cycle ran auto-fixes against the laptop's live crontab and rewrote 4 entries to point at `archive/` paths. Operator review caught it immediately. Policy fix committed to `feat/dreaming-tier1` branch as commit aeca186 (PR #1 in internexio/[project]): A1 detector action changed from `crontab_rewrite` to `crontab_disable` with `archive_path_hint` preserved in evidence; new A3 detector `A:cron-references-archive` flags entries already pointing into archive/ directories; 5 unit tests added.
