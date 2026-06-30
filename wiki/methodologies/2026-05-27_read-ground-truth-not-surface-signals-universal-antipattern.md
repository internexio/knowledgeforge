---
title: Read ground truth, not surface signals — universal debugging discipline
source_mode: direct
novelty_type: reusable_diagnostic
grounding_score: 0.9
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-27
tags: verification, debugging-discipline, anti-pattern, claims-discipline, failure-mode
related_entries:
  - methodologies/2026-05-26_deterministic-scan-before-claiming-refactor-audit-beads.md
  - methodologies/2026-05-13_verify-audit-claims-before-designing-fix.md
  - diagnostics/2026-05-23_beads-multi-database-working-directory-gotcha.md
domain: methodologies
topic: verification
---

# Read Ground Truth, Not Surface Signals — Universal Debugging Discipline

## The Anti-Pattern

**Do not infer the STATE of a system from a surface signal instead of reading the actual contents.**

Surface signals are proxies that often mislead:

| Signal | Common Misinterpretation | Reality Check |
|--------|-------------------------|--------------|
| Empty log file | "This process ran but produced no output" OR "This process never ran" | Read the actual state file / database / process listing / stderr log |
| Filesystem dir count or shape (e.g., "two dirs of the same name") | "One is a duplicate, delete it" | Read the contents of both dirs; check metadata (owner, mtime, db scope) |
| Filename or path structure | "This is inert/stale/deprecated based on the name" | Read the actual file contents or follow active imports/references |
| Queue file emptiness | "No jobs pending" | Query the database directly; check for stalled writers; verify read cursor |
| Past cost comparison in docs | "Old approach superseded; irrelevant now" | Verify what the CURRENT trade-off actually compares (API changes, new vendors) |

Confident claims from surface signals produce **wrong assertions** and **misled action**.

## Why It Recurs

Surface signals are **cheap to read** and the inference **feels safe**. The asymmetric cost is borne by the person who acted on the wrong claim — they waste time, chase ghosts, or corrupt data based on a diagnosis that didn't match reality. When that person is the one who built the thing being dismissed, the wrong claim also erodes trust.

The mental shortcut is: "I can see this signal cheaply, so I can infer state cheaply." This is true in stable systems but false in active engineering: logs rotate, databases fill asynchronously, filenames get repurposed, docs get stale mid-execution, cost comparisons become outdated between writing and reading.

## The Rule

