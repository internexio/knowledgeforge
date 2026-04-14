#!/usr/bin/env python3
"""
kf-edit-nudge.py — KnowledgeForge PostToolUse Hook (Edit Nudge)
Hook type: PostToolUse
Purpose: Count file edit operations. After every 10 edits, append a nudge to
         the tool response reminding Claude to checkpoint (commit or save)
         before continuing. Counter resets when the nudge fires.

         Triggers on: Edit, Write, MultiEdit (case-insensitive tool name match).
         All other tools: exit 0 immediately.

Graceful degradation: any failure → exit 0 (never modify tool response on error).
Output: modified hookSpecificOutput with nudge appended, or nothing (exit 0).

Env vars: CLAUDE_PROJECT_DIR — project root (fallback: cwd)
"""

import sys
import json
import os
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

NUDGE_AT = 10
EDIT_TOOLS = {"edit", "write", "multiedit"}

# ─── State directory resolution ───────────────────────────────────────────────

def get_state_dir() -> Path:
    project_root = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd()))
    return project_root / ".kf" / "state"


def ensure_state_dir(state_dir: Path) -> bool:
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        sys.stderr.write(f"[kf-edit-nudge] Could not create state dir: {e}\n")
        return False


def read_count(state_dir: Path) -> int:
    try:
        count_file = state_dir / "edit_count"
        if not count_file.exists():
            return 0
        return int(count_file.read_text(encoding="utf-8").strip() or "0")
    except Exception as e:
        sys.stderr.write(f"[kf-edit-nudge] Could not read edit_count: {e}\n")
        return 0


def write_count(state_dir: Path, count: int) -> None:
    try:
        (state_dir / "edit_count").write_text(str(count), encoding="utf-8")
    except Exception as e:
        sys.stderr.write(f"[kf-edit-nudge] Could not write edit_count: {e}\n")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    try:
        raw_input = sys.stdin.read()
        hook_input = json.loads(raw_input)
    except Exception as e:
        sys.stderr.write(f"[kf-edit-nudge] Could not parse hook input: {e}\n")
        sys.exit(0)

    # Only act on edit-family tools
    tool_name = hook_input.get("tool_name", "").lower().strip()
    if tool_name not in EDIT_TOOLS:
        sys.exit(0)

    # Ensure state directory exists
    state_dir = get_state_dir()
    if not ensure_state_dir(state_dir):
        sys.exit(0)

    # Read, increment, and persist count
    count = read_count(state_dir) + 1
    write_count(state_dir, count)

    # Only nudge when threshold is reached
    if count < NUDGE_AT:
        sys.exit(0)

    # Build nudge message
    nudge = (
        f"\n\n---\n"
        f"[KF: {count} edits since last checkpoint. "
        f"Consider saving progress or committing before continuing.]"
    )

    # Append nudge to tool_response
    tool_response = hook_input.get("tool_response", "")
    if not isinstance(tool_response, str):
        # If tool_response is structured (e.g. dict), convert to string for safety
        try:
            tool_response = json.dumps(tool_response)
        except Exception:
            tool_response = str(tool_response)

    modified_response = tool_response + nudge

    # Reset counter after nudge fires
    write_count(state_dir, 0)

    # Emit modified tool response
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "toolResponse": modified_response,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[kf-edit-nudge] Unhandled exception: {e}\n")
        sys.exit(0)
