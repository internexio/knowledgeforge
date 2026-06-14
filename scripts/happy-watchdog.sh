#!/usr/bin/env bash
# Happy watchdog for knowledgeforge-core
# Keeps a tmux session "knowledgeforge-core" running with Happy --yolo
# Managed by launchd: com.happy.knowledgeforge-core.plist

set -euo pipefail

SESSION="knowledgeforge-core"
PROJECT_DIR="~/Scripts/knowledgeforge-core"
LOG="~/agent-workflow/happy-knowledgeforge-core.log"
PAUSE_FILE="/tmp/happy-paused"
BACKOFF_DIR="/tmp/happy-backoff-state"
BACKOFF_FILE="$BACKOFF_DIR/$SESSION"

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HAPPY_SERVER_URL="https://happy.semalytics.io"
export HAPPY_WEBAPP_URL="https://happy-app.semalytics.io"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"; }

mkdir -p "$BACKOFF_DIR" "$(dirname "$LOG")"

# Respect global pause
if [[ -f "$PAUSE_FILE" ]]; then
    log "Paused: $(cat "$PAUSE_FILE")"
    exit 0
fi

# Check backoff
if [[ -f "$BACKOFF_FILE" ]]; then
    attempts=$(grep -c "^fail:" "$BACKOFF_FILE" 2>/dev/null || echo 0)
    last_fail=$(tail -1 "$BACKOFF_FILE" | cut -d: -f2)
    now=$(date +%s)

    case $attempts in
        [12])   wait=60 ;;
        3)      wait=300 ;;
        4)      wait=900 ;;
        5)      wait=1800 ;;
        6)      wait=3600 ;;
        7)      wait=5400 ;;
        *)      wait=7200 ;;
    esac

    if (( now - last_fail < wait )); then
        log "Backoff: attempt $attempts, waiting ${wait}s"
        exit 0
    fi
fi

# Check if session already running and healthy
if tmux has-session -t "$SESSION" 2>/dev/null; then
    pane_pid=$(tmux list-panes -t "$SESSION" -F '#{pane_pid}' 2>/dev/null | head -1)
    if [[ -n "$pane_pid" ]] && kill -0 "$pane_pid" 2>/dev/null; then
        # Claude-liveness check ([project]-g27n): when Claude exits, the tmux
        # session + pane process persist (pane drops to a shell), so has-session
        # and kill -0 both pass and we'd wrongly report healthy. Two signals must
        # agree: pane foreground command is a shell AND the last non-blank pane
        # line is a shell prompt. Both-required avoids false-restarting a session
        # transiently running a Bash tool (pane_cmd shell, but last line is TUI).
        pane_cmd=$(tmux list-panes -t "$SESSION" -F '#{pane_current_command}' 2>/dev/null | head -1)
        last_line=$(tmux capture-pane -t "$SESSION" -p 2>/dev/null | grep -v '^$' | tail -1)
        claude_dead=0
        case "$pane_cmd" in
            zsh|-zsh|bash|-bash|sh|-sh|fish|-fish|dash)
                if echo "$last_line" | grep -qE '^[A-Za-z0-9._-]+@[A-Za-z0-9._-]+ .+[%$#][[:space:]]*$'; then
                    claude_dead=1
                fi
                ;;
        esac
        if [[ "$claude_dead" == "1" ]]; then
            log "Claude exited to shell (pane_cmd=$pane_cmd), restarting $SESSION (g27n)"
            tmux kill-session -t "$SESSION" 2>/dev/null || true
        else
            output=$(tmux capture-pane -t "$SESSION" -p -S -5 2>/dev/null || true)
            if echo "$output" | grep -qiE "401|403|token expired|unauthorized|auth.*error"; then
                log "Auth error detected, recording failure"
                echo "fail:$(date +%s)" >> "$BACKOFF_FILE"
                tmux kill-session -t "$SESSION" 2>/dev/null || true
            else
                if [[ -f "$BACKOFF_FILE" ]]; then
                    rm -f "$BACKOFF_FILE"
                    log "Backoff cleared — session healthy"
                fi
                exit 0
            fi
        fi
    else
        log "Session exists but process dead, cleaning up"
        tmux kill-session -t "$SESSION" 2>/dev/null || true
    fi
fi

# Start new session
log "Starting $SESSION in $PROJECT_DIR"
tmux new-session -d -s "$SESSION" -c "$PROJECT_DIR"
tmux send-keys -t "$SESSION" "export PATH=$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin HAPPY_SERVER_URL=https://happy.semalytics.io HAPPY_WEBAPP_URL=https://happy-app.semalytics.io; cd $PROJECT_DIR && happy --yolo" Enter

# Verify it started
sleep 5
if tmux has-session -t "$SESSION" 2>/dev/null; then
    log "Session $SESSION started successfully"
else
    log "Failed to start $SESSION"
    echo "fail:$(date +%s)" >> "$BACKOFF_FILE"
fi
