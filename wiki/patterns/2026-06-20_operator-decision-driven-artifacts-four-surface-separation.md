---
title: Operator-decision-driven artifacts — separate the briefing, the bead, the field state, and the audit trail
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.85
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-20
domain: patterns
topic: workflow-design
tags: workflow, decision-trail, operator-handoff, artifact-management, documentation, schema, beads, governance
related_entries:
  - architecture/2026-05-18_bead-as-context-anchor-deferred-runbooks.md
  - methodologies/2026-06-19_operator-review-gate-in-semi-automated-workflows.md
  - methodologies/2026-06-17_tracker-state-drift-at-session-boundary.md
  - patterns/2026-06-15_fail-closed-publish-guards-multi-target-compiler.md
---

# Operator-decision-driven artifacts — four-surface separation

## The pattern

When an artifact (a config file, a YAML card, a schema definition, a brand decision document) has fields that require operator/human judgment — fields not derivable from code, first principles, or static analysis — those fields need FOUR coordinated surfaces:

| Surface | Purpose | Format |
|---|---|---|
| **1. Briefing doc** | Frames the question for the operator: options, sources, trade-offs, what each choice blocks | Markdown, version-controlled near the artifact |
| **2. Bead / issue** | Opens the question on the human queue with a clear "Resolve via..." instruction; stable address for tracking | Issue tracker (bd, Linear, GitHub Issues, etc.) |
| **3. Artifact field state** | Marks the field as `OPEN-PENDING-{role}` so downstream consumers don't act on it; tracks open items in a `deferred_open` list | The artifact itself (YAML, JSON, etc.) |
| **4. Audit trail** | Logs the verdict + date + verdict_summary when resolved; preserves the decision history without re-litigation | A `resolved_history` list in the artifact |

The artifact has a clean state machine:

```
field: OPEN-PENDING-{ROLE}                         → field: <verdict>
deferred_open: [<bead-id>, ...]                    → deferred_open: [...] (remove)
resolved_history: [...]                            → resolved_history: + {bead, field, resolved_at, verdict_summary}
```

When `deferred_open: []`, the artifact is **ready for downstream consumers** (schema.org emit, generated content, gated CI checks, etc.).

## The mistake this pattern prevents

Without this discipline, operator decisions tend to:

- **Disappear into chat history** — "we decided this in a meeting last week, can someone find the message?"
- **Get re-litigated repeatedly** — the next person to encounter the question sees no record of the prior verdict
- **Block downstream work without a clear handoff** — agents/contributors don't know whether they can proceed past `OPEN-PENDING-...`
- **Drift from the artifact** — verdict was X verbally, artifact still says Y silently. Schema gets emitted with stale value.
- **Lose the why** — even if the verdict propagates to the artifact, the *rationale* and *what-was-considered* vanishes, so when conditions change nobody knows if the prior verdict still applies

## Concrete implementation (lived 2026-06-18 → 2026-06-20)

For a company entity card (`[project]/cos/docs/entity-card/`):

```
README.md                            — index, provenance, status table
ground-truth-pass-2026-06-18.md      — read-only discovery report (frozen snapshot)
canonical-card-v1.0.yaml             — the ratified machine-readable artifact
open-decisions.md                    — operator-facing briefing for open questions
```

Each open question in `open-decisions.md` contained:

- **Heading**: `## D<n><role> — <question>  ·  Owner: <David|Counsel>  ·  Bead: <id>`
- **Options table**: with sources for each ("only variant in repo at file:line", "off-site only per audit")
- **Why it needs a decision**: what gets unblocked when it resolves
- **Blocks**: what's specifically gated
- **Resolve via**: `bd human respond <id>` (or equivalent for whatever queue tool is used)

The card YAML had matching fields:

```yaml
founder:
  linkedin_url:
    canonical_for_card: "OPEN-PENDING-DAVID"
    in_repo: "https://www.linkedin.com/in/davepedersen/"
    canonical_note: "Audit found a /in/internexio/ variant off-site only..."

deferred_open:
  - {field: "founder.linkedin_url.canonical_for_card", bead: "cos-merw", reason: "..."}
```

When the operator responded with a verdict, three coordinated mutations:

