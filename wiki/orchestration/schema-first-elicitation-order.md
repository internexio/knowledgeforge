---
title: Schema-First Elicitation Authorship Order
source_mode: synthesizer
source_session: redacted
created: '2026-04-21T00:00:00Z'
date: '2026-04-21'
confidence: 0.92
grounding_score: 0.92
grounding_source: 'VisionForge Unified composition chain. Sev 1 finding [2]: grep
  confirmed behavioral_signals, problem_statement, desired_state, acceptance_criteria
  all had zero matches in wf-elicitation.md. Field name mismatch (demographic_signals
  vs behavioral_signals) was the mechanism. Every brief exits elicitation failing
  the completeness gate.'
novelty_type: transferable_framework
staleness_risk: stable
importance: 4
pinned: false
accreted_in: '6.5'
related:
- wiki/orchestration/multi-framework-cp-composition.md
- wiki/orchestration/adversarial-filename-audit.md
- modules/02_builder.md
- modules/07_critic_agent.md
---

# Schema-First Elicitation Authorship Order

## Pattern

When a pipeline has an upstream elicitation module that produces a structured artifact (brief, schema, request object) validated by a downstream module's completeness gate:

**Define the consuming schema completely first. Derive elicitation questions from the schema's required fields. Never author them in parallel.**

**Steps:**
1. Define the consuming schema completely first — required fields, optional fields, types, validation rules
2. Extract the required fields list with exact field names as they appear in the schema
3. For each required field: confirm the elicitation module includes a question or inference path that populates that exact field name
4. For fields with minimum count constraints (e.g., `behavioral_signals[] ≥ 3`): confirm elicitation generates that minimum before the brief exits
5. **Run grep verification:** for each required field name, search the elicitation module source — zero matches is a blocking failure regardless of semantic similarity to fields that do exist

---

## Why Grep, Not Narrative Review

The causal mechanism for failure is structural: elicitation authors use natural-language-derived field names (`demographic_signals` — what you ask about audiences); schema authors use pipeline-logic field names (`behavioral_signals` — what COS modules need). Names are semantically adjacent, structurally distinct.

A narrative read of the elicitation module will likely judge it complete — it asks about the audience, the goal, and the desired output. Only the grep check against exact required field names reveals the structural mismatch.

**Zero matches on any required field name = blocking failure**, regardless of what the module says in prose.

---

## Anti-Pattern — "Parallel Authorship, Align Later"

Write elicitation and the consuming schema in parallel, planning to align them in review.

**What breaks:** VisionForge's `wf-elicitation.md` elicited `audience.demographic_signals` while `kf-04-spec-templates-extension.md` required `audience.behavioral_signals[]` (≥3) as a required field. Every brief exits elicitation already failing the completeness gate. The pipeline appears to run — elicitation completes, a brief is produced — but every downstream step operates on a brief the system formally considers invalid. This was the most insidious Sev 1 finding: no error is raised, plausible-looking degraded output is produced.

---

## Evidence from VisionForge

- Sev 1 finding [2] confirmed by grep: `behavioral_signals`, `problem_statement`, `desired_state`, `acceptance_criteria` all had zero matches in `wf-elicitation.md`
- A narrative read of the elicitation module would likely have judged it complete — it asks about the audience, the goal, and the desired output
- Only the grep check against exact required field names revealed the structural mismatch

---

## Reuse Context

Reference this entry when:
- Authoring any elicitation module that feeds a schema-validated downstream module
- Any future VisionForge deployment reusing the Unified_Brief schema: elicitation must be re-derived from the then-current schema required fields, not from prior elicitation modules
- Code review of pipeline modules: grep the elicitation source for each required field name in the schema before approving
- The failure class is guaranteed to recur whenever elicitation is authored before or parallel to its consuming schema
