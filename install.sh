#!/usr/bin/env bash
# KnowledgeForge install — Claude Code / Cursor / Windsurf / Zed
#
# Usage:
#   bash install.sh            # compile + install to ~/.claude/
#   bash install.sh --dry-run  # show what would happen, no changes
#
# Requires: Python 3.9+, bash

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$(mktemp -d /tmp/kf-cc-build.XXXXXX)"
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    *) echo "Unknown argument: $arg"; exit 1 ;;
  esac
done

# ── Prerequisites ─────────────────────────────────────────────────────────────

if ! command -v python3 &>/dev/null; then
  echo "Error: python3 not found. Install Python 3.9+ and try again."
  exit 1
fi

PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
if (( PY_MINOR < 9 )); then
  echo "Error: Python 3.9+ required (found 3.${PY_MINOR})."
  exit 1
fi

# ── Step 1: Compile ───────────────────────────────────────────────────────────

echo "KnowledgeForge installer"
echo "  Source:  $REPO_DIR"
echo "  Build:   $BUILD_DIR"
echo "  Target:  ~/.claude/"
echo

if $DRY_RUN; then
  echo "[dry-run] would compile: python3 compiler/kf-compile.py --target claude-code --output $BUILD_DIR"
  echo "[dry-run] would run: $BUILD_DIR/install.sh"
  echo
  echo "No changes made."
  exit 0
fi

echo "Step 1/2 — Compiling Claude Code variant..."
python3 "$REPO_DIR/compiler/kf-compile.py" --target claude-code --output "$BUILD_DIR"
echo

# ── Step 2: Install ───────────────────────────────────────────────────────────

echo "Step 2/2 — Installing to ~/.claude/ ..."
bash "$BUILD_DIR/install.sh"

# ── Cleanup ───────────────────────────────────────────────────────────────────

rm -rf "$BUILD_DIR"

echo
echo "Done. Restart your editor to activate KnowledgeForge."
echo
echo "Optional: set GEMINI_API_KEY in your environment to enable pre-prompt"
echo "routing classification (degrades gracefully if absent)."
echo
echo "Configure integrations: ~/.claude/kf-integrations.yaml"
