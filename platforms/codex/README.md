# KnowledgeForge — Codex (Planned)

## Status

🔜 Planned — not yet implemented.

The platform binding stub exists at [`platform-bindings/codex.yaml`](../../platform-bindings/codex.yaml).

## Planned target format

- **`AGENTS.md`** — orchestrator compiled to Codex's agent instruction format
- Mode-specific context injection via Codex's file-based context system

## Contributing

If you want to build the Codex target:

1. Review `platform-bindings/codex.yaml`
2. Add a `--target codex` compile path in `compiler/kf-compile.py`
3. Add a load map at `platforms/codex/load-map.md`
4. Update this README with install instructions

Open an issue: [github.com/internexio/knowledgeforge/issues](https://github.com/internexio/knowledgeforge/issues)
