#!/usr/bin/env bash
# install-git-hooks.sh — Copy KF git hooks into .git/hooks/.
#
# Hooks tracked in scripts/git-hooks/ are not auto-installed by git clone.
# Run this once per fresh clone. Re-run when a hook in scripts/git-hooks/ changes.
#
# Usage:
#   ./scripts/install-git-hooks.sh
#   ./scripts/install-git-hooks.sh --force   # overwrite existing differing hook

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$REPO_ROOT/scripts/git-hooks"
DST_DIR="$REPO_ROOT/.git/hooks"

FORCE=false
if [[ "${1:-}" == "--force" ]]; then
  FORCE=true
fi

mkdir -p "$DST_DIR"

for src in "$SRC_DIR"/*; do
  name=$(basename "$src")
  dst="$DST_DIR/$name"

  if [[ -e "$dst" ]] && ! cmp -s "$src" "$dst"; then
    if $FORCE; then
      cp "$src" "$dst"
      chmod +x "$dst"
      echo "OVERWROTE $name"
    else
      echo "SKIP      $name (exists with different content; re-run with --force to overwrite)"
    fi
  else
    cp "$src" "$dst"
    chmod +x "$dst"
    echo "INSTALLED $name"
  fi
done
