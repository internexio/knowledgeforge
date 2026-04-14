#!/usr/bin/env python3
"""
kf-precompact.py — KnowledgeForge PreCompact Hook
Hook type: PreCompact
Purpose: Before context compaction, extract and persist session state so it
         survives the compaction. Writes active mode, original intent,
         constraints, chain step, and a session summary to .kf/state/.
         Also backs up the full transcript to .kf/transcripts/.

         ENH-006: original_intent and current_constraints are stored VERBATIM —
         never summarized. These are the anchor that PostCompact and SessionStart
         inject back after compaction.

Graceful degradation: any failure → exit 0 (compaction must not be blocked).
Output: none (state written to files; no stdout needed for PreCompact).

Env vars: CLAUDE_PROJECT_DIR — project root (fallback: cwd)
"""

import sys
import json
import os
import re
from pathlib import Path
from datetime import datetime

# ─── State directory resolution ───────────────────────────────────────────────

def get_project_root() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd()))


def ensure_dirs(root: Path) -> tuple[Path, Path]:
    state_dir = root / ".kf" / "state"
    transcripts_dir = root / ".kf" / "transcripts"
    state_dir.mkdir(parents=True, exist_ok=True)
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    return state_dir, transcripts_dir

# ─── Transcript extraction ────────────────────────────────────────────────────

def get_message_text(entry: dict) -> str:
    """Extract plain text from a transcript entry regardless of content shape."""
    content = entry.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            p.get("text", "") for p in content
            if isinstance(p, dict) and p.get("type") == "text"
        )
    return ""


def extract_active_mode(transcript: list) -> str:
    """Find the most recent [KF-ROUTE: mode=X] string in any message."""
    pattern = re.compile(r"\[KF-ROUTE:[^\]]*mode=([a-zA-Z_-]+)", re.IGNORECASE)
    for entry in reversed(transcript):
        if not isinstance(entry, dict):
            continue
        text = get_message_text(entry)
        match = pattern.search(text)
        if match:
            return match.group(1).lower().strip()
    return ""


def extract_original_intent(transcript: list) -> str:
    """
    First substantive user message: not a [KF-ROUTE] directive, not empty,
    and longer than 20 characters. Stored verbatim per ENH-006.
    """
    for entry in transcript:
        if not isinstance(entry, dict):
            continue
        if entry.get("role") != "user":
            continue
        text = get_message_text(entry).strip()
        if len(text) <= 20:
            continue
        if text.startswith("[KF-ROUTE"):
            continue
        return text
    return ""


def extract_constraints(transcript: list) -> str:
    """
    Find user messages containing explicit constraint language.
    Returns comma-joined constraint snippets, or "none".
    """
    constraint_keywords = ["don't", "must not", "out of scope", "exclude", "constraint"]
    found = []
    for entry in transcript:
        if not isinstance(entry, dict):
            continue
        if entry.get("role") != "user":
            continue
        text = get_message_text(entry).strip()
        lower = text.lower()
        if any(kw in lower for kw in constraint_keywords):
            # Store the first 200 chars of the constraint message verbatim
            found.append(text[:200])
    return ", ".join(found) if found else "none"


def extract_chain_step(transcript: list) -> str:
    """
    Look for @mode → @mode patterns. Return the last one found, or "none".
    """
    pattern = re.compile(r"@[\w-]+\s*→\s*@[\w-]+(?:\s*\|\s*step\s*\d+/\d+)?", re.IGNORECASE)
    last_match = ""
    for entry in transcript:
        if not isinstance(entry, dict):
            continue
        text = get_message_text(entry)
        matches = pattern.findall(text)
        if matches:
            last_match = matches[-1].strip()
    return last_match if last_match else "none"

# ─── State writing ────────────────────────────────────────────────────────────

def write_state(state_dir: Path, key: str, value: str) -> None:
    try:
        (state_dir / key).write_text(value, encoding="utf-8")
    except Exception as e:
        sys.stderr.write(f"[kf-precompact] Could not write {key}: {e}\n")


def write_session_summary(state_dir: Path, mode: str, intent: str,
                           constraints: str, chain_step: str) -> None:
    summary = (
        f"# KF Session Summary\n\n"
        f"**Mode:** {mode or '(none)'}\n"
        f"**Original intent:** {intent or '(none)'}\n"
        f"**Constraints:** {constraints}\n"
        f"**Chain step:** {chain_step}\n"
        f"**Written:** {datetime.utcnow().isoformat()}Z\n"
    )
    try:
        (state_dir / "session_summary.md").write_text(summary, encoding="utf-8")
    except Exception as e:
        sys.stderr.write(f"[kf-precompact] Could not write session_summary.md: {e}\n")


def backup_transcript(transcripts_dir: Path, raw_input: str) -> None:
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    backup_path = transcripts_dir / f"{timestamp}.json"
    try:
        backup_path.write_text(raw_input, encoding="utf-8")
    except Exception as e:
        sys.stderr.write(f"[kf-precompact] Could not backup transcript: {e}\n")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    try:
        raw_input = sys.stdin.read()
        hook_input = json.loads(raw_input)
    except Exception as e:
        sys.stderr.write(f"[kf-precompact] Could not parse hook input: {e}\n")
        sys.exit(0)

    transcript = hook_input.get("transcript", [])
    if not isinstance(transcript, list):
        transcript = []

    # Ensure state directories exist
    try:
        root = get_project_root()
        state_dir, transcripts_dir = ensure_dirs(root)
    except Exception as e:
        sys.stderr.write(f"[kf-precompact] Could not create state dirs: {e}\n")
        sys.exit(0)

    # Extract session state
    mode = extract_active_mode(transcript)
    intent = extract_original_intent(transcript)
    constraints = extract_constraints(transcript)
    chain_step = extract_chain_step(transcript)

    # Write state files
    write_state(state_dir, "active_mode", mode)
    write_state(state_dir, "original_intent", intent)
    write_state(state_dir, "current_constraints", constraints)
    write_state(state_dir, "chain_step", chain_step)
    write_session_summary(state_dir, mode, intent, constraints, chain_step)

    # Backup full transcript
    backup_transcript(transcripts_dir, raw_input)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[kf-precompact] Unhandled exception: {e}\n")
        sys.exit(0)
