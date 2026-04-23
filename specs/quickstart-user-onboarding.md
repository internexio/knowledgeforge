# Spec: 00_User_Quickstart.md

**Component:** 1 — User Quickstart  
**Target file:** `00_User_Quickstart.md` at repo root  
**Version:** 1.0.0  
**Decision type:** Reckoning  
**Date:** 2026-04-23

---

## Purpose

This spec defines the content and structure of `00_User_Quickstart.md`, the first user-facing document in the KF User Education Layer. The target reader is someone who has installed KnowledgeForge but has never used it — they know Claude, they do not know KF modes, routing, or decision types. The file lives at repo root (not in `docs/`) because it is the first artifact a new user should encounter, not an appendix. It fills the gap confirmed by Phase 0 discovery: no user-facing onboarding content of any kind exists in the repo. Module 06 Quick Reference is the deep agent reference — this quickstart is the shallow entry point that routes a user to the right mode for their current task, then steps aside.

---

## Audience and Constraints

- **Audience:** User who has never used KF. Assumes general Claude familiarity, zero framework knowledge.
- **Length ceiling:** 1500 words. Must fit one desktop screen at default zoom.
- **Excluded:** Infrastructure modules (Tier 0, salience, calibration layer, grounding scores, permission model). Users do not need these on day one.
- **Excluded:** Any mention of partnership, business contexts, or products other than KF itself.
- **No YAML frontmatter** — this is a user doc, not a module.
- **No sub-variant exposure:** Expert (domain, infra, ERA) and Critic (adversarial, linter, audit) sub-variants are implementation details and must not appear in the decision tree or examples.

---

## Structure

Exactly four sections, in this order. No other sections. No introductory preamble before Section 1.

---

### Section 1: What KF Does That Raw Claude Doesn't

**Spec:** Write 3–5 sentences. No framework jargon. The sentences must convey:

1. Raw Claude responds to every request the same way — it does not change its reasoning strategy based on what you are trying to accomplish.
2. KF patches this by routing your request to a mode whose protocol is shaped for that class of problem — creating, diagnosing, reviewing, deciding, etc.
3. The practical effect: KF forces the second question raw Claude skips. A builder asks what constraints exist. A critic asks what the spec assumes. A strategist asks what you are deferring.
4. There is no configuration required. KF classifies and routes automatically. The user's job is to phrase the request clearly enough for classification to fire correctly.

**Tone:** Flat declarative. No enthusiasm. No claims about power or intelligence. One sentence per idea.

---

### Section 2: Decision Tree — The 9 Modes

**Spec:** A decision tree with exactly 9 terminal paths — one per mode. The user asks a decision question and arrives at exactly one mode. No dead ends. No compound entries. No ambiguous branches.

Navigator is the only mode that fires automatically — it is triggered by KF when a request is genuinely ambiguous, not by the user selecting it. Include it in the tree but mark it clearly as automatic.

Expert and Critic entries must stay at the generalization level. Do not mention sub-variants, variant names, or internal routing within those modes.

**Decision tree (exact structure to implement):**

```
What do you want to do?

├── CREATE something (spec, agent, system prompt, architecture, RFC)
│   └── → Builder

├── COORDINATE multiple agents or services
│   └── → Coordinator

├── DIAGNOSE a problem (broken, failing, unexpected behavior)
│   └── → Debugger

├── REVIEW or VALIDATE something (spec, plan, deployment, security)
│   └── → Critic

├── DECIDE between options (trade-offs, prioritization, what to build next)
│   └── → Strategist

├── FIND PATTERNS across multiple examples or artifacts
│   └── → Synthesizer

├── DEEP ANALYSIS (second-order effects, blast radius, irreversible decisions)
│   └── → Expert

├── CONFIGURE AI coder setup (CLAUDE.md, project conventions, guardrails)
│   └── → Calibrator

└── REQUEST IS UNCLEAR (fires automatically — you do not invoke this)
    └── → Navigator
```

**Mapping verification (sourced from Phase 0 discovery):**

| Mode | Phase 0 Purpose Summary | Decision Tree Entry | Match |
|------|------------------------|---------------------|-------|
| Navigator | Detect and resolve genuinely ambiguous user requests | REQUEST IS UNCLEAR — fires automatically | Yes |
| Builder | Create new agents and complete specifications from requirements | CREATE something | Yes |
| Coordinator | Design multi-agent workflows by mapping dependencies first | COORDINATE multiple agents or services | Yes |
| Expert | Domain-specific analysis that forces second-order reasoning | DEEP ANALYSIS, second-order effects | Yes — generalized across 3 sub-variants |
| Critic | Systematically challenge specifications, find unstated assumptions | REVIEW or VALIDATE something | Yes — generalized across 3 sub-variants |
| Synthesizer | Extract reusable patterns from disparate sources | FIND PATTERNS across multiple examples | Yes |
| Debugger | Systematically diagnose problems through hypothesis testing | DIAGNOSE a problem | Yes |
| Strategist | Strategic decisions about what to build, when, and what to defer | DECIDE between options | Yes |
| Calibrator | Generate complexity-aware AI coder configuration | CONFIGURE AI coder setup | Yes |

All 9 paths confirmed mapped. No gaps.

---

### Section 3: Good vs. Bad Phrasing

**Spec:** Three example pairs. Same goal each time. Show how phrasing changes which mode activates. Format: two columns or a before/after block. The "bad" example in each pair is genuinely too vague — it triggers Navigator. The "good" example is specific enough to trigger the claimed mode directly.

