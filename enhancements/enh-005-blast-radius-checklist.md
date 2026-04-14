# ENH-005: Blast Radius Checklist in Expert
**Mode:** Expert
**Priority:** P2
**Effort:** Low — structured template addition to Expert HIGH-risk outputs
**Status:** Proposed

## Problem

Expert mode mentions "blast radius" in passing. For HIGH-risk outputs, this is too vague.
The concept exists but there's no structured template that forces Expert to work through
all four dimensions of risk before making an irreversible recommendation.

Nate's framework, derived from actual job postings for trust/security design roles:

1. **Blast radius** — worst case if this goes wrong?
2. **Reversibility** — can you undo this mistake?
3. **Frequency** — how often does this action run?
4. **Verifiability** — can you confirm the output is functionally correct?

These four together determine where to put human oversight and how tight to make guardrails.
Without a checklist, Expert may address one or two and miss the others — leading to incomplete
risk assessment on decisions that warrant the full treatment.

## Proposed Fix

Add a structured **Blast Radius Checklist** as a required template in Expert's HIGH-risk
output section.

### When It Fires
- Expert output classified as HIGH risk tier
- Any recommendation involving: production deploys, irreversible data operations, auth changes,
  financial transactions, AI systems acting autonomously on user data

### Template

```
## Risk Assessment

**Blast Radius**
Worst case if this recommendation is wrong:
- [Describe max damage: data loss / downtime / user impact / financial / reputational]
- Scope: [individual user / team / all users / external / public]

**Reversibility**
Can this be undone if it goes wrong?
- [ ] Fully reversible (can roll back exactly)
- [ ] Partially reversible (data loss possible, service recoverable)
- [ ] Irreversible (no rollback — this is permanent)
If irreversible: what's the minimum viable test before committing?

**Frequency**
How often does this action execute?
- One-time / per-session / per-user / per-request / continuous
- At scale, low-frequency errors become high-frequency — note if frequency increases with adoption.

**Verifiability**
How do you confirm this worked correctly?
- Semantic check: [what it looks like when correct]
- Functional check: [what it proves when correct — different from semantic]
- Observable signal: [metric, log, state change that confirms functional correctness]

**Overall Risk Verdict**
[ ] LOW — proceed, standard monitoring
[ ] MEDIUM — proceed, add verification step before full rollout
[ ] HIGH — human review required before this recommendation is acted on
```

### Integration with Permission Framing

The checklist output feeds directly into KF's existing permission framing:
- Checklist verdict HIGH → output flagged: *"HIGH-risk decision. Warrants review before acting."*
- Checklist verdict MEDIUM → include assumptions and explicit confidence
- Checklist verdict LOW → no framing overhead (standard Expert output)

## Acceptance Criteria
- Blast radius checklist appears on all HIGH-risk Expert outputs
- All four dimensions (blast radius, reversibility, frequency, verifiability) are addressed
- Checklist produces a verdict that feeds the permission framing
- Does not appear on LOW/MEDIUM Expert outputs — only HIGH
- Template is filled out with actual content, not placeholder text

## Anti-Patterns
- Running the checklist on every Expert output — only HIGH-risk
- Using the checklist as a stalling mechanism ("I need more info before assessing")
- Filling in "unknown" for all fields — Expert should make a best estimate with confidence stated
- Confusing semantic verifiability with functional verifiability (the checklist distinguishes them)
