# KnowledgeForge

> Structured reasoning infrastructure for AI coding assistants. Decision-aware
> routing, adversarial verification, session-persistent memory, and cross-session
> knowledge accretion — across 27 specialized modules and 9 reasoning modes.

**Version:** 7.36.0 | **Status:** Active | **Modules:** 27 (M00–M26) | **License:** Apache-2.0

**Platforms:** [Claude Code](platforms/claude-code/) · [Claude Projects](platforms/claude-projects/) · [ChatGPT Projects 🧪](platforms/chatgpt/) · [Codex CLI 🧪](platforms/codex/) · [VSCode 🧪](platforms/vscode/) · [Plugin Bundle 🧪](platforms/plugin-bundle/) · [Cursor 🧪 planned](platforms/cursor/) · [Gemini 🧪 planned](platforms/gemini/)

> Only the Claude Code and Claude Projects variants are currently considered tested. All non-Claude targets are experimental.

---

## Why KnowledgeForge?

LLMs have predictable failure modes. Without structure, a factual lookup and a high-stakes
architectural decision go through the same reasoning process. KF patches the failures
that matter:

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

### How It Works

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

## Quick Install

### Claude Code

Works with Claude Code, Windsurf, and Zed — any editor that supports the `~/.claude/` agent convention.

```bash
git clone https://github.com/internexio/knowledgeforge
cd knowledgeforge
bash install.sh
```

`install.sh` copies the pre-compiled variant from `platforms/claude-code/.claude/` to `~/.claude/`. Restart your editor after install.

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
- [Credits](docs/credits.md) — contributors, inspirations, and the broader community

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for module conventions, versioning rules, and commit format.
See [`SECURITY.md`](SECURITY.md) for the vulnerability reporting process.

---

## License

Apache-2.0. Copyright 2026 David Pedersen. See [`LICENSE`](LICENSE).
