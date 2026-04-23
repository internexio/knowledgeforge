# Spec: Module 01 Navigator — Confusion Detection Amendment

**Component:** 2 — Navigator confusion detection
**Target file:** `modules/01_navigator.md`
**Version bump:** 6.6.1 → 6.6.2
**Decision type:** Evaluative
**Date:** 2026-04-23

---

## Purpose

Users who receive a Navigator disambiguation question and respond with another ambiguous reply are stuck in a loop. The current module notes this as a watch-for in Anti-Patterns (L343) but provides no response behavior. This amendment adds a single protocol step that fires a framing hint on the second consecutive ambiguous Navigator response — nudging users toward mode-trigger vocabulary before the Module 16 circuit breaker applies on the third.

Who uses it: Navigator, on the second consecutive Navigator fire within a session when the user's clarification response is itself ambiguous.

Out of scope: first fires, third fires (circuit breaker owns those), "I don't know" responses, any change to the activation predicate from 6.6.1, any new routing index fields or risk tiers.

---

## Insertion Point

**Section:** Ambiguity Detection Protocol
**Insert after:** Step 3 — Resolution (ends at approximately L237 in the module file)
**Insert before:** The closing `---` separator that precedes "Integration with KF-5"
**What comes immediately before:** The Step 3 YAML block ending with `principle: > The question should discriminate...`
**What comes immediately after:** `---` then `## Integration with KF-5 (Decision Classification)`

The new subsection is "Step 4 — Loop Detection" and belongs inside the Ambiguity Detection Protocol section, numbered sequentially after Step 3.

The CC Skill section (starting at `## CC Skill`, approximately L383) contains its own protocol numbered Step 1–4 (where current Step 4 is "Route"). The CC Skill amendment renames the current CC Skill Step 4 to "Step 5 — Route" and inserts a new Step 4 between Step 3 Resolution and routing. See Amendment Text below.

---

## Amendment Text

### Main module section (insert after Step 3 block, before closing `---`)

```markdown
### Step 4: Loop Detection

Applied only on the **second consecutive Navigator fire** in a session when the user's clarification response was itself ambiguous.

```yaml
loop_detection:
  activation_predicate:
    condition_1: This is the second consecutive Navigator fire in this session
    condition_2: The user's response to the prior disambiguation question was itself ambiguous
    both_required: true

  non_activation:
    - First Navigator fire: never — user has not yet attempted to clarify
    - Third consecutive Navigator fire: Module 16 circuit breaker applies instead
    - User response is "I don't know", "not sure", "no idea", or equivalent acknowledgment
      of genuine uncertainty — hint would not help; proceed to circuit breaker early

  behavior:
    append_to_disambiguation_question: true
    hint_format: >
      Append after the clarifying question, on a new line:
      "Try phrasing like: '[mode-trigger verb] me [X]' or '[mode-trigger verb] why [X] is [Y].'"
    hint_examples:
      - "Try phrasing like: 'build me a spec for X' or 'debug why X is failing.'"
      - "Try phrasing like: 'review my spec for X' or 'help me prioritize X vs Y.'"
    hint_is_a_question: false
    counts_toward_one_question_limit: false

  state_tracking: >
    Infer from conversation context. If the immediately preceding assistant turn was also
    a Navigator disambiguation question AND the user's reply to it did not resolve the
    ambiguity (i.e., Navigator fires again on that reply), the loop detection condition
    is met. No routing index fields. No new session state variables. Conversation history
    is sufficient.
```

**Loop detection does not alter the primary activation predicate.** Navigator still fires only when top-2 candidate modes produce different output types (6.6.1 SPEC-3). Step 4 adds a hint layer on top of Step 3 behavior; it does not change when Navigator fires.
```

---

### CC Skill section amendment

In the CC Skill `## Protocol` block (inside `## CC Skill`), the current Step 4 is "Route". Renumber it to Step 5 and insert the following as Step 4 between Step 3 and the renamed Step 5:

```markdown
### Step 4 — Loop Detection (second consecutive fire only)
If this is the second consecutive Navigator fire AND the user's prior clarification was itself ambiguous:
- Append a one-line framing hint after the clarifying question: "Try phrasing like: '[mode-trigger verb] me [X]' or '[mode-trigger verb] why [X] is [Y].'"
- The hint is not a question — it does not count toward the one-question-per-turn limit.
- Do NOT fire on: first fire, third fire (circuit breaker applies), or "I don't know" responses.
- State tracking: infer from conversation context — no new session variables needed.

### Step 5 — Route
After disambiguation, tag decision type: `reckoning | evaluative | predictive | novel`
```

---

### CC Agent section amendment

In the CC Agent `## Protocol` block (inside `## CC Agent`), the current Step 4 is "Route". Renumber it to Step 5 and insert the following as Step 4:

```markdown
### Step 4 — Loop Detection (second consecutive fire only)
If this is the second consecutive Navigator fire AND the prior clarification was itself ambiguous:
- Append hint after clarifying question: "Try phrasing like: 'build me X' or 'debug why X is failing.'"
- Hint is NOT a question. Does not count toward one-question limit.
- Skip on: first fire, third fire (circuit breaker), "I don't know" responses.

### Step 5 — Route
After disambiguation, tag decision type: `reckoning | evaluative | predictive | novel`
```

