#!/usr/bin/env python3
"""
kf-stop-validator.py — KnowledgeForge Stop Hook
Hook type: Stop
Purpose: Run mode-specific quality checklists against the last assistant message.
         If the active mode's checklist fails, block the stop and surface what's
         missing. Transforms quality gates from advisory to mandatory.

Graceful degradation: ANY exception → exit 0 (never block Claude on hook error).
                      stop_hook_active=true → exit 0 immediately (loop guard).
                      No active mode → exit 0.

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

# ─── Mode checklists ──────────────────────────────────────────────────────────

CHECKLISTS: dict = {
    "builder": {
        "checks": [
            ("Has sections (##)", lambda t: t.count("## ") >= 2),
            ("Has deliverables or acceptance criteria", lambda t: any(
                w in t.lower() for w in ["deliverable", "acceptance", "validation", "output"]
            )),
        ],
        "min_length": 200,
    },
    "critic": {
        "checks": [
            ("Has findings", lambda t: any(
                w in t.lower() for w in ["finding", "issue", "gap", "missing", "severity", "recommendation"]
            )),
            ("Has severity or priority", lambda t: any(
                w in t.lower() for w in ["high", "medium", "low", "critical", "severity", "priority"]
            )),
        ],
        "min_length": 150,
    },
    "debugger": {
        "checks": [
            ("Has root cause or hypothesis", lambda t: any(
                w in t.lower() for w in ["root cause", "hypothesis", "cause", "because", "likely"]
            )),
            ("Has fix or next step", lambda t: any(
                w in t.lower() for w in ["fix", "solution", "recommendation", "next step", "try"]
            )),
        ],
        "min_length": 100,
    },
    "strategist": {
        "checks": [
            ("Has trade-offs", lambda t: any(
                w in t.lower() for w in ["trade-off", "tradeoff", "pro", "con", "advantage", "disadvantage", "vs", "versus"]
            )),
            ("Has recommendation", lambda t: any(
                w in t.lower() for w in ["recommend", "suggest", "should", "better", "preferred"]
            )),
        ],
        "min_length": 150,
    },
    "expert": {
        "checks": [
            ("Has adversarial depth or second-order", lambda t: any(
                w in t.lower() for w in ["compound", "second-order", "cascade", "blast radius", "adversarial", "failure mode"]
            )),
        ],
        "min_length": 200,
    },
    "synthesizer": {
        "checks": [
            ("Has patterns", lambda t: any(
                w in t.lower() for w in ["pattern", "theme", "common", "across", "shared"]
            )),
            ("Has anti-patterns or boundaries", lambda t: any(
                w in t.lower() for w in ["anti-pattern", "antipattern", "boundary", "limit", "not applicable", "avoid"]
            )),
        ],
        "min_length": 150,
    },
    "coordinator": {
        "checks": [
            ("Has dependency or workflow", lambda t: any(
                w in t.lower() for w in ["dependency", "depends", "workflow", "parallel", "sequential", "handoff"]
            )),
        ],
        "min_length": 100,
    },
    # navigator, calibrator: no checklist — guidance modes, not artifact producers
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_last_assistant_text(transcript: list) -> str:
    for entry in reversed(transcript):
        if isinstance(entry, dict) and entry.get("role") == "assistant":
            content = entry.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return " ".join(
                    p.get("text", "") for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                )
    return ""


def read_active_mode(state_dir: Path) -> str:
    try:
        mode_file = state_dir / "active_mode"
        if not mode_file.exists():
            return ""
        return mode_file.read_text(encoding="utf-8").strip().lower()
    except Exception as e:
        sys.stderr.write(f"[kf-stop-validator] Could not read active_mode: {e}\n")
        return ""


def run_checklist(mode: str, text: str) -> list[str]:
    """Return list of failed check names. Empty list = all passed."""
    spec = CHECKLISTS.get(mode)
    if not spec:
        return []  # No checklist for this mode (navigator, calibrator, unknown)

    failures = []

    min_len = spec.get("min_length", 0)
    if len(text) < min_len:
        failures.append(f"Response too short (need {min_len} chars, got {len(text)})")

    for label, check_fn in spec.get("checks", []):
        try:
            if not check_fn(text):
                failures.append(label)
        except Exception as e:
            sys.stderr.write(f"[kf-stop-validator] Check '{label}' error: {e}\n")
            # Skip this check on error — don't block

    return failures

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    try:
        raw_input = sys.stdin.read()
        hook_input = json.loads(raw_input)
    except Exception as e:
        sys.stderr.write(f"[kf-stop-validator] Could not parse hook input: {e}\n")
        sys.exit(0)

    # Mandatory loop guard — if stop hook is already active, exit immediately
    if hook_input.get("stop_hook_active", False):
        sys.exit(0)

    # Read active mode
    state_dir = get_state_dir()
    mode = read_active_mode(state_dir)
    if not mode:
        sys.exit(0)  # No mode active, nothing to validate

    # Get last assistant message
    transcript = hook_input.get("transcript", [])
    if not isinstance(transcript, list):
        sys.exit(0)

    last_text = get_last_assistant_text(transcript)
    if not last_text:
        sys.exit(0)

    # Run checklist
    failures = run_checklist(mode, last_text)
    if not failures:
        sys.exit(0)  # All checks passed

    # Block with specific failure list
    missing = ", ".join(failures)
    output = {
        "decision": "block",
        "reason": f"KF Stop Gate [{mode}]: Missing {missing}. Complete these before finishing.",
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[kf-stop-validator] Unhandled exception: {e}\n")
        sys.exit(0)
