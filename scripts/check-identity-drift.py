#!/usr/bin/env python3
"""
check-identity-drift.py — Flag version strings embedded in modules/ that drift
from the module's own canonical `version:` field.

Detects two embedded patterns:
  - title:        "  title: KnowledgeForge X.Y.Z ..."
  - body identity: "You are the KnowledgeForge X.Y.Z ..."

…and compares each occurrence against the file's first
`version: X.Y.Z` line.

Why: identity strings in module bodies (e.g. M00's
"You are the KnowledgeForge 7.5.0 orchestrator") have silently desynced
from the module's own version field across multiple changelog bumps.
See knowledgeforge-core-3kk and core@c341518.

Exit codes:
  0 — every embedded version matches the canonical `version:` field
      (or the file has no canonical/embedded versions to check).
  1 — drift detected; report written to stdout, summary to stderr.

Usage:
  python3 scripts/check-identity-drift.py
  python3 scripts/check-identity-drift.py modules/00_orchestrator.md [...]
"""
import re
import sys
from pathlib import Path

VERSION_RE = re.compile(r"^\s*version:\s*(\d+\.\d+\.\d+)\s*$", re.MULTILINE)
TITLE_RE = re.compile(
    r"^\s*title:\s*KnowledgeForge\s+(\d+\.\d+\.\d+)\b", re.MULTILINE
)
IDENTITY_RE = re.compile(r"You are the KnowledgeForge\s+(\d+\.\d+\.\d+)\b")


def find_drift(path: Path):
    text = path.read_text(encoding="utf-8")
    vm = VERSION_RE.search(text)
    if not vm:
        return None, []
    canonical = vm.group(1)

    findings = []
    for label, regex in (("title", TITLE_RE), ("identity", IDENTITY_RE)):
        for m in regex.finditer(text):
            embedded = m.group(1)
            if embedded != canonical:
                line = text.count("\n", 0, m.start()) + 1
                findings.append((label, line, embedded))
    return canonical, findings


def main(argv):
    if len(argv) > 1:
        files = [Path(p) for p in argv[1:]]
    else:
        repo_root = Path(__file__).resolve().parent.parent
        files = sorted((repo_root / "modules").glob("[0-9][0-9]_*.md"))

    any_drift = False
    for f in files:
        if not f.exists():
            sys.stderr.write(f"SKIP {f}: not found\n")
            continue
        canonical, findings = find_drift(f)
        for label, line, embedded in findings:
            any_drift = True
            print(
                f"DRIFT  {f}:{line}  {label}={embedded}  "
                f"expected={canonical}"
            )

    if any_drift:
        sys.stderr.write(
            "\nIdentity-string drift detected. Bump each embedded version to "
            "match the canonical `version:` field, then re-commit.\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
