#!/usr/bin/env bash
# KnowledgeForge install — Claude Code / Windsurf / Zed / Cursor / Codex
#
# Copies the pre-compiled Claude Code variant from platforms/claude-code/.claude/
# into ~/.claude/. No compiler required.
#
# Usage:
#   bash install.sh                         # install to ~/.claude/
#   bash install.sh --codex --project PATH  # install to PATH/AGENTS.md
#   bash install.sh --codex --global        # install to ~/.codex/AGENTS.md
#   bash install.sh --dry-run                # show what would happen, no changes
#   bash install.sh --compile                # compile fresh from source (requires Python 3.9+)
#   bash install.sh --force                  # back up and replace an existing target

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
PRECOMPILED="$REPO_DIR/platforms/claude-code/.claude"
DRY_RUN=false
COMPILE_FRESH=false
INSTALL_TARGET="claude"
CODEX_SCOPE=""
CODEX_PROJECT_DIR=""
FORCE=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=true ;;
    --compile) COMPILE_FRESH=true ;;
    --force) FORCE=true ;;
    --codex) INSTALL_TARGET="codex" ;;
    --global) CODEX_SCOPE="global" ;;
    --project)
      shift
      if [ "$#" -eq 0 ]; then
        echo "Error: --project requires a directory path."
        exit 1
      fi
      CODEX_SCOPE="project"
      CODEX_PROJECT_DIR="$1"
      ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
  shift
done

if [ "$INSTALL_TARGET" = "claude" ] && [ -n "$CODEX_SCOPE" ]; then
  echo "Error: --global and --project require --codex."
  exit 1
fi

if [ "$INSTALL_TARGET" = "codex" ] && [ -z "$CODEX_SCOPE" ]; then
  echo "Error: choose --global or --project PATH when installing for Codex."
  exit 1
fi

if [ "$INSTALL_TARGET" = "codex" ]; then
  PRECOMPILED="$REPO_DIR/platforms/codex/AGENTS.md"
fi

echo "KnowledgeForge installer"
if [ "$INSTALL_TARGET" = "codex" ]; then
  if [ "$CODEX_SCOPE" = "global" ]; then
    echo "  Target: ~/.codex/AGENTS.md"
  else
    echo "  Target: $CODEX_PROJECT_DIR/AGENTS.md"
  fi
else
  echo "  Target: ~/.claude/"
fi
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
  BUILD_DIR="$(mktemp -d /tmp/kf-build.XXXXXX)"
  echo "  Compiling from source → $BUILD_DIR ..."
  if [ "$INSTALL_TARGET" = "codex" ]; then
    python3 "$REPO_DIR/compiler/kf-compile.py" --target codex --output "$BUILD_DIR"
    PRECOMPILED="$BUILD_DIR/AGENTS.md"
  else
    python3 "$REPO_DIR/compiler/kf-compile.py" --target claude-code --output "$BUILD_DIR"
    PRECOMPILED="$BUILD_DIR/.claude"
  fi
  echo
fi

# ── Validate source ───────────────────────────────────────────────────────────

if [ "$INSTALL_TARGET" = "codex" ]; then
  if [ ! -f "$PRECOMPILED" ]; then
    echo "Error: pre-compiled Codex instructions not found at platforms/codex/AGENTS.md"
    echo "       Clone the full repo, or run: bash install.sh --codex --compile --global"
    exit 1
  fi
else
  if [ ! -d "$PRECOMPILED" ]; then
    echo "Error: pre-compiled output not found at platforms/claude-code/.claude/"
    echo "       Clone the full repo, or run: bash install.sh --compile"
    exit 1
  fi
fi

# ── Dry-run ───────────────────────────────────────────────────────────────────

if $DRY_RUN; then
  if [ "$INSTALL_TARGET" = "codex" ]; then
    if [ "$CODEX_SCOPE" = "global" ]; then
      echo "[dry-run] would copy: $PRECOMPILED → ~/.codex/AGENTS.md"
    else
      echo "[dry-run] would copy: $PRECOMPILED → $CODEX_PROJECT_DIR/AGENTS.md"
    fi
  else
    echo "[dry-run] would copy: $PRECOMPILED → ~/.claude/"
    find "$PRECOMPILED" -type f | sort | while IFS= read -r f; do
      rel="${f#$PRECOMPILED/}"
      echo "  + ~/.claude/$rel"
    done
  fi
  echo
  echo "No changes made."
  exit 0
fi

# ── Install ───────────────────────────────────────────────────────────────────

if [ "$INSTALL_TARGET" = "codex" ]; then
  if [ "$CODEX_SCOPE" = "global" ]; then
    TARGET_DIR="$HOME/.codex"
  else
    TARGET_DIR="$CODEX_PROJECT_DIR"
  fi
  TARGET_FILE="$TARGET_DIR/AGENTS.md"

  if [ -e "$TARGET_FILE" ] && ! cmp -s "$PRECOMPILED" "$TARGET_FILE"; then
    if ! $FORCE; then
      echo "Error: $TARGET_FILE already exists and differs from KnowledgeForge."
      echo "       Re-run with --force to back it up and replace it."
      exit 1
    fi
    BACKUP_FILE="$TARGET_FILE.knowledgeforge-backup-$(date +%Y%m%d%H%M%S)"
    cp "$TARGET_FILE" "$BACKUP_FILE"
    echo "Backed up existing instructions to $BACKUP_FILE"
  fi

  echo "Installing to $TARGET_FILE ..."
  mkdir -p "$TARGET_DIR"
  cp "$PRECOMPILED" "$TARGET_FILE"
else
  echo "Installing to ~/.claude/ ..."
  mkdir -p ~/.claude

  if command -v rsync &>/dev/null; then
    rsync -a "$PRECOMPILED/" ~/.claude/
  else
    cp -r "$PRECOMPILED/." ~/.claude/
  fi
fi

# ── Cleanup (compile-fresh only) ──────────────────────────────────────────────

if $COMPILE_FRESH && [ -n "${BUILD_DIR:-}" ]; then
  rm -rf "$BUILD_DIR"
fi

# ── Done ──────────────────────────────────────────────────────────────────────

echo
if [ "$INSTALL_TARGET" = "codex" ]; then
  echo "Done. Start a new Codex session to load KnowledgeForge."
else
  echo "Done. Restart your editor to activate KnowledgeForge."
  echo
  echo "Optional: set GEMINI_API_KEY in your environment to enable pre-prompt"
  echo "routing classification (degrades gracefully if absent)."
  echo
  echo "Configure integrations: ~/.claude/kf-integrations.yaml"
fi
