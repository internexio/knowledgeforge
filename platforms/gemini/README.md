# KnowledgeForge — Gemini (Planned)

## Status

🔜 Planned — not yet implemented.

The platform binding stub exists at [`platform-bindings/gemini.yaml`](../../platform-bindings/gemini.yaml).

## Planned target format

- **Gemini system instruction** — orchestrator + modes compiled for the Gemini API and Gemini for Google Workspace
- Possible integration with NotebookLM or Gemini Gems

## Contributing

If you want to build the Gemini target:

1. Review `platform-bindings/gemini.yaml`
2. Add a `--target gemini` compile path in `compiler/kf-compile.py`
3. Add a load map at `platforms/gemini/load-map.md`
4. Update this README with install instructions

Open an issue: [github.com/internexio/knowledgeforge/issues](https://github.com/internexio/knowledgeforge/issues)
