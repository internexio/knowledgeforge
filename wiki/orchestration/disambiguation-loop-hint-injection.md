---
title: Disambiguation Loop Hint Injection
source_mode: expert
source_session: redacted
created: '2026-04-23T00:00:00Z'
date: '2026-04-23'
confidence: 0.92
grounding_score: 0.92
grounding_source: Direct read of modules/01_navigator.md v6.6.3, loop_detection block
  (lines 248-279, 460-464, 555-559). Module 16 circuit breaker consulted for contrast.
  Grep confirmed zero prior wiki matches on confusion-detection, loop-detection, framing-hint,
  or disambiguation-loop terms.
novelty_type: transferable_framework
staleness_risk: stable
importance: 3
pinned: false
accreted_in: 6.6.3
related:
- modules/01_navigator.md
- modules/16_circuit_breaker.md
- wiki/architecture/scaffolding-vs-patching-pattern.md
---

# Disambiguation Loop Hint Injection

## Pattern

When an agent runs a clarification/disambiguation protocol and the user's response is itself ambiguous for the second consecutive iteration, inject a one-line **framing hint** — a concrete vocabulary example of a request the agent knows how to handle — before escalating to a hard stop.

This is distinct from asking another clarifying question. The user has already failed twice to produce a parseable intent; the problem is not lack of information but lack of vocabulary. A vocabulary example short-circuits the loop; another question deepens it.

---

## Problem Solved

An agent with a clarification protocol can enter a disambiguation loop: the agent asks "what do you want to do?", the user replies with something equally ambiguous, the agent asks again. Three-round loops before a circuit breaker are standard, but the second-round fire is a structural opportunity: the user is not ignoring the question — they don't know how to phrase their intent in terms the agent understands.

At the second consecutive fire, vocabulary injection is lower cost than another open-ended question and has higher probability of breaking the loop.

---

## Protocol (KF Navigator 6.6.3 Specification)

**Trigger condition:** Both must be true:
1. This is the second consecutive Navigator fire in the session
2. The user's prior clarification response was itself ambiguous (Navigator fired on it)

**Action:** Append a one-line framing hint to the normal clarifying question output. Do not replace the question — append after it.

**Hint format:** `"Try phrasing like: '[mode-trigger verb] me [X]' or '[mode-trigger verb] why [X] is [Y].'"`

The verbs in the hint examples must be ones the agent recognizes as mode-trigger signals. This makes the hint functional — it shows the user the vocabulary that unlocks routing — rather than generic.

**State inference:** Whether this is the second consecutive fire is inferred from conversation context. No session variables required. The agent reads whether Navigator fired on the immediately preceding user turn.

**Non-activation cases (do not inject hint):**
- First Navigator fire — too early; one clarification round is expected
- Third consecutive fire — circuit breaker applies; hint would delay a necessary halt
- User's prior response expressed genuine uncertainty ("I don't know", "not sure") — user hasn't formed intent; vocabulary examples don't help; proceed to circuit breaker early

---

## Key Design Insight

**Framing hints vs. more clarification:** When a user is stuck in a clarification loop, the cause is usually vocabulary mismatch, not information withholding. More clarifying questions probe for information the user doesn't know how to articulate. A vocabulary example demonstrates the shape of an answerable request, which the user can then mirror or contrast.

**State from context, not variables:** Session state (consecutive fire count) is readable from the conversation transcript without maintaining explicit session variables. This keeps the pattern lightweight and composable.

**Intervention at the structural midpoint:** The second fire is the right injection point. First fire = normal operation. Third fire = circuit breaker territory. Second fire is the structural gap where early intervention has positive expected value: low cost (one appended line), meaningful probability of breaking the loop, no harm if the user was already recovering.

---

## Applicability Beyond KF

Use this pattern in any agent system where:
- The agent has an explicit intent-classification or routing step that can fire on ambiguous input
- The agent serves a bounded domain with a finite vocabulary of recognizable request types
- Users are not domain experts and may not know how to phrase requests the agent can handle

**Concrete applicability:**
- Customer support bots with intent routing
- Code assistant agents with mode dispatch (build / debug / explain / test)
- Any multi-mode agent where the routing predicate requires the user to signal a mode
- CLI tools with command classification that accept natural language

The pattern is particularly valuable when the agent's domain vocabulary is non-obvious: users arrive with a goal but no model of the agent's capabilities.

---

## Anti-Patterns

**Inject hint on first fire:** Skips the normal clarification round. Users who would have clarified successfully on their own get an unnecessary vocabulary lesson.

**Inject hint on "I don't know" responses:** When the user signals genuine uncertainty about their own intent, vocabulary examples don't help. The problem is intent formation, not vocabulary. Proceed to circuit breaker early.

**Generic hint ("be more specific"):** A hint that doesn't demonstrate the agent's actual vocabulary offers no new information. The hint must use concrete examples drawn from the agent's recognized request types.

**Hint as replacement for the clarifying question:** The hint supplements the question; it doesn't replace it. The question anchors the disambiguation attempt; the hint provides vocabulary scaffolding alongside it.

**Session variable for consecutive fire count:** Inferring from conversation context is sufficient and keeps the pattern stateless. Adding a session variable for this single purpose is premature infrastructure.

---

## Reuse Context

Reference this entry when:
- Designing a clarification or disambiguation protocol for any agent with intent routing
- Evaluating whether a circuit breaker is the right second-round response — it isn't; hint first at second fire, circuit breaker at third
- Deciding what a vocabulary hint should contain — it must use the agent's actual recognized trigger vocabulary, not generic phrasing advice
- Reviewing agent UX for systems where users are non-experts in the agent's domain
