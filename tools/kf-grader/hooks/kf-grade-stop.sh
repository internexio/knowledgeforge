#!/bin/sh
# kf-grade-stop.sh: worker-machine Stop hook (Completion Gate nudge). Hook type: Stop.
# Graceful degradation: every error path exits 0. This is a nudge; the hard gate is `kf-grade verify` at the completion consumer.
#
# Behavior (build prompt 4.7):
#   stop_hook_active true                                          -> allow (it blocks at most once)
#   no active task for this repo (~/.kf-grader/active/<repo>.json) -> allow
#   last message has completion language AND `kf-grade verify` fails for HEAD -> block once with a reason
INPUT="$(cat 2>/dev/null)" || exit 0
RESULT="$(printf '%s' "$INPUT" | KF_GRADE_BIN="${KF_GRADE_BIN:-kf-grade}" KF_GRADER_ACTIVE_DIR="${KF_GRADER_ACTIVE_DIR:-$HOME/.kf-grader/active}" python3 -c '
import json, os, re, subprocess, sys
try:
    d = json.load(sys.stdin)
    if d.get("stop_hook_active"):
        sys.exit(0)
    cwd = d.get("cwd") or os.getcwd()
    top = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=10)
    if top.returncode != 0:
        sys.exit(0)
    repo = os.path.basename(top.stdout.strip())
    marker = os.path.join(os.environ["KF_GRADER_ACTIVE_DIR"], repo + ".json")
    if not os.path.isfile(marker):
        sys.exit(0)
    task = json.load(open(marker)).get("task_id")
    msg = d.get("last_assistant_message") or ""
    if not task or not re.search(r"(?i)\b(done|complete[d]?|all (acceptance )?criteria|ready for review|finished)\b", msg):
        sys.exit(0)
    head = subprocess.run(["git", "-C", cwd, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10).stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        sys.exit(0)
    v = subprocess.run([os.environ["KF_GRADE_BIN"], "verify", "--task-id", task, "--head-sha", head], capture_output=True, text=True, timeout=60)
    if v.returncode == 0:
        sys.exit(0)
    print(json.dumps({"decision": "block", "reason": "Completion requires a grader PASS for HEAD " + head + ". Run: kf-grade submit --task-id " + task + " --head-sha " + head + " --wait"}))
except Exception:
    sys.exit(0)
' 2>/dev/null)" || exit 0
[ -n "$RESULT" ] && printf '%s\n' "$RESULT"
exit 0
