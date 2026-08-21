#!/usr/bin/env python3
"""
kf-loop.py — KnowledgeForge Loop Enforcement
Hook type: UserPromptSubmit  (when called with no arguments)
CLI mode:  enable / pause / disable / status / list  (when called with arguments)

Purpose:
  Behavioral loops that decay within long sessions get re-injected on every
  prompt turn, so context growth can't dilute them. The registry persists
  across sessions.

Registry: ~/.claude/kf/loops/registry.yaml
  Managed by CLI subcommands; read by hook on every UserPromptSubmit.

Graceful degradation: any failure in hook mode → exit 0 (pass through unmodified).

Usage (CLI):
  python3 kf-loop.py enable <name>
  python3 kf-loop.py pause <name>
  python3 kf-loop.py disable <name>
  python3 kf-loop.py status
  python3 kf-loop.py list
"""

import sys
import json
import os
from pathlib import Path
from datetime import date

# ─── Registry ─────────────────────────────────────────────────────────────────

REGISTRY_PATH = Path.home() / ".claude" / "kf" / "loops" / "registry.yaml"

# ─── Built-in loop library ────────────────────────────────────────────────────

BUILT_IN_LOOPS = {
    "de-ai": {
        "description": "Strip AI fingerprints from all outputs",
        "rules": (
            "DE-AI LOOP ACTIVE — apply to every output this session:\n"
            "- No banned vocabulary: leverage, utilize, robust, seamless, holistic, "
            "transformative, comprehensive, cutting-edge, innovative, deep dive, "
            "paradigm, ecosystem, synergy, landscape, revolutionize, empower, harness\n"
            "- No sycophantic openers: Great question, Absolutely, Certainly, Of course\n"
            "- No summary-restatement closers: In conclusion, In summary, To summarize, In essence\n"
            "- Vary sentence rhythm — mix short punches (5–8 words) with longer "
            "explanatory sentences (20–30 words). Uniform rhythm is an AI fingerprint.\n"
            "- No em dashes for technical-builder audiences — convert to periods, "
            "colons, or parentheses\n"
            "- Cut every sentence that restates a point already made\n"
            "- Every claim needs a source, number, or timeline — or cut it\n"
            "- No hollow intensifiers: genuinely, truly, really, quite, essentially, "
            "fundamentally, incredibly"
        ),
    },
    "decision-tag": {
        "description": "Tag every evaluative+ output with decision type and confidence",
        "rules": (
            "DECISION-TAG LOOP ACTIVE — on every evaluative+ output:\n"
            "- Open with the decision type tag: [Reckoning] [Evaluative] [Predictive] [Novel]\n"
            "- State confidence explicitly when < 0.9 (e.g., 'Confidence: 0.7 — limited data')\n"
            "- For Novel judgments, flag: 'This is a novel judgment — warrants human review'\n"
            "- For Reckonings: answer directly, no tag needed, < 50 tokens"
        ),
    },
    "accretion-check": {
        "description": "Flag evaluative+ outputs as KB candidates when novel and reusable",
        "rules": (
            "ACCRETION-CHECK LOOP ACTIVE — after every evaluative+ output:\n"
            "- Ask: is this finding novel + would it benefit a future query?\n"
            "- If yes: append 'ACCRETION_CANDIDATE: [one-line summary of what to file]'\n"
            "- If no: continue normally\n"
            "- Do not flag reckonings or routine outputs"
        ),
    },
}

# ─── YAML helpers (stdlib only — no PyYAML dependency) ───────────────────────

def load_registry() -> dict:
    """Load registry from disk. Returns empty structure if missing or corrupt."""
    if not REGISTRY_PATH.exists():
        return {"loops": {}}
    try:
        text = REGISTRY_PATH.read_text(encoding="utf-8").strip()
        if not text:
            return {"loops": {}}
        return _parse_registry_yaml(text)
    except Exception as e:
        sys.stderr.write(f"[kf-loop] Could not load registry: {e}\n")
        return {"loops": {}}


def save_registry(registry: dict) -> None:
    """Serialize and write registry to disk."""
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = _serialize_registry_yaml(registry)
    REGISTRY_PATH.write_text(text, encoding="utf-8")


def _parse_registry_yaml(text: str) -> dict:
    """
    Minimal YAML parser for the registry format.
    Only handles the specific structure we write — not general YAML.
    """
    registry = {"loops": {}}
    current_loop = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "loops:":
            continue
        # Loop name (2-space indent key ending in colon)
        if line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":"):
            current_loop = stripped[:-1]
            registry["loops"][current_loop] = {}
            continue
        # Loop field (4-space indent)
        if line.startswith("    ") and current_loop and ":" in stripped:
            key, _, val = stripped.partition(":")
            val = val.strip().strip('"')
            registry["loops"][current_loop][key.strip()] = val
    return registry


def _serialize_registry_yaml(registry: dict) -> str:
    """Serialize registry dict to YAML string."""
    lines = ["# KF Loop Registry — managed by kf-loop.py", "loops:"]
    loops = registry.get("loops", {})
    if not loops:
        lines.append("  {}")
    else:
        for name, config in sorted(loops.items()):
            lines.append(f"  {name}:")
            status = config.get("status", "active")
            enabled_at = config.get("enabled_at", str(date.today()))
            custom = config.get("custom_rules", "")
            lines.append(f'    status: "{status}"')
            lines.append(f'    enabled_at: "{enabled_at}"')
            if custom:
                lines.append(f'    custom_rules: "{custom}"')
            else:
                lines.append(f"    custom_rules: \"\"")
    return "\n".join(lines) + "\n"

