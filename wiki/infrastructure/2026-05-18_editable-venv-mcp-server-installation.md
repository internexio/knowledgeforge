---
title: Editable-venv install for MCP servers — Python version floors + dependency major bumps
source_mode: builder
novelty_type: reusable_diagnostic
grounding_score: 0.65
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-05-18
domain: integration
topic: mcp-protocol
tags: mcp, packaging, deployment, empirical
related_entries: [patterns/2026-05-18_composite-vs-atomic-mcp-tool-design.md]
---

# Editable-venv Install for MCP Servers — Python Version Floors + Dependency Major Bumps

## Pattern

For local-install dogfood of an MCP server that hasn't shipped to PyPI yet, use a dedicated `python3.X -m venv` (matching the package's `requires-python` floor) and editable `pip install -e .`. Register with Claude Code via `claude mcp add` pointing at the venv's binary path. System pip and global Python often produce subtle failures — venvs eliminate both.

## Two Specific Failure Modes This Pattern Avoids

### 1. System Python Version Mismatch

On macOS, `pip install -e .` defaults to the system Python (often 3.9.x on older OS versions). Packages declaring `requires-python = ">=3.10"` in pyproject.toml will fail with:

```
ERROR: Package 'X' requires a different Python: 3.9.6 not in '>=3.10'
```

**Fix:** `python3.11 -m venv .venv && .venv/bin/pip install -e .`. Use the venv's bin/Python, never the system one.

### 2. Dependency Major-Version Internal API Drift

Test scripts that worked at install-time may break later when a transitive dep bumps a major version. Specific instance from this session: `fastmcp 2.x` exposed `mcp._tool_manager._tools` for enumeration; `fastmcp 3.3.1` removed that attribute. Test code that read `_tool_manager` raised `AttributeError`. The fix: use the public async API (`tools = await mcp.list_tools()`) instead of private attributes. General rule: never read underscore-prefixed attributes from a dep; use only documented public APIs.

## The Full Pattern (Verified End-to-End This Session)

```bash
# 1. Create venv with explicit Python version matching pyproject's floor
cd /path/to/your-mcp-package
python3.11 -m venv .venv

# 2. Editable install — picks up local source changes without reinstall
.venv/bin/pip install -e .

# 3. Verify CLI exists at venv path
.venv/bin/your-mcp --help  # or your CLI's entrypoint

# 4. Verify tools register (use async API, not private attrs)
.venv/bin/python -c "
import asyncio
from your_mcp.server import mcp
async def main():
    tools = await mcp.list_tools()
    for t in sorted(tools, key=lambda t: t.name):
        print(t.name)
asyncio.run(main())
"

# 5. Register with Claude Code — point at the venv binary explicitly
claude mcp add your-mcp \
  --env YOUR_API_KEY=... \
  --env YOUR_API_URL=https://... \
  -- /full/path/to/.venv/bin/your-mcp

# 6. Verify connection
claude mcp list | grep your-mcp  # should show "✓ Connected"
```

## Gotchas

- **`.venv/` must be gitignored** at the package level OR globally. Check before committing other changes in the same repo.
- **`pip install -e .` requires the working tree** — uninstalling the venv breaks the install. Don't move the package directory after registration.
- **`claude mcp add` writes to `~/.claude.json`** — registration is persistent across sessions. Use `claude mcp remove your-mcp` to undo cleanly.
- **`COS_API_KEY` and any other secrets in `--env`** are stored in `~/.claude.json` in plaintext. Treat that file like a credentials store.

## When This Applies

- MCP server packages developed locally, not yet on PyPI
- Dogfood / pre-release verification of new tools
- Demo recipes that need a specific Python version
- Any time `pip install <package>` would fail due to Python floor

## When This Does NOT Apply

- Packages already on PyPI at the version you want — just `pip install <package>` (in a venv still, but no editable mode needed)
- HTTP-transport MCPs (no local install — just `claude mcp add --transport http <url>`)
- Containerized MCPs (use Docker-based registration instead)

## Grounding from Session

Built `cos-mcp 0.2.0` (Python `>=3.10`) with new `audience_profile` + `optimize_email_for_prospect` tools. PyPI publish was deliberately held pending dogfood verification. Steps run, verified:

- `python3.11 -m venv .venv` → succeeded (system Python was 3.9.6, would have failed)
- `.venv/bin/pip install -e .` → installed 60+ transitive deps including `fastmcp 3.3.1`
- Test script using `mcp._tool_manager._tools` → AttributeError (fastmcp 3.x removed the attr)
- Switched to `await mcp.list_tools()` → 13 tools enumerated correctly
- `claude mcp add cos-mcp -- ~/Scripts/[project]/cos/cos-mcp/.venv/bin/cos-mcp` → registered
- `claude mcp list` → `cos-mcp: ✓ Connected`

End-to-end install + register took ~3 minutes. No system Python pollution. No dep conflicts. Cleanly removable.

## Counterexample / Failure Mode to Watch

- Don't install the MCP into your project's main venv (e.g. backend's venv). MCPs run in separate processes — keep their venvs separate from application venvs.
- Don't use `pipx install` for editable workflows — pipx is great for stable CLIs but resists editable installs by design.
- macOS Homebrew Python may shadow system Python. Always check `which python3.11` first.

## Cross-References

Pairs with [patterns/2026-05-18_composite-vs-atomic-mcp-tool-design.md] — the MCP design pattern + this install pattern together give a full local-to-deployed workflow.

## Source Context

Built `cos-mcp 0.2.0` during cos-mcp-clarify-integration-phase2-3 session. Verified editable venv installation + registration with `claude mcp add` to resolve Python floor version mismatch and fastmcp API drift issues.
