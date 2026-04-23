# Spec: KF Fit Check Skill

**Component:** 3 — kf-fit-check skill  
**Target location:** `## CC Skill` section in `modules/01_navigator.md`  
**Compiled path (variant repos):** `.claude/skills/kf/fit-check.md`  
**Version:** 1.0.0  
**Decision type:** Evaluative  
**Date:** 2026-04-23

---

## Path Adaptation Note

The handoff originally specified `skills/kf-fit-check/SKILL.md`. Phase 0 discovery (2026-04-23) confirmed that knowledgeforge-core authors skills as `## CC Skill` sections inside module files, not as standalone skill directories. This spec adapts accordingly: the fit-check skill is authored as a new `## CC Skill` section at the end of `modules/01_navigator.md`. Compiled output in variant repos: `.claude/skills/kf/fit-check.md`.

---

## Purpose

One sentence: the fit-check skill takes a 2-3 sentence description of a user's current work and returns a ranked list of 2-3 KF modes most relevant to that work, giving first-contact users a concrete starting point.

Who uses it: users who have installed KF but do not yet know which modes apply to their work. Invoked explicitly, not automatically.

Not in scope: infrastructure module ranking, sub-variant exposure, automatic trigger on ambiguous requests (that is Navigator's job), any output beyond mode ranking.

---

## Design

### Capabilities

**Primary:**
- Accept a 2-3 sentence work description
- Return a ranked list of 2-3 modes with one-sentence justifications per mode
- Provide a concrete "start with X" directive

**Secondary:**
- Prompt user for description if not provided with the trigger
- Accept description provided inline with trigger phrase (no re-prompt)

### Inputs

| Name | Type | Required | Notes |
|------|------|----------|-------|
| trigger_phrase | string | yes | One of the defined trigger patterns |
| work_description | string | yes (after trigger) | 2-3 sentences; one sentence minimum accepted |

### Outputs

| Type | Format | Structure |
|------|--------|-----------|
| mode_ranking | markdown list | 2-3 items; each: mode name + one-sentence justification tied to the description |
| start_directive | string | "Start with [#1 mode]. Ignore the other modes until you have used this one a few times." |

### Constraints

- Does NOT rank infrastructure modules (Navigator, Coordinator, any module numbered above 11 in the user-facing set)
- Does NOT expose Expert sub-variants (domain, infra, ERA) or Critic sub-variants (adversarial, linter, audit)
- Does NOT appear in the orchestrator mode trigger table — this is a skill, not a mode
- Navigator is excluded from the ranking output (it fires automatically; users do not select it)
- Maximum ranked output: 3 modes. Minimum: 2.
- Ranking is deterministic on description content — same description produces same ranking (idempotent)

### Integration

- Receives from: user explicit invocation
- Sends to: no downstream mode; output is terminal
- Coordination pattern: none — skill fires and completes in one turn
- Not triggered by orchestrator routing — user must invoke explicitly

---

## Decision Type Tags

| Decision | Type | Rationale |
|----------|------|-----------|
| Home module is 01_navigator.md | Evaluative | Both fit-check and Navigator are routing-assistance functions. Module 01 is the routing-focused module; Module 06 Quick Reference is deep agent reference. Fit-check belongs where routing logic lives, not in reference. |
| Skill, not a mode | Reckoning | Fit-check produces no analytical artifact. It classifies intent and points. Modes produce work product. |
| 2-3 mode output ceiling | Evaluative | Fewer than 2 is too directive for users with mixed workloads. More than 3 creates decision paralysis at exactly the moment the user is trying to reduce it. |
| Navigator excluded from ranking | Reckoning | Navigator fires automatically on KF detection of ambiguity. Users cannot usefully pre-select it; including it in fit-check output would confuse its automatic trigger semantics. |
| Calibrator overlap assessed at 15% | Evaluative | Both can surface Calibrator as a recommendation; both can fire when a user describes setup work. Functional inputs and outputs are orthogonal: fit-check classifies task intent, Calibrator audits project config health. Sequential composition is valid; redundancy is not present. |

---

## Implementation

### Trigger Conditions

The skill activates on any of these explicit user phrasings:

- "what KF modes should I use"
- "KF fit check"
- "where do I start with KF"
- `/kf-fit-check`
- "which modes are relevant for [described work]"
- Equivalent first-contact orientation phrasings (e.g., "which KF mode fits my project", "help me pick a mode")

Navigator's ambiguity detection does NOT trigger fit-check. Fit-check is user-initiated.

### Input Protocol

1. If the trigger arrives without a work description: respond with exactly "Describe your current work or project in 2-3 sentences."
2. If the trigger arrives with an inline description (e.g., "KF fit check — I'm building a multi-agent pipeline for X"): proceed directly without re-prompting.
3. Minimum viable input: one complete sentence describing a concrete work activity. If the user provides only a topic word (e.g., "AI agents"), ask for a sentence.

### Ranking Protocol

Map the description to modes using these primary signals. First matching signal wins primary slot. Secondary slot is the next strongest match.

| Signal in description | Primary mode |
|-----------------------|-------------|
| "creating", "building", "writing", "designing", "implementing", "adding", "scaffolding" | Builder |
| "broken", "failing", "not working", "error", "bug", "crash", "why is", "unexpected" | Debugger |
| "should I", "which option", "trade-off", "decide", "prioritize", "worth it", "torn between" | Strategist |
| "patterns", "common across", "extract", "generalize", "abstract", "distill", "recurring" | Synthesizer |
| "review", "check", "validate", "audit", "find gaps", "before we ship", "what am I missing" | Critic |
| "blast radius", "second-order", "irreversible", "production decision", "complex system" | Expert |
| "configure", "setup", "CLAUDE.md", "project conventions", "guardrails", "coding standards" | Calibrator |
| "multiple agents", "workflow", "coordinate", "pipeline", "orchestrate", "handoff" | Coordinator |

**Multi-activity descriptions:** rank by which activity appears first or is most concrete (has specifics, not vague qualifiers).

**No-match fallback:** if the description does not match any signal, ask one clarifying question: "Is this primarily about creating something, diagnosing a problem, making a decision, or something else?"

### Output Format

```
Based on your description, the most relevant KF modes are:

1. **[Mode]** — [one sentence tied to what user described]
2. **[Mode]** — [one sentence tied to what user described]
3. **[Mode]** — [one sentence tied to what user described, if applicable]

Start with [#1 mode]. Ignore the other modes until you have used this one a few times.
```

The justification sentences must reference the user's actual description, not generic mode descriptions. "Builder — you said you're writing a Stripe webhook handler" is correct. "Builder — for creating new agents and systems" is not.

---

## Test Set

Five test descriptions with expected outputs. These are acceptance tests for the implementation.

**Test 1 — Pure build:**
Description: "I'm writing a new Python service that handles webhook events from Stripe. I need to design the data model and write the processing logic."
Expected #1: Builder (creating, writing)
Expected #2: Coordinator (if multi-service scope implied) or Critic (review before implementation)
Expected excluded from ranking: Debugger, Strategist, Expert, Calibrator

**Test 2 — Pure debug:**
Description: "My API endpoint is returning 500 errors on POST requests but not GET. I've been trying to fix it for two hours and cannot figure out why."
Expected #1: Debugger (failing, not working, error)
Expected #2: Strategist (if scope of fix vs. rebuild is a live question)
Expected excluded from ranking: Builder, Synthesizer, Calibrator, Coordinator

**Test 3 — Pattern extraction:**
Description: "I have 12 different AI agent projects from the last year. I want to understand what architectural patterns I keep using so I can standardize them."
Expected #1: Synthesizer (patterns, recurring, generalize)
Expected #2: Builder (standardization produces a template)
Expected excluded from ranking: Debugger, Expert, Calibrator

**Test 4 — Strategy:**
Description: "We have three ways to approach the authentication system rewrite — session-based, JWT, or OAuth delegation. I need to pick one and justify it to the team."
Expected #1: Strategist (trade-off, decide, which option)
Expected #2: Expert (if irreversibility or blast radius is in scope)
Expected excluded from ranking: Builder, Debugger, Synthesizer, Calibrator

**Test 5 — Review:**
Description: "My team just finished a six-week spec for a new data pipeline. I want to find any gaps, unstated assumptions, or edge cases before we start implementing."
Expected #1: Critic (review, find gaps, what am I missing)
Expected #2: Expert (pipeline is production-scope with complex dependencies)
Expected excluded from ranking: Builder, Debugger, Synthesizer, Calibrator

---

## Calibrator Overlap Assessment

| Dimension | Fit-Check | Calibrator Context Hygiene Audit |
|-----------|-----------|----------------------------------|
| Input | User task intent description | Project CLAUDE.md and config files |
| Output | Mode ranking for routing | Config health report with remediation |
| Trigger | Explicit user phrase | Explicit user invocation or periodic audit |
| Operates on | What the user wants to do | What the project environment looks like |
| Can surface Calibrator | Yes (if description includes setup signals) | N/A (it IS Calibrator) |

Overlap: ~15%. The only intersection is that fit-check may rank Calibrator as a recommended mode when a user describes setup work. This is correct behavior, not redundancy. If both fire in the same session (fit-check recommends Calibrator, user then invokes Calibrator), they are sequential and complementary. Functional overlap is CLEAR.

---

## Placement in Module 01

- Added after the existing `## CC Skill` section (the Navigator skill, currently at line 383)
- As a NEW `## CC Skill` section titled: `## CC Skill — KF Fit Check`
- Does not replace or modify the existing Navigator CC Skill section
- Module version bump: 6.6.2 if Component 2 (Navigator confusion-detection amendment) ships first; 6.6.3 if this skill is committed separately after Component 2
- The compiled output path (`.claude/skills/kf/fit-check.md`) must appear in the section header comment

---

## Acceptance Criteria

- [ ] Skill section added to `modules/01_navigator.md` after the existing CC Skill section
- [ ] Section header is exactly `## CC Skill — KF Fit Check`
- [ ] Compiled path `.claude/skills/kf/fit-check.md` documented in section header
- [ ] Trigger conditions include all six specified phrasings
- [ ] Input protocol: asks for 2-3 sentence description when not provided; accepts inline description without re-prompting
- [ ] Output format: 2-3 ranked modes with justifications tied to user's description, plus "Start with #1" directive
- [ ] No infrastructure modules in ranking output
- [ ] No Expert or Critic sub-variants exposed
- [ ] Navigator excluded from ranking (marked as automatic in output if user asks)
- [ ] Idempotent: same description produces same ranking
- [ ] All 5 test descriptions produce the expected #1 mode when run through the skill
- [ ] Calibrator functional overlap confirmed at < 20% in this spec
- [ ] Module 01 version bumped per versioning rules
- [ ] `kf.yaml` changelog updated to reflect module minor bump

---

## Dependencies

- Component 2 (Navigator 6.6.2 confusion-detection amendment) should be committed first — this skill goes into the same module file. If Component 2 is not yet committed, this skill is the first change to `01_navigator.md` and takes version 6.6.2.
- Phase 0 path convention confirmed: `## CC Skill` in module file, not standalone `skills/` directory
- Module 06 Quick Reference unchanged — fit-check does not replace it; the quickstart cross-link to Module 06 remains valid
- Calibrator Module 11 unchanged — overlap confirmed clear, no coordination needed
- Compiler (`compiler/kf-compile.py`) must extract `## CC Skill — KF Fit Check` and write it to `.claude/skills/kf/fit-check.md` in variant repos — verify compiler skill-extraction regex handles titled CC Skill sections
