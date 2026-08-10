# KnowledgeForge — ChatGPT (Planned)

## Status

🔜 Planned — not yet implemented.

The platform binding stub exists at [`platform-bindings/chatgpt.yaml`](../../platform-bindings/chatgpt.yaml).

## Planned target format

- **Custom GPT system prompt** — compiled from the orchestrator and mode modules
- **ChatGPT Projects** — single compiled instruction block
- Optional: **Actions schema** for any tool-use equivalents

## Contributing

If you want to build the ChatGPT target, the path is:

1. Fill out `platform-bindings/chatgpt.yaml` with the output spec
2. Add a `--target chatgpt` compile path in `compiler/kf-compile.py`
3. Add a load map at `platforms/chatgpt/load-map.md`
4. Update this README with install instructions

Open an issue to discuss scope before starting: [github.com/internexio/knowledgeforge/issues](https://github.com/internexio/knowledgeforge/issues)
