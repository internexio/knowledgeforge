---
title: Critic-finding triage — Strategist for spec-MUST violations, deferred-doc for forward-compat
source_mode: critic
novelty_type: emerging_pattern
grounding_score: 0.75
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-13
tags: orchestration, methodologies, routing, empirical
related_entries: 
  - orchestration/spec-commit-before-impl-commit.md
  - architecture/pattern-extraction-reuse-heuristic.md
  - methodologies/2026-05-13_verify-audit-claims-before-designing-fix.md
---

# Critic-finding triage — Strategist for spec-MUST violations, deferred-doc for forward-compat

**Scope note:** This pattern was extracted from a single KnowledgeForge chain (Critic → Builder → Strategist → Builder → Critic). It assumes the surrounding workflow has distinct Critic, Builder, and Strategist roles with the authority boundaries KF defines — Builder downstream of contracts, Strategist owning spec amendments. Triage shape will not transfer cleanly to workflows lacking that role separation; treat as an emerging pattern pending broader validation.

Critic produces severity-categorized findings. Not all findings of the same severity get handled the same way. Two distinct triage paths emerge in practice when Builder receives a Critic finding:

## Path 1 — Spec-MUST violations → escalate to Strategist

When a Critic finding identifies that the proposed implementation violates a "MUST" or other contract-level requirement in an upstream spec, Builder cannot resolve it alone. Builder is downstream of the contract; their job is to honor it. The right unit of work is a **spec amendment**, not a code workaround.

**Flow:**
1. Critic flags the violation
2. Builder annotates "needs Strategist" and halts the revision pass
3. Strategist surveys the option space:
   - (a) Confirm spec stands; Builder must redesign within it
   - (b) Amend spec to authorize a previously-disallowed approach
4. Strategist owns spec amendments because Strategist sees cross-cutting consequence space; Builder sees one path

**Why this matters:** Prevents Builder from contorting code around a spec violation. Cleaner outcome: explicit spec amendment + revised implementation, not a hidden re-implementation cost buried in Builder's workaround.

## Path 2 — Forward-compat findings → document at the phase where they'd manifest

When a Critic finding identifies a real bug that only manifests at a later development phase (v1+ concurrency, multi-machine, scaled volume), the v0 fix is wrong—premature, often the wrong shape because the actual conditions aren't yet observable. 

**Right action:** Builder documents the finding in the spec at the phase where it'd manifest, with a clear annotation of the trigger condition. v0 ships clean; v1+ implementer reads the spec, sees the flag, addresses it before crossing the trigger.

**Why this matters:** Prevents premature fixes that achieve the wrong shape. Avoids implementing deduplication or concurrency logic for a scenario we can't observe and can't validate. Phase-forward documentation acts as a tripwire: future implementer reads it and knows the condition before hitting the bug.

## Triage Decision Tree

When a Critic finding lands, Builder evaluates the trigger condition:

| Trigger condition | Path | Action |
|---|---|---|
| Violates a "MUST" in upstream spec | 1 | Annotate "needs Strategist"; halt this revision pass; escalate |
| Manifests in the current phase | (default) | Builder revises plan to address |
| Manifests only at a later phase | 2 | Builder adds note to spec at that phase; current ship unchanged |
| Ambiguous trigger | (default to Path 2 with caveat) | If unsure when it manifests, document AND fix conservatively |

## When This Does NOT Apply

- Finding is at code-quality level (test theater, arbitrary bound, miscited reference) → Builder resolves directly
- Finding is a contradiction within the plan (not against upstream spec) → Builder resolves
- Finding is a missing failure mode → Builder adds to plan; no spec escalation needed

## Empirical Grounding (KF Chain 2026-05-13)

### Path 1 — Critic Sev 1 #3 (§11.4 violation)

**Iteration-loop v0 Phase 1, baking pipeline contract:**

- **Finding:** Critic identified "bd-as-cost-meter does NOT satisfy §11.4's 'MUST use Dolt's transaction primitives'"
- **Builder defense:** "v0 concurrency=1 → no R-M-W race needs Dolt transaction syntax"
- **Critic counter:** Forward-compat claim is false; switching from bd notes JSON to Dolt SQL table is re-implementation, not upgrade
- **Escalation:** Builder escalated to Strategist
- **Strategist resolution:** Surveyed 4 paths (direct Dolt SQL / bd-as-cost-meter / amend §11.4 / JSONL-append-with-bd-identity); selected JSONL-append path with §11.4 amendment
- **Amendment:** Added primitive to §11.4: "append-only event logs satisfying POSIX-atomic-append semantics"
- **Outcome:** Builder revised plan; Critic re-pass cleared finding as RESOLVED
- **Artifact:** Baking pipeline contract (authority file, lines 362–389)

### Path 2 — Critic re-pass Sev 2 #1 (concurrent polecat double-release)

**Same iteration, post-amendment:**

- **Finding:** "Concurrent polecat sweeps could double-release — §11.4 amendment's 'commutative' claim is incomplete"
- **v0 risk:** ZERO (single machine, single polecat)
- **v1+ risk:** Phase 4 forward-compat surface (multi-polecat coordination)
- **Action:** Builder documented in v0.3 architecture §7.4 phase-forward note:
  ```
  Phase 4 forward note — polecat synthetic-release idempotency required at Phase 4. 
  Required mechanism: event_id = sha256(session_id + 'expired-swept-' + work_type).
  ```
- **Outcome:** v0 First Reversible Step shipped unchanged; Phase 4 implementer has explicit instruction
- **Commit:** [project] `6ad9f77`

Both paths produced ship-ready v0.3 code.

## Related

- **builder-after-critic-revision-flow** — Builder's complete response surface to Critic findings (close relative; this entry adds the routing question Builder asks first) — concept-tag, not yet a wiki entry
- **forward-compat-vs-premature-optimization** — broader principle this triage strategy applies to — concept-tag, not yet a wiki entry

## Source Context

KnowledgeForge chain executed 2026-05-13 for iteration-loop v0 Phase 1 specification and baking-pipeline implementation. Critic mode produced severity-categorized findings; routing patterns emerged across two distinct cases (Strategist escalation vs. phase-forward documentation). Pattern has repeatable applicability: any Critic-Builder-Strategist loop over a spec-driven implementation will encounter these decision points.
