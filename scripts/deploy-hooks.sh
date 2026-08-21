#!/usr/bin/env bash
# deploy-hooks.sh — Deploy KF hooks and commands locally or to a remote machine
#
# Run this after editing hooks in knowledgeforge-core/hooks/ or commands/.
# All non-CP variants share the same deployed hooks — global ~/.claude/settings.json
# registers them once and all variants benefit automatically.
#
# Usage:
#   ./scripts/deploy-hooks.sh                  # deploy locally
#   ./scripts/deploy-hooks.sh --dry-run        # preview local changes
#   ./scripts/deploy-hooks.sh --remote HOST    # install on a remote machine via SSH
#   ./scripts/deploy-hooks.sh --remote HOST --dry-run

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_SRC="$SCRIPT_DIR/../hooks"
COMMANDS_SRC="$SCRIPT_DIR/../commands"

DRY_RUN=false
REMOTE=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --remote)  REMOTE="${2:-}"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

HOOKS=(
  "kf-route.py"
  "kf_module_index.txt"
  "kf-stop-validator.py"
  "kf-precompact.py"
  "kf-postcompact.py"
  "kf-edit-nudge.py"
  "kf-session-start.py"
  "kf-stats.py"
  "kf-loop.py"
)

# Commands to deploy (just the filenames; source in commands/, dest in ~/.claude/commands/)
COMMANDS=(
  "kf-loop.md"
)

# ─── Local deploy ─────────────────────────────────────────────────────────────

local_deploy() {
  local hooks_dst="$HOME/.claude/hooks"
  local commands_dst="$HOME/.claude/commands"
  local any_changed=false

  echo "KF Local Deploy"
  echo "  Hooks:    $HOOKS_SRC → $hooks_dst"
  echo "  Commands: $COMMANDS_SRC → $commands_dst"
  echo ""

  mkdir -p "$hooks_dst" "$commands_dst"

  echo "Hooks:"
  for hook in "${HOOKS[@]}"; do
    local src="$HOOKS_SRC/$hook"
    local dst="$hooks_dst/$hook"
    if [[ ! -f "$src" ]]; then
      echo "  MISSING  $hook  (not in source, skipping)"
      continue
    fi
    if [[ -f "$dst" ]] && cmp -s "$src" "$dst"; then
      echo "  OK       $hook"
    else
      if $DRY_RUN; then
        echo "  WOULD    $hook"
      else
        cp "$src" "$dst"
        echo "  DEPLOYED $hook"
      fi
      any_changed=true
    fi
  done

  echo ""
  echo "Commands:"
  for cmd in "${COMMANDS[@]}"; do
    local src="$COMMANDS_SRC/$cmd"
    local dst="$commands_dst/$cmd"
    if [[ ! -f "$src" ]]; then
      echo "  MISSING  $cmd  (not in source, skipping)"
      continue
    fi
    if [[ -f "$dst" ]] && cmp -s "$src" "$dst"; then
      echo "  OK       $cmd"
    else
      if $DRY_RUN; then
        echo "  WOULD    $cmd"
      else
        cp "$src" "$dst"
        echo "  DEPLOYED $cmd"
      fi
      any_changed=true
    fi
  done

  echo ""
  if $DRY_RUN; then
    echo "Dry run complete. Run without --dry-run to apply."
  elif $any_changed; then
    echo "Done. Restart Claude Code for hook changes to take effect."
  else
    echo "Done. All files already up to date."
  fi
}

# ─── Remote deploy ────────────────────────────────────────────────────────────

remote_deploy() {
  local host="$REMOTE"
  echo "KF Remote Deploy → $host"
  echo ""

  # 1. Copy hooks
  echo "Hooks:"
  for hook in "${HOOKS[@]}"; do
    local src="$HOOKS_SRC/$hook"
    if [[ ! -f "$src" ]]; then
      echo "  MISSING  $hook  (not in source, skipping)"
      continue
    fi
    if $DRY_RUN; then
      echo "  WOULD    $hook"
    else
      scp -q "$src" "$host:~/.claude/hooks/$hook"
      echo "  DEPLOYED $hook"
    fi
  done

  # 2. Copy commands
  echo ""
  echo "Commands:"
  for cmd in "${COMMANDS[@]}"; do
    local src="$COMMANDS_SRC/$cmd"
    if [[ ! -f "$src" ]]; then
      echo "  MISSING  $cmd  (not in source, skipping)"
      continue
    fi
    if $DRY_RUN; then
      echo "  WOULD    $cmd"
    else
      scp -q "$src" "$host:~/.claude/commands/$cmd"
      echo "  DEPLOYED $cmd"
    fi
  done

  # 3. Remote setup: registry dir, settings.json hook registration
  echo ""
  echo "Remote setup:"
  if $DRY_RUN; then
    echo "  WOULD    create ~/.claude/kf/loops/ and initialize registry"
    echo "  WOULD    register UserPromptSubmit hook in settings.json"
  else
    ssh "$host" 'bash -s' <<'REMOTE_SETUP'
set -e

# Create registry dir and initialize if missing
mkdir -p ~/.claude/kf/loops
if [[ ! -f ~/.claude/kf/loops/registry.yaml ]]; then
  printf '# KF Loop Registry — managed by kf-loop.py\nloops:\n  {}\n' \
    > ~/.claude/kf/loops/registry.yaml
  echo "  CREATED  ~/.claude/kf/loops/registry.yaml"
else
  echo "  OK       ~/.claude/kf/loops/registry.yaml"
fi

# Register UserPromptSubmit hook in settings.json if not already present
python3 - <<'PYEOF'
import json
from pathlib import Path

settings_path = Path.home() / '.claude' / 'settings.json'
settings = json.loads(settings_path.read_text())

hooks = settings.setdefault('hooks', {})
ups = hooks.setdefault('UserPromptSubmit', [])

hook_cmd = 'python3 ' + str(Path.home() / '.claude' / 'hooks' / 'kf-loop.py')

# Check if already registered
already = any(
    h.get('command') == hook_cmd
    for entry in ups
    for h in entry.get('hooks', [])
)

if already:
    print('  OK       kf-loop UserPromptSubmit hook (already registered)')
else:
    ups.append({'matcher': '', 'hooks': [{'type': 'command', 'command': hook_cmd}]})
    settings_path.write_text(json.dumps(settings, indent=4))
    print('  DEPLOYED kf-loop UserPromptSubmit hook → settings.json')
PYEOF
REMOTE_SETUP
  fi

  echo ""
  if $DRY_RUN; then
    echo "Dry run complete. Run without --dry-run to apply."
  else
    echo "Done. Restart Claude Code on $host for hook changes to take effect."
    echo "Note: activate loops on $host separately — registries are per-machine."
    echo "  e.g. ssh $host 'python3 ~/.claude/hooks/kf-loop.py auto de-ai'"
  fi
}

# ─── Entry point ──────────────────────────────────────────────────────────────

if [[ -n "$REMOTE" ]]; then
  remote_deploy
else
  local_deploy
fi
