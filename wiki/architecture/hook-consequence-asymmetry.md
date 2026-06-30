---
title: Hook Consequence Asymmetry
source_mode: synthesizer
source_session: redacted
created: '2026-04-29T00:00:00Z'
date: '2026-04-29'
confidence: 0.93
grounding_score: 0.93
grounding_source: 'CCT triage of 72 hook files across 11 categories. Asymmetry observed
  from comparing security hooks (exit 2, friction-tolerant) against productivity hooks
  (exit 0, latency-sensitive). Cross-referenced against CCT anti-pattern: build-on-change.json
  (runs 8-minute COS Docker build on every file Edit) and plan-gate.json (blocks legitimate
  fixes when todo.md absent).'
novelty_type: design_principle
staleness_risk: stable
importance: 4
pinned: false
accreted_in: '6.5'
related:
- wiki/architecture/scaffolding-vs-patching-pattern.md
- wiki/architecture/skills-vs-agents-design-boundary.md
- modules/02_builder.md
domain: architecture
topic: mode-design
---

# Hook Consequence Asymmetry

## Pattern

Claude Code hooks have two distinct consequence profiles that require different design constraints:

| Profile | Hook type | Acceptable friction | Blocking behavior | Failure mode |
|---------|-----------|--------------------|--------------------|--------------|
| **Security** | Secret scanners, dangerous-command blockers, env-file protection | High — false positive is acceptable cost | Yes (exit 2) | False negative (missed threat) is catastrophic |
| **Productivity** | Format-on-save, notifications, loggers, build triggers | Low — every added ms degrades flow | No (exit 0, || true) | False positive (hook firing unnecessarily) is the primary risk |

**The principle:** The acceptable friction level of a hook is determined by the consequence of the failure it prevents. Security hooks tolerate friction because what they're preventing (leaked API key, deleted production data) is irreversible. Productivity hooks must be fast because their friction compounds across every tool invocation in a session.

---

## Mechanism

A hook fires on every matching tool event. In an active session, this means:

- A security hook that takes 200ms per Bash invocation adds ~60 seconds to a 300-operation session. Acceptable — the protection justifies it.
- A productivity hook that takes 200ms per Edit adds ~120 seconds to a 600-edit session. Unacceptable — the formatting benefit doesn't offset the flow interruption.
- A build hook that takes 8 minutes per Edit makes the tool unusable. Catastrophic misclassification.

**The compound effect:** Productivity hook latency accumulates invisibly. Users don't experience "this hook takes 200ms" — they experience "Claude feels slow today." The degradation is attributed to the model, not the hook.

---

## Anti-Pattern — Uniform Exit Behavior

Apply the same exit behavior (blocking or non-blocking) to all hooks regardless of consequence type.

**What breaks (blocking applied to productivity):**
- `plan-gate.json`: exits 2 if no `todo.md` exists. Blocks a legitimate mid-session regression fix because the developer didn't create a plan file first. The frustration cost is immediate; the planning discipline benefit is speculative.
- `tdd-gate.json`: exits 2 if no test file exists for the source file being edited. Blocks the common case of creating the source first, then the test. Forces an artificial ordering that TDD purists don't actually follow either.
- `validate-branch-name.json`: exits 2 on non-conforming branch name. Blocks legitimate hotfix branches created under pressure.

**What breaks (non-blocking applied to security):**
- A secret scanner that emits a warning (exit 0) and continues: the commit lands anyway. The warning is noise in a long session. Non-blocking security is security theater.

**Observed in CCT:** Several quality-gate hooks use exit 2 (blocking) for workflow-preference enforcement. These block legitimate work in the majority of real development scenarios where plans, tests, and branches don't precede every edit.

---

## Design Decision Framework

When designing a hook:

1. **What failure is this preventing?** Name the specific worst case.
2. **Is that failure reversible?** 
   - Irreversible (committed secret, deleted data, force-pushed main) → security profile → blocking, friction-tolerant
   - Reversible (unformatted code, no notifications, no log entry) → productivity profile → non-blocking, latency-sensitive
3. **What's the false positive rate?** Security hooks can tolerate ~1-5% false positives (developer is interrupted, reads the error, overrides). Productivity hooks at 5% false positive means 1 in 20 tool invocations triggers a spurious effect — immediately perceptible as noise.

---

## Calibration Reference

**Security hooks — target specifications:**
- Exit behavior: exit 2 on positive detection (hard block)
- Latency budget: up to 500ms (regex scanning is fast; 50+ patterns in <100ms)
- False positive tolerance: low (5% acceptable); false negative tolerance: zero
- Bypass mechanism: should exist but require explicit operator intent

**Productivity hooks — target specifications:**
- Exit behavior: exit 0 always (|| true suffix on command)
- Latency budget: <50ms; formatter hooks <200ms
- Output behavior: silent on success, informational only on error
- Should never block tool execution under any circumstance

**Boundary cases — classification tests:**
- `conventional-commits.py` (exits 2 on non-conforming commit format): Security or productivity? Commits are reversible (amend), but bad commit messages compound across the project history. Classify as productivity → non-blocking with a warning message, not a block.
- `force-push-blocker.json` (exits 2 on force push to main): Security — force push to production is reversible with effort but operationally catastrophic. Blocking is justified.

---

## Reuse Context

Reference this entry when:
- Evaluating any new hook for adoption (apply the consequence test before deciding on exit behavior)
- Reviewing CCT or community hook libraries — most quality-gate hooks misclassify reversible workflow preferences as security concerns
- Designing hooks for KF, COS, or [project] — format-on-save hooks must be exit 0 with || true; secret scanners must be exit 2
- Debugging why Claude Code feels slow — check whether any installed productivity hooks are using blocking exit codes or have latency above 200ms
- Any hook that fires on every Edit/Write invocation should be classified as productivity and held to the stricter latency constraint
