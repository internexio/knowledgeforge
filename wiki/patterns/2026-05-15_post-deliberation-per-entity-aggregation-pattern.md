---
title: Post-deliberation per-entity aggregation pattern (synthesizer pass)
source_mode: direct
novelty_type: new_pattern
grounding_score: 0.75
staleness_risk: stable
importance: 4
pinned: false
created: 2026-05-15
tags: patterns, architecture, deliberation, persona-convening, llm-aggregation, graceful-degradation
related_entries:
  - architecture/2026-05-14_identity-registry-append-only-event-log-separation.md
  - patterns/2026-05-14_collapse-usestate-discriminated-union-reducer.md
---

# Post-deliberation per-entity aggregation pattern (synthesizer pass)

## The Pattern

For structured-deliberation engines (e.g., a 5-turn buying-committee, a 3-pass expert critique), surfacing a final per-entity verdict (e.g., "champion / supporter / neutral / blocker / vetoing" per persona) is often best implemented as a **single post-deliberation aggregation pass** rather than per-entity prompting during the deliberation itself.

### Core Shape

1. **Runs AFTER** the structured engine completes — not as another turn, not as a parallel call mid-engine
2. **Receives** the full deliberation transcript + entity definitions + the structured-engine's verdict (e.g., the judge's verdict on the highest-stakes opposition)
3. **Emits** per-entity `{stance, rationale}` via ONE LLM call with structured JSON output (not N calls — one batched emission)
4. **Embeds** the stance-derivation table in the prompt as constraints, so the LLM picks rows that fit each entity rather than inventing stances
5. **Persists** to a separate table keyed `(run_id, entity_id) UNIQUE` so re-running cleanly conflicts
6. **Implements graceful degradation EVERYWHERE**: provider error, parse error, schema validation error, isolation violation, persistence error → log + swallow, run still completes
7. **Defensive fetcher in the read path**: wraps `query_all` in `try/except` returning empty list so consumer endpoints don't 500 if the migration hasn't applied yet on this environment

## Cross-Provider Posture

Unlike the deliberation engine itself (where cross-provider isolation is often a hard requirement — see auditor-independence patterns), the aggregation pass MAY share a provider with the judge or synthesizer roles. Aggregation is not deliberation; isolation doesn't apply. The judge_client is often a natural reuse target — it's already proven for structured-output work.

## When This Applies

- Structured deliberation engine with N entities and per-entity output desired
- Verdict can be derived from existing turn outputs + entity definitions (no new deliberation needed)
- Verdict is nice-to-have, not load-bearing (graceful degradation is acceptable — most of the run's value lives in the structured turns)
- Reproducibility is valuable but not strict (LLM is constrained by the embedded derivation table; perfect determinism would require a pure code heuristic)

## When This Does NOT Apply

- Verdict requires new deliberation between entities (use a deliberation turn, not aggregation)
- Verdict must be byte-deterministic across reruns of the same transcript (use a pure code heuristic — the LLM is too non-deterministic even with constraints)
- Downstream consumers can't tolerate missing data (then the verdict IS load-bearing; either re-architect to make it required, or move it inside the deliberation as a fan-out pass)

## Concrete Grounding: BC cos-3bu.4 (shipped 2026-05-15)

After T1-T4 of the BC 5-turn protocol complete, `synthesize_buying_signals` makes one judge_client call:

**Inputs:**
- Persona roster (with role_vector + incentive_vector containing win_condition and veto_trigger)
- T1 reactions (with self-reported VETO_NONE/SOFT/HARD tag)
- T4 verdict text + which persona was the T4 target
- Proposal title + content

**Prompt shape:**
- Embeds a 13-row stance-derivation table (T1 tag × was-T4-target × T4-verdict × win_condition-fit → final_stance ∈ {champion, supporter, neutral, blocker, vetoing})
- Instruction: pick rows matching each persona's T1 tag, T4 exposure, and win condition

**Output:**
- Structured JSON `{buying_signals: [{persona_id, final_stance, final_rationale}, ...]}`

**Parse + validate:**
- One entry per persona
- persona_id matches input verbatim
- stance in enum
- rationale 5-600 chars
- Retry once on parse failure with corrective instruction

**Persist:**
- `buyers_committee_buying_signals` table, UNIQUE (run_result_id, persona_id)
- CHECK constraint on stance enum
- CHECK on rationale length 5-600

### Graceful Degradation Surfaces

- `BuyingSignalSynthesizerError`, `IsolationViolation`, any other Exception in the synthesizer wrapper → log + return (no exception escapes to the orchestrator)
- Persistence error in `_persist_buying_signals` → log + continue (run still finalizes)
- `_fetch_buying_signals` in `get_run_detail` → try/except returns `[]` (RunDetail still renders if migration hasn't applied)
- `RunDetail.buying_signals` is `Field(default_factory=list)` so pre-cos-3bu.4 runs degrade to `[]` automatically

### Template Origin

The implementation was templated from EC's `_run_pass_3` (3-pass expert critique) which emits per-expert `final_stance + final_rationale` as the P3 synthesizer output. **Key difference:** EC's P3 is the END of the deliberation; BC's buying-signal pass is AFTER the deliberation. The pattern works in both shapes.

## Implementation Notes

### Constraint Embedding

The derivation table in the prompt is **not** a hint — it's a constraint. The LLM should understand it as: "Pick the row from this table that matches your assessment of [entity X]." This prevents hallucinated stances that don't map to the deliberation.

### Idempotency

If the aggregation pass fails mid-run (e.g., persistence error) and you re-run, a UNIQUE constraint on `(run_id, entity_id)` surfaces the conflict. Handle with INSERT ... ON CONFLICT DO UPDATE to allow safe reruns.

### Defensive Reads

In the consumer read path (e.g., `get_run_detail`), wrap the fetch:

```python
def _fetch_buying_signals(run_id):
    try:
        return query_all("SELECT ... FROM buyers_committee_buying_signals WHERE run_id = %s", run_id)
    except Exception as e:
        logger.warning(f"Failed to fetch buying signals: {e}")
        return []
```

This ensures old runs (predating the table migration) degrade to empty lists rather than 500s.

## Related Patterns

- **[[identity-registry-append-only-event-log-separation]]** — similar post-hoc aggregation of event streams; applicable when you want a materialized view after the stream is complete
- **[[collapse-usestate-discriminated-union-reducer]]** — batch decision-making shape (though in frontend state, not deliberation)

## Source Context

Discovered during COS Buyers Committee cos-3bu.4 implementation, 2026-05-15. After 4 turns of structured deliberation (T1 reactions, T2-T3 discussion, T4 judge verdict), the product team wanted per-persona buying signals ("would Champion back this?" "would Blocker veto?"). Initial approach: prompt each persona individually after the deliberation. Refined approach: one call with all personas, constrained by the deliberation transcript + a derivation table. Result: cleaner orchestration, easier to test (one call, not N), graceful degradation works naturally (if the pass fails, the run's deliberation value is unaffected).

The pattern is immediately applicable to any structured deliberation engine needing a post-hoc verdict roll-up: expert councils, security reviews, architectural audits, multi-agent consensus patterns.
