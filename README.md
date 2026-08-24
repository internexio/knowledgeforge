# KnowledgeForge

## The problem

AI coding assistants fail in predictable ways.

They loop on the same error. They skip hypothesis enumeration on hard bugs and jump to the first plausible answer. They surface recommendations without naming trade-offs. They reach for framework abstractions on problems that need five lines.

These aren't model failures. They're routing failures. The reasoning approach that works for a debugging task is wrong for a trade-off decision. Sending every request through the same undifferentiated prompt makes all of these worse.

KnowledgeForge fixes the routing.

---

## What it is

KnowledgeForge is a reasoning harness for AI coding assistants. It classifies each request by decision type and routes it to a mode built to prevent that type's typical failure:

- **Debugging** gets forced hypothesis enumeration. The model cannot declare a root cause without evidence. Each new hypothesis must differ from everything already eliminated.
- **Recommendations** get explicit trade-off surfacing. Every option includes what it costs and what it forecloses.
- **Reviews** are read-only by constraint. The reviewer cannot modify what it reviews.
- **Simple questions** get direct answers with no framework overhead at all.

Nine modes. Each one handles a distinct class of reasoning problem. The orchestrator classifies the request, routes it, and chains modes automatically when a task needs more than one — "fix this bug" runs Debugger then Builder without being told to.

| Failure Mode | Without KF | With KF |
|---|---|---|
| **Wrong reasoning depth** | Novel strategic question treated like a factual lookup | Decision classification routes each to the correct depth first |
| **Skipping hypotheses** | "The bug is in X" stated without evidence | Debugger requires >0.8 confidence; documents hypothesis → elimination path |
| **Hidden trade-offs** | "Use option A" without mentioning what you sacrifice | Strategist: quantified trade-offs + reversibility always assessed |
| **Spec gaps** | Ships incomplete requirements | Critic: systematic completeness check + adversarial variant assuming ≥1 flaw |
| **Session drift** | Routing accuracy degrades as context fills | Three-tier memory: routing index always loaded, utilization plateaus |
| **Retry loops** | Keeps trying the same failing approach | Circuit breakers: 3 failures → halt, surface pattern, present options |
| **Missing adversarial thinking** | "Looks good to me" without real challenge | Auto-verification fires on qualifying chains — framed to find what the producing agent missed |

> **"KF modes patch Claude's weaknesses, not scaffold its strengths."**
>
> Modes activate only when they prevent a known failure. Most requests route directly.

---

## How it works

```
Request arrives
    │
    ▼
Decision Classification (always, silent)
    │
    ├── Reckoning (verifiable answer)
    │       └── Answer directly. <50 tokens. No mode.
    │
    ├── Evaluative judgment (criteria exist)
    │       └── Structured analysis with confidence. Mode if needed.
    │
    ├── Predictive judgment (future outcomes)
    │       └── Explicit assumptions + probability ranges. Mode activated.
    │
    └── Novel judgment (no precedent)
            └── Full expanded reasoning. Human review flagged. Mode activated.
```

Routing is handled by [M00 Orchestrator](modules/00_orchestrator.md). Decision types are defined in [M13 Decision Classification](modules/13_decision_classification.md). All 27 modules listed in [docs/modules.md](docs/modules.md).

---

## The circuit breaker

After the same failure mode appears three consecutive times, KnowledgeForge pauses instead of looping.

Every failed attempt is logged and stays in context. The next diagnosis must differ from every approach already tried. The model cannot re-enter a hypothesis it has already eliminated.

This is the feature that matters most in practice. Looping on the same error is the most expensive failure mode in agentic work — it compounds across sessions, burns context, and produces no new information. The circuit breaker kills the loop, forces a different angle, and surfaces the pattern so you can see it.

---

## How it got to nine modes

KnowledgeForge started in 2023 as a stack of instruction files in a ChatGPT project. Patterns I had noticed. Things I wanted the model to carry between sessions.

By late 2025 it had 43 modules — one for every failure mode I had actually hit. Decision classification. Confidence calibration. Adversarial verification. Knowledge accretion. A module for each.

A framework with 43 modules is not a framework. It is a documentation project.

I ran a Pareto pass: which modules produced measurable results in daily work, which were overhead built for edge cases that never recurred. Nine modes survived. The other 34 existed because I was anxious about coverage, not because they paid for themselves.

What survived: Builder, Critic, Debugger, Strategist, Expert, Synthesizer, Calibrator, Coordinator, Navigator. Each one addresses a real, recurring failure mode. Nothing in the list exists for completeness.

The 27 underlying modules (M00–M26) implement those nine modes plus the cross-cutting infrastructure they share: memory architecture, decision classification, knowledge accretion, grounding scores.

---

## Quick Install

Works with Claude Code, Claude Projects, ChatGPT Projects, Codex CLI, VSCode, and a platform-agnostic plugin bundle.

### Claude Code

Works with Claude Code, Windsurf, and Zed — any editor that supports the `~/.claude/` agent convention.

```bash
git clone https://github.com/internexio/knowledgeforge
cd knowledgeforge
bash install.sh
```

`install.sh` copies the pre-compiled variant from [`platforms/claude-code/`](platforms/claude-code/) to `~/.claude/`. Restart your editor after install.

See [`docs/install.md`](docs/install.md) for the full guide: `settings.json` configuration, add-ons setup, and other platform install paths.

### Claude Projects

1. Create or open a Claude Project at [claude.ai](https://claude.ai)
2. **Project Instructions** → paste the full contents of [`platforms/claude-projects/00_Project_Instructions-Claude.md`](platforms/claude-projects/00_Project_Instructions-Claude.md)
3. **Project Knowledge** → upload all 26 files from [`platforms/claude-projects/`](platforms/claude-projects/)
4. Start a conversation — routing is automatic

> Delete all existing KF knowledge files before re-uploading. Claude Projects appends rather than replaces — duplicate filenames create contradictions that retrieval cannot resolve.

---

## Navigation

- [Full install guide](docs/install.md) — CC + CP paths, `settings.json` config, all platforms, add-ons
- [Add-ons](docs/add-ons.md) — MemPalace, Gemini Routing, Beads, GitNexus, Asta, COS, Orchestra
- [Modules](docs/modules.md) — all 27 modules with versions and purposes
- [Changelog](CHANGELOG.md) — full version history
- [Exploration prompts](EXPLORATION_PROMPTS.md) — ready-to-paste prompts that exercise specific KF behaviors
- [Distribution matrix](docs/dist-matrix.md) — platform capability and module coverage matrix
- [Glossary](docs/glossary.md) — acronyms, invented terms, and framework-specific vocabulary
- [Credits](docs/credits.md) — contributors, inspirations, and the broader community

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for module conventions, versioning rules, and commit format.
See [`SECURITY.md`](SECURITY.md) for the vulnerability reporting process.

---

## License

Apache-2.0. Copyright 2026 David Pedersen. See [`LICENSE`](LICENSE).

**Version:** 7.36.0 | **Modules:** 27 (M00–M26)
