"""SSH forced-command gate. authorized_keys line: command="kf-grade-ssh <role> <key_id>",restrict ssh-ed25519 ...

worker key:     submit, status, verify          (read-only boolean for verify; the Stop hook and completion consumer need it)
dispatcher key: register, digest, spotcheck, canary, plus the worker set
Anything else is refused before argparse runs. The command is parsed with shlex and passed as an argv list, never to a
shell, so metacharacters inside arguments (for example a registered --test-command) are inert.
"""
from __future__ import annotations

import os
import shlex
import sys

WORKER = {"submit", "status", "verify"}
DISPATCHER = WORKER | {"register", "digest", "spotcheck", "canary"}
ROLES = {"worker": WORKER, "dispatcher": DISPATCHER}


def parse(role: str, original: str | None) -> list[str]:
    if role not in ROLES:
        raise PermissionError(f"unknown role {role!r}")
    if not original:
        raise PermissionError("interactive sessions are not allowed")
    try:
        argv = shlex.split(original)
    except ValueError as e:
        raise PermissionError(f"unparseable command: {e}")
    if argv and os.path.basename(argv[0]) == "kf-grade":
        argv = argv[1:]
    if not argv or argv[0] not in ROLES[role]:
        raise PermissionError(f"{role} key may only run: {', '.join(sorted(ROLES[role]))}")
    return argv


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    role = args[0] if args else ""
    key_id = args[1] if len(args) > 1 else role
    try:
        cmd = parse(role, os.environ.get("SSH_ORIGINAL_COMMAND"))
    except PermissionError as e:
        sys.stderr.write(f"kf-grade-ssh: denied: {e}\n")
        return 2
    os.environ["KF_GRADER_KEY_ID"] = f"{role}:{key_id}"
    os.environ["KF_GRADER_MODE"] = "local"
    from .cli import main as cli_main

    return cli_main(cmd)
