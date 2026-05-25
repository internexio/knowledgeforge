---
title: Hook installed-vs-source drift after direct ~/.claude/ edits
source_mode: builder
source_session: redacted
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-25
domain: infrastructure
topic: deployment
tags: deployment, quality-gate, validation, grounding
related_entries: ["infrastructure/2026-05-12_vendoring-drift-detection.md", "patterns/2026-05-18_markdown-binary-artifact-drift-independent-editing.md"]
---

# Hook installed-vs-source drift after direct ~/.claude/ edits

## The Pattern

Claude Code hooks live in two locations:
- **Source of truth:** `<repo>/.claude/hooks/*.py` (committed to git; canonical)
- **Deployed copy:** `~/.claude/hooks/*.py` (installed via install.sh from source)

When implementing or debugging a hook, the natural test loop edits the DEPLOYED copy at `~/.claude/hooks/` because that's what fires in your live session. If you stop there, the source-of-truth becomes stale. The next `install.sh` (or sync workflow) overwrites your live working hook with the stale source.

The drift is silent until install.sh runs — at which point the changes vanish without warning.

## Concrete Instance

**Module 22 Phase 1 hook implementation (knowledgeforge-core-rk4, 2026-05-25):** Added a `tool_check_duplicate` block to `mempalace-wiki-mine.py`. Edits were applied to `~/.claude/hooks/mempalace-wiki-mine.py` (installed copy) for live testing. The corresponding source at `~/Scripts/knowledgeforge-cc/.claude/hooks/mempalace-wiki-mine.py` was never updated.

Discovered when checking deploy state: source was 7896 bytes (mtime May 16), installed was 10774 bytes (mtime May 24). Diff confirmed the dup-check block existed only in the installed copy. Fix: `cp` installed → source, commit cc, push. ~2 minutes once identified.

## Diagnostic Check (One-Liner)

```bash
for f in <repo>/.claude/hooks/*.py; do
  base=$(basename "$f")
  installed="$HOME/.claude/hooks/$base"
  [ -f "$installed" ] && diff -q "$f" "$installed" > /dev/null 2>&1 || echo "DRIFT: $base"
done
```

Run this before any push, before any install.sh, or whenever you suspect "my hook changes vanished."

## When to Apply

- Any time you've edited a hook directly at `~/.claude/hooks/` for testing convenience
- Before running install.sh on a project with hook-deploying behavior
- Whenever a hook's behavior reverts unexpectedly between sessions
- When git status on the source repo shows clean but the live hook clearly has changes you made

## Operational Methodology

Two viable patterns:

**A. Source-first (safer, slightly slower test loop):** Edit source in the repo, run install.sh to deploy, test live. Repeat. Source is always authoritative; no drift possible. Test loop adds one shell command per iteration.

**B. Installed-first (faster test loop, requires discipline):** Edit installed directly for tight iteration, then when satisfied, immediately `cp` back to source and commit BEFORE declaring done or moving to the next task. The discipline is the immediate back-port — not "I'll do it later."

Either pattern works. Mixing them is what creates drift. Pick one per session and commit to it.

## When NOT to Apply

- Hooks not deployed by install.sh (e.g., one-off scripts in a project that aren't propagated)
- Greenfield hooks where the source repo doesn't yet have the file (then installed IS the only copy, until you add it to source)
- Hook directories explicitly marked "user-local" / "do not deploy" — those are intentionally not synced

## Related Patterns

This pattern is a specialized instance of **vendoring drift** (wiki/infrastructure/2026-05-12_vendoring-drift-detection.md) and **artifact drift** (wiki/patterns/2026-05-18_markdown-binary-artifact-drift-independent-editing.md). The principle is identical: when source and deployed copies can drift, add explicit reconciliation checks.

The CLAUDE.md guidance for KnowledgeForge explicitly states "knowledgeforge-cc is the authoritative source for .claude/hooks/." This pattern operationalizes that guidance with a diagnostic check.

## Source Context

Discovered during Module 22 Phase 1 hook implementation in knowledgeforge-core-rk4 session (2026-05-25). Testing a new `tool_check_duplicate` block required iterative hook changes. Changes were applied directly to the installed copy at `~/.claude/hooks/mempalace-wiki-mine.py` for rapid feedback. The source file in `~/Scripts/knowledgeforge-cc/.claude/hooks/` was not updated simultaneously. Drift was detected at session wrap-up via mtime and size comparison; fix took 2 minutes (copy + commit). Pattern is stable and generalizable to any hook-based installation workflow.
