# KnowledgeForge Quickstart

## What KF Does That Raw Claude Doesn't

Raw Claude responds to every request the same way — it does not change its reasoning strategy based on what you are trying to accomplish. KF patches this by routing your request to a mode whose protocol is shaped for that class of problem: creating, diagnosing, reviewing, deciding. The practical effect is that KF forces the second question raw Claude skips — a Builder asks what constraints exist, a Critic asks what the spec assumes, a Strategist asks what you are deferring. There is no configuration required. KF classifies and routes automatically; your job is to phrase the request clearly enough for classification to fire correctly.

---

## The 9 Modes

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

---

## Good vs. Bad Phrasing

Vague requests trigger Navigator, which stops to ask clarifying questions. Specific requests route directly to the right mode.

**Goal: debug a failing test**

| | Phrasing |
|---|---|
| Bad | `"What's wrong with my test?"` — too vague, Navigator fires to clarify |
| Good | `"Diagnose why my auth test is failing on line 47"` → **Debugger** |

**Goal: review an architecture plan**

| | Phrasing |
|---|---|
| Bad | `"Is this good?"` — too vague, Navigator fires to clarify |
| Good | `"Review this service topology for gaps and unstated assumptions"` → **Critic** |

**Goal: choose between two implementation approaches**

| | Phrasing |
|---|---|
| Bad | `"Which is better, approach A or B?"` — too vague, Navigator fires to clarify |
| Good | `"Weigh the trade-offs between approach A and B for a 50k-user load"` → **Strategist** |

---

## The Ozymandias Check

Ozymandias was the king who declared his works eternal; the decay was already in progress and he missed it. The check is named for that failure mode: confident short answers that miss the structural problem underneath. The rule is this — if answering a yes/no question requires multi-paragraph reasoning, it is not a simple lookup; upgrade it to an evaluative or novel judgment. In practice, before asking KF "should I do X?", ask whether X has meaningful trade-offs, irreversible consequences, or dependencies you have not mapped. If yes, frame the question as a decision with context, not a yes/no. The check is not a framework overhead — it is a prompt to notice what you are actually asking.

---

> For the full routing reference, see [Module 06 Quick Reference](modules/06_quick_reference.md).
