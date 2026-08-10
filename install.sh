#!/usr/bin/env bash
# KnowledgeForge install — Claude Code / Windsurf / Zed / Cursor
#
# Copies the pre-compiled Claude Code variant from platforms/claude-code/.claude/
# into ~/.claude/. No compiler required.
#
# Usage:
#   bash install.sh            # install to ~/.claude/
#   bash install.sh --dry-run  # show what would happen, no changes
#   bash install.sh --compile  # compile fresh from source (requires Python 3.9+)

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
PRECOMPILED="$REPO_DIR/platforms/claude-code/.claude"
DRY_RUN=false
COMPILE_FRESH=false

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --compile) COMPILE_FRESH=true ;;
    *) echo "Unknown argument: $arg"; exit 1 ;;
  esac
done

echo "KnowledgeForge installer"
echo "  Target: ~/.claude/"
echo

# ── Compile-fresh mode ────────────────────────────────────────────────────────

if $COMPILE_FRESH; then
  if ! command -v python3 &>/dev/null; then
    echo "Error: python3 not found. Install Python 3.9+ and try again."
    exit 1
  fi
  PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
  if (( PY_MINOR < 9 )); then
    echo "Error: Python 3.9+ required (found 3.${PY_MINOR})."
    exit 1
  fi
  BUILD_DIR="$(mktemp -d /tmp/kf-cc-build.XXXXXX)"
  echo "  Compiling from source → $BUILD_DIR ..."
  python3 "$REPO_DIR/compiler/kf-compile.py" --target claude-code --output "$BUILD_DIR"
  PRECOMPILED="$BUILD_DIR/.claude"
  echo
fi

# ── Validate source ───────────────────────────────────────────────────────────

if [ ! -d "$PRECOMPILED" ]; then
  echo "Error: pre-compiled output not found at platforms/claude-code/.claude/"
  echo "       Clone the full repo, or run: bash install.sh --compile"
  exit 1
fi

# ── Dry-run ───────────────────────────────────────────────────────────────────

if $DRY_RUN; then
  echo "[dry-run] would copy: $PRECOMPILED → ~/.claude/"
  find "$PRECOMPILED" -type f | sort | while IFS= read -r f; do
    rel="${f#$PRECOMPILED/}"
    echo "  + ~/.claude/$rel"
  done
  echo
  echo "No changes made."
  exit 0
fi

# ── Install ───────────────────────────────────────────────────────────────────

echo "Installing to ~/.claude/ ..."
mkdir -p ~/.claude

if command -v rsync &>/dev/null; then
  rsync -a "$PRECOMPILED/" ~/.claude/
else
  cp -r "$PRECOMPILED/." ~/.claude/
fi

# ── Cleanup (compile-fresh only) ──────────────────────────────────────────────

if $COMPILE_FRESH && [ -n "${BUILD_DIR:-}" ]; then
  rm -rf "$BUILD_DIR"
fi

# ── Done ──────────────────────────────────────────────────────────────────────

echo
echo "Done. Restart your editor to activate KnowledgeForge."
echo
echo "Optional: set GEMINI_API_KEY in your environment to enable pre-prompt"
echo "routing classification (degrades gracefully if absent)."
echo
echo "Configure integrations: ~/.claude/kf-integrations.yaml"
