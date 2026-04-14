#!/usr/bin/env python3
"""
sync-cp-modules.py — Sync core module files to knowledgeforge-cp by prefix number.

Matching rule: core `modules/NN_*.md` → cp `NN_*.md` (same two-digit prefix).
Core is authoritative; CP file content is replaced with core content.
CP filenames are preserved (they're referenced by Claude Projects by name).

Usage:
    python3 scripts/sync-cp-modules.py --core modules/ --cp /path/to/cp-repo/
    python3 scripts/sync-cp-modules.py --core modules/ --cp /path/to/cp-repo/ --dry-run

Exit codes:
    0 — success (with or without changes)
    1 — error (missing directories, unreadable files)
"""

import argparse
import sys
from pathlib import Path


def find_cp_target(prefix: str, cp_dir: Path) -> Path | None:
    """Find the CP file with the given two-digit prefix. Returns None if not found."""
    matches = list(cp_dir.glob(f"{prefix}_*.md"))
    if not matches:
        return None
    if len(matches) > 1:
        # Ambiguous — shouldn't happen, but log and skip
        sys.stderr.write(
            f"[sync-cp] Warning: multiple CP files match prefix {prefix}: "
            f"{[str(m) for m in matches]} — skipping\n"
        )
        return None
    return matches[0]


def sync(core_dir: Path, cp_dir: Path, dry_run: bool) -> tuple[int, int, int]:
    """
    Sync core modules to CP.

    Returns (synced, skipped, errors) counts.
    """
    synced = 0
    skipped = 0
    errors = 0

    core_modules = sorted(core_dir.glob("[0-9][0-9]_*.md"))

    if not core_modules:
        sys.stderr.write(f"[sync-cp] No modules found in {core_dir}\n")
        return 0, 0, 1

    for core_file in core_modules:
        prefix = core_file.name[:2]
        cp_target = find_cp_target(prefix, cp_dir)

        if cp_target is None:
            sys.stderr.write(
                f"[sync-cp] No CP file found for prefix {prefix} "
                f"({core_file.name}) — skipping\n"
            )
            skipped += 1
            continue

        try:
            core_content = core_file.read_text(encoding="utf-8")
            cp_content = cp_target.read_text(encoding="utf-8") if cp_target.exists() else ""

            if core_content == cp_content:
                print(f"  UNCHANGED  {core_file.name} → {cp_target.name}")
                continue

            if dry_run:
                print(f"  WOULD SYNC {core_file.name} → {cp_target.name}")
            else:
                cp_target.write_text(core_content, encoding="utf-8")
                print(f"  SYNCED     {core_file.name} → {cp_target.name}")

            synced += 1

        except OSError as e:
            sys.stderr.write(f"[sync-cp] Error syncing {core_file.name}: {e}\n")
            errors += 1

    return synced, skipped, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync core modules to knowledgeforge-cp")
    parser.add_argument("--core", required=True, help="Path to core modules/ directory")
    parser.add_argument("--cp", required=True, help="Path to knowledgeforge-cp repo root")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    core_dir = Path(args.core).resolve()
    cp_dir = Path(args.cp).resolve()

    if not core_dir.is_dir():
        sys.stderr.write(f"[sync-cp] Core directory not found: {core_dir}\n")
        return 1

    if not cp_dir.is_dir():
        sys.stderr.write(f"[sync-cp] CP directory not found: {cp_dir}\n")
        return 1

    mode = "DRY RUN — " if args.dry_run else ""
    print(f"KF Module Sync {mode}({core_dir} → {cp_dir})")
    print()

    synced, skipped, errors = sync(core_dir, cp_dir, args.dry_run)

    print()
    print(f"Done: {synced} synced, {skipped} skipped (no CP match), {errors} errors")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
