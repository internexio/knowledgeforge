# KnowledgeForge — Claude Projects

## What you get

- **Compiled system prompt** (`00_Project_Instructions-Claude.md`) — paste into Project Instructions
- **25 knowledge files** — one per module, uploaded to Project Knowledge
- Full mode routing, chaining, and cross-cutting behaviors — no hooks or file system required

## Install

> **Before uploading:** delete all existing KF knowledge files from the project first. Claude Projects appends rather than replaces. Duplicate filenames create a contradiction source where retrieval cannot distinguish canonical from stale.

1. Create or open a Claude Project at [claude.ai](https://claude.ai)
2. **Project Instructions** → paste the full contents of `00_Project_Instructions-Claude.md` from `knowledgeforge-cp/`
3. **Project Knowledge** → upload all 25 module files from `knowledgeforge-cp/`
4. Start a conversation — mode routing activates automatically

The compiled variant is in the [`knowledgeforge-cp`](https://github.com/internexio/knowledgeforge-cp) repo.

## Why M25 (ERA) matters

M25 (Entity Relationship Analysis) is required. The orchestrator runs ERA as a post-routing, pre-execution pass on Builder, Coordinator, Expert, Strategist, and Critic requests. Omitting `25_Entity_Relationship_Analysis.md` from Project Knowledge leaves five routing paths without their pre-execution graph pass.

## Compile from source

```bash
python3 compiler/kf-compile.py --target claude-projects --output /path/to/knowledgeforge-cp
```

## Output mapping

See [load-map.md](load-map.md) for the complete mapping of modules → compiled output files.
