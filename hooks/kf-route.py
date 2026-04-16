#!/usr/bin/env python3
"""
kf-route.py — KnowledgeForge UserPromptSubmit Hook
Hook type: UserPromptSubmit
Purpose: Classify the user prompt via Gemini Flash Lite API and inject a
         [KF-ROUTE] directive telling Claude which mode + cross-cutting
         modules to load. Replicates Claude Projects semantic retrieval at
         ~300ms overhead on the free tier.

Graceful degradation: any failure → exit 0 (no directive, Claude handles raw).
The hook is additive — failure is silent and the system works like current CC.

Dependencies: stdlib only (urllib.request, json, os, sys, pathlib)
Env:          GEMINI_API_KEY  — required
              KF_ROUTE_MODEL  — override model (default: gemini-2.0-flash-lite)
              KF_ROUTE_TIMEOUT — HTTP timeout in seconds (default: 10)
"""

import sys
import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

GEMINI_API_KEY  = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL    = os.environ.get("KF_ROUTE_MODEL", "gemini-2.5-flash-lite")
GEMINI_TIMEOUT  = int(os.environ.get("KF_ROUTE_TIMEOUT", "10"))

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
)

# Module number → filename mapping for doc hints
MODULE_MAP = {
    "M12": "12_calibration_layer.md",
    "M13": "13_decision_classification.md",
    "M14": "14_metacognitive_monitor.md",
    "M15": "15_grounding_scores.md",
    "M16": "16_operational_bounds.md",
    "M17": "17_temporal_knowledge.md",
    "M18": "18_salience_allocation.md",
    "M19": "19_memory_architecture.md",
    "M20": "20_permission_model.md",
    "M21": "21_knowledge_accretion.md",
    "M22": "22_semantic_wiki_search.md",
    "M23": "23_taxonomy_enforcement.md",
    "M24": "24_verbatim_history_mining.md",
}

# Path to the compact module index (relative to this script)
INDEX_PATH = Path(__file__).parent / "kf_module_index.txt"

# Usage log — JSONL, one entry per routed request
LOG_PATH = Path.home() / ".claude" / "kf-usage.jsonl"

# ─── Load module index ────────────────────────────────────────────────────────

def load_index() -> str | None:
    try:
        return INDEX_PATH.read_text(encoding="utf-8")
    except Exception as e:
        sys.stderr.write(f"[kf-route] Could not load module index: {e}\n")
        return None

# ─── Session context extraction ───────────────────────────────────────────────

def extract_session_id(hook_input: dict) -> str:
    """Extract session ID from hook input."""
    for field in ("session_id", "sessionId", "session"):
        val = hook_input.get(field, "")
        if val:
            return str(val)
    return ""


def extract_model(hook_input: dict) -> str:
    """Extract active Claude model from the hook input transcript.

    Claude Code stores the model name on each assistant message in the
    transcript.  We scan from the end to find the most recent one.
    Falls back to 'unknown' if the transcript is absent or empty.
    """
    transcript = hook_input.get("transcript", [])
    if not isinstance(transcript, list):
        return "unknown"
    for entry in reversed(transcript):
        try:
            msg = entry.get("message", {})
            if isinstance(msg, dict):
                model = msg.get("model", "")
                if model:
                    return model
        except Exception:
            pass
    return "unknown"


