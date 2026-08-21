---
description: "Manage KF behavioral loops. Usage: /kf-loop [enable|pause|disable|status|list] [name]"
---

Manage KnowledgeForge behavioral loops. Active loops inject their rules on every prompt turn — they don't decay as context grows.

Run: `python3 ~/.claude/hooks/kf-loop.py $ARGUMENTS`

Show the output to the user exactly as returned.

If $ARGUMENTS is empty, default to `status`.

Built-in loops: de-ai, decision-tag, accretion-check