Also in `## Rules`, add after the "Maximum one clarifying question per turn" line:
```markdown
- On second consecutive ambiguous fire: append one-line framing hint (not a question) to disambiguation response
```

---

## State Tracking

**Approach:** Conversation context inference. [Decision type: Evaluative — two options evaluated against constraint of no new routing index fields.]

Navigator checks whether the immediately preceding assistant turn was a Navigator disambiguation question. If yes, and the user's reply to it failed to resolve ambiguity (Navigator fires again), loop detection activates.

This requires no new session state, no routing index fields, no new memory architecture entries. The conversation history already contains the prior turn. Navigator can read it.

**Why not routing index:** Phase 0 confirmed no routing index schema change is needed or desired for this component. Conversation context inference satisfies the requirement with zero schema cost.

**Why not Tier 3 session memory:** Session memory (Module 19) is for persistent cross-session state. Loop detection is ephemeral within one conversation. Tier 3 is heavier than necessary.

**Assumption:** Navigator has access to the immediately preceding assistant turn in context. This holds in all current deployment patterns (Claude Code, Claude Projects). Probability: high (>0.95).

---

## Version Bump

- **Old version:** 6.6.1
- **New version:** 6.6.2
- **Changelog entry to add:**

```yaml
6.6.2:
  - Add Step 4 Loop Detection to Ambiguity Detection Protocol
  - Confusion detection hint fires on second consecutive ambiguous clarification
  - CC Skill and CC Agent Step 4 renumbered; Loop Detection inserted
  - No routing index changes, no new risk tiers
```

---

## What Does NOT Change

- **Activation predicate from 6.6.1:** Navigator fires only when top-2 candidate modes produce different output types. Unchanged. Loop detection is a behavior layer on top — it does not change when Navigator fires.
- **Maximum one clarifying question per turn:** The hint is a formatting suggestion, not a question. The one-question constraint is not affected.
- **Routing index schema:** No fields added. Conversation context inference requires no schema.
- **Module 16 circuit breaker:** Owns the third consecutive failure. This amendment does not touch or duplicate it.
- **Module 16 "I don't know" handling:** If user says "I don't know" or equivalent, loop detection explicitly skips. Genuine uncertainty is not helped by vocabulary hints.
- **Risk tier:** Navigator remains LOW. No escalation change.
- **Chain patterns:** No new chains introduced.
- **Modes:** No new modes.

---

## Module 06 Cross-Reference Check

Module 06 (`06_quick_reference.md`) currently references Navigator at:
- L95: Agent Modes table row — trigger and action description
- L444: Module reference table — "Ambiguity detection and intent disambiguation"
- L473: Integration flows — "Navigator (if ambiguous)"
- L518: Mode combinations — "Navigator → Any: Disambiguate then route (only if ambiguous)"

None of these entries describe the internal protocol steps. Loop detection is a protocol-internal behavior change, not a trigger or routing change. Module 06 does not need amendment for 6.6.2.

**Action during implementation:** Confirm no Module 06 lines reference the "three-step" protocol count or "Steps 1–3" numbering. If found, update to "Steps 1–4" or remove the step count reference.

---

## Acceptance Criteria

- [ ] "Step 4 — Loop Detection" subsection added to Ambiguity Detection Protocol, after Step 3, before closing `---`
- [ ] Activation predicate specifies: second consecutive Navigator fire AND user's prior clarification was itself ambiguous
- [ ] Non-activation cases specified: first fire excluded, third fire excluded (circuit breaker applies), "I don't know" excluded
- [ ] Hint appended to disambiguation question — framed as formatting suggestion, not a question
- [ ] Hint does not count toward the one-question-per-turn limit — stated explicitly
- [ ] State tracking: conversation context inference, no routing index fields, no new session variables
- [ ] Primary activation predicate from 6.6.1 preserved and explicitly noted as unchanged
- [ ] Version bumped to 6.6.2 in module metadata block
- [ ] Changelog entry added per format: `6.6.2: ...`
- [ ] CC Skill Step 4 renamed to Step 5 (Route); new Step 4 Loop Detection inserted
- [ ] CC Agent Step 4 renamed to Step 5 (Route); new Step 4 Loop Detection inserted
- [ ] CC Agent Rules list updated with hint behavior note
- [ ] No new routing index fields
- [ ] No new modes, risk tiers, or chain patterns
- [ ] Module 06 checked for step-count references; updated if found

---

## Failure Modes

| Failure | Indicator | Mitigation |
|---------|-----------|------------|
| Hint fires on first Navigator turn | User receives hint before any prior disambiguation attempt | Activation predicate check: confirm preceding assistant turn was also a Navigator question |
| Hint fires when user said "I don't know" | User expressed genuine uncertainty; hint unhelpful | Explicit non-activation case for "I don't know" equivalents |
| Hint fires three or more consecutive times | Circuit breaker bypassed | Explicit non-activation on third fire; Module 16 owns recovery |
| Hint treated as a question (breaks one-question limit) | Response contains hint plus a clarifying question and both are counted | Hint format spec: append on new line, no question mark, framed as suggestion |
| State tracking fails in no-context window | Prior turn not visible | Graceful degradation: treat as first fire, no hint |
