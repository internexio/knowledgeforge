---
title: 'Imagination as Suppression: New Evidence for the Patching Principle'
source_mode: expert
source_session: redacted
created: '2026-04-23T00:00:00Z'
confidence: 0.55
grounding_score: 0.55
grounding_source: Single primary paper presenting a hypothesis, not replicated consensus.
  Convergent with three independent KF observations (patching principle, Module 18
  inhibition mechanics, Leonardo anti-cliché prevention-first). Convergence is the
  evidence; promote score if replication emerges.
source_fingerprint: ng-et-al-2026-spontaneous-activity-reshaping-hypothesis
novelty_type: new_evidence_for_existing_pattern
staleness_risk: stable
importance: 3
pinned: false
accreted_in: 7.1.0
citation: 'Ng et al. (2026), "Spontaneous Activity Reshaping Hypothesis."

  Psychological Review.

  '
related:
- wiki/architecture/scaffolding-vs-patching-pattern.md
- modules/18_salience_allocation.md
- modules/21_knowledge_accretion.md
---

# Imagination as Suppression: New Evidence for the Patching Principle

## Core Claim

Visual imagination works by suppressing competing currents in ongoing spontaneous neural activity so the target signal settles out of noise. The brain does not construct images from scratch; it sculpts what is already there by dampening competitors. Ng et al. (2026) term this the "spontaneous activity reshaping hypothesis": the neural substrate is continuously active, and imagination is the selective suppression of off-target activations until the intended pattern is the last one standing. Suppression is the mechanism; construction is the result.

---

## KF Convergences

**1. Patching meta-principle validated at mechanism level**

KF's meta-principle — "patch weaknesses, don't scaffold strengths" — has a structural parallel: patches activate conditionally (suppress when weakness manifests) rather than scaffold unconditionally (build capability in advance). The Ng et al. finding shows this is not merely a software design preference. The brain allocates creative capacity the same way: not by building signal from scratch, but by clearing space for it. The mechanism *is* selective suppression of competitors. Patching works because conditional suppression is how the system that originated the design problem also solves analogous problems — the correspondence is at the level of mechanism, not analogy.

**2. Module 18 Salience Allocation — amplification vs. suppression framing**

Module 18 uses "competitive inhibition" terminology but implements it as amplification-first: compute salience for all tasks, highest salience wins resources. The imagination-as-suppression mechanism suggests an alternative framing: instead of picking a winner and amplifying it, suppress the losers and let the winner settle naturally. In practice the computations are equivalent — but the design emphasis is different. Suppression-first shifts the question from "what should we load?" to "what should we prevent from loading?" For the Phase 1 pre-prompt routing hook, this reframes the design: rather than loading the relevant module's context, the hook could suppress irrelevant module attention before routing commits. The salience stack remains the arbitration mechanism; suppression-first changes which direction the dial is turned.

**3. Leonardo anti-cliché architecture — structurally identical mechanism**

The Leonardo anti-cliché approach applies an adjective-level penalty during generation to dampen attractor formation around common phrase patterns before structure forms around them. This is structurally identical to imagination-as-suppression: you do not generate the cliché and scrub it post-hoc; you prevent the attractor from settling in the first place. Pre-suppression of attractors produces the target output through clearing, not construction. The three-way parallel — biological imagination, KF routing, Leonardo generation — is the load-bearing convergent evidence for this entry.

---

## Implications

The design reframe: suppression-first over amplification-first. The question is no longer "which signal to boost" but "which competitors to silence."

For KF architecture specifically:

- **Pre-prompt routing hook (Phase 1 critical path):** frame as suppressing irrelevant module attention at prompt entry, not loading relevant modules on demand. Same mechanism, different emphasis — but suppression-first aligns with how the brain allocates creative capacity and avoids the "load everything relevant" trap that produces context bloat.
- **Salience Allocation (Module 18):** a note flagging the suppression-first reframe is added as a spec-level observation (see Module 18 v7.1.0 changelog). Not an implementation change — a design framing for the next revision pass.

---

## What It Does Not Change

The aphantasia → overactive-agent analogy was considered and rejected. If imagination is suppression, then overactive agents would map to insufficient suppression of competing activations, which maps structurally to aphantasia (inability to sustain a suppression pattern). The analogy was rejected because the mechanism does not transfer cleanly: aphantasia involves the inability to initiate or sustain suppression, not merely insufficient suppression magnitude. Using it as a design guide would require claiming the *same* causal mechanism operates in LLM attention, which is not established by Ng et al. The analogy is noted and set aside; the three convergences above are the load-bearing evidence.

---

## Limits

- **Hypothesis-grade:** Ng et al. (2026) presents a mechanistic hypothesis, not replicated empirical consensus
- **Cross-domain:** neuroscience → AI design is not direct transfer; mechanism analogy, not causal claim
- **Single paper:** grounding score 0.55; promote if independent replication emerges
- **Convergences are independent observations, not controlled tests:** their convergence is suggestive, not confirmatory

---

## Relationship to `scaffolding-vs-patching-pattern`

`scaffolding-vs-patching-pattern` documents *that* patching outperforms scaffolding through three historical artifacts and empirical mechanism evidence (Sofroniew et al., 2026 — emotion vectors in Claude). This entry provides *why* at a biological level: the mechanism that makes patching optimal is suppression, not construction. The two entries are read together: `scaffolding-vs-patching` answers "when to patch and what the evidence is"; this entry answers "what the mechanism is."

---

## Pending Cross-References

**Leonardo anti-cliché architecture** (KF convergence 3) is documented only as a passing reference in `plans/kf-universal-architecture.md` (lines 421, 783) — no standalone doc exists in this repo as of 2026-04-23. When a Leonardo architecture doc is created, it should add a one-line note pointing back to this entry. The cross-reference is directionally correct; the target file does not yet exist.