Before asserting that something is:
- **missing** (doesn't exist),
- **broken** (not working as intended),
- **duplicate** (redundant copy),
- **outdated** (replaced by something better),
- **inert** (not actively used),

read the **ground truth**. State the specific source you actually inspected:

- For "process never ran" → check: process log + return code + state artifact mtime + database commit timestamp
- For "duplicate dir" → read: file listings, content hashes, owner/mtime, active references to each
- For "module is stale" → check: git history of that file + grep for current imports/usage
- For "queue is empty" → query: the actual database, not the queue file on disk
- For "approach is outdated" → verify: what the current trade-off actually compares (not the prior one)

Make the investigation **deterministic, cheap, and falsifying** (see related entry on audit-doc verification).

## Concrete Session Grounding

Single session ([project]-semalytics-2026-05-27) produced **four distinct instances** of the same failure pattern:

### Instance 1: Empty log file → false absence claim
**Claim:** "North Star Steps 2-4 (morning suggestion, approval contract, execution dispatch) are not yet built."
**Evidence:** Empty `~/agent-workflow/morning-brief.log` file.
**Reality:** Modules existed — `iteration_loop/morning_briefing.py`, `interrupt_envelope.py`, `exec_dispatch.py` — built, tested, wired into the pipeline.
**What should have been checked:** Module existence (`ls iteration_loop/`) + git history (`git log --oneline -- iteration_loop/morning_briefing.py`) + test coverage (`grep -l "def test" iteration_loop/tests/*morning*`).

The empty log proved nothing about code absence. The log's emptiness was caused by missing launchd wiring, not missing implementation. Investigating the wrong signal sent diagnosis down a wrong path.

### Instance 2: Stale cost comparison → inverted trade-off claim
**Claim:** "FastText is likely a full replacement, outdated vs LLM embeddings" (implied: abandon FastText, migrate to embeddings APIs).
**Evidence:** A prior cost comparison in project notes (FastText vs Claude-as-judge, ~6 months old).
**Reality:** The actual current cost comparison was FastText vs Claude-as-judge (not vs dedicated embedding APIs, which Anthropic does not offer). FastText remained the cheaper path for the operator's specific use case.
**What should have been checked:** Re-read the CURRENT cost driver (what's being compared NOW) before claiming a prior analysis was obsolete. The comparison axis changed but the name "embeddings" remained the same.

Trusting the doc name rather than re-examining the actual comparison inverted the recommendation.

### Instance 3: Filesystem shape → false duplicate claim
**Claim:** "Two `.beads/` directories at different paths are duplicates; one is stale and should be deleted."
**Evidence:** Same directory name at two different project roots (filesystem shape signal).
**Reality:** Two **active** Beads databases with **different scopes** — one for SEO/brand work, one for application code. Neither was stale. Both were actively receiving filings.
**What should have been checked:** Read the Beads database metadata (`git rev-parse --git-dir` in each, check mtime, query bead counts, verify active file modification).

Shape-based inference missed the functional separation.

### Instance 4: Directory name → false inert/stale claim
**Claim:** "A nested `/[project]/[project]/` directory is an inert stub and should be gitignored."
**Evidence:** Redundant-looking directory name structure.
**Reality:** The directory was actively receiving beads from a site-monitor worker, but the Dolt database pointed to it was misconfigured. Beads were silently lost. The directory was NOT inert; it was a **data-loss vulnerability** that later filed as a real P2 bug.
**What should have been checked:** Check git history of the directory (`git log --oneline -- [project]/[project]/`) + search for references in active code (`grep -r "[project]/[project]/" src/`) + verify the Dolt scope (`dolt config --list | grep workspace`).

Dismissing based on the name prevented discovering the real bug.

## When This Applies

- Any claim about system state (process status, module presence, data availability, config correctness)
- Debugging production issues ("The cache is empty" → query the cache, don't trust the log)
- Evaluating third-party audit findings ("That recommendation is outdated" → re-verify the current context)
- File-system-based reasoning about project structure ("This module is deprecated" → check imports, not the name)
- Assessing work completion ("This feature is done" → run the tests, don't trust the feature branch name)

## When This Does NOT Apply

- Systems with **verified, automated ground-truth signals** (e.g., a health-check endpoint that's known to be accurate, a Postgres trigger that keeps a state table in sync)
- Claims that **explicitly state their source** ("I just checked the code and...") and the source is current
- Straightforward factual lookups (e.g., "What's the latest Python version?") — these have no ambiguity between signal and state

## Defensive Patterns

When working in systems where surface signals are commonly mismatched with ground truth:

1. **Log-vs-db principle:** Never trust logs for state. Always query the database for the source of truth. (Logs are for debugging, not for asserting state.)
2. **Multi-source verification:** For critical claims, check 2-3 independent sources before asserting state change.
3. **Mtime freshness:** When claiming "not recently modified," check actual file modification times, not names or commit dates.
4. **Import tracing:** When claiming "code is unused," grep for callers in the actual codebase, not in docs or issue titles.
5. **Explicit falsifying test:** Before closing a "verified done" claim, state the specific check that would prove it false if the claim is wrong.

## Cross-References

Related entries:
- [[deterministic-scan-before-claiming-refactor-audit-beads]] — specific application to refactor/audit beads with a 7-day decay heuristic
- [[verify-audit-claims-before-designing-fix]] — pre-design verification of structural claims
- [[beads-disk-reconciliation-discipline]] — keeping bead queue and filesystem in sync
- [[deterministic-first-debugging]] (KF meta) — exhaust deterministic checks before invoking LLM judgment

## Source Context

Discovered during [project]-semalytics session 2026-05-27. User asked for a broad architectural audit. During scoping, I made four distinct false claims based on surface signals (empty log, filesystem shape, filename, stale doc reference) instead of reading actual state. Each caused investigation to veer in the wrong direction. After the fourth instance, the pattern became clear: this is a universal anti-pattern that should apply across all engineering work, not just code audits. The four instances anchored a stronger generalization of the existing audit-doc scanning discipline (which is narrower, focused on 7-day decay windows for audit claims).

