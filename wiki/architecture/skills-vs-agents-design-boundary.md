# Skills vs. Agents Design Boundary

```yaml
metadata:
  source_mode: synthesizer
  source_session: redacted
  created: "2026-04-29T00:00:00Z"
  date: "2026-04-29"
  confidence: 0.91
  grounding_score: 0.91
  grounding_source: "CCT triage of 422 agents + skill files in davila7/claude-code-templates. Design boundary observed from systematic misclassification: context-manager (state service) placed in agents/; code-formatter (deterministic tool) placed in skills/; hook behaviors placed in neither. Cross-referenced against KF's own agent/skill/hook taxonomy."
  novelty_type: transferable_framework
  staleness_risk: stable
  importance: 4
  pinned: false
  accreted_in: "6.5"
  related:
    - wiki/architecture/scaffolding-vs-patching-pattern.md
    - modules/02_builder.md
    - modules/01_kf_orchestrator.md
```

---

## Pattern

Three Claude Code component types — skills, agents, and hooks — have distinct design responsibilities. Conflating them produces components that work but don't compose, reuse, or maintain well.

| Component | Decision-making | Persistence | Invocation | Right question |
|-----------|----------------|-------------|------------|----------------|
| **Hook** | None — rule execution only | None (stateless) | Automatic on tool event | "Should this always happen after X?" |
| **Skill** | None — deterministic given inputs | None (stateless) | Explicit by user or agent | "Can another agent reuse this as a building block?" |
| **Agent** | Yes — reasons, adapts, routes | Session-scoped context | Explicit, via sub-agent or slash-command | "Does this need to decide what to do next?" |

**Design boundary test:**
1. Does the component make decisions based on context? → Agent
2. Does it execute the same logic deterministically given inputs? → Skill
3. Does it need to fire automatically on tool events without human intervention? → Hook

---

## Why Misclassification Happens

The surface description of a component hides its decision-making depth:

- A "context manager" sounds like infrastructure → lands in agents. But if it only serializes and deserializes state from a file, it makes no decisions — it's a skill.
- A "code formatter" sounds like a tool → lands in skills. But if it runs `black` on every Python edit, it needs no user invocation — it's a hook.
- A "security reviewer" sounds like a tool → could be any of the three. If it blocks commits (hook), it's a hook. If it applies heuristics and reports findings (deterministic), it's a skill. If it adapts its analysis strategy to the codebase (reasoning), it's an agent.

The failure mode: building 422 agents when ~350 of them make no decisions and should be skills or hooks. Agents load context, acquire tools, and have behavioral guidelines — all overhead that skills and hooks don't need.

---

## Anti-Pattern — "Agent-First" Design

Make every new Claude Code component an agent by default. When uncertain, write an agent.

**What breaks:**
- Over-agents proliferate: 422 agent files in CCT where ~350 do deterministic work
- Agents designed to do deterministic work (formatting, linting, state serialization) have misleading behavioral instructions that imply reasoning occurs when it doesn't
- Skill reuse is lost: skills are invocable by any agent; agent-role-bound implementations are not
- Context budget used on agent preamble (role declaration, behavioral guidelines) for tasks that don't benefit from it

**Observed in CCT:**
- `context-manager.md` agent: opens with a JSON query to reconstruct state. The state serialization is deterministic — this is a skill. The "reasoning" is just deserialization logic.
- `code-formatter.md` agents: run black/prettier with no decision-making — should be PostToolUse hooks
- `codebase-explorer.md`: 6-phase protocol with no branching decisions — should be a command or skill, not an agent

---

## The Right Way to Decide: Inversion Test

Ask: "If I hardcoded every decision in this component, would it stop working?"

- **Agent:** Yes — it needs to adapt to context, route differently based on what it finds, or make judgment calls
- **Skill:** No — the logic is the same regardless of context; parameterize the inputs and it's done
- **Hook:** Not applicable — hooks don't have inputs (they react to events)

The inversion test catches disguised skills: a "database migration reviewer" that follows a fixed checklist every time is a skill masquerading as an agent.

---

## KF Application

KF's own component taxonomy follows this boundary cleanly:
- **Hooks:** Used for security enforcement, format-on-save, stop notifications — all automatic, no reasoning
- **Skills:** `youtube-transcript`, `cos-analysis`, `kf-*` — invocable tools with defined inputs/outputs
- **Agents:** KF modes (Builder, Critic, Debugger, Strategist) — all require reasoning and routing decisions

When adding a new KF component, apply the design boundary test before choosing the component type. The most common error in KF development is creating a new agent when a skill would compose better.

---

## Reuse Context

Reference this entry when:
- Adding a new component to KF, COS, or any Claude Code project (run the three-question test before writing)
- Reviewing a component library (CCT, community repos) for reusability — misclassified components need reclassification before adoption
- Encountering an agent that "makes no decisions" — it should be demoted to skill or hook
- Designing multi-agent workflows: skills compose better than agents for shared utility functions
