---
title: Helper extraction beats loop refactor when per-step state diverges
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.75
staleness_risk: stable
importance: 3
pinned: false
created: 2026-05-13
tags: [refactoring, code-structure, pipeline-design, state-passing, audit-feedback]
related_entries: [patterns/2026-05-13_phased-god-module-split-facade-first.md, architecture/pattern-extraction-reuse-heuristic.md]
---

# Helper extraction beats loop refactor when per-step state diverges

## The framework

When you face a sequential pipeline of N steps where each step's body looks
similar but the inputs differ, there are two common refactor approaches:

1. **Loop refactor**: extract a `Step(name, runner, args_builder)` dataclass,
   build a `STEPS = [step1, step2, step3, ...]` list, loop over them
   uniformly.
2. **Helper extraction**: keep each step inline but extract the repeated
   boilerplate (accumulate-state / persist / check-cancel) into one named
   helper called from each step.

The decision criterion:

| Per-step state-passing | Recommended |
|---|---|
| Each step is independent (same inputs, same shape) | **Loop refactor** |
| Step N needs the *output* of step N-1 (and N-2…) | **Helper extraction** |
| Mixed (some independent, some chained) | **Helper extraction** for the chained part, optionally **loop** for the independent part |

A loop refactor on a state-chained pipeline forces one of these workarounds:

- **Shared mutable state dict**: `state = {"r1": None, "r2": None, ...}`; each
  runner mutates it. Hides dataflow and re-introduces the bug class the loop
  was supposed to prevent (hand-passing values across boundaries).
- **Closure captures inside builder**: `runner=lambda: step2(state["r1"], ...)`.
  Pollutes the call site, forces lazy construction of the step list, and
  the "uniform loop" stops being uniform.
- **Generic step interface**: `Step` accepts `Any` for runner args. Type
  safety lost; refactor benefit forfeited.

## Concrete grounding (COS STR-M1)

The Week-4 audit cited `buyers_committee/run_orchestrator.py::execute_run` as
a god-pipeline: T1→T2→T3→T4 with hand-written `call_count += used.calls`,
`token_total += used.tokens`, `await _db(_persist_turn, ...)`, and
`if await _db(_is_cancelled, ...): return` at each turn boundary. The
prescribed fix was `TurnSpec(name, runner, persist_args_builder)` +
`for turn in TURN_PIPELINE: ...`.

The state graph blocked it:
- T1 = fan-out: independent persona reactions, persisted as a batch via
  `_persist_reactions` (different shape from `_persist_turn`)
- T2 needs T1's reactions + persona_rows → produces `challenge` + `target_persona`
- T3 needs `target_persona` + `challenge.text` → produces `response`
- T4 needs `persona_rows`, `challenge`, `response`, `target_persona`
  → produces `veto_check`

A uniform `runner` signature would need to either: (a) accept a shared
state dict, hiding the dataflow, or (b) build the runners lazily inside the
loop, which means each step builds its own — at which point the loop is
just a glorified `for` over three near-identical assignments.

The shipped refactor extracted three primitives:
- `_UsageTotals` — mutable accumulator (replaces `call_count` + `token_total`
  int pair, plays well with try/except boundaries)
- `_TurnRecord` — dataclass capturing the 6 fields varying between T2/T3/T4
  persistence (turn_number, turn_type, speaker_persona_id, target_persona_id,
  content, model_used)
- `_record_seq_turn_or_cancel(ctx, run_id, totals, used, record) -> bool` —
  the one helper hiding accumulate + persist + cancel-check

T2/T3/T4 now read as: `result, used = await _run_tN(...); if await
_record_seq_turn_or_cancel(...): return`. T1 stays inline because its
shape is genuinely different. Each call site still explicitly states which
prior-step state it consumes.

## When the audit doc is overreaching

Specifically: if an audit fix prescribes a uniform loop, check whether the
pipeline has data-dependent state-passing. If it does, the loop is the
wrong shape. Helper extraction gives you 80% of the LOC savings without
forcing artificial uniformity.

## When this does NOT apply

- The N steps really are independent (e.g. `for analyzer in ANALYZERS:
  result = analyzer(input)`). Loop is correct.
- The state graph is a clean acyclic chain where every step takes exactly
  the previous step's output. `state = step(state)` works.
- A single helper would have only one call site. Then it's just inlining
  with extra steps.

## The deeper lesson

The shape of refactor follows the shape of the data dependency graph, not
the shape of the source-code repetition. Visually similar blocks with
divergent state graphs are NOT a uniformity-extraction candidate.

## Source Context

Sourced from COS Week-4 audit feedback on `execute_run` (buyers_committee orchestration pipeline). The audit prescribed a uniform loop refactor, but the state-passing graph (T1 fan-out → T2 dependent on T1 output + persona_rows → T3 dependent on T2 output → T4 dependent on T2 and T3) blocked straightforward loop uniformity. Shipped solution: helper extraction for the common boilerplate (accumulate usage, persist turn record, cancel-check), keeping each step inline so state dependencies are explicit. Represents tactical decision in refactoring strategy when audit prescriptions conflict with actual data dependencies.
