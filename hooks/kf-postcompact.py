#!/usr/bin/env python3
"""
kf-postcompact.py — KnowledgeForge PostCompact Hook
Hook type: PostCompact
Purpose: After context compaction, inject a minimal context block so Claude
         resumes with the right mode and knows what the original intent was.
         Asymmetry rule: inject LESS than PreCompact. Target < 200 tokens.
         Do NOT inject the full session_summary.md — just mode, intent, chain.

Graceful degradation: any failure → exit 0 (no injection, Claude handles raw).
Output: {"additionalContext": "..."} or nothing (exit 0).

Env vars: CLAUDE_PROJECT_DIR — project root (fallback: cwd)
"""

import sys
import json
import os
from pathlib import Path

# ─── State directory resolution ───────────────────────────────────────────────

def get_state_dir() -> Path:
    project_root = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd()))
    return project_root / ".kf" / "state"


def read_state_file(state_dir: Path, filename: str, default: str = "") -> str:
    try:
        path = state_dir / filename
        if not path.exists():
            return default
        return path.read_text(encoding="utf-8").strip()
    except Exception as e:
        sys.stderr.write(f"[kf-postcompact] Could not read {filename}: {e}\n")
        return default

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    try:
        raw_input = sys.stdin.read()
        # Parse stdin but we don't need the summary content for injection logic
        json.loads(raw_input)
    except Exception as e:
        sys.stderr.write(f"[kf-postcompact] Could not parse hook input: {e}\n")
        sys.exit(0)

    state_dir = get_state_dir()

    # If state directory doesn't exist, nothing to inject
    if not state_dir.exists():
        sys.exit(0)

    # Read state files
    mode = read_state_file(state_dir, "active_mode")
    intent = read_state_file(state_dir, "original_intent")
    chain_step = read_state_file(state_dir, "chain_step")

    # If no meaningful state found, nothing to inject
    if not mode and not intent:
        sys.exit(0)

    # Build minimal context block (target: < 200 tokens)
    # Asymmetry rule: inject less than PreCompact — one-liners only, no summary
    lines = ["[KF State — post-compaction resume]"]
    if mode:
        lines.append(f"Mode: {mode}")
    if intent:
        lines.append(f"Original intent: {intent}")
    if chain_step and chain_step != "none":
        lines.append(f"Chain: {chain_step}")
    lines.append("State files: .kf/state/ (routing_index.yaml, session_summary.md available)")

    context = "\n".join(lines)

    output = {"additionalContext": context}
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[kf-postcompact] Unhandled exception: {e}\n")
        sys.exit(0)
