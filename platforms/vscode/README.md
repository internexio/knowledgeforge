# KnowledgeForge — VSCode Copilot

## What you get

KF mode resources compiled for VSCode's GitHub Copilot Chat extension — the orchestrator prompt and all mode docs injected as Copilot context resources.

## Output files

The compiled output writes to `src/resources/` in the target VSCode extension:

```
src/resources/
├── kf-orchestrator.md          # M00 verbatim — full orchestrator
├── kf-mode-registry.json       # mode registry (from platform-bindings/vscode.yaml)
└── kf-modes/
    ├── navigator.md
    ├── builder.md
    ├── coordinator.md
    ├── expert.md
    ├── critic.md
    ├── synthesizer.md
    ├── debugger.md
    ├── strategist.md
    └── calibrator.md
```

## Compile from source

```bash
python3 compiler/kf-compile.py --target vscode --output /path/to/vscode-extension
```

## Output mapping

See [load-map.md](load-map.md) for the complete mapping of modules → compiled output files.
