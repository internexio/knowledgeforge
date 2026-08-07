---
title: Schema maxLength caps on LLM reasoning fields cause schema_violation + retry timeout
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 0.95
staleness_risk: stable
importance: 4
pinned: false
created: 2026-07-23
domain: diagnostics
topic: schema-validation
tags: schema-validation,llm-output,pipeline-reliability,adversarial-critic
related_entries: []
---

# Schema maxLength Caps on LLM Reasoning Fields Cause Schema_Violation + Retry Timeout

## Pattern: LLM reasoning fields fail silently when schema imposes hard maxLength caps

### What happened (grounding)

The [project] baking pipeline's adversarial critic generated a valid HIGH-severity finding about a proposed GDRIVE_OUTPUT accessibility check. The finding's `fix` field contained a three-part requirement specifying:
1. use gdrive-read.sh with timeout
2. hard ceiling on the whole validation hook
3. warn-and-proceed failure mode

This was correct and necessary detail. But the `CriticFinding.fix` schema field had a `maxLength: 1000` constraint.

**Result:** `schema_violation: adversarial_findings.0.fix: "..." is too long` on the first attempt, then timeout on the retry attempt. The valid finding was silently dropped. The routing log recorded this as:
```
critic_adversarial: chain failure source=nm-xmo4 reason='retried: 1st=schema_violation...; 2nd=timeout'
```

The fix was commit `20e268e`: "remove maxLength cap on CriticFinding.fix — 1000 still too tight."

A prior commit `4863b62` had raised the cap to 1000 from a lower value — same failure mode, same root cause, just delayed.

### Why this happens

LLM-generated reasoning fields (fix recommendations, rationale, adversarial critique) are inherently verbose when the finding is genuinely complex. A schema `maxLength` that feels generous for simple cases (100 chars, 500 chars, 1000 chars) will be exceeded by any multi-part fix recommendation or nuanced critique.

The cap-raise-and-fail cycle is predictable and repeating:
- A hard cap causes valid findings to be dropped
- Operator notices the drop, bumps the cap
- LLM generates similarly-lengthed output on next run
- Same failure, now at a higher cap threshold
- Cycle repeats until the cap is removed entirely

### Pattern: What to do

**Remove `maxLength` from free-form LLM reasoning fields entirely.** Apply `maxLength` only to:

- **Structured enumerable fields** — e.g. `verdict: "reject" | "passable" | "clean"` (use enum constraints, not maxLength)
- **User-facing display fields with a known UI width budget** — e.g. a card title field that must fit in a 120px container
- **Fields that feed downstream systems with hard limits** — e.g. routing-log headline, 480-byte JSONL line cap

For fields that capture reasoning (`fix`, `rationale`, `critique`, `explanation`), use **no cap or a very high sentinel** (e.g. 10000) that only catches runaway loops, not legitimate multi-point reasoning.

### When this does NOT apply

- **Structured enumerable fields SHOULD have enum constraints**, not maxLength
- **Fields that directly populate a downstream system with a hard byte limit MUST respect that limit** — the cap belongs at the truncation layer, not the schema layer. Example: the routing log `request_text` has `_LOG_HEADLINE_CAP = 80` because the JSONL line itself has a 480-byte hard cap; the request-truncation happens in the headline-setter, not in the schema that validates the finding body.
- **LLM output fields used for exact matching or key lookup should have exact-length or bounded constraints**

### Diagnostic signal

**If you see `schema_violation: [field]: "..." is too long` followed by `2nd=timeout` in a retry pattern**, the field is a free-form reasoning field with an undersized cap.

The retry times out because the LLM will generate a similarly-lengthed response on the second attempt — the cap was the limiting factor, not the LLM's concision. Each retry bumps the context (showing the prior rejection) but the LLM's natural output length for that type of reasoning remains unchanged.

### Related commits in [project]

- `4863b62` — raised CriticFinding maxLength to 1000 (first cap-bump, same root cause)
- `20e268e` — removed maxLength cap on CriticFinding.fix entirely (correct fix)
- `72663bd` — raised routing-log headline cap 40→80 (separate: this IS a structured field with a downstream limit)

## When This Applies

- LLM-facing schema fields that collect reasoning, explanation, or multi-part recommendations
- Adversarial critic findings, strategic analysis, synthesis output
- Any field where the LLM's natural output length varies by problem complexity
- Debug/diagnostic output from LLM chains (fix recommendations, rationale, alternative approaches)

## When This Does NOT Apply

- Enumerable output fields (enum constraints, not maxLength)
- Display fields with hard pixel-width or character-count UI budgets
- Fields that feed exact-match lookup or key systems
- Fields with documented truncation layers downstream (the cap belongs in the truncator, not the schema)

## Source Context

[project] overnight-2026-07-23 / [project] baking pipeline adversarial critic. The critic correctly identified a multi-part requirement but the schema rejected it as "too long." Discovered via routing log inspection (schema_violation + timeout retry pattern).