def log_decision(session_id: str, model: str, mode: str, decision_type: str,
                 cross_cutting: list, prompt_len: int, routed: bool) -> None:
    """Append one routing decision to the usage log.  Never raises."""
    try:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry = {
            "ts":            ts,
            "session_id":    session_id,
            "model":         model,
            "mode":          mode,
            "decision_type": decision_type,
            "cross_cutting": [str(m) for m in cross_cutting],
            "prompt_len":    prompt_len,
            "routed":        routed,
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        sys.stderr.write(f"[kf-route] Log write failed: {e}\n")


# ─── Call Gemini ──────────────────────────────────────────────────────────────

def classify(prompt: str, index: str) -> dict:
    """Call Gemini Flash Lite with module index + user prompt. Returns parsed JSON."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    routing_input = f"{index}\"{prompt}\""

    body = json.dumps({
        "contents": [
            {"parts": [{"text": routing_input}]}
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0,
            "maxOutputTokens": 200,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        GEMINI_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=GEMINI_TIMEOUT) as resp:
        raw = resp.read().decode("utf-8")

    data = json.loads(raw)

    # Extract the text from Gemini's response envelope
    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    return json.loads(text)

# ─── Build directive ──────────────────────────────────────────────────────────

def build_directive(routing: dict) -> str | None:
    """Format the [KF-ROUTE: ...] directive. Returns None if no routing needed."""
    mode          = routing.get("mode") or ""
    decision_type = routing.get("decision_type", "")
    cross_cutting = routing.get("cross_cutting") or []
    notes         = routing.get("notes", "")

    # Reckonings and null-mode: no directive
    if not mode or mode.lower() in ("null", "none") or decision_type == "reckoning":
        return None

    parts = []
    if mode:
        parts.append(f"mode={mode}")
    if decision_type:
        parts.append(f"decision={decision_type}")
    if cross_cutting:
        modules = ", ".join(str(m) for m in cross_cutting)
        parts.append(f"load=[{modules}]")
    if notes:
        parts.append(notes)

    return " | ".join(parts) if parts else None

# ─── Build skill + doc hints ──────────────────────────────────────────────────

def build_hints(routing: dict) -> str:
    """Build skill-load and doc-reference lines injected below the directive."""
    mode          = (routing.get("mode") or "").lower()
    cross_cutting = routing.get("cross_cutting") or []
    lines         = []

    if mode and mode not in ("null", "none"):
        lines.append(f"Load skill: .claude/skills/kf/{mode}.md")

    doc_files = [
        f".claude/docs/knowledgeforge/{MODULE_MAP[str(m)]}"
        for m in cross_cutting
        if str(m) in MODULE_MAP
    ]
    if doc_files:
        lines.append("Reference docs: " + ", ".join(doc_files))

    return "\n".join(lines)

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    # Read hook stdin
    try:
        raw_input = sys.stdin.read()
        hook_input = json.loads(raw_input)
    except Exception as e:
        sys.stderr.write(f"[kf-route] Could not parse hook input: {e}\n")
        sys.exit(0)

    user_prompt = hook_input.get("prompt", "").strip()
    if not user_prompt or len(user_prompt) < 8:
        sys.exit(0)

    # Extract session context for logging (before any early-exit)
    session_id = extract_session_id(hook_input)
    model      = extract_model(hook_input)
    prompt_len = len(user_prompt)

    # Load module index
    index = load_index()
    if not index:
        log_decision(session_id, model, "error", "", [], prompt_len, False)
        sys.exit(0)

    # Classify
    try:
        routing = classify(user_prompt, index)
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"[kf-route] Gemini HTTP {e.code}: {e.reason} — passing through\n")
        log_decision(session_id, model, "gemini_error", "", [], prompt_len, False)
        sys.exit(0)
    except TimeoutError:
        sys.stderr.write(f"[kf-route] Gemini timeout ({GEMINI_TIMEOUT}s) — passing through\n")
        log_decision(session_id, model, "gemini_timeout", "", [], prompt_len, False)
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"[kf-route] Classification failed: {e}\n")
        log_decision(session_id, model, "gemini_error", "", [], prompt_len, False)
        sys.exit(0)

    # Extract routing fields
    raw_mode      = routing.get("mode") or ""
    decision_type = routing.get("decision_type", "")
    cross_cutting = routing.get("cross_cutting") or []

    # Determine whether KF activates a mode or passes through
    is_direct = (
        not raw_mode
        or raw_mode.lower() in ("null", "none")
        or decision_type == "reckoning"
    )
    mode_label = "direct" if is_direct else raw_mode.lower()

    # Log every decision — raw and routed alike
    log_decision(session_id, model, mode_label, decision_type,
                 cross_cutting, prompt_len, not is_direct)

    # No mode to activate — pass through without directive
    if is_direct:
        sys.exit(0)

    # Build directive
    directive = build_directive(routing)
    if not directive:
        sys.exit(0)

    # Build hints
    hints = build_hints(routing)

    # Assemble augmented prompt
    header_lines = [f"[KF-ROUTE: {directive}]"]
    if hints:
        header_lines.append(hints)
    header_lines.append("---")

    augmented_prompt = "\n".join(header_lines) + "\n" + user_prompt

    # Emit hook output
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "updatedPrompt": augmented_prompt,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
