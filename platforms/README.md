# KnowledgeForge — Platforms

KnowledgeForge compiles to multiple AI assistant platforms from a single canonical source in `modules/`. Pick your platform below.

| Platform | Status | Guide |
|----------|--------|-------|
| [Claude Code](claude-code/) | ✓ Tested | [Install guide](claude-code/README.md) |
| [Claude Projects](claude-projects/) | ✓ Tested | [Install guide](claude-projects/README.md) |
| [Plugin Bundle](plugin-bundle/) | 🧪 Experimental | [Install guide](plugin-bundle/README.md) |
| [VSCode Copilot](vscode/) | 🧪 Experimental | [Install guide](vscode/README.md) |
| [ChatGPT Projects](chatgpt/) | 🧪 Experimental | [Install guide](chatgpt/README.md) |
| [Codex CLI](codex/) | 🧪 Experimental | [Install guide](codex/README.md) |
| [Cursor](cursor/) | 🧪 Experimental / planned | — |
| [Gemini](gemini/) | 🧪 Experimental / planned | — |

## How it works

The 26 module specs in `modules/` are platform-agnostic. The compiler (`compiler/kf-compile.py`) reads platform bindings from `platform-bindings/*.yaml` and produces platform-specific output — skill files and agents for Claude Code, a compiled system prompt for Claude Projects, VSCode extension resources, and so on.

Only the Claude Code and Claude Projects variants are currently considered tested. Every other target is experimental, including targets whose compiler implementation is active.

```
modules/           ←  canonical source (platform-agnostic)
platform-bindings/ ←  per-platform adaptation rules (YAML)
compiler/          ←  kf-compile.py — translates core → platform output
platforms/         ←  you are here — install guides and load maps
```

## Adding a new platform

1. Add a binding at `platform-bindings/<platform>.yaml`
2. Add a compile target in `compiler/kf-compile.py`
3. Add an install guide at `platforms/<platform>/README.md`
4. Run `python3 compiler/kf-compile.py --target <platform> --verify`

See `CONTRIBUTING.md` for conventions.
