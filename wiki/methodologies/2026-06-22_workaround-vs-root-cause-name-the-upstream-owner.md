---
title: Workaround-vs-root-cause — name the upstream owner when shipping a tarp
source_mode: direct
source_session: redacted
novelty_type: transferable_framework
grounding_score: 0.7
staleness_risk: stable
importance: 3
pinned: false
created: 2026-06-22
domain: methodologies
topic: scope-discipline
tags: multi-component-systems, decision-making, scope-discipline, technical-debt
related_entries:
  - architecture/2026-05-20_platform-deprecation-architectural-intent-preservation.md
  - patterns/2026-05-15_sidecar-mirror-upstream-missing-relations.md
  - methodologies/2026-05-16_upstream-noise-flood-bulk-close-source-pointer.md
  - methodologies/2026-05-18_reframe-stated-scope-to-actual-goal-strategist-heuristic.md
---

# Workaround-vs-root-cause — name the upstream owner when shipping a tarp

## The discipline

When you ship a fix that is a workaround in your codebase for a bug whose root cause lives elsewhere (upstream library, vendor product, partner API, sibling service in a multi-repo system), the disposition note for that work MUST explicitly label root-cause ownership. Otherwise the workaround becomes load-bearing in operator mental models and accumulates "iterate to perfect it" pressure that should instead pressure the upstream owner.

## Closure-note shape

Bead/ticket close-reason should follow this template:

```
Workaround shipped (Option N — [brief description]; commit [SHA]).
Backend-side verified: [evidence].
Root cause is [upstream X — Anthropic Agent-OS connector / Vendor Y / sibling
service Z] — that's an upstream fix, not [our-codebase]-side.
The fallback only kicks in when [precondition fails], so if [upstream]
later fixes [behavior] the workaround becomes a no-op rather than a
conflict.
No further [our-codebase]-side work warranted.
```

Five load-bearing components:
1. **Mark it explicitly as a workaround** — not "fix," not "patch," not "resolution."
2. **Cite the verification evidence** for the local-side change (commit SHA + smoke result).
3. **Name the upstream owner of the root cause** by repo, vendor, or service.
4. **Describe the eviction condition** — what happens when the upstream owner fixes the real bug. (Ideally: workaround becomes a no-op, not a conflict requiring removal.)
5. **State the no-further-work-on-this-side conclusion** to forestall iteration drift.

## When this applies

Any patch where the architecturally-correct fix lives in someone else's code but you ship a local workaround anyway because their fix is out of your control or not coming on your timeline. Typical surfaces:
- Vendor SDK bugs.
- Partner API behavior you can't change (auth handshake quirks, response-shape variance, rate-limit edge cases).
- Sibling services in a multi-repo system where the team that owns the real fix is on a different roadmap.
- Upstream library bugs awaiting a release.

## When this does NOT apply

- Bugs whose root cause is genuinely in your code — no reframe needed; close as a normal fix.
- Bugs where you're patching at the wrong layer of YOUR OWN system — that's a different anti-pattern ("fix at the right layer," not "name the upstream owner"). The owner is still you; the question is which module.

## Why this matters

Without the explicit naming:
- The workaround silently becomes the architecture in the operator's mental model.
- Subsequent sessions inherit "improve the workaround" as the natural next step, when the correct next step is "wait for upstream / file upstream issue / route around."
- Successor beads accumulate that patch deeper at the wrong layer (e.g., "add per-user key UX," "build a token translation layer") — each one looks reasonable in isolation but compounds the wrong-layer investment.
- The eviction condition is forgotten, so when upstream finally ships their fix, the local workaround becomes dead code nobody dares to remove.

Naming the upstream owner in the closure note converts the workaround from an architectural commitment into a known-tarp with a removal trigger.

## Grounding instance

cos-yb1i (2026-06-22, [project]). Original frame: "COS MCP returns 401 on Claude.ai Agent-OS tool calls." Shipped Option A — a `COS_API_KEY` env-var fallback on the COS MCP container. Operator reframed mid-stream: "Shouldn't this be done by the agent-os repo?" Closure became:

> "Root cause is Claude.ai Agent OS connector not forwarding a usable Bearer to /mcp — that's an upstream Anthropic-side fix, not COS-side."

Without the reframe, the natural next-step trajectory was "add per-user key UX, token translation layer, etc." — all of which patch deeper at the wrong layer. The reframe stopped that drift and converted a "we own this" technical-debt accumulation into a "we're tarping this until Anthropic ships" eviction-ready workaround.

## Related entries

- `architecture/2026-05-20_platform-deprecation-architectural-intent-preservation.md` — different problem (deprecation, not bug-with-external-owner) but shares the architectural-intent-vs-implementation separation discipline.
- `patterns/2026-05-15_sidecar-mirror-upstream-missing-relations.md` — concrete technical pattern when the upstream is unfixable; this entry is the disposition-discipline complement.
- `methodologies/2026-05-16_upstream-noise-flood-bulk-close-source-pointer.md` — companion methodology: surviving an ongoing flood of upstream-caused issues; this entry covers naming ownership in the closure of any single one.
- `methodologies/2026-05-18_reframe-stated-scope-to-actual-goal-strategist-heuristic.md` — the reframe mechanic in the grounding instance lives in this family.
