#!/usr/bin/env python3
"""
kf-bead-nudge.py — remind to close the driving bead when module changes are staged
Hook type: git pre-commit (called by scripts/git-hooks/pre-commit)
Graceful degradation: exits 0 on every path. This is a nudge, never a gate.

Why: beads core-acu and core-xaq were fully implemented but never closed; the gap surfaced only when a later
session picked them up. Module commits that leave an in-progress bead behind are the pattern.

Behavior:
  staged modules/*.md changes AND at least one in-progress bead -> print a reminder to stderr
  anything else (no module changes, no bd, no in-progress bead, bd error or slow) -> silent
"""
import os
import re
import subprocess
import sys

BD_TIMEOUT_S = float(os.environ.get("KF_BEAD_NUDGE_TIMEOUT", "8"))  # a hung bd (lock contention) must not stall a commit
MODULE_RE = re.compile(r"^modules/[0-9]+_.*\.md$")
# bd list rows look like: "◐ knowledgeforge-core-j2c P2 Title"
ROW_RE = re.compile(r"^\s*\S\s+([A-Za-z0-9][A-Za-z0-9._-]*-[A-Za-z0-9.]+)\s+P\d\b")
MAX_SHOWN = 5


def staged_module_files() -> list[str]:
    r = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True, text=True, timeout=10,
    )
    return [p for p in r.stdout.splitlines() if MODULE_RE.match(p)]


def in_progress_beads() -> list[str]:
    # stdout only: bd prints permission and role warnings to stderr and they must not become "beads".
    r = subprocess.run(
        ["bd", "list", "--status=in_progress"],
        capture_output=True, text=True, timeout=BD_TIMEOUT_S, stdin=subprocess.DEVNULL,
    )
    if r.returncode != 0:
        return []
    return [m.group(1) for line in r.stdout.splitlines() if (m := ROW_RE.match(line))]


def message(ids: list[str]) -> str:
    shown = ids[:MAX_SHOWN]
    more = f" (+{len(ids) - MAX_SHOWN} more)" if len(ids) > MAX_SHOWN else ""
    cmds = "; ".join(f"bd close {i}" for i in shown)
    return f"[kf] Staged module changes — did you close the driving bead? Run: {cmds}{more}"


def main() -> int:
    try:
        if not staged_module_files():
            return 0
        ids = in_progress_beads()
        if ids:
            sys.stderr.write(message(ids) + "\n")
    except Exception as e:  # noqa: BLE001 - nudge only: never block a commit
        sys.stderr.write(f"[kf-bead-nudge] skipped: {e}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
