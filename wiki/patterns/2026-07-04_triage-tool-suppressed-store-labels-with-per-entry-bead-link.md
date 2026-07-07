---
title: Triage-tool SUPPRESSED_STORE_LABELS pattern with per-entry bead link
source_mode: builder
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.70
staleness_risk: stable
importance: 3
pinned: false
created: 2026-07-04
tags: triage-tools, false-positive-management, nightly-scanners, expected-failures, noise-vs-signal
related_entries:
  - methodologies/2026-05-16_upstream-noise-flood-bulk-close-source-pointer.md
  - patterns/2026-05-20_per-detector-error-isolation-audit-pipelines.md
  - patterns/2026-05-12_pin-tests-declarative-policy-manifests.md
domain: patterns
topic: scanner-suppression
---

# Triage-tool SUPPRESSED_STORE_LABELS pattern with per-entry bead link

## The problem

You have a recurring scanner (nightly cron job, triage tool, lint sweep) that surfaces a list of "problems" every run. Some of those problems are:

- **Real, actionable now** — should be surfaced loudly.
- **Real, deferred** — should be surfaced but not loudly (already have follow-up beads).
- **Known-state, non-actionable** — you've diagnosed them, decided not to fix, but they still fail the scanner's check every run.

The third category creates alert fatigue: every night the operator sees the same "3 errors" and eventually stops reading the report at all. Real new signal drowns in known noise.

## Naive approaches that don't work well

- **Delete the offending store/file/whatever** — sometimes not safe. In the case that grounded this pattern, one "erroring" store held 168 real historical issues that weren't safe to delete.
- **Fix the scanner to auto-migrate/repair** — hides the fact that the state is dormant/legacy; the scanner ends up doing product-decision work.
- **Add a `--verbose` flag to hide known errors** — everyone forgets to pass the flag; you're back to noise.
- **Add a comment in the scanner source explaining the exception** — invisible to the operator reading the nightly output.

## The pattern

Add a **module-level suppression set** with three properties:

1. **Frozen set of stable identifiers** — not paths (paths vary by host), but a stable label like the last-2-components (`"gt/town"`, `"[project]/mcp_agent_mail"`). Host-agnostic so laptop + Mini + CI share one list.
2. **Each entry documented in a comment** with a link to the bead that owns the "why" — so re-audit is a lookup, not a re-diagnosis.
3. **Applied at discovery time**, not report time — the suppressed entries never enter the pipeline, so they don't inflate "surveyed" counts or ranking denominators.

Example (from `[project]/scripts/nw-triage.py`):

```python
# Stores that are known dormant / expected-to-fail bd queries and would
# otherwise pollute the "Errors" section every night. Match is on the last
# two path components so it works host-agnostically without ~/ resolution.
# Each entry MUST have a linked bead explaining the state, so re-audit is a
# lookup rather than re-diagnosis.
#
#   "gt/town"                     — pre-schema_migrations bd store, zero
#                                   data; see [project]-8n5w (diagnosis)
#                                   + [project]-yj6g (archive-vs-migrate).
#   "[project]/mcp_agent_mail"   — 168-issue pre-dolt SQLite store the
#                                   current bd binary cannot read; see
#                                   [project]-9bks (decision).
SUPPRESSED_STORE_LABELS: frozenset[str] = frozenset({
    "gt/town",
    "[project]/mcp_agent_mail",
})
```

Applied at both local scan (`find_local_repos`) and remote scan (`parse_remote_summaries`) discovery points:

```python
if _label_for(parent) in SUPPRESSED_STORE_LABELS:
    continue
```

## Why this works

- **Reversible** — remove the entry, the item comes back into the report. Never destroys data.
- **Auditable** — the comment block IS the docs. `grep SUPPRESSED_STORE_LABELS` gives you the current expected-failure list + the bead ids that own each.
- **Discoverable** — new operators reading the scanner source see the pattern immediately.
- **Defers the real decision without losing it** — the linked bead is the "when we care" surface; the scanner just stops nagging until then.

## When NOT to use this pattern

- **When the "known state" is a bug you should just fix.** The suppression list is for deferred/dormant items where the real answer is "archive-later" or "operator sign-off pending", not for real bugs you're too lazy to address.
- **When the scanner has no bead-tracker to link to.** Without a follow-up bead, "suppressed" becomes "forgotten forever". If your project has no issue tracker, use a `# TODO(2026-01-01): resurface if not resolved` timeout-comment instead.
- **When the check itself is wrong.** If your scanner is producing false positives across many items, fix the scanner logic, not the report.

## The 3-per-week ceiling heuristic

If your suppression list grows past ~3 entries in a working week, that's a signal:

- The scanner might be flagging too many state-drift items you don't own → tighten scope.
- OR you're procrastinating on a class of decisions → schedule a triage session.

## Related Patterns

- **[[2026-05-16_upstream-noise-flood-bulk-close-source-pointer]]** — the reactive counterpart: when noise has already flooded the tracker, bulk-close with source pointers. This pattern is the proactive complement — prevent the noise from ever entering the report.
- **[[2026-05-20_per-detector-error-isolation-audit-pipelines]]** — different concern (per-detector fault isolation), but shares the "scanner UX must degrade gracefully" instinct.
- **[[2026-05-12_pin-tests-declarative-policy-manifests]]** — pin-tests protect a declarative allowlist against accidental deletion; the same discipline could guard a `SUPPRESSED_STORE_LABELS` set once it becomes load-bearing.

## Grounding

Applied 2026-07-04 in [project] commits b49f93c + fa252c0. Before: `nw-triage` errors section listed 3 items every night (gt/town, mcp_agent_mail, nested [project]/[project] ghost). After: errors section absent, real signal preserved, 18 repos surveyed cleanly. Each suppressed entry links to a live bead ([project]-yj6g, [project]-9bks) that owns the deferred decision.