# ─── Hook mode ────────────────────────────────────────────────────────────────

def hook_mode() -> None:
    """
    Called as UserPromptSubmit hook. Read registry, inject active loop rules
    into the user prompt.
    """
    try:
        raw = sys.stdin.read()
        hook_input = json.loads(raw) if raw.strip() else {}
    except Exception as e:
        sys.stderr.write(f"[kf-loop] Could not parse hook input: {e}\n")
        sys.exit(0)

    registry = load_registry()
    active_loops = [
        name for name, cfg in registry.get("loops", {}).items()
        if cfg.get("status") == "active"
    ]

    if not active_loops:
        sys.exit(0)

    # Build injection block
    block_lines = ["[KF-LOOPS ACTIVE]"]
    for name in sorted(active_loops):
        cfg = registry["loops"][name]
        custom_rules = cfg.get("custom_rules", "").strip()
        rules = custom_rules if custom_rules else BUILT_IN_LOOPS.get(name, {}).get("rules", "")
        if rules:
            block_lines.append(f"\n# {name}")
            block_lines.append(rules)

    injection = "\n".join(block_lines)

    # Append to user prompt
    original_prompt = hook_input.get("userPrompt", "")
    augmented_prompt = f"{original_prompt}\n\n{injection}" if original_prompt else injection

    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "updatedPrompt": augmented_prompt,
        }
    }
    print(json.dumps(output))
    sys.exit(0)

# ─── CLI mode ─────────────────────────────────────────────────────────────────

def cli_enable(name: str) -> None:
    if name not in BUILT_IN_LOOPS:
        known = ", ".join(sorted(BUILT_IN_LOOPS.keys()))
        print(f"Unknown loop '{name}'. Built-in loops: {known}")
        print("To add a custom loop, edit the registry directly at:")
        print(f"  {REGISTRY_PATH}")
        sys.exit(1)

    registry = load_registry()
    loops = registry.setdefault("loops", {})
    existing = loops.get(name, {})
    loops[name] = {
        "status": "active",
        "enabled_at": existing.get("enabled_at", str(date.today())),
        "custom_rules": existing.get("custom_rules", ""),
    }
    save_registry(registry)
    desc = BUILT_IN_LOOPS[name]["description"]
    print(f"Loop enabled: {name}")
    print(f"  {desc}")
    print(f"  Rules inject on every prompt turn until paused or disabled.")


def cli_pause(name: str) -> None:
    registry = load_registry()
    loops = registry.get("loops", {})
    if name not in loops:
        print(f"Loop '{name}' is not in the registry. Enable it first.")
        sys.exit(1)
    loops[name]["status"] = "paused"
    save_registry(registry)
    print(f"Loop paused: {name}  (use 'enable' to resume)")


def cli_disable(name: str) -> None:
    registry = load_registry()
    loops = registry.get("loops", {})
    if name not in loops:
        print(f"Loop '{name}' is not in the registry.")
        sys.exit(0)
    del loops[name]
    save_registry(registry)
    print(f"Loop removed: {name}")


def cli_status() -> None:
    registry = load_registry()
    loops = registry.get("loops", {})
    if not loops:
        print("No loops registered. Use 'enable <name>' to add one.")
        return
    print("Active loops:")
    active = [(n, c) for n, c in loops.items() if c.get("status") == "active"]
    paused = [(n, c) for n, c in loops.items() if c.get("status") == "paused"]
    for name, cfg in sorted(active):
        desc = BUILT_IN_LOOPS.get(name, {}).get("description", "custom")
        since = cfg.get("enabled_at", "?")
        print(f"  [on]     {name} — {desc}  (since {since})")
    for name, cfg in sorted(paused):
        desc = BUILT_IN_LOOPS.get(name, {}).get("description", "custom")
        print(f"  [paused] {name} — {desc}")
    if not active and not paused:
        print("  (none)")


def cli_list() -> None:
    registry = load_registry()
    registered = registry.get("loops", {})
    print("Built-in loops:")
    for name, meta in sorted(BUILT_IN_LOOPS.items()):
        status = registered.get(name, {}).get("status", "off")
        tag = f"[{status}]" if name in registered else "[off]"
        print(f"  {tag:<10} {name} — {meta['description']}")


# ─── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]

    # No arguments → hook mode
    if not args:
        hook_mode()
        return

    subcommand = args[0].lower()

    if subcommand == "enable":
        if len(args) < 2:
            print("Usage: kf-loop.py enable <name>")
            sys.exit(1)
        cli_enable(args[1])

    elif subcommand == "pause":
        if len(args) < 2:
            print("Usage: kf-loop.py pause <name>")
            sys.exit(1)
        cli_pause(args[1])

    elif subcommand == "disable":
        if len(args) < 2:
            print("Usage: kf-loop.py disable <name>")
            sys.exit(1)
        cli_disable(args[1])

    elif subcommand in ("status", "st"):
        cli_status()

    elif subcommand in ("list", "ls"):
        cli_list()

    else:
        print(f"Unknown subcommand '{subcommand}'.")
        print("Usage: kf-loop.py [enable|pause|disable|status|list] [name]")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # In hook mode, never crash loudly
        if not sys.argv[1:]:
            sys.stderr.write(f"[kf-loop] Unhandled exception: {e}\n")
            sys.exit(0)
        else:
            raise
