# KnowledgeForge — Claude Code

## What you get

- **KF orchestrator agent** (`kf.md`) — routes every prompt to the right mode
- **10+ specialized agents** — builder, critic, debugger, strategist, synthesizer, expert, coordinator, navigator, calibrator, knowledge-librarian, adversarial-critic
- **Skill files** for each mode — loaded on-demand via the agent
- **Hooks** — pre-prompt routing, session start, stop validation, post-compact
- **Knowledge wiki** (`wiki/`) — auto-accretes session learnings to disk

## Quick install

Install the compiled Claude Code variant directly:

```bash
git clone https://github.com/internexio/knowledgeforge-cc ~/.claude/plugins/knowledgeforge
cd ~/.claude/plugins/knowledgeforge
bash install.sh
```

The install script registers the agents, skills, and hooks. It does not touch your existing `CLAUDE.md` or project files.

## Routing hook (optional but recommended)

The pre-prompt routing hook classifies every user message and injects a `[KF-ROUTE]` directive before Claude processes it — faster, more reliable mode activation.

The hook uses **Gemini Flash Lite** for classification (fast, cheap, falls back gracefully):

```bash
export GEMINI_API_KEY=your_key_here
```

Without the key, the hook skips injection and Claude routes natively via the orchestrator's built-in routing table. Routing still works — just without the pre-classification assist.

## Compile from source

If you prefer to compile from this repo rather than cloning the pre-built variant:

```bash
python3 compiler/kf-compile.py --target claude-code --output /path/to/knowledgeforge-cc
cd /path/to/knowledgeforge-cc && bash install.sh
```

## Output mapping

See [load-map.md](load-map.md) for the complete mapping of module sections → compiled output files.
