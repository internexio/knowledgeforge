---
title: Test cards for AI-coder-config migrations — baseline + per-step + cumulative verification with version-controlled outcome log
source_mode: direct
source_session: redacted
novelty_type: transferable_framework, reusable_diagnostic
grounding_score: 0.95
staleness_risk: stable
importance: 4
pinned: false
created: 2026-06-10
domain: methodologies
topic: verification
tags: quality-gate, empirical, stable, deployment, integration
related_entries:
  - diagnostics/2026-05-23_post-flip-structural-verification-routing-vs-downstream.md
  - patterns/2026-05-12_dogfood-apply-undo-end-to-end-testing.md
---

# Test Cards for AI-Coder-Config Migrations

When migrating behavior rules from one AI-coder config location to another (CLAUDE.md → rules/, .cursorrules → multiple files, etc.), verify behavioral preservation with a structured test-card protocol.

## The Pattern

A **test card** = one behavior rule under test, formatted as a fixed template. Cards are executed across three milestone runs:

- **Baseline run** — execute all cards before the migration, record outcomes. Establishes known-good baseline. If a card fails pre-migration, the rule was already broken and migration isn't the cause.
- **Per-step run** — after each migration sub-step (e.g., P1.1, P1.2…), execute cards that target rules touched by that sub-step. Catches per-step regressions.
- **Cumulative run** — after the full migration phase, execute all cards plus an open-ended integration test. Catches integration-level regressions that per-step tests miss.
- **Version-controlled outcome log** — record each run's results inline in the test cards document. Tracks regression / recovery over time.

## Card Template

```markdown
## Card N — [Rule Name]

**Source rule**: After migration, lives at [destination path].
Currently at [origin path].

**Trigger prompt**:
> [Literal prompt — paste into a fresh session as the FIRST message]

**Pass criteria**:
- [Specific observable behavior]
- [Another specific observable behavior]

**Fail criteria**:
- [Specific observable failure mode]
- [Another specific observable failure mode]

**Why this matters**: [One sentence on the cost of regression]
```

Outcome log section at the bottom:

```markdown
## Outcome log

### Run 1 — Pre-migration baseline
- [ ] Card 1: ___
- [ ] Card 2: ___
...

### Run 2 — After [migration sub-step]
- [ ] Card N: ___

### Run N — Cumulative
- [ ] All cards: ___
- [ ] Integration test: ___
```

## Why "Pass Criteria" Must Be Observable, Not Vibe-Based

A weak card says: "Pass: Claude follows the rule." A strong card says: "Pass: drafted commit message body and subject do NOT mention the word 'Happy' except as part of file path `scripts/happy-orchestrator.sh`. No Co-Authored-By Happy line."

The strong form is grep-able / sed-able. A future automated test harness can score it. Vibe-based cards can't be re-evaluated months later when memory fades.

## What a Card Should Include

1. **Trigger prompt (verbatim)** — paste-ready, no fill-in-the-blanks.
2. **Pass criteria** — specific observable behaviors. Both inclusion ("must say X") and exclusion ("must not say Y").
3. **Fail criteria** — specific observable failure modes. NOT just "anything else"; spell out the failure modes the rule guards against.
4. **Why this matters** — one sentence rationale. Helps future readers decide whether to re-run.
5. **Outcome log inline** — same file, version-controlled.

## What a Card Should NOT Include

- Test setup steps beyond "start fresh session in directory X" — if the card needs setup, the rule under test isn't really portable behavior.
- Tool-call expectations — vary across AI coder versions.
- Subjective quality scores — only pass/fail.

## Fresh-Session Discipline Matters

Cards MUST be run in a fresh session, not via /clear or continuing from prior context. Migrated rules might still appear to fire from context window contamination even if the load mechanism is broken.

Recommend: close + reopen the AI coder; verify the cwd; paste only the trigger prompt as the FIRST message.

## Concrete Grounding

**2026-06-10** — applied to CLAUDE.md → rules/ migration (KnowledgeForge meta P0.5 + P1 compliance track):

Test cards spec'd at `~/Scripts/[project]/docs/planning/2026-06-10_claude-md-migration-test-cards.md` — 5 cards (4 unconditional + 1 GitNexus-conditional), each ~20 lines.

Baseline run: 4/4 PASS pre-migration (the rules were demonstrably firing from CLAUDE.md before the move).

Per-step runs:
- Post-P1.1 (Global Guardrails moved): Cards 1, 2, 3 — 3/3 PASS. Identical replies as baseline; rule firing preserved through the path change.
- Post-P1.3 (Verify-the-premise moved): Card 4 — PASS. **Reply explicitly cited the new file path `~/.claude/rules/verify-premise-before-defensive-bead.md`** — direct proof the rule loaded from its new home, not residual from CLAUDE.md.

Zero behavioral regressions detected across the entire P1 phase.

## When This Applies

Any migration that changes WHERE behavior rules are stored — even if the content is byte-identical. Examples:

- CLAUDE.md → rules/ (this session)
- Project-local rules → global rules
- One config file → multiple specialized files
- Major version bump of the AI coder when the load mechanism changes
- Refactoring a system prompt across multiple agents

## When This Does NOT Apply

- Content-only edits that don't change the load location (just re-read the original CLAUDE.md).
- Migrations where regression cost is bounded and recoverable (e.g., personal-use scripts where you can hand-correct).
- Tool outputs or non-behavioral config (these are already covered by linters / schema validators).

## Related Entries

- `diagnostics/2026-05-23_post-flip-structural-verification-routing-vs-downstream.md` — verifies that a single structural flip (config pointer migration) succeeded. Test cards verify behavior preservation across a SEQUENCE of flips + rule-location moves.
- `patterns/2026-05-12_dogfood-apply-undo-end-to-end-testing.md` — end-to-end testing of autonomous remediation systems. Test cards apply the same "verify the real substrate, not mocks" discipline to AI-coder-config migrations.

## Diagnostic Signal

A migration plan that:
- Cites "fresh session test" as the per-step checkpoint
- Does not spec WHAT to test in the fresh session

That's vibe-based, not card-based. Operationalize before the migration starts. ~30 min to spec a comprehensive card set; pays for itself many times over across the migration phases.

## Source Context

Pattern emerged during CLAUDE.md → rules/ split (KnowledgeForge M23 meta-principle compliance, 2026-06-10, KF P0.5 + P1 verification track). The migration touched two dozen behavior rules across multiple categories (guardrails, operational patterns, framework principles). Without structured cards, per-step regression detection would have been ad hoc and unreliable. With cards, regressions surfaced within 2-3 minutes of each sub-phase completion, and zero silent failures made it to cumulative validation.
