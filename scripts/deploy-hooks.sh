#!/usr/bin/env bash
# deploy-hooks.sh — Deploy KF hooks to ~/.claude/hooks/
#
# Run this after editing hooks in knowledgeforge-core/hooks/.
# All non-CP variants (knowledgeforge-cc, knowledgeforge-cw, any future CC-based
# variant) share the same deployed hook — the global ~/.claude/settings.json
# registers it once and all variants benefit automatically.
#
# Usage:
#   ./scripts/deploy-hooks.sh
#   ./scripts/deploy-hooks.sh --dry-run

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/../hooks"
DEPLOY_DIR="$HOME/.claude/hooks"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
fi

HOOKS=(
  "kf-route.py"
  "kf_module_index.txt"
  "kf-stop-validator.py"
  "kf-precompact.py"
  "kf-postcompact.py"
  "kf-edit-nudge.py"
  "kf-session-start.py"
)

echo "KF Hook Deploy"
echo "  Source:  $SOURCE_DIR"
echo "  Target:  $DEPLOY_DIR"
echo ""

mkdir -p "$DEPLOY_DIR"

any_changed=false

for hook in "${HOOKS[@]}"; do
  src="$SOURCE_DIR/$hook"
  dst="$DEPLOY_DIR/$hook"

  if [[ ! -f "$src" ]]; then
    echo "  MISSING  $hook  (not found in source, skipping)"
    continue
  fi

  if [[ -f "$dst" ]] && cmp -s "$src" "$dst"; then
    echo "  OK       $hook  (unchanged)"
  else
    if $DRY_RUN; then
      echo "  WOULD    $hook  (would copy)"
    else
      cp "$src" "$dst"
      echo "  DEPLOYED $hook"
    fi
    any_changed=true
  fi
done

echo ""

if $DRY_RUN; then
  echo "Dry run complete. Run without --dry-run to deploy."
elif $any_changed; then
  echo "Done. Restart Claude Code for hook changes to take effect."
else
  echo "Done. All hooks already up to date."
fi
