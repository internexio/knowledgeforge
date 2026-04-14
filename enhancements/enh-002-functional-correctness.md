# ENH-002: Functional Correctness in Critic
**Mode:** Critic (standard and adversarial)
**Priority:** P0
**Effort:** Low — framing addition to Critic prompt
**Status:** Proposed

## Problem

KF's Critic currently reviews for semantic quality: Is this coherent? Well-reasoned? Complete?
Does it address the question? These are necessary — but they don't catch silent failures.

**Semantic correctness:** The output sounds right.
**Functional correctness:** The output does the right thing.

An LLM can recommend the correct credit card in fluent, well-reasoned prose — and recommend
the wrong card. A spec can be internally coherent and correctly structured — and solve the
wrong problem. Semantic review passes both. Functional review catches both.

Nate's formulation: *"You can't just be tolerating semantic correctness."*

KF's adversarial Critic framing ("this output has at least one significant flaw — find it")
gets close but doesn't explicitly target the semantic/functional distinction. A Critic looking
for flaws will find structural gaps, missing edge cases, weak reasoning — but may miss that
the entire output is correctly built for the wrong goal.

## The Distinction

| Type | Question | Catches |
|------|----------|---------|
| Semantic correctness | Does this make sense and hang together? | Incoherence, gaps, weak reasoning |
| Functional correctness | Does this do what the user actually needs? | Wrong problem solved, correct answer to wrong question |

Silent failures are functionally incorrect. They look semantically correct. Semantic review
doesn't catch them.

## Proposed Fix

Add a **functional correctness check** to Critic's review sequence — both standard and
adversarial passes.

### Standard Critic Addition

After the existing gap-finding pass, add:

> **Functional correctness check:** Set aside whether this is well-reasoned and ask: does
> this actually do what the user needs in practice? Specifically:
> - What is the user's real-world goal (not just the stated request)?
> - Does this output, if acted on, achieve that goal?
> - Is there any scenario where this is semantically correct but functionally wrong?
> If yes, surface it as a finding regardless of severity.

### Adversarial Critic Addition

Update adversarial framing from:
> "This output has at least one significant flaw — find it."

To:
> "This output has at least one significant flaw — find it. Start with functional correctness:
> does this do what the user actually needs, or does it correctly solve the wrong problem?
> Then check semantic quality. Report severity High/Critical only."

## Failure Example

User: "Spec out a webhook handler for Stripe payment events."
Builder produces a well-structured webhook handler — for checkout.session.completed only.
User actually needed payment_intent.payment_failed handling (for dunning).
Semantic review: passes (coherent, complete for its scope).
Functional review: fails (wrong event, wrong use case).

## Acceptance Criteria
- Standard Critic includes functional correctness as a named review step
- Adversarial Critic leads with functional correctness before semantic review
- Functional correctness findings are surfaced even when severity is medium
  (unlike adversarial which is High/Critical only — functional wrong = always surface)
- Does not replace semantic review — runs in addition

## Anti-Patterns
- Treating "functional correctness" as "does it compile/run" — it's about real-world goal achievement
- Firing functional check on reckonings — only on evaluative+ outputs
- Blocking on functional check — it's a finding surface, not a gate