1. **Card YAML**: field flipped to the chosen value, gained `resolved_at` + `resolved_by` + `note`; `deferred_open` entry removed; new entry appended to `resolved_history` with verdict_summary
2. **open-decisions.md**: question heading struck through (`~~Original question~~ ✅ RESOLVED <date>`), verdict inlined as a blockquote
3. **Bead**: closed with the verdict as the closure reason, providing the audit trail in the issue tracker

After 3 operator decisions all resolved (D2a + D2b + D3-legal), `deferred_open: []` signaled the card was emit-ready.

## When the pattern doesn't apply

- **Pure-code decisions** (anything verifiable from first principles, code inspection, or unit tests) — no operator needed; just make the decision in PR review.
- **Trivial decisions** (which color hex code to use) — overhead of the pattern exceeds the decision-cost.
- **One-shot decisions that don't need to be re-litigated** — the audit trail provides no future value.

Best fit: artifacts that combine machine-derivable fields with operator-judgment fields, where the verdict needs an audit trail and the decision could plausibly resurface.

## Variations worth considering

- **Two-stage briefing**: separate the discovery report (frozen snapshot of what was found) from the briefing (decision options) — the [project] entity card did this: `ground-truth-pass-2026-06-18.md` is the snapshot; `open-decisions.md` is the briefing. The snapshot doesn't change when decisions resolve.
- **Cross-reference both directions**: each bead description has a "see briefing at <path>" pointer; the briefing has a "tracking at bead <id>" pointer. Stable bidirectional navigation.
- **Counsel-only items vs operator-only items**: tag each question by the role that can resolve it (`Owner: David` vs `Owner: Counsel`) so the operator can route correctly.

## Composes with

- **[architecture/2026-05-18_bead-as-context-anchor-deferred-runbooks.md]** — the bead-as-anchor pattern is the persistence layer for surface 2 (the bead). This entry extends it: instead of a single bead carrying the full runbook, the bead points to a briefing doc that frames operator-judgment options, and the artifact carries machine-checkable state alongside.
- **[methodologies/2026-06-19_operator-review-gate-in-semi-automated-workflows.md]** — the operator-review-gate pattern handles the gate between generation and publication. This entry handles the artifact-level discipline that lets a gate operate: without `deferred_open: []` as a deterministic readiness signal, the reviewer has nothing concrete to gate on.
- **[patterns/2026-06-15_fail-closed-publish-guards-multi-target-compiler.md]** — fail-closed publish guards can check `deferred_open: []` as a publish invariant. The audit-trail discipline lets the guard explain *why* a field has a particular value when challenged.
- **[methodologies/2026-06-17_tracker-state-drift-at-session-boundary.md]** — the three-mutation discipline (card + briefing + bead) is the cure for tracker-state drift at the artifact level: the source-of-truth artifact, the human-facing briefing, and the queue tracker stay in sync because each verdict updates all three atomically.

## Grounding from session

[project]/cos/docs/entity-card/ end-to-end cycle 2026-06-18 → 2026-06-20:

- Card ratified 2026-06-18 with 3 OPEN-PENDING-{DAVID, COUNSEL} fields, briefing doc + 3 beads filed (cos-merw, cos-k83y, cos-0wxd)
- All 3 resolved 2026-06-20 in sequence via the pattern:
  - D3-legal (cos-0wxd, DISC): David's verdict "only DiSC lowercase-i is protected" → card `mbti_disc_legal.status: RESOLVED` + strikethrough + bead close
  - D2a (cos-merw, LinkedIn URL): David's verdict "/in/internexio/" → card `founder.linkedin_url.canonical_for_card: "/in/internexio/"` + SITE update + strikethrough + bead close
  - D2b (cos-k83y, founder title): David's verdict "Founder & CEO" → card `founder.title.canonical_for_card: "Founder & CEO"` + strikethrough + bead close (no site update needed since on-site already matched)
- Final state: card `deferred_open: []`; `resolved_history` has 3 entries with verdict summaries; emit-ready.

Cycle time from ratification to all-resolved: 2 days, with the resolution itself taking ~15 minutes of operator time across all 3 decisions (because the briefing presented each question with sufficient context that no follow-up was needed).
