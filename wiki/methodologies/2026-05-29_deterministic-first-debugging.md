---
title: Deterministic-first debugging — exhaust deterministic checks before invoking LLM judgment
source_mode: kf-meta, direct
novelty_type: transferable_framework
grounding_score: 0.9
staleness_risk: stable
importance: 5
pinned: true
created: 2026-05-29
tags: methodology, debugging, verification, deterministic, llm-judgment, kf-meta, triage, anti-rework
related_entries:
  - methodologies/2026-05-26_deterministic-scan-before-claiming-refactor-audit-beads.md
  - methodologies/2026-05-27_read-ground-truth-not-surface-signals-universal-antipattern.md
  - methodologies/2026-05-13_verify-audit-claims-before-designing-fix.md
---

# Deterministic-First Debugging

## The Rule

Before invoking LLM judgment, exhaust deterministic checks. **Before fixing, reproduce. Before acting, triage.** Then state which deterministic checks you ran, so the conclusion is auditable rather than asserted.

This is the KF meta-principle ("Deterministic first") promoted to a standalone entry because multiple methodologies depend on it as a shared parent.

## Why It Matters

LLM judgment is probabilistic, costs tokens, and is *persuasive even when wrong* — a confident wrong answer propagates into every downstream step that trusts it. A deterministic check (`grep`, `find`, `ls`, `wc`, reading the actual file, running the test, `lsof`, `git log`) is the opposite: cheap, repeatable, and **falsifying**. Same input → same output, and a "fail" result definitively settles the question.

Spending judgment on something a one-line command could answer is doubly wasteful: it burns budget *and* risks importing a fabricated premise. The discipline is not "never use judgment" — it's "don't use judgment on questions that have a deterministic answer sitting one command away."

## The Order of Operations

1. **Observe ground truth.** Read the actual file/state/config — not a summary, not a stale memory, not a proxy signal.
2. **Run the cheapest falsifying check.** The smallest `grep`/`wc`/`read`/`curl` that would disprove the hypothesis if it's wrong.
3. **Triage.** Is this even the right problem? Classify the decision type before solving it (reckoning vs. evaluative vs. novel).
4. **Only then invoke LLM judgment** — and only on the residual that deterministic checks genuinely could not resolve.

## The Pattern in Practice

| Question | Deterministic check that precedes judgment |
|--|--|
| "Is capability X missing?" | `grep -r` / `find` / `git log --grep` before claiming absence |
| "Is the server down / mis-pointed?" | `lsof -iTCP`, `curl`, read the config file before any restart |
| "Is this queued finding still valid?" | read the *current* source before acting on a stale suggestion |
| "Did the refactor already ship?" | smallest falsifying test per claim (see related entry) |

## When It Does NOT Apply

- **Genuinely novel decisions** with no precedent and no observable state to check — that is true Novel judgment: expand reasoning and flag for human review, don't pretend a check exists.
- **Creative / generative work** where there is no ground truth to verify against.
- The rare case where the deterministic check costs more than being wrong.

## The Failure Mode It Prevents

The "confident substrate-missing" claim: asserting that code, a capability, or a constraint does not exist when a 5-second `grep` would show that it does. [project]'s project-level "Pre-claim verification rule" (grep + `bd memories` + `git log` before claiming substrate is missing) is a domain-specific instance of this principle; so is reading a full route/function before filing a "missing guard" bead.

## Cross-References

- [[deterministic-scan-before-claiming-refactor-audit-beads]] — applies this rule to stale audit/refactor beads via the "smallest falsifying test per claim."
- [[read-ground-truth-not-surface-signals-universal-antipattern]] — the read-side corollary: check the authoritative source, never a proxy signal that can drift from it.
- [[verify-audit-claims-before-designing-fix]] — pre-design verification of an audit's structural claims before committing to a fix.

## Source Context

Codified in the KF meta-principle (`kf-meta.md`). Promoted to a standalone hub entry on 2026-05-29 because two methodology entries — `deterministic-scan-before-claiming-refactor-audit-beads` and `read-ground-truth-not-surface-signals-universal-antipattern` — both referenced `[[deterministic-first-debugging]]` as a shared parent that did not yet exist (a wiki-linter orphan_link finding). Grounding instances recur across sessions: claiming [project] substrate was missing while modules + tests for it sat in `iteration_loop/`; diagnosing a Dolt port mismatch by reading the port file + `lsof` + metadata before any restart; triaging stale wiki orphan-link findings by reading the current source (which showed 2 of 5 links had already been corrected) before acting.
