---
title: bd search idempotency grep trap — match ^Found header, not query string
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-13
tags: quality-gate, empirical, stable
related_entries: []
domain: diagnostics
topic: issue-tracking
---

# bd search idempotency grep trap — match ^Found header, not query string

## The trap

The natural idempotency idiom for "is there an open bead matching X?" is:

```bash
if bd search "Silent session: $session" --status open | grep -q "Silent session: $session"; then
    # bead exists — skip
fi
```

This is WRONG. `bd search` (alias for `br` / `beads_rust`) prints its query back to you in the no-match case:

```
No issues found matching 'Silent session: [project]'
```

The substring `Silent session: [project]` appears in both:
- **Match-case rows:** actual bead titles/descriptions that contain the query
- **No-match echo line:** the literal query string in the "No issues found matching 'X'" header

Therefore, `grep -q "Silent session: $session"` returns true regardless of whether any beads exist. Idempotency check always-matches; bead creation is suppressed forever; the escalation surface goes dark.

Same trap applies to any wrapper around `bd` that intends "did this search return rows?" semantics by grepping for the query string.

## The fix

Match the count header instead:

```bash
if bd search "Silent session: $session" --status open 2>/dev/null | head -1 | grep -q "^Found"; then
    # at least one match exists — skip
fi
```

The match-case header is exactly:

```
Found N issues matching 'X':
```

The no-match line starts with "No issues found...". A leading-anchored `^Found` regex distinguishes them cleanly. `head -1` bounds the search to the header so a bead whose title or description happens to start with "Found" can't false-positive.

## When this applies

- Any idempotent action gated on "does this bead already exist?"
- Watchdog scripts (silent-run detection, stranded-bead reconciliation)
- Cron jobs that should skip if their previous run's bead is still open
- Any wrapper script that wants "did this search produce results?" exit semantics
- Shell functions that gate bead creation on prior-work detection

## When this does NOT apply

- If `bd` ever ships a `--json` mode, prefer parsing JSON over grepping headers
- If you're inspecting rows for content (e.g., extracting bead IDs), parse rows directly — the header check is only for "is the set empty?"
- One-off manual queries where you can read the output directly

## Grounding

**Caught in real implementation:** [project] paperclip Pattern 2 Phase B (`[project]-1x6`), commit 1e1c391. The first version of the watchdog branch in `scripts/happy-healthcheck.sh` used the query-grep idiom; a validation probe with no matching beads still returned a non-zero count, suppressing escalation indefinitely. Fix landed in the same commit. Bug surfaced during isolated dry-run testing before any production effects.

## Why the staleness risk is "stable"

This is `bd` CLI display behavior. Changing it would break every shell script using the no-match line as a signal. The header format has been stable across multiple `br` releases used in this user's environment.

## Source Context

Direct diagnostic from [project] paperclip Pattern 2 Phase B escalation logic (2026-05-13).
