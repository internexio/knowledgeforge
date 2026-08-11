# KnowledgeForge — Plugin Bundle

> **Experimental:** Bundle generation is implemented, but this distribution has not received the same validation coverage as the Claude variants.

The plugin bundle is a self-contained, redistributable package of KF agents and skills for use in Claude Code plugin marketplaces and managed deployments.

## What's included

- Core agents: builder, critic, debugger, strategist, synthesizer, expert, coordinator, calibrator, knowledge-librarian
- Skill files for each agent
- Plugin manifest (`plugin.json`) — marketplace-compatible metadata
- Install script (`install.sh`)

Excludes: hooks (routing, session management) and the wiki — those require per-user setup and are not appropriate for bundle distribution.

## Install

```bash
git clone https://github.com/internexio/knowledgeforge-cc
cd knowledgeforge-cc
bash install-plugin-bundle.sh
```

Or install from a released bundle artifact:

```bash
# Download the latest plugin bundle from GitHub Releases
curl -L https://github.com/internexio/knowledgeforge/releases/latest/download/plugin-bundle.zip -o plugin-bundle.zip
unzip plugin-bundle.zip
cd plugin-bundle && bash install.sh
```

## Compile from source

```bash
python3 compiler/kf-compile.py --target plugin-bundle --output /path/to/bundle
```

## Output mapping

See [load-map.md](load-map.md) for the complete mapping of modules → compiled output files.
