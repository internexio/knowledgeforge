#!/usr/bin/env python3
"""
kf-session-start.py — KnowledgeForge SessionStart Hook
Hook type: SessionStart
Purpose: On session start, detect whether this is a fresh session, a resume,
         or a post-compaction start. Inject the appropriate amount of context
         from .kf/state/ so Claude picks up the right mode and intent.

Session type detection:
  - Fresh start: no .kf/state/ or no state files → exit 0
  - Resume: transcript > 5 entries and state files exist → inject full context
  - Post-compact: transcript ≤ 5 entries (or empty) and state files exist → inject minimal context

Graceful degradation: any failure → exit 0 (never block session start).
Output: {"additionalContext": "..."} or nothing (exit 0).

Env vars: CLAUDE_PROJECT_DIR — project root (fallback: cwd)
"""

import sys
import json
import os
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

RESUME_TRANSCRIPT_THRESHOLD = 5
SESSION_SUMMARY_PREVIEW_CHARS = 300

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
        sys.stderr.write(f"[kf-session-start] Could not read {filename}: {e}\n")
        return default


def has_any_state(state_dir: Path) -> bool:
    """Return True if at least one meaningful state file exists."""
    for filename in ("active_mode", "original_intent", "session_summary.md"):
        try:
            p = state_dir / filename
            if p.exists() and p.stat().st_size > 0:
                return True
        except Exception:
            pass
    return False

# ─── Context builders ─────────────────────────────────────────────────────────

def build_resume_context(mode: str, intent: str, chain_step: str, summary: str) -> str:
    lines = ["[KF Session Resume]"]
    if mode:
        lines.append(f"Mode: {mode}")
    if intent:
        lines.append(f"Original intent: {intent}")
    if chain_step and chain_step != "none":
        lines.append(f"Chain: {chain_step}")

    if summary:
        lines.append("")
        lines.append("Session summary:")
        preview = summary[:SESSION_SUMMARY_PREVIEW_CHARS]
        if len(summary) > SESSION_SUMMARY_PREVIEW_CHARS:
            preview += "..."
        lines.append(preview)

    lines.append("")
    lines.append("State files available: .kf/state/")
    return "\n".join(lines)


def build_postcompact_context(mode: str, intent: str) -> str:
    lines = ["[KF Post-Compaction Resume]"]
    if mode:
        lines.append(f"Mode: {mode}")
    if intent:
        lines.append(f"Original intent: {intent}")
    return "\n".join(lines)

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    try:
        raw_input = sys.stdin.read()
        hook_input = json.loads(raw_input) if raw_input.strip() else {}
    except Exception as e:
        sys.stderr.write(f"[kf-session-start] Could not parse hook input: {e}\n")
        sys.exit(0)

    state_dir = get_state_dir()

    # Fresh start — no state directory, nothing to inject
    if not state_dir.exists():
        sys.exit(0)

    # No meaningful state files — fresh session
    if not has_any_state(state_dir):
        sys.exit(0)

    # Read transcript for session type detection
    transcript = hook_input.get("transcript", [])
    if not isinstance(transcript, list):
        transcript = []

    transcript_len = len(transcript)

    # Read state
    mode = read_state_file(state_dir, "active_mode")
    intent = read_state_file(state_dir, "original_intent")
    chain_step = read_state_file(state_dir, "chain_step")
    summary = read_state_file(state_dir, "session_summary.md")

    # If neither mode nor intent survived, nothing useful to inject
    if not mode and not intent:
        sys.exit(0)

    # Determine session type and build context
    if transcript_len > RESUME_TRANSCRIPT_THRESHOLD:
        # Resume: inject full context
        context = build_resume_context(mode, intent, chain_step, summary)
    else:
        # Post-compact or empty transcript with state: inject minimal context
        context = build_postcompact_context(mode, intent)

    # If context collapsed to just the header line, don't inject
    if not context.strip() or context.strip() in ("[KF Session Resume]", "[KF Post-Compaction Resume]"):
        sys.exit(0)

    output = {"additionalContext": context}
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[kf-session-start] Unhandled exception: {e}\n")
        sys.exit(0)
