---
title: Collapse N-useState chorus into discriminated union + reducer
source_mode: direct
source_session: redacted
novelty_type: new_pattern
grounding_score: 0.9
staleness_risk: slow_decay
importance: 4
pinned: false
created: 2026-05-14
domain: patterns
topic: synthesis
tags: [classification, validation, quality-gate, grounding]
related_entries: [patterns/2026-05-13_helper-extraction-beats-loop-refactor-state-divergence.md]
---

# Collapse N-useState chorus into discriminated union + reducer

## The smell

A React component owns N (typically 5+) `useState` values that are
*together* representing one workflow's progression — e.g. `streaming`,
`streamedText`, `draftId`, `draftVersion`, `streamError`, `preCheck`,
`preCheckError`, `copied`, ... Each individual `setX` is well-intentioned
but the component is implicitly maintaining an N-flag state machine where
half the (2^N) combinations are unreachable or inconsistent.

The recurring bug class: "operation finished but `loading` is still true,"
"error set but `data` from previous attempt still rendered," "two
mutually-exclusive flags simultaneously true."

## The fix

Replace the N booleans with a single discriminated-union `Status` type
and a `useReducer` whose actions correspond to workflow transitions.

```typescript
type RewriteStatus =
  | { kind: 'idle' }
  | { kind: 'precheck' }
  | { kind: 'blocked';   preCheck: PreCheckResponse }
  | { kind: 'warning';   preCheck: PreCheckResponse }
  | { kind: 'streaming'; text: string }
  | { kind: 'ready';     text: string; draft: { id: string; version: number } }
  | { kind: 'error';     message: string; text: string };

type Action =
  | { type: 'precheck_start' }
  | { type: 'precheck_block'; preCheck }
  | { type: 'stream_start' }
  | { type: 'stream_token'; token: string }
  | { type: 'stream_done'; draft }
  | { type: 'stream_error'; message: string }
  | { type: 'reset' };

function reducer(state: Status, action: Action): Status {
  // exhaustive switch over action.type
}
```

Then wrap in a `useFooHook({...args})` that returns `{status, actions}`
plus any non-machine concerns (DOM refs, transient UI flags like `copied`
that aren't part of the workflow). The component reads one `status`
object and dispatches via `actions.*`.

## Why this kills the bug class

The bug "flag X still true after stage Y completes" required two
independent setStates to stay in sync. With a discriminant, the type
*is* the stage — there is no second flag to forget to flip. Late
callbacks (e.g. an SSE token arriving after stream_error) can be
explicitly handled as no-ops in non-streaming states:

```typescript
case 'stream_token': {
  if (state.kind !== 'streaming') return state;  // ghost token, ignore
  return { ...state, text: state.text + action.token };
}
```

The reducer is pure → it's directly unit-testable without spinning up
a render tree. A small test suite of "state X + action Y → state Z"
covers the entire machine.

## When to apply

- React component holds **5+ useStates** that collectively represent
  one user-facing workflow's progression.
- You can articulate stages of the workflow as nouns (`idle`,
  `streaming`, `ready`, `error`) — i.e. the booleans aren't really
  independent.
- Bug reports mention "got stuck in [intermediate state]" or "two
  things showed at once."

## When NOT to apply

- The useStates are genuinely independent UI concerns (e.g. a
  modal-open flag, a separate confirmation-checkbox flag, a sort
  direction). These have no stage relationship; a state machine is
  overkill.
- Form-field state. `useForm` / `react-hook-form` already solves
  this; reducing each field to a discriminant is needless ceremony.
- The component has 2-3 booleans that legitimately do not interact.
  Threshold for this refactor is roughly N ≥ 5 plus a workflow
  narrative connecting them.

## Concrete grounding

COS `RewriteWorkspace` (frontend/src/components/website/WebsiteTool.tsx)
managed 11 `useState` values coordinating a rewrite workflow with stages:
precheck → blocked|warning|streaming → ready|error. Refactored to
`useRewriteStream` (frontend/src/hooks/useRewriteStream.ts) with a
7-state discriminated-union `RewriteStatus` and a 10-action reducer.
Component shrank from 429 → ~280 LOC; component-level useStates dropped
from 11 to 3 (the 3 are mode, userPrompt, showHistory — independent UI
state with no workflow relationship). The audit's specific concern
("stream finished but `streaming` still true") became inexpressible by
construction. 20 reducer tests in `useRewriteStream.test.ts` cover the
machine — the reducer is pure, no React Testing Library needed.

Commit `56c6afe`, audit ref CODE_REVIEW_2026-05-12.md STR-M5.

## Composition notes

- Pair the hook with a small `actions` bag (`{generate, accept, reset, ...}`)
  rather than exporting the dispatch function directly. The actions can
  encapsulate side effects (HTTP calls, query invalidation) that don't
  belong in the reducer.
- Keep transient UI flags (`copied: boolean` with auto-clear) as
  separate `useState` inside the hook, NOT as discriminant states.
  Those don't represent workflow progression; they're presentation
  details.
- `outputRef` and other DOM refs live in the hook so the component
  doesn't have to manage cross-render persistence — return the ref
  from the hook and let the component attach it.

## Anti-pattern: the "loop refactor" alternative

The related entry **"Helper extraction beats loop refactor when per-step state diverges"** (patterns/2026-05-13_helper-extraction-beats-loop-refactor-state-divergence.md) describes a related pattern for backend orchestration where the audit prescribed a `for turn in TURN_PIPELINE` loop refactor over per-turn varying state. That style fails when the per-step state genuinely diverges; a boilerplate helper + explicit sequence is cleaner. The state-machine collapse pattern here is the opposite shape: the audit's "implicit state machine" diagnosis is correct precisely when the states ARE uniform enough to enumerate as a discriminated union. Both patterns live in the same neighborhood (refactor an implicit-machine smell) but resolve to different shapes based on whether the per-stage state shape is uniform.

## When this applies beyond React

This pattern generalizes to any framework or language with:
- A discriminated-union or tagged-union type system (TypeScript, Rust, Elm, Scala)
- A reducer or state-machine library (Zustand, Jotai, MobX, Redux, Pydantic + dataclass discriminants)

The core principle is type-driven refinement: use the type system to make impossible states unrepresentable.

## Source Context

Sourced from COS audit STR-M5 (audit ref: CODE_REVIEW_2026-05-12.md). The RewriteWorkspace component coordinated a rewrite workflow (precheck → streaming → ready/error) across 11 independent useState calls. The implicit state machine allowed bugs where transition flags never reset. Refactored into a discriminated-union RewriteStatus type with a pure reducer, collapsing the 11 useState calls into 1 + a hook. This eliminated the bug class by construction: states that can't co-exist are not representable in the type.
