"""Tamper detection (R4.1-R4.3). R4.4 (grader.lock) lives in registry.check_lock; R4.5 is config-on-host."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .acs import match_glob

PROTECTED = [
    "tests/**", "test/**", "**/__tests__/**", "**/*.test.*", "**/*_test.*", "**/test_*.*", "**/fixtures/**",
    "conftest.py", "pytest.ini", "jest.config.*", "vitest.config.*", ".github/workflows/**", ".claude/**", ".kf/**",
]
ADD_PROTECTED = [".claude/**", ".kf/**"]  # an Added file counts only here


def git(clone: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", "-C", str(clone), *args], capture_output=True, timeout=120)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.decode('utf-8', 'replace').strip()}")
    return r


def changed(clone: Path, base: str, head: str) -> list[tuple[str, str]]:
    out = git(clone, "diff", "--name-status", "--no-renames", "-z", f"{base}..{head}").stdout.decode("utf-8", "surrogateescape")
    parts = [p for p in out.split("\0") if p]
    return [(parts[i][0], parts[i + 1]) for i in range(0, len(parts) - 1, 2)]


def _scripts(clone: Path, rev: str, path: str) -> dict | None:
    r = git(clone, "show", f"{rev}:{path}", check=False)
    if r.returncode != 0:
        return None
    try:
        doc = json.loads(r.stdout.decode("utf-8", "replace"))
    except ValueError:
        return {"__unparseable__": r.stdout.decode("utf-8", "replace")}
    return doc.get("scripts", {}) if isinstance(doc, dict) else {}


def check(clone: Path, base: str, head: str, reg: dict) -> list[str]:
    """Return human-readable violations; empty list = clean."""
    violations: list[str] = []
    if git(clone, "merge-base", "--is-ancestor", base, head, check=False).returncode != 0:
        violations.append("history_rewrite: base_sha is not an ancestor of head_sha")
    protected = list(PROTECTED)
    if reg.get("spec_repo_path"):
        protected.append(reg["spec_repo_path"])
    allow = reg.get("allow_modify") or []
    changes = changed(clone, base, head)
    for status, path in changes:
        if any(match_glob(g, path, True) for g in allow):
            continue
        hit = any(match_glob(g, path, True) for g in (ADD_PROTECTED if status == "A" else protected))
        if hit:
            violations.append(f"protected_path: {path} ({status})")
    pkg_paths = {"package.json"} | {p for _, p in changes if p.rsplit("/", 1)[-1] == "package.json"}
    for p in sorted(pkg_paths):
        if any(match_glob(g, p, True) for g in allow):
            continue
        if _scripts(clone, base, p) != _scripts(clone, head, p):
            violations.append(f"test_harness: {p} scripts object differs between base and head")
    return violations