**Pair 1 — Goal: debug a failing test**

- Bad: `"What's wrong with my test?"` — too vague, Navigator fires to clarify
- Good: `"Diagnose why my auth test is failing on line 47"` → **Debugger**

**Pair 2 — Goal: review an architecture plan**

- Bad: `"Is this good?"` — too vague, Navigator fires to clarify
- Good: `"Review this service topology for gaps and unstated assumptions"` → **Critic**

**Pair 3 — Goal: choose between two implementation approaches**

- Bad: `"Which is better, approach A or B?"` — too vague, Navigator fires to clarify
- Good: `"Weigh the trade-offs between approach A and B for a 50k-user load"` → **Strategist**

**Tone note:** Do not explain why the bad examples are bad at length. Show; do not lecture. One parenthetical per bad example is sufficient.

---

### Section 4: The Ozymandias Check

**Spec:** One paragraph, 4–6 sentences. Explain why questions that feel simple often aren't, and what to do when that happens.

Content to cover:

1. Name origin: Ozymandias — the king who declared his works eternal. The decay was already in progress; he missed it. The check is named for the failure mode of confident short answers that miss the structural problem underneath.
2. The rule: if answering a yes/no question requires multi-paragraph reasoning, it is not a reckoning. Upgrade it to an evaluative or novel judgment.
3. Practical application: before asking KF "should I do X?", ask whether X has meaningful trade-offs, irreversible consequences, or dependencies you have not mapped. If yes, frame the question as a decision with context, not a yes/no.
4. Close with one sentence: "The check is not a framework overhead — it is a prompt to notice what you are actually asking."

---

## Cross-link

One line at the end, exactly as written:

> For the full routing reference, see [Module 06 Quick Reference](modules/06_quick_reference.md).

This appears once, at the end of the document, after Section 4. Nowhere else.

---

## Acceptance Criteria

- [ ] All 4 sections present, in exact order: What KF Does / Decision Tree / Good vs. Bad Phrasing / Ozymandias Check
- [ ] Section 2 decision tree: exactly 9 terminal paths, one mode per path, no dead ends, no ambiguous branches
- [ ] Navigator entry marked as automatic (user does not invoke it)
- [ ] Expert entry: does not mention "domain", "infra", or "ERA" sub-variants
- [ ] Critic entry: does not mention "adversarial", "linter", or "audit" sub-variants
- [ ] Section 3: all three "good" phrasings verified to trigger the stated mode (see Round-Trip Validation below)
- [ ] Word count of the implemented document: ≤ 1500
- [ ] No YAML frontmatter in the implemented document
- [ ] No mention of: infrastructure modules, grounding scores, salience, permission model, Tier 0, or calibration layer
- [ ] Cross-link to Module 06 appears exactly once, at the end

---

## Round-Trip Phrasing Validation

The following phrasings must be verified against the KF orchestrator routing table before the implementation is accepted as complete. Run each through the orchestrator and confirm the stated mode fires.

| # | Phrasing | Claimed Mode | Must Verify Before: |
|---|----------|--------------|---------------------|
| 1 | `"Diagnose why my auth test is failing on line 47"` | Debugger | Implementation commit |
| 2 | `"Review this service topology for gaps and unstated assumptions"` | Critic | Implementation commit |
| 3 | `"Weigh the trade-offs between approach A and B for a 50k-user load"` | Strategist | Implementation commit |

If any phrasing fires Navigator instead of the claimed mode, revise Section 3 to use a phrasing that routes correctly. Do not ship examples that fail their own round-trip test.

---

## Dependencies

- `modules/06_quick_reference.md` must exist and be cross-linkable — **confirmed present** (Phase 0 discovery, Section 9)
- Mode purpose summaries sourced from Phase 0 discovery note (`docs/planning/phase-0-discovery-user-education.md`, Section 5)
- No new module, skill, or wiki entry is required to implement this document

---

## Decision Type Tags

| Decision | Type | Rationale |
|----------|------|-----------|
| Four-section structure | Reckoning | Standard minimal onboarding pattern: what/how/examples/check |
| File at repo root (not `docs/`) | Reckoning | First file new users encounter; `docs/` is for deep reference |
| No YAML frontmatter | Reckoning | User doc, not module — module conventions do not apply |
| 1500-word ceiling | Evaluative | Criteria: must fit one screen at default zoom; 1500 is a tested threshold for onboarding docs that get read vs. skipped |
| Expert/Critic at generalization level | Reckoning | Sub-variants are routing implementation details; exposing them adds decision burden without user benefit |
| Navigator marked automatic | Reckoning | Navigator fires on KF detection of ambiguity; user cannot usefully pre-select it |
| Ozymandias Check as Section 4 | Evaluative | Alternative was a "when not to use KF" section; Ozymandias Check is more actionable — it teaches a skill rather than listing exclusions |

---

## Notes

- `00_User_Quickstart.md` lives at repo root. The `00_` prefix sorts it before all other root-level Markdown in directory listings.
- This is not a module. It does not get a version header, changelog, or module number. The spec version (1.0.0) is this spec's version, not the implemented document's version.
- If word count approaches 1500 during implementation, cut Section 1 sentences first (they are scene-setting). Do not cut the decision tree or phrasing examples — those are the load-bearing content.
- The Ozymandias Check section name in the implemented document should be exactly "The Ozymandias Check" — do not soften it to "When to Upgrade a Question" or similar.
- This spec is intentionally narrow. It does not govern the fit-check skill (Component 3) or the confusion detection amendment (Component 2). Those have separate specs.
