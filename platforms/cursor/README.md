# KnowledgeForge — Cursor (Planned)

## Status

🔜 Planned — not yet implemented.

The platform binding stub exists at [`platform-bindings/cursor.yaml`](../../platform-bindings/cursor.yaml).

## Planned target format

- **`.cursorrules`** — orchestrator + mode routing compiled into Cursor's rules format
- Possibly a `.cursor/rules/` directory structure for modular loading

## Contributing

If you want to build the Cursor target:

1. Review `platform-bindings/cursor.yaml`
2. Add a `--target cursor` compile path in `compiler/kf-compile.py`
3. Add a load map at `platforms/cursor/load-map.md`
4. Update this README with install instructions

Open an issue: [github.com/internexio/knowledgeforge/issues](https://github.com/internexio/knowledgeforge/issues)
